from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from functools import reduce
import crud, models, schemas
from dependencies import get_db
from typing import List, Any, Dict
import json
from datetime import datetime
import os
import logging
from pyrsistent import pmap
from pprint import pformat


router = APIRouter()

# Настройка логирования
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "logs_parsed_by_page.log")

logging.basicConfig(filename=log_file_path, level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s')

def default_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)

@router.get("/logs", response_model=List[schemas.Log], operation_id="read_logs")
async def read_logs(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    logs = crud.get_logs(db, skip=skip, limit=limit)
    if not logs:
        raise HTTPException(status_code=404, detail="Logs not found")
    return logs

@router.post("/logs", response_model=schemas.Log, operation_id="create_log")
async def create_log(log: schemas.LogCreate, db: Session = Depends(get_db)):
    return crud.create_log(db=db, log=log)

@router.delete("/logs", operation_id="delete_logs")
async def delete_logs(db: Session = Depends(get_db)):
    crud.delete_logs(db)
    return {"message": "Logs deleted successfully"}

@router.api_route("/logs_parsed_by_page/{page_str}", methods=['GET'], operation_id="logs_parsed_by_page")
async def logs_parsed_by_page(page_str: int, db: Session = Depends(get_db)):
    pageSize = 100

    logging.info(f'Запрос на страницу: {page_str}')
    page = int(page_str)
    logging.info(f'Номер страницы: {page}')
    
    dbanswer = db.query(models.Logs).filter(models.Logs.id <= (page * pageSize), models.Logs.id > ((page - 1) * pageSize)).all()
    logging.info(f'Количество записей на странице: {len(dbanswer)}')
    
    if not dbanswer:
        logging.error('Записи не найдены')
        raise HTTPException(status_code=404, detail='Logs not found')
    
    # Логирование исходных данных из базы
    logging.info('Исходные данные из базы данных:')
    for row in dbanswer:
        logging.info(json.dumps(row.__dict__, default=default_serializer, ensure_ascii=False, indent=4))
    
    def flatDbAnswerItem(item: Dict[str, Any]) -> Dict[str, Any]:
        logging.info(f'Обработка item: {json.dumps(item, default=default_serializer, ensure_ascii=False, indent=4)}')
        
        if 'payload' in item['body']:
            logging.info(f'Найден payload в body: {item["body"]}')
            bodyUpped = pmap(item).update(json.loads(item['body']))
            bodyUpped_dict = dict(bodyUpped)
            logging.info(f'Результат после обновления bodyUpped: {json.dumps(bodyUpped_dict, default=default_serializer, ensure_ascii=False, indent=4)}')
            
            payloadUpped = bodyUpped.update(bodyUpped['payload'])
            payloadUpped_dict = dict(payloadUpped)
            logging.info(f'Результат после обновления payloadUpped: {json.dumps(payloadUpped_dict, default=default_serializer, ensure_ascii=False, indent=4)}')
            
            return payloadUpped_dict
        else:
            return item


    unsortedResult = []
    for ans in dbanswer:
        item = ans.__dict__.copy()  # Используем копию, чтобы избежать изменений оригинала
        flat_item = flatDbAnswerItem(item)
        unsortedResult.append(flat_item)
    
    for item in unsortedResult:
        if '_sa_instance_state' in item:
            del item['_sa_instance_state']  # Удаление ключа _sa_instance_state

    logging.info(f'Количество преобразованных записей: {len(unsortedResult)}')

    def sortResultItem(item: Dict[str, Any]) -> Dict[str, Any]:
        return dict(sorted(item.items(), key=lambda answerItem: answerItem[0]))

    headers = {v: v for v in list(reduce(lambda allKeys, dict: allKeys.union(dict.keys()), unsortedResult, set()))}
    unsortedResult.insert(0, headers)
    result = list(map(sortResultItem, unsortedResult))

    if not result:
        logging.error('Записи не найдены после сортировки')
        raise HTTPException(status_code=404, detail='Logs not found')
    
    logging.info('Формирование окончательного ответа')

    # Запись результата в файл для анализа
    response_log_file_path = os.path.join(log_dir, f"response_page_{page}.txt")
    
    with open(response_log_file_path, "w", encoding="utf-8") as log_file:
        log_file.write(json.dumps(result, ensure_ascii=False, indent=4, default=default_serializer))
    
    logging.info(f'Ответ записан в файл: {response_log_file_path}')
    
    return json.loads(json.dumps(result, ensure_ascii=False, indent=4, default=default_serializer))

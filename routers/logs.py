from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from functools import reduce
import crud, models, schemas
from dependencies import get_db
from typing import List, Any, Dict
import json
from datetime import datetime
import os

router = APIRouter()

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

    def immutableDictUpdate(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        dict1.update(dict2)
        return dict1

    print('page_str', page_str)
    page = int(page_str)
    print('page', page)
    
    dbanswer = db.query(models.Logs).filter(models.Logs.id <= (page * pageSize), models.Logs.id > ((page - 1) * pageSize)).all()
    print('Количество записей на странице:', len(dbanswer))
    
    if not dbanswer:
        raise HTTPException(status_code=404, detail='Logs not found')
    
    def flatDbAnswerItem(item: Dict[str, Any]) -> Dict[str, Any]:
        if 'payload' in item['body']:
            bodyUpped = immutableDictUpdate(item, json.loads(item['body']))
            payloadUpped = immutableDictUpdate(bodyUpped, item['payload'])
            return payloadUpped
        else:
            return item

    unsortedResult = list(map(flatDbAnswerItem, [ans.__dict__ for ans in dbanswer]))
    for item in unsortedResult:
        if '_sa_instance_state' in item:
            del item['_sa_instance_state']  # Удаление ключа _sa_instance_state

    print('Количество преобразованных записей:', len(unsortedResult))

    def sortResultItem(item: Dict[str, Any]) -> Dict[str, Any]:
        return dict(sorted(item.items(), key=lambda answerItem: answerItem[0]))

    headers = {v: v for v in list(reduce(lambda allKeys, dict: allKeys.union(dict.keys()), unsortedResult, set()))}
    unsortedResult.insert(0, headers)
    result = list(map(sortResultItem, unsortedResult))

    if not result:
        raise HTTPException(status_code=404, detail='Logs not found')
    
    print('Формирование окончательного ответа')
    
    # Запись результата в файл для анализа
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f"response_page_{page}.txt")
    
    with open(log_file_path, "w", encoding="utf-8") as log_file:
        log_file.write(json.dumps(result, ensure_ascii=False, indent=4, default=default_serializer))
    
    return json.loads(json.dumps(result, ensure_ascii=False, indent=4, default=default_serializer))

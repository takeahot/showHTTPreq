import csv
import os
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from functools import reduce
import crud, models, schemas
from dependencies import get_db
from typing import List, Any, Dict
from datetime import datetime
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

def replace_newlines(obj):
    if isinstance(obj, str):
        return obj.replace('\n', '\\u000A').replace('"','""')
    elif isinstance(obj, list):
        return [replace_newlines(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: replace_newlines(value) for key, value in obj.items()}
    else:
        return obj

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

    # Получаем список столбцов
    columns = models.Logs.__table__.columns.keys()

    # Формируем запрос, используя только определенные столбцы
    dbanswer = db.query(*[getattr(models.Logs, col) for col in columns]) \
                .filter(models.Logs.id <= (page * pageSize), models.Logs.id > ((page - 1) * pageSize)) \
                .all()

    dbanswer = [{col: getattr(row, col) for col in columns} for row in dbanswer]
    logging.info(f'Количество записей на странице: {len(dbanswer)}')
    
    if not dbanswer:
        logging.error('Записи не найдены')
        raise HTTPException(status_code=404, detail='Logs not found')
    
    # Логирование исходных данных из базы
    logging.info('Исходные данные из базы данных:')
    for row in dbanswer:
        logging.info(json.dumps(row, default=default_serializer, indent=4))

    def add_prefix_to_keys(data: Dict[str, Any], prefix: str) -> Dict[str, Any]:
        return {f"{prefix}_{key}": value for key, value in data.items()}

    def flatDbAnswerItem(item: Dict[str, Any]) -> Dict[str, Any]:
        logging.info(f'Обработка item: {json.dumps(item, default=json.JSONEncoder().default, indent=4)}')

        # все названия колонок item
        column_name = str(item.keys())

        # Определяем обязательные ключи
        id = item.get('id', 'Not found')
        headers = json.loads(item.get('headers') or '{"x-origin-domain": "Not found domain","x-forwarded-for": "Not found id"}')
        domain = headers.get('x-origin-domain')
        ip = headers.get('x-forwarded-for')
        timestamp = item.get('timestamp', 'Not found')
        headers = item.get('headers')


        # Определяем eventName и eventTimestamp и заполняем их или "Not found" по умолчанию
        event_name = item.get('eventName', 'Not found eventName')
        event_timestamp = item.get('eventTimestamp', 'Not found eventTimestamp')
        event_id = item.get('eventId','Not found eventId')
        ticket_id = item.get('ticketId',"Not found ticketId")
        internal_id = item.get('internalId','Not found internalId')
        number = item.get('number','Not found number')

        body = item.get('body', 'Not found body')
        if isinstance(body, str):
            try:
                body_json = json.loads(body)
            except json.JSONDecodeError:
                body = body
        else:
            body = 'Body is not string. Body type is ' + type(body) 
        
        if isinstance(body_json, dict):
            event_name = body_json.get('eventName') \
                or body_json.get('body') \
                and body_json.get('body').get('eventName',event_name)\
                or event_name
            event_timestamp = body_json.get('eventTimestamp') \
                or body_json.get('body') \
                and body_json.get('body').get('eventTimestamp',event_timestamp)\
                or event_timestamp
            event_id = body_json.get('eventId') \
                or body_json.get('body') \
                and body_json.get('body').get('eventId',event_timestamp)\
                or event_id
            internal_id = body_json.get('internalId') \
                or body_json.get('body') \
                and body_json.get('body').get('internalId') \
                or body_json.get('payload') \
                and body_json.get('payload').get('internalId')\
                or internal_id
            number = body_json.get('number') \
                or body_json.get('body') \
                and body_json.get('body').get('number') \
                or body_json.get('payload') \
                and body_json.get('payload').get('number') \
                or number
            ticket_id = body_json.get('ticketId') \
                or body_json.get('body') \
                and body_json.get('body').get('ticketId') \
                or body_json.get('payload') \
                and body_json.get('payload').get('ticketId')\
                or ticket_id


        logging.info(f'Определён eventName: {event_name}')
        logging.info(f'Определён eventTimestamp: {event_timestamp}')

        # Добавляем обязательные ключи на верхний уровень
        result = {
            'id': id,
            'ip': ip,
            'domain': domain,
            'eventName': event_name,
            'timestamp': timestamp,
            'eventTimestamp': event_timestamp,
            'column_names': column_name,
            'body': body,
            'body_json': body_json,
            'eventId': event_id,
            'ticketId': ticket_id,
            'internalId': internal_id,
            'number': number,
            'ticketId': ticket_id,
            'headers': headers,
        }

        if event_name == 'ticket_updated':
            # Ничего не поднимаем, оставляем все на своих местах
            pass

        elif event_name == 'ELMA_event_ticket update':
            # Поднимаем все поля body и payload на верхний уровень с префиксами
            # result['body'] = 'ELMA_event_ticket update'
            if 'body' in item and isinstance(body_json, dict):
                result.update(add_prefix_to_keys(body_json, 'body'))
                del item['body']
            if 'payload' in item and isinstance(item['payload'], dict):
                result.update(add_prefix_to_keys(item['payload'], 'payload'))
                del item['payload']
            
            # Оставляем некоторые поля на втором уровне
            second_level_fields = ['headers', 'query_params']
            result['second_level'] = {key: item[key] for key in second_level_fields if key in item}
        
        elif event_name == 'ticket_comment_created':
            # Поднимаем только поля из payload на верхний уровень с префиксами
            # if 'payload' in item and isinstance(item['payload'], dict):
            #     result.update(add_prefix_to_keys(item['payload'], 'payload'))
            #     del item['payload']
            
            # Оставляем некоторые поля на втором уровне
            second_level_fields = ['path_params', 'headers']
            # result['second_level'] = {key: item[key] for key in second_level_fields if key in item}
        
        
        # Другие eventName можно добавить аналогично
        elif event_name == 'ticket_created':
            if 'body' in item and isinstance(body_json, dict):
                result.update(add_prefix_to_keys(body_json, 'body'))
                del item['body']
            # Оставляем некоторые поля на втором уровне
            second_level_fields = ['headers', 'query_params']
            result['second_level'] = {key: item[key] for key in second_level_fields if key in item}
        
        elif event_name == 'document_downloaded':
            # Пример обработки для document_downloaded
            if 'body' in item and isinstance(body_json, dict):
                result.update(add_prefix_to_keys(body_json, 'body'))
                del item['body']
            if 'payload' in item and isinstance(item['payload'], dict):
                result.update(add_prefix_to_keys(item['payload'], 'payload'))
                del item['payload']
        
        # Пример обработки для остальных eventName
        else:
            if 'body' in item and isinstance(body_json, dict):
                result.update(add_prefix_to_keys(body_json, 'body'))
                del item['body']
            if 'payload' in item and isinstance(item['payload'], dict):
                result.update(add_prefix_to_keys(item['payload'], 'payload'))
                del item['payload']

        logging.info(f'Результат обработки item: {json.dumps(result, default=json.JSONEncoder().default, indent=4)}')
        return result

    # def flatDbAnswerItem(item: Dict[str, Any]) -> Dict[str, Any]:
    #     logging.info(f'Обработка item: {json.dumps(item, default=json.JSONEncoder().default, indent=4)}')

    #     # Логирование всех свойств item с их типами данных
    #     for key, value in item.items():
    #         logging.info(f'Ключ: {key}, Значение: {value}, Тип данных: {type(value)}')

    #     if 'payload' in item['body']:
    #         logging.info(f'Найден payload в body: {item["body"]}')

    #         bodyUpped = pmap(item).update(json.loads(item['body']))
    #         bodyUpped_dict = dict(bodyUpped)
    #         logging.info(f'Результат после обновления bodyUpped: {json.dumps(bodyUpped_dict, default=json.JSONEncoder().default, indent=4)}')

    #         payloadUpped = bodyUpped.update(bodyUpped['payload'])
    #         payloadUpped_dict = dict(payloadUpped)
    #         logging.info(f'Результат после обновления payloadUpped: {json.dumps(payloadUpped_dict, default=json.JSONEncoder().default, indent=4)}')

    #         # Логирование всех свойств после обновления payload
    #         for key, value in payloadUpped_dict.items():
    #             logging.info(f'Ключ: {key}, Значение: {value}, Тип данных: {type(value)}')

    #         return {
    #             key: json.dumps(value, default=str) if not isinstance(value, (str, int, float, bool)) else value
    #             for key, value in payloadUpped_dict.items()
    #         }

    #     else:
    #         return {
    #             key: json.dumps(value, default=str) if not isinstance(value, (str, int, float, bool)) else value
    #             for key, value in item.items()
    #         }

    # def sortAndFormatLogString(item: Dict[str, Any]) -> Dict[str, Any]:


    unsortedResult = []
    for ans in dbanswer:
        item = ans.copy()  # Используем копию, чтобы избежать изменений оригинала
        flat_item = flatDbAnswerItem(item)
        unsortedResult.append(flat_item)
    
    for item in unsortedResult:
        if '_sa_instance_state' in item:
            del item['_sa_instance_state']  # Удаление ключа _sa_instance_state

    logging.info(f'Количество преобразованных записей: {len(unsortedResult)}')

    def sort_result_item(item: Dict[str, Any]) -> Dict[str, Any]:
        # Обязательные поля впереди
        mandatory_keys = ['id', 'ip', 'domain', 'eventName', 'timestamp', 'eventTimestamp','eventId','internalId','number','ticketId']
        sorted_item = {key: item.pop(key, 'Not found') for key in mandatory_keys}
        # Остальные поля в алфавитном порядке
        sorted_item.update(dict(sorted(item.items())))
        return sorted_item

    headers = {v: v for v in list(reduce(lambda allKeys, dict: allKeys.union(dict.keys()), unsortedResult, set()))}
    unsortedResult.insert(0, headers)
    result = list(map(sort_result_item, unsortedResult))

    if not result:
        logging.error('Записи не найдены после сортировки')
        raise HTTPException(status_code=404, detail='Logs not found')
    
    logging.info('Формирование окончательного ответа')

    # # Запись результата в файл для анализа
    # response_log_file_path = os.path.join(log_dir, f"response_page_{page}.txt")
    # csv_file_path = os.path.join(log_dir, f"response_page_{page}.csv")

    # Обработка данных перед сериализацией
    processed_result = replace_newlines(result)

    # Проверка результатов перед записью
    logging.info(f'Result before saving: {json.dumps(processed_result, default=default_serializer, indent=4)}')

    # with open(response_log_file_path, "w", encoding="utf-8") as log_file:
        # log_file.write(json.dumps(processed_result, indent=4, default=default_serializer))
    
    # Запись данных в CSV файл
    # with open(csv_file_path, "w", newline='', encoding="utf-8") as csv_file:
        # writer = csv.DictWriter(csv_file, fieldnames=processed_result[0].keys())
        # writer.writeheader()
        # writer.writerows(processed_result)
    
    # logging.info(f'Ответ записан в файлы: {response_log_file_path} и {csv_file_path}')
    
    return json.loads(json.dumps(processed_result, indent=4, default=default_serializer))

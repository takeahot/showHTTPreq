from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from functools import reduce
import crud, models, schemas
from dependencies import get_db
from typing import List

router = APIRouter()

@router.get("/logs", response_model=List[schemas.Log])
async def read_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logs = crud.get_logs(db, skip=skip, limit=limit)
    if not logs:
        raise HTTPException(status_code=404, detail="Logs not found")
    return logs

@router.post("/logs", response_model=schemas.Log)
async def create_log(log: schemas.LogCreate, db: Session = Depends(get_db)):
    return crud.create_log(db=db, log=log)

@router.delete("/logs")
async def delete_logs(db: Session = Depends(get_db)):
    crud.delete_logs(db)
    return {"message": "Logs deleted successfully"}

@router.api_route("/logs_parsed_by_page/{page_str}", methods=['GET', 'PUT', 'POST', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE', 'CONNECT'])
async def logs_parsed_by_page(page_str: int, db: Session = Depends(get_db)):
    pageSize = 1000

    def immutableDictUpdate(dict1, dict2):
        dict1.update(dict2)
        return dict1

    page = int(page_str)

    dbanswer = db.query(models.Logs).filter(models.Logs.id <= (page * pageSize), models.Logs.id > ((page - 1) * pageSize)).all()

    def flatDbAnswerItem(item):
        if 'payload' in item['body']:
            bodyUpped = immutableDictUpdate(item, json.loads(item['body']))
            payloadUpped = immutableDictUpdate(bodyUpped, item['payload'])
            return payloadUpped
        else:
            return item

    unsortedResult = list(map(flatDbAnswerItem, [ans.__dict__ for ans in dbanswer]))

    def sortResultItem(item):
        return dict(sorted(item.items(), key=lambda answerItem: answerItem[0]))

    headers = {v: v for v in list(reduce(lambda allKeys, dict: allKeys.union(dict.keys()), unsortedResult, set()))}
    unsortedResult.insert(0, headers)
    result = list(map(sortResultItem, unsortedResult))

    if not result:
        raise HTTPException(status_code=404, detail='Logs not found')
    return result

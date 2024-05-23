from fastapi import FastAPI, HTTPException, Depends, Request, Body
from typing import List, Annotated
from pydantic import BaseModel
from database import engine, SessionLocal
import models, json, pprint, datetime, httpx
from sqlalchemy.orm import Session
from sqlalchemy import text
from functools import reduce

app = FastAPI()
models.Base.metadata.create_all(bind=engine)
# tableModel = models.Base.metadata.reflect(bind=engine,checkfirst=True)
# tableModel = models.Base.metadata.drop_all(bind=engine)
tableModel = models.Base.metadata.tables
print(tableModel)

with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'logs'"))
    print(result.all())

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        return super().default(obj)
    
# class ChoiceBase(BaseModel):
#     choice_text: str
#     is_correct: bool

# class QuestionBase(BaseModel):
#     question_text: str
#     choices: List[ChoiceBase]

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally: 
        db.close()
    
db_dependency = Annotated[Session, Depends(get_db)]

# @app.get('/questions/{question_id}')
# async def read_question(question_id: int, db: db_dependency):
#     result = db.query(models.Questions).filter(models.Questions.id == question_id).first()
#     if not result: 
#         raise HTTPException(status_code=404, detail='Question is not found')
#     return result

# @app.post("/questions/")
# async def create_questions(question: QuestionBase, db: db_dependency):
#     db_question = models.Questions(question_text=question.question_text)
#     db.add(db_question)
#     db.commit()
#     db.refresh(db_question)
#     for choice in question.choices:
#         db_choice = models.Choices(choice_text=choice.choice_text, is_correct=choice.is_correct, question_id=db_question.id)
#         db.add(db_choice)
#     db.commit()

@app.api_route('/',methods=['GET','PUT','POST','DELETE','PATCH','HEAD','OPTIONS','TRACE','CONNECT'])
async def write_request(request: Request, db: db_dependency):
    try:
        # return json.dump(Request.method)
        bodyObj = await request.json()
        db_logs = models.Logs(
            timestamp= datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"), 
            httpmethod=request.method, 
            headers=json.dumps(request.headers.__dict__, cls=CustomJSONEncoder), 
            body=json.dumps(bodyObj),
            path_params=repr(request.path_params), 
            query_params=json.dumps(request.query_params.__dict__)
        )
        db.add(db_logs)
        db.commit()
        db.refresh(db_logs)
        if str(bodyObj['eventName']) not in [\
            'ticket_created',\
            'ticket_updated',\
            'ticket_comment_created',\
            'ticket_comment_updated'\
        ]:
            print ('request got',str(bodyObj['eventName']))
        else:
            print('request got for resend', str(bodyObj['eventName']))
            # Отправка запроса на внешний URL
            # Преобразование заголовков в словарь
            headers_dict = dict(request.headers)
            headers_dict.pop('content-length', None)
            headers_dict.pop('host', None)

            bodyObj['eventName'] = bodyObj['eventName'] + '_from_koyeb'
            timeout = httpx.Timeout(60.0, connect=20.0, read=60.0)
            async with httpx.AsyncClient() as client:
                print(
                    'query parameter for ELMA',
                    {
                        'method': request.method,
                        'url': "https://7isfa26wfvp4a.elma365.eu/api/extensions/22fe87c3-14fc-4c97-83dd-52ef65fa4644/script/"
                               + bodyObj['eventName'],
                        'headers': headers_dict,
                        'json': bodyObj
                    }
                )
                try:
                    external_response = await client.request(
                        method=request.method,
                        url="https://7isfa26wfvp4a.elma365.eu/api/extensions/22fe87c3-14fc-4c97-83dd-52ef65fa4644/script/"
                            + bodyObj['eventName'],
                        headers=headers_dict,
                        json=bodyObj
                    )
                except httpx.RequestError as exc:
                    print(f"An error occurred while requesting {exc.request.url!r}.")
                    raise HTTPException(status_code=500, detail=f"Request to external service failed: {str(exc)}")


            response_data = dict()

            if not (200 <= external_response.status_code < 300):
                response_data['payload'] = {
                    'textError': f"data:text/html,{external_response.text}"
                }
            else: 
                response_data = external_response.json()

            response_data['status_code'] = external_response.status_code
            response_data['eventName'] = bodyObj['eventName'] + "_response"

            # Сохранение ответа от внешнего URL в БД
            db_response_logs = models.Logs(
                timestamp= datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"), 
                httpmethod=request.method, 
                headers=json.dumps(dict(external_response.headers), cls=CustomJSONEncoder),
                body=json.dumps(response_data),
                path_params=repr(request.path_params), 
                query_params=json.dumps(request.query_params.__dict__),
            )
            db.add(db_response_logs)
            db.commit()
            db.refresh(db_response_logs)

            print('Request and response logged')
            print(response_data)

        return {
            'method': request.method, 
            "headers": request.headers, 
            "body":await request.json(), 
            "path_params": request.path_params, 
            "query_params": request.query_params
        }
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.api_route('/list',methods=['GET','PUT','POST','DELETE','PATCH','HEAD','OPTIONS','TRACE','CONNECT'])
async def show_requests(db: db_dependency):
    result = db.query(models.Logs).all()
    # result = db.query(models.Logs).statement.columns.keys()
    # result = tableModel
    if not result: 
        raise HTTPException(status_code=404, detail='Logs is not found')
    return result

@app.api_route('/clean',methods=['GET','PUT','POST','DELETE','PATCH','HEAD','OPTIONS','TRACE','CONNECT'])
async def clean_history(db: db_dependency):
    del_res = db.query(models.Logs).delete()
    db.commit()
    return  del_res

@app.api_route('/present_casavi_body',methods=['GET','PUT','POST','DELETE','PATCH','HEAD','OPTIONS','TRACE','CONNECT'])
async def show_requests(db: db_dependency):

    def immutableDictUpdate(dict1,dict2):
        dict1.update(dict2)
        return dict1

    result = db.query(models.Logs).all()

    result = list(map(lambda x: immutableDictUpdate(immutableDictUpdate(x.__dict__,json.loads(x.body)),x.payload) if 'payload' in x.body else x ,result))
    # result = db.query(models.Logs).statement.columns.keys()
    # result = tableModel
    if not result: 
        raise HTTPException(status_code=404, detail='Logs is not found')
    return result

@app.api_route('/present_casavi_body/{page_str}',methods=['GET','PUT','POST','DELETE','PATCH','HEAD','OPTIONS','TRACE','CONNECT'])
async def show_requests(page_str, db: db_dependency):

    pageSize = 1000

    def immutableDictUpdate(dict1,dict2):
        dict1.update(dict2)
        return dict1

    page = int(page_str)

    dbanswer = db.query(models.Logs).filter( models.Logs.id <= (page * pageSize),models.Logs.id > ((page - 1) * pageSize) ).all()#.where(models.Logs.id > (page * 1000 - 1000)).all()
    # dbanswer = [{ 'a': 1 , "body": '{"payload":{"b":1,"c":2}}'}]

    def flatDbAnswerItem(item):
        if 'payload' in item['body']: 
            bodyUpped = immutableDictUpdate(item,json.loads(item['body']))
            payloadUpped = immutableDictUpdate(bodyUpped ,item['payload'])
            return payloadUpped
        else:
            return item
    unsortedResult = list(map( flatDbAnswerItem , [ans.__dict__ for ans in dbanswer] ))
    
    def sortResultItem (item):
        return dict(sorted(item.items(), key=lambda answerItem: answerItem[0]))
    
    headers = {v: v for v in list(reduce(lambda allKeys, dict: allKeys.union(dict.keys()),unsortedResult,set()))}
    unsortedResult.insert(0,headers)
    result = list(map(sortResultItem, unsortedResult))

    # result = db.query(models.Logs).statement.columns.keys()
    # result = tableModel
    if not result: 
        raise HTTPException(status_code=404, detail='Logs is not found')
    return result
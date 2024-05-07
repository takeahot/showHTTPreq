from fastapi import FastAPI, HTTPException, Depends, Request, Body
from typing import List, Annotated
from pydantic import BaseModel
from database import engine, SessionLocal
import models, json, pprint, datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

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
    # return json.dump(Request.method)
    db_logs = models.Logs(
        timestamp= datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"), 
        httpmethod=request.method, 
        headers=json.dumps(request.headers.__dict__, cls=CustomJSONEncoder), 
        body=await request.body(),
        path_params=repr(request.path_params), 
        query_params=json.dumps(request.query_params.__dict__)
    )
    db.add(db_logs)
    db.commit()
    db.refresh(db_logs)
    pprint.pp ({
        'method': request.method, 
        "headers": request.headers, 
        "body":await request.body(), 
        "path_params": request.path_params, 
        "query_params": request.query_params
    })
    return {
        'method': request.method, 
        "headers": request.headers, 
        "body":await request.body(), 
        "path_params": request.path_params, 
        "query_params": request.query_params
    }

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
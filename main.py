from fastapi import FastAPI
import models
from database import engine
from routers import logs, requests
from sqlalchemy import text

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

# Вывод схемы таблицы (для PostgreSQL или другой базы данных)
with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'logs'"))
    print(result.fetchall())

app.include_router(logs.router)
app.include_router(requests.router)

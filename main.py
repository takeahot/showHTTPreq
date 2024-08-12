from fastapi import FastAPI, Request
import models
import os
from database import engine
from routers import logs, requests
from sqlalchemy import text
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Добавляем TrustedHostMiddleware для всех хостов
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)


# Поднимаемся на один уровень вверх, чтобы выйти из папки main.py
one_level_up = os.path.dirname(os.path.abspath(__file__))

# Формируем путь к папке static
static_path = os.path.join(one_level_up, "static")
print("Path to static ----- ", static_path)

# Подключаем статические файлы для React приложения
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    client_ip = request.client.host
    print(f"Handling request for: {request.url}")
    print(f"Request method: {request.method}")
    print(f"Client IP: {client_ip}")

    # Чтение части тела запроса
    body = await request.body()
    print(f"Request body: {body}")  # Выводим первые 100 символов тела запроса

    response = await call_next(request)
    print(f"Response status for {request.url.path}: {response.status_code}")
    return response

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static"):
            print(f"Static file requested: {request.url.path} -> Status: {response.status_code}")
        return response

app.add_middleware(LoggingMiddleware)

models.Base.metadata.create_all(bind=engine)
tableModel = models.Base.metadata.tables
print(tableModel)

# Вывод схемы таблицы (для PostgreSQL или другой базы данных)
with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'logs'"))
    print(result.fetchall())

app.include_router(logs.router)
app.include_router(requests.router)

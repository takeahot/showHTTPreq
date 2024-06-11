from fastapi import FastAPI
import models
from database import engine
from routers import logs, requests

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

app.include_router(logs.router)
app.include_router(requests.router)

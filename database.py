import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

env = os.environ
connect_kwargs = dict(
    username=env['DATABASE_USER'],
    password=env['DATABASE_PASSWORD'],
    host=env['DATABASE_HOST'],
    database=env['DATABASE_NAME'],
)
if 'DATABASE_PORT' in env:
    connect_kwargs['port'] = env['DATABASE_PORT']

URL_DATABASE = URL.create(
    'postgresql',
    **connect_kwargs
)

engine = create_engine(URL_DATABASE, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

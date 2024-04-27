from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os, pprint
from dotenv import load_dotenv

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
print('url_database', URL_DATABASE)

engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
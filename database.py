from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os, pprint
env = os.environ
# os.environ['DATABASE_URL'] = 'postgresql://postgres:PoAn!000@localhost:5432/clay_pigeon_DB'
pprint.pprint(dict(env), width= 1 );
# URL_DATABASE = os.environ.get('DATABASE_URL') 

engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
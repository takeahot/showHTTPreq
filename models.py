from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, text
from database import Base

# class Questions(Base):
#     __tablename__ = 'questions'

#     id = Column(Integer, primary_key=True, index=True)
#     question_text = Column(String, index=True)

# class Choices(Base):
#     __tablename__ = 'choices'

#     id = Column(Integer, primary_key=True, index=True)
#     choice_text = Column(String, index=True)
#     is_correct = Column(Boolean, default=False)
#     question_id = Column(Integer, ForeignKey("questions.id"))

class Logs(Base):
    __tablename__ = 'logs'

    id = Column(Integer, unique=True, primary_key=True, index=True)
    timestamp = Column(String, index=True)
    httpmethod = Column(String) 
    headers = Column(String)
    body = Column(String)
    path_params = Column(String)
    query_params = Column(String)
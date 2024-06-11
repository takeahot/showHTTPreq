from sqlalchemy import Column, Integer, String, DateTime
from database import Base

class Logs(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime)
    httpmethod = Column(String)
    headers = Column(String)
    body = Column(String)
    path_params = Column(String)
    query_params = Column(String)
    payload = Column(String, nullable=True)

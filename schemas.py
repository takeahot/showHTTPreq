from pydantic import BaseModel
from typing import List

class LogBase(BaseModel):
    timestamp: str
    httpmethod: str
    headers: str
    body: str
    path_params: str
    query_params: str

class LogCreate(LogBase):
    pass

class Log(LogBase):
    id: int

    class Config:
        from_attributes = True

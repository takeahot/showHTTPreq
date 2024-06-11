from sqlalchemy.orm import Session
import models, schemas

def get_logs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Logs).offset(skip).limit(limit).all()

def create_log(db: Session, log: schemas.LogCreate):
    db_log = models.Logs(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def delete_logs(db: Session):
    db.query(models.Logs).delete()
    db.commit()

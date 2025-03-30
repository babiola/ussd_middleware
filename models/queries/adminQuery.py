from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.sql import select,update
from models.model import *
import logging

logger = logging.getLogger(__name__)

def getAdmin(db: Session,username:str):
    return db.query(AdminModel).filter_by(username=username).first()
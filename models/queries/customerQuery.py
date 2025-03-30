from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.sql import select,update
from models.model import *
import logging

logger = logging.getLogger(__name__)

def getCustomerByMsisdn(db: Session,msisdn:str):
    return db.query(CustomerModel).filter(CustomerModel.phonenumber == msisdn).first()
def customer(db: Session):
    return db.query(CustomerModel).first()
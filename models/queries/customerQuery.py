from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.sql import select,update
from models.model import *
import logging

logger = logging.getLogger(__name__)

def getCustomerByMsisdn(db: Session,msisdn:str):
    return db.query(CustomerModel).filter(CustomerModel.phonenumber == msisdn).first()
def getCustomerAccount(db: Session,account:str):
    return db.query(AccountModel).filter(AccountModel.accountNumber == account).first()
def customer(db: Session):
    return db.query(CustomerModel).first()
def create_account(db: Session, user: CustomerModel):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
def create(db: Session, model: object):
    db.add(model)
    db.commit()
    db.refresh(model)
    return model
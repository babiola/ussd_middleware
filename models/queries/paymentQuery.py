
from sqlalchemy.orm import Session
from models.model import *
import logging

logger = logging.getLogger(__name__)

def querySender(db:Session,walletAccount:str):
    return db.query(AccountModel).filter(AccountModel.walletAccount == walletAccount).first()
def queryLatestRecordByAmount(db:Session,amount:str):
    return db.query(TransactionModel).filter(TransactionModel.amount == amount).first()
def create(db: Session, model: object):
    db.add(model)
    db.commit()
    db.refresh(model)
    return model
def create_payment(db: Session, payment: TransactionModel):
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
def getPaymentByReference(db: Session, reference: str):
    return db.query(TransactionModel).filter(TransactionModel.reference == reference).first()

def getPaymentHistories(db: Session,userId:int,start:DateTime,end:DateTime,transType:str):
    return db.query(TransactionModel).filter(TransactionModel.user_id == userId).all()

def get_all_bill(db: Session):
    return db.query(ProductModel).all()


def get_single_bill_by_id(db: Session, id: int):
    return db.query(ProductModel).filter(ProductModel.id == id).first()


def get_all_biller(db: Session):
    return db.query(ProductTypeModel).all()


def get_single_biller_by_id(db: Session, id: int):
    return db.query(ProductTypeModel).filter(ProductTypeModel.id == id).first()


def get_single_biller_by_billerId(db: Session, billerId: str):
    return db.query(ProductTypeModel).filter(ProductTypeModel.billerId == billerId).first()

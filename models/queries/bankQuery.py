from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.sql import select,update
from models.model import *
import logging

logger = logging.getLogger(__name__)

def notifications(db: Session,userId:int):
    if userId:
        return db.query(BankModel).join(UserNotification).join(CustomerModel).filter(CustomerModel.id==userId).all()
    return db.query(BankModel).all()
def bank(db: Session,userId:int):
    if userId:
        return db.query(BankModel).filter(BankModel.user_notifications).all()
    return db.query(BankModel).first()
def updateNotifications(db: Session,userId:int):
    if userId:
        return db.query(BankModel).filter(BankModel.user_notifications).all()
    return db.query(BankModel).first()
def updateNotification(db: Session,userId:int):
    if userId:
        return db.query(BankModel).filter(BankModel.user_notifications).all()
    return db.query(BankModel).first()
def deleteNotification(db: Session,userId:int):
    if userId:
        return db.query(BankModel).filter(BankModel.user_notifications).all()
    return db.query(BankModel).first()
def deleteNotifications(db: Session,userId:int):
    if userId:
        return db.query(BankModel).filter(BankModel.user_notifications).all()
    return db.query(BankModel).first()
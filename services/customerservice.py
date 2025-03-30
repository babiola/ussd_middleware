
import logging
from sqlalchemy.orm import Session
from models.model import *
from models.queries import customerQuery
from datetime import datetime,timedelta
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.customer import *
from schemas.admin import Admin
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)

logger = logging.getLogger(__name__)

def profile(
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        msisdn: str,
        background_task: BackgroundTasks,):
    try:
        customer = customerQuery.getCustomerByMsisdn(db=db,msisdn=msisdn)
        if customer:
            return CustomerResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=Customer.model_validate(customer))
        response.status_code = status.HTTP_404_NOT_FOUND
        return CustomerResponse(statusCode=str(status.HTTP_404_NOT_FOUND),statusDescription=NOTFOUND) 
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CustomerResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
    
    
def balance(
        wallet:str,
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        user: Customer,
        background_task: BackgroundTasks,):
    try:
        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=user.wallet.availableBalance)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)

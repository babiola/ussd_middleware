from fastapi import APIRouter
from fastapi import (
    Depends,
    Query,
    status,
    Response,
    Request,
    BackgroundTasks,
)
from models.model import AccountModel
from sqlalchemy.orm import Session
from typing import Annotated
from utils import util
from utils.constant import *
from datetime import date
from utils.dependencies import getSystemSetting, authenticate_user,validateTransactionPIN
from utils.database import get_db
from schemas.admin import Admin
from schemas.customer import Customer
from services import transactionservice
import logging
from schemas.setting import Setting
from schemas.transaction import Transactions,BaseResponse

logger = logging.getLogger(__name__)


router = APIRouter()

# transaction
@router.get("/ministatement", 
    response_model=Transactions,
    response_model_exclude_unset=True,name="get customer transactions")
async def get_transactions(
    request: Request,
    response: Response,
    
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    account:Annotated[AccountModel, Depends(validateTransactionPIN)],
    db: Annotated[Session, Depends(get_db)],
    startDate: str = Query(str(date.today())),
    endDate: str = Query(str(date.today())),
    transaction_type: str = Query(None),
):
    try:
        return transactionservice.transactions(
                request=request,
                response=response,
                setting=setting,
                db=db,
                tenant=tenant,
                user=user,
                startDate=startDate,
                endDate=endDate,
                transactionType=transaction_type
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.get("/{id}", 
    response_model=Transactions,
    response_model_exclude_unset=True,name="get single transaction")
async def get_transaction(
    id:str,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return transactionservice.getNotification(
                id=id,
                db=db,
                tenant=tenant,
                setting=setting,
                request=request,
                response=response,
                user=user,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )


import logging
from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Response,
    Request,
    BackgroundTasks,
)
from models.model import *
from schemas.bank import *
from schemas.base import *
from schemas.setting import Setting
from sqlalchemy.orm import Session
from utils.constant import *
from typing import Annotated
from utils.dependencies import getSystemSetting, authenticate_user,validateTransactionPIN
from utils.database import get_db
from services import bankservice
from schemas.admin import Admin
from utils import util

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transfer"
)

# Intra
@router.post(
    "/enquiry/inMFB",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
)
async def bank_name_enquiry(
    payload: TransferNameEnquiryRequest,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await bankservice.bankNameEnquiry(
                request=request,
                response=response,
                setting=setting,
                db=db,
                payload=payload
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post(
    "/inMFB",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
)
async def post_intra_bank_transfer(
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    account:Annotated[AccountModel, Depends(validateTransactionPIN)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return bankservice.getAdmin(
                request=request,
                response=response,
                setting=setting,
                db=db,
                user=user,
                background_task=background_task,
            )
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
# NIP
@router.get("/banks", 
    response_model=BanksResponse,
    response_model_exclude_unset=True)
async def bank_list(
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
):
    try:
        if user:
            return bankservice.banks(request=request,response=response,setting=setting)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BanksResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(ex),)
@router.post(
    "/possible-banks",
    response_model=BanksResponse,
    response_model_exclude_unset=True
)
async def get_possible_banks(
    payload:TransferPossibleRequest,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return bankservice.possibleBank(
                request=request,
                response=response,
                setting=setting,
                payload=payload,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BanksResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post(
    "/enquiry/toNIP",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
)
async def post_nip_name_enquiry(
    payload: TransferNameEnquiryRequest,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await bankservice.bankNameEnquiry(
                request=request,
                response=response,
                setting=setting,
                db=db,
                payload=payload
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post(
    "/toNIP",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
)
async def post_nip_bank_transfer(
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    account:Annotated[AccountModel, Depends(validateTransactionPIN)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return bankservice.getAdmin(
                request=request,
                response=response,
                setting=setting,
                db=db,
                user=user,
                background_task=background_task,
            )
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )

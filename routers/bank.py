
import logging
from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Response,
    Request,
    BackgroundTasks,
)
from schemas.bank import *
from schemas.setting import Setting
from sqlalchemy.orm import Session
from utils.constant import *
from typing import Annotated
from utils.dependencies import getSystemSetting, authenticate_user
from utils.database import get_db
from services import bankservice
from schemas.admin import Admin
from utils import util

logger = logging.getLogger(__name__)
router = APIRouter(
)

# Intra
@router.post(
    "/transfer/enquiry/inMFB",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
)
async def bank_name_enquiry(
    request: Request,
    responses: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return Adminservice.getAdmin(
                request=request,
                response=responses,
                setting=setting,tenant=tenant,
                db=db,
                user=user,
                background_task=background_task,
            )
        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post(
    "/transfer/inMFB",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
)
async def post_intra_bank_transfer(
    request: Request,
    responses: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return Adminservice.getAdmin(
                request=request,
                response=responses,
                setting=setting,tenant=tenant,
                db=db,
                user=user,
                background_task=background_task,
            )
        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )

# NIP
@router.get("/transfer/banks", 
    response_model=BanksResponse,
    response_model_exclude_unset=True)
async def bank_list(
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    #db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return bankservice.banks(request=request,response=response,setting=setting)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BanksResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(ex),)
@router.post(
    "/transfer/possible-banks",
    response_model=BaseResponse,
    response_model_exclude_unset=True
)
async def get_possible_banks(
    request: Request,
    responses: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return Adminservice.getAdmin(
                request=request,
                response=responses,
                setting=setting,tenant=tenant,
                db=db,
                user=user,
                background_task=background_task,
            )
        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post(
    "/transfer/enquiry/NIP",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
)
async def post_nip_name_enquiry(
    request: Request,
    responses: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return Adminservice.getAdmin(
                request=request,
                response=responses,
                setting=setting,tenant=tenant,
                db=db,
                user=user,
                background_task=background_task,
            )
        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post(
    "/transfer/NIP",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
)
async def post_nip_bank_transfer(
    request: Request,
    responses: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return Adminservice.getAdmin(
                request=request,
                response=responses,
                setting=setting,tenant=tenant,
                db=db,
                user=user,
                background_task=background_task,
            )
        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )

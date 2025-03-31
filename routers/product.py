
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
router = APIRouter(prefix="/product",
    tags=["product"],
)
@router.get("", 
    response_model=BanksResponse,
    response_model_exclude_unset=True,name="bank list")
async def getbanks(
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
    "/name-enquiry",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
    name="Open account"
)
async def post_Admin_open_new_account(
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
    "/transfer",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
    name="Open account"
)
async def post_Admin_open_new_account(
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
 
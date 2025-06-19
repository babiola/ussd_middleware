from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Response,
    Request,
    BackgroundTasks,
)
from schemas.customer import *
from schemas.admin import Admin
from schemas.setting import Setting
from models.model import AccountLevelEnum
from sqlalchemy.orm import Session
from utils.constant import *
from typing import Annotated
from utils.dependencies import getSystemSetting, authenticate_user
from utils.database import get_db
from services import customerservice
from utils import util
import logging

logger = logging.getLogger(__name__)
router = APIRouter(
)
@router.get(
    "/{msisdn}",
    response_model=CustomerResponse,
    response_model_exclude_unset=True,name="Customer details"
)
async def get_customer(
    msisdn:str,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return customerservice.profile(
                request=request,
                response=response,
                setting=setting,
                db=db,
                msisdn=msisdn,
                background_task=background_task,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CustomerResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post(
    "/bvn-verified",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
    name="Verify customer bvn details"
)
async def post_customer_bvn_verification(
    payload:BvnRequest,
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
):
    try:
        if user:
            if util.validateIP(request=request, allowed=user.ips):
                return await customerservice.getBvnDetails(
                payload=payload,
                response=responses,
                setting=setting,
            )
        else:
            responses.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=SYSTEMBUSY,
            )
    except Exception as ex:
        logger.error(ex)
        responses.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post(
    "/create-customer",
    response_model=BaseResponse,
    response_model_exclude_unset=True,
    name="Open account"
)
async def create_customer(
    payload:OpenAccountRequest,
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return await customerservice.create_customer(
                db=db,
                payload=payload,
                response=responses,
                setting=setting,accountType=AccountLevelEnum.TIER3
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
    "/create-account",
    response_model=CustomerResponse,
    response_model_exclude_unset=True,
    name="Open account"
)
async def post_customer_open_new_account(
    payload:OpenAccountRequest,
    request: Request,
    response: Response,
    user: Annotated[Customer, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return customerservice.open_account(
                db=db,
                request=request,
                payload=payload,
                response=response,
                setting=setting,
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
@router.get(
    "/balance/{accountNumber}",
    response_model=CustomerResponse,
    response_model_exclude_unset=True,
)
async def get_customer_balance(
    msisdn:str,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return customerservice.profile(
                request=request,
                response=response,
                setting=setting,
                db=db,
                msisdn=msisdn,
                background_task=background_task,
            )
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return CustomerResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CustomerResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post(
    "/enrolment",
    response_model=CustomerResponse,
    response_model_exclude_unset=True,
)
async def post_customer_enable_ussd_profile(
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return customerservice.getCustomer(
                request=request,
                response=responses,
                setting=setting,
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
    "/link/{event}",
    response_model=CustomerResponse,
    response_model_exclude_unset=True,
)
async def update_account_by_event(
    event:str,
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return customerservice.getCustomer(
                request=request,
                response=responses,
                setting=setting,
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
    "/deactivate-ussd",
    response_model=CustomerResponse,
    response_model_exclude_unset=True,
)
async def disable_customer_ussd_profile(
    request: Request,
    responses: Response,
    user: Annotated[Customer, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return customerservice.getCustomer(
                request=request,
                response=responses,
                setting=setting,
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
@router.patch(
    "/{msisdn}/update",
    response_model=CustomerResponse,
    response_model_exclude_unset=True,
    name="Update Customer details"
)
async def update_customer(
    request: Request,
    responses: Response,
    
    user: Annotated[Customer, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return customerservice.getCustomer(
                request=request,
                
                response=responses,
                setting=setting,
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
@router.delete(
    "/{msisdn}/delete",
    response_model=CustomerResponse,
    response_model_exclude_unset=True,
    name="disable customer ussd profile"
)
async def delete_customer(
    request: Request,
    responses: Response,
    
    user: Annotated[Customer, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return customerservice.getCustomer(
                request=request,
                response=responses,
                setting=setting,
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
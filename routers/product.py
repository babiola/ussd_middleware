
import logging
from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Response,
    Request,
    BackgroundTasks,
)
from models.model import AccountModel
from schemas.product import *
from schemas.package import PackagesResponse
from schemas.setting import Setting
from sqlalchemy.orm import Session
from utils.constant import *
from typing import Annotated
from utils.dependencies import getSystemSetting, authenticate_user,validateTransactionPIN
from utils.database import get_db
from services import productservices
from schemas.admin import Admin
from utils import util

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/product"
)
@router.post(
    "/buy-airtime",
    response_model=BaseResponse,
    response_model_exclude_unset=True
)
async def buy_airtime(
    payload: BillPaymentRequest,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    account:Annotated[AccountModel, Depends(validateTransactionPIN)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        return await productservices.buyAirtime(db=db,request=request,payload=payload,response=response,setting=setting,account=account,background_task=background_task,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.post(
    "/buy-data",
    response_model=BaseResponse,
    response_model_exclude_unset=True
)
async def buy_data_plan(
    payload: BillPaymentRequest,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    account:Annotated[AccountModel, Depends(validateTransactionPIN)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return await productservices.buyDataPlan(
                db=db,
                request=request,
                payload=payload,
                response=response,
                setting=setting,
                account=account,
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
@router.get("/list",
    response_model=ProductsResponse,
    response_model_exclude_unset=True,)
async def get_products(
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await productservices.getProducts(db=db,response=response,setting=setting)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return BaseResponse(
            statusCode=str(status.HTTP_500_INTERNAL_SERVER_ERROR),
            statusDescription=str(ex),
        )
@router.get("/billers/{productId}",
    response_model=ProductsResponse,
    response_model_exclude_unset=True,)
async def get_product_billers(
    productId: str,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return await productservices.getProductBillersByProductId(db=db,response=response,setting=setting,productId=productId)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=UNKNOWNUSER,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return BaseResponse(
            statusCode=str(status.HTTP_500_INTERNAL_SERVER_ERROR),
            statusDescription=str(ex),
        )
@router.get("/biller/packages/{billerId}",
    response_model=PackagesResponse,
    response_model_exclude_unset=True,)
async def get_biller_packages(
    billerId: str,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return await productservices.getBillerPackages(db=db,response=response,setting=setting,billerId=billerId)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return BaseResponse(
            statusCode=str(status.HTTP_500_INTERNAL_SERVER_ERROR),
            statusDescription=str(ex),
        )
@router.post("/name-enquiry",
    response_model=BaseResponse,
    response_model_exclude_unset=True)
async def biller_name_enquiry(
    payload: BillNameEnquiryRequest,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return await productservices.billNameEnquiry(payload=payload,response=response,setting=setting,db=db)
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
            statusDescription=str(ex),
        )
@router.post("/payment",
    response_model=BaseResponse,
    response_model_exclude_unset=True)
async def biller_payment(
    payload: BillPaymentRequest,
    request: Request,
    response: Response,
    user: Annotated[Admin, Depends(authenticate_user)],
    account:Annotated[AccountModel, Depends(validateTransactionPIN)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return await productservices.billPayment(payload=payload,request=request,response=response,setting=setting,db=db,user=user,background_task=background_task)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT,)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=str(ex), )

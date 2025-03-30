from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Response,
    Request,
    BackgroundTasks,
)
from schemas.customer import *
from schemas.setting import Setting
from sqlalchemy.orm import Session
from utils.constant import *
from typing import Annotated
from utils.dependencies import getSystemSetting, validateAdmin, getTenant
from utils.database import get_db
from services import customerservice
from utils import util
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/customers",
    tags=["customer"],
)
@router.get("", 
    response_model=CustomersResponse,
    response_model_exclude_unset=True,name="Insurance customers list")
async def getCustomers(
    request: Request,
    response: Response,
    tenant: Annotated[str, Depends(getTenant)],
    user: Annotated[Admin, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        if user:
            return customerservice.getCustomers(db=db,tenant=tenant)
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CustomersResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=str(ex),
        )
@router.get(
    "/{plateNumber}",
    response_model=VehicleResponse,
    response_model_exclude_unset=True,name="Insurance Customer details"
)
async def get_customer(
    plateNumber:str,
    request: Request,
    response: Response,
    tenant: Annotated[str, Depends(getTenant)],
    user: Annotated[Admin, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return customerservice.getCustomerByPlateNumber(
                db=db,
                plateNumber=plateNumber,
                request=request,
                response=response,
                setting=setting,
                tenant=tenant,
                user=user,
                background_task=background_task,
            )
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return VehicleResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=INVALIDACCOUNT,
            )
    except Exception as ex:
        logger.error(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return VehicleResponse(
            statusCode=str(status.HTTP_400_BAD_REQUEST),
            statusDescription=SYSTEMBUSY,
        )
@router.patch(
    "/{PlateNumber}/update",
    response_model=CustomerResponse,
    response_model_exclude_unset=True,
    name="Update Customer details"
)
async def update_customer(
    request: Request,
    responses: Response,
    tenant: Annotated[str, Depends(getTenant)],
    user: Annotated[Customer, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return customerservice.getCustomer(
                request=request,
                tenant=tenant,
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
    "/{PlateNumber}/delete",
    response_model=CustomerResponse,
    response_model_exclude_unset=True,
    name="delete customer record"
)
async def delete_customer(
    request: Request,
    responses: Response,
    tenant: Annotated[str, Depends(getTenant)],
    user: Annotated[Customer, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return customerservice.getCustomer(
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
    "",
    response_model=CustomerResponse,
    response_model_exclude_unset=True,
    name="Add new customer record"
)
async def post_customer(
    request: Request,
    responses: Response,
    tenant: Annotated[str, Depends(getTenant)],
    user: Annotated[Customer, Depends(validateAdmin)],
    setting: Annotated[Setting, Depends(getSystemSetting)],
    db: Annotated[Session, Depends(get_db)],
    background_task: BackgroundTasks,
):
    try:
        if user:
            return customerservice.getCustomer(
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
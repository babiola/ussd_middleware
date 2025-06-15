
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
def getBvnDetails(payload:BvnRequest,response:Response,setting:Setting):
    try:
        params = {'basic_or_advance': 'basic','bvn': payload.bvn}
        res = util.http(url=f'{setting.bvn_base_url}identity/validate-bvn',params=params)
        if res['status']:
            if util.formatPhoneFull(payload.msisdn) == util.formatPhoneFull(res['data']['phoneNumber']):
                if util.validateBVNDateOfBirth(res['data']['dateOfBirth'],payload.dob):
                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=res['detail'],data=res['data'])
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Record Mismatched")
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST 
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Phone Number Mismatched")
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=res['message'])
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
def create_customer(db:Session,payload:BvnRequest,response:Response,setting:Setting):
    try:
        params = {'basic_or_advance': 'advance','bvn': payload.bvn}
        res = util.http(url=f'{setting.bvn_base_url}identity/validate-bvn',params=params)
        if res['status']:
            if util.formatPhoneFull(payload.msisdn) == util.formatPhoneFull(res['data']['phoneNumber']):
                if util.validateBVNDateOfBirth(res['data']['dateOfBirth'],payload.dob):
                    payload ={
                        "birthCountryId": 1,
                        "branchId": 1,
                        "bvn": res['data']['bvn'],
                        "customerDomiciledState": "1",
                        "dateOfBirth": res['data']['dateOfBirth'],
                        "email": res['data']['email'],
                        "employStatusId": 1,
                        "firstName": res['data']['firstName'],
                        "fullname": f"{res['data']['firstName']} {res['data']['lastName']}",
                        "genderId": 1 if res['data']['gender'] == "Male" else 2,
                        "homeTelno": res['data']['phoneNumber1'],
                        "kycTierId": 1,
                        "language": "1",
                        "lastName": res['data']['lastName'],
                        "lgaOfOrigin": "Oshogob",
                        "maidenName": "Lawal",
                        "maritalStatusId": 1,
                        "middleName": res['data']['middleName'],
                        "mobileNumber": res['data']['phoneNumber1'],
                        "mobileNumber2": "",
                        "mothersMaidenName": "",
                        "nationalityId": 1,
                        "nickname": "gol",
                        "permanentAddressLine1": "Lagos",
                        "permanentAddressLine2": "Lagos",
                        "permanentAddressLine3": "Lagos",
                        "permanentAddressLine4": "Lagos",
                        "picture": "string",
                        "placeOfBirth": "Lagos",
                        "residenceStatus": "1",
                        "residentialAddressLine1": "Lagos",
                        "residentialAddressLine2": "Lagos",
                        "residentialAddressLine3": "Lagos",
                        "residentialAddressLine4": "Lagos",
                        "signature": "string",
                        "spouseEmploymentstatus": "1",
                        "spouseName": "Ruth",
                        "stateOfOriginId": 1,
                        "telephoneNo": res['data']['phoneNumber1'],
                        "titleId": 1
                    }
                    res = util.http(url=f'{setting.bank_bank_url}cis/channel/create-customer-biodata',params=payload)
                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=res['detail'],data=res['data'])
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Record Mismatched")
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST 
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Phone Number Mismatched")
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=res['message'])
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
def open_account(db:Session,request:Request,payload:OpenAccountRequest,response:Response,setting:Setting,background_task: BackgroundTasks):
    try:
        params = {'basic_or_advance': 'basic','bvn': payload.bvn}
        res = util.http(url=f'{setting.bvn_base_url}identity/validate-bvn',params=params)
        if res['status']:
            if util.formatPhoneFull(payload.msisdn) == util.formatPhoneFull(res['data']['phoneNumber']):
                if util.validateBVNDateOfBirth(res['data']['dateOfBirth'],payload.dob):
                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=res['detail'],data=res['data'])
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Record Mismatched")
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST 
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Phone Number Mismatched")
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=res['message'])
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)

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

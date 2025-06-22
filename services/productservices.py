
import logging
import json
from sqlalchemy.orm import Session
from models.model import *
from models.queries import productQuery
from datetime import datetime,timedelta
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.customer import *
from schemas.product import *
from schemas.product_type import ProductTypesResponse
from schemas.package import PackagesResponse
from schemas.base import BaseResponse, BillPaymentRequest, BillNameEnquiryRequest
from services import externalService
from utils import redisUtil
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)
logger = logging.getLogger(__name__)
async def buyAirtime(db:Session,request:Request,payload:BillPaymentRequest,response:Response,setting:Setting,account:AccountModel,background_task: BackgroundTasks):
    try:
        checkAccountBalance =await externalService.accountBalance(account=account.accountNumber,setting=setting)
        if checkAccountBalance['statuscode'] == str(status.HTTP_200_OK):
            if int(util.amountToKobo(checkAccountBalance['data']['WithdrawableBalance'])) > int(payload.amount):
                airtime = await externalService.buyAirtime(setting=setting,account=account,amount=payload.amount,msisdn=util.formatPhoneFull(payload.msisdn),network=payload.network)
                if airtime['statuscode'] == str(status.HTTP_200_OK):
                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=airtime['data'])
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=airtime['message'])
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=checkAccountBalance['message'])
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)   
async def buyDataPlan(db:Session,request:Request,payload:BillPaymentRequest,response:Response,setting:Setting,account:AccountModel,background_task: BackgroundTasks):
    try:
        checkAccountBalance =await externalService.accountBalance(account=account.accountNumber,setting=setting)
        if checkAccountBalance['statuscode'] == str(status.HTTP_200_OK):
            if int(util.amountToKobo(checkAccountBalance['data']['WithdrawableBalance'])) > int(payload.amount):
                data = await externalService.buyDataPlan(setting=setting,account=account,amount=payload.amount,msisdn=util.formatPhoneFull(payload.msisdn),network=payload.network,planId=payload.planId)
                if data['statuscode'] == str(status.HTTP_200_OK):
                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=data['data'])
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=data['message'])
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=checkAccountBalance['message'])
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
async def billNameEnquiry(db:Session,request:Request,payload:BillNameEnquiryRequest,response:Response,setting:Setting,account:AccountModel,background_task: BackgroundTasks):
    try:
        checkAccountBalance =await externalService.accountBalance(account=account.accountNumber,setting=setting)
        if checkAccountBalance['statuscode'] == str(status.HTTP_200_OK):
            if int(util.amountToKobo(checkAccountBalance['data']['WithdrawableBalance'])) > int(payload.amount):
                bill = await externalService.billNameEnquiry(setting=setting,account=account,amount=payload.amount,msisdn=util.formatPhoneFull(payload.msisdn),billType=payload.billType,billId=payload.billId)
                if bill['statuscode'] == str(status.HTTP_200_OK):
                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=bill['data'])
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=bill['message'])
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=checkAccountBalance['message'])
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
async def billPayment(db:Session,request:Request,payload:BillPaymentRequest,response:Response,setting:Setting,account:AccountModel,background_task: BackgroundTasks):
    try:
        checkAccountBalance =await externalService.accountBalance(account=account.accountNumber,setting=setting)
        if checkAccountBalance['statuscode'] == str(status.HTTP_200_OK):
            if int(util.amountToKobo(checkAccountBalance['data']['WithdrawableBalance'])) > int(payload.amount):
                bill = await externalService.billPayment(setting=setting,account=account,amount=payload.amount,msisdn=util.formatPhoneFull(payload.msisdn),billType=payload.billType,billId=payload.billId)
                if bill['statuscode'] == str(status.HTTP_200_OK):
                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=bill['data'])
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=bill['message'])
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=checkAccountBalance['message'])
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
async def getProducts(db:Session,request:Request,response:Response,setting:Setting):
    try:
        products = await productQuery.getProduts(db=db)
        return ProductsResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=products)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ProductsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
async def getProductByProductId(db:Session,request:Request,response:Response,setting:Setting,productId:str):
    try:
        product = await productQuery.getProductById(db=db,productId=productId)
        if product:
            return ProductResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=product)
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return ProductResponse(statusCode=str(status.HTTP_404_NOT_FOUND),statusDescription=PRODUCTNOTFOUND)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ProductResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
async def getProductBillersByProductId(db:Session,request:Request,response:Response,setting:Setting,productId:str):
    try:
        billers = await productQuery.getBillersByproductId(db=db,productId=productId)
        return ProductTypesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=billers)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ProductTypesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
async def getBillerPackages(db:Session,request:Request,response:Response,setting:Setting,billerId:str):
    try:
        plans = await productQuery.getPackagesBillerId(db=db,billerId=billerId)
        return PackagesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=plans)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PackagesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
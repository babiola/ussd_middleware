
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
        logger.info(f"Started buy {payload.billerId} of {payload.amount} for {payload.receipient} from account {payload.accountNumber}")
        biller = productQuery.getBillerByBillerId(db=db,billerId=payload.billerId)
        if biller:
            params = {"GLCode":setting.bankone_cust_gl,"RetrievalReference": util.generateId(),"AccountNumber": account.accountNumber,"Amount": payload.amount,"Narration":f"{biller.billerName}/{payload.receipient}/N{payload.amount}"}
            debitAccount =await externalService.debitAccountByBankOne(setting=setting,params=params)
            if debitAccount['statuscode'] == str(status.HTTP_200_OK):
                background_task.add_task(routeBillToProvider,payload=payload,biller=biller,account=account,db=db,setting=setting)
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)   
async def buyDataPlan(db:Session,request:Request,payload:BillPaymentRequest,response:Response,setting:Setting,account:AccountModel,background_task: BackgroundTasks):
    try:
        logger.info(f"Started buy {payload.billerId} of {payload.amount} for {payload.receipient} from account {payload.accountNumber}")
        biller = productQuery.getBillerByBillerId(db=db,billerId=payload.billerId)
        if biller:
            params = {"GLCode":setting.bankone_cust_gl,"RetrievalReference": util.generateId(),"AccountNumber": account.accountNumber,"Amount": payload.amount,"Narration":f"{biller.billerName}/{payload.receipient}/N{payload.amount}"}
            debitAccount =await externalService.debitAccountByBankOne(setting=setting,params=params)
            if debitAccount['statuscode'] == str(status.HTTP_200_OK):
                background_task.add_task(routeBillToProvider,payload=payload,biller=biller,account=account,db=db,setting=setting)
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)   
async def billPayment(db:Session,request:Request,payload:BillPaymentRequest,response:Response,setting:Setting,account:AccountModel,background_task: BackgroundTasks):
    try:
        logger.info(f"Started buy {payload.billerId} of {payload.amount} for {payload.receipient} from account {payload.accountNumber}")
        biller = productQuery.getBillerByBillerId(db=db,billerId=payload.billerId)
        if biller:
            params = {"GLCode":setting.bankone_cust_gl,"RetrievalReference": util.generateId(),"AccountNumber": account.accountNumber,"Amount": payload.amount,"Narration":f"{biller.billerName}/{payload.receipient}/N{payload.amount}"}
            debitAccount =await externalService.debitAccountByBankOne(setting=setting,params=params)
            if debitAccount['statuscode'] == str(status.HTTP_200_OK):
                background_task.add_task(routeBillToProvider,payload=payload,biller=biller,account=account,db=db,setting=setting)
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)  
async def billNameEnquiry(db:Session,payload:BillNameEnquiryRequest,response:Response,setting:Setting):
    try:
        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data={"customerName":"Adamu Chijioke Omolaja"})
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
async def getProducts(db:Session,response:Response,setting:Setting):
    try:
        products = await productQuery.getProduts(db=db)
        return ProductsResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=products)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ProductsResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
async def getProductByProductId(db:Session,response:Response,setting:Setting,productId:str):
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
async def getProductBillersByProductId(db:Session,response:Response,setting:Setting,productId:str):
    try:
        billers = await productQuery.getBillersByproductId(db=db,productId=productId)
        return ProductTypesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=billers)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ProductTypesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
async def getBillerPackages(db:Session,response:Response,setting:Setting,billerId:str):
    try:
        plans = await productQuery.getPackagesBillerId(db=db,billerId=billerId)
        return PackagesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=plans)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PackagesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
def routeBillToProvider(payload:BillPaymentRequest,biller:ProductTypeModel,account:AccountModel,db:Session,setting:Setting):
    try:
        return PackagesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
    except Exception as ex:
        logger.info(ex)
        return PackagesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
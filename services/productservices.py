
import logging
import json
from sqlalchemy.orm import Session
from models.model import *
from models.queries import productQuery,paymentQuery
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
async def buyAirtime(db:Session,payload:BillPaymentRequest,response:Response,setting:Setting,account:AccountModel,background_task: BackgroundTasks):
    try:
        logger.info(f"Started airtime purchase of N{payload.amount} for {payload.recipient} from account {payload.accountNumber} with biller {payload.billerId}  at {datetime.now()}")
        biller = productQuery.getBillerByBillerId(db=db,billerId=payload.billerId.upper(),billtype="airtime")
        if biller:
            logger.info(f"Biller {biller.billerName} is available for {payload.recipient} at {datetime.now()}")
            if biller.service_provider:
                logger.info(f"service provider {biller.service_provider.provider_name} has been configured for {biller.billerName} {payload.recipient}  at {datetime.now()}")
                transaction = TransactionModel(customer_id = account.customer_id,account_id = account.id,reference = f"{biller.billerId[:3]}-{util.generateUniqueTransactionId()}",recipient = payload.recipient,amount = payload.amount,product_id = biller.product_id,product_type_id = biller.id,service_provider_id = biller.service_provider_id,created_at =datetime.now(),)
                logTransaction = paymentQuery.create(db=db,model=transaction)
                if logTransaction:
                    logger.info(f"Started debit process for  {payload.recipient} with account {payload.accountNumber}  at {datetime.now()}")
                    params = {"GLCode":setting.bankone_cust_gl,"RetrievalReference": util.generateId(),"AccountNumber": account.accountNumber,"Amount": payload.amount,"Narration":f"{biller.billerName}/{payload.recipient}/N{payload.amount}"}
                    debitAccount = await externalService.debitAccountByBankOne(setting=setting,params=params)
                    logTransaction.debitStatus = debitAccount['statuscode']
                    logTransaction.debit_description = debitAccount['message']
                    logTransaction.updated_at = datetime.now()
                    if debitAccount['statuscode'] == str(status.HTTP_200_OK):
                        logger.info(f"Debit successful for  {payload.recipient} with account {payload.accountNumber} at {datetime.now()}")
                        logTransaction.debitReference = str(debitAccount['data'])
                        updatedTransaction = paymentQuery.create(db=db,model=logTransaction)
                        background_task.add_task(routeBillToProvider,payload=payload,transactionId=updatedTransaction.id,db=db,setting=setting)
                        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
                    elif debitAccount['statuscode'] == "V00":
                        logger.info(f"Debit pending for  {payload.recipient} with account {payload.accountNumber} at {datetime.now()}")
                        updatedTransaction = paymentQuery.create(db=db,model=logTransaction)
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=PENDING)
                    elif debitAccount['statuscode'] == "A00":
                        logger.info(f"Debit failed for  {payload.recipient} with account {payload.accountNumber} at {datetime.now()}")
                        logTransaction.statusCode = "C13"
                        logTransaction.statusMessage = TransactionStatusEnum.FAILED.value
                        updatedTransaction = paymentQuery.create(db=db,model=logTransaction)
                        #background_task.add_task(routeBillToProvider,payload=payload,transactionId=updatedTransaction.id,db=db,setting=setting)
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
                    else:
                        logTransaction.statusCode = "C13"
                        logTransaction.statusMessage = TransactionStatusEnum.FAILED.value
                        updatedTransaction = paymentQuery.create(db=db,model=logTransaction)
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=debitAccount['message'])
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNABLE)
            else:
                logger.info(f"service provider has not been configured for {biller.billerName} {payload.recipient}  at {datetime.now()}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDPROVIDER)
        else:
            logger.info(f"biller not found for {payload.recipient}  at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)   
async def buyDataPlan(db:Session,payload:BillPaymentRequest,response:Response,setting:Setting,account:AccountModel,background_task: BackgroundTasks):
    try:
        logger.info(f"Started buy {payload.billerId} of {payload.amount} for {payload.recipient} from account {payload.accountNumber}")
        biller = productQuery.getBillerByBillerId(db=db,billerId=payload.billerId,billtype="data")
        if biller:
            logger.info(f"Biller {biller.billerName} is available for {payload.recipient} at {datetime.now()}")
            if biller.service_provider:
                logger.info(f"service provider {biller.service_provider.provider_name} has been configured for {biller.billerName} {payload.recipient}  at {datetime.now()}")
                package = paymentQuery.getPackageByPackageCode(db=db,packageId=payload.packageId)
                if package:                    
                    logger.info(f"Package {package.short_description} {package.databundle} {package.productId} is available for {payload.recipient} at {datetime.now()}")
                    transaction = TransactionModel(customer_id = account.customer_id,account_id = account.id,reference = f"{biller.billerId[:3]}-{util.generateUniqueTransactionId()}",recipient = payload.recipient,amount = package.amount,product_id = biller.product_id,product_type_id = biller.id,service_provider_id = biller.service_provider_id,created_at =datetime.now(),)
                    logTransaction = paymentQuery.create(db=db,model=transaction)
                    if logTransaction:
                        logger.info(f"Started debit process for  {payload.recipient} with account {payload.accountNumber}  at {datetime.now()}")
                        params = {"GLCode":setting.bankone_cust_gl,"RetrievalReference": util.generateId(),"AccountNumber": account.accountNumber,"Amount": package.amount,"Narration":f"{biller.billerName}/{payload.recipient}/N{(int(package.amount)/100)}"}
                        debitAccount = await externalService.debitAccountByBankOne(setting=setting,params=params)
                        logTransaction.debitStatus = debitAccount['statuscode']
                        logTransaction.debit_description = debitAccount['message']
                        logTransaction.updated_at = datetime.now()
                        if debitAccount['statuscode'] == str(status.HTTP_200_OK):
                            logger.info(f"Debit successful for  {payload.recipient} with account {payload.accountNumber} at {datetime.now()}")
                            logTransaction.debitReference = str(debitAccount['data'])
                            updatedTransaction = paymentQuery.create(db=db,model=logTransaction)
                            background_task.add_task(routeBillToProvider,payload=payload,transactionId=updatedTransaction.id,db=db,setting=setting)
                            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
                        elif debitAccount['statuscode'] == "V00":
                            logger.info(f"Debit pending for  {payload.recipient} with account {payload.accountNumber} at {datetime.now()}")
                            updatedTransaction = paymentQuery.create(db=db,model=logTransaction)
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=PENDING)
                        elif debitAccount['statuscode'] == "A00":
                            logger.info(f"Debit failed for  {payload.recipient} with account {payload.accountNumber} at {datetime.now()}")
                            logTransaction.statusCode = "C13"
                            logTransaction.statusMessage = TransactionStatusEnum.FAILED.value
                            updatedTransaction = paymentQuery.create(db=db,model=logTransaction)
                            #background_task.add_task(routeBillToProvider,payload=payload,transactionId=updatedTransaction.id,db=db,setting=setting)
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
                        else:
                            logTransaction.statusCode = "C13"
                            logTransaction.statusMessage = TransactionStatusEnum.FAILED.value
                            updatedTransaction = paymentQuery.create(db=db,model=logTransaction)
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=debitAccount['message'])
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNABLE)
                else:
                    logger.info(f"Package not found for {payload.recipient}  at {datetime.now()}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Invalid Data Plan")
            else:
                logger.info(f"service provider has not been configured for {biller.billerName} {payload.recipient}  at {datetime.now()}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDPROVIDER)    
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)   
async def billPayment(db:Session,payload:BillPaymentRequest,response:Response,setting:Setting,account:AccountModel,background_task: BackgroundTasks):
    try:
        logger.info(f"Started buy {payload.billerId} of {payload.amount} for {payload.recipient} from account {payload.accountNumber}")
        biller = productQuery.getBillerByBillerId(db=db,billerId=payload.billerId)
        if biller:
            logger.info(f"Biller {biller.billerName} is available for {payload.recipient} at {datetime.now()}")
            if biller.service_provider:
                logger.info(f"service provider {biller.service_provider.provider_name} has been configured for {biller.billerName} {payload.recipient}  at {datetime.now()}")
                package = paymentQuery.getPackageByPackageCode(db=db,packageId=payload.packageId)
                if package:                    
                    logger.info(f"Package {package.short_description} {package.databundle} {package.productId} is available for {payload.recipient} at {datetime.now()}")
                    transaction = TransactionModel(customer_id = account.customer_id,account_id = account.id,reference = f"{biller.billerId[:3]}-{util.generateUniqueTransactionId()}",recipient = payload.recipient,amount = payload.amount,product_id = biller.product_id,product_type_id = biller.id,service_provider_id = biller.service_provider_id,created_at =datetime.now(),)
                    logTransaction = paymentQuery.create(db=db,model=transaction)
                    if logTransaction:
                        logger.info(f"Started debit process for  {payload.recipient} with account {payload.accountNumber}  at {datetime.now()}")
                        params = {"GLCode":setting.bankone_cust_gl,"RetrievalReference": util.generateId(),"AccountNumber": account.accountNumber,"Amount": payload.amount,"Narration":f"{biller.billerName}/{payload.recipient}/N{(int(payload.amount)/100)}"}
                        debitAccount = await externalService.debitAccountByBankOne(setting=setting,params=params)
                        logTransaction.debitStatus = debitAccount['statuscode']
                        logTransaction.debit_description = debitAccount['message']
                        logTransaction.updated_at = datetime.now()
                        if debitAccount['statuscode'] == str(status.HTTP_200_OK):
                            logger.info(f"Debit successful for  {payload.recipient} with account {payload.accountNumber} at {datetime.now()}")
                            logTransaction.debitReference = str(debitAccount['data'])
                            updatedTransaction = paymentQuery.create(db=db,model=logTransaction)
                            background_task.add_task(routeBillToProvider,payload=payload,transactionId=updatedTransaction.id,db=db,setting=setting)
                            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
                        elif debitAccount['statuscode'] == "V00":
                            logger.info(f"Debit pending for  {payload.recipient} with account {payload.accountNumber} at {datetime.now()}")
                            updatedTransaction = paymentQuery.create(db=db,model=logTransaction)
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=PENDING)
                        elif debitAccount['statuscode'] == "A00":
                            logger.info(f"Debit failed for  {payload.recipient} with account {payload.accountNumber} at {datetime.now()}")
                            logTransaction.statusCode = "C13"
                            logTransaction.statusMessage = TransactionStatusEnum.FAILED.value
                            updatedTransaction = paymentQuery.create(db=db,model=logTransaction)
                            #background_task.add_task(routeBillToProvider,payload=payload,transactionId=updatedTransaction.id,db=db,setting=setting)
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
                        else:
                            logTransaction.statusCode = "C13"
                            logTransaction.statusMessage = TransactionStatusEnum.FAILED.value
                            updatedTransaction = paymentQuery.create(db=db,model=logTransaction)
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=debitAccount['message'])
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=UNABLE)
                else:
                    logger.info(f"Package not found for {payload.recipient}  at {datetime.now()}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Invalid Data Plan")
            else:
                logger.info(f"service provider has not been configured for {biller.billerName} {payload.recipient}  at {datetime.now()}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDPROVIDER)    
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)  
async def billNameEnquiry(db:Session,payload:BillNameEnquiryRequest,response:Response,setting:Setting):
    try:
        logger.info(f"Started bill name enquiry {payload.billerId} of {payload.amount} for {payload.recipient} at {datetime.now()}")
        biller = productQuery.getBillerByBillerId(db=db,billerId=payload.billerId)
        if biller:
            if biller.service_provider:
                logger.info(f"Provider {biller.service_provider.provider_name} has been configured for  {payload.recipient} at {datetime.now()}")
                params ={"productId":payload.packageId,"customerId": payload.recipient,"serviceId" :str(biller.billerId)}
                enquiry = await externalService.billEnquriesServiceNew(serviceprovider=biller.service_provider,params=params)
                if enquiry['statuscode'] == str(status.HTTP_200_OK):
                    logger.info(f"Bill name enquiry successful for  {payload.recipient} at {datetime.now()}")
                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data={"customerName":enquiry['data']['customerName'],"customerAddress":enquiry['data']['customerAddress']})
                else:
                    logger.info(f"Bill name enquiry failed for  {payload.recipient} at {datetime.now()}")
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=enquiry['message'])
            else:
                logger.info(f"Provider has not been configured for  {payload.recipient} at {datetime.now()}")
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDPROVIDER)
        else:
            logger.info(f"Biller not found for  {payload.recipient} at {datetime.now()}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDBILLER)
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
async def routeBillToProvider(payload:BillPaymentRequest,transactionId:int,db:Session,setting:Setting):
    try:
        logger.info(f"Started processing transaction {transactionId} for  {payload.recipient} with account {payload.accountNumber} with at {datetime.now()}")
        params = {}
        transaction = paymentQuery.getTransactionById(db=db,transactionId=transactionId)
        if transaction:
            if transaction.product_type:
                logger.info(f"Transaction {transactionId} has biller {transaction.product_type.billerName} for  {payload.recipient} with account {payload.accountNumber} at {datetime.now()}")
                if transaction.provider:
                    logger.info(f"Transaction {transactionId} has provider {transaction.provider.provider_name} for  {payload.recipient} with account {payload.accountNumber} at {datetime.now()}")
                    if transaction.debitStatus == "200":
                        logger.info(f"Transaction {transactionId} has successful debit for  {payload.recipient} with account {payload.accountNumber} at {datetime.now()}")
                        params['amount'] = str(int(int(payload.amount)/100))
                        params['recipient'] = payload.recipient
                        params['serviceId'] = transaction.product_type.billerId
                        params['channelCode'] = '01'
                        params['operator'] = transaction.product_type.billerName
                        params['requestId'] = transaction.reference
                        params['date'] = datetime.now().isoformat()
                        params['accountNo'] = transaction.account.accountNumber
                        params['customerName'] = payload.customerName
                        params['customerAddress'] =payload.customerAddress
                        if payload.packageId:
                            params['productId'] = payload.packageId
                        purchase = await externalService.purchaseServiceNew(biller=transaction.product_type,setting=setting,serviceprovider=transaction.provider,payload=params)
                        transaction.providerStatus = purchase['statuscode']
                        transaction.providerDescription = purchase['message']
                        transaction.updated_at = datetime.now()
                        if purchase['statuscode'] == str(status.HTTP_200_OK):
                            logger.info(f"Vending successful for  {payload.recipient} with account {payload.accountNumber} with biller {transaction.product_type.billerName} at {datetime.now()}")
                            transaction.statusCode = "00"
                            transaction.statusMessage = SUCCESS
                            transaction.providerReference = purchase['data']['confirmCode']
                            if transaction.product_type.billerType.lower() == "electricity":
                                transaction.customerName = purchase['data']['customerName'] if 'customerName' in purchase['data'] else None
                                transaction.token = purchase['data']['token'] if 'token' in purchase['data'] else None
                                transaction.configureToken = purchase['data']['configureToken'] if 'configureToken' in purchase['data'] else None
                                transaction.unit = purchase['data']['unit'] if 'unit' in purchase['data'] else None
                                transaction.unitType = purchase['data']['unitType'] if 'unitType' in purchase['data'] else None
                                message=f"Your {transaction.product_type.billerName} purchase was successful. Token {transaction.token}. Thank you for choosing Rayyan MFB. Dial *5113*amount# to buy airtime."
                                paramsMsg =[{'AccountNumber':transaction.account.accountNumber,'To':util.formatPhoneFull(payload.msisdn),"AccountId": account.customerNumber,'Body':message,'ReferenceNo':util.generateUniqueId()}]
                                await externalService.sendSms(setting=setting,params=paramsMsg)
                        else:
                            transaction.statusCode = purchase['statuscode']
                            transaction.statusMessage = purchase['message']
                        updatedTransaction = paymentQuery.create(db=db,model=transaction)
                    return PackagesResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
    except Exception as ex:
        logger.info(ex)
        return PackagesResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
    finally:
        db.close()
async def transactionRequery(db: Session,transaction:TransactionModel,setting:Setting):
    response = BaseResponse(statusCode= "C001",statusDescription= "Processing")
    logger.info(f"Started TSQ for transaction {transaction.recipient} with reference {transaction.reference} with status {transaction.statusCode} and created at {transaction.created_at}  at {str(datetime.now())}")
    try:
        if transaction.debitStatus == "200":
            logger.info(f"Started Requerying for Past transactions {transaction.recipient} with status {transaction.statusCode} at transaction ID {str(transaction.id)}")
            params={"loginId":transaction.provider.login_id,"key":transaction.provider.service_key,"requestId":transaction.reference}
            res = util.http(url=f"{transaction.provider.provider_url}requery",params=params)
            requeryBillResponse = res.json()
            if requeryBillResponse:
                if requeryBillResponse["statusCode"] == "00":
                    logger.info(f"TSQ is still pending response for {util.formatPhone(msisdn=transaction.recipient)} with reference {transaction.reference}........ at {datetime.now()}")
                    transaction.statusCode = "200"
                    transaction.statusMessage = TransactionStatusEnum.SUCCESS.value
                    transaction.providerStatus = requeryBillResponse["statusCode"]
                    transaction.providerDescription = requeryBillResponse["statusDescription"]
                    transaction.updated_at = datetime.now()
                    if requeryBillResponse["data"]:
                        transaction.providerReference = requeryBillResponse["data"]["confirmCode"]
                        if requeryBillResponse["data"]["token"]:
                            transaction.token = requeryBillResponse["data"]["token"]
                            transaction.configureToken = requeryBillResponse["data"]["configureToken"]
                            transaction.unit = requeryBillResponse["data"]["units"]
                            transaction.unitType = requeryBillResponse["data"]["unitType"]
                            transaction.customerAddress = requeryBillResponse["data"]["customerAddress"]
                            transaction.customerName = requeryBillResponse["data"]["customerName"]
                            message=f"Your {transaction.product_type.billerName} purchase was successful. Token {transaction.token}. Thank you for choosing Rayyan MFB. Dial *5113*amount# to buy airtime."
                            paramsMsg =[{'AccountNumber':transaction.account.accountNumber,'To':util.formatPhoneFull(transaction.customer.phonenumber),"AccountId": transaction.account.customerNumber,'Body':message,'ReferenceNo':util.generateUniqueId()}]
                            await externalService.sendSms(setting=setting,params=paramsMsg)
                    updatedTransaction = paymentQuery.create(db=db,model=transaction)
                    response.statusCode = "00"
                    response.statusDescription = TransactionStatusEnum.SUCCESS.value
                    return response
                elif requeryBillResponse["statusCode"] == "C001":
                    logger.info(f"TSQ failed for {util.formatPhone(msisdn=transaction.recipient)} with reference {transaction.reference}........ at {datetime.now()}")
                    transaction.statusCode = requeryBillResponse["statusCode"]
                    transaction.statusMessage = requeryBillResponse["statusDescription"]
                    transaction.providerStatus = requeryBillResponse["statusCode"]
                    transaction.providerDescription = requeryBillResponse["statusDescription"]
                    transaction.updated_at = datetime.now()
                    response.statusCode = "C001"
                    response.statusDescription =TransactionStatusEnum.PENDING.value
                else:
                    logger.info(f"TSQ failed for {util.formatPhone(msisdn=transaction.recipient)} with reference {transaction.reference}........ at {datetime.now()}")
                    transaction.statusCode = requeryBillResponse["statusCode"]
                    transaction.statusMessage = requeryBillResponse["statusDescription"]
                    transaction.providerStatus = requeryBillResponse["statusCode"]
                    transaction.providerDescription = requeryBillResponse["statusDescription"]
                    transaction.updated_at = datetime.now()
                    response.statusCode = requeryBillResponse["statusCode"]
                    response.statusDescription = requeryBillResponse["statusDescription"]
            else:
                logger.info(f"TSQ failed for {util.formatPhone(msisdn=transaction.recipient)} with reference {transaction.reference}........ at {datetime.now()}")
                response.statusCode = "C001"
                response.statusDescription = TransactionStatusEnum.PENDING.value
        elif transaction.debitStatus == "V00":
            logger.info(f"Transaction {transaction.recipient} with reference {transaction.reference} has pending debit status for transaction ID {str(transaction.id)} at {datetime.now()}")
            requeryResponse = externalService.requeryDebitAccountByBankOne(setting=setting,params={"RetrievalReference": transaction.debitReference,"TransactionDate": transaction.created_at.strftime("%Y-%m-%dT%H:%M:%S"),"Amount": str(int(transaction.amount)*100),})
            if requeryResponse['statuscode'] == str(status.HTTP_200_OK):
                logger.info(f"Debit successful for  {transaction.recipient} with account {transaction.account.accountNumber} at {datetime.now()} for transaction ID {str(transaction.id)}")
                transaction.debitStatus = "00"
                transaction.debit_description = requeryResponse['message']
                transaction.updated_at = datetime.now()
            elif requeryResponse['statuscode'] == "V00":
                logger.info(f"Debit still pending for  {transaction.recipient} with account {transaction.account.accountNumber} at {datetime.now()} for transaction ID {str(transaction.id)}")
                transaction.debitStatus = "V00"
                transaction.debit_description = requeryResponse['message']
                transaction.updated_at = datetime.now()
                response.statusCode = "V00"
                response.statusDescription = PENDING
            else:
                logger.info(f"Debit failed for  {transaction.recipient} with account {transaction.account.accountNumber} at {datetime.now()} for transaction ID {str(transaction.id)}")
                transaction.statusCode = "C13"
                transaction.statusMessage = TransactionStatusEnum.FAILED.value
                transaction.debitStatus = "C13"
                transaction.debit_description = requeryResponse['message']
                transaction.providerStatus = "C13"
                transaction.providerDescription = "Transaction failed due to unsuccessful debit"
                transaction.updated_at = datetime.now()
                response.statusCode = "C13"
                response.statusDescription = TransactionStatusEnum.FAILED.value
        else:
            logger.info(f"Transaction {transaction.recipient} with reference {transaction.reference} has debit status {transaction.debitStatus} for transaction ID {str(transaction.id)} at {datetime.now()}")
            transaction.statusCode = "C13"
            transaction.statusMessage = TransactionStatusEnum.FAILED.value
            transaction.providerStatus = "C13"
            transaction.providerDescription = "Transaction failed due to unsuccessful debit"
            transaction.updated_at = datetime.now()
            response.statusCode = "C13"
            response.statusDescription = TransactionStatusEnum.FAILED.value
    except Exception as ex:
        logger.info(f"Error requerying transactions {transaction.recipient} at {str(datetime.now())} with message {str(ex)}")
    paymentQuery.create(db=db,model=transaction)
    return response
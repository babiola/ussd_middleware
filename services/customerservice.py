
import logging
import json
from sqlalchemy.orm import Session
from models.model import *
from models.queries import customerQuery
from datetime import datetime,timedelta
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.customer import *
from schemas.base import BaseResponse, BvnRequest, OpenAccountRequest,EnrolAccountRequest
from services import externalService
from utils import redisUtil
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)
logger = logging.getLogger(__name__)
async def profile(
        request: Request,
        response: Response,
        setting: Setting,
        db: Session,
        msisdn: str,
        background_task: BackgroundTasks,):
    try:
        customer = customerQuery.getCustomerByMsisdn(db=db,msisdn=msisdn)
        if customer:
            if customer.active and customer.isUssdEnrolled and customer.blacklisted is False:
                return CustomerResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=Customer.model_validate(customer))
            elif customer.blacklisted:
                #response.status_code = status.HTTP_401_UNAUTHORIZED
                return CustomerResponse(statusCode=str(status.HTTP_200_OK),statusDescription=BLACKLISTED,data=Customer.model_validate(customer))
            elif not customer.isUssdEnrolled:
                #response.status_code = status.HTTP_401_UNAUTHORIZED
                return CustomerResponse(statusCode=str(status.HTTP_200_OK),statusDescription=NOTENROLLED,data=Customer.model_validate(customer))
            else:
                #response.status_code = status.HTTP_401_UNAUTHORIZED
                return CustomerResponse(statusCode=str(status.HTTP_200_OK),statusDescription=INACTIVE,data=Customer.model_validate(customer))
        response.status_code = status.HTTP_404_NOT_FOUND
        return CustomerResponse(statusCode=str(status.HTTP_404_NOT_FOUND),statusDescription=NOTFOUND) 
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return CustomerResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def getBvnDetails(payload:BvnRequest,response:Response,setting:Setting):
    try:
        logger.info(f"Checking BVN: {payload.bvn} for {payload.msisdn} with DOB: {payload.dob}")
        checkbvn = await externalService.checkBvn(setting=setting,bvn=payload.bvn,bvnType='advance')
        if checkbvn['statuscode'] == str(status.HTTP_200_OK):
            if util.formatPhoneFull(payload.msisdn) == util.formatPhoneFull(checkbvn['data']['phoneNumber1']):
                if util.validateBVNDateOfBirth(checkbvn['data']['dateOfBirth'],payload.dob):
                    savedBvn = await redisUtil.set_cache(key=f"bvn:{payload.bvn}", value=json.dumps(checkbvn['data']), ttl=timedelta(days=1))
                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=checkbvn['message'],data=checkbvn['data'])
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Record Mismatched")
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST 
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Phone Number Mismatched")
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=checkbvn['message'])
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
async def open_account(db:Session,payload:OpenAccountRequest,response:Response,setting:Setting,accountType:AccountLevelEnum):
    try:
        if payload.pin and payload.pin.isdigit() and len(payload.pin) == 4:
            retrieveBvn = await redisUtil.get_cache(key=f"bvn:{payload.bvn}")
            if retrieveBvn:
                retrieveBvn = json.loads(retrieveBvn)
                if util.formatPhoneFull(payload.msisdn) == util.formatPhoneFull(retrieveBvn['phoneNumber1']):
                    if util.validateBVNDateOfBirth(retrieveBvn['dateOfBirth'],payload.dob):
                        params = {
                            "TransactionTrackingRef":util.generateUniqueId(),
                            "AccountOpeningTrackingRef": util.formatPhoneShort(retrieveBvn['phoneNumber1']),
                            "CustomerId":"",
                            "ProductCode": "101",
                            "FirstName":retrieveBvn['firstName'],
                            "LastName":retrieveBvn['lastName'],
                            "OtherNames": f"{retrieveBvn['middleName']}",
                            "BVN":retrieveBvn['bvn'],
                            "PhoneNo":retrieveBvn['phoneNumber1'],
                            "Gender": 1 if retrieveBvn['gender'].lower()=="male" else 0,
                            "PlaceOfBirth":retrieveBvn['lgaOfOrigin'],
                            "DateOfBirth":retrieveBvn['dateOfBirth'],
                            "Address":retrieveBvn['residentialAddress'],
                            "AccountOfficerCode": "002",
                            "Email":'info@rayyan.com' if retrieveBvn.get('email','info@rayyan.com') == '' else retrieveBvn.get('email','info@rayyan.com'),
                            "NotificationPreference": 0,
                            "TransactionPermission": "0",
                            "AccountTier": "3"} if accountType == AccountLevelEnum.TIER3 else {
                            "TransactionTrackingRef":util.generateUniqueId(),
                            "AccountOpeningTrackingRef": util.formatPhoneShort(retrieveBvn['phoneNumber1']),
                            "ProductCode": "101",
                            "FirstName":retrieveBvn['firstName'],
                            "LastName":retrieveBvn['lastName'],
                            "OtherNames": f"{retrieveBvn['middleName']}",
                            "BVN":retrieveBvn['bvn'],
                            "NationalIdentityNo":retrieveBvn['nin'],
                            "PhoneNo": retrieveBvn['phoneNumber1'],
                            "Gender":retrieveBvn['gender'],
                            "PlaceOfBirth":retrieveBvn['lgaOfOrigin'],
                            "DateOfBirth": retrieveBvn['dateOfBirth'],
                            "Address":retrieveBvn['residentialAddress'],
                            "AccountTier": "3",
                            "CustomerImage":retrieveBvn['base64Image'],
                            "AccountOfficerCode": "002",
                            "HasSufficientInfoOnAccountInfo": True,
                            "Email":'info@rayyan.com' if retrieveBvn.get('email','info@rayyan.com') == '' else retrieveBvn.get('email','info@rayyan.com'),
                            "NotificationPreference":0,
                            "TransactionPermission": "0",
                            "AccountInformationSource": 0,
                            "NextOfKinPhoneNo": "",
                            "NextOfKinName": "",
                            "ReferralPhoneNo": "",
                            "ReferralName": "",
                            "OtherAccountInformationSource": "",
                            "CustomerSignature": "",
                            "IdentificationImage": retrieveBvn['base64Image']
                        }
                        createAccount = await externalService.openAccount(setting=setting,params=params)
                        logger.info(createAccount)
                        if createAccount['statuscode'] == str(status.HTTP_200_OK):
                            customer = CustomerModel(
                                    firstname = retrieveBvn['firstName'],
                                    lastname = retrieveBvn['lastName'],
                                    middlename = retrieveBvn['middleName'],
                                    customerNumber = createAccount["data"]["CustomerID"],
                                    dob = retrieveBvn['dateOfBirth'],
                                    email =retrieveBvn.get('email',''),
                                    phonenumber = util.formatPhoneFull(payload.msisdn),
                                    bvn = payload.bvn,
                                    nin = retrieveBvn['nin'],
                                    pin=util.get_password_hash(payload.pin),
                                    gender = True if retrieveBvn['gender'] =="Male" else False,
                                    active = True,
                                    isUssdEnrolled =True,
                                    blacklisted = False,
                                    indemnitySigned = False,
                                    accounts = [
                                        AccountModel(
                                                accountNumber = createAccount["data"]["AccountNumber"],
                                                customerNumber = createAccount["data"]["CustomerID"],
                                                active = True,
                                                isDefaultPayment = True,
                                                blacklisted = False,
                                                balance = "0",
                                                level = AccountLevelEnum.TIER3
                                    )],
                                    created_at = datetime.now(),
                                    updated_at = datetime.now())
                            savecustomer = customerQuery.create_account(db=db,user=customer)
                            if savecustomer:
                                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=createAccount['message'],data=createAccount["data"]["AccountNumber"])
                            else:
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=createAccount['message'])
                        else:
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=createAccount['message'])
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Record Mismatched")
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST 
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Phone Number Mismatched")
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="PIN must be 4 digits and numeric")
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)
async def create_customer(db:Session,request:Request,payload:EnrolAccountRequest,response:Response,setting:Setting,background_task: BackgroundTasks):
    try:
        customer = await externalService.getCustomerViaAccount(setting=setting,account=payload.accountNumber)
        logger.info(customer)
        if customer['statuscode'] == str(status.HTTP_200_OK):
            if util.formatPhoneFull(payload.msisdn) == util.formatPhoneFull(customer['data']['phoneNumber']):
                if customer['data']['BVN'] == payload.bvn:
                    await redisUtil.set_cache(key=f"enrollment:{payload.accountNumber}", value=json.dumps(customer['data']), ttl=timedelta(days=1))
                    checkCustomer = customerQuery.getCustomerByMsisdn(db=db,msisdn=util.formatPhoneFull(payload.msisdn))
                    if checkCustomer and checkCustomer.active and checkCustomer.isUssdEnrolled and checkCustomer.blacklisted is False:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="Customer already enrolled and active")
                    elif checkCustomer and checkCustomer.isUssdEnrolled is False:
                        logger.info(f"Customer {checkCustomer.customerNumber} is blacklisted")
                        checkCustomer.active = True
                        checkCustomer.isUssdEnrolled = True
                        checkCustomer.blacklisted = False
                        checkCustomer.updated_at = datetime.now()
                        checkCustomer.hasPin = True
                        checkCustomer.pin = util.get_password_hash(payload.pin)
                        saved = customerQuery.create(db=db,model=checkCustomer)
                        if saved:
                            await redisUtil.delete_cache(key=f"account:{payload.msisdn}")
                            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
                        else:
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
                    else:
                        logger.info(f"Creating new customer with account {payload.accountNumber}")
                        account = next((account for account in customer['data']['Accounts'] if account['NUBAN'] == payload.accountNumber), None)
                        newcustomer = CustomerModel(
                                    firstname = customer['data']['name'].split(' ')[1] if len(customer['data']['name'].split(' ')) > 1 else customer['data']['name'].split(' ')[0],
                                    lastname = customer['data']['name'].split(' ')[0] if len(customer['data']['name'].split(' ')) > 1 else "",
                                    customerNumber = customer['data']["customerID"],
                                    dob = customer['data']['dateOfBirth'],
                                    email = customer['data']['email'],
                                    phonenumber = util.formatPhoneFull(payload.msisdn),
                                    bvn = payload.bvn,
                                    hasPin = True,
                                    pin=util.get_password_hash(payload.pin),
                                    gender = True if customer['data']['gender'].lower() =="male" else False,
                                    active = True,
                                    isUssdEnrolled =True,
                                    blacklisted = False,
                                    indemnitySigned = False,
                                    accounts = [
                                        AccountModel(
                                                accountNumber = account['NUBAN'] if account else payload.accountNumber,
                                                customerNumber = account['customerID'] if account else customer['data']["customerID"],
                                                active = True,
                                                isDefaultPayment = True,
                                                blacklisted = False,
                                                balance = account['withdrawableAmount'] if account else "0",
                                                level = AccountLevelEnum.TIER3
                                    )],
                                    created_at = datetime.now(),
                                    updated_at = datetime.now())
                        saved = customerQuery.create(db=db,model=newcustomer)
                        if saved:
                            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
                        else:
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=FAILED)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST 
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=BVNMISMATCH)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST 
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=PHONENUMBERMISMATCH)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=customer['message'])
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)   
async def balance(account:AccountModel,request: Request,response: Response,setting: Setting,db: Session,background_task: BackgroundTasks):
    try:
        checkBalance = await externalService.accountBalance(setting=setting,account=account.accountNumber)
        if checkBalance:
            if checkBalance['statuscode'] == str(status.HTTP_200_OK):
                account.balance = checkBalance['data']['WithdrawableBalance'] if 'WithdrawableBalance' in checkBalance['data'] else "0"
                account.updated_at = datetime.now()
                background_task.add_task(customerQuery.create, db=db, model=account)
                logger.info(f"Account Balance for {account.accountNumber} is {account.balance}")
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=checkBalance['data']['WithdrawableBalance'])
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=checkBalance['message'])
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=BALANCEERROR)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST), statusDescription=SYSTEMBUSY,)

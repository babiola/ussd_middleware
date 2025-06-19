
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
from schemas.admin import Admin
from services import externalService
from utils import redisUtil
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
            if customer.active and customer.isUssdEnrolled and customer.blacklisted is False:
                return CustomerResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=Customer.model_validate(customer))
            elif customer.blacklisted:
                response.status_code = status.HTTP_403_FORBIDDEN
                return CustomerResponse(statusCode=str(status.HTTP_403_FORBIDDEN),statusDescription=BLACKLISTED)
            elif not customer.isUssdEnrolled:
                response.status_code = status.HTTP_403_FORBIDDEN
                return CustomerResponse(statusCode=str(status.HTTP_403_FORBIDDEN),statusDescription=NOTENROLLED)
            else:
                response.status_code = status.HTTP_403_FORBIDDEN
                return CustomerResponse(statusCode=str(status.HTTP_403_FORBIDDEN),statusDescription=INACTIVE)
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
async def create_customer(db:Session,payload:BvnRequest,response:Response,setting:Setting,accountType:AccountLevelEnum):
    try:
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
                    createAccount = externalService.openAccount(setting=setting,params=params)
                    logger.info(createAccount)
                    if createAccount['statuscode'] == str(status.HTTP_200_OK):
                        customer = CustomerModel(
                                firstname = retrieveBvn['firstName'],
                                lastname = retrieveBvn['lastName'],
                                middlename = retrieveBvn['middleName'],
                                customerNumber = createAccount["details"]["CustomerID"],
                                dob = retrieveBvn['lgaOfOrigin'],
                                email = retrieveBvn['email'],
                                phonenumber = util.formatPhoneFull(payload.msisdn),
                                bvn = payload.bvn,
                                nin = retrieveBvn['nin'],
                                gender = True if retrieveBvn['gender'] =="Male" else False,
                                active = True,
                                isUssdEnrolled =False,
                                blacklisted = False,
                                indemnitySigned = False,
                                accounts = [
                                    AccountModel(
                                            accountNumber = createAccount["details"]["AccountNumber"],
                                            customerNumber = createAccount["details"]["CustomerID"],
                                            active = True,
                                            isDefaultPayment = True,
                                            blacklisted = False,
                                            balance = "0",
                                            level = AccountLevelEnum.TIER3
                                )],
                                created_at = datetime.now(datetime.timezone.utc),
                                updated_at = datetime.now(datetime.timezone.utc))
                        savecustomer = customerQuery.create_account(db=db,user=customer)
                        if savecustomer:
                            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=createAccount['message'],data=createAccount["details"]["AccountNumber"])
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

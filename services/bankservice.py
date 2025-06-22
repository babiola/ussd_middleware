
import logging
from sqlalchemy.orm import Session
from models.model import *
from models.queries import customerQuery
from datetime import datetime,timedelta
from utils import util
from schemas.setting import Setting
from utils.constant import *
from schemas.bank import *
from schemas.base import *
from services import externalService
from fastapi import (
    status,
    Response,
    Request,
    BackgroundTasks,
)
from models.bank import ALLBANK

logger = logging.getLogger(__name__)

async def banks(
        request: Request,
        response: Response,
        setting: Setting,search:str=None):
    try:
        if search:
            banks = filter(lambda bank:len(bank.Code) > 3 and bank.Name.lower().startswith(search.lower()),ALLBANK.banks)
        else:
            banks = filter(lambda bank:len(bank.Code) > 3,ALLBANK.banks)
        return BanksResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=banks)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BanksResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def possibleBank(request:Request,response:Response,setting:Setting,payload:TransferPossibleRequest):
    try:
        if ALLBANK:
            likelyBanks = filter(lambda bank:len(bank.Code) == 3 and isPossibleBank(bank=bank,account=payload.receipient),ALLBANK.banks)
            logger.info(likelyBanks)
            if likelyBanks:
                return BanksResponse(statusCode= str(status.HTTP_200_OK),statusDescription=SUCCESS,data=likelyBanks)
            else:
                return BanksResponse(statusCode= str(status.HTTP_200_OK),statusDescription= SUCCESS,data=ALLBANK.banks,)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BanksResponse(statusCode= str(status.HTTP_400_BAD_REQUEST),statusDescription= FAILED)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BanksResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def bankNameEnquiry(request:Request,response: Response, setting: Setting, db: Session, payload: TransferNameEnquiryRequest):
    try:
        logger.info(f"started name enquiry for bank {payload.receipient} with account {payload.receipient}")
        if payload.bankcode:
            selectedBank = util.get_bank_by_code(bankcode=payload.bankcode, banks=ALLBANK.banks)
            if selectedBank:
                params = {
                    "AccountNumber": payload.receipient,
                    "BankCode": payload.bankcode,
                }
                customerEnquiry =await externalService.accountEnquiryInterByBankOne(params=params,setting=setting)
                if customerEnquiry and customerEnquiry['statuscode'] == str(status.HTTP_200_OK):
                    return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=customerEnquiry["data"]["Name"],)
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=customerEnquiry["message"],)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription="INVALID BANK",)
        else:
            params = {"AccountNo": payload.receipient}
            customerEnquiry =await externalService.accountEnquiryIntraByBankOne(params=params,setting=setting)
            if customerEnquiry and customerEnquiry['statuscode'] == str(status.HTTP_200_OK):
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=customerEnquiry["data"]["Name"],)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=customerEnquiry["message"],)
            
            customer = customerQuery.getCustomerByMsisdn(db=db,msisdn=util.formatPhoneFull(payload.receipient))
            if customer:
                return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=f"{customer.firstname} {customer.lastname}",)
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INVALIDACCOUNT,)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def bankTransferIntra(request:Request,account:AccountModel,response: Response, setting: Setting, db: Session, payload: TransferRequest,background_task: BackgroundTasks):
    try:
        logger.info(f"started intra bank transfer to account {payload.receipient}")
        params = {"FromAccountNumber": account.accountNumber,"Amount":payload.amount,"ToAccountNumber":payload.receipient,"RetrievalReference": util.generateId(),"Narration": f"USSD-TRF/{util.mask_email(payload.receipient)}",}
        debitAccount =await externalService.accountTransferIntraByBankOne(setting=setting,params=params)
        if debitAccount['statuscode'] == str(status.HTTP_200_OK):
            #background_task.add_task(routeBillToProvider,payload=payload,biller=biller,account=account,db=db,setting=setting)
            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
        elif debitAccount['statuscode'] == "51":
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=debitAccount['message'])
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
async def bankTransferInter(request:Request,account:AccountModel,response: Response, setting: Setting, db: Session, payload: TransferRequest,background_task: BackgroundTasks):
    try:
        logger.info(f"started payment transfer for bank {payload.receipient} with account {payload.msisdn}")
        params = {
             "Amount":payload.amount,
             "AppzoneAccount":"",
            "Payer":f"{account.customer.lastname} {account.customer.firstname}",
            "PayerAccountNumber" :account.accountNumber,
            "ReceiverAccountNumber":payload.receipient,
            "ReceiverAccountType":"",
            "ReceiverBankCode":payload.bankcode,
            "ReceiverPhoneNumber":"",
            "ReceiverName":payload.receipientName,
            "ReceiverBVN":"",
            "ReceiverKYC":"",
            "Narration":f"USSD-TRF/{util.mask_email(payload.receipient)}",
            "TransactionReference":util.generateId(),
            "NIPSessionID":"",}
        debitAccount = await externalService.accountTransferInterByBankOne(setting=setting,params=params)
        if debitAccount['statuscode'] == str(status.HTTP_200_OK):
            #background_task.add_task(routeBillToProvider,payload=payload,biller=biller,account=account,db=db,setting=setting)
            return BaseResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS)
        elif debitAccount['statuscode'] == "51":
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=INSUFFICIENTFUND)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=debitAccount['message'])
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def isPossibleBank(account:str,bank:Bank):
    logger.info(f"{account} bank {bank.Code} with code {bank.Name}")
    return str(util.generateCheckDigit(account[:9], bank.Code)) == account[9]

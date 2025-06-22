
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

def banks(
        request: Request,
        response: Response,
        setting: Setting):
    try:
        banks = filter(lambda bank:len(bank.Code) > 3,ALLBANK.banks)
        return BanksResponse(statusCode=str(status.HTTP_200_OK),statusDescription=SUCCESS,data=banks)
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BanksResponse(statusCode=str(status.HTTP_400_BAD_REQUEST),statusDescription=SYSTEMBUSY,)
def possibleBank(request:Request,response:Response,setting:Setting,payload:TransferPossibleRequest):
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
def isPossibleBank(account:str,bank:Bank):
    logger.info(f"{account} bank {bank.Code} with code {bank.Name}")
    return str(util.generateCheckDigit(account[:9], bank.Code)) == account[9]
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
def accountTransferPayment(request:Request,user:CustomerModel,response: Response, setting: Setting, db: Session, payload: TransferRequest):
    try:
        logger.info(
            f"started payment transfer for bank {payload.destinationBankCode} with account {payload.destinationAccountNumber}"
        )
        bank = transferQuery.getBankByCBNCode(db=db,code=payload.destinationBankCode)
        if bank:
            walletAccount = transferQuery.getWalletAccountByAccountNumber(db=db,wallet=payload.senderAccountNumber)
            if walletAccount:
            #if int(walletAccount.balance) < int(payload.amount):
                #walletAccount.balance_before = walletAccount.balance
                #walletAccount.balance = str(int(walletAccount.balance) - int(payload.amount))
                # create transaction 
                transactionId = f"TF{util.generateId()}"
                transaction = TransactionModel(
                    user_id=user.id,
                    transactionId=transactionId,
                    amount=payload.amount,
                    product="TRANSFER",
                    isDebit=True,
                    customerBillerId=payload.destinationBankCode,
                    recipientAccountNumber=payload.destinationAccountNumber,
                    recipientBank=bank.shortname,
                    recipientName=payload.destinationAccountNumber,
                    senderName=f"{user.lastname} {user.firstname}",
                    recipientId=payload.destinationAccountNumber,
                    remarks=f"TRF/{payload.remark if payload.remark else  payload.destinationAccountNumber } {payload.amount}",# f"commission on {transaction.transactionType}",
                    reference=transactionId,
                    transactionType="TRANSFER",
                    transactionStatus=PENDING,
                    owner_id=user.id,
                    updated_at=datetime.now(),
                    created_at=datetime.now(),
                )
                createdTransaction = paymentQuery.create_transaction(
                    db=db, transaction=transaction
                )
                if createdTransaction:
                    resp ={}
                    if payload.destinationBankCode == setting.focus_code:
                        resp = externalService.accountTransferIntraPaymentByBankOne(
                            amount=payload.amount,senderName=f"{user.lastname} {user.firstname}",
                            senderAccount=payload.senderAccountNumber,destinationAccountNumber=payload.destinationAccountNumber,
                            destinationAccountName=payload.destinationAccountName,destinationBankCode=payload.destinationBankCode,
                            setting=setting,
                            transactionId=transactionId,
                            transType="LOCALFUNDTRANSFER",
                            remark=f"Trf/{payload.remark if payload.remark else  payload.destinationAccountNumber }/{payload.amount}")
                    else:
                        if setting.trf_lookup_provider.upper() == "ISW":
                            resp = externalService.accountTransferInterPaymentByInterSwitch(
                            amount=payload.amount,senderName=f"{user.lastname} {user.firstname}",
                            senderAccount=payload.senderAccountNumber,destinationAccountNumber=payload.destinationAccountNumber,
                            destinationAccountName=payload.destinationAccountName,destinationBankCode=payload.destinationBankCode,
                            setting=setting,
                            transactionId=transactionId,
                            transType="INTERBANKTRANSFER",
                            remark=f"Trf/{payload.remark if payload.remark else  payload.destinationAccountNumber }/{payload.amount}")
                        elif setting.trf_lookup_provider.upper() == "BKONE":
                            resp = externalService.accountTransferInterPaymentByBankOne(
                            amount=payload.amount,senderName=f"{user.lastname} {user.firstname}",
                            senderAccount=payload.senderAccountNumber,destinationAccountNumber=payload.destinationAccountNumber,
                            destinationAccountName=payload.destinationAccountName,destinationBankCode=payload.destinationBankCode,
                            setting=setting,
                            transactionId=transactionId,
                            transType="INTERBANKTRANSFER",
                            remark=f"Trf/{payload.remark if payload.remark else  payload.destinationAccountNumber }/{payload.amount}")
                        else:
                            resp = externalService.accountTransferInterPaymentByBankOne(
                            amount=payload.amount,senderName=f"{user.lastname} {user.firstname}",
                            senderAccount=payload.senderAccountNumber,destinationAccountNumber=payload.destinationAccountNumber,
                            destinationAccountName=payload.destinationAccountName,destinationBankCode=payload.destinationBankCode,
                            setting=setting,
                            transactionId=transactionId,
                            transType="INTERBANKTRANSFER",
                            remark=f"Trf/{payload.remark if payload.remark else  payload.destinationAccountNumber }/{payload.amount}")
                    if resp:
                        createdTransaction.btcode= resp["code"]
                        createdTransaction.provider = "BankOne"
                        createdTransaction.reference = resp["mRef"]
                        createdTransaction.transactionStatus = resp["message"]
                        updatedTransaction = paymentQuery.create_transaction(db=db,transaction=createdTransaction)
                        if updatedTransaction:
                            if resp["code"] == "00":
                                response.status_code = status.HTTP_200_OK
                                return BaseResponse(
                                    
                                    statusCode=str(status.HTTP_200_OK),
                                    statusDescription=SUCCESS
                                )
                            elif resp["code"] =="BT00":
                                    # query transaction status
                                logger.info("Log for requery later")
                                logger.info(f"Transaction is in {resp['code']} state and will be requeried")
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(
                                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                                    statusDescription=resp["message"]
                                )
                            else:
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return BaseResponse(
                                    statusCode=str(status.HTTP_400_BAD_REQUEST),
                                    statusDescription=resp["message"]
                                )
                        else:
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return BaseResponse(
                            
                                statusCode=str(status.HTTP_400_BAD_REQUEST),
                                statusDescription=resp["message"]
                            )
                    else:
                        response.status_code = status.HTTP_400_BAD_REQUEST 
                        return BaseResponse(
                        
                                statusCode=str(status.HTTP_400_BAD_REQUEST),
                                statusDescription=PENDING,
                        
                        )
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return BaseResponse(
                        
                                statusCode=str(status.HTTP_400_BAD_REQUEST),
                                statusDescription=SYSTEMBUSY,
                        
                        )
            #else:
                #response.status_code = status.HTTP_400_BAD_REQUEST
                #return BaseResponse(
                #        
                #                statusCode=str(status.HTTP_400_BAD_REQUEST),
                #                statusDescription=INSUFFICIENTFUND,
                #        
                #        )
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return BaseResponse(
                        
                                statusCode=str(status.HTTP_400_BAD_REQUEST),
                                statusDescription=INVALIDACCOUNT,
                        
                        )
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(
                        
                                statusCode=str(status.HTTP_400_BAD_REQUEST),
                                statusDescription=INVALIDBILLER,
                        
                        )
    except Exception as ex:
        logger.info(ex)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(
                statusCode=str(status.HTTP_400_BAD_REQUEST),
                statusDescription=SYSTEMBUSY,
        
        )

from models.model import *
import json
from schemas.customer import Customer
from sqlalchemy.orm import Session
from schemas.account import Account
from models.queries import paymentQuery
from schemas.setting import Setting
from utils import util
from utils import redisUtil
from utils.constant import *
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def checkBvn(setting: Setting,bvn:str,bvnType:str):
    response = {}
    try:
        logger.info(f"started bank verification check for {bvn}")
        retrieveBvn = await redisUtil.get_cache(key=f"bvn:{bvn}")
        if retrieveBvn:
            retrieveBvn = json.loads(retrieveBvn)
            response["statuscode"] = "200"
            response["message"] = SUCCESS
            response["data"] = retrieveBvn
        else:
            params = {'basic_or_advance': bvnType, 'bvn': bvn}
            res = util.http(url=f'{setting.bvn_base_url}identity/validate-bvn',params=params)
            resp = res.json()
            if res.status_code == 200:
                if resp["status"] is True:
                    response["statuscode"] = str(res.status_code)
                    response["message"] = resp["detail"]
                    response["data"] = resp["data"]
                else:
                    response["statuscode"] = "400"
                    response["message"] = resp["message"]
            else:
                response["statuscode"] = str(res.status_code)
                response["message"] = resp["message"]
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
def openDetailedAccount(setting: Setting,params: dict = None):
    response = {}
    try:
        logger.info(f"started get customer records for account Number {params} with BankOne")
        res = util.http(url=f"{setting.bankone_url}BankOneWebAPI/api/Account/CreateCustomerAndAccount/2?authToken={setting.bankone_token}",params=params)
        resp = res.json()
        if res.status_code == 200:
            if resp["status"] is True:
                response["statuscode"] = str(res.status_code)
                response["message"] = resp["detail"]
                response["data"] = resp["Message"]
            else:
                response["statuscode"] = "400"
                response["message"] = resp["detail"]
        else:
            response["statuscode"] = str(res.status_code)
            response["message"] = resp["detail"]
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
def openAccount(setting: Setting, params: dict = None):
    response = {}
    try:
        logger.info(
            f"started get customer records for account Number {params} with BankOne"
        )
        
        bankOneResponse = util.http(
                        url=f"{setting.bankone_url}BankOneWebAPI/api/Account/CreateAccountQuick/2?authToken={setting.bankone_token}",
                        params=params)
        if bankOneResponse.status_code == 200:
            res = bankOneResponse.json()
            if res["IsSuccessful"] is True:
                response["statuscode"] = str(bankOneResponse.status_code)
                response["message"] = SUCCESS
                response["data"] = res["Message"]
            else:
                response["statuscode"] = "400"
                response["message"] = res["Message"]["CreationMessage"] if "CreationMessage" in res["Message"] else res["Message"]
        else:
            response["statuscode"] = str(bankOneResponse.status_code)
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
async def getCustomerViaAccount(account:str,setting: Setting):
    response = {}
    try:
        logger.info(
            f"started get customer records for account Number {account}"
        )
        retrieveFromCache = await redisUtil.get_cache(key=f"enrollment:{account}")
        if retrieveFromCache:
            retrieveFromCache = json.loads(retrieveFromCache)
            response["statuscode"] = "200"
            response["message"] = SUCCESS
            response["data"] = retrieveFromCache
        else:
            logger.info(f"getting customer records for account {account} from BankOne")
            bankOneResponse = util.http(url=f"{setting.bankone_url}BankOneWebAPI/api/Customer/GetByAccountNo2/2?authToken={setting.bankone_token}&accountNumber={account}")
            if bankOneResponse.status_code == 200:
                resp = bankOneResponse.json()
                response["statuscode"] = str(bankOneResponse.status_code)
                response["message"] = SUCCESS
                response["data"] = resp
            else:
                response["statuscode"] = str(bankOneResponse.status_code)
                response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
async def accountBalance(account:str,setting: Setting):
    response = {}
    try:
        logger.info(
            f"started balance enquiry for {account} with BankOne"
        )
        bankOneResponse = util.http(
                        url=f"{setting.bankone_url}BankOneWebAPI/api/Account/GetAccountByAccountNumber/2?authToken={setting.bankone_token}&accountNumber={account}&computewithdrawableBalance=true")
        if bankOneResponse.status_code == 200:
            resp = bankOneResponse.json()
            response["statuscode"] = str(bankOneResponse.status_code)
            response["message"] = SUCCESS
            response["data"] = resp
        else:
            response["statuscode"] = str(bankOneResponse.status_code)
            response["message"] = BALANCEERROR
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
async def accountEnquiryInterByBankOne(setting: Setting,params: dict = None):
    response = {}
    try:
        logger.info(f"started name enquiry for bank {params} with BankOne")
        retrieveFromCache = await redisUtil.get_cache(key=f"enquiry:{params['BankCode']}:{params['AccountNumber']}")
        if retrieveFromCache:
            retrieveFromCache = json.loads(retrieveFromCache)
            response["statuscode"] = "200"
            response["message"] = SUCCESS
            response["data"] = retrieveFromCache
        else:
            params["Token"] = setting.bankone_token
            bankOneResponse = util.http(url=f"{setting.bankone_url}thirdpartyapiservice/apiservice/Transfer/NameEnquiry",params=params)
            if bankOneResponse.status_code == 200:
                resp = bankOneResponse.json()
                if resp["IsSuccessful"] is True:
                    await redisUtil.set_cache(key=f"enquiry:{params['BankCode']}:{params['AccountNumber']}",value=json.dumps(resp),ttl=timedelta(hours=24),)
                    response["statuscode"] = str(bankOneResponse.status_code)
                    response["message"] = SUCCESS
                    response["data"] = resp
                else:
                    response["statuscode"] = "400"
                    response["message"] = resp["ResponseMessage"]
            else:
                response["statuscode"] = str(bankOneResponse.status_code)
                response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
async def accountEnquiryIntraByBankOne(setting: Setting,params: dict = None):
    response = {}
    try:
        logger.info(f"started name enquiry for bank {params} with BankOne")
        retrieveFromCache = await redisUtil.get_cache(key=f"enquiryIntra:{params['AccountNo']}")
        if retrieveFromCache:
            retrieveFromCache = json.loads(retrieveFromCache)
            response["statuscode"] = "200"
            response["message"] = SUCCESS
            response["data"] = retrieveFromCache
        else:
            params["AuthenticationCode"] = setting.bankone_token
            bankOneResponse = util.http(url=f"{setting.bankone_url}thirdpartyapiservice/apiservice/Account/AccountEnquiry",params=params)
            if bankOneResponse.status_code == 200:
                resp = bankOneResponse.json()
                if resp["IsSuccessful"] is True:
                    await redisUtil.set_cache(key=f"enquiryIntra:{params['AccountNo']}",value=json.dumps(resp),ttl=timedelta(hours=24),)
                    response["statuscode"] = str(bankOneResponse.status_code)
                    response["message"] = SUCCESS
                    response["data"] = resp
                else:
                    response["statuscode"] = "400"
                    response["message"] = resp["ResponseDescription"]
            else:
                response["statuscode"] = str(bankOneResponse.status_code)
                response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response




def debitTransaction(
    db: Session,
    user: Customer,
    wallet: Account,
    transaction: TransactionModel,
):
    if user.commission_enabled:
        # get the commission configured per user per service
        commission = paymentQuery.get_one_commission(
            db=db, userId=user.id, billerId=transaction.customerBillerId
        )
        if commission:
            commissionAmount = int(transaction.amount) * (
                int(commission.totalcommission) / 100
            )
            paidAmount = int(transaction.amount) - int(commissionAmount)
            debit = debitAccount(db=db, wallet=wallet, amount=paidAmount)
            if debit and debit == util.DebitStatusEnum.APPROVE:
                # credit commission
                transaction = TransactionModel(
                    user_id=wallet.user_id,
                    transactionId=f"COM-{util.generateUniqueId()}",
                    amount=commissionAmount,
                    product=transaction.product,
                    isDebit=False,
                    customerBillerId=transaction.customerBillerId,
                    remarks=f"commission on {transaction.transactionType}",
                    reference=transaction.transactionId,
                    transactionType="COMMISSION",
                    transactionStatus=SUCCESS,
                    owner_id=user.id,
                    updated_at=datetime.now(),
                    created_at=datetime.now(),
                )
                createdTransaction = paymentQuery.create_transaction(
                    db=db, transaction=transaction
                )
                if createdTransaction:
                    return util.DebitStatusEnum.APPROVE
                else:
                    return util.DebitStatusEnum.PROCESSING
            else:
                return debit
        else:
            return debitAccount(db=db, wallet=wallet, amount=int(transaction.amount))
    else:
        return debitAccount(db=db, wallet=wallet, amount=int(transaction.amount))
def debitAccount(
    db: Session,
    wallet: Account,
    amount: int,
):
    if int(wallet.balance) > amount:
        wallet.balance_before = wallet.balance
        wallet.balance = int(wallet.balance) - amount
        updatedWallet = paymentQuery.update_wallet(db=db, wallet=wallet)
        if updatedWallet:
            return util.DebitStatusEnum.APPROVE
        else:
            return util.DebitStatusEnum.ERROR
    else:
        return util.DebitStatusEnum.INSUFICIENT
def creditAccountByBankOne(
        user:Customer,
        accountToBeCredited:str,
        setting: Setting, 
        db: Session, 
        amount: str,
        remarks:str
):
    response = {}
    try:
        logger.info(f"started debit with BankOne")
        params = {
    "RetrievalReference":  util.generateId(),
    "AccountNumber": accountToBeCredited,
    "NibssCode": setting.bankone_inst_code,
    "Amount": amount,
    "Fee": "string",
    "Narration":remarks,
    "Token": setting.bankone_token,
    "GLCode":setting.bankone_gl_cust# "1530"
}
        bankOneResponse = util.http(
                         url=f"{setting.bankone_url}thirdpartyapiservice/apiservice/CoreTransactions/Debit",
                        params=params)
        resp = bankOneResponse.json()
        if resp:
            if bankOneResponse.status_code == 200 and resp["IsSuccessful"] is True:
                 if resp["Status"] == "Successful" or resp["ResponseCode"] == str(bankOneResponse.status_code):
                      response["statuscode"] = resp["ResponseCode"]
                      response["message"] = SUCCESS
                      response["reference"] = resp["Reference"]
                      response["mRef"] = resp["UniqueIdentifier"]
                 elif resp["ResponseCode"] in ["91","06"]:
                      response["statuscode"] = "500"
                      response["message"] = PENDING
                      response["reference"] = resp["Reference"]
                      response["mRef"] = resp["UniqueIdentifier"]
                 else:
                      response["statuscode"] = "BT001"
                      response["message"] = FAILED
                      response["reference"] = resp["Reference"]
                      response["mRef"] = resp["UniqueIdentifier"]     
            else:
                response["statuscode"] = "BT00F"
                response["message"] = resp["ResponseDescription"]
        else:
            response["statuscode"] = "BT00F"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
def debitAccountByBankOne(
        user:Customer,
        accountToBeDebited:str,
        setting: Setting, 
        db: Session, 
        amount: str,
        remarks:str
):
    response = {
        "Provider":"BANKONE"
    }
    try:
        logger.info(f"started debit with BankOne")
        params = {
                    "RetrievalReference": util.generateId(),
                    "AccountNumber": accountToBeDebited,
                    "Amount": amount,
                    "Narration":remarks,
                    "Token": setting.bankone_token,
                    "GLCode":setting.bankone_cust_gl  #"1531"
                    }
        bankOneResponse = util.http(
                         url=f"{setting.bankone_url}thirdpartyapiservice/apiservice/CoreTransactions/Debit",
                        params=params)
        resp = bankOneResponse.json()
        if resp:
            if bankOneResponse.status_code == 200 and resp["IsSuccessful"] is True:
                 if  resp["ResponseCode"] == str(bankOneResponse.status_code):
                      response["statuscode"] = resp["ResponseCode"]
                      response["message"] = resp["ResponseMessage"]
                      response["reference"] = resp["Reference"]
                 elif resp["ResponseCode"] in ["91","06"]:
                      response["statuscode"] = "500"
                      response["message"] = resp["ResponseMessage"]
                      response["reference"] = resp["Reference"]
                 else:
                      response["statuscode"] = "BT001"
                      response["message"] = resp["ResponseMessage"]    
                      response["reference"] = resp["Reference"]
            else:
                response["statuscode"] = "BT00F"
                response["message"] = resp["ResponseMessage"]
                response["reference"] = None
        else:
            response["statuscode"] = "BT00F"
            response["message"] = SYSTEMBUSY
            response["reference"] = None
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = PENDING
        response["reference"] = None
    return response
def accountTransferInterPaymentByBankOne(
        amount:str,senderName:str,senderAccount:str,AccountNumber:str,destinationAccountName:str,
    BankCode: str, setting: Setting, transactionId: str, remark: str,transType:str
):
    response = {}
    try:
        logger.info(
            f"started payment transfer for bank {BankCode} with account {AccountNumber} with BankOne"
        )
        params = {
                            "Amount":amount,
                            "AppzoneAccount":"",
                            "Payer":senderName,
                            "PayerAccountNumber" :senderAccount,
                            "ReceiverAccountNumber":AccountNumber,
                            "ReceiverAccountType":"",
                            "ReceiverBankCode":BankCode,
                            "ReceiverPhoneNumber":"",
                            "ReceiverName":destinationAccountName,
                            "ReceiverBVN":"",
                            "ReceiverKYC":"",
                            "Narration":remark,
                            "TransactionReference":transactionId,
                            "NIPSessionID":"",
                            "Token":setting.bankone_token
                        }
        bankOneResponse = util.http(
                        url=f"{setting.bankone_url}thirdpartyapiservice/apiservice/Transfer/InterBankTransfer",
                        params=params)
        resp = bankOneResponse.json()
        if resp:
            if bankOneResponse.status_code == 200 and resp["IsSuccessFul"] is True:
                 if resp["Status"] == "Successful" or resp["ResponseCode"] == str(bankOneResponse.status_code):
                      response["statuscode"] = resp["ResponseCode"]
                      response["message"] = SUCCESS
                      response["reference"] = resp["Reference"]
                      response["mRef"] = resp["UniqueIdentifier"]
                 elif resp["ResponseCode"] in ["91","06"]:
                      response["statuscode"] = "500"
                      response["message"] = PENDING
                      response["reference"] = resp["Reference"]
                      response["mRef"] = resp["UniqueIdentifier"]
                 else:
                      response["statuscode"] = "BT001"
                      response["message"] = FAILED
                      response["reference"] = resp["Reference"]
                      response["mRef"] = resp["UniqueIdentifier"]     
            else:
                response["statuscode"] = "BT00F"
                response["mRef"] = resp["UniqueIdentifier"]
                response["message"] = resp["ResponseDescription"] if resp["ResponseDescription"] else str(resp["Status"])
        else:
            response["statuscode"] = "BT00F"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
def accountTransferIntraPaymentByBankOne(
        amount:str,senderName:str,senderAccount:str,AccountNumber:str,destinationAccountName:str,
    BankCode: str, setting: Setting, transactionId: str, remark: str,transType:str
):
    response = {}
    try:
        logger.info(
            f"started intra payment transfer for bank {BankCode} with account {AccountNumber} with BankOne"
        )
        params = {
            "FromAccountNumber": senderAccount,
            "Amount":amount,
            "ToAccountNumber":AccountNumber,
            "RetrievalReference": transactionId,
            "Narration": remark,
            "AuthenticationKey": setting.bankone_token
            }
        bankOneResponse = util.http(
                        url=f"{setting.bankone_url}thirdpartyapiservice/apiservice/CoreTransactions/LocalFundsTransfer",
                        params=params)
        resp = bankOneResponse.json()
        if resp:
            if bankOneResponse.status_code == 200 and resp["IsSuccessful"] is True:
                 if resp["Status"] == "Successful" or resp["ResponseCode"] == str(bankOneResponse.status_code):
                      response["statuscode"] = resp["ResponseCode"]
                      response["message"] = SUCCESS
                      response["reference"] = resp["Reference"]
                 elif resp["ResponseCode"] in ["91","06"]:
                      response["statuscode"] = "500"
                      response["message"] = PENDING
                      response["reference"] = resp["Reference"]
                 else:
                      response["statuscode"] = "BT001"
                      response["message"] = FAILED
                      response["reference"] = resp["Reference"]  
            else:
                response["statuscode"] = "BT00F"
                response["message"] = resp["ResponseMessage"]
        else:
            response["statuscode"] = "BT00F"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
def accountTransferRequeryByBankOne(amount:str,transactionId:str,transDate:str,transType:str,setting: Setting):
    response = {}
    try:
        logger.info(
            f"started {transType} bank transfer transaction requery for ID {transactionId} with BankOne"
        )
        params = {
            "Amount":amount,
            "RetrievalReference": transactionId,
            "TransactionDate":util.formatDateOfBirthForOpenAcct(transDate),
            "Token": setting.bankone_token
            }
        bankOneResponse = util.http(
                        url=f"{setting.bankone_url}thirdpartyapiservice/apiservice/CoreTransactions/TransactionStatusQuery" if transType.upper() == "INTRA" else f"{setting.bankone_url}thirdpartyapiservice/apiservice/Transactions/TransactionStatusQuery",
                        params=params)
        resp = bankOneResponse.json()
        if resp:
            if bankOneResponse.status_code == 200 and resp["IsSuccessful"] is True:
                 if resp["Status"] == "Successful" or resp["ResponseCode"] == str(bankOneResponse.status_code):
                      response["statuscode"] = resp["ResponseCode"]
                      response["message"] = SUCCESS
                      response["reference"] = resp["Reference"]
                 elif resp["ResponseCode"] in ["91","06"]:
                      response["statuscode"] = "500"
                      response["message"] = PENDING
                      response["reference"] = resp["Reference"]
                 else:
                      response["statuscode"] = "BT001"
                      response["message"] = FAILED
                      response["reference"] = resp["Reference"]  
            else:
                response["statuscode"] = "BT00F"
                response["message"] = resp["ResponseMessage"]
        else:
            response["statuscode"] = "BT00F"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
def accountTransferReversalByBankOne(amount:str,transactionId:str,transDate:str,transType:str,setting: Setting):
    response = {}
    try:
        logger.info(
            f"started {transType} bank transfer transaction requery for ID {transactionId} with BankOne"
        )
        params = {
            "Amount":amount,
            "RetrievalReference": transactionId,
            "TransactionDate":util.formatDateOfBirthForOpenAcct(transDate),
            "TransactionType":transType,
            "Token": setting.bankone_token
            }
        bankOneResponse = util.http(
                        url=f"{setting.bankone_url}thirdpartyapiservice/apiservice/CoreTransactions/Reversal",
                        params=params)
        resp = bankOneResponse.json()
        if resp:
            if bankOneResponse.status_code == 200 and resp["IsSuccessful"] is True:
                 if resp["Status"] == "Successful" or resp["ResponseCode"] == str(bankOneResponse.status_code):
                      response["statuscode"] = resp["ResponseCode"]
                      response["message"] = SUCCESS
                      response["reference"] = resp["Reference"]
                 elif resp["ResponseCode"] in ["91","06"]:
                      response["statuscode"] = "500"
                      response["message"] = PENDING
                      response["reference"] = resp["Reference"]
                 else:
                      response["statuscode"] = "BT001"
                      response["message"] = FAILED
                      response["reference"] = resp["Reference"]  
            else:
                response["statuscode"] = "BT00F"
                response["message"] = resp["ResponseMessage"]
        else:
            response["statuscode"] = "BT00F"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
def accountBalanceEnquiryByBankOne(accountNumber:str,setting: Setting):
    response = {}
    try:
        logger.info(
            f"started balance enquiry for {accountNumber} with BankOne"
        )
        bankOneResponse = util.http(
                        url=f"{setting.bankone_url}BankOneWebAPI/api/Account/GetAccountByAccountNumber/2?authToken={setting.bankone_token}&accountNumber={accountNumber}&computewithdrawableBalance=true")
        if bankOneResponse.status_code == 200:
            resp = bankOneResponse.json()
            response["statuscode"] = str(bankOneResponse.status_code)
            response["message"] = SUCCESS
            response["wbalance"] = util.getKoboValue(amount=resp["WithdrawableBalance"])
            response["abalance"] = util.getKoboValue(amount=resp["AvailableBalance"])
            response["lbalance"] = util.getKoboValue(amount=resp["LedgerBalance"])
        else:
            response["statuscode"] = "BT00F"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
def getCustomerRecordsViaBVNFromBankOne(bvn:str,setting: Setting):
    response = {}
    try:
        logger.info(
            f"started get customer records for bvn {bvn} with BankOne"
        )
        bankOneResponse = util.http(
                        url=f"{setting.bankone_url}BankOneWebAPI/api/Customer/GetCustomerByBVN/2?authToken={setting.bankone_token}&BVN={bvn}")
        if bankOneResponse.status_code == 200:
            resp = bankOneResponse.json()
            response["statuscode"] = str(bankOneResponse.status_code)
            response["message"] = SUCCESS
            response["data"] = resp
        else:
            response["statuscode"] = "BT00F"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response
def updateCustomerViaCustomerIdFromBankOne(setting: Setting,custId:str,firstName:str,lastName:str,middleName:str,
                                           dob:str,phoneNumber:str,bvn:str,officerCode:str,gender:str,nin:str,
                                           email:str=None,placeOfBirth:str=None,nKinName:str=None,nKinPhone:str=None,

                                           city:str=None,address:str=None,):
    response = {}
    try:
        logger.info(
            f"started updating customer records for customer {custId} with BankOne"
        )
        params = {
    "CustomerID":custId,
    "LastName": firstName,
    "FirstName":lastName,
    "OtherNames":middleName,
    "City":city,
    "Address": address,
    "Gender": gender,
    "DateOfBirth":dob,
    "PhoneNo":phoneNumber,
    "PlaceOfBirth":placeOfBirth,
    "NationalIdentityNo": nin,
    "NextOfKinName":nKinName,
    "NextOfKinPhoneNumber": nKinPhone,
    "BankVerificationNumber":bvn,
    "Email": email,
    #"ReferralName": "string",
    #"ReferralPhoneNo": "string",
    #"CustomerType": "string",
    #"BranchID": "string",
    "HasCurrentRunningLoanAndNottDefaulting": 0,
    "HasDefaultedInAnyLoan": 0,
    "HasNoOutStandingLoanAndNotDefaulting": 0,
    "HasCompleteDocumentatiOn": True,
    #"CustomerPassportInBytes": "string",
    "AccountOfficerCode": officerCode
}
        bankOneResponse = util.http(
                        url=f"{setting.bankone_url}BankOneWebAPI/api/Customer/UpdateCustomer/2?authToken={setting.bankone_token}",
                        params=params)
        if bankOneResponse.status_code == 200:
            resp = bankOneResponse.json()
            response["statuscode"] = str(bankOneResponse.status_code)
            response["message"] = SUCCESS
            response["data"] = resp
        else:
            response["statuscode"] = "BT00F"
            response["message"] = SYSTEMBUSY
    except Exception as ex:
        logger.info(ex)
        response["statuscode"] = "500"
        response["message"] = SYSTEMBUSY
    return response

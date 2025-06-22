from pydantic import BaseModel,field_validator
from typing import Dict, Union,Optional
from utils import util

class BaseResponse(BaseModel):
    statusCode: str
    statusDescription: str
    data: Union[Dict, str] = None
class BvnRequest(BaseModel):
    bvn: str
    dob: str
    msisdn: str
    telco:str
    sessionId:str
class OpenAccountRequest(BaseModel):
    bvn: str
    dob: str
    msisdn: str
    telco:str
    sessionId:str
    pin:str
class EnrolAccountRequest(BaseModel):
    bvn: str
    accountNumber: str
    msisdn: str
    telco:str
    sessionId:str
    pin:str
class CreatePINRequest(BaseModel):
    pin: str
    confirmPin: str
class ChangePINRequest(BaseModel):
    oldPin: str
    pin: str
    confirmPin: str
class PINRequest(BaseModel):
    pin: Optional[str]= None
    accountNumber: str
    msisdn: str
    receipient:str
    telco:str
    sessionId:str
class CheckBalanceRequest(PINRequest):
    pass
class TransferPossibleRequest(BaseModel):
    receipient: str
    msisdn: str
    telco:str
    sessionId:str
class TransferNameEnquiryRequest(BaseModel):
    bankcode: Optional[str]= None
    receipient: str
    msisdn: str
    telco:str
    sessionId:str
class TransferRequest(PINRequest):
    amount: str
    bankcode: Optional[str]= None
class TransferInterRequest(PINRequest):
    amount: str
    bankCode: str
class BillNameEnquiryRequest(BaseModel):
    receipient:str
    billerId:str
    amount: str
    packageId:Optional[str]= None
    telco:str
    sessionId:str
    msisdn: str
class BillPaymentRequest(PINRequest):
    billerId:str
    packageId:Optional[str]= None
    amount: str
    @field_validator("amount")
    def amount_validator(cls, amount):
        formattedAmount = util.amountToKobo(amount=amount)
        return formattedAmount
    customerAddress:Optional[str]= None
    customerName:Optional[str] = None

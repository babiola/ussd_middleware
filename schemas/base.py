from pydantic import BaseModel,field_validator
from typing import Dict, Union,Optional
from utils import util


class BaseResponse(BaseModel):
    statusCode: str
    statusDescription: str
    data: Union[Dict, str] = None
class PINRequest(BaseModel):
    pin: str
class TransferIntraRequest(PINRequest):
    amount: str
    phoneNumber: str
    accountNumber: str
    receipientAccountNumber: str
class TransferInterRequest(PINRequest):
    amount: str
    phoneNumber: str
    accountNumber: str
    receipientAccountNumber: str
    receipientBankCode: str
class BillPaymentRequest(PINRequest):
    accountNumber: str
    amount: str
    customerNumber: str
    billerId: str
    packageCode: Optional[str] = None

class BillNameEnquiryRequest(BaseModel):
    accountNumber:str
    customerNumber:str
    billerId:str
    amount: str
    packageId:Optional[str]= None
class BillPaymentRequest(PINRequest):
    customerNumber:str
    accountNumber:str
    billerId:str
    packageId:Optional[str]= None
    amount: str
    @field_validator("amount")
    def amount_validator(cls, amount):
        formattedAmount = util.amountToKobo(amount=amount)
        return formattedAmount
    customerAddress:Optional[str]= None
    customerName:Optional[str] = None

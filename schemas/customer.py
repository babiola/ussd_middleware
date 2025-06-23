
from utils import util
from typing import Union,List
from schemas.account import Account
from pydantic import BaseModel,field_validator
from schemas.base import BaseResponse

class CustomerBase(BaseModel):
    active:  Union[bool,None]=False
    isUssdEnrolled:  Union[bool,None]=False
    indemnitySigned:  Union[bool,None]=False
    blacklisted:  Union[bool,None]=True
    customerNumber: str
    phonenumber: str
    hasPin: Union[bool,None]=False
    @field_validator("phonenumber")
    def phoneNumber_validator(cls, phonenumber):
        phone = util.formatPhoneFull(msisdn=phonenumber)
        return phone
class Customer(CustomerBase):
    accounts:Union[List[Account],None] = None
    class Config:
        from_attributes = True
        populate_by_name = True
class CustomersResponse(BaseResponse):
    data: Union[List[Customer],None] = None
class CustomerResponse(BaseResponse):
    data: Customer = None
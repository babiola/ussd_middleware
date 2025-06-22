
from utils import util
from typing import Union,List
from schemas.account import Account
from pydantic import BaseModel,field_validator
from schemas.base import BaseResponse

class CustomerBase(BaseModel):
    active: bool
    isUssdEnrolled: bool
    indemnitySigned: bool
    blacklisted: bool
    customerNumber: str
    phonenumber: str
    hasPin: bool
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
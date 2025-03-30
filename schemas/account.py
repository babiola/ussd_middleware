from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse


class AccountBase(BaseModel):
    active:bool
    accountNumber: str
    customerNumber:str
    isDefaultPayment:bool
    active:bool
class Account(AccountBase):
    pass

    class Config:
        from_attributes = True
        populate_by_name = True

class AccountsResponse(BaseResponse):
    data: Union[List[Account],None] = None
    
class AccountResponse(BaseResponse):
    data: Account = None
from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.base import BaseResponse

class BankBase(BaseModel):
    Code: Union[str, None] = None
    Name: Union[str, None] = None


class Bank(BankBase):
    pass
    class Config:
        from_attributes = True
        populate_by_name = True

class Banks(BankBase):
    banks: List[Bank]
class BanksResponse(BaseResponse):
    data: Union[List[Bank],None] = None
    
class BankResponse(BaseResponse):
    data: Bank = None
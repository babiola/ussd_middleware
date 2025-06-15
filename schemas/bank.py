from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.base import BaseResponse

class BankBase(BaseModel):
    institutionCode: Union[str, None] = None
    institutionName: Union[str, None] = None
    institutionShortName: Union[str, None] = None

class BankRequest(BankBase):
    user: Union[List[str], None] = None

class Bank(BankBase):
    pass

    class Config:
        from_attributes = True
        populate_by_name = True

class BanksResponse(BaseResponse):
    data: Union[List[Bank],None] = None
    
class BankResponse(BaseResponse):
    data: Bank = None
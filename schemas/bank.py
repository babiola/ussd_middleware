from typing import Optional, Union,List
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from schemas.response import BaseResponse

class BankBase(BaseModel):
    name: Union[str, None] = None
    BankImage: Union[str, None] = None
    address: Union[str, None] = None
    contact: Union[str, None] = None
    startingPoint: Union[str, None] = None
    estimatedDeparture: Union[datetime, None] = None
    estimatedArrival: Union[datetime, None] = None
    destination: Union[str, None] = None
    description: Union[str, None] = None
    policy: Union[str, None] = None

class BankRequest(BankBase):
    user: Union[List[str], None] = None

class Bank(BankBase):
    price: Union[str, None] = None
    status: Union[bool, None] = False
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class BanksResponse(BaseResponse):
    data: Union[List[Bank],None] = None
    
class BankResponse(BaseResponse):
    data: Bank = None
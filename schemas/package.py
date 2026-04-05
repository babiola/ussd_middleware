from typing import Optional, Union,List
from decimal import ROUND_HALF_UP, Decimal
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel,model_validator
from schemas.base import BaseResponse


class PackageBase(BaseModel):
    product_type_id:int
    billerId: Union[str, None] = None
    short_description: Union[str, None] = None
    databundle: Union[str, None] = None
    amount: Union[str, None] = None
    @model_validator(mode="after")
    def compute_kobo(self):
        if self.amount is not None:
            self.amount = int(
                (int(self.amount) / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            )
        return self
    validity: Union[str, None] = None
    productId: Union[str, None] = None
    hasValidity: Union[bool, None] = None
    status: Union[bool, None] = None
    currencyCode: Union[str, None] = None
    currencySymbol: Union[str, None] = None


class PackageRequest(PackageBase):
    user: Union[List[str], None] = None

class Package(PackageBase):
    id: Optional[int]
    created_at: Union[datetime, None] = func.now()
    updated_at: Union[datetime, None] = func.now()

    class Config:
        from_attributes = True
        populate_by_name = True

class PackagesResponse(BaseResponse):
    data: Union[List[Package],None] = None
    
class PackageResponse(BaseResponse):
    data: Package = None
from pydantic import BaseModel, Field,field_validator,EmailStr
from typing import Optional, Union, List
from datetime import datetime
from schemas.base import BaseResponse


class AdminBase(BaseModel):
    username: str
    name: str
    ips: List[str] = []


class AdminCreate(AdminBase):
    password: Union[str, None] = None
    created_at: datetime
    updated_at: datetime


class Admin(AdminBase):
    id: int
    password: Union[str, None] = None
    @field_validator('ips',mode='before')
    def parse_ips(cls, value):
        if value is None or value == "":
            return []  # Return an empty list if the input is None or an empty string
        if isinstance(value, str):
            # Split the string by commas, strip whitespace, and filter out empty strings
            return [ip.strip() for ip in value.split(',') if ip.strip()]
        elif isinstance(value, list):
            return value  # If it's already a list, return it as-is
        else:
            raise ValueError("Input must be a string or a list of strings")


    class Config:
        from_attributes = True
        populate_by_name = True
    
class CreateAdminRequest(AdminBase):
    pass      
class AdminLoginRequest(BaseModel):
    username: EmailStr
    password: str  

class ForgetPasswordRequest(BaseModel):
    email: EmailStr
class ChangePasswordRequest(BaseModel):
    oldPassword: str
    password: str
    confirmPassword: str

from pydantic import BaseModel, Field,validator,EmailStr
from typing import Optional, Union, List
from datetime import datetime
from schemas.response import BaseResponse


class AdminBase(BaseModel):
    username: str
    name: str


class AdminCreate(AdminBase):
    password: Union[str, None] = None
    created_at: datetime
    updated_at: datetime


class Admin(AdminBase):
    password: Union[str, None] = None
    id: int

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

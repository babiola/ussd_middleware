from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
    Enum,func
)
from sqlalchemy.orm import backref, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import timedelta
import uuid

# from utils.database import Base
from enum import Enum as PythonEnum

Base = declarative_base()

class AccountLevelEnum(PythonEnum):
    TIER1 = "tier1"
    TIER2 = "admin"
    TIER3 = "accountant"
    TIER4 = "audit"
class OTPStatusEnum(PythonEnum):
    SENT = "sent"
    PENDING = "pending"
    NOTSENT = "notsent"
    OPEN = "open"
    LOGGED = "logged"
    CLOSED = "closed"
class TransactionStatusEnum(PythonEnum):
    SUCCESS = "success"
    PENDING = "pending"
    PROCESSING = "processing"
    FAILED = "failed"
class AdminModel(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(8), unique=True, index=True)
    password = Column(String(255))
    name = Column(String(255))
    ips = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
class CustomerModel(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    username = Column(String(50),unique=True,index=True,default=lambda: str(uuid.uuid4()).replace("-", ""),)
    firstname = Column(String(25))
    lastname = Column(String(25))
    otherNames = Column(String(255),nullable=True)
    dob = Column(String(25),nullable=True,default=f"{func.now()}")
    email = Column(String(255),nullable=False)
    phonenumber = Column(String(13))
    bvn = Column(String(13))
    nin = Column(String(13))
    gender = Column(Boolean, default=False)
    address = Column(String(255),nullable=True)
    state = Column(String(255),nullable=True)
    landphone = Column(String(255),nullable=True)
    nationalId = Column(String(25),nullable=True)
    occupation = Column(String(50),nullable=True)
    country = Column(String(25),nullable=True)
    meansOfId = Column(String(25),nullable=True)
    meansOfIdNumber = Column(String(25),nullable=True)
    pin = Column(String(255), nullable=True)
    active = Column(Boolean, default=False)
    blacklisted = Column(Boolean, default=False)
    indemnitySigned = Column(Boolean, default=False)
    indemnitySigned_at = Column(DateTime, nullable=True)
    accounts = relationship("AccountModel", back_populates="customer")
    transactions = relationship("TransactionModel", back_populates="customer")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
class AccountModel(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    accountNumber = Column(String(100))
    customerNumber = Column(String(100))
    active = Column(Boolean, default=False)
    isDefaultPayment = Column(Boolean, default=False)
    blacklisted = Column(Boolean, default=False)
    balance = Column(String(25),default="0")
    level = Column(Enum(AccountLevelEnum), nullable=False, default=AccountLevelEnum.TIER1)
    customer = relationship("CustomerModel", back_populates="accounts")
    transactions = relationship("TransactionModel", back_populates="transaction")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
class TransactionModel(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    account_id = Column(Integer, ForeignKey('accounts.id'))
    reference = Column(String(100), nullable=True)
    amount = Column(String(50), nullable=False)
    product = Column(String(100), nullable=True)
    statusCode = Column(String(25), nullable=True)
    statusMessage = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
class OTPModel(Base):
    __tablename__ = "otps"
    id = Column(Integer, primary_key=True, index=True)
    
    otp = Column(String(6))
    servicename = Column(String(255))
    status = Column(Enum(OTPStatusEnum), nullable=False, default=OTPStatusEnum.OPEN)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    created_at = Column(DateTime, default=func.now())
    expired_at = Column(
        DateTime,
        default=func.now() + timedelta(minutes=15),
    )
    updated_at = Column(DateTime, default=func.now())
class SettingsModel(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    
    app_name = Column(String(255), default="DIP API")
    channel_name = Column(String(50), default="dip")
    debug = Column(Boolean, default=True)
    db_url = Column(String(100), default="")
    mail_username = Column(String(150), nullable=True)
    mail_password = Column(String(150), nullable=True)
    mail_from = Column(String(150), nullable=True)
    mail_port = Column(String(9), nullable=True)
    mail_server = Column(String(150), nullable=True)
    mail_from_name = Column(String(150), nullable=True)
    allowed_hosts = Column(String(255), nullable=True)
    allowed_origins = Column(String(255), nullable=True)
    access_token_expire_minutes = Column(Integer, nullable=True)
    flutterwave_pub= Column(String(250), nullable=True)
    secret_key = Column(String(250), nullable=True)
    algorithm = Column(String(250), nullable=True)
    vanso_url = Column(String(250), nullable=True)
    vanso_username = Column(String(250), nullable=True)
    vanso_password = Column(String(250), nullable=True)
    senderid = Column(String(250), nullable=True)
    paystack_url = Column(String(250), nullable=True)
    paystack_token = Column(String(250), nullable=True)
    payment_callback_url = Column(String(250), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
    Enum,func,text
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
    firstname = Column(String(25))
    middlename = Column(String(25))
    lastname = Column(String(25))
    customerNumber = Column(String(100))
    dob = Column(String(25),nullable=True,default=f"{func.now()}")
    email = Column(String(255),nullable=True)
    phonenumber = Column(String(13))
    bvn = Column(String(11))
    nin = Column(String(11))
    gender = Column(Boolean, default=False ,server_default=text("false"))
    country = Column(String(25),nullable=True)
    pin = Column(String(255), nullable=True)
    hasPin = Column(Boolean, default=False,server_default=text("false"))
    active = Column(Boolean, default=False,server_default=text("false"))
    isUssdEnrolled = Column(Boolean, default=False,server_default=text("false"))
    blacklisted = Column(Boolean, default=False,server_default=text("false"))
    indemnitySigned = Column(Boolean, default=False)
    indemnitySigned_at = Column(DateTime, nullable=True)
    accounts = relationship("AccountModel", back_populates="customer")
    transactions = relationship("TransactionModel", back_populates="customer")
    updated_at = Column(DateTime,server_default=func.now(),server_onupdate=func.now())
    created_at = Column(DateTime,server_default=func.now())
class AccountModel(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    accountNumber = Column(String(100))
    customerNumber = Column(String(100))
    active = Column(Boolean, default=False, server_default=text("false"))
    isDefaultPayment = Column(Boolean, default=False, server_default=text("false"))
    blacklisted = Column(Boolean, default=False, server_default=text("false"))
    balance = Column(String(25),default="0")
    level = Column(Enum(AccountLevelEnum), nullable=False, default=AccountLevelEnum.TIER1,server_default=AccountLevelEnum.TIER1.value)
    customer = relationship("CustomerModel", back_populates="accounts")
    transactions = relationship("TransactionModel", back_populates="account")
    updated_at = Column(DateTime,server_default=func.now(),server_onupdate=func.now())
    created_at = Column(DateTime,server_default=func.now())
class TransactionModel(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    account_id = Column(Integer, ForeignKey('accounts.id'))
    reference = Column(String(100), nullable=True)
    providerReference = Column(String(100), nullable=True)
    amount = Column(String(50), nullable=False)
    product = Column(String(100), nullable=True)
    statusCode = Column(String(25), nullable=True)
    statusMessage = Column(String(50), nullable=True)
    customer = relationship("CustomerModel", back_populates="transactions")
    account = relationship("AccountModel", back_populates="transactions")
    updated_at = Column(DateTime,server_default=func.now(),server_onupdate=func.now())
    created_at = Column(DateTime,server_default=func.now())
class OTPModel(Base):
    __tablename__ = "otps"
    id = Column(Integer, primary_key=True, index=True)
    
    otp = Column(String(6))
    servicename = Column(String(255))
    status = Column(Enum(OTPStatusEnum), nullable=False, default=OTPStatusEnum.OPEN,server_default=OTPStatusEnum.OPEN.value)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    expired_at = Column(
        DateTime,
        default=func.now() + timedelta(minutes=15),
    )
    updated_at = Column(DateTime,server_default=func.now(),server_onupdate=func.now())
    created_at = Column(DateTime,server_default=func.now())
class SettingsModel(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    
    app_name = Column(String(255), default="API")
    channel_name = Column(String(50), default="api")
    debug = Column(Boolean, default=True)
    db_url = Column(String(100), default="")
    bvn_base_url = Column(String(200), default="")
    bank_base_url = Column(String(200), default="")
    mail_username = Column(String(150), nullable=True)
    mail_password = Column(String(150), nullable=True)
    mail_from = Column(String(150), nullable=True)
    mail_port = Column(String(9), nullable=True)
    mail_server = Column(String(150), nullable=True)
    mail_from_name = Column(String(150), nullable=True)
    bankone_url = Column(String(255), nullable=True)
    bankone_token = Column(String(100), nullable=True)
    bankone_inst_code = Column(String(10), nullable=True)
    bankone_cust_gl = Column(String(15), nullable=True)
    bankone_gl_cust = Column(String(15), nullable=True)
    allowed_hosts = Column(String(255), nullable=True)
    allowed_origins = Column(String(255), nullable=True)
    access_token_expire_minutes = Column(Integer, nullable=True)
    flutterwave_pub= Column(String(250), nullable=True)
    secret_key = Column(String(250), nullable=True)
    algorithm = Column(String(250), nullable=True)
    senderid = Column(String(250), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    description = Column(String(255), nullable=True)
    vasType = Column(String(50))
    icon = Column(String(55), nullable=True)
    customerField = Column(String(20), nullable=True)
    status = Column(Boolean, default=False, server_default=text("false"))
    billers = relationship("ProductTypeModel", backref="product")
    enabledInline = Column(Boolean, default=False)
    isWeb = Column(Boolean, default=False)
    updated_at = Column(DateTime,server_default=func.now(),server_onupdate=func.now())
    created_at = Column(DateTime,server_default=func.now())
class ProductTypeModel(Base):
    __tablename__ = "product_types"
    id = Column(Integer, primary_key=True, index=True)
    service_provider_id = Column(Integer, ForeignKey("service_providers.id"),nullable=True)
    billerName = Column(String(50))
    billerId = Column(String(15))
    billerType = Column(String(25))
    amountType = Column(String(20), nullable=True)
    logo = Column(String(255), nullable=True)
    customerField = Column(String(255))
    provider = Column(String(10),default="BANKONE",server_default="BANKONE")
    network = Column(String(255), nullable=True)
    vat = Column(Integer, default=0,server_default="0")
    maxAmountLimit = Column(Integer, default=500000,server_default="500000")
    minAmountLimit = Column(Integer, default=5000,server_default="5000")
    status = Column(Boolean, default=False, server_default=text("false"))
    hasPackages = Column(Boolean, default=False, server_default=text("false"))
    hasLookup = Column(Boolean, default=False, server_default=text("false"))
    hasAddons = Column(Boolean, default=False, server_default=text("false"))
    currencyCode = Column(String(25), default="566", server_default="566")
    currencySymbol = Column(String(25), default="NGN", server_default="NGN")
    product_id = Column(Integer, ForeignKey("products.id"))
    service_provider = relationship("ServiceProviderModel",uselist=False, back_populates="product_type")
    packages = relationship("PackageModel", back_populates="product_type")
    updated_at = Column(DateTime,server_default=func.now(),server_onupdate=func.now())
    created_at = Column(DateTime,server_default=func.now())
class PackageModel(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    product_type_id = Column(Integer, ForeignKey("product_types.id"))
    billerId = Column(String(15))
    databundle = Column(String(150))
    short_description = Column(String(150))
    amount = Column(String(50), default="0",server_default="0")
    validity = Column(String(50), nullable=True)
    productId = Column(String(50))
    currencyCode = Column(String(25), default="566", server_default="566")
    currencySymbol = Column(String(25), default="NGN", server_default="NGN")
    status = Column(Boolean, default=False , server_default=text("false"))
    hasValidity = Column(Boolean, default=False , server_default=text("false"))
    product_type = relationship("ProductTypeModel", back_populates="packages")
    updated_at = Column(DateTime,server_default=func.now(),server_onupdate=func.now())
    created_at = Column(DateTime,server_default=func.now())
class ServiceProviderModel(Base):
    __tablename__ = "service_providers"
    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String(100))
    provider_code = Column(String(100),default="001", server_default="001")
    billerId = Column(String(15),default="A01E" ,server_default="A01E")
    auth_method = Column(String(100))
    provider_url = Column(String(200))
    active = Column(Boolean, default=False , server_default=text("false"))
    service_secret = Column(String(255))
    service_key = Column(String(255))
    login_id = Column(String(25))
    product_type = relationship("ProductTypeModel",uselist=False, back_populates="service_provider")
    updated_at = Column(DateTime,server_default=func.now(),server_onupdate=func.now())
    created_at = Column(DateTime,server_default=func.now())
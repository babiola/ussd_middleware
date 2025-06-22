import logging
import secrets
from utils import util
from fastapi import Depends
from typing import Annotated
from urllib.parse import urlparse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from models.queries import settingQuery,adminQuery,customerQuery
from schemas.setting import Setting
from datetime import datetime,timedelta
from utils.constant import *
from schemas.admin import Admin
from schemas.base import PINRequest
from utils import redisUtil
from jose import jwt, JWTError
from utils.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends,status,Request
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
logger = logging.getLogger(__name__)
security = HTTPBasic()
middlewares = [
    Middleware(TrustedHostMiddleware, allowed_hosts=util.get_setting().allowed_hosts
               ),
    Middleware(
        CORSMiddleware,
        allow_origins=util.get_setting().allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    ),
]
device_exception = util.UnicornException(
        status=status.HTTP_401_UNAUTHORIZED,
        error={"statusCode": str(status.HTTP_401_UNAUTHORIZED), "statusDescription": UNSUPPORTEDDEVICE},
    )
def authenticate_user(
        request: Request,
    db: Annotated[Session, Depends(get_db)],
    credentials: HTTPBasicCredentials = Depends(security),
):
    logger.info(credentials.username)
    user = adminQuery.getAdmin(username=credentials.username, db=db)
    logger.info(user)
    if user:
        logger.info(user.name)
        correct_username = secrets.compare_digest(credentials.username, user.username)
        correct_password = secrets.compare_digest(credentials.password, user.password)
        if correct_username and correct_password:
            if util.validateIP(request=request, allowed=user.ips):
                return Admin.model_validate(user)
        raise util.UnicornException(
        status=status.HTTP_401_UNAUTHORIZED,
        error={"statusCode": "401", "statusDescription": "Unathorised"},)
    raise util.UnicornException(
        status=status.HTTP_401_UNAUTHORIZED,
        error={"statusCode": "401", "statusDescription": "Unathorised"},)
def getTenant(request: Request):
    appsetting = util.get_setting().app
    if appsetting == "dev":
        return "borno.getdip.com.ng"
    origin = request.headers.get("origin", "katsina.getdip.com.ng")
    logger.info(origin)
    domain = urlparse(origin).netloc if origin else None
    logger.info(domain)
    return domain
def getSystemSetting(db: Session = Depends(get_db)):
    settings = settingQuery.setting(db=db)    
    if settings:
        logger.info(settings.app_name)
        return Setting.model_validate(settings)
    logger.info("Unable to get system setting. please check database settings for more info")
    exit(code=99)
async def validateAdmin(
        request:Request,
    setting: Setting = Depends(getSystemSetting),
    db: Session = Depends(get_db),
    tenant:str=Depends(getTenant)
):
    credentials_exception = util.UnicornException(
        status=status.HTTP_401_UNAUTHORIZED,
        error={"statusCode": "401", "statusDescription": "Your session has expired!"},
    )
    try:
        token = request.cookies.get("access_token")
        logger.info(token)
        if token:
            payload = jwt.decode(
            token, setting.secret_key, algorithms=[setting.algorithm]
        )
            logger.info(payload)
            user = adminQuery.getOne(
            db=db,
            tenant=tenant,
            email=payload["username"],
        )
            if user:
                logger.info(user.status)
                if user.status:
                    logger.info(user.status)
                    return Admin.from_orm(user)
                raise util.UnicornException(
                    status=status.HTTP_401_UNAUTHORIZED,
                    error={
                    "statusCode": str(status.HTTP_401_UNAUTHORIZED),
                    "statusDescription": f"Your account is {user.status.value}",
                },
            )
        raise credentials_exception
    except JWTError:
        raise credentials_exception
async def validateTransactionPIN(
    payload:PINRequest,
    setting: Setting = Depends(getSystemSetting),
    db: Session = Depends(get_db),
):
    try:
        logger.info(payload)
        account = customerQuery.getCustomerAccount(db=db,account=payload.accountNumber)
        if account:
            if account.customer:
                logger.info(f"checking if customer exist with account {payload.accountNumber}")
                if account.customer.blacklisted is False:
                    logger.info(f"checking if customer blacklisted status with account {payload.accountNumber}")
                    if account.customer.isUssdEnrolled:
                        logger.info(f"checking if customer ussd enrollment status with account {payload.accountNumber}")
                        if account.customer.active:
                            logger.info(f"checking if customer active status with account {payload.accountNumber}")
                            if util.formatPhoneFull(payload.receipient) == util.formatPhoneFull(account.customer.phonenumber):
                                logger.info(f"checking if receipient phone number matches with account {payload.accountNumber}")
                                return account
                            else:
                                pintries = await redisUtil.get_cache(key=f"account:{payload.accountNumber}")
                                logger.info(f"pintries for account {payload.accountNumber} is {pintries}")
                                logger.info(pintries)
                                pintries = int(pintries) if pintries else None
                                if pintries is None or pintries < setting.max_pin_tries:
                                    if util.verify_password(payload.pin, account.customer.pin) is True:
                                        await redisUtil.delete_cache(key=f"account:{payload.accountNumber}")
                                        return account
                                    else:
                                        pintries = pintries + 1 if pintries else 1
                                        logger.info(f"incrementing pintries for account {payload.accountNumber} to {pintries}")
                                        await redisUtil.incrementCounter(key=f"account:{payload.accountNumber}")
                                        raise util.UnicornException(status=status.HTTP_400_BAD_REQUEST,error={"statusCode": str(status.HTTP_400_BAD_REQUEST),"statusDescription": f"{INVALIDPIN}. You have {setting.max_pin_tries - pintries} attempt left",})
                                else:
                                    account.active = False
                                    account.customer.active = False
                                    account.blacklisted = True
                                    account.customer.blacklisted = True
                                    customerQuery.create(db=db,model=account)
                                    raise util.UnicornException(status=status.HTTP_400_BAD_REQUEST,error={"statusCode": str(status.HTTP_400_BAD_REQUEST),"statusDescription": f"Your account has been disabled due to too many failed PIN attempts. Please contact customer support.",},)
                        else:
                            raise util.UnicornException(status=status.HTTP_403_FORBIDDEN,error={"statusCode": str(status.HTTP_403_FORBIDDEN),"statusDescription": INACTIVE,},)
                    else:
                        raise util.UnicornException(status=status.HTTP_403_FORBIDDEN,error={"statusCode": str(status.HTTP_403_FORBIDDEN),"statusDescription": USSDNOTENROLLED,},)
                else:
                    raise util.UnicornException(
                        status=status.HTTP_403_FORBIDDEN,
                        error={
                            "statusCode": str(status.HTTP_403_FORBIDDEN),
                            "statusDescription": BLACKLISTEDUSER,
                        },
                    )
            else:
                raise util.UnicornException(
                    status=status.HTTP_404_NOT_FOUND,
                    error={
                        "statusCode": str(status.HTTP_404_NOT_FOUND),
                        "statusDescription": UNKNOWNUSER,
                    },
                )
        else:
            logger.info(f"account {payload.accountNumber} not found")
            raise util.UnicornException(
                status=status.HTTP_404_NOT_FOUND,
                error={
                    "statusCode": str(status.HTTP_404_NOT_FOUND),
                    "statusDescription": INVALIDACCOUNT,
                },)
    except Exception as e:
        logger.error(f"Error validating transaction PIN: {e}")
        raise util.UnicornException(status=status.HTTP_401_UNAUTHORIZED,error={"statusCode": str(status.HTTP_404_NOT_FOUND),"statusDescription": SYSTEMBUSY,})
async def validateSelfTransaction(
    payload:PINRequest,
    setting: Setting = Depends(getSystemSetting),
    db: Session = Depends(get_db),
):
    try:
        logger.info(payload)
        account = customerQuery.getCustomerAccount(db=db,account=payload.accountNumber)
        if account:
            if account.customer:
                logger.info(f"checking if customer exist with account {payload.accountNumber}")
                if account.customer.blacklisted is False:
                    logger.info(f"checking if customer blacklisted status with account {payload.accountNumber}")
                    if account.customer.isUssdEnrolled:
                        logger.info(f"checking if customer ussd enrollment status with account {payload.accountNumber}")
                        if account.customer.active:
                            logger.info(f"checking if customer active status with account {payload.accountNumber}")
                            return account
                        else:
                            raise util.UnicornException(status=status.HTTP_403_FORBIDDEN,error={"statusCode": str(status.HTTP_403_FORBIDDEN),"statusDescription": INACTIVE,},)
                    else:
                        raise util.UnicornException(status=status.HTTP_403_FORBIDDEN,error={"statusCode": str(status.HTTP_403_FORBIDDEN),"statusDescription": USSDNOTENROLLED,},)
                else:
                    raise util.UnicornException(
                        status=status.HTTP_403_FORBIDDEN,
                        error={
                            "statusCode": str(status.HTTP_403_FORBIDDEN),
                            "statusDescription": BLACKLISTEDUSER,
                        },
                    )
            else:
                raise util.UnicornException(
                    status=status.HTTP_404_NOT_FOUND,
                    error={
                        "statusCode": str(status.HTTP_404_NOT_FOUND),
                        "statusDescription": UNKNOWNUSER,
                    },
                )
        else:
            logger.info(f"account {payload.accountNumber} not found")
            raise util.UnicornException(
                status=status.HTTP_404_NOT_FOUND,
                error={
                    "statusCode": str(status.HTTP_404_NOT_FOUND),
                    "statusDescription": INVALIDACCOUNT,
                },)
    except Exception as e:
        logger.error(f"Error validating transaction PIN: {e}")
        raise util.UnicornException(status=status.HTTP_401_UNAUTHORIZED,error={"statusCode": str(status.HTTP_404_NOT_FOUND),"statusDescription": SYSTEMBUSY,})


import logging
import secrets
from utils import util
from fastapi import Depends
from typing import Annotated
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from models.queries import settingQuery,adminQuery,customerQuery
from schemas.setting import Setting
from utils.constant import *
from schemas.admin import Admin
from schemas.base import PINRequest
from utils import redisUtil
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
def getSystemSetting(db: Session = Depends(get_db)):
    settings = settingQuery.setting(db=db)    
    if settings:
        logger.info(settings.app_name)
        return Setting.model_validate(settings)
    logger.info("Unable to get system setting. please check database settings for more info")
    exit(code=99)
async def validateTransactionPIN1(
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
                            pintries = await redisUtil.get_cache(key=f"account:{payload.msisdn}")
                            logger.info(f"pintries for account {payload.msisdn} is {pintries}")
                            logger.info(pintries)
                            pintries = int(pintries) if pintries else None
                            if pintries is None or pintries < setting.max_pin_tries:
                                if util.verify_password(payload.pin, account.customer.pin) is True:
                                    await redisUtil.delete_cache(key=f"account:{payload.msisdn}")
                                    return account
                                pintries = pintries + 1 if pintries else 1
                                logger.info(f"incrementing pintries for account {payload.msisdn} to {pintries}")
                                await redisUtil.incrementCounter(key=f"account:{payload.msisdn}")
                                raise util.UnicornException(status=status.HTTP_400_BAD_REQUEST,error={"statusCode": str(status.HTTP_400_BAD_REQUEST),"statusDescription": f"{INVALIDPIN}. You have {setting.max_pin_tries - pintries} attempt left",})
                            account.active = False
                            account.customer.active = False
                            account.blacklisted = True
                            account.customer.blacklisted = True
                            customerQuery.create(db=db,model=account)
                            raise util.UnicornException(status=status.HTTP_400_BAD_REQUEST,error={"statusCode": str(status.HTTP_400_BAD_REQUEST),"statusDescription": f"Your account has been disabled due to too many failed PIN attempts. Please contact customer support.",},)
                        raise util.UnicornException(status=status.HTTP_404_NOT_FOUND,error={"statusCode": str(status.HTTP_404_NOT_FOUND),"statusDescription": INACTIVE,},)
                    raise util.UnicornException(status=status.HTTP_404_NOT_FOUND,error={"statusCode": str(status.HTTP_404_NOT_FOUND),"statusDescription": USSDNOTENROLLED,},)
                raise util.UnicornException(status=status.HTTP_404_NOT_FOUND,error={"statusCode": str(status.HTTP_404_NOT_FOUND),"statusDescription": BLACKLISTEDUSER,},)
            raise util.UnicornException(status=status.HTTP_404_NOT_FOUND,error={"statusCode": str(status.HTTP_404_NOT_FOUND),"statusDescription": UNKNOWNUSER,},)
        logger.info(f"account {payload.accountNumber} not found")
        raise util.UnicornException(status=status.HTTP_404_NOT_FOUND,error={"statusCode": str(status.HTTP_404_NOT_FOUND),"statusDescription": INVALIDACCOUNT,},)
    except Exception as e:
        logger.error(f"Error validating transaction PIN: {e}")
        raise util.UnicornException(status=status.HTTP_400_BAD_REQUEST,error={"statusCode": str(status.HTTP_400_BAD_REQUEST),"statusDescription": SYSTEMBUSY,})
async def validateTransactionPIN(
    payload: PINRequest,
    setting: Setting = Depends(getSystemSetting),
    db: Session = Depends(get_db),
):
    try:
        logger.info(payload)

        account = customerQuery.getCustomerAccount(db=db, account=payload.accountNumber)
        if not account or not account.customer:
            raise util.UnicornException(
                status=status.HTTP_404_NOT_FOUND,
                error={"statusCode": str(status.HTTP_404_NOT_FOUND), "statusDescription": UNKNOWNUSER}
            )

        customer = account.customer
        logger.info(f"Verifying customer status for account {payload.accountNumber}")

        if customer.blacklisted:
            raise util.UnicornException(
                status=status.HTTP_404_NOT_FOUND,
                error={"statusCode": str(status.HTTP_404_NOT_FOUND), "statusDescription": BLACKLISTEDUSER}
            )

        if not customer.isUssdEnrolled:
            raise util.UnicornException(
                status=status.HTTP_404_NOT_FOUND,
                error={"statusCode": str(status.HTTP_404_NOT_FOUND), "statusDescription": USSDNOTENROLLED}
            )

        if not customer.active:
            raise util.UnicornException(
                status=status.HTTP_404_NOT_FOUND,
                error={"statusCode": str(status.HTTP_404_NOT_FOUND), "statusDescription": INACTIVE}
            )

        if util.formatPhoneFull(payload.receipient) == util.formatPhoneFull(customer.phonenumber):
            return account

        pintries_key = f"account:{payload.msisdn}"
        pintries = await redisUtil.get_cache(key=pintries_key)
        pintries = int(pintries) if pintries else 0

        logger.info(f"PIN tries for {payload.msisdn}: {pintries}")

        if pintries >= setting.max_pin_tries:
            customer.active = False
            customer.blacklisted = True
            account.active = False
            account.blacklisted = True
            customerQuery.create(db=db, model=account)
            raise util.UnicornException(
                status=status.HTTP_400_BAD_REQUEST,
                error={
                    "statusCode": str(status.HTTP_400_BAD_REQUEST),
                    "statusDescription": "Your account has been disabled due to too many failed PIN attempts. Please contact customer support.",
                },
            )

        if util.verify_password(payload.pin, customer.pin):
            await redisUtil.delete_cache(key=pintries_key)
            return account
        else:
            pintries += 1
            await redisUtil.incrementCounter(key=pintries_key)
            logger.info(f"Invalid PIN for {payload.msisdn}. Tries: {pintries}")
            raise util.UnicornException(
                status=status.HTTP_400_BAD_REQUEST,
                error={
                    "statusCode": str(status.HTTP_400_BAD_REQUEST),
                    "statusDescription": f"{INVALIDPIN}. You have {setting.max_pin_tries - pintries} attempt(s) left",
                },
            )

    except util.UnicornException as ue:
        raise ue
    except Exception as e:
        logger.error(f"Error validating transaction PIN: {e}")
        raise util.UnicornException(
            status=status.HTTP_400_BAD_REQUEST,
            error={
                "statusCode": str(status.HTTP_400_BAD_REQUEST),
                "statusDescription": SYSTEMBUSY,
            },
        )

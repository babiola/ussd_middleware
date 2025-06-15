import logging
import secrets
from utils import util
from fastapi import Depends
from typing import Annotated
from urllib.parse import urlparse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from models.queries import settingQuery,adminQuery
from services import adminservice
from schemas.setting import Setting
from utils.constant import *
from schemas.admin import Admin
from jose import jwt, JWTError
from utils.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends,status,Request
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

logger = logging.getLogger(__name__)

security = HTTPBasic()
# initialise fast api instance
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


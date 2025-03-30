from fastapi import APIRouter
from fastapi import (
    Depends,
    status,
    Response,
    Request,
    BackgroundTasks,
)
from schemas.customer import *
from schemas.vehicle import *
from schemas.setting import Setting
from sqlalchemy.orm import Session
from utils.constant import *
from typing import Annotated
from utils.dependencies import getSystemSetting, validateAdmin, getTenant
from utils.database import get_db
from services import customerservice
from schemas.admin import Admin
from utils import util
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/customers",
    tags=["customer"],
)
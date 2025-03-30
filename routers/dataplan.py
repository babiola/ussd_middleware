
import logging
from utils import util
from fastapi import APIRouter
from utils.database import get_db
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/customers",
    tags=["customer"],
)
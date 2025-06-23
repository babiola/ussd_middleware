
from sqlalchemy.orm import Session
from models.model import *
import logging

logger = logging.getLogger(__name__)

async def getProduts(db: Session):
    return db.query(ProductModel).all()
async def getProdutsForUssd(db: Session):
    return db.query(ProductModel).all()
def getProduct(db: Session, id: int):
    return db.query(ProductModel).filter(ProductModel.id == id).first()
def getBillers(db: Session):
    return db.query(ProductTypeModel).all()
def getBillersByproductId(db: Session, productId: int):
    return db.query(ProductTypeModel).filter(ProductTypeModel.product_id == productId).all()
def getBillerByBillerId(db: Session, billerId: str):
    return db.query(ProductTypeModel).filter(ProductTypeModel.billerId == billerId).first()
async def getPackagesBillerId(db: Session, billerId: str):
    return db.query(PackageModel).filter(PackageModel.billerId == billerId).all()
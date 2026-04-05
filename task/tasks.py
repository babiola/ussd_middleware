
import logging

from task.celery_app import celery_app
from datetime import datetime, timedelta
from utils.database import SessionLocal
from sqlalchemy import desc,asc
from utils import util
from models.model import TransactionModel,ServiceProviderModel,ProductModel,ProductTypeModel,PackageModel
from services.productservices import transactionRequery
logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def requery_pending_transactions(self):
    db = SessionLocal()
    cutoff = datetime.now() - timedelta(minutes=10)
    try:
        txns = (db.query(TransactionModel).filter(TransactionModel.statusCode == "C001",TransactionModel.created_at <= cutoff).order_by(asc(TransactionModel.created_at)).with_for_update().limit(5).all() )
        for txn in txns:
            if txn.reference:
                logger.info(f"Requerying transaction with reference {txn.reference} and status {txn.statusCode} for the time at {str(datetime.now())}")
                response = transactionRequery(db=db,transaction=txn)
                if response.statusCode == "200":
                    txn.statusCode = response.statusCode
                    txn.statusMessage = response.statusDescription
                else:
                    txn.statusCode = response.statusCode
                    txn.statusMessage = response.statusDescription
            else:
                txn.statusCode = "C13"
                txn.statusMessage = "Transaction has no reference for requery"
                logger.info(f"Transaction with id {txn.id} phone {txn.recipient} done at {txn.created_at} has no reference for requery at {str(datetime.now())}")
            txn.updated_at = datetime.now()
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
@celery_app.task(bind=True)
def run_product_updates(self):
    db = SessionLocal()
    try:
        provider = (db.query(ServiceProviderModel).filter(ServiceProviderModel.provider_code == "INSURTECHIT").first())
        if provider:
            logger.info(f"Started product update for provider {provider.provider_name} at {str(datetime.now())}")
            products = db.query(ProductModel).all()
            if products:
                logger.info(f"Found {len(products)} products to update for provider {provider.provider_name} at {str(datetime.now())}")
                for product in products:
                    providerProducts = util.http(url=f"{provider.provider_url}bill/billers",params={"loginId":provider.login_id,"key":provider.service_key,"product":product.vasType})
                    if providerProducts.status_code == 200:
                        logger.info(f"Successfully updated product {product.vasType} from provider {provider.provider_name} at {str(datetime.now())}")
                        jsonResponse = providerProducts.json()
                        if jsonResponse["statusCode"] == "00":
                            for productType in jsonResponse["data"]:
                                existingProductType = db.query(ProductTypeModel).filter(ProductTypeModel.billerId == productType["billerId"]).first()
                                if existingProductType:
                                    existingProductType.billerName = productType["billerName"]
                                    existingProductType.hasLookup = productType["hasLookup"]
                                    existingProductType.hasPackages = productType["hasPackages"]
                                    existingProductType.billerType = productType["billerType"]
                                    existingProductType.updated_at = datetime.now()
                                    existingProductType.service_provider_id = provider.id
                                    if productType["hasPackages"] and productType["packages"]:
                                        for package in productType["packages"]:
                                            dbPackage = db.query(PackageModel).filter(PackageModel.productId == package["packageCode"]).first()
                                            if dbPackage:
                                                dbPackage.productId = package["packageCode"]
                                                dbPackage.short_description = package["short_description"]
                                                dbPackage.product_type_id = existingProductType.id
                                                dbPackage.databundle = package["description"]
                                                dbPackage.validity = package["validity"]
                                                dbPackage.amount = str(int(package["amount"])*100)
                                                dbPackage.billerId = productType["billerId"]
                                                dbPackage.updated_at = datetime.now()
                                                db.commit()
                                            else:
                                                newPackage = PackageModel(
                                                    product_type_id=existingProductType.id,
                                                    productId=package["packageCode"],
                                                    short_description=package["short_description"],
                                                    databundle=package["description"],
                                                    validity=package["validity"],
                                                    status=True,
                                                    amount=str(int(package["amount"])*100),
                                                    billerId=productType["billerId"]
                                                )
                                                db.add(newPackage)
                                                db.commit()
                                    db.commit()
                                else:
                                    newProductType = ProductTypeModel(
                                        billerId=productType["billerId"],
                                        billerName=productType["billerName"],
                                        hasLookup=productType["hasLookup"],
                                        hasPackages=productType["hasPackages"],
                                        billerType=productType["billerType"],
                                        created_at = datetime.now(),
                                        product_id = product.id,
                                        service_provider_id = provider.id
                                    )
                                    db.add(newProductType)
                                    db.commit()
                                    db.refresh(newProductType)
                                    if productType["hasPackages"] and productType["packages"]:
                                        for package in productType["packages"]:
                                            newPackage = PackageModel(
                                                product_type_id=newProductType.id,
                                                productId=package["packageCode"],
                                                short_description=package["short_description"],
                                                databundle=package["description"],
                                                validity=package["validity"],
                                                status=True,
                                                amount=str(int(package["amount"])*100),
                                                billerId=productType["billerId"],
                                                created_at=datetime.now()
                                            )
                                            db.add(newPackage)
                                            db.commit()
            else:
                logger.info(f"No products found for provider {provider.provider_name} at {str(datetime.now())}")
        else:
            logger.info(f"No provider found with code INSURTECHIT for product update at {str(datetime.now())}")       
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
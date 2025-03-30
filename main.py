import logging
import secrets
from utils import util
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
)
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request
from utils.dependencies import middlewares
from middleware.http import LoggingMiddleware
from routers import auth,admin, customer, payment, provider,notification,product,pricing,policy

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
security = HTTPBasic()



app = FastAPI(debug=False,
    title="Digital Insurance Platform API",
    contact={
        "name": "Abiola Bello",
        "url": "https://www.linkedin.com/in/babiola",
    },
    middleware=middlewares,
)

# admin API
app.include_router(customer.router,)
app.include_router(bank.router,)
app.include_router(admin.router,)
app.include_router(provider.router,)
app.include_router(product.router,)
app.include_router(pricing.router,)
app.include_router(payment.router,)
app.include_router(policy.router,)
app.include_router(notification.router,)
app.mount("/static", StaticFiles(directory="views"), name="static")
app.add_middleware(LoggingMiddleware)
@app.exception_handler(util.UnicornException)
async def unicorn_exception_handler(request: Request, exc: util.UnicornException):
    return JSONResponse(status_code=exc.status,content=exc.name,)

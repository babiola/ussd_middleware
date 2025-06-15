import logging
from utils import util
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request
from utils.dependencies import middlewares
from middleware.http import LoggingMiddleware
from routers import bank,dataplan, customer, transaction,product

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI(debug=False,
    title="USSD MIDDLEWARE",
    root_path="/api/v1",
    contact={
        "name": "Abiola Bello",
        "url": "https://www.linkedin.com/in/babiola",
    },
    middleware=middlewares,
)
app.include_router(customer.router,prefix="/account",tags=['Account'])
app.include_router(product.router,tags=['Product'])
app.include_router(bank.router,tags=['Bank'])
app.include_router(transaction.router,prefix="/transaction",tags=['Statement'])
app.mount("/static", StaticFiles(directory="views"), name="static")
app.add_middleware(LoggingMiddleware)
@app.exception_handler(util.UnicornException)
async def unicorn_exception_handler(request: Request, exc: util.UnicornException):
    return JSONResponse(status_code=exc.status,content=exc.name,)

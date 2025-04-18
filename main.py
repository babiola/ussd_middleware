import logging
from utils import util
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request
from utils.dependencies import middlewares
from middleware.http import LoggingMiddleware
from routers import bank,dataplan, customer, transaction

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI(debug=False,
    title="Digital Insurance Platform API",
    contact={
        "name": "Abiola Bello",
        "url": "https://www.linkedin.com/in/babiola",
    },
    middleware=middlewares,
)
app.include_router(customer.router,)
app.include_router(bank.router,)
app.include_router(dataplan.router,)
app.include_router(transaction.router,)
app.mount("/static", StaticFiles(directory="views"), name="static")
app.add_middleware(LoggingMiddleware)
@app.exception_handler(util.UnicornException)
async def unicorn_exception_handler(request: Request, exc: util.UnicornException):
    return JSONResponse(status_code=exc.status,content=exc.name,)

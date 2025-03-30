from pydantic import BaseModel
from typing import Dict, Union


class BaseResponse(BaseModel):
    statusCode: str
    statusDescription: str
    data: Union[Dict, str] = None
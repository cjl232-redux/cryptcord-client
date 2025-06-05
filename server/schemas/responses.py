from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints

class BaseResponse(BaseModel):
    status: str
    message: str

class _PostMessageResponseData(BaseModel):
    timestamp: datetime
    nonce: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            max_length=32,
            min_length=32,
            to_lower=True,
            pattern='^[A-Fa-f0-9]*$',
        ),
    ]

class PostMessageResponse(BaseResponse):
    data: _PostMessageResponseData

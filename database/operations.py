# Eg. append messages from retrieved

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from server.schemas.responses import RetrieveExchangeKeysResponseModel

def add_exchange_keys(
        engine: Engine,
        response: RetrieveExchangeKeysResponseModel,
    ):
    for exchange_key in response.data.exchange_keys:
        exchange_key.
        message.


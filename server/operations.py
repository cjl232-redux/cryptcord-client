import requests

from base64 import urlsafe_b64encode

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from database.models import (
    Contact,
    FernetKey,
    ReceivedExchangeKey,
    SentExchangeKey,
)
from database.schemas.input import (
    ExchangeKeyInputSchema,
    FernetKeyInputSchema,
)
from database.schemas.output import (
    ContactKeyOutputSchema,
    PendingExchangeKeyOutputSchema,
)
from server.schemas.requests import PostExchangeKeyRequest
from server.schemas.responses import PostDataResponse
from settings import settings

def post_message():
    pass

def post_exchange_key(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
        contact_id: int,
        received_key_id: int | None = None,
    ):
    with Session(engine) as session:
        contact = ContactKeyOutputSchema.model_validate(
            session.get_one(Contact, contact_id),
        )
        if received_key_id is not None:
            received_key = PendingExchangeKeyOutputSchema.model_validate(
                session.get_one(ReceivedExchangeKey, received_key_id),
            )
            received_key = received_key.key
        else:
            received_key = None
    exchange_key = X25519PrivateKey.generate()
    signature = signature_key.sign(exchange_key.public_key().public_bytes_raw())
    request_body = PostExchangeKeyRequest.model_validate({
        'public_key': signature_key.public_key(),
        'recipient_public_key': contact.public_key,
        'signature': signature,
        'exchange_key': exchange_key.public_key(),
        'response_to': received_key if received_key is not None else None,
    })
    raw_response = requests.post(
        url=settings.server.post_exchange_key_url,
        json=request_body.model_dump(),
    )
    if 200 <= raw_response.status_code <= 299:
        response = PostDataResponse.model_validate(raw_response.json())
        if received_key is not None:
            secret_bytes = exchange_key.exchange(received_key)
            input = FernetKeyInputSchema.model_validate({
                'key': urlsafe_b64encode(secret_bytes),
                'timestamp': response.data.timestamp,
                'contact_id': contact_id,
            })
            with Session(engine) as session:
                session.add(FernetKey(**input.model_dump()))
                session.commit()
        else:
            input = ExchangeKeyInputSchema.model_validate({
                'key': urlsafe_b64encode(exchange_key.private_bytes_raw()),
                'contact_id': contact_id,
            })
            with Session(engine) as session:
                session.add(SentExchangeKey(**input.model_dump()))
                session.commit()



    
        




def retrieve_exchange_keys():
    pass
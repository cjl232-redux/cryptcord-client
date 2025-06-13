# Need to clean up retrieval, add proper nonce filtering, etc. Do it by a SELECT command, it's no slower than attempting to insert.
# 

import requests

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)

from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from database.models import (
    Contact,
    FernetKey,
    ReceivedExchangeKey,
    SentExchangeKey,
)
from database.schemas.input import (
    ReceivedExchangeKeyInputSchema,
    SentExchangeKeyInputSchema,
    FernetKeyInputSchema,
)
from database.schemas.output import (
    ContactOutputSchema,
    PendingExchangeKeyOutputSchema,

)
from server.schemas.requests import (
    PostExchangeKeyRequest,
    RetrieveDataRequest,
)
from server.schemas.responses import (
    PostDataResponse,
    RetrieveExchangeKeysResponseModel,
)
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
        contact = ContactOutputSchema.model_validate(
            session.get_one(Contact, contact_id),
        )
        if received_key_id is not None:
            received_key = PendingExchangeKeyOutputSchema.model_validate(
                session.get_one(ReceivedExchangeKey, received_key_id),
            )
            received_key = received_key.public_key
        else:
            received_key = None
    private_exchange_key = X25519PrivateKey.generate()
    public_exchange_key = private_exchange_key.public_key()
    signature = signature_key.sign(public_exchange_key.public_bytes_raw())
    request_body = PostExchangeKeyRequest.model_validate({
        'public_key': signature_key.public_key(),
        'recipient_public_key': contact.public_key,
        'signature': signature,
        'exchange_key': public_exchange_key,
        'response_to': received_key if received_key is not None else None,
    })
    raw_response = requests.post(
        url=settings.server.post_exchange_key_url,
        json=request_body.model_dump(),
    )
    if 200 <= raw_response.status_code <= 299:
        response = PostDataResponse.model_validate(raw_response.json())
        if received_key is not None:
            secret_bytes = private_exchange_key.exchange(received_key)
            input = FernetKeyInputSchema.model_validate({
                'key': urlsafe_b64encode(secret_bytes),
                'timestamp': response.data.timestamp,
                'contact_id': contact_id,
            })
            with Session(engine) as session:
                session.add(FernetKey(**input.model_dump()))
                session.commit()
        else:
            input = SentExchangeKeyInputSchema.model_validate({
                'private_key': private_exchange_key,
                'public_key': public_exchange_key,
                'contact_id': contact_id,
            })
            with Session(engine) as session:
                session.add(SentExchangeKey(**input.model_dump()))
                session.commit()

def retrieve_exchange_keys(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
    ):
    # Retrieve request filtering parameters.
    with Session(engine) as session:
        contact_dict: dict[str, int] = dict()
        for contact in session.scalars(select(Contact)):
            contact_dict[contact.public_key] = contact.id
        min_datetime = session.query(
            func.max(FernetKey.timestamp),
        ).scalar()
    if min_datetime is not None:
        min_datetime = min_datetime.replace(tzinfo=timezone.utc)
    # Construct and send the request.
    request_body = RetrieveDataRequest.model_validate({
        'public_key': signature_key.public_key(),
        'sender_keys': [x for x in contact_dict.keys()],
        'min_datetime': min_datetime,
    })
    raw_response = requests.post(
        url = settings.server.retrieve_exchange_keys_url,
        json=request_body.model_dump(),
    )
    if 200 <= raw_response.status_code <= 299:
        response = RetrieveExchangeKeysResponseModel.model_validate(
            raw_response.json(),
        )
        for element in response.data.exchange_keys:
            # Check the basic filtering conditions.
            if element.sender_key not in contact_dict:
                continue
            sender_key = Ed25519PublicKey.from_public_bytes(
                urlsafe_b64decode(element.sender_key),
            )
            try:
                sender_key.verify(
                    signature=urlsafe_b64decode(element.signature),
                    data=urlsafe_b64decode(element.key),
                )
            except InvalidSignature:
                continue
            if element.response_to is not None:
                with Session(engine) as session:
                    statement = select(
                        SentExchangeKey,
                    ).where(
                        SentExchangeKey.public_key == element.response_to,
                    )
                    sent_key = session.scalar(statement)
            else:
                sent_key = None
            if sent_key is not None:
                private_x25519_key = X25519PrivateKey.from_private_bytes(
                    urlsafe_b64decode(sent_key.private_key),
                )
                public_x25519_key = X25519PublicKey.from_public_bytes(
                    urlsafe_b64decode(element.key),
                )
                shared_secret = private_x25519_key.exchange(public_x25519_key)
                with Session(engine) as session:
                    fernet_key_obj = FernetKey(
                        key=urlsafe_b64encode(shared_secret),
                        timestamp=element.timestamp,
                        contact_id=contact_dict[element.sender_key],
                    )
                    session.add(fernet_key_obj)
                    try:
                        session.commit()
                    except:
                        session.rollback()
            else:
                with Session(engine, expire_on_commit=False) as session:
                    received_key_obj = ReceivedExchangeKey(
                        public_key=element.key,
                        contact_id=contact_dict[element.sender_key],
                    )
                    session.add(received_key_obj)
                    try:
                        session.commit()
                        post_exchange_key(
                            engine=engine,
                            signature_key=signature_key,
                            contact_id=contact_dict[element.sender_key],
                            received_key_id=received_key_obj.id,
                        )
                    except:
                        session.rollback()
    else:
        print('connection failed')
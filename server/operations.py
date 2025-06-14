# Need to clean up retrieval, add proper nonce filtering, etc. Do it by a SELECT command, it's no slower than attempting to insert.
# 

# Need a change in approach. Too much is happening in one function. Retrieval should simply store values, mass conversion to fernets should come separately.
# So should attempts to post keys in response to receiving a key that's not a response to your own.

import asyncio

from datetime import datetime, timezone
from types import CoroutineType
from typing import Any

import httpx

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from pydantic import BaseModel
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
)
from database.schemas.output import (
    ReceivedExchangeKeyOutputSchema,
)
from server.schemas.requests import (
    FetchDataRequest,
    PostExchangeKeyRequest,
)
from server.schemas.responses import (
    FetchExchangeKeysResponseModel,
    PostExchangeKeyResponseModel,
)
from settings import settings

def post_message():
    pass

# def post_exchange_key(
#         engine: Engine,
#         signature_key: Ed25519PrivateKey,
#         contact_id: int,
#         received_key_id: int | None = None,
#     ):
#     with Session(engine) as session:
#         contact = ContactOutputSchema.model_validate(
#             session.get_one(Contact, contact_id),
#         )
#         if received_key_id is not None:
#             received_key = PendingExchangeKeyOutputSchema.model_validate(
#                 session.get_one(ReceivedExchangeKey, received_key_id),
#             )
#             received_key = received_key.public_key
#         else:
#             received_key = None
#     private_exchange_key = X25519PrivateKey.generate()
#     public_exchange_key = private_exchange_key.public_key()
#     signature = signature_key.sign(public_exchange_key.public_bytes_raw())
#     request_body = PostExchangeKeyRequest.model_validate({
#         'public_key': signature_key.public_key(),
#         'recipient_public_key': contact.public_key,
#         'signature': signature,
#         'exchange_key': public_exchange_key,
#         'response_to': received_key if received_key is not None else None,
#     })
#     raw_response = requests.post(
#         url=settings.server.post_exchange_key_url,
#         json=request_body.model_dump(),
#     )
#     if 200 <= raw_response.status_code <= 299:
#         response = PostDataResponse.model_validate(raw_response.json())
#         if received_key is not None:
#             secret_bytes = private_exchange_key.exchange(received_key)
#             input = FernetKeyInputSchema.model_validate({
#                 'key': urlsafe_b64encode(secret_bytes),
#                 'timestamp': response.data.timestamp,
#                 'contact_id': contact_id,
#             })
#             with Session(engine) as session:
#                 session.add(FernetKey(**input.model_dump()))
#                 session.commit()
#         else:
#             input = SentExchangeKeyInputSchema.model_validate({
#                 'private_key': private_exchange_key,
#                 'public_key': public_exchange_key,
#                 'contact_id': contact_id,
#             })
#             with Session(engine) as session:
#                 session.add(SentExchangeKey(**input.model_dump()))
#                 session.commit()

def retrieve_exchange_keys(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
    ):
    # Retrieve request filtering parameters.
    with Session(engine) as session:
        contact_dict: dict[str, int] = {
            x.public_key: x.id
            for x in session.scalars(select(Contact))
        }
        min_datetime: datetime | None = session.query(
            func.max(FernetKey.timestamp)
        ).scalar()
        if min_datetime is not None:
            min_datetime = min_datetime.astimezone(timezone.utc)
    # Do not send any request if no contacts are registered.
    if not contact_dict:
        return
    # Otherwise, construct and send the request.
    request_body = FetchDataRequest.model_validate({
        'public_key': signature_key.public_key(),
        'sender_keys': [x for x in contact_dict.keys()],
        'min_datetime': min_datetime,
    })
    raw_response = httpx.post(
        url = settings.server.retrieve_exchange_keys_url,
        json=request_body.model_dump(),
    )
    # Add any returned keys that haven't already been stored.
    if 200 <= raw_response.status_code <= 299:
        response = FetchExchangeKeysResponseModel.model_validate(
            raw_response.json(),
        )
        for element in response.data.elements:
            # Check the basic filtering conditions.
            if element.sender_public_key_b64 not in contact_dict:
                continue
            elif not element.is_valid:
                continue
            # If they're met, store the key.
            elif element.initial_exchange_key is not None:
                statement = select(
                    SentExchangeKey,
                ).where(
                    SentExchangeKey.public_key
                    == element.initial_exchange_key_b64,
                ).join(
                    ReceivedExchangeKey,
                ).where(
                    ReceivedExchangeKey.fernet_key_id == None,
                )
                with Session(engine) as session:
                    obj = session.scalar(statement)
                if obj is not None:
                    sent_exchange_key_id = obj.id
                else:
                    sent_exchange_key_id = None
            else:
                sent_exchange_key_id = None
            input = ReceivedExchangeKeyInputSchema.model_validate({
                'public_key': element.transmitted_exchange_key,
                'timestamp': element.timestamp,
                'contact_id': contact_dict[element.sender_public_key_b64],
                'sent_exchange_key_id': sent_exchange_key_id,
            })
            with Session(engine) as session:
                session.add(ReceivedExchangeKey(**input.model_dump()))
                try:
                    session.commit()
                except:
                    session.rollback()
    else:
        print(raw_response.json())
        print('connection failed')

class _OutboundExchangeKeyContext(BaseModel):
    received_key_id: int
    private_exchange_key: X25519PrivateKey
    request: PostExchangeKeyRequest
    class Config:
        arbitrary_types_allowed = True

def post_pending_exchange_keys(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
    ):
    """Sends exchange keys for all received keys not yet matched with one."""
    # Define async functions to run connections through.
    async def post_one(
        client: httpx.AsyncClient,
        outbound_context: _OutboundExchangeKeyContext,
        ):
        raw_response = await client.post(
            url=settings.server.post_exchange_key_url,
            json=outbound_context.request.model_dump(),
        )
        if 200 <= raw_response.status_code <= 299:
            response = PostExchangeKeyResponseModel.model_validate(
                raw_response.json(),
            )
            return (outbound_context, response)
        else:
            return (outbound_context, None)
    async def post_all(outbound_contexts: list[_OutboundExchangeKeyContext]):
        async with httpx.AsyncClient() as client:
            tasks = [post_one(client, x) for x in outbound_contexts]
            return await asyncio.gather(*tasks)
        
    # Gather all the relevant keys and assemble requests.
    statement = select(
        ReceivedExchangeKey
    ).where(
        ReceivedExchangeKey.sent_exchange_key == None,
    ).where(
        ReceivedExchangeKey.fernet_key == None,
    )
    outbound_contexts: list[_OutboundExchangeKeyContext] = list()
    with Session(engine) as session:
        for id, output in (
            (obj.id, ReceivedExchangeKeyOutputSchema.model_validate(obj))
            for obj in session.scalars(statement).all()
        ):
            assert output.sent_exchange_key is not None
            private_key = X25519PrivateKey.generate()
            public_key = private_key.public_key()
            signature = signature_key.sign(public_key.public_bytes_raw())
            request = PostExchangeKeyRequest.model_validate({
                'recipient_public_key': output.contact.public_key,
                'response_to': output.sent_exchange_key.public_key,
                'public_exchange_key': public_key,
                'signature': signature,
            })
            outbound_contexts.append(_OutboundExchangeKeyContext(
                received_key_id=id,
                private_exchange_key=private_key,
                request=request,
            ))
    
    with Session(engine) as session:
        for context, response in asyncio.run(post_all(outbound_contexts)):
            if response is not None:
                received_key = session.get_one(
                    ReceivedExchangeKey,
                    context.received_key_id,
                )
                input = SentExchangeKeyInputSchema.model_validate({
                    'private_key': context.private_exchange_key,
                    'public_key': context.private_exchange_key.public_key(),
                })
                sent_exchange_key = SentExchangeKey(**input.model_dump())
                received_key.sent_exchange_key = sent_exchange_key
                try:
                    session.commit()
                except:
                    session.rollback()


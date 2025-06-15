# Need to clean up retrieval, add proper nonce filtering, etc. Do it by a SELECT command, it's no slower than attempting to insert.
# 

# Need a change in approach. Too much is happening in one function. Retrieval should simply store values, mass conversion to fernets should come separately.
# So should attempts to post keys in response to receiving a key that's not a response to your own.

import asyncio

from datetime import datetime, timezone

import httpx

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from pydantic import BaseModel
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from database.models import (
    Contact,
    FernetKey,
    Message,
    MessageType,
    ReceivedExchangeKey,
    SentExchangeKey,
)
from database.operations.messages import add_fetched_messages
from database.operations.exchange_keys import add_fetched_exchange_keys
from database.schemas.input import (
    MessageInputSchema,
    ReceivedExchangeKeyInputSchema,
    SentExchangeKeyInputSchema,
)
from database.schemas.output import (
    ContactOutputSchema,
    FernetKeyOutputSchema,
    ReceivedExchangeKeyOutputSchema,
)
from schema_components.validators import key_to_base64
from server.schemas.requests import (
    FetchDataRequest,
    PostExchangeKeyRequestModel,
    PostMessageRequestModel,
)
from server.schemas.responses import (
    FetchDataResponse,
    FetchExchangeKeysResponseModel,
    FetchMessagesResponseModel,
    PostExchangeKeyResponseModel,
    PostMessageResponseModel,
)
from settings import settings

CLIENT = httpx.Client()

def fetch_data(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
    ):
    """Fetch all data stored on the server that is addressed to the user."""
    with Session(engine) as session:
        contact_dict: dict[str, int] = {
            x.public_key: x.id
            for x in session.scalars(select(Contact))
        }
    if not contact_dict:
        return
    request = FetchDataRequest.model_validate({
        'public_key': signature_key.public_key(),
        'sender_keys': [x for x in contact_dict.keys()],
    })
    raw_response = CLIENT.post(
        url=settings.server.fetch_data_url,
        json=request.model_dump(),
    )
    if raw_response.status_code == 200:
        response = FetchDataResponse.model_validate(raw_response.json())
        add_fetched_messages(engine, response.data.messages)
        add_fetched_exchange_keys(engine, response.data.exchange_keys)
            

# def retrieve_messages(
#         engine: Engine,
#         signature_key: Ed25519PrivateKey,
#     ):
#     # Retrieve request filtering parameters.
#     with Session(engine) as session:
#         contact_dict: dict[str, int] = {
#             x.public_key: x.id
#             for x in session.scalars(select(Contact))
#         }
#         min_datetime: datetime | None = session.query(
#             func.max(FernetKey.timestamp)
#         ).scalar()
#         if min_datetime is not None:
#             min_datetime = min_datetime.astimezone(timezone.utc)
#     # Do not send any request if no contacts are registered.
#     if not contact_dict:
#         return
#     # Otherwise, construct and send the request.
#     request_body = FetchDataRequest.model_validate({
#         'public_key': signature_key.public_key(),
#         'sender_keys': [x for x in contact_dict.keys()],
#         'min_datetime': min_datetime,
#     })
#     raw_response = CLIENT.post(
#         url = settings.server.retrieve_messages_url,
#         json=request_body.model_dump(),
#     )
#     # Add any returned keys that haven't already been stored.
#     if 200 <= raw_response.status_code <= 299:
#         response = FetchMessagesResponseModel.model_validate(
#             raw_response.json(),
#         )
#         with Session(engine) as session:
#             for element in response.data.elements:
#                 # Check the basic filtering conditions.
#                 if key_to_base64(element.sender_public_key) not in contact_dict:
#                     continue
#                 elif not element.is_valid:
#                     continue
#                 contact_id = contact_dict[
#                     key_to_base64(element.sender_public_key)
#                 ]
#                 obj = session.scalar(
#                     select(
#                         FernetKey,
#                     ).where(
#                         FernetKey.contact_id == contact_id,
#                     ).order_by(
#                         FernetKey.timestamp.desc(),
#                     )
#                 )
#                 if obj is not None:
#                     fernet_output = FernetKeyOutputSchema.model_validate(obj)
#                     message_input = MessageInputSchema.model_validate({
#                         'text': fernet_output.key.decrypt(
#                             element.encrypted_text
#                         ).decode(),
#                         'timestamp': element.timestamp,
#                         'message_type': MessageType.RECEIVED,
#                         'nonce': element.nonce,
#                         'contact_id': contact_id,
#                     })
#                     session.add(
#                         ReceivedExchangeKey(**message_input.model_dump()),
#                     )
#                     try:
#                         session.commit()
#                     except:
#                         session.rollback()
#     else:
#         print(raw_response.json())
#         print('connection failed')

# def retrieve_exchange_keys(
#         engine: Engine,
#         signature_key: Ed25519PrivateKey,
#     ):
#     # Retrieve request filtering parameters.
#     with Session(engine) as session:
#         contact_dict: dict[str, int] = {
#             x.public_key: x.id
#             for x in session.scalars(select(Contact))
#         }
#         min_datetime: datetime | None = session.query(
#             func.max(FernetKey.timestamp)
#         ).scalar()
#         if min_datetime is not None:
#             min_datetime = min_datetime.astimezone(timezone.utc)
#     # Do not send any request if no contacts are registered.
#     if not contact_dict:
#         return
#     # Otherwise, construct and send the request.
#     request_body = FetchDataRequest.model_validate({
#         'public_key': signature_key.public_key(),
#         'sender_keys': [x for x in contact_dict.keys()],
#         'min_datetime': min_datetime,
#     })
#     raw_response = CLIENT.post(
#         url = settings.server.retrieve_exchange_keys_url,
#         json=request_body.model_dump(),
#     )
#     # Add any returned keys that haven't already been stored.
#     if 200 <= raw_response.status_code <= 299:
#         response = FetchExchangeKeysResponseModel.model_validate(
#             raw_response.json(),
#         )
#         for element in response.data.elements:
#             # Check the basic filtering conditions.
#             if key_to_base64(element.sender_public_key) not in contact_dict:
#                 continue
#             elif not element.is_valid:
#                 continue
#             # If they're met, store the key.
#             elif element.initial_exchange_key is not None:
#                 statement = select(
#                     SentExchangeKey,
#                 ).where(
#                     SentExchangeKey.public_key
#                     == key_to_base64(element.initial_exchange_key)
#                 ).join(
#                     ReceivedExchangeKey,
#                 ).where(
#                     ReceivedExchangeKey.fernet_key_id == None,
#                 )
#                 with Session(engine) as session:
#                     obj = session.scalar(statement)
#                 if obj is not None:
#                     sent_exchange_key_id = obj.id
#                 else:
#                     sent_exchange_key_id = None
#             else:
#                 sent_exchange_key_id = None
#             input = ReceivedExchangeKeyInputSchema.model_validate({
#                 'public_key': element.transmitted_exchange_key,
#                 'timestamp': element.timestamp,
#                 'contact_id': contact_dict[
#                     key_to_base64(element.sender_public_key)
#                 ],
#                 'sent_exchange_key_id': sent_exchange_key_id,
#             })
#             with Session(engine) as session:
#                 session.add(ReceivedExchangeKey(**input.model_dump()))
#                 try:
#                     session.commit()
#                 except:
#                     session.rollback()
#     else:
#         print(raw_response.json())
#         print('connection failed')

def post_message(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
        plaintext: str,
        contact_id: int,
    ) -> bool:
    # Retrieve the latest Fernet key for the contact and encrypt the message.
    with Session(engine) as session:
        obj = session.scalar(
            select(
                FernetKey,
            ).where(
                FernetKey.contact_id == contact_id,
            ).order_by(
                FernetKey.timestamp.desc(),
            )
        )
        if obj is None:
            raise ValueError('No encryption key available for contact.')
        print(obj.key)
        output = FernetKeyOutputSchema.model_validate(obj)
    ciphertext = output.key.encrypt(plaintext.encode())
    # Construct and send the request.
    print(f'Ciphertext: {ciphertext}')
    signature = signature_key.sign(ciphertext)
    print(f'Signature: {signature}')
    request = PostMessageRequestModel.model_validate({
        'public_key': signature_key.public_key(),
        'recipient_public_key': output.contact.public_key,
        'encrypted_text': ciphertext,
        'signature': signature,
    })
    raw_response = CLIENT.post(
        url = settings.server.post_message_url,
        json=request.model_dump(),
    )
    if 200 <= raw_response.status_code <= 299:
        response = PostMessageResponseModel.model_validate(
            raw_response.json(),
        )
        message_input = MessageInputSchema.model_validate({
            'text': plaintext,
            'timestamp': response.data.timestamp,
            'message_type': MessageType.SENT,
            'contact_id': contact_id,
            'nonce': response.data.nonce,
        })
        with Session(engine) as session:
            session.add(Message(**message_input.model_dump()))
            try:
                session.commit()
                return True
            except:
                session.rollback()
    return False

class _OutboundExchangeKeyContext(BaseModel):
    received_key_id: int
    private_exchange_key: X25519PrivateKey
    request: PostExchangeKeyRequestModel
    class Config:
        arbitrary_types_allowed = True

def post_exchange_key(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
        contact_id: int,
    ):
    with Session(engine) as session:
        obj = session.get(Contact, contact_id)
        if obj is not None:
            contact = ContactOutputSchema.model_validate(obj)
            new_private_key = X25519PrivateKey.generate()
            new_public_key = new_private_key.public_key()
            signature = signature_key.sign(new_public_key.public_bytes_raw())
            request = PostExchangeKeyRequestModel.model_validate({
                'public_key': signature_key.public_key(),
                'recipient_public_key': contact.public_key,
                'transmitted_exchange_key': new_public_key,
                'signature': signature,
            })
            raw_response = CLIENT.post(
                settings.server.post_exchange_key_url,
                json=request.model_dump(),
            )
            if 200 <= raw_response.status_code <= 299:
                input = SentExchangeKeyInputSchema.model_validate({
                    'private_key': new_private_key,
                    'public_key': new_public_key,
                })
                session.add(SentExchangeKey(**input.model_dump()))
                try:
                    session.commit()
                except:
                    session.rollback()

# Fragility! Need to handle duplicates (which will cause an error raised on the server side)
def post_pending_exchange_keys(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
    ):
    """Sends exchange keys for all received keys not yet matched with one."""
    with Session(engine) as session:
        query = (
            select(ReceivedExchangeKey)
            .where(ReceivedExchangeKey.sent_exchange_key == None)
            .where(ReceivedExchangeKey.fernet_key == None)
        )
        for obj in session.scalars(query):
            output = ReceivedExchangeKeyOutputSchema.model_validate(obj)
            new_private_key = X25519PrivateKey.generate()
            new_public_key = new_private_key.public_key()
            signature = signature_key.sign(new_public_key.public_bytes_raw())
            request = PostExchangeKeyRequestModel.model_validate({
                'public_key': signature_key.public_key(),
                'recipient_public_key': output.contact.public_key,
                'transmitted_exchange_key': new_public_key,
                'initial_exchange_key': output.public_key,
                'signature': signature,
            })
            raw_response = CLIENT.post(
                settings.server.post_exchange_key_url,
                json=request.model_dump(),
            )
            if raw_response.status_code == 200:
                response = PostExchangeKeyResponseModel.model_validate(
                    raw_response.json(),
                )
                obj.timestamp = response.data.timestamp
                input = SentExchangeKeyInputSchema.model_validate({
                    'private_key': new_private_key,
                    'public_key': new_public_key,
                })
                obj.sent_exchange_key = SentExchangeKey(**input.model_dump())
        session.commit()
    return
    # Define async functions to run connections through.
    async def post_one(
            outbound_context: _OutboundExchangeKeyContext,
            client: httpx.AsyncClient,
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
            tasks = [post_one(x, client) for x in outbound_contexts]
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
        for obj in session.scalars(statement):
            received_key = ReceivedExchangeKeyOutputSchema.model_validate(obj)
            new_private_key = X25519PrivateKey.generate()
            new_public_key = new_private_key.public_key()
            signature = signature_key.sign(new_public_key.public_bytes_raw())
            request = PostExchangeKeyRequest.model_validate({
                'public_key': signature_key.public_key(),
                'recipient_public_key': received_key.contact.public_key,
                'transmitted_exchange_key': new_public_key,
                'initial_exchange_key': received_key.public_key,
                'signature': signature,
            })
            outbound_contexts.append(_OutboundExchangeKeyContext(
                received_key_id=received_key.id,
                private_exchange_key=new_private_key,
                request=request,
            ))
    print(outbound_contexts)
    exit()
    
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
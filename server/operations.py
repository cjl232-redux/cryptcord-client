import httpx

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from database.models import (
    Contact,
    ReceivedKey,
    SentKey,
)
from database.operations.messages import (
    add_fetched_messages,
    add_posted_message,
)
from database.operations.exchange_keys import add_fetched_keys, add_sent_key
from database.schemas.output import (
    ContactOutputSchema,
    ReceivedKeyOutputSchema,
)
from server.exceptions import (
    MissingFernetKey,
    ClientError,
    ServerError,
)
from server.schemas.requests import (
    FetchDataRequest,
    PostKeyRequestModel,
    PostMessageRequestModel,
)
from server.schemas.responses import (
    FetchDataResponse,
    PostKeyResponseModel,
    PostMessageResponseModel,
)
from settings import settings

def check_connection(http_client: httpx.Client) -> bool:
    try:
        http_client.get(
            url=settings.server.ping_url,
            timeout=settings.server.ping_timeout,
        )
        return True
    except (httpx.ConnectError, httpx.TimeoutException):
        return False

def fetch_data(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
        http_client: httpx.Client,
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
    raw_response = http_client.post(
        url=settings.server.fetch_data_url,
        json=request.model_dump(),
    )
    if raw_response.status_code == 200:
        response = FetchDataResponse.model_validate(raw_response.json())
        add_fetched_messages(engine, response.data.messages)
        add_fetched_keys(engine, response.data.exchange_keys)

def post_exchange_key(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
        http_client: httpx.Client,
        contact: ContactOutputSchema,
        initial_key: ReceivedKeyOutputSchema | None = None,
    ):
    private_key = X25519PrivateKey.generate()
    public_key = private_key.public_key()
    request = PostKeyRequestModel.model_validate({
        'public_key': signature_key.public_key(),
        'recipient_public_key': contact.public_key,
        'transmitted_exchange_key': public_key,
        'initial_exchange_key': (
            initial_key.public_key if initial_key is not None else None
        ),
        'signature': signature_key.sign(public_key.public_bytes_raw()),
    })
    raw_response = http_client.post(
        url = settings.server.post_exchange_key_url,
        json=request.model_dump(),
    )
    if 400 <= raw_response.status_code < 500:
        raise ClientError(raw_response)
    elif 500 <= raw_response.status_code:
        raise ServerError(raw_response)
    response = PostKeyResponseModel.model_validate(raw_response.json())
    add_sent_key(engine, private_key, initial_key, response.data.timestamp)

# TODO expand outputs to avoid this clunky workaround rather than
# essentially doing a join
def post_initial_contact_keys(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
        http_client: httpx.Client,
    ):
    with Session(engine) as session:
        for obj in session.scalars(select(Contact)):
            contact = ContactOutputSchema.model_validate(obj)
            received_key_query = (
                select(ReceivedKey)
                .where(ReceivedKey.contact_id == contact.id)
            )
            sent_key_query = (
                select(SentKey)
                .where(ReceivedKey.contact_id == contact.id)
                .join(ReceivedKey)
            )
            received_key = session.scalar(received_key_query)
            sent_key = session.scalar(sent_key_query)
            if received_key is None and sent_key is None:
                post_exchange_key(engine, signature_key, http_client, contact)

def post_pending_exchange_keys(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
        http_client: httpx.Client,
    ):
    with Session(engine) as session:
        query = (
            select(ReceivedKey)
            .where(ReceivedKey.sent_key == None)
            .where(ReceivedKey.fernet_key == None)
        )
        received_keys = [
            ReceivedKeyOutputSchema.model_validate(x)
            for x in session.scalars(query).all()
        ]
    for received_key in received_keys:
        post_exchange_key(
            engine=engine,
            signature_key=signature_key,
            http_client=http_client,
            contact=received_key.contact,
            initial_key=received_key,
        )

def post_message(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
        http_client: httpx.Client,
        plaintext: str,
        contact: ContactOutputSchema,
    ):
    """Post a specified message to the server, storing it on success."""
    contact_public_key, fernet_key = _get_message_keys(contact)
    ciphertext = fernet_key.encrypt(plaintext.encode())
    request = PostMessageRequestModel.model_validate({
        'public_key': signature_key.public_key(),
        'recipient_public_key': contact_public_key,
        'encrypted_text': ciphertext.decode(),
        'signature': signature_key.sign(ciphertext),
    })
    raw_response = http_client.post(
        url = settings.server.post_message_url,
        json=request.model_dump(),
    )
    if 400 <= raw_response.status_code < 500:
        raise ClientError(raw_response)
    elif 500 <= raw_response.status_code:
        raise ServerError(raw_response) 
    response = PostMessageResponseModel.model_validate(raw_response.json())
    timestamp, nonce = (response.data.timestamp, response.data.nonce)
    add_posted_message(engine, plaintext, contact.id, timestamp, nonce)

# type _key_exchange_keys = tuple[
#     Ed25519PublicKey,
#     X25519PublicKey | None,
#     X25519PrivateKey,
#     X25519PublicKey,
# ]

# # def _get_key_exchange_keys(
# #         engine: Engine,
# #         contact: ContactOutputSchema,
# #         initial_key_id: int | None = None,
# #     ) -> _key_exchange_keys:
# #     with Session(engine) as session:
# #         contact = session.get_one(Contact, contact_id)
# #         contact_output = ContactOutputSchema.model_validate(contact)
# #         contact_key = contact_output.public_key
# #         if initial_key_id is not None:
# #             initial_x_key_output = ReceivedKeyOutputSchema.model_validate(
# #                 session.get_one(ReceivedKey, initial_key_id),
# #             )
# #             initial_x_key = initial_x_key_output.public_key
# #         else:
# #             initial_x_key = None
# #     private_x_key = X25519PrivateKey.generate()
# #     public_x_key = private_x_key.public_key()
# #     return contact_key, initial_x_key, private_x_key, public_x_key

def _get_message_keys(
        contact: ContactOutputSchema,
    ) -> tuple[Ed25519PublicKey, Fernet]:
    if not contact.fernet_keys:
        raise MissingFernetKey(f'No fernet keys exist for {contact.name}')
    return contact.public_key, contact.fernet_keys[-1].key
import httpx

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
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
    FernetKeyOutputSchema,
    ReceivedKeyOutputSchema,
)
from server.exceptions import (
    MissingFernetKey,
    ResponseClientError,
    ResponseServerError,
    ResponseUnknownError,
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

CLIENT = httpx.Client()

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
        contact_id: int,
        initial_key_id: int | None = None,
    ):
    keys = _get_key_exchange_keys(
        engine,
        contact_id,
        initial_key_id,
    )
    request = PostKeyRequestModel.model_validate({
        'public_key': signature_key.public_key(),
        'recipient_public_key': keys[0],
        'initial_exchange_key': keys[1],
        'transmitted_exchange_key': keys[3],
        'signature': signature_key.sign(keys[3].public_bytes_raw()),
    })
    raw_response = http_client.post(
        url = settings.server.post_exchange_key_url,
        json=request.model_dump(),
    )
    if 400 <= raw_response.status_code < 500:
        raise ResponseClientError(raw_response.json())
    elif 500 <= raw_response.status_code:
        raise ResponseServerError(raw_response.json())
    elif raw_response.status_code != 201:
        raise ResponseUnknownError(raw_response.json())    
    response = PostKeyResponseModel.model_validate(raw_response.json())
    add_sent_key(engine, keys[2], initial_key_id, response.data.timestamp)

def post_initial_contact_keys(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
    ):
    contact_ids: list[int] = []
    with Session(engine) as session:
        for contact_id in session.scalars(select(Contact.id)):
            received_key_query = (
                select(ReceivedKey)
                .where(ReceivedKey.contact_id == contact_id)
            )
            sent_key_query = (
                select(SentKey)
                .where(SentKey.contact_id == contact_id)
            )
            received_key = session.scalar(received_key_query)
            sent_key = session.scalar(sent_key_query)
            if received_key is None and sent_key is None:
                contact_ids.append(contact_id)
    for contact_id in contact_ids:
        post_exchange_key(engine, signature_key, contact_id)


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
            contact_id=received_key.contact.id,
            initial_key_id=received_key.id,
        )

def post_message(
        engine: Engine,
        signature_key: Ed25519PrivateKey,
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
    try:
        raw_response = CLIENT.post(
            url = settings.server.post_message_url,
            json=request.model_dump(),
        )
    except httpx.ConnectError:
        raise ResponseServerError('Server connection failed.')
    if 400 <= raw_response.status_code < 500:
        raise ResponseClientError(raw_response.json())
    elif 500 <= raw_response.status_code:
        raise ResponseServerError(raw_response.json())
    elif raw_response.status_code != 201:
        raise ResponseUnknownError(raw_response.json())    
    response = PostMessageResponseModel.model_validate(raw_response.json())
    timestamp, nonce = (response.data.timestamp, response.data.nonce)
    add_posted_message(engine, plaintext, contact.id, timestamp, nonce)

type _key_exchange_keys = tuple[
    Ed25519PublicKey,
    X25519PublicKey | None,
    X25519PrivateKey,
    X25519PublicKey,
]

def _get_key_exchange_keys(
        engine: Engine,
        contact_id: ContactOutputSchema,
        initial_key_id: int | None = None,
    ) -> _key_exchange_keys:
    with Session(engine) as session:
        contact = session.get_one(Contact, contact_id)
        contact_output = ContactOutputSchema.model_validate(contact)
        contact_key = contact_output.public_key
        if initial_key_id is not None:
            initial_x_key_output = ReceivedKeyOutputSchema.model_validate(
                session.get_one(ReceivedKey, initial_key_id),
            )
            initial_x_key = initial_x_key_output.public_key
        else:
            initial_x_key = None
    private_x_key = X25519PrivateKey.generate()
    public_x_key = private_x_key.public_key()
    return contact_key, initial_x_key, private_x_key, public_x_key

def _get_message_keys(
        contact: ContactOutputSchema,
    ) -> tuple[Ed25519PublicKey, Fernet]:
    if not contact.fernet_keys:
        raise MissingFernetKey(f'No fernet keys exist for {contact.name}')
    return contact.public_key, contact.fernet_keys[-1].key
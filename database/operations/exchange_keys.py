from base64 import urlsafe_b64encode
from datetime import datetime

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from database.models import Contact, ReceivedKey, SentKey
from database.schemas.input import ReceivedKeyInputSchema, SentKeyInputSchema
from server.schemas.responses import FetchedKey

def add_fetched_keys(
        engine: Engine,
        fetched_keys: list[FetchedKey],
    ):
    """Stores exchange keys retrieved from a server."""
    contact_cache: dict[bytes, int | None] = dict()
    with Session(engine) as session:
        for fetched_key in fetched_keys:
            exchange_key = _process_fetched_key(
                session,
                fetched_key,
                contact_cache,
            )
            if exchange_key is not None:
                session.add(exchange_key)
        session.commit()

def add_sent_key(
        engine: Engine,
        private_key: X25519PrivateKey,
        received_key_id: int | None,
        response_timestamp: datetime | None,
    ):
    input = SentKeyInputSchema.model_validate({
        'private_key': private_key,
        'public_key': private_key.public_key(),
    })
    sent_key = SentKey(**input.model_dump())
    with Session(engine) as session:
        if received_key_id is not None:
            received_key = session.get_one(ReceivedKey, received_key_id)
            received_key.sent_key = sent_key
            if response_timestamp is not None:
                received_key.timestamp = response_timestamp
        else:
            session.add(sent_key)
        session.commit()

def _create_received_key_object(
        key: FetchedKey,
        contact_id: int,
        sent_key_id: int | None,
    ) -> ReceivedKey | None:
    key_input = ReceivedKeyInputSchema.model_validate({
        'public_key': key.transmitted_exchange_key,
        'contact_id': contact_id,
        'timestamp': key.timestamp,
        'sent_key_id': sent_key_id,
    })
    return ReceivedKey(**key_input.model_dump())

def _get_contact_id(session: Session, key_bytes: bytes) -> int | None:
    b64_key = urlsafe_b64encode(key_bytes).decode()
    id_query = (
        select(Contact.id)
        .where(Contact.public_key == b64_key)
    )
    return session.scalar(id_query)

def _get_sent_key_id(session: Session, key_bytes: bytes) -> int | None:
    b64_key = urlsafe_b64encode(key_bytes).decode()
    id_query = (
        select(SentKey.id)
        .where(SentKey.public_key == b64_key)
    )
    return session.scalar(id_query)

def _is_valid_received_key(session: Session, key_bytes: bytes) -> bool:
    b64_key = urlsafe_b64encode(key_bytes).decode()
    query = (
        select(ReceivedKey)
        .where(ReceivedKey.public_key == b64_key)
    )
    return session.scalar(query) is None

def _is_valid_sent_key_id(session: Session, id: int | None) -> bool:
    if id is None:
        return True
    return session.get(SentKey, id) is not None

def _process_fetched_key(
        session: Session,
        key: FetchedKey,
        cache: dict[bytes, int | None],
    ) -> ReceivedKey | None:
    key_bytes = key.transmitted_exchange_key.public_bytes_raw()
    if not key.is_valid or not _is_valid_received_key(session, key_bytes):
        return None
    sender_key_bytes = key.sender_public_key.public_bytes_raw()
    if sender_key_bytes not in cache:
        cache[sender_key_bytes] = _get_contact_id(session, sender_key_bytes)
    contact_id = cache[sender_key_bytes]
    if contact_id is None:
        return None
    if key.initial_exchange_key is not None:
        sent_key_bytes = key.initial_exchange_key.public_bytes_raw()
        sent_key_id = _get_sent_key_id(session, sent_key_bytes)
    else:
        sent_key_id = None
    if not _is_valid_sent_key_id(session, sent_key_id):
        return None
    return _create_received_key_object(key, contact_id, sent_key_id)
    
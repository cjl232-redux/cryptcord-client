from base64 import urlsafe_b64encode

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from database.models import Contact, ReceivedExchangeKey, SentExchangeKey
from database.schemas.input import ReceivedExchangeKeyInputSchema
from server.schemas.responses import FetchedExchangeKey

def add_fetched_exchange_keys(
        engine: Engine,
        fetched_exchange_keys: list[FetchedExchangeKey],
    ):
    """Stores exchange keys retrieved from a server."""
    contact_cache: dict[bytes, int | None] = dict()
    with Session(engine) as session:
        for fetched_exchange_key in fetched_exchange_keys:
            exchange_key = _process_fetched_exchange_key(
                session,
                fetched_exchange_key,
                contact_cache,
            )
            if exchange_key is not None:
                session.add(exchange_key)
        session.commit()

def _create_exchange_key_object(
        key: FetchedExchangeKey,
        contact_id: int,
        sent_key_id: int | None,
    ) -> ReceivedExchangeKey | None:
    exchange_key_input = ReceivedExchangeKeyInputSchema.model_validate({
        'public_key': key.transmitted_exchange_key,
        'contact_id': contact_id,
        'timestamp': key.timestamp,
    })
    return ReceivedExchangeKey(**exchange_key_input.model_dump())

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
        select(SentExchangeKey.id)
        .where(SentExchangeKey.public_key == b64_key)
    )
    return session.scalar(id_query)

def _is_valid_sent_key_id(session: Session, id: int | None) -> bool:
    if id is None:
        return True
    query = (
        select(ReceivedExchangeKey)
        .where(ReceivedExchangeKey.sent_exchange_key_id == id)
    )
    return session.scalar(query) is not None

def _process_fetched_exchange_key(
        session: Session,
        key: FetchedExchangeKey,
        cache: dict[bytes, int | None],
    ) -> ReceivedExchangeKey | None:
    if not key.is_valid:
        return None
    sender_key_bytes = key.sender_public_key.public_bytes_raw()
    if sender_key_bytes not in cache:
        cache[sender_key_bytes] = _get_contact_id(session, sender_key_bytes)
    contact_id = cache[sender_key_bytes]
    if contact_id is None:
        return None
    exchange_key_bytes = key.transmitted_exchange_key.public_bytes_raw()
    sent_key_id = _get_sent_key_id(session, exchange_key_bytes)
    if not _is_valid_sent_key_id(session, sent_key_id):
        return None
    return _create_exchange_key_object(key, contact_id, sent_key_id)
    
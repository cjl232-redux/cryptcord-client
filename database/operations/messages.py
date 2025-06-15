from base64 import urlsafe_b64encode

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from database.models import Contact, FernetKey, Message, MessageType
from database.schemas.input import MessageInputSchema
from server.schemas.responses import FetchedMessage

def add_fetched_messages(
        engine: Engine,
        fetched_messages: list[FetchedMessage],
    ):
    """Decrypt and store encrypted messages retrieved from a server."""
    contact_cache: dict[bytes, tuple[int | None, list[Fernet]]] = dict()
    with Session(engine) as session:
        for fetched_message in fetched_messages:
            message = _process_fetched_message(
                session,
                fetched_message,
                contact_cache,
            )
            if message is not None:
                session.add(message)
        session.commit()

def _create_message_object(
        msg: FetchedMessage,
        contact_id: int,
        fernet_keys: list[Fernet],
    ) -> Message | None:
    for key in fernet_keys:
        try:
            plaintext = key.decrypt(msg.encrypted_text)
            message_input = MessageInputSchema.model_validate({
                'text': plaintext,
                'message_type': MessageType.RECEIVED,
                'contact_id': contact_id,
                'timestamp': msg.timestamp,
                'nonce': msg.nonce,
            })
            return Message(**message_input.model_dump())
        except InvalidToken:
            continue

def _get_contact_info(
        session: Session,
        key_bytes: bytes,
    ) -> tuple[int | None, list[Fernet]]:
    b64_key = urlsafe_b64encode(key_bytes).decode()
    id_query = (
        select(Contact.id)
        .where(Contact.public_key == b64_key)
    )
    contact_id = session.scalar(id_query)
    if contact_id is None:
        return None, []
    keys_query = (
        select(FernetKey.key)
        .where(FernetKey.contact != None)
        .join(Contact)
        .where(Contact.public_key == b64_key)
        .order_by(FernetKey.timestamp.desc())
    )
    print([x for x in session.scalars(keys_query)])
    return contact_id, [Fernet(x) for x in session.scalars(keys_query)]

def _is_valid_nonce(session: Session, nonce: str) -> bool:
    query = (
        select(Message)
        .where(Message.nonce == nonce)
    )
    return session.scalar(query) is None

def _process_fetched_message(
        session: Session,
        msg: FetchedMessage,
        cache: dict[bytes, tuple[int | None, list[Fernet]]],
    ) -> Message | None:
    print('debug1')
    print(f'Ciphertext: {msg.encrypted_text}')
    print(f'Signature: {msg.signature}')
    if not msg.is_valid or not _is_valid_nonce(session, hex(msg.nonce)):
        return None
    print('debug2')
    public_key_bytes = msg.sender_public_key.public_bytes_raw()
    if public_key_bytes not in cache:
        cache[public_key_bytes] = _get_contact_info(session, public_key_bytes)
    contact_id, fernet_keys = cache[public_key_bytes]
    if contact_id is None:
        return None
    return _create_message_object(msg, contact_id, fernet_keys)
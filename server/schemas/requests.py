import binascii

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime
from typing import Annotated

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
from pydantic import BaseModel, BeforeValidator

def _validate_public_key(
        value: str | Ed25519PublicKey | X25519PublicKey
    ) -> str:
    try:
        if isinstance(value, str):
            raw_bytes = urlsafe_b64decode(value)
        else:
            raw_bytes = value.public_bytes_raw()
    except binascii.Error:
        raise ValueError('Value is not valid Base64')
    if len(raw_bytes) != 32:
        raise ValueError('Value must have an unencoded length of 32 bytes')
    return urlsafe_b64encode(raw_bytes).decode()

def _validate_public_key_list(
    value: list[str | Ed25519PublicKey | X25519PublicKey],
) -> list[str]:
    return [_validate_public_key(x) for x in value]

def _validate_message(value: bytes) -> str:
    return value.decode()

def _validate_signature(value: bytes) -> str:
    if len(value) != 64:
        raise ValueError('Value must have an unencoded length of 64 bytes')
    return urlsafe_b64encode(value).decode()

type _PublicKey = Annotated[
    str,
    BeforeValidator(_validate_public_key),
]

type _PublicKeyList = Annotated[
    list[str],
    BeforeValidator(_validate_public_key_list),
]

type _Message = Annotated[
    str,
    BeforeValidator(_validate_message),
]

type _Signature = Annotated[
    str,
    BeforeValidator(_validate_signature),
]

class _BaseRequest(BaseModel):
    public_key: _PublicKey

class _BasePostRequest(_BaseRequest):
    recipient_public_key: _PublicKey
    signature: _Signature

    class Config:
        arbitary_types_allowed = True

class PostExchangeKeyRequest(_BasePostRequest):
    exchange_key: _PublicKey
    response_to: _PublicKey | None = None

class PostMessageRequest(_BasePostRequest):
    encrypted_text: _Message

class RetrieveDataRequest(_BaseRequest):
    sender_keys: _PublicKeyList | None = None
    min_datetime: datetime | None = None
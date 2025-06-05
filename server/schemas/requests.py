from base64 import urlsafe_b64encode
from typing import Annotated

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel, BeforeValidator

def _validate_public_key(value: Ed25519PublicKey) -> str:
    return urlsafe_b64encode(value.public_bytes_raw()).decode()

def _validate_message(value: bytes) -> str:
    return value.decode()

def _validate_signature(value: bytes) -> str:
    if len(value) != 64:
        raise ValueError('The signature must be 64 bytes in length')
    return urlsafe_b64encode(value).decode()

type _PublicKey = Annotated[
    str,
    BeforeValidator(_validate_public_key),
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

class PostMessageRequest(_BaseRequest):
    recipient_public_key: _PublicKey
    encrypted_text: _Message
    signature: _Signature




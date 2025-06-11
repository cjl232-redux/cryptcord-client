import binascii

from base64 import urlsafe_b64decode, urlsafe_b64encode
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


from typing import Any
import requests as pyrequests
from server.schemas.responses import PostDataResponse
from base64 import urlsafe_b64encode
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
if __name__ == '__main__':
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    recipient_public_key = Ed25519PrivateKey.generate().public_key()
    ephemeral_private_key = X25519PrivateKey.generate()
    ephemeral_public_key = ephemeral_private_key.public_key()
    received_key = X25519PrivateKey.generate().public_key()
    signature = private_key.sign(ephemeral_public_key.public_bytes_raw())

    data: dict[str, Any] = {
        'public_key': public_key,
        'recipient_public_key': recipient_public_key,
        'signature': signature,
        'exchange_key': ephemeral_public_key,
        'response_to': received_key,
    }
    #print(data)

    obj = PostExchangeKeyRequest.model_validate(data)

    response = PostDataResponse.model_validate(
        pyrequests.post('http://127.0.0.1:8000/exchange_keys/post', json=obj.model_dump()).json()
    )
    print(response.data)
    print(response.data.timestamp.tzinfo)



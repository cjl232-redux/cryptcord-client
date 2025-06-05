import binascii

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime
from typing import Annotated

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from pydantic import BaseModel, BeforeValidator, StringConstraints

from database.models import MessageType

type _BytesType = bytes | bytearray | memoryview

def _validate_elliptic_curve_key(
        value: _BytesType | str | Ed25519PublicKey | X25519PrivateKey,
    ) -> str:
    if isinstance(value, (bytes, bytearray, memoryview, str)):
        try:
            raw_bytes = urlsafe_b64decode(value)
            if len(raw_bytes) != 32:
                raise ValueError((
                    'Value must have an unencoded length of 32 bytes'
                ))
            return urlsafe_b64encode(raw_bytes).decode()
        except binascii.Error:
            raise ValueError('Value is not valid Base64')
    elif isinstance(value, Ed25519PublicKey):
        return urlsafe_b64encode(value.public_bytes_raw()).decode()
    else:
        return urlsafe_b64encode(value.private_bytes_raw()).decode()
    
def _validate_fernet_key(value: _BytesType | str):
    try:
        raw_bytes = urlsafe_b64decode(value)
        if len(raw_bytes) != 32:
            raise ValueError('Value must have an unencoded length of 32 bytes')
        return urlsafe_b64encode(raw_bytes)
    except binascii.Error:
        raise ValueError('Value is not valid Base64')
    
type _EllipticCurveKey = Annotated[
    str,
    BeforeValidator(_validate_elliptic_curve_key),
]

type _FernetKey = Annotated[
    str,
    BeforeValidator(_validate_fernet_key),
]

type _MessageNonce = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        max_length=32,
        min_length=32,
        to_lower=True,
        pattern='^[A-Fa-f0-9]*$',
    ),
]

class ContactInputSchema(BaseModel):
    model_config = {
        'arbitrary_types_allowed': True,
    }
    name: str
    public_key: _EllipticCurveKey
    private_ephemeral_key: _EllipticCurveKey | None = None
    fernet_key: _FernetKey | None = None

class MessageInputSchema(BaseModel):
    text: str
    timestamp: datetime
    message_type: MessageType
    contact_id: int
    nonce: _MessageNonce
import binascii

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime
from typing import Annotated

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from pydantic import BeforeValidator, BaseModel, ConfigDict

def validate_b64_verification_key(value: str) -> Ed25519PublicKey:
    try:
        raw_bytes = urlsafe_b64decode(value)
        return Ed25519PublicKey.from_public_bytes(raw_bytes)
    except binascii.Error:
        raise ValueError('Value is not valid Base64')
    except ValueError:
        raise ValueError('Value must have an unencoded length of 32 bytes')
    
def _validate_b64_ephemeral_key(value: str) -> X25519PrivateKey:
    try:
        raw_bytes = urlsafe_b64decode(value)
        return X25519PrivateKey.from_private_bytes(raw_bytes)
    except binascii.Error:
        raise ValueError('Value is not valid Base64')
    except ValueError:
        raise ValueError('Value must have an unencoded length of 32 bytes')
    
def _validate_b64_fernet_key(value: str) -> Fernet:
    try:
        return Fernet(urlsafe_b64encode(urlsafe_b64decode(value)))
    except binascii.Error:
        raise ValueError('Value is not valid Base64')
    except ValueError:
        raise ValueError('Value must have an unencoded length of 32 bytes')

type _PublicVerificationKey = Annotated[
    Ed25519PublicKey,
    BeforeValidator(validate_b64_verification_key),
]

type _PrivateEphemeralKey = Annotated[
    X25519PrivateKey,
    BeforeValidator(_validate_b64_ephemeral_key),
]

type _FernetKey = Annotated[
    Fernet,
    BeforeValidator(_validate_b64_fernet_key),
]

def _validate_nonce(value: str) -> int:
    return int(value, base=16)


type _MessageNonce = Annotated[
    int,
    BeforeValidator(_validate_nonce),
]

class ContactFernetOutputSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    fernet_key: _FernetKey | None = None

class ContactOutputSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        revalidate_instances='always',
        arbitrary_types_allowed=True,
    )
    id: int
    name: str
    public_verification_key: _PublicVerificationKey
    private_ephemeral_key: _PrivateEphemeralKey | None = None
    fernet_key: _FernetKey | None = None

class MessageOutputSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        revalidate_instances='always',
    )
    id: int
    text: str
    timestamp: datetime
    message_type: str
    nonce: _MessageNonce
    contact_id: int
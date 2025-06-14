import binascii

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)

type _PrivateKey = Ed25519PrivateKey | X25519PrivateKey
type _PublicKey = Ed25519PublicKey | X25519PublicKey
type _PrivateKeyType = type[Ed25519PrivateKey] | type[X25519PrivateKey]
type _PublicKeyType = type[Ed25519PublicKey] | type[X25519PublicKey]

def raw_to_base64(value: bytes, length: int | None = None) -> str:
    if length is not None and len(value) != length:
        raise ValueError(
            f'Value must have an unencoded length of {length} bytes',
        )
    return urlsafe_b64encode(value).decode()

def key_to_base64(key: _PrivateKey | _PublicKey) -> str:
    if isinstance(key, (Ed25519PrivateKey, X25519PrivateKey)):
        return urlsafe_b64encode(key.private_bytes_raw()).decode()
    else:
        return urlsafe_b64encode(key.public_bytes_raw()).decode()

def _base64_to_raw(value: str | bytes, length: int | None = None) -> bytes:
    try:
        raw_bytes = urlsafe_b64decode(value)
        if length is not None and len(raw_bytes) != length:
            raise ValueError(
                f'Value must have an unencoded length of {length} bytes',
            )
        return raw_bytes
    except binascii.Error:
        raise ValueError('Value is not valid Base64')
    
def base64_to_key(
        value: str,
        output_type: _PrivateKeyType | _PublicKeyType | type[Fernet],
    ):
    raw_bytes = _base64_to_raw(value, 32)
    if issubclass(output_type, (Ed25519PrivateKey, X25519PrivateKey)):
        return output_type.from_private_bytes(raw_bytes)
    elif issubclass(output_type, (Ed25519PublicKey, X25519PublicKey)):
        return output_type.from_public_bytes(raw_bytes)
    else:
        return output_type(value)
    
def datetime_to_utc(value: datetime):
    return value.astimezone(timezone.utc)

def datetime_to_str(value: datetime):
    return datetime_to_utc(value).isoformat()
    
def hex_to_int(value: str):
    return int(value, 16)
    
# import binascii

# from base64 import urlsafe_b64decode, urlsafe_b64encode
# from datetime import datetime, timezone
# from typing import Annotated

# from cryptography.hazmat.primitives.asymmetric.ed25519 import (
#     Ed25519PrivateKey,
#     Ed25519PublicKey,
# )
# from cryptography.hazmat.primitives.asymmetric.x25519 import (
#     X25519PrivateKey,
#     X25519PublicKey,
# )
# from pydantic import (
#     AfterValidator,
#     BaseModel,
#     BeforeValidator,
#     StringConstraints,
# )

# from database.models import MessageType

# type _BytesType = bytes | bytearray | memoryview
# type _PrivateKeyType = Ed25519PrivateKey | X25519PrivateKey
# type _PublicKeyType = Ed25519PublicKey | X25519PublicKey

# def _validate_key(
#         value: _BytesType | str | _PublicKeyType | _PrivateKeyType,
#     ) -> str:
#     if isinstance(value, (bytes, bytearray, memoryview, str)):
#         try:
#             raw_bytes = urlsafe_b64decode(value)
#             if len(raw_bytes) != 32:
#                 raise ValueError((
#                     'Value must have an unencoded length of 32 bytes'
#                 ))
#             return urlsafe_b64encode(raw_bytes).decode()
#         except binascii.Error:
#             raise ValueError('Value is not valid Base64')
#     elif isinstance(value, (Ed25519PublicKey, X25519PublicKey)):
#         return urlsafe_b64encode(value.public_bytes_raw()).decode()
#     else:
#         return urlsafe_b64encode(value.private_bytes_raw()).decode()

# def _validate_fernet_key(value: _BytesType | str):
#     try:
#         raw_bytes = urlsafe_b64decode(value)
#         if len(raw_bytes) != 32:
#             raise ValueError('Value must have an unencoded length of 32 bytes')
#         return urlsafe_b64encode(raw_bytes)
#     except binascii.Error:
#         raise ValueError('Value is not valid Base64')
    
# def _validate_timestamp(value: datetime) -> datetime:
#     return value.replace(tzinfo=timezone.utc)
    
# type _Key = Annotated[
#     str,
#     BeforeValidator(_validate_key),
# ]

# type _FernetKey = Annotated[
#     str,
#     BeforeValidator(_validate_fernet_key),
# ]

# type _MessageNonce = Annotated[
#     str,
#     StringConstraints(
#         strip_whitespace=True,
#         max_length=32,
#         min_length=32,
#         to_lower=True,
#         pattern='^[A-Fa-f0-9]*$',
#     ),
# ]

# class ContactInputSchema(BaseModel):
#     model_config = {
#         'arbitrary_types_allowed': True,
#     }
#     name: str
#     public_key: _Key

# class MessageInputSchema(BaseModel):
#     text: str
#     timestamp: datetime
#     message_type: MessageType
#     contact_id: int
#     nonce: _MessageNonce

# class ReceivedExchangeKeyInputSchema(BaseModel):
#     public_key: _Key
#     timestamp: Annotated[datetime, AfterValidator(_validate_timestamp)]
#     contact_id: int
#     sent_exchange_key_id: int | None = None

# class SentExchangeKeyInputSchema(BaseModel):
#     private_key: _Key
#     public_key: _Key
#     contact_id: int

# class FernetKeyInputSchema(BaseModel):
#     key: _Key
#     timestamp: Annotated[datetime, AfterValidator(_validate_timestamp)]
#     contact_id: int
from typing import Annotated

from pydantic import BaseModel, BeforeValidator

from database.models import MessageType
from schema_components.types.common import UTCTimestamp
from schema_components.types.input import HexNonce, Key
from schema_components.validators import raw_to_base64

class FernetKeyInputSchema(BaseModel):
    key: Annotated[
        str,
        BeforeValidator(lambda x: raw_to_base64(x, 32)),
    ]
    timestamp: UTCTimestamp
    contact_id: int

class MessageInputSchema(BaseModel):
    text: str
    timestamp: UTCTimestamp
    message_type: MessageType
    contact_id: int
    nonce: HexNonce

class SentExchangeKeyInputSchema(BaseModel):
    private_key: Key
    public_key: Key

class ReceivedExchangeKeyInputSchema(BaseModel):
    public_key: Key
    timestamp: UTCTimestamp
    contact_id: int
    sent_exchange_key_id: int | None = None
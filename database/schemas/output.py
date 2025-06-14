# import binascii

# from base64 import urlsafe_b64decode, urlsafe_b64encode
# from datetime import datetime, timezone
# from typing import Annotated

# from cryptography.fernet import Fernet
# from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
# from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
# from pydantic import AfterValidator, BeforeValidator, BaseModel, ConfigDict

# def _validate_b64(value: str) -> str:
#     try:
#         return urlsafe_b64encode(urlsafe_b64decode(value)).decode()
#     except binascii.Error:
#         raise ValueError('Value is not valid Base64')

# def _validate_b64_verification_key(value: str) -> Ed25519PublicKey:
#     try:
#         raw_bytes = urlsafe_b64decode(value)
#         return Ed25519PublicKey.from_public_bytes(raw_bytes)
#     except binascii.Error:
#         raise ValueError('Value is not valid Base64')
#     except ValueError:
#         raise ValueError('Value must have an unencoded length of 32 bytes')
    
# def _validate_b64_ephemeral_key(value: str) -> X25519PublicKey:
#     try:
#         raw_bytes = urlsafe_b64decode(value)
#         return X25519PublicKey.from_public_bytes(raw_bytes)
#     except binascii.Error:
#         raise ValueError('Value is not valid Base64')
#     except ValueError:
#         raise ValueError('Value must have an unencoded length of 32 bytes')
    
# def _validate_b64_fernet_key(value: str) -> Fernet:
#     try:
#         return Fernet(urlsafe_b64encode(urlsafe_b64decode(value)))
#     except binascii.Error:
#         raise ValueError('Value is not valid Base64')
#     except ValueError:
#         raise ValueError('Value must have an unencoded length of 32 bytes')

# type _Base64String = Annotated[
#     str,
#     BeforeValidator(_validate_b64),
# ]

# type _VerificationKey = Annotated[
#     Ed25519PublicKey,
#     BeforeValidator(_validate_b64_verification_key),
# ]

# type _EphemeralKey = Annotated[
#     X25519PublicKey,
#     BeforeValidator(_validate_b64_ephemeral_key),
# ]

# type _FernetKey = Annotated[
#     Fernet,
#     BeforeValidator(_validate_b64_fernet_key),
# ]

# def _validate_nonce(value: str) -> int:
#     return int(value, base=16)


# type _MessageNonce = Annotated[
#     int,
#     BeforeValidator(_validate_nonce),
# ]

# class ContactFernetOutputSchema(BaseModel):
#     model_config = ConfigDict(
#         from_attributes=True,
#         arbitrary_types_allowed=True,
#     )
#     fernet_key: _FernetKey | None = None

# class ContactOutputSchema(BaseModel):
#     model_config = ConfigDict(
#         from_attributes=True,
#         revalidate_instances='always',
#         arbitrary_types_allowed=True,
#     )
#     id: int
#     name: str
#     public_key: _VerificationKey

# class ContactSimplifiedOutputSchema(BaseModel):
#     """Retrieves the name and key of a contact in string form."""
#     model_config = ConfigDict(
#         from_attributes=True,
#         revalidate_instances='always',
#         arbitrary_types_allowed=True,
#     )
#     name: str
#     public_key: _Base64String

# class MessageOutputSchema(BaseModel):
#     model_config = ConfigDict(
#         from_attributes=True,
#         revalidate_instances='always',
#     )
#     id: int
#     text: str
#     timestamp: Annotated[
#         datetime,
#         AfterValidator(lambda x: x.replace(tzinfo=timezone.utc)),
#     ]
#     message_type: str
#     nonce: _MessageNonce
#     contact_id: int

# class ContactKeyOutputSchema(BaseModel):
#     public_key: _VerificationKey
#     class Config:
#         arbitrary_types_allowed = True
#         from_attributes = True
#         revalidate_instances = 'always'

# class PendingExchangeKeyOutputSchema(BaseModel):
#     public_key: _EphemeralKey
#     class Config:
#         arbitrary_types_allowed = True
#         from_attributes = True
#         revalidate_instances = 'always'


# class _ExchangeKeyAbstractSchema(BaseModel):


# class ReceivedExchangeKeyOutputSchema(BaseModel):

from pydantic import BaseModel

from schema_components.types import (
    Nonce,
    PrivateExchangeKey,
    PublicExchangeKey,
    PublicVerificationKey,
    UTCTimestamp,
)

class ContactOutputSchema(BaseModel):
    id: int
    name: str
    public_key: PublicVerificationKey
    class Config:
        arbitrary_types_allowed = True
        from_attributes = True

class MessageOutputSchema(BaseModel):
    id: int
    text: str
    timestamp: UTCTimestamp
    message_type: str
    nonce: Nonce
    contact: ContactOutputSchema
    class Config:
        from_attributes = True

class _ExchangeKeyOutputSchema(BaseModel):
    public_key: PublicExchangeKey
    class Config:
        arbitrary_types_allowed = True
        from_attributes = True

class SentExchangeKeyOutputSchema(_ExchangeKeyOutputSchema):
    private_key: PrivateExchangeKey

class ReceivedExchangeKeyOutputSchema(_ExchangeKeyOutputSchema):
    timestamp: UTCTimestamp
    contact_id: int
    sent_exchange_key: SentExchangeKeyOutputSchema | None
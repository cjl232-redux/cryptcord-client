import binascii

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime
from typing import Annotated

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
from pydantic import BaseModel, BeforeValidator, StringConstraints

def _validate_verification_key(value: str) -> Ed25519PublicKey:
    try:
        raw_bytes = urlsafe_b64decode(value)
        if len(raw_bytes) != 32:
            raise ValueError('Value must have an unencoded length of 32 bytes')
        return Ed25519PublicKey.from_public_bytes(raw_bytes)
    except binascii.Error:
        raise ValueError('Value is not valid Base64')

def _validate_signature(value: str) -> bytes:
    try:
        raw_bytes = urlsafe_b64decode(value)
        if len(raw_bytes) != 64:
            raise ValueError('Value must have an unencoded length of 64 bytes')
        return raw_bytes
    except binascii.Error:
        raise ValueError('Value is not valid Base64')

def _validate_message(value: str) -> bytes:
    try:
        return urlsafe_b64encode(urlsafe_b64decode(value))
    except binascii.Error:
        raise ValueError('Value is not valid Base64')

def _validate_exchange_key(value: str) -> X25519PublicKey:
    try:
        raw_bytes = urlsafe_b64decode(value)
        if len(raw_bytes) != 32:
            raise ValueError('Value must have an unencoded length of 32 bytes')
        return X25519PublicKey.from_public_bytes(raw_bytes)
    except binascii.Error:
        raise ValueError('Value is not valid Base64')


class BaseResponseModel(BaseModel):
    status: str
    message: str

class _PostMessageResponseData(BaseModel):
    timestamp: datetime
    nonce: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            max_length=32,
            min_length=32,
            to_lower=True,
            pattern='^[A-Fa-f0-9]*$',
        ),
    ]

class PostMessageResponseModel(BaseResponseModel):
    data: _PostMessageResponseData

class _PostDataResponseDataModel(BaseModel):
    timestamp: datetime
    nonce: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            max_length=32,
            min_length=32,
            to_lower=True,
            pattern='^[A-Fa-f0-9]*$',
        ),
    ]

class PostDataResponse(BaseResponseModel):
    data: _PostDataResponseDataModel

# class _RetrieveMessageResponseMessage(BaseModel):
#     sender_key: Annotated[
#         Ed25519PublicKey,
#         BeforeValidator(_validate_verification_key),
#     ]
#     encrypted_text: Annotated[
#         bytes,
#         BeforeValidator(_validate_message),
#     ]
#     signature: Annotated[
#         bytes,
#         BeforeValidator(_validate_signature),
#     ]
#     timestamp: datetime
#     nonce: str

# class _RetrieveMessagesResponseData(BaseModel):
#     messages: list[_RetrieveMessageResponseMessage]

# class RetrieveMessagesResponse(BaseResponseModel):
#     data: _RetrieveMessagesResponseData

#TODO very likely need to turn fernet keys into a separate table. Work out
# the EXACT procedure and order in which key exchange should work. Assume 
# some weirdo is re-exchanging every other message and design to handle it!



class _RetrieveExchangeKeysResponseElementModel(BaseModel):
    key: str
    signature: str
    sender_key: str
    timestamp: datetime
    nonce: str
    response_to: str | None

class _RetrieveExchangeKeysResponseDataModel(BaseModel):
    exchange_keys: list[_RetrieveExchangeKeysResponseElementModel]

class RetrieveExchangeKeysResponseModel(BaseResponseModel):
    data: _RetrieveExchangeKeysResponseDataModel
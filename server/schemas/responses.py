# import binascii

# from base64 import urlsafe_b64decode, urlsafe_b64encode
# from datetime import datetime, timezone
# from functools import cached_property
# from typing import Annotated

# from cryptography.exceptions import InvalidSignature
# from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
# from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
# from pydantic import (
#     AfterValidator,
#     AliasChoices,
#     BaseModel,
#     BeforeValidator,
#     Field,
#     StringConstraints,
# )

# type _KeyType = type[Ed25519PublicKey] | type[X25519PublicKey]
# type _UTCTimestamp = Annotated[
#     datetime,
#     AfterValidator(lambda x: x.replace(tzinfo=timezone.utc)),
# ]

# def _key_to_b64(key: Ed25519PublicKey | X25519PublicKey) -> str:
#     return urlsafe_b64encode(key.public_bytes_raw()).decode()

# def _validate_base64(value: str | bytes) -> bytes:
#     try:
#         return urlsafe_b64decode(value)
#     except binascii.Error:
#         raise ValueError('Value is not valid Base64')

# def _validate_bytes_length(value: str, n: int) -> bytes:
#     raw_bytes = _validate_base64(value)
#     if len(raw_bytes) != n:
#         raise ValueError(f'Value must have an unencoded length of {n} bytes')
#     return raw_bytes

# def _validate_key(value: str, output_type: _KeyType):
#     raw_bytes = _validate_bytes_length(value, 32)
#     return output_type.from_public_bytes(raw_bytes)

# class BaseResponseModel(BaseModel):
#     status: str
#     message: str

# class _PostMessageResponseData(BaseModel):
#     timestamp: _UTCTimestamp
#     nonce: Annotated[
#         str,
#         StringConstraints(
#             strip_whitespace=True,
#             max_length=32,
#             min_length=32,
#             to_lower=True,
#             pattern='^[A-Fa-f0-9]*$',
#         ),
#     ]

# class PostMessageResponseModel(BaseResponseModel):
#     data: _PostMessageResponseData

# class _PostDataResponseDataModel(BaseModel):
#     timestamp: _UTCTimestamp
#     nonce: Annotated[
#         str,
#         StringConstraints(
#             strip_whitespace=True,
#             max_length=32,
#             min_length=32,
#             to_lower=True,
#             pattern='^[A-Fa-f0-9]*$',
#         ),
#     ]

# class PostDataResponse(BaseResponseModel):
#     data: _PostDataResponseDataModel

# # class _RetrieveMessageResponseMessage(BaseModel):
# #     sender_key: Annotated[
# #         Ed25519PublicKey,
# #         BeforeValidator(_validate_verification_key),
# #     ]
# #     encrypted_text: Annotated[
# #         bytes,
# #         BeforeValidator(_validate_message),
# #     ]
# #     signature: Annotated[
# #         bytes,
# #         BeforeValidator(_validate_signature),
# #     ]
# #     timestamp: datetime
# #     nonce: str

# # class _RetrieveMessagesResponseData(BaseModel):
# #     messages: list[_RetrieveMessageResponseMessage]

# # class RetrieveMessagesResponse(BaseResponseModel):
# #     data: _RetrieveMessagesResponseData

# #TODO very likely need to turn fernet keys into a separate table. Work out
# # the EXACT procedure and order in which key exchange should work. Assume 
# # some weirdo is re-exchanging every other message and design to handle it!

# class _FetchAbstractDataResponseElement(BaseModel):
#     sender_public_key: Annotated[
#         Ed25519PublicKey,
#         BeforeValidator(lambda x: _validate_key(x, Ed25519PublicKey)),
#         Field(
#             validation_alias=AliasChoices(
#                 'sender_key',
#             )
#         ),
#     ]
#     signature: Annotated[
#         bytes,
#         BeforeValidator(lambda x: _validate_bytes_length(x, 64)),
#     ]
#     timestamp: _UTCTimestamp

#     @cached_property
#     def sender_public_key_b64(self) -> str:
#         return _key_to_b64(self.sender_public_key)
    
#     class Config:
#         arbitrary_types_allowed = True


# type _TransmittedExchangeKey = Annotated[
#     X25519PublicKey,
#     BeforeValidator(lambda x: _validate_key(x, X25519PublicKey)),
# ]

# type _InitialExchangeKey = Annotated[
#     X25519PublicKey,
#     BeforeValidator(lambda x: _validate_key(x, X25519PublicKey)),
# ]

# class _FetchExchangeKeysResponseElement(_FetchAbstractDataResponseElement):
#     transmitted_exchange_key: _TransmittedExchangeKey = Field(
#         validation_alias=AliasChoices(
#             'transmitted_exchange_key',
#             'key',
#             'exchange_key',
#             'transmitted_key',
#         ),
#     )
#     initial_exchange_key: _InitialExchangeKey | None = Field(
#         default=None,
#         validation_alias=AliasChoices(
#             'initial_exchange_key',
#             'response_to',
#         ),
#     )
#     @cached_property
#     def is_valid(self):
#         try:
#             self.sender_public_key.verify(
#                 signature=self.signature,
#                 data=self.transmitted_exchange_key.public_bytes_raw(),
#             )
#             return True
#         except InvalidSignature:
#             return False
#     @cached_property
#     def transmitted_exchange_key_b64(self) -> str:
#         return _key_to_b64(self.transmitted_exchange_key)
#     @cached_property
#     def initial_exchange_key_b64(self) -> str | None:
#         if self.initial_exchange_key is not None:
#             return _key_to_b64(self.initial_exchange_key)
#         return None


# class _FetchExchangeKeysResponseDataModel(BaseModel):
#     elements: list[_FetchExchangeKeysResponseElement] = Field(
#         validation_alias=AliasChoices(
#             'elements',
#             'exchange_keys',
#         )
#     )


# class FetchExchangeKeysResponseModel(BaseResponseModel):
#     data: _FetchExchangeKeysResponseDataModel

from functools import cached_property

from cryptography.exceptions import InvalidSignature
from pydantic import AliasChoices, BaseModel, Field

from schema_components.types.common import UTCTimestamp
from schema_components.types.output import (
    PublicExchangeKey,
    PublicVerificationKey,
    Signature,
)

class BaseResponseModel(BaseModel):
    status: str
    message: str

# Post requests:
class PostExchangeKeyResponseModel(BaseResponseModel):
    timestamp: UTCTimestamp

# Fetch requests:
class _FetchAbstractDataResponseElement(BaseModel):
    sender_public_key: PublicVerificationKey = Field(
        validation_alias=AliasChoices(
            'sender_public_key',
            'sender_key',
        )
    )
    signature: Signature
    timestamp: UTCTimestamp
    
    class Config:
        arbitrary_types_allowed = True


class _FetchExchangeKeysResponseElement(_FetchAbstractDataResponseElement):
    transmitted_exchange_key: PublicExchangeKey = Field(
        validation_alias=AliasChoices(
            'transmitted_exchange_key',
            'key',
            'exchange_key',
            'transmitted_key',
        ),
    )
    initial_exchange_key: PublicExchangeKey | None = Field(
        default=None,
        validation_alias=AliasChoices(
            'initial_exchange_key',
            'response_to',
        ),
    )
    @cached_property
    def is_valid(self):
        try:
            self.sender_public_key.verify(
                signature=self.signature,
                data=self.transmitted_exchange_key.public_bytes_raw(),
            )
            return True
        except InvalidSignature:
            return False


class _FetchExchangeKeysResponseDataModel(BaseModel):
    elements: list[_FetchExchangeKeysResponseElement] = Field(
        validation_alias=AliasChoices(
            'elements',
            'exchange_keys',
        )
    )


class FetchExchangeKeysResponseModel(BaseResponseModel):
    data: _FetchExchangeKeysResponseDataModel
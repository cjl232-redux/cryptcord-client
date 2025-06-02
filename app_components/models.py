"""
A collection of Pydantic models with custom types and validation.

This module defines models that can be used to validate user input (such
as from dialogs), as well as to store smaller data objects in memory to
avoid additional database lookups.

"""
import binascii

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator

def _validate_base64(value: bytes) -> bytes:
    """Confirm the value is valid Base64, then return a url-safe version."""
    try:
        return urlsafe_b64encode(urlsafe_b64decode(value))
    except binascii.Error:
        raise ValueError('Value must be valid Base64')
   
type _BytesFromBase64 = Annotated[bytes, BeforeValidator(_validate_base64)]

class ContactModel(BaseModel):
    id: int
    name: str
    public_key: _BytesFromBase64
    ephemeral_key: _BytesFromBase64 | None = None
    fernet_key: _BytesFromBase64 | None = None

class Message(BaseModel):
    sender_key: BytesFromBase64
    encrypted_text: BytesFromBase64
    signature: BytesFromBase64
    timestamp: datetime


class Model(BaseModel):
    x: BytesFromBase64


model = Model.model_validate({'x':'YWJjOi8_Jj0=', 'y': 1})
print(model.x)

import base64

data = b'This is a longer string with special characters: !@#$%^&*()+=/?><|\\[]{}~`'
encoded_unsafe = base64.b64encode(data).decode()
print(encoded_unsafe)

encoded_safe = base64.urlsafe_b64encode(data).decode()
print(encoded_safe)
import binascii

from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Annotated

from pydantic import BeforeValidator

def _validate_base64(value: bytes | str) -> str:
    """Confirm the value is valid Base64, then return a url-safe version."""
    if isinstance(value, (bytes, str)):
        try:
            return urlsafe_b64encode(urlsafe_b64decode(value)).decode()
        except binascii.Error:
            raise ValueError('Value must be valid Base64')
    else:
        raise TypeError('Type must be bytes or str')
   
type StrFromBase64 = Annotated[str, BeforeValidator(_validate_base64)]
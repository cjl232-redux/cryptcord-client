import binascii
from base64 import urlsafe_b64decode, urlsafe_b64encode

def validate_key(value: str) -> str:
    try:
        raw_bytes = urlsafe_b64decode(value)
        if len(raw_bytes) != 32:
            raise ValueError('Value must have an unencoded length of 32 bytes')
        return urlsafe_b64encode(raw_bytes).decode()
    except binascii.Error:
        raise ValueError('Value is not valid Base64')
from datetime import datetime
from typing import Annotated

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from pydantic import AfterValidator, BeforeValidator

from schema_components.validators import (
    base64_to_key,
    datetime_to_str,
    datetime_to_utc,
    hex_to_int,
    key_to_base64,
    raw_to_base64,
)

type Base64Key = Annotated[
    str,
    BeforeValidator(key_to_base64),
]
type Nonce = Annotated[
    int,
    BeforeValidator(hex_to_int),
]
type PublicVerificationKey = Annotated[
    Ed25519PublicKey,
    BeforeValidator(lambda x: base64_to_key(x, Ed25519PublicKey))
]
type PrivateExchangeKey = Annotated[
    X25519PrivateKey,
    BeforeValidator(lambda x: base64_to_key(x, X25519PrivateKey))
]
type PublicExchangeKey = Annotated[
    X25519PublicKey,
    BeforeValidator(lambda x: base64_to_key(x, X25519PublicKey))
]
type FernetKey = Annotated[
    Fernet,
    BeforeValidator(lambda x: base64_to_key(x, Fernet)),
]
type FernetKeyBytes = Annotated[
    str,
    AfterValidator(lambda x: raw_to_base64(x, 32)),
]
type UTCTimestamp = Annotated[
    datetime,
    AfterValidator(datetime_to_utc),
]
type StringTimestamp = Annotated[
    str,
    BeforeValidator(datetime_to_str),
]
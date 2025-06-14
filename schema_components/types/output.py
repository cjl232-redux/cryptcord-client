from typing import Annotated

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from pydantic import AfterValidator, BeforeValidator

from schema_components.validators import (
    base64_to_raw,
    base64_to_key,
    raw_to_base64,
    validate_int_nonce,
)

type RawBytes = Annotated[
    bytes,
    BeforeValidator(lambda x: base64_to_raw(x)),
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


type IntNonce = Annotated[
    int,
    BeforeValidator(validate_int_nonce),
]
type FernetKeyBytes = Annotated[
    str,
    AfterValidator(lambda x: raw_to_base64(x, 32)),
]
type Signature = Annotated[
    bytes,
    BeforeValidator(lambda x: base64_to_raw(x, 64)),
]
from typing import Annotated

from pydantic import BeforeValidator

from schema_components.validators import (
    key_to_base64,
    raw_to_base64,
    validate_hex_nonce,
)

type HexNonce = Annotated[
    int | str,
    BeforeValidator(validate_hex_nonce),
]

type Key = Annotated[
    str,
    BeforeValidator(key_to_base64),
]

type Signature = Annotated[
    str,
    BeforeValidator(lambda x: raw_to_base64(x, 64)),
]
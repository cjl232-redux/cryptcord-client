# Just put it all in models.py!!!!
# Ugh, I hate this. Going for a rush walk

import binascii

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator

from model_types import StrFromBase64

class ContactSchema(BaseModel):
    id: int
    name: str
    public_key: StrFromBase64
    ephemeral_key: StrFromBase64 | None = None
    fernet_key: StrFromBase64 | None = None
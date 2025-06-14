from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator

from schema_components.validators import datetime_to_utc

type UTCTimestamp = Annotated[
    datetime,
    AfterValidator(datetime_to_utc),
]
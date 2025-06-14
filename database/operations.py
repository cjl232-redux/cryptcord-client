from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from database.models import FernetKey, ReceivedExchangeKey
from database.schemas.input import FernetKeyInputSchema
from database.schemas.output import ReceivedExchangeKeyOutputSchema

def create_fernet_keys(engine: Engine):
    """Create symmetric keys from successful key exchanges."""
    statement = select(
        ReceivedExchangeKey,
    ).where(
        ReceivedExchangeKey.fernet_key_id == None,
    ).where(
        ReceivedExchangeKey.sent_exchange_key != None,
    )
    with Session(engine) as session:
        received_keys = (
            ReceivedExchangeKeyOutputSchema.model_validate(x)
            for x in session.scalars(statement).all()
        )
        for obj in received_keys:
            assert obj.sent_exchange_key is not None
            private_key = obj.sent_exchange_key.private_key
            input = FernetKeyInputSchema.model_validate({
                'key': private_key.exchange(obj.public_key),
                'timestamp': obj.timestamp,
                'contact_id': obj.contact_id,
            })
            session.add(FernetKey(**input.model_dump()))
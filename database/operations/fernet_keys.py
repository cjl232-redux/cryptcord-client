from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from database.models import FernetKey, ReceivedKey
from database.schemas.input import FernetKeyInputSchema
from database.schemas.output import ReceivedKeyOutputSchema

def create_fernet_keys(engine: Engine):
    """Create symmetric keys from successful key exchanges."""
    statement = (
        select(ReceivedKey)
        .where(ReceivedKey.sent_key != None)
        .where(ReceivedKey.fernet_key == None)
    )
    with Session(engine) as session:
        for obj in session.scalars(statement):
            received_key = ReceivedKeyOutputSchema.model_validate(obj)
            assert received_key.sent_key is not None
            private_key = received_key.sent_key.private_key
            input = FernetKeyInputSchema.model_validate({
                'key': private_key.exchange(received_key.public_key),
                'timestamp': received_key.timestamp,
                'contact_id': received_key.contact.id,
            })
            obj.fernet_key = FernetKey(**input.model_dump())
        session.commit()
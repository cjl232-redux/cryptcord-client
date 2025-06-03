from dataclasses import dataclass

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from database.models import Contact, Message
from database.schemas.outputs import ContactSchema

@dataclass
class ContactData:
    id: int


def get_contacts(engine: Engine) -> list[Contact]:
    with Session(engine) as session:
        return list(session.scalars(select(Contact)))

def get_message_nonces(engine: Engine) -> set[int]:
    with Session(engine) as session:
        return set(session.scalars(select(Message.nonce)))
    
def store_messages(engine: Engine, messages: list[Message]):
    with Session(engine) as session:
        session.add_all(messages)
        session.commit()
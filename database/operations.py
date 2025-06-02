from dataclasses import dataclass

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from database.models import Contact

@dataclass
class ContactInfo:
    id: int
    fernet_key: str | None

type ContactDict = dict[str, ContactInfo]

def get_contact_dict(engine: Engine) -> ContactDict:
    result: ContactDict = {}
    with Session(engine) as session:
        for contact in session.scalars(select(Contact)):
            result[contact.public_key] = ContactInfo(
                contact.id,
                contact.fernet_key,
            )
        return result
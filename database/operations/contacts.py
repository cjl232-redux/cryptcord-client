from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from database.models import Contact
from database.schemas.output import ContactOutputSchema

def get_contacts(engine: Engine) -> list[ContactOutputSchema]:
    with Session(engine) as session:
        result = [
            ContactOutputSchema.model_validate(contact)
            for contact in session.scalars(select(Contact))
        ]
        return result



def remove_contact(engine: Engine, id: int):
    with Session(engine) as session:
        session.delete(session.get_one(Contact, id))
        session.commit()
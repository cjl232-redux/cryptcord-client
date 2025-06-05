from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime, String, Text

class Base(DeclarativeBase):
    pass

class Contact(Base):
    __tablename__ = 'contacts'

    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    public_key: Mapped[str] = mapped_column(
        String(44),
        unique=True,
        nullable=False,
    )
    ephemeral_key: Mapped[str] = mapped_column(
        String(44),
        nullable=True,
    )
    fernet_key: Mapped[str] = mapped_column(
        String(44),
        nullable=True,
    )
    messages: Mapped[list['Message']] = relationship(
        back_populates='contact',
        cascade='all, delete-orphan',
    )

class MessageType(Enum):
    SENT = 'S'
    RECEIVED = 'R'

def _values_callable(x: type[Enum]):
    return [i.value for i in x]

class Message(Base):
    __tablename__ = 'messages'
    __table_args__ = (
        # Index this once I decide on the precise operations
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    text: Mapped[str] = mapped_column(
        Text(),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    message_type: Mapped[MessageType] = mapped_column(
        SQLEnum(MessageType, values_callable=_values_callable),
    )
    nonce: Mapped[str] = mapped_column(
        String(32),
        unique=True,
    )
    contact_id: Mapped[int] = mapped_column(
        ForeignKey(
            column=Contact.id,
        ),
    )
    contact: Mapped[Contact] = relationship(
        back_populates='messages',
    )
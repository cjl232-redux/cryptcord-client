from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime, String, Text

def _values_callable(x: type[Enum]):
    return [i.value for i in x]

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
    messages: Mapped[list['Message']] = relationship(
        back_populates='contact',
        cascade='all, delete-orphan',
    )
    received_exchange_keys: Mapped[list['ReceivedExchangeKey']] = relationship(
        back_populates='contact',
        cascade='all, delete-orphan',
    )
    sent_exchange_keys: Mapped[list['SentExchangeKey']] = relationship(
        back_populates='contact',
        cascade='all, delete-orphan',
    )
    fernet_keys: Mapped[list['FernetKey']] = relationship(
        back_populates='contact',
        cascade='all, delete-orphan',
    )

class MessageType(Enum):
    SENT = 'S'
    RECEIVED = 'R'

class Message(Base):
    __tablename__ = 'messages'
    __table_args__ = (
        Index('messages_contact_timestamp_index', 'contact_id', 'timestamp'),
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

class KeyType(Enum):
    EPHEMERAL = 'E'
    COMPLETE = 'C'

class FernetKey(Base):
    __tablename__ = 'fernet_keys'
    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    key: Mapped[str] = mapped_column(
        String(44),
        nullable=False,
        unique=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    contact_id: Mapped[int] = mapped_column(
        ForeignKey(
            column=Contact.id,
        ),
    )
    contact: Mapped[Contact] = relationship(
        back_populates='fernet_keys',
    )

class ReceivedExchangeKey(Base):
    __tablename__ = 'received_exchange_keys'
    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    public_key: Mapped[str] = mapped_column(
        String(44),
        nullable=False,
        unique=True,
    )
    contact_id: Mapped[int] = mapped_column(
        ForeignKey(
            column=Contact.id,
        ),
    )
    contact: Mapped[Contact] = relationship(
        back_populates='received_exchange_keys',
    )

class SentExchangeKey(Base):
    __tablename__ = 'sent_exchange_keys'
    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    private_key: Mapped[str] = mapped_column(
        String(44),
        nullable=False,
        unique=True,
    )
    public_key: Mapped[str] = mapped_column(
        String(44),
        nullable=False,
        unique=True,
    )
    contact_id: Mapped[int] = mapped_column(
        ForeignKey(
            column=Contact.id,
        ),
    )
    contact: Mapped[Contact] = relationship(
        back_populates='sent_exchange_keys',
    )
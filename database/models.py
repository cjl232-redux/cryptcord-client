import enum

from datetime import datetime

import sqlalchemy

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime, String, Text

class MessageType(enum.Enum):
    SENT = 'S'
    RECIEVED = 'R'

def values_callable(x: type[enum.Enum]):
    return [i.value for i in x]

class Base(DeclarativeBase):
    pass

class Contact(Base):
    __tablename__ = 'contacts'

    id: Mapped[int] = mapped_column(
        primary_key=True,
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
    pending_exchange_key: Mapped[str] = mapped_column(
        String(44),
        nullable=True,
    )
    encryption_key: Mapped[str] = mapped_column(
        String(44),
        nullable=True,
    )
    messages: Mapped[list['Message']] = relationship(
        back_populates='contact',
        cascade='all, delete-orphan',
    )

class Message(Base):
    __tablename__ = 'messages'
    __table_args__ = (
        Index('message_retrieval_index', 'contact_id', 'timestamp'),
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
    contact_id: Mapped[int] = mapped_column(
        ForeignKey(
            column='contacts.id',
            ondelete='CASCADE',
            onupdate='CASCADE',
        )
    )
    contact: Mapped[Contact] = relationship(back_populates='messages')
    message_type: Mapped[MessageType] = mapped_column(
        sqlalchemy.Enum(MessageType, values_callable=values_callable),
    )
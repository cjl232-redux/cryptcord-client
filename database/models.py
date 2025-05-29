from datetime import datetime

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DateTime, String, Text

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

class Message(Base):
    __tablename__ = 'messages'
    __table_args__ = (
        Index('message_retrieval_index', 'sender_id', 'timestamp'),
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
    sender_id: Mapped[int] = mapped_column(
        ForeignKey(
            column='contacts.id',
            ondelete='CASCADE',
            onupdate='CASCADE',
        )
    )
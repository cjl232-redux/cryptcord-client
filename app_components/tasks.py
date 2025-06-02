import tkinter as tk

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime

import requests

from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import ed25519
from pydantic import BaseModel
from sqlalchemy import Engine

from database import operations
from database.models import Message, MessageType
from model_types import StrFromBase64

# Remember to integrate unique 16-byte nums, but only using 'unique on 
# conflict ignore... or maybe it'd be faster to get the set? No, surely not 
# with unique indexing. Not available in ORM.... ugh

class _ContactInfo(BaseModel):
    id: int
    fernet_key: str | None = None

class _RetrievedMessage(BaseModel):
    encrypted_text: StrFromBase64
    sender_key: StrFromBase64
    signature: StrFromBase64
    timestamp: datetime
    nonce: int

class _MessageRetrievalResponseData(BaseModel):
    messages: list[_RetrievedMessage]

class _MessageRetrievalResponseBody(BaseModel):
    data: _MessageRetrievalResponseData


class TaskManager(tk.Frame):
    """A special widget that exists only to fetch data from the server."""
    def __init__(
            self,
            master: tk.Toplevel,
            engine: Engine,
            signature_key: ed25519.Ed25519PrivateKey,
            frequency_ms: int,
        ):
        super().__init__(master)
        self.engine = engine
        public_bytes = signature_key.public_key().public_bytes_raw()
        self.b64_public_key = urlsafe_b64encode(public_bytes).decode()
        self.frequency_ms = frequency_ms
        self.after(self.frequency_ms, self._tasks)

    def _retrieve_messages(self, contacts: dict[str, _ContactInfo]):
        # Send a message retrieval request.
        response = requests.post(
            url='http://127.0.0.1:8000/messages/retrieve',
            json={
                'public_key': self.b64_public_key,
                'sender_keys': list(contacts.keys()),
            },
        )
        if response.status_code == 200:
            body = _MessageRetrievalResponseBody.model_validate(
                response.json(),
            )
            i = 0
            decrypted_messages: list[Message] = []
            message_nonces = operations.get_message_nonces(self.engine)
            for message in body.data.messages:
                print(i)
                i += 1
                # Check that the message has not already been retrieved.
                if message.nonce in message_nonces:
                    continue
                print(i)
                i += 1
                print(contacts)

                # Confirm that the sender is a contact.
                if message.sender_key not in contacts:
                    continue
                contact = contacts[message.sender_key]
                print(i)
                i += 1

                # Check that a shared secret key is available.
                if not contact.fernet_key:
                    continue
                print(i)
                i += 1

                # Decrypt the message.
                fernet_key = Fernet(contact.fernet_key)
                text = fernet_key.decrypt(message.encrypted_text).decode()
                print(i)
                i += 1

                # Create the decrypted message object.
                decrypted_message = Message(
                    text=text,
                    timestamp=message.timestamp,
                    contact_id=contact.id,
                    message_type=MessageType.RECIEVED,
                    nonce=message.nonce,
                )
                decrypted_messages.append(decrypted_message)

            # Store the valid messages.
            operations.store_messages(self.engine, decrypted_messages)

    def _tasks(self):
        contacts = {
            x.public_key: _ContactInfo(id=x.id, fernet_key=x.fernet_key)
            for x in operations.get_contacts(self.engine)
        }
        self._retrieve_messages(contacts)
        self.after(self.frequency_ms, self._tasks)

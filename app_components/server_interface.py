import asyncio
import json

from base64 import b64encode, urlsafe_b64decode
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests

from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey, Ed25519PrivateKey
from pydantic import BaseModel
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from database.models import Message, MessageType
from database.operations import ContactDict
from json_types import JSONDict

class MessageResponse(BaseModel):
    encrypted_text: str
    sender_key: str
    signature: str
    timestamp: datetime

def retrieve_messages(
        url: str,
        engine: Engine,
        public_key: str,
        contact_dict: ContactDict, # better than endless endless queries
        min_datetime: datetime | None = None, # See above
    ):
    data: dict[str, Any] = {
        'public_key': public_key,
        'min_datetime': min_datetime,
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        messages: list[MessageResponse] = [
            MessageResponse(**message_data)
            for message_data in response.json()['data']['messages']
        ]
        valid_messages: list[Message] = []
        for message in messages:
            print(contact_dict)
            print(message.sender_key not in contact_dict)
            # Verify the sender is a registered contact.
            if message.sender_key not in contact_dict:
                continue
            contact_info = contact_dict[message.sender_key]
            # Ensure a fernet key is available.
            if contact_info.fernet_key is None:
                continue
            # Retrieve the sent values.
            text_bytes = message.encrypted_text.encode()
            sender_key_bytes = urlsafe_b64decode(message.sender_key)
            signature_bytes = urlsafe_b64decode(message.signature)
            # Verify the message source.
            sender_key = Ed25519PublicKey.from_public_bytes(sender_key_bytes)
            print('verifying')
            try:
                sender_key.verify(signature_bytes, text_bytes)
            except InvalidSignature:
                continue
            # Decipher the message.
            print('verified')
            key = Fernet(contact_info.fernet_key)
            try:
                decrypted_message = key.decrypt(text_bytes).decode()
            except InvalidToken:
                continue
            # Create and append a new message.
            valid_messages.append(
                Message(
                    text=decrypted_message,
                    contact_id=contact_dict[message.sender_key].id,
                    timestamp=message.timestamp,
                    message_type=MessageType.RECIEVED,
                )
            )
        with Session(engine) as session:
            session.add_all(valid_messages)
            session.commit()


@dataclass
class ServerInterface:
    host: str
    port: int
    signature_key: Ed25519PrivateKey

    async def _async_send_request(self, data: JSONDict) -> JSONDict:
        # Sign the data and prepare the request bytes.
        data_bytes = json.dumps(data).encode()
        signature_bytes = self.signature_key.sign(data_bytes)
        public_key_bytes = self.signature_key.public_key().public_bytes_raw()
        request: JSONDict = {
            'data': data,
            'signature': b64encode(signature_bytes).decode(),
            'public_key': b64encode(public_key_bytes).decode(),
        }
        request_bytes = json.dumps(request).encode()

        # Connect to the server and then send the request.
        reader, writer = await asyncio.open_connection(self.host, self.port)
        writer.write(request_bytes)
        await writer.drain()

        # Receive the response and then close the connection.
        response = await reader.read()
        writer.close()
        await writer.wait_closed()

        # Load and return the response.
        return json.loads(response.decode())
    
    def send_request(self, data: JSONDict) -> JSONDict:
        try:
            return asyncio.run(self._async_send_request(data))
        except:
            return {'status': 500, 'message': 'Unknown error.'}
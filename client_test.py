import asyncio
import json

from base64 import b64encode
from dataclasses import dataclass
from secrets import token_bytes

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

HOST = '127.0.0.1'
PORT = 8888
NUM_CONNECTIONS = 10

@dataclass
class User:
    name: str
    private_key: Ed25519PrivateKey
    connection_time: float
    message: str | None = None
    recipient_public_key: Ed25519PublicKey | None = None

keys = [Ed25519PrivateKey.from_private_bytes(x * 32) for x in [b'a', b'b', b'c']]

kirby = User('Kirby', keys[0], 0.0, message="Hai!", recipient_public_key=keys[2].public_key())
waddle_dee = User('Waddle Dee', keys[1], 1.5, message="Wanya!", recipient_public_key=keys[2].public_key())
king_dedede = User('King Dedede', keys[2], 0.5, message='Rup.', recipient_public_key=keys[1].public_key())

async def simulate_connection(user: User):
    # If a message exists, send it.

    await asyncio.sleep(user.connection_time)
    if user.message:
        data = {
            'command': 'POST_MESSAGE',
            'recipient_public_key': b64encode(user.recipient_public_key.public_bytes_raw()).decode(),
            'ciphertext': user.message,
            'signature': b64encode(user.private_key.sign(user.message.encode())).decode(),
        }
        signature = b64encode(user.private_key.sign(json.dumps(data).encode()))
        public_key = b64encode(user.private_key.public_key().public_bytes_raw())
        request = {
            'data': data,
            'signature': signature.decode(),
            'public_key': public_key.decode(),
        }
        try:
            reader, writer = await asyncio.open_connection(HOST, PORT)
            writer.write(json.dumps(request).encode())
            await writer.drain()
            # Optional: receive response
            response = await reader.readline()
            print(json.loads(response))
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"Send request by {user.name} failed: {e}")

    # Retrieve messages.
    data = {
        'command': 'RETRIEVE_MESSAGES',
    }
    signature = b64encode(user.private_key.sign(json.dumps(data).encode()))
    public_key = b64encode(user.private_key.public_key().public_bytes_raw())
    request = {
        'data': data,
        'signature': signature.decode(),
        'public_key': public_key.decode(),
    }
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
        writer.write(json.dumps(request).encode())
        await writer.drain()
        # Optional: receive response
        response = await reader.readline()
        print(json.loads(response))
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"Retrieve request by {user.name} failed: {e}")


# async def simulate_connection(i):
#     private_key = Ed25519PrivateKey.generate()
#     data = {}
#     from random import random
#     for i in range(int(random() * 1000)):
#         data[str(i)] = 30
#     signature = b64encode(private_key.sign(json.dumps(data).encode()))
#     public_key = b64encode(private_key.public_key().public_bytes_raw())
#     request = {
#         'data': data,
#         'signature': signature.decode(),
#         'public_key': public_key.decode(),
#     }

#     try:
#         reader, writer = await asyncio.open_connection(HOST, PORT)
#         writer.write(json.dumps(request).encode())
#         await writer.drain()
#         # Optional: receive response
#         response = await reader.readline()
#         print(json.loads(response))
#         writer.close()
#         await writer.wait_closed()
#     except Exception as e:
#         print(f"Connection {i} failed: {e}")

async def main():
    tasks = [simulate_connection(user) for user in [kirby, waddle_dee, king_dedede]]
    await asyncio.gather(*tasks)

asyncio.run(main())

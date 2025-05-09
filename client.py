import asyncio
import base64
import json
from socket import socket
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, types
from cryptography.hazmat.primitives.asymmetric.dsa import DSAPrivateKey
from cryptography.hazmat.primitives.asymmetric.ed448 import Ed448PrivateKey
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key

_HOST = '127.0.0.1'
_PORT = 8888
_DB_NAME = 'test_database.db'
_MAX_REQUEST_BYTES = 4096
# Debug keys
kirby_key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex('00' * 32))
dedede_key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex('ff' * 32))

async def send_exchange_key(
        host: str,
        port: int,
        recipient_key: ed25519.Ed25519PublicKey,
        signature_key: ed25519.Ed25519PrivateKey,
) -> None:
    private_exchange_key = X25519PrivateKey.generate()
    public_exchange_key = private_exchange_key.public_key()
    exchange_key_bytes = public_exchange_key.public_bytes_raw()
    print(base64.b64encode(private_exchange_key.private_bytes_raw()).decode())
    
    # Construct and send the request:
    data = {
        'command': 'SEND_EXCHANGE_KEY',
        'recipient_verification_key': base64.b64encode(recipient_key.public_bytes_raw()).decode(),
        'exchange_key': base64.b64encode(exchange_key_bytes).decode(),
        'exchange_key_signature': base64.b64encode(signature_key.sign(exchange_key_bytes)).decode(),
    }
    request = {
        'data': json.dumps(data),
        'verification_key': base64.b64encode(signature_key.public_key().public_bytes_raw()).decode(),
        'signature': base64.b64encode(signature_key.sign(json.dumps(data).encode())).decode(),
    }
    # Open the connection:
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(json.dumps(request).encode())
    await writer.drain()

    response = await reader.read()
    print('Received from server:', response.decode())

    writer.close()
    await writer.wait_closed()



# Shift this to JSON
# Consider a password system with local hashing? Not a bad idea...
# No, I don't think so. Just require all requests to have a signed component.

async def sign_data(key: types.PrivateKeyTypes, data: bytes) -> bytes:
    if isinstance(key, Ed25519PrivateKey) or isinstance(key, Ed448PrivateKey):
        return key.sign(data)
    elif isinstance(key, RSAPrivateKey):
        return key.sign(
            data=data,
            padding=padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            algorithm=hashes.SHA256(),
        )
    elif isinstance(key, DSAPrivateKey):
        return key.sign(data, hashes.SHA256())
    # And others. For the time being, drop this. Enforce Ed25516 for speed.

async def send_dm_request(
        host: str,
        port: int,
        recipient_key: ed25519.Ed25519PublicKey,
        signature_key: ed25519.Ed25519PrivateKey,
) -> None:
    private_exchange_key = X25519PrivateKey.generate()
    print(private_exchange_key.private_bytes_raw())
    public_exchange_key = private_exchange_key.public_key()
    key_bytes = public_exchange_key.public_bytes_raw()
    
    # Construct and send the request:
    data = {
        'command': 'MESSAGE_REQUEST',
        'public_exchange_key': key_bytes.hex(),
        'recipient_key': recipient_key.public_bytes_raw().hex(),
    }
    request = {
        'data': data,
        'verification_key': signature_key.public_key().public_bytes_raw().hex(),
        'signature': signature_key.sign(json.dumps(data).encode()).hex(),
    }
    # Open the connection:
    reader, writer = await asyncio.open_connection(host, port)
    print(len(json.dumps(request)))
    writer.write(json.dumps(request).encode())
    await writer.drain()

    response = await reader.read()
    print('Received from server:', response.decode())

    writer.close()
    await writer.wait_closed()

    

asyncio.run(send_exchange_key('127.0.0.1', 8888, dedede_key.public_key(), kirby_key))
asyncio.run(send_exchange_key('127.0.0.1', 8888, kirby_key.public_key(), dedede_key))
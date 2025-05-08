import asyncio
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
    public_exchange_key = private_exchange_key.public_key()
    key_bytes = public_exchange_key.public_bytes_raw()
    signature_bytes = signature_key.sign(key_bytes)
    
    # Construct and send the request:
    data = {
        'command': 'MESSAGE_REQUEST',
        'public_exchange_key': key_bytes.hex(),
        'recipient_key': signature_key.public_key().public_bytes_raw().hex(),
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

    

with open('verification_keys/dedede.pem', 'rb') as file:
    data = file.read()
ver_key = load_pem_public_key(data)
with open('unencrypted_private_key.pem', 'rb') as file:
    data = file.read()
sig_key = load_pem_private_key(data, None)
asyncio.run(send_dm_request('127.0.0.1', 8888, ver_key, sig_key))
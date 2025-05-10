import asyncio
import json
import sqlite3
from base64 import urlsafe_b64decode, urlsafe_b64encode
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.exceptions import InvalidSignature

# From rubber duck session:
# Timestamp key exchange to allow them to be ordered by most recent to least recent
# Move ALL signature verification to the client side
# Set up auto-deletion parameters (eg. messages not delivered...)
# CONSIDER having server-side verification specifically for message and key retrieval, allowing speedier deletion.

_HOST = '127.0.0.1'
_PORT = 8888
_DB_NAME = 'client_database.db'
_PRIVATE_KEY = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex('00' * 32))

def setup():
    with sqlite3.connect(_DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute((
            'CREATE TABLE IF NOT EXISTS contacts( '
            '   id INTEGER PRIMARY KEY, '
            '   nickname VARCHAR(255) UNIQUE NOT NULL, '
            '   ed25519_public_key CHAR(44) UNIQUE NOT NULL '
            ')'
        ))
        cursor.execute((
            'CREATE TABLE IF NOT EXISTS encryption_keys( '
            '   id INTEGER PRIMARY KEY, '
            '   contact_id INTEGER NOT NULL, '
            '   shared_secret_key CHAR(44) NOT NULL, '
            '   FOREIGN KEY(contact_id) REFERENCES contacts(id), '
            '   UNIQUE(contact_id) ON CONFLICT REPLACE '
            ')'
        ))
        cursor.execute((
            'CREATE TABLE IF NOT EXISTS pending_exchanges( '
            '   id INTEGER PRIMARY KEY, '
            '   contact_id INTEGER NOT NULL, '
            '   private_key CHAR(44) NOT NULL, '
            '   FOREIGN KEY(contact_id) REFERENCES contacts(id), '
            '   UNIQUE(contact_id) ON CONFLICT REPLACE '
            ')'
        ))
        cursor.execute((
            'CREATE TABLE IF NOT EXISTS messages( '
            '   id INTEGER PRIMARY KEY, '
            '   contact_id INTEGER NOT NULL, '
            '   decrypted_message TEXT NOT NULL, '
            '   FOREIGN KEY(contact_id) REFERENCES contacts(id) '
            ')'
        ))

def register_contact(nickname: str, public_key: ed25519.Ed25519PublicKey):
    public_key = urlsafe_b64encode(public_key.public_bytes_raw()).decode()
    with sqlite3.connect(_DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute(
            'INSERT INTO contacts(nickname, ed25519_public_key) VALUES (?, ?)',
            (nickname, public_key,),
        )

def get_contact_id(contact_key: str):
    with sqlite3.connect(_DB_NAME, autocommit=False) as connection:
        cursor = connection.cursor()
        cursor.execute(
            'SELECT id FROM contacts WHERE ed25519_public_key = ?',
            (contact_key,),
        )
        result = cursor.fetchone()
        return result[0] if result is not None else None

def get_contact_key(contact_id: int):
    with sqlite3.connect(_DB_NAME, autocommit=False) as connection:
        cursor = connection.cursor()
        cursor.execute(
            'SELECT ed25519_public_key FROM contacts WHERE id = ?',
            (contact_id,),
        )
        result = cursor.fetchone()
        if result is None:
            raise ValueError('Invalid contact id.')
        return result[0]
    

async def send_exchange_key(host, port, contact_id: int):

    # Retrieve the contact key:
    contact_key = get_contact_key(contact_id)    

    # Generate an exchange key pair and sign the public component:
    x25519_private_key = x25519.X25519PrivateKey.generate()
    x25519_public_key = x25519_private_key.public_key()
    key_signature = _PRIVATE_KEY.sign(x25519_public_key.public_bytes_raw())

    # Convert the public key and signature to base64 representations:
    x25519_public_key = urlsafe_b64encode(x25519_public_key.public_bytes_raw())
    key_signature = urlsafe_b64encode(key_signature)

    # Construct the request data and sign it:
    data = {
        'command': 'SEND_EXCHANGE_KEY',
        'recipient_ed25519_public_key': contact_key,
        'x25519_public_key': x25519_public_key.decode(),
        'x25519_public_key_signature': key_signature.decode(),
    }
    data_signature = _PRIVATE_KEY.sign(json.dumps(data).encode())

    # Construct the full request:
    request = {
        'data': data,
        'public_key': urlsafe_b64encode(_PRIVATE_KEY.public_key().public_bytes_raw()).decode(),
        'signature': urlsafe_b64encode(data_signature).decode(),
    }

    # Open the connection and send the request:
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(json.dumps(request).encode())
    await writer.drain()

    # Retrieve the server's response:
    response = await reader.read()
    processed_response = json.loads(response.decode())
    print(processed_response)

    # Close the connection:
    writer.close()
    await writer.wait_closed()

    # If successful, store the private key and wipe any existing shared key:
    if processed_response.get('status') == 'ok':
        insertion_query = (
            'INSERT INTO pending_exchanges(contact_id, private_key) '
            'VALUES(?, ?) '
        )
        insertion_parameters = (
            contact_id,
            urlsafe_b64encode(x25519_private_key.private_bytes_raw()).decode(),
        )
        removal_query = (
            'DELETE FROM encryption_keys '
            'WHERE contact_id = ? '
        )
        with sqlite3.connect(_DB_NAME, autocommit=True) as connection:
            cursor = connection.cursor()
            cursor.execute(insertion_query, insertion_parameters)
            cursor.execute(removal_query, (contact_id,))

    # POSSIBLY RETRIEVE LAST MESSAGES

async def retrieve_exchange_keys(host, port) -> list[dict]:
       # Construct the request data and sign it:
    data = {
        'command': 'RETRIEVE_EXCHANGE_KEYS',
    }
    data_signature = _PRIVATE_KEY.sign(json.dumps(data).encode())

    # Construct the full request:
    request = {
        'data': data,
        'public_key': urlsafe_b64encode(_PRIVATE_KEY.public_key().public_bytes_raw()).decode(),
        'signature': urlsafe_b64encode(data_signature).decode(),
    }

    # Open the connection and send the request:
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(json.dumps(request).encode())
    await writer.drain()

    # Retrieve the server's response:
    response = await reader.read()
    processed_response = json.loads(response.decode())

    # Close the connection:
    writer.close()
    await writer.wait_closed()

    # Print the result if a failure occurs:
    if processed_response.get('status') != 'ok':
        raise Exception(processed_response)
    
    valid_results = []
    request_results = processed_response.get('exchange_keys')
    for sender_key_str, exchange_key_str, signature_str in request_results:
        try:
            sender_key = ed25519.Ed25519PublicKey.from_public_bytes(
                urlsafe_b64decode(sender_key_str.encode()),
            )
            exchange_key = x25519.X25519PublicKey.from_public_bytes(
                urlsafe_b64decode(exchange_key_str.encode()),
            )
            signature = urlsafe_b64decode(signature_str.encode())
            sender_key.verify(signature, exchange_key.public_bytes_raw())
            valid_results.append({
                'contact_id': get_contact_id(sender_key_str),
                'exchange_key': exchange_key_str,
            })
        except InvalidSignature:
            print('INVALID SIGNATURE')

    print(valid_results)
    return valid_results


if __name__ == '__main__':
    setup()
    # register_contact(
    #     'King Dedede',
    #     ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex('ff' * 32)).public_key(),
    # )
    asyncio.run(send_exchange_key(_HOST, _PORT, 1))
    _DB_NAME = 'client_database3.db'
    _PRIVATE_KEY = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex('11' * 32))
    asyncio.run(send_exchange_key(_HOST, _PORT, 1))
    _DB_NAME = 'client_database2.db'
    _PRIVATE_KEY = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex('ff' * 32))
    asyncio.run(retrieve_exchange_keys(_HOST, _PORT))

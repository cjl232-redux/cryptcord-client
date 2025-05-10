import asyncio
import inspect
import json
import sqlite3
from base64 import urlsafe_b64decode, urlsafe_b64encode
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey, Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey

_HOST = '127.0.0.1'
_PORT = 8888
_DB_NAME = 'test_database.db'
_MAX_REQUEST_BYTES = 4096
# Debug keys
kirby_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex('00' * 32))
dedede_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex('ff' * 32))

# Order needs to be:
# Request is made
# No, I think this is ultimately fine... I mean, regardless, you could DDOS or whatever
# the technical term is by just getting a correct public key and forcing it to continually 
# check an incorrect signature

#TODO: probably ditch the replacement after all, instead just... hm... not sure, really
# The problem is you could clog up the system by sending thousands of exchange keys to random addresses

def setup():
    with sqlite3.connect(_DB_NAME, autocommit=True) as connection:
        cursor = connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS users')
        cursor.execute('DROP TABLE IF EXISTS messages')
        cursor.execute('DROP TABLE IF EXISTS exchange_keys')
        cursor.execute((
            'CREATE TABLE IF NOT EXISTS users('
            '   id INTEGER PRIMARY KEY,'
            '   verification_key CHAR(44) UNIQUE NOT NULL'
            ')'
        ))
        cursor.execute((
            'CREATE TABLE IF NOT EXISTS messages('
            '   id INTEGER PRIMARY KEY,'
            '   sender_id INTEGER NOT NULL,'
            '   recipient_id INTEGER NOT NULL,'
            '   encrypted_message TEXT NOT NULL,'
            '   signature CHAR(88) NOT NULL,'
            '   timestamp DATETIME NOT NULL,'
            '   FOREIGN KEY (sender_id) REFERENCES users(id),'
            '   FOREIGN KEY (recipient_id) REFERENCES users(id)'
            ')'
        ))
        cursor.execute((
            'CREATE TABLE IF NOT EXISTS exchange_keys('
            '   id INTEGER PRIMARY KEY,'
            '   sender_id INTEGER NOT NULL,'
            '   recipient_id INTEGER NOT NULL,'
            '   public_key CHAR(44) NOT NULL,'
            '   signature CHAR(88) NOT NULL,'
            '   FOREIGN KEY (sender_id) REFERENCES users(id),'
            '   FOREIGN KEY (recipient_id) REFERENCES users(id),'
            '   UNIQUE(sender_id, recipient_id) ON CONFLICT REPLACE'
            ')'
        ))

def get_user_id(verification_key: str) -> int:
    if not isinstance(verification_key, str):
        raise TypeError('Invalid verification key.')
    with sqlite3.connect(_DB_NAME, autocommit=True) as connection:
        cursor = connection.cursor()
        # Attempt to retrieve the key's associated id.
        cursor.execute(
            'SELECT id FROM users WHERE verification_key = ? LIMIT 1',
            (verification_key,),
        )
        result = cursor.fetchone()
        # If the key is not found but is a valid format, register it.
        if result is None:
            try:
                Ed25519PublicKey.from_public_bytes(
                    data=urlsafe_b64decode(verification_key.encode()),
                )
            except:
                raise ValueError('Invalid verification key.')
            cursor.execute(
                'INSERT INTO users (verification_key) VALUES (?)',
                (verification_key,),
            )
            cursor.execute(
                'SELECT id FROM users WHERE verification_key = ? LIMIT 1',
                (verification_key,),
            )
            result = cursor.fetchone()
        # Return the id associated with the existing or newly registered key.
        return result[0]

def send_exchange_key(
        user_id,
        recipient_ed25519_public_key,
        x25519_public_key,
        x25519_public_key_signature,
    ) -> dict:
    # For now, don't worry about failure responses, just let it raise errors.
    # Probably need to put failure responses extracted from an exception raised to the listen function
    recipient_id = get_user_id(recipient_ed25519_public_key)

    # Validate the exchange key:
    # Worth considering shifting validation to the client for performance, especially if blocking
    try:
        X25519PublicKey.from_public_bytes(
            data=urlsafe_b64decode(x25519_public_key.encode()),
        )
    except:
        raise ValueError('Invalid exchange key.')
    
    # Post the exchange key to the database:
    with sqlite3.connect(_DB_NAME, autocommit=True) as connection:
        cursor = connection.cursor()
        cursor.execute(
            (
                'INSERT INTO exchange_keys ( '
                '   sender_id, '
                '   recipient_id, '
                '   public_key, '
                '   signature '
                ') '
                'VALUES ('
                '   ?, '
                '   ?, '
                '   ?, '
                '   ? '
                ') '
            ),
            (
                user_id,
                recipient_id,
                x25519_public_key,
                x25519_public_key_signature,
            ),
        )
    
    # Return a successful response:
    return {'status': 'ok'}

def retrieve_exchange_keys(user_id):
    query = (
        'SELECT '
        '   u.verification_key, '
        '   e.public_key, '
        '   e.signature '
        'FROM '
        '   exchange_keys e '
        'LEFT JOIN '
        '   users u '
        'ON '
        '   e.sender_id = u.id '
        'WHERE '
        '   e.recipient_id = ? '
    )
    with sqlite3.connect(_DB_NAME, autocommit=False) as connection:
        cursor = connection.cursor()
        cursor.execute(query, (user_id,))
        exchange_keys = cursor.fetchall()
    return {'status': 'ok', 'exchange_keys': exchange_keys}
        

async def message_request(data):
    user_id = identify_user(data['verification_key'])
    if user_id:
        recipient_id = identify_user(data['recipient_key'])
        if recipient_id:
            return {'status': 'ok', 'message': 'Success'}
            # Add an entry to a table if it doesn't already exist

            # with sqlite3.connect(_DB_NAME) as connection:
            #     cursor = connection.cursor()
            #     try:
            #         cursor.execute(
            #             (
            #                 'SELECT id'
            #                 'FROM users'
            #                 'WHERE verification_key = ?'
            #                 'LIMIT 1'
            #             ),
            #             (data['recipient_key'],),
            #         )
            #         print(1)
            #         recipient_id = cursor.fetchone()
            #         print(recipient_id)
            #         return {'status': 'ok', 'message': 'Success'}
            #     except:
            #         return {'status': 'error', 'message': 'Unknown'}
        else:
            return {'status': 'error', 'message': 'Invalid Recipient'}
    else:
        return {'status': 'unauthorised', 'message': 'Authentication Failed'}



async def init_dm(data: dict) -> dict:
    print(data)
    return {'status': 'ok'}

_handlers = {
    'INIT_DM': init_dm,
    'MESSAGE_REQUEST': message_request,
    'SEND_EXCHANGE_KEY': send_exchange_key,
    'RETRIEVE_EXCHANGE_KEYS': retrieve_exchange_keys,
}

# Should lead with identifying the user for all handlers except REGISTER
# Changed my mind: don't allow register either. That should be for existing users.
# Or not. Ugh. Too exhausted for this right now. In general: store keys as hex after all. Require ed25519.
# Put in some kind of identification before the main handling, feed it as an argument

async def _handle_request(request: dict):
    required_parameters = ['data', 'verification_key', 'signature']
    if all(parameter in request for parameter in required_parameters):
        # Verify the request with the key provided:
        try:
            key_bytes = bytes.fromhex(request['verification_key'])
            public_key = Ed25519PublicKey.from_public_bytes(key_bytes)
            data_bytes = json.dumps(request['data']).encode()
            signature_bytes = bytes.fromhex(request['signature'])
            public_key.verify(signature_bytes, data_bytes)
        except InvalidSignature:
            return {'status': 'error', 'message': 'Verification Failed'}
        except (ValueError, UnsupportedAlgorithm):
            return {'status': 'error', 'message': 'Invalid Key Format'}
        except:
            return {'status': 'error', 'message': 'Malformed Request'}
        
        # If no exceptions occur, attempt to handle the request:
        if _handlers.get(request['data'].get('command')):
            return await _handlers[request['data']['command']](request['data'])
        elif request['data'].get('command'):
            return {'status': 'error', 'message': 'Unrecognised Command'}
        else:
            return {'status': 'error', 'message': 'Missing Command'}
        
    else:
        return {'status': 'error', 'message': 'Malformed Request'}
    
def handle_request(data, sender_public_key, signature) -> dict:
    # Verify the structure of the data and the command's existence:
    if not isinstance(data, dict):
        raise TypeError('Malformed request.')
    elif 'command' not in data:
        raise TypeError('No command parameter provided.')
    elif data.get('command') not in _handlers:
        raise ValueError(f'{data.get('command')} is not a recognised command.')
    
    # Verify that the key is valid and the signature is correct:
    try:
        key_bytes = urlsafe_b64decode(sender_public_key.encode())
        loaded_key = Ed25519PublicKey.from_public_bytes(key_bytes)
    except:
        raise ValueError('Invalid verification key.')
    try:
        loaded_signature = urlsafe_b64decode(signature.encode())
        loaded_key.verify(loaded_signature, json.dumps(data).encode())
    except:
        raise ValueError('Invalid signature.')
    
    # Retrieve the user id and store it in the data dictionary:
    data['user_id'] = get_user_id(sender_public_key)
    
    # Retrieve the handler and verify the arguments:
    handler = _handlers.get(data.get('command'))
    relevant_data = {}
    missing_parameters = []
    for k, v in inspect.signature(handler).parameters.items():
        if not isinstance(k, str):
            raise TypeError('Malformed request.')
        elif k in data:
            relevant_data[k] = data[k]
        elif v.default == inspect.Parameter.empty:
            missing_parameters.append(k)
    if missing_parameters:
        raise ValueError((
            f'Required parameters {', '.join(missing_parameters)} for '
            f'command {data.get('command')} are missing from the request.'
        ))
    
    # Get the response from the handler:
    return handler(**relevant_data)


async def listen(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    # Retrieve and report the connection details:
    address = writer.get_extra_info('peername')
    print(f'Connection from {address}')

    # Unpack and handle the request:
    print(f'reading from {address}')
    raw_request = await reader.read(_MAX_REQUEST_BYTES)
    print(f'verifying from {address}')
    if not reader.at_eof():
        try:
            processed_request = json.loads(raw_request.decode())
            required_arguments = ['data', 'public_key', 'signature']
            if len(processed_request) != len(required_arguments):
                raise TypeError('Malformed Request')
            elif any(x not in processed_request for x in required_arguments):
                raise TypeError('Malformed Request')
            response = handle_request(
                data=processed_request.get('data'),
                sender_public_key=processed_request.get('public_key'),
                signature=processed_request.get('signature'),
            )
        except json.JSONDecodeError:
            response = {'status': 'error', 'message': 'Malformed Request'}
        except Exception as e:
            response = {'status': 'error', 'message': str(e)}
    else:
        response = {'status': 'error', 'message': 'Request Too Large'}

    print(f'writing to {address}')
    writer.write(json.dumps(response).encode())
    await writer.drain()
    writer.close()
    await writer.wait_closed()
    

# # Split into receive/reply and handle (the latter returning a response)? I think so... or maybe that's silly
# async def ahandle_request(
#         reader: asyncio.StreamReader,
#         writer: asyncio.StreamWriter,
#     ):
#     address = writer.get_extra_info('peername')
#     print(f'Connection from {address}')
#     raw_request = await reader.read(1024)

#     # Expect data in the form: { data: {}, verification_key: x, signature: y} where y is a signature from data

#     # Handle the request and determine the appropriate response:
#     try:
#         processed_request = json.loads(raw_request.decode())
#         required_parameters = ['data', 'verification_key', 'signature']
#         if all(x in processed_request for x in required_parameters):
#             pass
#         else:
#             response = {'status': 'error', 'error': 'Malformed Request'}

#         if _handlers.get(data.get('command')):
#             response = await _handlers.get(data.get('command'))(data)
#         elif data.get('command'):
#             response = {'status': 'error', 'error': 'Invalid Command'}
#         else:
#             response = {'status': 'error', 'error': 'Malformed Request'}
#     except json.JSONDecodeError:
#         response = {'status': 'error', 'error': 'Malformed Request'}

#     # Write the response and close the connection:
#     writer.write(json.dumps(response).encode())
#     await writer.drain()
#     writer.close()
#     await writer.wait_closed()
    


# async def handle_process(data1, data2):
#     print(f"Handling PROCESS command with: {data1}, {data2}")
#     return f"Processed: {data1}, {data2}"

# async def handle_client(reader, writer):
#     addr = writer.get_extra_info('peername')
#     print(f"Connection from {addr}")

#     data = await reader.readline()
#     message = data.decode().strip()
#     parts = message.split('|')

#     if len(parts) == 3:
#         command, data1, data2 = parts
#         if command == 'INIT_DM':
#             response = await handle_process(data1, data2)
#         else:
#             response = 'Unknown command'
#     else:
#         response = 'Malformed message'

#     writer.write(response.encode())
#     await writer.drain()
#     writer.close()
#     await writer.wait_closed()

async def main():
    server = await asyncio.start_server(listen, _HOST, _PORT)
    async with server:
        await server.serve_forever()

# Run the server
setup()
asyncio.run(main())
import asyncio
import json
import sqlite3
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

_DB_NAME = 'test_database.db'
_MAX_REQUEST_BYTES = 4096

# Order needs to be:
# Request is made
# No, I think this is ultimately fine... I mean, regardless, you could DDOS or whatever
# the technical term is by just getting a correct public key and forcing it to continually 
# check an incorrect signature


def setup():
    with sqlite3.connect(_DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute((
            'CREATE TABLE IF NOT EXISTS users('
            '   id INTEGER PRIMARY KEY,'
            '   verification_key BYTEA NOT NULL'
            ')'            
        ))
        cursor.execute(
            'SELECT id FROM users WHERE verification_key = "12e0" LIMIT 1',
        )
        print(cursor.fetchone())

def identify_user(verification_key: str):
    with sqlite3.connect(_DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute(
            (
                'SELECT id'
                'FROM users'
                'WHERE verification_key = ?'
                'LIMIT 1'
            ),
            (verification_key,),
        )
        result = cursor.fetchone()
        if result is not None:
            return result[0]
        return result


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
}

# Should lead with identifying the user for all handlers except REGISTER
# Changed my mind: don't allow register either. That should be for existing users.
# Or not. Ugh. Too exhausted for this right now. In general: store keys as hex after all. Require ed25519.
# Put in some kind of identification before the main handling, feed it as an argument

async def handle_request(request: dict):
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

async def listen(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    # Retrieve and report the connection details:
    address = writer.get_extra_info('peername')
    print(f'Connection from {address}')

    # Unpack and handle the request:
    print(f'reading from {address}')
    raw_request = await reader.read(_MAX_REQUEST_BYTES)
    print(f'verifying from {address}')
    print(raw_request)
    if not reader.at_eof():
        try:
            processed_request = json.loads(raw_request.decode())
            response = await handle_request(processed_request)
        except json.JSONDecodeError:
            response = {'status': 'error', 'message': 'Malformed Request'}
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
    server = await asyncio.start_server(listen, '127.0.0.1', 8888)
    async with server:
        await server.serve_forever()

# Run the server
setup()
asyncio.run(main())
import asyncio
import json

from base64 import b64encode
from secrets import token_bytes

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

HOST = '127.0.0.1'
PORT = 8888
NUM_CONNECTIONS = 10

async def simulate_connection(i):
    private_key = Ed25519PrivateKey.generate()
    data = {}
    from random import random
    for i in range(int(random() * 1000)):
        data[str(i)] = 30
    signature = b64encode(private_key.sign(json.dumps(data).encode()))
    public_key = b64encode(private_key.public_key().public_bytes_raw())
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
        print(f"Connection {i} failed: {e}")

async def main():
    tasks = [simulate_connection(i) for i in range(NUM_CONNECTIONS)]
    await asyncio.gather(*tasks)

asyncio.run(main())

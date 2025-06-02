import asyncio

from base64 import b64encode

import aiohttp
import requests

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

universal_fernet = Fernet(Fernet.generate_key())

class Agent:
    def __init__(self, name: str):
        self.requests: list[dict[str, str]] = []
        for i in range(100):
            signature_key = Ed25519PrivateKey.generate()
            public_key = signature_key.public_key()
            public_bytes = b64encode(public_key.public_bytes_raw())
            recipient_bytes = b64encode(
                Ed25519PrivateKey.generate().public_key().public_bytes_raw(),
            )
            plaintext = f'Greetings from {name}!'
            ciphertext = universal_fernet.encrypt(plaintext.encode())
            signature = b64encode(signature_key.sign(ciphertext))
            self.requests.append({
                'public_key': public_bytes.decode(),
                'recipient_public_key': recipient_bytes.decode(),
                'encrypted_text': ciphertext.decode(),
                'signature': signature.decode(),
            })

agents = [Agent(f'Agent #{i + 1:02}') for i in range(5)]

# Ten agents, all making ten requests
async def async_request(request: dict[str, str], session: aiohttp.ClientSession):
    async with session.post('http://127.0.0.1:8000/messages/send', json=request) as response:
        r = await response.json()
        print(r)

async def async_session(agent: Agent):
    connector=aiohttp.TCPConnector(limit=60)
    async with aiohttp.ClientSession(connector=connector) as session:
        await asyncio.gather(*[async_request(request, session) for request in agent.requests])

async def async_agents():
    await asyncio.gather(*[async_session(agent) for agent in agents])

def async_main():
    asyncio.run(async_agents())

def sync_request(request: dict[str, str]):
    with requests.post('http://127.0.0.1:8000/messages/send', json=request) as response:
        print(response.json())

async def sync_session(agent: Agent):
    for request in agent.requests:
        sync_request(request)

async def sync_agents():
    await asyncio.gather(*[sync_session(agent) for agent in agents])

def sync_main():
    asyncio.run(sync_agents())

def test():
    time.sleep(1)

import timeit
import time
print(timeit.timeit(sync_main, number=1))
print(timeit.timeit(async_main, number=1))
print(timeit.timeit(test, number=1))

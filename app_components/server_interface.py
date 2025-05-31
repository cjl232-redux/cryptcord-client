import asyncio
import json

from base64 import b64encode
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from json_types import JSONDict

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
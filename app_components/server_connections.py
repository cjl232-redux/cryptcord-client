import asyncio
import json

from base64 import b64decode, b64encode

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from json_types import JSONDict

class ServerContext:
    def __init__(self, host: str, port: int, signature_key: Ed25519PrivateKey):
        self.host = host
        self.port = port
        self.signature_key = signature_key

    async def _async_send_request(self, data: JSONDict) -> JSONDict:

        # Generate signature bytes for the data.
        signature = self.signature_key.sign(json.dumps(data).encode())

        # Retrieve the sender's public key bytes.
        public_key = self.signature_key.public_key().public_bytes_raw()

        # Create a request dictionary, using Base64 encoding for byte values.
        request = {
            'data': data,
            'signature': b64encode(signature).decode(),
            'public_key': b64encode(public_key).decode(),
        }

        # Open a connection to the server.
        reader, writer = await asyncio.open_connection(self.host, self.port)

        # Transmit the request.
        writer.write(json.dumps(request).encode())
        await writer.drain()

        # Receive the response.
        raw_response = await reader.read()

        # Close the connection.
        writer.close()
        await writer.wait_closed()

        # Load and return the response.
        return json.loads(raw_response)
    
    def send_request(self, data: JSONDict) -> JSONDict:
        return asyncio.run(self._async_send_request(data))


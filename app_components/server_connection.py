import asyncio
import json

from base64 import b64decode, b64encode

from cryptography.hazmat.primitives.asymmetric import ed25519

type _JSONPrimitive = bool | int | float | str | None
type _JSONType = _JSONPrimitive | list['_JSONType'] | dict[str, '_JSONType']

# Should the server itself have to return signatures? That might be a good
# extra step.

class ServerConnection:
    def __init__(
            self,
            host: str,
            port: int,
            verification_key: ed25519.Ed25519PublicKey | None = None,
        ):
        self.host = host
        self.port = port
        self.verification_key = verification_key

    async def send_request(
            self,
            data: _JSONType,
            signature_key: ed25519.Ed25519PrivateKey,
        ):

        # Generate signature bytes for the data.
        signature = signature_key.sign(json.dumps(data).encode())

        # Retrieve the sender's public key bytes.
        public_key = signature_key.public_key().from_public_bytes()

        # Create a request dictionary, using Base64 encoding for byte values.
        request = {
            'data': data,
            'signature': b64encode(signature).decode(),
            'public_key': b64encode(public_key).decode(),
            'signature_requested': self.verification_key is not None,
        }

        # Open a connection to the server.
        reader, writer = await asyncio.open_connection(self.host, self.port)

        # Transmit the request.
        writer.write(json.dumps(request).encode())
        await writer.drain()

        # Receive the response.
        raw_response = await reader.read()
        #TODO: handle too large responses. Hm... maybe best to just have
        # this at -1 no matter what?

        # Close the connection.
        writer.close()
        await writer.wait_closed()

        # Load the response as a dictionary.
        response: _JSONType = json.loads(raw_response)

        # Confirm data is present in the response.
        if 'data' not in response:
            raise ValueError('Malformed response: missing data.')
        
        # If verification is required, retrieve and validate a signature.
        if self.verification_key is not None:
            if 'signature' not in response:
                raise ValueError('Malformed response: missing signature.')
            data_bytes = json.dumps(response['data']).encode()
            signature_bytes = b64decode(response['signature'])
            self.verification_key.verify(signature_bytes, data_bytes)

        # Return the data from the response.
        return response['data']


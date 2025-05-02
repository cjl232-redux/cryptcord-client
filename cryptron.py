import asyncio
import os
import threading

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from dotenv import load_dotenv
import discord

load_dotenv()

# Set the padding to be used for all encryption and decryption:
padding = padding.OAEP(
    mgf=padding.MGF1(algorithm=hashes.SHA256()),
    algorithm=hashes.SHA256(),
    label=None,
)

with open("private_key.pem", "rb") as file:
    private_key = serialization.load_pem_private_key(
        data=file.read(),
        password=os.environ.get('PRIVATE_KEY_PASSWORD').encode('utf-8'),
    )


# ciphertext=bytes.fromhex('ab231df5931f5823c0663e0872abfd6321967a0dd1eb2916d2ddb3f6440675a2468e8829eca923b5cc545652082a6d8883175b1a95e128788509cc8549189799646bb6c0067b2f375b11a1fbacf9c9ddb02380dcc6cc1e81e040b99f6116f7cc41056c57b6ce9f67a5863a40eea74cca3da9c58d7b76485b6b1373e0ba4db276ad0cd3a4632f9449a9f5745c188eaf78ff60cc02fe6d015ccb213b649a5d6e21b9daa5d5108c812a76ef6f3d5a29a0f1d95edaa6edf891e5d4f4b68d20a81f4c3b809e21af6225a479aea1027ce2d64f50448cc9809b2aacb00cd059102d6338e8d89ae7c6e1391d38d1ee51f14860028e830198c72faeba8d2ee586b5aff1a93065d478db3b1ba3c2040ca7d8bc266cdc6133c424f3c2361ccba9ff75a1cbbc3370849d83496ba6d478ba460f5a841e0524ef01e8aa01071a45a3353447db902eca9f9bbc99c6bced8f798c31e228a316bfd80878ecd08b978aa10d564663cac836d808af0bb739339eabe8d8749a02dd916c122ed36f6bc544394853801c997f4281ee610494fa36c44ab115912b752d3d1f3b7ad4e0beb14844c9a5f4cd93de6e19e020f3c0af103dff2933b07313215d0d800ccb70e829595d9cbc308d6106a157e7241e53137e646573bddf836ed756a151f1baf2e0420e3217959a3ec222e7a1246d8c7670aeb69aa2793824e1bd164a8574921c82f12a024be9850ef2')
# print(
#     private_key.decrypt(
#         ciphertext=ciphertext,
#         padding=padding.OAEP(
#             mgf=padding.MGF1(algorithm=hashes.SHA256()),
#             algorithm=hashes.SHA256(),
#             label=None,
#         ),
#     ).decode('utf-8')
# )
# exit()

# print(private_key.decrypt(
#     plaintext=plaintext.encode('utf-16'),
#     padding=padding.OAEP(
#         mgf=padding.MGF1(algorithm=hashes.SHA256()),
#         algorithm=hashes.SHA256(),
#         label=None,
#     ),
# ))

# private_key = rsa.generate_private_key(
#     public_exponent=65537,
#     key_size=4096,
# )

# with open('private_key.pem', 'wb') as file:
#     private_bytes = private_key.private_bytes(
#         encoding=serialization.Encoding.PEM,
#         format=serialization.PrivateFormat.PKCS8,
#         encryption_algorithm=serialization.BestAvailableEncryption(
#             os.environ.get('PRIVATE_KEY_PASSWORD').encode(),
#         ),
#     )
#     file.write(private_bytes)


intents = discord.Intents.default()
# intents.message_content = True

client = discord.Client(intents=intents)
client.intents.message_content = True

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

def input_thread():
    try:
        while True:
            plaintext = input()
            ciphertext = private_key.public_key().encrypt(
                plaintext=plaintext.encode('utf-8'),
                padding=padding,
            )
            asyncio.run_coroutine_threadsafe(
                client.get_channel(331386359518461959).send(ciphertext.hex()),
                client.loop,
            )
    except Exception as e:
        pass

threading.Thread(target=input_thread, daemon=True).start()

client.run(os.environ.get('TOKEN'))
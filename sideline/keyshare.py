from base64 import urlsafe_b64encode
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.fernet import Fernet

# Ugh... let's start with a two-way thing. Groups can come later.

class Participant:
    def __init__(self):
        self.signing_key = Ed25519PrivateKey.generate()
        self.verification_key = self.signing_key.public_key()
        self.generate_exchange_key()

    def generate_exchange_key(self):
        self.private_exchange_key = X25519PrivateKey.generate()
        self.public_exchange_bytes = self.private_exchange_key.public_key().public_bytes_raw()
        self.public_exchange_signature = self.signing_key.sign(self.public_exchange_bytes)


kirby = Participant()
bandana_dee = Participant()
king_dedede = Participant()

# Kirby verifies Dedede's provided key:
try:
    king_dedede.verification_key.verify(king_dedede.public_exchange_signature, king_dedede.public_exchange_bytes)
    print('Verified')
except:
    print('Not verified')
    exit()

# Kirby combines the keys:
key_1 = Fernet(urlsafe_b64encode(kirby.private_exchange_key.exchange(X25519PublicKey.from_public_bytes(king_dedede.public_exchange_bytes))))
print(key_1)

# Dedede verifies Kirby's provided key:
try:
    kirby.verification_key.verify(kirby.public_exchange_signature, kirby.public_exchange_bytes)
    print('Verified')
except:
    print('Not verified')
    exit()

# Dedede combines the keys:
key_2 = Fernet(urlsafe_b64encode(king_dedede.private_exchange_key.exchange(X25519PublicKey.from_public_bytes(kirby.public_exchange_bytes))))
print(key_2)

# Kirby sends a message:
message = key_1.encrypt(b'Poyo!')
print(message)

# Dedede decodes it:
print(key_2.decrypt(message))

# Bandana Dee tries to pretend to be Dedede:
try:
    king_dedede.verification_key.verify(bandana_dee.public_exchange_signature, bandana_dee.public_exchange_bytes)
    print('Verified')
except:
    print('Not verified')
    exit()





# b_key_2 = urlsafe_b64encode(key_2)
# print(urlsafe_b64encode(key_2))
# print((int(key_2.hex(), 16).bit_length() + 7) // 8)
# print((int(b_key_2.hex(), 16).bit_length() + 7) // 8)

# print(int(Fernet.generate_key().hex(), 16))
# print(Fernet(urlsafe_b64encode(key_1)))

# Confirmed: the two are the same.




# # Generate on the client side by getting (signed) shared keys from all partners.
# # How to transmit that they should be provided, though...?

# domestic_key = X25519PrivateKey.generate()
# print(domestic_key)

# foreign_keys = []
# for _ in range(10):
#     foreign_keys.append(X25519PrivateKey.generate())

# current_key = domestic_key
# print(current_key)
# for x in foreign_keys:
#     shared_key = X25519PrivateKey.from_private_bytes(current_key.exchange(x.public_key()))

# print(shared_key.public_key().public_bytes_raw())

# key2 = foreign_keys[0]
# key2 = X25519PrivateKey.from_private_bytes(key2.exchange(domestic_key.public_key()))
# for i in range(9):
#     key2 = X25519PrivateKey.from_private_bytes(key2.exchange(foreign_keys[i + 1].public_key()))

# print(key2.public_key().public_bytes_raw())
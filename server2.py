import sqlite3
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from secrets import token_hex

DB_NAME = 'database.db'

# How can I get a user-friendly (read: fast) circular process? Automatically approve based on stored keys?
# I want absolute security here.


# Members table, applicants table, votes table
# Can't index blobs. Alternatives... hex format then string index? NOTE: this was a lie
# Or a stored user id for the server that gets validated on startup?
# Should index the public key, look it up when connecting, refuse connection if
# missing from users (allow application requests though). On connection, associate the
# correctly signed connection with e.g. handle. Drop the index if issues arise, but shouldn't do. It'll only get used on connection, int id will elsewhere

# Cannot rely on storing public keys on the server. They need to be on people's computers to be trustworthy.
# So while they can be used for lookups, the server-side copies should never be used for verification.

with open('public_key.pem', 'rb') as file:
    data = file.read()

key = serialization.load_pem_public_key(data).public_bytes_raw()

with sqlite3.connect(DB_NAME) as connection:
    cursor = connection.cursor()
    cursor.execute(
        (
            'CREATE TABLE IF NOT EXISTS members('
            '   id INTEGER PRIMARY KEY,'
            '   verification_key BYTEA UNIQUE NOT NULL,'
            '   handle VARCHAR(255) UNIQUE NOT NULL'
            ')'
        ),
    )
    cursor.execute(
        (
            'CREATE INDEX IF NOT EXISTS verification_key_index '
            'ON members (verification_key)'
        ),
    )
    cursor.execute(
        (
            'INSERT INTO members (verification_key, handle)'
            'VALUES (?, ?)'
        ),
        (
            Ed25519PrivateKey.generate().public_key().public_bytes_raw(),
            token_hex(16),
        ),
    )
    cursor.execute(
        (
            'ANALYZE'
        ),
    )
    cursor.execute(
        (
            'EXPLAIN QUERY PLAN SELECT * FROM members WHERE verification_key = ?'
        ),
        (
            key,
        )
    )
    print(cursor.fetchall())

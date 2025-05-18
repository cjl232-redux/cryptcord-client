from contextlib import closing
import sqlite3

def create_tables(conn: sqlite3.Connection):
    with closing(conn.cursor()) as cursor:
        cursor.execute((
            'CREATE TABLE IF NOT EXISTS '
            '    contacts( '
            '        id INTEGER PRIMARY KEY, '
            '        name VARCHAR(255) UNIQUE NOT NULL, '
            '        ed25519_public_key CHAR(44) UNIQUE NOT NULL '
            '    ) '
        ))
        cursor.execute((
            'CREATE TABLE IF NOT EXISTS '
            '    encryption_keys( '
            '        id INTEGER PRIMARY KEY, '
            '        contact_id INTEGER NOT NULL, '
            '        shared_secret_key CHAR(44) NOT NULL, '
            '        FOREIGN KEY(contact_id) '
            '            REFERENCES contacts(id) '
            '            ON DELETE CASCADE, '
            '        UNIQUE(contact_id) '
            '            ON CONFLICT REPLACE '
            '    ) '
        ))
        cursor.execute((
            'CREATE TABLE IF NOT EXISTS '
            '    pending_exchanges( '
            '        id INTEGER PRIMARY KEY, '
            '        contact_id INTEGER NOT NULL, '
            '        x25519_private_key CHAR(44) NOT NULL, '
            '        FOREIGN KEY(contact_id) '
            '            REFERENCES contacts(id) '
            '            ON DELETE CASCADE, '
            '        UNIQUE(contact_id) '
            '            ON CONFLICT REPLACE '
            '    ) '
        ))

def add_contact(conn: sqlite3.Connection, name: str, key: str):
    query = 'INSERT INTO contacts(name, ed25519_public_key) VALUES(?, ?)'
    with closing(conn.cursor()) as cursor:
        cursor.execute(query, (name, key))
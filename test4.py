import sqlite3

with sqlite3.connect('client_database.db') as connection:
    cursor = connection.cursor()
    cursor.execute((
        'SELECT '
        '   contacts.id, '
        '   contacts.nickname, '
        '   encryption_keys.id IS NOT NULL as exchange_complete, '
        '   pending_exchanges.id IS NOT NULL as exchange_pending '
        'FROM '
        '   contacts '
        'LEFT JOIN '
        '   encryption_keys '
        'ON '
        '   contacts.id = encryption_keys.contact_id '
        'LEFT JOIN '
        '   pending_exchanges '
        'ON '
        '   contacts.id = pending_exchanges.contact_id '
    ))
    print(cursor.fetchall())
import sqlite3

DB_NAME = 'database.db'

# When a person joins:
# They select a username
# If it exists already, they can't have it UNLESS it's associated with their public key
# Otherwise, add to a users table: username and user's signature key
# Need to factor in approved keys... better to have admins set up users, I think. Or the owner, moreover
# Going forward, ALL requests by the user must be signed, and this will be used to verify them
# Signing in sends a request that reads 'SIGNIN', etc.

# ...maybe??? Ugh...

# Messages all need to be signed, regardless of anything else

# Database setup:
with sqlite3.connect(DB_NAME) as connection:
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            public_key BLOB NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message BLOB NOT NULL,
            signature BLOB NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

# # import asyncio

# # HOST = '0.0.0.0'
# # PORT = 12345

# # async def handle_client(reader, writer):
# #     addr = writer.get_extra_info('peername')
# #     print(f'New connection from {addr}')

# #     try:
# #         while True:
# #             data = await reader.read(4096)
# #             if not data:
# #                 break  # connection closed by client
# #             message = data.decode()
# #             print(f"Received from {addr}: {message}")

# #             # Echo message back to client (for testing)
# #             await asyncio.sleep(2)
# #             writer.write(data)
# #             await writer.drain()
# #     except Exception as e:
# #         print(f"Error handling client {addr}: {e}")
# #     finally:
# #         print(f"Connection closed from {addr}")
# #         writer.close()
# #         await writer.wait_closed()

# # async def main():
# #     server = await asyncio.start_server(handle_client, HOST, PORT)
# #     print(f"Server listening on {HOST}:{PORT}")

# #     async with server:
# #         await server.serve_forever()

# # #if __name__ == "__main__":
# # asyncio.run(main())

# import asyncio
# import sqlite3
# from datetime import datetime

# DB_NAME = "messages.db"

# # Create the database and table if they don't exist yet
# def setup_database():
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS messages (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             client_id TEXT,
#             timestamp TEXT,
#             message TEXT
#         )
#     ''')
#     conn.commit()
#     conn.close()

# async def handle_client(reader, writer):
#     addr = writer.get_extra_info('peername')
#     client_id = f"{addr[0]}:{addr[1]}"
#     print(f"New connection from {client_id}")

#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()

#     while True:
#         data = await reader.read(4096)
#         if not data:
#             break

#         message = data.decode().strip()

#         if message.startswith("GET "):
#             try:
#                 n = int(message[4:])
#                 c.execute('SELECT timestamp, client_id, message FROM messages ORDER BY id DESC LIMIT ?', (n,))
#                 rows = c.fetchall()

#                 response = "\n".join(f"[{ts}] {cid}: {msg}" for ts, cid, msg in reversed(rows))
#                 if not response:
#                     response = "No messages found."
#                 response += "\n"

#             except ValueError:
#                 response = "Invalid GET request. Usage: GET N\n"

#             writer.write(response.encode())
#             await writer.drain()

#         else:
#             timestamp = datetime.now().isoformat()
#             c.execute('INSERT INTO messages (client_id, timestamp, message) VALUES (?, ?, ?)',
#                       (client_id, timestamp, message))
#             conn.commit()

#             response = "Message saved.\n"
#             writer.write(response.encode())
#             await writer.drain()

#     print(f"Connection closed: {client_id}")
#     writer.close()
#     await writer.wait_closed()
#     conn.close()

# async def main():
#     setup_database()
#     server = await asyncio.start_server(handle_client, '127.0.0.1', 12345)

#     addr = server.sockets[0].getsockname()
#     print(f'Serving on {addr}')

#     async with server:
#         await server.serve_forever()

# asyncio.run(main())
import asyncio

HOST = '127.0.0.1'
PORT = 12345

async def tcp_client():
    reader, writer = await asyncio.open_connection(HOST, PORT)
    
    message = "GET 100"
    print(f"Sending: {message}")
    writer.write(message.encode())
    await writer.drain()

    response = await reader.read(4096)
    print(f"Received from server: {response.decode()}")

    print("Closing connection")
    writer.close()
    await writer.wait_closed()

asyncio.run(tcp_client())

# import asyncio

# HOST = '127.0.0.1'
# PORT = 12345
# NUM_CLIENTS = 1000

# async def single_client(id):
#     try:
#         reader, writer = await asyncio.open_connection(HOST, PORT)
#         message = f"Hello from client {id}"
#         writer.write(message.encode())
#         await writer.drain()

#         response = await reader.read(4096)
#         print(f"Client {id} received: {response.decode()}")

#         # Keep the connection open for a bit to simulate "active" clients
#         await asyncio.sleep(5)

#         writer.close()
#         await writer.wait_closed()
#     except Exception as e:
#         print(f"Client {id} error: {e}")

# async def main():
#     tasks = []
#     for i in range(NUM_CLIENTS):
#         task = asyncio.create_task(single_client(i))
#         tasks.append(task)

#     await asyncio.gather(*tasks)

# asyncio.run(main())

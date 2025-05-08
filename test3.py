import asyncio
import time

def blocking_task(name, delay):
    print(f"{name} start (sleeping {delay}s)")
    time.sleep(delay)
    print(f"{name} end")

async def main():
    tasks = [
        asyncio.to_thread(blocking_task, "Task 1", 2),
        asyncio.to_thread(blocking_task, "Task 2", 3),
        asyncio.to_thread(blocking_task, "Task 3", 1),
    ]
    await asyncio.gather(*tasks)

asyncio.run(main())
x: dict[str, str | list[str]] = {
  "sender_keys": [
    "XuPFHG1T6MfukWZSDEjLCAqFFh9EAUWUYRZow_1FJ6c=",
    "1pkkOi6TX-o8RTU4NAZXT6SRcaUu6DFKIg7eMB9ujD8=",
    "Vx_ZU7jYWd-csCdgK3gRZRRBmTdkV3VCV-clcbzxaBg="
  ],
  "min_datetime": "2025-06-14T13:34:26.311Z",
  "public_key": "PBiNdoolrxt0FdTiAA2wSbG4eoKClTJEP2JoVFGrWU0="
}

import asyncio
from httpx import AsyncClient, post
from timeit import timeit

async def request():
    async with AsyncClient() as client:
        y = await client.post('http://127.0.0.1:8000/exchange-keys/retrieve', json=x)
        return y
async def main():
    async with AsyncClient() as client:
        requests = [client.post('http://127.0.0.1:8000/exchange-keys/retrieve', json=x)] * 10
        return await asyncio.gather(*requests)

def asyncreqs():
    asyncio.run(main())

def syncreqs():
    for _ in range(10):
        post('http://127.0.0.1:8000/exchange-keys/retrieve', json=x)


print(timeit(asyncreqs, number=30))
print(timeit(syncreqs, number=30))


# from sqlalchemy import create_engine
# from sqlalchemy.orm import Session
# from database.models import ReceivedExchangeKey, SentExchangeKey
# from database.schemas.output import ReceivedExchangeKeyOutputSchema
# from secrets import token_bytes
# from base64 import urlsafe_b64encode

# engine = create_engine('sqlite:///database4.db')
# with Session(engine, expire_on_commit=False) as session:
#     key = session.get_one(ReceivedExchangeKey, 1)
#     session.add(SentExchangeKey(public_key=urlsafe_b64encode(token_bytes(32)).decode(), private_key=urlsafe_b64encode(token_bytes(32)).decode()))
#     session.commit()
#     key.sent_exchange_key_id = 1
#     session.commit()
#     print(key)
#     output = ReceivedExchangeKeyOutputSchema.model_validate(key)
#     print(output)




# import tkinter as tk
# from tkinter import ttk

# PADDING = 20

# root = tk.Tk()
# root.geometry("400x300")

# # Container frame
# container = ttk.Frame(root)
# container.grid(row=0, column=0, sticky="nsew")
# root.rowconfigure(0, weight=1)
# root.columnconfigure(0, weight=1)

# # Canvas and scrollbar
# canvas = tk.Canvas(container, highlightthickness=0)
# scrollbar = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
# canvas.configure(yscrollcommand=scrollbar.set)

# canvas.grid(row=0, column=0, sticky='nsew')
# scrollbar.grid(row=0, column=1, sticky='ns', padx=(0, PADDING))

# container.rowconfigure(0, weight=1)
# container.columnconfigure(0, weight=1)

# # Frame inside canvas (acts as outer padding frame)
# padding_frame = ttk.Frame(canvas)
# canvas_window = canvas.create_window((0, 0), window=padding_frame, anchor='nw')

# # Actual interior content frame inside the padding frame
# interior = ttk.Frame(padding_frame)
# interior.grid(row=0, column=0, sticky='nsew', padx=PADDING, pady=PADDING)

# padding_frame.columnconfigure(0, weight=1)
# padding_frame.rowconfigure(0, weight=1)

# # Make the canvas expand the window when resized
# def on_canvas_configure(event):
#     canvas.itemconfig(canvas_window, width=event.width)

# canvas.bind("<Configure>", on_canvas_configure)

# # Update scrollregion
# def on_padding_configure(event):
#     # Get bounding box of all items
#     bbox = canvas.bbox("all")
#     if not bbox:
#         return  # No content to calculate

#     x0, y0, x1, y1 = bbox
#     content_height = y1 - y0
#     canvas_height = canvas.winfo_height()

#     # Clamp the scrollregion to not be smaller than the visible canvas
#     y1_clamped = max(content_height, canvas_height)
#     canvas.configure(scrollregion=(x0, y0, x1, y0 + y1_clamped))

# padding_frame.bind("<Configure>", on_padding_configure)

# # Sample content
# for i in range(30):
#     ttk.Label(interior, text=f"Label {i}").grid(row=i, column=0, sticky='w', pady=2)

# root.mainloop()

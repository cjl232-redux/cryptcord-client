# Worth considering using older fernet keys?
# Another serious consideration: whether to use signatures at all outside the fernet decryption
# I'm inclined to, so I can differentiate between message being from the wrong person and the message using the wrong key.
# Because in the latter case, a new exchange is likely needed.
# That said, I should keep that to the contacts section.

import tkinter as tk

from datetime import datetime
from tkinter import ttk

import requests

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app_components.scrollable_frames import ScrollableFrame
from database.models import Contact, Message, MessageType
from database.schemas.input import MessageInputSchema
from database.schemas.output import (
    ContactFernetOutputSchema,
    MessageOutputSchema,
)
from server.schemas.requests import PostMessageRequest
from server.schemas.responses import PostMessageResponse

class MessageWindow(tk.Toplevel):
    def __init__(
            self,
            master: tk.Widget | tk.Tk | tk.Toplevel,
            engine: Engine,
            signature_key: Ed25519PrivateKey,
            contact_id: int,
            contact_name: str,
            contact_verification_key: Ed25519PublicKey,
            post_message_url: str = 'http://127.0.0.1:8000/messages/send'
        ):
        # Call the parent constructor and store key values.
        super().__init__(master)
        self.engine = engine
        self.signature_key = signature_key
        self.contact_id = contact_id
        self.contact_name = contact_name
        self.contact_verification_key = contact_verification_key
        self.post_message_url = post_message_url
        self.last_message_timestamp = datetime.min
        self.loaded_nonces: set[int] = set()
        
        # Set up and place the message log.
        self.message_log = ScrollableFrame(self)
        self.message_log.grid(
            column=0,
            row=0,
            padx=10,
            pady=(10, 5),
            sticky='nsew',
        )
        self._update_message_log()

        # Set up and place the input box.
        self.input_box = tk.Text(self, height=2)
        self.input_box.grid(
            column=0,
            row=1,
            padx=10,
            pady=(5, 10),
            sticky='nsew',
        )
        self.input_box.focus()

        self.input_box.bind('<Return>', self._post_message)
        self.input_box.bind('<Shift-Return>', lambda *_: None)

    def _update_message_log(self):
        with Session(self.engine) as session:
            statement = select(
                Message,
            ).where(
                Message.contact_id == self.contact_id,
            ).where(
                Message.timestamp >= self.last_message_timestamp,
            ).order_by(
                Message.timestamp,
            )
            messages = (
                MessageOutputSchema.model_validate(message)
                for message in session.scalars(statement)
            )
            for message in messages:
                if message.nonce not in self.loaded_nonces:
                    author_label = ttk.Label(self.message_log.interior)
                    if message.message_type == MessageType.SENT.value:
                        author_label.config(text='You:')
                    else:
                        author_label.config(text=f'{self.contact_name}:')
                    author_label.grid(
                        column=0,
                        row=len(self.loaded_nonces),
                        sticky='nw',
                        padx=(10, 5),
                        pady=(10 if len(self.loaded_nonces) == 0 else 5, 5),
                    )
                    message_label = ttk.Label(
                        master=self.message_log.interior,
                        text=message.text,
                        wraplength=480,
                        anchor='nw',
                    )
                    message_label.grid(
                        column=1,
                        row=len(self.loaded_nonces),
                        sticky='nsew',
                        padx=(5, 10),
                        pady=(10 if len(self.loaded_nonces) == 0 else 5, 5),
                    )
                    self.loaded_nonces.add(message.nonce)
                    self.last_message_timestamp = message.timestamp
    
    def _post_message(self, *_):
        """
        Post a message to the contact.

        If the input box contains text after stripping trailing whitespace,
        encrypt the text using a Fernet key, assemble and send a request, and
        then register the sent message using the returned timestamp and nonce.
        """
        # Retrieve the message text and ensure it isn't empty.
        message_text = self.input_box.get('1.0', tk.END).rstrip()
        if message_text:
            # Retrieve the current symmetric key.
            with Session(self.engine) as session:
                contact = ContactFernetOutputSchema.model_validate(
                    session.get(Contact, self.contact_id),
                )
            if contact.fernet_key is not None:
                ciphertext = contact.fernet_key.encrypt(message_text.encode())
                data = PostMessageRequest.model_validate(
                    {
                        'public_key': self.signature_key.public_key(),
                        'recipient_public_key': self.contact_verification_key,
                        'encrypted_text': ciphertext,
                        'signature': self.signature_key.sign(ciphertext),
                    }
                )
                response = requests.post(
                    url=self.post_message_url,
                    json=data.model_dump(),
                )
                if response.status_code == 200:
                    response = PostMessageResponse.model_validate(
                        response.json(),
                    )
                    with Session(self.engine) as session:
                        message = MessageInputSchema(
                            text=message_text,
                            timestamp=response.data.timestamp,
                            message_type=MessageType.SENT,
                            contact_id=self.contact_id,
                            nonce=response.data.nonce,
                        )
                        session.add(Message(**message.model_dump()))
                        session.commit()
                    yview = self.message_log.canvas.yview()
                    self._update_message_log()
                    if yview[1] == 1.0:
                        self.after_idle(
                            lambda: self.message_log.canvas.yview_moveto(1.0),
                        )
                else:
                    print('connection failed')
                    # Error
            else:
                print('no fernet key')
                # Error message
        self.input_box.delete('1.0', tk.END)
        return 'break'
        




#         # # Retrieve the name and symmetric key for the contact.
#         # with Session(self.engine) as session:
#         #     contact = session.get_one(Contact, contact_id)
#         #     self.title(contact.name)
#         #     self.contact_key = contact.public_key
#         #     self.fernet_key = None
#         #     if contact.fernet_key is not None:
#         #         self.fernet_key = Fernet(contact.fernet_key.encode())
        
#         # # Set up the message log and a label for all message instances.
#         # self.message_log = ScrollableFrame(self)
#         # self.message_log.grid(
#         #     column=0,
#         #     row=0,
#         #     padx=10,
#         #     pady=(10, 5),
#         #     sticky='nsew',
#         # )
#         # with Session(self.engine) as session:
#         #     statement = select(
#         #         Message,
#         #     ).where(
#         #         Message.contact_id == self.contact_id,
#         #     ).order_by(
#         #         Message.timestamp,
#         #     )
#         #     for message in session.scalars(statement):
#         #         self._load_message(message)
#         # self.message_log.interior.columnconfigure(1, weight=1)
#         # self.after_idle(lambda: self.message_log.canvas.yview_moveto(1.0))

#         # self.input_box = tk.Text(self, height=2)
#         # self.input_box.grid(
#         #     column=0,
#         #     row=1,
#         #     padx=10,
#         #     pady=(5, 10),
#         #     sticky='nsew',
#         # )
#         # self.input_box.focus()

#         # self.input_box.bind('<Return>', self._send_message)
#         # self.input_box.bind('<Shift-Return>', lambda *_: None)

#         # self.columnconfigure(0, weight=1)
#         # self.rowconfigure(0, weight=1)

#         # button = ttk.Button(self)
#         # button.grid(column=0, row=2)

#     def _send_message(self, *_):
#         message_text = self.input_box.get('1.0', tk.END).rstrip()
#         if message_text:
#             # Verify that a fernet key is present. If not, try to load one.
#             if self.fernet_key is None:
#                 with Session(self.engine) as session:
#                     contact = session.get_one(Contact, self.contact_id)
#                     if contact.fernet_key is not None:
#                         self.fernet_key = Fernet(contact.fernet_key.encode())
#                     else:
#                         messagebox.showerror(
#                             title='Missing Secret Key',
#                             message=(
#                                 'No shared secret key is available for this '
#                                 'contact. Until one is created by a '
#                                 'successful key exchange, messages cannot be '
#                                 'sent or received.'
#                             )
#                         )
#                         self.input_box.focus()
#                         return 'break'
#             encrypted_bytes = self.fernet_key.encrypt(message_text.encode())
#             signature_bytes = self.signature_key.sign(encrypted_bytes)
#             # Send these to the server.
#             response = self.server_interface.send_request({
#                 'action': 'POST_MESSAGE',
#                 'recipient_public_key': self.contact_key,
#                 'ciphertext': b64encode(encrypted_bytes).decode(),
#                 'signature': b64encode(signature_bytes).decode(),
#             })
#             if response.get('status', 500) == 201:
#                 print(response)
#                 message = Message(
#                     text=message_text,
#                     timestamp=datetime.fromisoformat(response['data']['timestamp']),
#                     contact_id=self.contact_id,
#                     message_type=MessageType.SENT,
#                 )
#                 with Session(self.engine) as session:
#                     session.add(message)
#                     session.commit()
#                 yview = self.message_log.canvas.yview()
#                 self._refresh_messages()
#                 if yview[1] == 1.0:
#                     self.after_idle(
#                         lambda: self.message_log.canvas.yview_moveto(1.0),
#                     )
#                 self.input_box.delete('1.0', tk.END)
#             else:
#                 messagebox.showerror(
#                     title='Message Send Failure',
#                     message=str(response['message']),
#                 )
#         self.input_box.focus()
#         return 'break'

#     def _refresh_messages(self):
#         with Session(self.engine) as session:
#             statement = select(
#                 Message,
#             ).where(
#                 Message.contact_id == self.contact_id,
#             ).where(
#                 Message.timestamp >= self.last_message_timestamp,
#             ).order_by(
#                 Message.timestamp,
#             )
#             for message in session.scalars(statement):
#                 self._load_message(message)

#     def _load_message(self, message: Message):
#         if not message.id in self.loaded_messages:
#             person_label = ttk.Label(self.message_log.interior, text='You:')
#             if message.message_type == MessageType.RECIEVED:
#                 person_label.config(text=f'{message.contact.name}:')
#             person_label.grid(
#                 column=0,
#                 row=len(self.loaded_messages),
#                 sticky='nw',
#                 padx=(10, 5),
#                 pady=(10 if len(self.loaded_messages) == 0 else 5, 5),
#             )
#             message_label = ttk.Label(
#                 master=self.message_log.interior,
#                 text=message.text,
#                 wraplength=480,
#                 anchor='nw',
#             )
#             message_label.grid(
#                 column=1,
#                 row=len(self.loaded_messages),
#                 sticky='nsew',
#                 padx=(5, 10),
#                 pady=(10 if len(self.loaded_messages) == 0 else 5, 5),
#             )
#             self.loaded_messages.add(message.id)
#             self.last_message_timestamp = message.timestamp

# # import tkinter as tk

# # from base64 import b64encode
# # from datetime import datetime
# # from tkinter import messagebox, ttk
# # from typing import Any

# # from cryptography.fernet import Fernet
# # from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
# # from sqlalchemy import Engine, select
# # from sqlalchemy.orm import Session

# # from app_components.scrollable_frames import ScrollableFrame
# # from database.models import Contact, Message, MessageType



# # Ideally want to make return (NOT shift return) send message
# # And tab move to the next widget per usual, not insert a tab (easier?)

# # First is done. We'll see about the second, may be simple.
# # Not trivial, at least... may have to ditch the idea of a scrollabletext class
# # Just program in dynamic text size instead

# class _MessageWindow(tk.Toplevel):
#     def __init__(
#             self,
#             master: tk.Widget | ttk.Widget | tk.Tk | tk.Toplevel,
#             engine: Engine,
#             signature_key: Ed25519PrivateKey,
#             contact_id: int,
#         ):
#         # Call the parent constructor and store key values.
#         super().__init__(master)
#         self.engine = engine
#         self.signature_key = signature_key
#         self.contact_id = contact_id
#         self.last_message_timestamp = datetime.min
#         self.loaded_messages: set[int] = set()

#         # Retrieve the name and symmetric key for the contact.
#         with Session(self.engine) as session:
#             contact = session.get_one(Contact, contact_id)
#             self.title(contact.name)
#             self.contact_key = contact.public_key
#             self.fernet_key = None
#             if contact.fernet_key is not None:
#                 self.fernet_key = Fernet(contact.fernet_key.encode())
        
#         # Set up the message log and a label for all message instances.
#         self.message_log = ScrollableFrame(self)
#         self.message_log.grid(
#             column=0,
#             row=0,
#             padx=10,
#             pady=(10, 5),
#             sticky='nsew',
#         )
#         with Session(self.engine) as session:
#             statement = select(
#                 Message,
#             ).where(
#                 Message.contact_id == self.contact_id,
#             ).order_by(
#                 Message.timestamp,
#             )
#             for message in session.scalars(statement):
#                 self._load_message(message)
#         self.message_log.interior.columnconfigure(1, weight=1)
#         self.after_idle(lambda: self.message_log.canvas.yview_moveto(1.0))

#         self.input_box = tk.Text(self, height=2)
#         self.input_box.grid(
#             column=0,
#             row=1,
#             padx=10,
#             pady=(5, 10),
#             sticky='nsew',
#         )
#         self.input_box.focus()

#         self.input_box.bind('<Return>', self._send_message)
#         self.input_box.bind('<Shift-Return>', lambda *_: None)

#         self.columnconfigure(0, weight=1)
#         self.rowconfigure(0, weight=1)

#         button = ttk.Button(self)
#         button.grid(column=0, row=2)

#     def _send_message(self, *_):
#         message_text = self.input_box.get('1.0', tk.END).rstrip()
#         if message_text:
#             # Verify that a fernet key is present. If not, try to load one.
#             if self.fernet_key is None:
#                 with Session(self.engine) as session:
#                     contact = session.get_one(Contact, self.contact_id)
#                     if contact.fernet_key is not None:
#                         self.fernet_key = Fernet(contact.fernet_key.encode())
#                     else:
#                         messagebox.showerror(
#                             title='Missing Secret Key',
#                             message=(
#                                 'No shared secret key is available for this '
#                                 'contact. Until one is created by a '
#                                 'successful key exchange, messages cannot be '
#                                 'sent or received.'
#                             )
#                         )
#                         self.input_box.focus()
#                         return 'break'
#             encrypted_bytes = self.fernet_key.encrypt(message_text.encode())
#             signature_bytes = self.signature_key.sign(encrypted_bytes)
#             # Send these to the server.
#             response = self.server_interface.send_request({
#                 'action': 'POST_MESSAGE',
#                 'recipient_public_key': self.contact_key,
#                 'ciphertext': b64encode(encrypted_bytes).decode(),
#                 'signature': b64encode(signature_bytes).decode(),
#             })
#             if response.get('status', 500) == 201:
#                 print(response)
#                 message = Message(
#                     text=message_text,
#                     timestamp=datetime.fromisoformat(response['data']['timestamp']),
#                     contact_id=self.contact_id,
#                     message_type=MessageType.SENT,
#                 )
#                 with Session(self.engine) as session:
#                     session.add(message)
#                     session.commit()
#                 yview = self.message_log.canvas.yview()
#                 self._refresh_messages()
#                 if yview[1] == 1.0:
#                     self.after_idle(
#                         lambda: self.message_log.canvas.yview_moveto(1.0),
#                     )
#                 self.input_box.delete('1.0', tk.END)
#             else:
#                 messagebox.showerror(
#                     title='Message Send Failure',
#                     message=str(response['message']),
#                 )
#         self.input_box.focus()
#         return 'break'

#     def _refresh_messages(self):
#         with Session(self.engine) as session:
#             statement = select(
#                 Message,
#             ).where(
#                 Message.contact_id == self.contact_id,
#             ).where(
#                 Message.timestamp >= self.last_message_timestamp,
#             ).order_by(
#                 Message.timestamp,
#             )
#             for message in session.scalars(statement):
#                 self._load_message(message)

#     def _load_message(self, message: Message):
#         if not message.id in self.loaded_messages:
#             person_label = ttk.Label(self.message_log.interior, text='You:')
#             if message.message_type == MessageType.RECIEVED:
#                 person_label.config(text=f'{message.contact.name}:')
#             person_label.grid(
#                 column=0,
#                 row=len(self.loaded_messages),
#                 sticky='nw',
#                 padx=(10, 5),
#                 pady=(10 if len(self.loaded_messages) == 0 else 5, 5),
#             )
#             message_label = ttk.Label(
#                 master=self.message_log.interior,
#                 text=message.text,
#                 wraplength=480,
#                 anchor='nw',
#             )
#             message_label.grid(
#                 column=1,
#                 row=len(self.loaded_messages),
#                 sticky='nsew',
#                 padx=(5, 10),
#                 pady=(10 if len(self.loaded_messages) == 0 else 5, 5),
#             )
#             self.loaded_messages.add(message.id)
#             self.last_message_timestamp = message.timestamp

# if __name__ == '__main__':
#     app = tk.Tk()
#     text = tk.Text(app)
#     text.grid(column=0, row=0, sticky='nsew')
#     def _submit(*_):
#         val = text.get('1.0', f'{tk.END}-1c')
#         if val:
#             print(val)
#             text.delete('1.0', tk.END)
#         return 'break'

#     text.bind('<Return>', _submit)
#     text.bind('<Shift-Return>', lambda *_: None)
#     app.mainloop()
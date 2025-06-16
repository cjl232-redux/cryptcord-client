import tkinter as tk

from datetime import datetime
from tkinter import messagebox, ttk
from zoneinfo import ZoneInfo

import requests

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app_components.scrollable_frames import ScrollableFrame
from database.models import Contact, FernetKey, Message, MessageType
from database.schemas.input import MessageInputSchema
from database.schemas.output import (
    ContactOutputSchema,
    MessageOutputSchema,
)
from server.operations import post_message
from server.schemas.requests import PostMessageRequestModel
from server.schemas.responses import PostMessageResponseModel
from settings import settings

class MessageWindow(tk.Toplevel):
    def __init__(
            self,
            master: tk.Widget | tk.Tk | tk.Toplevel,
            engine: Engine,
            signature_key: Ed25519PrivateKey,
            contact_id: int,
            contact_name: str,
            contact_public_key: Ed25519PublicKey,
        ):
        # Call the TopLevel constructor.
        super().__init__(master)
        # Rename the window to the contact name.
        self.title(contact_name)
        # Store supplied values that are required for methods.
        self.engine = engine
        self.signature_key = signature_key
        self.contact_id = contact_id
        self.contact_name = contact_name
        self.contact_public_key = contact_public_key
        # Store metadata on loaded messages.
        self.last_message_timestamp = datetime.min
        self.loaded_nonces: set[int] = set()        
        # Create and place widgets.
        self.message_log = ScrollableFrame(self)
        self.message_log.grid(
            column=0,
            row=0,
            padx=settings.graphics.horizontal_padding,
            pady=settings.graphics.vertical_padding,
            sticky='nsew',
        )
        self.input_box = tk.Text(
            self,
            height=2,
            font=(
                settings.graphics.font_family,
                settings.graphics.font_size,
            ),
        )
        self.input_box.grid(
            column=0,
            row=1,
            padx=settings.graphics.horizontal_padding,
            pady=(0, settings.graphics.vertical_padding),
            sticky='nsew',
        )
        # Configure grid properties.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.message_log.interior.columnconfigure(1, weight=1, minsize=100)
        # Load in existing messages and set up regular updates.
        self._update_message_log()
        # Finalise and focus on the input box.
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
                if len(self.loaded_nonces) == 0:
                    pady = 0
                else:
                    pady = (settings.graphics.vertical_padding, 0)
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
                        pady=pady,
                    )
                    message_label = ttk.Label(
                        master=self.message_log.interior,
                        text=message.text,
                        anchor='nw',
                    )
                    message_label.bind(
                        sequence='<Configure>',
                        func=(
                            lambda _, label=message_label:
                                label.config(
                                    wraplength=label.winfo_width() - 5,
                                )
                        )
                    )
                    message_label.grid(
                        column=1,
                        row=len(self.loaded_nonces),
                        sticky='nsew',
                        ipadx=settings.graphics.horizontal_padding,
                        padx=settings.graphics.horizontal_padding,
                        pady=pady,
                    )
                    ttk.Label(
                        master=self.message_log.interior,
                        text=message.timestamp.astimezone(
                            ZoneInfo('Europe/London'),
                        ).strftime(
                            '%Y-%m-%d %H:%M',
                        ),
                        anchor='nw',
                    ).grid(
                        column=2,
                        row=len(self.loaded_nonces),
                        sticky='nw',
                        pady=pady,
                    )
                    self.loaded_nonces.add(message.nonce)
                    self.last_message_timestamp = message.timestamp
        self.after(
            ms=int(settings.functionality.message_refresh_rate * 1000),
            func=self._update_message_log,
        )
    
    def _post_message(self, *_):
        """
        Post a message to the contact.

        If the input box contains text, then encrypt it using a Fernet key,
        assemble and send a post request, then store the message using the
        response timestamp and nonce.
        """
        # Retrieve the message text and ensure it isn't empty.
        message_text = self.input_box.get('1.0', tk.END).rstrip()
        if message_text:
            post_message(
                engine=self.engine,
                signature_key=self.signature_key,
                plaintext=message_text,
                contact_id=self.contact_id,
            )
            self._update_message_log()
            self.input_box.delete('1.0', tk.END)
        return 'break'
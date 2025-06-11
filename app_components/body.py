import tkinter as tk

from base64 import urlsafe_b64encode
from tkinter import ttk

import pyperclip

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from sqlalchemy import Engine

from app_components.contacts import ContactsPane
from settings import settings

class _Notebook(ttk.Notebook):
    def __init__(
            self,
            master: 'Body',
            engine: Engine,
            signature_key: Ed25519PrivateKey,
        ):
        super().__init__(master)
        self.add(ContactsPane(self, engine, signature_key), text='Contacts')

class _PublicKeyDisplay(ttk.Frame):
    def __init__(
            self,
            master: 'Body',
            public_key: Ed25519PublicKey,
        ):
        super().__init__(master)
        public_key_b64 = urlsafe_b64encode(public_key.public_bytes_raw())
        ttk.Label(
            master=self,
            text=f'Your public key: {public_key_b64.decode()}',
            anchor='w',
            font=(
                settings.graphics.font_family,
                settings.graphics.font_size,
                'normal',
            ),
        ).grid(
            column=0,
            row=0,
            sticky='w',
            padx=(0, 5),
        )
        ttk.Button(
            master=self,
            text='Copy',
            command=lambda *_: pyperclip.copy(public_key_b64.decode()),
        ).grid(
            column=1,
            row=0,
            sticky='w',
        )
        self.columnconfigure(1, weight=1)

class Body(ttk.Frame):
    def __init__(
            self,
            master: tk.Tk,
            engine: Engine,
            signature_key: Ed25519PrivateKey,
        ):
        # Call the Frame constructor.
        super().__init__(master)
        # Create and place widgets.
        _Notebook(
            master=self,
            engine=engine,
            signature_key=signature_key,
        ).grid(
            column=0,
            row=0,
            sticky='nsew',
            padx=settings.graphics.horizontal_padding,
            pady=settings.graphics.vertical_padding,
        )
        _PublicKeyDisplay(
            master=self,
            public_key=signature_key.public_key(),
        ).grid(
            column=0,
            row=1,
            sticky='w',
            padx=settings.graphics.horizontal_padding,
            pady=(0, settings.graphics.vertical_padding),
        )
        # Configure grid properties.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        
        # notebook = ttk.Notebook(self)
        # notebook.add(
        #     child=ContactsPane(notebook, engine, signature_key),
        #     text='Contacts',
        # )
        # notebook.grid(column=0, row=0, sticky='nsew', padx=)

        # self.notebook = ttk.Notebook(self)
        # self.notebook.add(
        #     child=ContactsPane(
        #         self.notebook,
        #         engine,
        #         signature_key,
        #     ),
        #     text='Contacts',
        # )
        # self.notebook.grid(
        #     column=0,
        #     row=0,
        #     sticky='nsew',
        #     padx=5,
        #     pady=5,
        #     columnspan=2,
        # )
        
        # # Display the user's public key in Base64 form.
        # public_bytes = signature_key.public_key().public_bytes_raw()
        # public_bytes_b64 = b64encode(public_bytes).decode()
        # label = ttk.Label(self, text=f'Your public key: {public_bytes_b64}')
        # label.grid(column=0, row=1, sticky='w', padx=5, pady=5)
        # copy_button = ttk.Button(
        #     master=self,
        #     text='Copy',
        #     command=lambda *_: pyperclip.copy(public_bytes_b64),
        # )
        # copy_button.grid(column=1, row=1, sticky='w', padx=5, pady=5)

        # # Configure overall grid properties.
        # self.grid_columnconfigure(1, weight=1)
        # self.grid_rowconfigure(0, weight=1)

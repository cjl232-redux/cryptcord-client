import tkinter as tk

from base64 import b64encode
from tkinter import ttk
from typing import Any

import pyperclip

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import Engine

from app_components.contacts import ContactsPane

class Body(ttk.Frame):
    def __init__(
            self,
            master: tk.Tk,
            engine: Engine,
            signature_key: Ed25519PrivateKey,
            settings: dict[str, Any],
        ):
        super().__init__(master)

        # Dedicate the main part of the body to a notebook.
        self.notebook = ttk.Notebook(self)
        self.notebook.add(
            child=ContactsPane(self, engine, signature_key, settings),
            text='Contacts',
        )
        self.notebook.grid(
            column=0,
            row=0,
            sticky='nsew',
            padx=5,
            pady=5,
            columnspan=2,
        )
        
        # Display the user's public key in Base64 form.
        public_bytes = signature_key.public_key().public_bytes_raw()
        public_bytes_b64 = b64encode(public_bytes).decode()
        label = ttk.Label(self, text=f'Your public key: {public_bytes_b64}')
        label.grid(column=0, row=1, sticky='w', padx=5, pady=5)
        copy_button = ttk.Button(
            master=self,
            text='Copy',
            command=lambda *_: pyperclip.copy(public_bytes_b64),
        )
        copy_button.grid(column=1, row=1, sticky='w', padx=5, pady=5)

        # Configure overall grid properties.
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

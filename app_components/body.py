import sqlite3
from base64 import urlsafe_b64encode
from tkinter import ttk

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app_components.contacts import ContactsPane

class Body(ttk.Frame):
    def __init__(
            self,
            master,
            public_key: Ed25519PublicKey,
            client_db: sqlite3.Connection,
            *args,
            **kwargs,
        ):
        super().__init__(master, *args, **kwargs)
        
        # Display the user's public key in Base64 form.
        public_key = urlsafe_b64encode(public_key.public_bytes_raw()).decode()
        self.label = ttk.Label(self, text=f'Your public key: {public_key}')
        self.label.grid(column=0, row=0, sticky='nw', pady=5)

        # Dedicate the main part of the body to a notebook.
        self.notebook = ttk.Notebook(self)
        self.notebook.add(child=ContactsPane(self, client_db), text='Contacts')
        self.notebook.grid(column=0, row=1, sticky='nsew', pady=5)

        # Configure overall grid properties.
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

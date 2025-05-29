import os
#import sqlite3
import tkinter as tk

from base64 import b64decode
from tkinter import messagebox
from typing import Any

import yaml

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine

from app_components.body import Body
from app_components.dialogs.private_key_dialogs import SignatureKeyDialog
from app_components.dialogs.server_dialogs import ServerDialog
from app_components.server_connections import ServerContext
from database import models

SETTINGS_FILE_PATH = 'settings.yaml'

# Need to pass through the network connection handler too

class Application(tk.Tk):
    def __init__(self):
        # Call the Tk constructor, then withdraw the main window.
        super().__init__()
        self.withdraw()
        
        # Set basic properties.
        self.title('Cryptcord')

        # Load stored settings, creating a file if one doesn't exist.
        if not os.path.exists(SETTINGS_FILE_PATH):
            with open(SETTINGS_FILE_PATH, mode='w'):
                pass
        with open(SETTINGS_FILE_PATH, mode='r') as file:
            settings: dict[str, Any] = yaml.safe_load(file)

        # Retrieve the local database url from settings, or set a default.
        database_url: str = settings.get(
            'database_url',
            'sqlite:///database.db',
        )
        settings['database_url'] = database_url

        try:
            # Attempt to start the engine with the provided url.
            self.engine = create_engine(database_url, echo=True)
        except:
            # If an exception is raised, terminate with a message.
            messagebox.showerror(
                title='Invalid Database Path',
                message=(
                    f'The local database file path specified in '
                    f'{SETTINGS_FILE_PATH} is invalid.'
                ),
            )
            self.destroy()
            return
        # TODO review error handling
        # TODO encryption of database according to private key

        # Ensure the database has the required tables.
        models.Base.metadata.create_all(self.engine)

        # Load the user's signature key via a custom dialog.
        signature_key_dialog = SignatureKeyDialog(self)
        self.wait_window(signature_key_dialog)

        # Halt initialisation and close the application if no key is loaded.
        if signature_key_dialog.result is None:
            self.destroy()
            return
        
        # Otherwise, initialise a key object from the dialog.
        self.signature_key = Ed25519PrivateKey.from_private_bytes(
            data=b64decode(signature_key_dialog.result['signature_key']),
        )

        # Get the server information with a dialog.
        server_dialog = ServerDialog(self, title='Server Connection')
        self.wait_window(server_dialog)

        # Halt initialisation and close the application on a cancel.
        if server_dialog.result is None:
            self.destroy()
            return
        
        # Otherwise, initialise the server context.
        self.server_context = ServerContext(
            host=server_dialog.result['ip_address'],
            port=int(server_dialog.result['port_number']),
            signature_key=self.signature_key,
        )

        # Save any changes to settings.
        with open(SETTINGS_FILE_PATH, 'w') as file:
            yaml.safe_dump(settings, file)

        # Restore the main window and render the body.
        self.deiconify()
        self.body = Body(
            master=self,
            engine=self.engine,
            signature_key=self.signature_key,
        )
        self.body.grid(column=0, row=0, sticky='nsew', padx=5, pady=5)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Test
        # from base64 import b64encode
        # data = {
        #     'command': 'SEND_MESSAGE2',
        #     'recipient_public_key': 'rwaj4ykXFOTzVsGcmxXNGVHsbmZiqne+B1R/KJODNB0=',
        #     'encrypted_message': 'Main app calling Kirby.',
        #     'signature': b64encode(self.signature_key.sign('Main app calling Kirby.'.encode())).decode(),
        # }
        # response = self.server_context.send_request(data)
        # print(response)

if __name__ == '__main__':
    Application().mainloop()
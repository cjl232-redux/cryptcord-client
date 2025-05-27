import os
import sqlite3
import tkinter as tk

from base64 import b64decode
from tkinter import messagebox

import yaml

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import database_functions

from app_components.body import Body
from app_components.dialogs.private_key_dialogs import SignatureKeyDialog
from app_components.dialogs.server_dialogs import ServerDialog
from app_components.server_connections import ServerContext

SETTINGS_FILE_PATH = 'settings.yaml'

class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        # Call the Tk constructor, then withdraw the main window.
        super().__init__(*args, **kwargs)
        self.withdraw()
        
        # Set basic properties.
        self.title('Cryptcord')

        # Load stored settings, creating a file if one doesn't exist.
        if not os.path.exists(SETTINGS_FILE_PATH):
            with open(SETTINGS_FILE_PATH, mode='w'):
                pass
        with open(SETTINGS_FILE_PATH, mode='r') as file:
            settings = yaml.safe_load(file)

        # Retrieve the local database path from settings, or set a default.
        database: str = settings.get('database', 'local_database.db')
        settings['database'] = database

        try:
            # Attempt to connect to the local database.
            self.db_connection = sqlite3.connect(database, autocommit=True)
        except:
            # If an exception is raised, display an appropriate error message.
            messagebox.showerror(
                title='Invalid Database Path',
                message=(
                    f'The local database file path specified in '
                    f'{SETTINGS_FILE_PATH} is invalid.'
                ),
            )
            # Destroy the application and terminate initialisation.
            self.db_connection = None
            self.destroy()
            return
        # TODO review error handling
        # TODO encryption of database according to private key

        # Ensure the database has the required tables.
        database_functions.create_tables(self.db_connection)

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

        # Test
        from base64 import b64encode
        data = {
            'command': 'SEND_MESSAGE',
            'recipient_public_key': 'rwaj4ykXFOTzVsGcmxXNGVHsbmZiqne+B1R/KJODNB0=',
            'encrypted_message': 'Main app calling Kirby.',
            'signature': b64encode(self.signature_key.sign('Main app calling Kirby.'.encode())).decode(),
        }
        response = self.server_context.send_request(data)
        print(response)


        # Save any changes to settings.
        with open(SETTINGS_FILE_PATH, 'w') as file:
            yaml.safe_dump(settings, file)

        # Restore the main window and render the body.
        self.deiconify()
        self.body = Body(
            master=self,
            public_key=self.signature_key.public_key(),
        )
        self.body.grid(column=0, row=0, sticky='nsew', padx=5, pady=5)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def __enter__(self):
        return self
    
    def __exit__(self, *_):
        if self.db_connection is not None:
            self.db_connection.close()

if __name__ == '__main__':
    with Application() as application:
        application.mainloop()
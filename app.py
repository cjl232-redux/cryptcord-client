import os
import sqlite3
import tkinter as tk
import tkinter.messagebox as messagebox
import yaml

from app_components.body import Body
from app_components.dialogs import SignatureKeyDialog
import database_functions

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
        # TODO encryption

        # Ensure the database has the required tables.
        database_functions.create_tables(self.db_connection)

        # Load the user's signature key via a custom dialog.
        signature_key_dialog = SignatureKeyDialog(
            master=self,
            file_path=settings.get('signature_key_path', None),
        )
        self.wait_window(signature_key_dialog)
        self.signature_key = signature_key_dialog.signature_key

        # Halt initialisation and close the application if no key is loaded.
        if self.signature_key is None:
            self.destroy()
            return
        
        # Add the path of the loaded signature key to settings.
        settings['signature_key_path'] = signature_key_dialog.file_path

        # Save any changes to settings.
        with open(SETTINGS_FILE_PATH, 'w') as file:
            yaml.safe_dump(settings, file)

        # Restore the main window and render the body.
        self.deiconify()
        self.body = Body(
            master=self,
            public_key=self.signature_key.public_key(),
            client_db=self.db_connection,
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
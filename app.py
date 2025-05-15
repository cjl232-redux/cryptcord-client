import os
import sqlite3
import tkinter as tk
import yaml

from app_components.body import Body
from app_components.dialogs import SignatureKeyDialog

DB_NAME = 'client_database.db'

class Application(tk.Tk):
    def __init__(self, client_db: sqlite3.Connection, *args, **kwargs):
        # Call the Tk constructor, then withdraw the main window.
        super().__init__(*args, **kwargs)
        self.withdraw()
        
        # Set basic properties.
        self.title('Cryptcord')

        # Load stored settings, creating a file if one doesn't exist.
        if not os.path.exists('settings.yaml'):
            with open('settings.yaml', mode='w'):
                pass
        with open('settings.yaml', mode='r') as file:
            settings = yaml.safe_load(file)

        # Load the user's signature key via a custom dialog.
        signature_key_dialog = SignatureKeyDialog(
            master=self,
            file_path=settings.get('signature_key_path', None),
        )
        self.wait_window(signature_key_dialog)
        self.signature_key = signature_key_dialog.signature_key

        # Halt initialisation and close the window if no key is loaded.
        if self.signature_key is None:
            self.destroy()
            return
        
        # Save the path of the loaded signature key to the settings file.
        settings['signature_key_path'] = signature_key_dialog.file_path
        with open('settings.yaml', 'w') as file:
            yaml.safe_dump(settings, file)

        # Restore the main window and render the body.
        self.deiconify()
        self.body = Body(
            master=self,
            public_key=self.signature_key.public_key(),
            client_db=client_db,
        )
        self.body.grid(column=0, row=0, sticky='nsew', padx=5, pady=5)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

if __name__ == '__main__':
    with sqlite3.connect(DB_NAME) as client_db:
        application = Application(client_db)
        application.mainloop()
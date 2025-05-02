import tkinter.simpledialog
from cryptography.hazmat.primitives.serialization import load_pem_private_key, Encoding, PublicFormat
import os
import tkinter as tk
from tkinter import messagebox, ttk
import tkinter.filedialog
import tkinter.messagebox
import yaml
from components import HeaderBar, Server
from channel import Channel
from dialogs import PasswordEntryDialog, SignatureKeyDialog

# Okay. First step to focus on: a series of startup windows.
# Of particular note, need to verify if a password is required to decrypt.
# This should definitely fall in the Application constructor, though.

# Need to consider the subsequent login (e.g. when already have signature key saved)

# I got the dialog for key retrieval to be satisfactory! Now I need to do the settings side.
# First priority for tomorrow, work allowing, is getting it set up so it tries
# To load the key from settings. If missing, bring up dialog. If error, bring up warning then dialog.
# Only caveat there is the need to handle password input... may need a login dialog

class Application(tk.Tk):
    def __init__(self):
        # Call the Tk constructor, then withdraw the main window:
        super().__init__()
        self.withdraw()

        # Set basic values.
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

        # Restore the main window and render the server view.
        self.deiconify()
        self.label = ttk.Label(self, text=self.signature_key.public_key().public_bytes(encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo))
        self.label.grid(column=0, row=0)
        
application = Application()
application.mainloop()

# Require signature key to retrieve messages
# Require private key to decrypt them
# Hmm... when entering, pick a username. Sign the username with signature key.
# Have that create a user account. Then any time they try to sign in, verify it.
# Map public keys to usernames in the database
# I think the next step is to get the database worked out. Then I can connect to a test one.
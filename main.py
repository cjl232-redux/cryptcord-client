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
        super().__init__()
        self.withdraw()
        # Load stored settings, creating a file if one doesn't exist:
        if not os.path.exists('settings.yaml'):
            with open('settings.yaml', mode='w'):
                pass
        with open('settings.yaml', mode='r') as file:
            settings = yaml.safe_load(file)
        self.title('Cryptcord')
        self.signature_key = None
        signature_key_dialog = SignatureKeyDialog(
            master=self,
            file_path=settings.get('signature_key_path', None),
        )
        self.wait_window(signature_key_dialog)
        if signature_key_dialog.signature_key:
            self.signature_key = signature_key_dialog.signature_key
            settings['signature_key_path'] = signature_key_dialog.file_path
            with open('settings.yaml', 'w') as file:
                yaml.safe_dump(settings, file)
            self.deiconify()
            self.label = ttk.Label(self, text=self.signature_key.public_key().public_bytes(encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo))
            self.label.grid(column=0, row=0)
        else:
            self.destroy()
        return


        # Terminate early if no signature key is provided:
        if signature_key_dialog.signature_key is None:
            self.destroy()
            return
        
        self.signature_key = dialog.signature_key
        
        print(dialog.signature_key)
        exit()
        self.signature_key = None
        if 'signature_key_path' in settings:
            try:
                with open(settings.get('signature_key_path'), 'rb') as file:
                    key_data = file.read()
                self.signature_key = load_pem_private_key(key_data, None)
            except TypeError:
                # Password dialog
                print('password')
                exit()
            except:
                messagebox.showwarning(
                    title='Signature Key Load Error',
                    message='Your signature key could not be loaded.',
                )
        if self.signature_key is None:
            dialog = SignatureKeyDialog(self)
            self.wait_window(dialog)
            if dialog.signature_key:
                self.signature_key = dialog.signature_key
                settings['signature_key_path'] = dialog.file_path
            else:
                self.destroy()
                return
        with open('settings.yaml', 'w') as file:
            yaml.safe_dump(settings, file)
        self.deiconify()
        exit()
            
        dialog = SignatureKeyDialog(self)
        self.wait_window(dialog)
        print(dialog.signature_key)
        self.deiconify()
        dialog = SignatureKeyDialog(self)
        self.wait_window(dialog)
        exit()
        self.signature_key = None
        with open('settings.yaml', mode='r') as file:
            settings = yaml.safe_load(file)
        while not 'signature_key' in settings or not os.path.exists(settings.get('signature_key')):
            print(settings)
            msgbox = tkinter.messagebox.askokcancel(
                title='Signature Key Required',
                message=' '.join([
                    'A valid private key for signing all outbound traffic is',
                    'required. The key should be serialized with PEM',
                    'encoding, and the corresponding public key should be',
                    'known to anyone you intend to exchange messages with.',
                    'If you have a private key saved to disk, select OK and',
                    'then choose the file. Otherwise, select Cancel, generate',
                    'a valid key, then re-launch this application.',
                ]),
            )
            if not msgbox:
                exit()
            file_path = tkinter.filedialog.askopenfilename()
            with open(file_path, mode='rb') as file:
                key_data = file.read()
                try:
                    self.signature_key = load_pem_private_key(
                        data=key_data,
                    )
                    settings['signature_key'] = file_path
                except TypeError:
                    while not 'signature_key' in settings or not os.path.exists(settings.get('signature_key')):
                        password = tkinter.simpledialog.askstring(
                            title='Enter Password',
                            prompt=' '.join([
                                'Please enter the password used to encrypt',
                                'this key.',
                            ]),
                            show='*',
                        )
                        if not password:
                            exit()
                        try:
                            self.signature_key = load_pem_private_key(
                                data=key_data,
                                password=password.encode(),
                            )
                            settings['signature_key'] = file_path
                        except ValueError:
                            msgbox = tkinter.messagebox.askretrycancel(
                                title='Incorrect Password',
                                message=' '.join([
                                    'The password provided is incorrect.',
                                    'Select Retry to try again, or Cancel to',
                                    'return to the key selection step.',
                                ]),
                                icon=tkinter.messagebox.ERROR,
                            )
                            if not msgbox:
                                break
        # If the setting already existed, load the key:
        while self.signature_key is None:
            with open(settings.get('signature_key'), mode='rb') as file:
                data = file.read()
            try:
                self.signature_key = load_pem_private_key(data)
            except TypeError:
                password = tkinter.simpledialog.askstring(
                    title='Enter Password',
                    prompt=' '.join([
                        'Please enter the password used to encrypt your',
                        'signature key.',
                    ]),
                    show='*',
                )
                if not isinstance(password, str):
                    exit()
                elif password is None:
                    password = ''
                try:
                    self.signature_key = load_pem_private_key(
                        data=data,
                        password=password.encode(),
                    )
                except:
                    tkinter.messagebox.showerror(
                        title='Incorrect Password',
                        message='The password provided is incorrect.',
                    )
        with open('settings.yaml', 'w') as file:
            yaml.safe_dump(settings, file)
        exit()
        self.title('Cryptcord')
        # Settings:
        self.header_bar = HeaderBar()
        self.header_bar.grid(column=0, row=0)
        self.server_pane = Server()
        self.server_pane.load_channels(['abc', 'cba'])
        self.server_pane.grid(column=0, row=1)
        
application = Application()
application.mainloop()

# Require signature key to retrieve messages
# Require private key to decrypt them
# Hmm... when entering, pick a username. Sign the username with signature key.
# Have that create a user account. Then any time they try to sign in, verify it.
# Map public keys to usernames in the database
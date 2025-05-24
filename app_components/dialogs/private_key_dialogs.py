import tkinter as tk

from base64 import b64decode, b64encode
from tkinter import filedialog, messagebox, ttk

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from app_components.dialogs.base_dialogs import DescriptionData, Dialog
from app_components.dialogs.fields import ButtonData, Field, PasswordField

class KeyPasswordDialog(Dialog):
    def __init__(self, master, key_data: bytes, *args, **kwargs):
        super().__init__(
            master=master,
            title='Encrypted Key File',
            description_data=self._description_data,
            fields={
                'password': PasswordField(),
            },
            validators=[
                self._validate_password,
            ],
            *args,
            **kwargs,
        )
        self.key_data = key_data

    _description_text = 'Please enter the password for the selected file.'
    _description_data = DescriptionData(_description_text, 480)

    def _validate_password(self, values: dict[str, str]) -> str | None:
        password = values.get('password', '').encode()
        if not password:
            return 'A value is required for the password field.'
        try:
            serialization.load_pem_private_key(self.key_data, password)
        except ValueError:
            self.stringvars['password'].set('')
            return 'The password provided is incorrect.'

class PrivateKeyField(Field):
    def __init__(
            self,
            name: str = 'Private Key',
            key_type: type = None,
            *args,
            **kwargs,
        ):
        super().__init__(
            name=name,
            button_data=self._button_data,
            hide_input=True,
            *args,
            **kwargs,
        )
        self.key_type = key_type

    def _browse(self, entry: ttk.Entry, variable: tk.StringVar):
        path = filedialog.askopenfilename()
        # Exit the function if no path is provided.
        if not path:
            return
        # Otherwise, attempt to load the key.
        try:
            with open(path, 'rb') as file:
                data = file.read()
            key = serialization.load_pem_private_key(data, None)
            if self.key_type and not isinstance(key, self.key_type):
                messagebox.showerror(
                    title='Invalid Key Type',
                    message=(
                        f'The selected file represents a {type(key).__name__} '
                        f'object, but a {self.key_type.__name__} object is '
                        f'required.'
                    ),
                )
            else:
                variable.set(b64encode(key.private_bytes_raw()).decode())
                entry.focus()
        except ValueError:
            messagebox.showerror(
                title='Invalid File Format',
                message=(
                    'The selected file does not contain a PEM-encoded '
                    'serialisation of a private key.'
                )
            )
        except TypeError:
            password_dialog = KeyPasswordDialog(entry.winfo_toplevel(), data)
            entry.winfo_toplevel().wait_window(password_dialog)
            if password_dialog.result:
                key = serialization.load_pem_private_key(
                    data=data,
                    password=password_dialog.result.get('password').encode(),
                )
                variable.set(b64encode(key.private_bytes_raw()).decode())
            entry.winfo_toplevel().grab_set()

    _button_data = ButtonData('Browse...', _browse)

class SignatureKeyDialog(Dialog):
    def __init__(self, master, title: str = 'Signature Key', *args, **kwargs):
        super().__init__(
            master=master,
            title=title,
            description_data=self._description_data,
            fields={
                'signature_key': PrivateKeyField(
                    name='Signature Key',
                    key_type=ed25519.Ed25519PrivateKey,
                ),
            },
            validators=[
                self._validate_key,
            ],
            *args,
            **kwargs,
        )
        
    _description_text = (
        'Using this program requires an Ed25519 private signature key. This '
        'will allow your contacts to confirm the authenticity of messages '
        'and shared encryption key exchange requests. This can either be '
        'entered directly as a Base64 representation of a 32-byte key or '
        'loaded from a PEM-encoded serialisation. If the serialisation is '
        'encrypted, you will be asked for the password.'
    )
    _description_data = DescriptionData(_description_text, 480)
    
    def _validate_key(self, values: dict[str, str]) -> str | None:
        key = values.get('signature_key', '')
        if not key:
            return 'A value is required for the key field.'
        try:
            raw_bytes = b64decode(key, validate=True)
            if len(raw_bytes) != 32:
                raise ValueError()
        except:
            return (
                'The value provided for the key field is not a valid Base64 '
                'representation of a 32-byte key.'
            )
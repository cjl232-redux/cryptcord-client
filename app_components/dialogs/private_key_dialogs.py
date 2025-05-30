import tkinter as tk

from base64 import b64decode, b64encode
from tkinter import filedialog, messagebox, ttk

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app_components.dialogs.base import Dialog
from app_components.dialogs.fields import ButtonData, Field, PasswordField

class KeyPasswordDialog(Dialog):
    def __init__(
            self,
            master: tk.Widget | ttk.Widget | tk.Tk | tk.Toplevel,
            key_data: bytes,
            title: str = 'Encrypted Key File',
        ):
        super().__init__(
            master=master,
            title=title,
            description_kwargs=self._description_kwargs,
            fields={
                'password': PasswordField(),
            },
            validators=[
                self._validate_password,
            ],
        )
        self.key_data = key_data

    _description_text = 'Please enter the password for the selected file.'
    _description_kwargs: dict[str, int | str] = {
        'text': _description_text,
        'wraplength': 480,
    }

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
        ):
        super().__init__(
            name=name,
            button_data=ButtonData('Browse...', self._browse),
        )

    @staticmethod
    def _browse(field: Field, entry: ttk.Entry, variable: tk.StringVar):
        # Open and read a file, terminating early if one isn't chosen.
        file = filedialog.askopenfile('rb')
        if file is not None:
            try:
                data = file.read()
            finally:
                file.close()
        else:
            return
        # Load bytes from the chosen file and attempt to handle them.
        try:
            key = serialization.load_pem_private_key(data, None)
            if isinstance(key, Ed25519PrivateKey):
                variable.set(b64encode(key.private_bytes_raw()).decode())
                entry.focus()
            else:
                messagebox.showerror(
                    title='Invalid Key Type',
                    message=(
                        f'The selected file represents a {type(key).__name__} '
                        f'object, but an Ed25519PublicKey object is required.'
                    ),
            )
        except ValueError:
            messagebox.showerror(
                title='Invalid File Format',
                message=(
                    'The selected file does not contain a PEM-encoded '
                    'serialisation of a public key.'
                )
            )
        except TypeError:
            password_dialog = KeyPasswordDialog(entry.winfo_toplevel(), data)
            entry.winfo_toplevel().wait_window(password_dialog)
            if password_dialog.result:
                key = serialization.load_pem_private_key(
                    data=data,
                    password=password_dialog.result['password'].encode(),
                )
                if isinstance(key, Ed25519PrivateKey):
                    variable.set(b64encode(key.private_bytes_raw()).decode())
                    entry.focus()
                else:
                    messagebox.showerror(
                        title='Invalid Key Type',
                        message=(
                            f'The selected file represents a '
                            f'{type(key).__name__} object, but an '
                            f'Ed25519PublicKey object is required.'
                        ),
                    )
            entry.winfo_toplevel().grab_set()



class SignatureKeyDialog(Dialog):
    def __init__(
            self,
            master: tk.Widget | ttk.Widget | tk.Tk | tk.Toplevel,
            title: str = 'Signature Key',
        ):
        super().__init__(
            master=master,
            title=title,
            description_kwargs=self._description_kwargs,
            fields={'signature_key': PrivateKeyField(name='Signature Key')},
            validators=[self._validate_key],
        )
        
    _description_text = (
        'Using this program requires an Ed25519 private signature key. This '
        'will allow your contacts to confirm the authenticity of messages '
        'and shared encryption key exchange requests. This can either be '
        'entered directly as a Base64 representation of a 32-byte key or '
        'loaded from a PEM-encoded serialisation. If the serialisation is '
        'encrypted, you will be asked for the password.'
    )
    _description_kwargs: dict[str, int | str] = {
        'text': _description_text,
        'wraplength': 480,
    }
    
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
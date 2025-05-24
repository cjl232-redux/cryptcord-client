import tkinter as tk

from base64 import b64decode, b64encode
from sqlite3 import connect, Connection
from tkinter import filedialog, messagebox, ttk

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from app_components.dialogs import DescriptionData, Dialog
from app_components.fields import ButtonData, Field, PasswordField
from database_functions import contact_key_exists, contact_name_exists

class KeyPasswordDialog(Dialog):
    def __init__(self, master, key_data: bytes, *args, **kwargs):
        super().__init__(
            master=master,
            title='Encrypted Key File',
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

    def _validate_password(self, values: dict[str, str]) -> str | None:
        password = values.get('password', '').encode()
        if not password:
            return 'A value is required for the password field.'
        try:
            serialization.load_pem_private_key(self.key_data, password)
        except ValueError:
            return 'The password provided is incorrect.'


class PublicKeyField(Field):
    def __init__(
            self,
            name: str = 'Public Key',
            key_type: type = None,
            *args,
            **kwargs,
        ):
        super().__init__(
            name=name,
            button_data=self._button_data,
            *args,
            **kwargs,
        )
        self.key_type = key_type

    def _browse(self, _: ttk.Entry, variable: tk.StringVar):
        path = filedialog.askopenfilename()
        # Exit the function if no path is provided.
        if not path:
            return
        # Otherwise, attempt to load the key.
        try:
            with open(path, 'rb') as file:
                data = file.read()
            key = serialization.load_pem_public_key(data)
            if self.key_type and not isinstance(key, self.key_type):
                raise TypeError()
            variable.set(b64encode(key.public_bytes_raw()).decode())
        except ValueError:
            messagebox.showerror(
                title='Invalid File Format',
                message=(
                    'The selected file does not contain a PEM-encoded '
                    'serialisation.'
                )
            )
        except TypeError:
            messagebox.showerror(
                title='Invalid Key Type',
                message=(
                    f'The selected file represents a {type(key).__name__} '
                    f'object, but a {self.key_type.__name__} object is '
                    f'required.'
                ),
            )

    _button_data = ButtonData('Browse...', _browse)
    

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
                    'serialisation.'
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


class AddContactDialog(Dialog):
    def __init__(
            self,
            master,
            db_connection: Connection,
            title: str = 'Add Contact',
            *args,
            **kwargs,
        ):
        super().__init__(
            master=master,
            title=title,
            description_data=self._description_data,
            fields={
                'name': Field(name='Name'),
                'public_key': PublicKeyField(ed25519.Ed25519PublicKey),
            },
            validators=[
                self._validate_name,
                self._validate_key,
            ],
            *args,
            **kwargs,
        )
        self.db_connection = db_connection
        
    _description_text = (
        'Specify a unique name and a Base64 representation of a 32-byte '
        'Ed25519 public key for this contact. The public key can be loaded '
        'from a PEM-encoded serialisation.'
    )
    _description_data = DescriptionData(_description_text, 480)

    def _validate_name(self, values: dict[str, str]) -> str | None:
        name = values.get('name', '')
        if not name:
            return 'A value is required for the name field.'
        elif contact_name_exists(self.db_connection, name):
            return 'The value provided for the name field is already in use.'
    
    def _validate_key(self, values: dict[str, str]) -> str | None:
        key = values.get('public_key', '')
        if not key:
            return 'A value is required for the key field.'
        elif contact_key_exists(self.db_connection, key):
            return 'The value provided for the key field is already in use.'
        try:
            raw_bytes = b64decode(key, validate=True)
            if len(raw_bytes) != 32:
                raise ValueError()
        except:
            return (
                'The value provided for the key field is not a valid Base64 '
                'representation of a 32-byte key.'
            )


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
        

if __name__ == '__main__':
    app = tk.Tk()
    with connect('client_database.db') as connection:
        dialog = SignatureKeyDialog(app)
        app.wait_window(dialog)
        print(dialog.result)
import tkinter as tk

from base64 import b64decode, b64encode
from sqlite3 import Connection
from tkinter import filedialog, messagebox, ttk

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey

from app_components.dialogs.base_dialogs import DescriptionData, Dialog
from app_components.dialogs.fields import ButtonData, Field
from database_functions import contact_key_exists, contact_name_exists

type AcceptableKeyType = type[Ed25519PublicKey] | type[X25519PublicKey]

class PublicKeyField(Field):
    def __init__(
            self,
            name: str = 'Public Key',
            key_type: AcceptableKeyType = Ed25519PublicKey,
        ):
        super().__init__(
            name=name,
            button_data=self._button_data,
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
            if not isinstance(key, self.key_type):
                raise TypeError()
            variable.set(b64encode(key.public_bytes_raw()).decode())
        except ValueError:
            messagebox.showerror(
                title='Invalid File Format',
                message=(
                    'The selected file does not contain a PEM-encoded '
                    'serialisation of a public key.'
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


class AddContactDialog(Dialog):
    def __init__(
            self,
            master: tk.Widget | ttk.Widget,
            used_names: set[str],
            used_public_keys: set[str],
            title: str = 'Add Contact',
        ):
        super().__init__(
            master=master,
            title=title,
            description_data=self._description_data,
            fields={
                'name': Field(name='Name'),
                'public_key': PublicKeyField(
                    key_type=Ed25519PublicKey,
                ),
            },
            validators=[
                self._validate_name,
                self._validate_key,
            ],
        )
        self.used_names = used_names
        self.used_public_keys = used_public_keys
        
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
        elif name in self.used_names:
            return 'The value provided for the name field is already in use.'
    
    def _validate_key(self, values: dict[str, str]) -> str | None:
        key = values.get('public_key', '')
        if not key:
            return 'A value is required for the key field.'
        elif key in self.used_public_keys:
            return 'The value provided for the key field is already in use.'
        try:
            if len(b64decode(key, validate=True)) != 32:
                raise ValueError()
        except:
            return (
                'The value provided for the public key field is not a valid '
                'Base64 representation of a 32-byte key.'
            )
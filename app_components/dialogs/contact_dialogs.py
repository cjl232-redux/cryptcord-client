import binascii
import tkinter as tk

from base64 import urlsafe_b64decode, urlsafe_b64encode
from tkinter import filedialog, messagebox
from typing import Annotated

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from pydantic import BaseModel, BeforeValidator, Field

from app_components.dialogs.base import BaseDialog, FieldButtonData

def _b64_to_public_key(value: str) -> Ed25519PublicKey:
    try:
        raw_bytes = urlsafe_b64decode(value)
        if len(raw_bytes) != 32:
            raise ValueError('Value must have an unencoded length of 32 bytes')
        return Ed25519PublicKey.from_public_bytes(raw_bytes)
    except binascii.Error:
        raise ValueError('Value is not valid Base64')

def _browse_public_key(_, var: tk.StringVar):
    file = filedialog.askopenfile(mode='rb')
    if file is not None:
        data: bytes = file.read()
        try:
            key = load_pem_public_key(data)
            if isinstance(key, Ed25519PublicKey):
                var.set(urlsafe_b64encode(key.public_bytes_raw()).decode())
            else:
                raise ValueError()
        except ValueError:
            messagebox.showerror(
                title='Error',
                message=(
                    'The selected file does not contain a valid PEM-encoding '
                    'of a public Ed25519 key.'
                ),
            )
        finally:
            file.close()

class _BaseContactModel(BaseModel):
    name: Annotated[
        str,
        Field(title='Name'),
    ]
    class Config:
        arbitrary_types_allowed = True

class _AddContactDialogModel(_BaseContactModel):
    public_key: Annotated[
        Ed25519PublicKey,
        Field(title='Public Key'),
        BeforeValidator(_b64_to_public_key),
        FieldButtonData('Browse...', _browse_public_key),
    ]

class AddContactDialog(BaseDialog[_AddContactDialogModel]):
    TITLE = 'Add Contact'
    DESCRIPTION = (
        'Specify a unique name and a Base64 representation of a 32-byte '
        'Ed25519 public key for this contact. The public key can be loaded '
        'from a PEM-encoded serialisation.'
    )
    VALIDATION_MODEL = _AddContactDialogModel

class ModifyContactDialog(BaseDialog[_BaseContactModel]):
    TITLE = 'Add Contact'
    DESCRIPTION = (
        'Specify a unique name and a Base64 representation of a 32-byte '
        'Ed25519 public key for this contact. The public key can be loaded '
        'from a PEM-encoded serialisation.'
    )
    VALIDATION_MODEL = _BaseContactModel








# import tkinter as tk
# # FIX REMAINING ERRORS
# from base64 import urlsafe_b64decode, urlsafe_b64encode
# from tkinter import filedialog, messagebox, ttk

# from cryptography.hazmat.primitives import serialization
# from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# from app_components.dialogs._base import Dialog
# from app_components.dialogs.fields import ButtonData, Field
# from database.schemas.input import ContactInputSchema

# class PublicKeyField(Field):
#     def __init__(
#             self,
#             name: str = 'Public Key',
#         ):
#         super().__init__(
#             name=name,
#             button_data=ButtonData('Browse...', self._browse),
#         )

#     @staticmethod
#     def _browse(_: Field, entry: ttk.Entry, variable: tk.StringVar):
#         path = filedialog.askopenfilename()
#         # Exit the function if no path is provided.
#         if not path:
#             return
#         # Otherwise, attempt to load the key.
#         try:
#             with open(path, 'rb') as file:
#                 data = file.read()
#             key = serialization.load_pem_public_key(data)
#             if isinstance(key, Ed25519PublicKey):
#                 variable.set(urlsafe_b64encode(key.public_bytes_raw()).decode())
#                 entry.focus()
#             else:
#                 messagebox.showerror(
#                     title='Invalid Key Type',
#                     message=(
#                         f'The selected file represents a {type(key).__name__} '
#                         f'object, but an Ed25519PublicKey object is required.'
#                     ),
#             )
#         except ValueError:
#             messagebox.showerror(
#                 title='Invalid File Format',
#                 message=(
#                     'The selected file does not contain a PEM-encoded '
#                     'serialisation of a public key.'
#                 )
#             )


# class AddContactDialog(Dialog):
#     def __init__(
#             self,
#             master: tk.Widget | ttk.Widget | tk.Tk | tk.Toplevel,
#             used_names: set[str],
#             used_public_keys: set[Ed25519PublicKey],
#             title: str = 'Add Contact',
#         ):
#         super().__init__(
#             master=master,
#             title=title,
#             input_schema=ContactInputSchema,
#             description_kwargs=self._description_kwargs,
#             fields={
#                 'name': Field(name='Name'),
#                 'public_key': PublicKeyField(name='Public Key'),
#             },
#             validators=[
#                 self._validate_name,
#                 self._validate_key,
#             ],
#         )
#         self.used_names = used_names
#         self.used_public_keys = used_public_keys
        
#     _description_text = (
#         'Specify a unique name and a Base64 representation of a 32-byte '
#         'Ed25519 public key for this contact. The public key can be loaded '
#         'from a PEM-encoded serialisation.'
#     )
#     _description_kwargs: dict[str, int | str] = {
#         'text': _description_text,
#         'wraplength': 480,
#     }

#     def _validate_name(self, values: dict[str, str]) -> str | None:
#         name = values.get('name', '')
#         if not name:
#             return 'A value is required for the name field.'
#         elif name in self.used_names:
#             return 'The value provided for the name field is already in use.'
    
#     def _validate_key(self, values: dict[str, str]) -> str | None:
#         key = values.get('public_key', '')
#         if not key:
#             return 'A value is required for the key field.'
#         elif key in self.used_public_keys:
#             return 'The value provided for the key field is already in use.'
#         try:
#             if len(urlsafe_b64decode(key)) != 32:
#                 raise ValueError()
#         except:
#             return (
#                 'The value provided for the public key field is not a valid '
#                 'Base64 representation of a 32-byte key.'
#             )
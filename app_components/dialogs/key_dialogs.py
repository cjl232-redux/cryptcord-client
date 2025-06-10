import binascii
import tkinter as tk

from base64 import urlsafe_b64decode, urlsafe_b64encode
from tkinter import filedialog, messagebox
from typing import Annotated

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)
from pydantic import AfterValidator, BaseModel, Field

from app_components.dialogs.base import (
    BaseDialog,
    FieldButtonData,
    FieldPropertiesData,
)

def _validate_key(value: str) -> str:
    try:
        raw_bytes = urlsafe_b64decode(value)
        if len(raw_bytes) != 32:
            raise ValueError('Value must have an unencoded length of 32 bytes')
        return urlsafe_b64encode(raw_bytes).decode()
    except binascii.Error:
        raise ValueError('Value is not valid Base64')

def _toggle_password_visibility(entry: tk.Entry, _):
    entry.config(show='●' if entry.cget('show') == '' else '')
    entry.focus()

class _PrivateKeyPasswordModel(BaseModel):
    password: Annotated[
        str,
        Field(title='Password'),
        FieldButtonData('Show/Hide', _toggle_password_visibility),
        FieldPropertiesData(hidden=True),
    ]

class _PrivateKeyPasswordDialog(BaseDialog[_PrivateKeyPasswordModel]):
    TITLE = 'Encrypted Key Password'
    DESCRIPTION = 'Enter the password for the selected file.'
    VALIDATION_MODEL = _PrivateKeyPasswordModel

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

def _browse_private_key(entry: tk.Entry, var: tk.StringVar):
    file = filedialog.askopenfile(mode='rb')
    if file is not None:
        data: bytes = file.read()
        try:
            try:
                key = load_pem_private_key(data, None)
            except TypeError:
                while True:
                    dialog = _PrivateKeyPasswordDialog(entry)
                    dialog.wait_window()
                    entry.winfo_toplevel().grab_set()
                    entry.focus()
                    if dialog.result is not None:
                        password = dialog.result.password.encode()
                        try:
                            key = load_pem_private_key(data, password)
                            break
                        except ValueError:
                            response = messagebox.askretrycancel(
                                title='Incorrect Password',
                                message='The provided password is incorrect.',
                                icon='error',
                            )
                            if not response:
                                return
                    else:
                        return                
            if isinstance(key, Ed25519PrivateKey):
                var.set(urlsafe_b64encode(key.private_bytes_raw()).decode())
                entry.icursor(tk.END)
                entry.xview_moveto(1.0)
            else:
                raise ValueError()
        except ValueError:
            messagebox.showerror(
                title='Error',
                message=(
                    'The selected file does not contain a valid PEM-encoding '
                    'of a private Ed25519 key.'
                ),
            )
        finally:
            file.close()

class _ContactDialogModel(BaseModel):
    name: Annotated[
        str,
        Field(title='Name'),
    ]
    public_key: Annotated[
        str,
        Field(title='Public Key'),
        AfterValidator(_validate_key),
        FieldButtonData('Browse...', _browse_public_key),
    ]

class _SignatureKeyDialogModel(BaseModel):
    signature_key: Annotated[
        str,
        Field(title='Signature Key'),
        AfterValidator(_validate_key),
        FieldButtonData('Browse...', _browse_private_key),
    ]

class AddContactDialog(BaseDialog[_ContactDialogModel]):
    TITLE = 'Add Contact'
    DESCRIPTION = (
        'Specify a unique name and a Base64 representation of a 32-byte '
        'Ed25519 public key for this contact. The public key can be loaded '
        'from a PEM-encoded serialisation.'
    )
    VALIDATION_MODEL = _ContactDialogModel

class SignatureKeyDialog(BaseDialog[_SignatureKeyDialogModel]):
    TITLE = 'Signature Key'
    DESCRIPTION = (
        'Using this program requires an Ed25519 private signature key. This '
        'will be used to sign transmitted messages and exchange keys so that '
        'recipents can verify their authenticity. This can either be entered '
        'directly as a Base64 representation of a 32-byte key or loaded from '
        'a PEM-encoded serialisation. If an encrypted serialisation is '
        'chosen, you will be asked for the password.'
    )
    VALIDATION_MODEL = _SignatureKeyDialogModel
import os
from dataclasses import dataclass
from sqlite3 import Connection
from typing import Callable

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import tkinter as tk
from tkinter import messagebox, ttk
from app_components import fields

#TODO URGENT: derive KeyLoadField from FileSelectField
# Add the validation and render it as Base64
# ALSO: password dialog for importing key from file
# Consider how to deal with this with a saved path. Most likely: immediately activate extra dialog.

@dataclass
class DescriptionData:
    text: str
    wrap_length: int | None = None

type Validator = Callable[[dict[str, str]], str | None]

class Dialog(tk.Toplevel):
    def __init__(
            self,
            master,
            title: str,
            description_data: DescriptionData = None,
            fields: dict[str, fields.Field] = None,
            validators: list[Validator] = None,
            x_padding: int = 6,
            y_padding: int = 2,
            *args,
            **kwargs,
        ):
        # Call the base constructor.
        super().__init__(master, *args, **kwargs)

        # Fill in default lists and dicts.
        if fields is None:
            fields = {}
        if validators is None:
            validators = []

        # Grab all incoming events and set window properties.
        self.grab_set()
        self.title(title)
        self.protocol('WM_DELETE_WINDOW', self.cancel)

        # Track the current row.
        row = 0
        
        # If provided, place the description text.
        if description_data is not None:
            label = ttk.Label(
                master=self,
                text=description_data.text,
                wraplength=description_data.wrap_length,
            )
            label.grid(
                column=0,
                row=row,
                columnspan=3,
                sticky='new',
                padx=x_padding,
                pady=(y_padding, y_padding // 2),
            )
            row += 1
        
        # Create and place widgets for each field.
        first_field = True
        self.stringvars: dict[str, tk.StringVar] = {}
        for key, field in fields.items():
            label, entry, button, var = field.load_widgets(self)
            entry.bind('<Return>', lambda _: self.submit())
            if first_field:
                entry.focus()
                first_field = False
            label.grid(
                column=0,
                row=row,
                sticky='w',
                padx=(
                    x_padding,
                    x_padding // 2,
                ),
                pady=(
                    y_padding if row == 0 else y_padding // 2,
                    y_padding // 2,
                ),
            )
            entry.grid(
                column=1,
                row=row,
                sticky='ew',
                padx=(
                    x_padding // 2,
                    x_padding // 2,
                ),
                pady=(
                    y_padding if row == 0 else y_padding // 2,
                    y_padding // 2,
                ),
            )
            if button is not None:
                button.grid(
                    column=2,
                    row=row,
                    sticky='ew',
                    padx=(
                        x_padding // 2,
                        x_padding,
                    ),
                    pady=(
                        y_padding if row == 0 else y_padding // 2,
                        y_padding // 2,
                    ),
                )
            self.stringvars[key] = var
            row += 1

        # Add in command buttons.
        submit_button = ttk.Button(self, text='Submit', command=self.submit)
        submit_button.grid(
            column=1,
            row=row,
            sticky='e',
            padx=(0, x_padding // 2),
            pady=(y_padding if row == 0 else y_padding // 2, y_padding),
        )
        submit_button.bind('<Return>', lambda _: self.submit())
        cancel_button = ttk.Button(self, text='Cancel', command=self.cancel)
        cancel_button.grid(
            column=2,
            row=row,
            sticky='ew',
            padx=(x_padding // 2, x_padding),
            pady=(y_padding if row == 0 else y_padding // 2, y_padding),
        )
        cancel_button.bind('<Return>', lambda _: self.cancel())

        # Configure the grid.
        self.columnconfigure(1, weight=1)

        # Store provided validators.
        self.validators = validators
        if self.validators is None:
            self.validators = []

    def submit(self, *_) -> bool:
        result = {x: y.get() for x, y in self.stringvars.items()}
        errors: list[str] = []
        for validator in self.validators:
            message = validator(result)
            if message:
                errors.append(f'• {message}')
        if errors:
            messagebox.showerror(
                title='Validation Error',
                message=f'The following errors occured:\n{'\n'.join(errors)}',
            )
            self.result = None
        else:
            self.result = result
            self.destroy()

    def cancel(self, *_):
        self.result = None
        self.destroy()

class AddContactDialog(Dialog):
    def __init__(self, master, db_connection: Connection, *args, **kwargs):
        super().__init__(
            master=master,
            title='Add Contact',
            description_data=self._description_data,
            fields=self._fields,
            validators=[
                AddContactDialog._validate_name,
                AddContactDialog._validate_public_key,
            ]
            *args,
            **kwargs,
        )
        self.db_connection = db_connection

    _description_text = (
        'Specify a unique name and a Base64 representation of a 32-byte '
        'Ed25519 public key for this contact. The public key can be loaded '
        'from a PEM-encoded serialisation.'
    )
    _description_data = DescriptionData(
        text=_description_text,
        wrap_length=480,
    )
    _fields = {
        'name': fields.Field(name='Field'),
        'public_key': fields.FilePathField(name='Public Key'),
    }

    def _validate_name(values: dict[str, str]) -> str | None:
        pass

    def _validate_public_key(values: dict[str, str]) -> str | None:
        pass

# class SignatureKeyDialog(Dialog):
    # def __init__(self, master, file_path: str = None, *args, **kwargs):
    #     super().__init__(
    #         master=master,
    #         title='Signature Key',
    #         description_data=self._description_data,
    #         fields = self._fields,
    #         validators=[SignatureKeyDialog._validate],
    #         *args,
    #         **kwargs,
    #     )
    #     if file_path:
    #         self.stringvars['path'].set(file_path)

    # def submit(self, *_):
    #     super().submit(*_)
    #     if self.result:
    #         with open(self.result['path'], 'rb') as file:
    #             data = file.read()
    #         if self.result['password']:
    #             password: bytes = self.result['password'].encode()
    #         else:
    #             password = None
    #         self.result['private_key'] = load_pem_private_key(data, password)
    #     else:
    #         self.stringvars['password'].set('')
        

    # _description_text = (
    #     'Using this program requires an Ed25519 private signature key. This '
    #     'will allow your contacts to confirm the authenticity of messages '
    #     'and shared encryption key exchange requests. If you already have '
    #     'one, please select a file containing a PEM-encoded serialisation '
    #     'of the private key, and provide a password if the file is encrypted. '
    #     'Otherwise, please generate and serialise a key pair.'
    # )
    # _description_data = DescriptionData(_description_text, 480)
    # _fields = {
    #     'path': fields.FilePathField(
    #         name='Private Key Path',
    #     ),
    #     'password': fields.PasswordField(),
    # }

    # def _validate(values: dict[str, str]) -> str | None:
    #     path = values.get('path', '')
    #     if not path:
    #         return 'A file path must be provided.'
    #     elif not os.path.exists(path):
    #         return 'The chosen file does not exist.'
    #     try:
    #         with open(path, 'rb') as file:
    #             data = file.read()
    #         password = None
    #         try:
    #             key = load_pem_private_key(data, password)
    #         except ValueError:
    #             return (
    #                 'The chosen file\'s content is invalid for a '
    #                 'PEM-encoded private key.'
    #             )
    #         except TypeError:
    #             password = values.get('password', '').encode()
    #             if not password:
    #                 return 'The chosen file requires a password.'
    #             key = load_pem_private_key(data, password)
    #         if not isinstance(key, Ed25519PrivateKey):
    #             return (
    #                 'The chosen file\'s content represents a non-Ed25519 '
    #                 'private key.'
    #             )
    #     except OSError:
    #         return 'The chosen file could not be opened.'
    #     except ValueError:
    #         return 'The password provided is incorrect for the chosen file.'
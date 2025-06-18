from tkinter import messagebox, ttk

import httpx

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError

from app_components.dialogs.contact_dialogs import AddContactDialog
from app_components.messages import MessageWindow
from app_components.scrollable_frames import ScrollableFrame
from database.operations.contacts import (
    add_contact,
    get_contacts,
    remove_contact,
)
from database.schemas.input import ContactInputSchema
from database.schemas.output import ContactOutputSchema
from settings import settings

class _ExistingContactsFrame(ScrollableFrame):
    def __init__(
            self,
            master: ttk.Frame,
            engine: Engine,
            http_client: httpx.Client,
            signature_key: Ed25519PrivateKey,
        ):
        super().__init__(master)
        self.engine = engine
        self.signature_key = signature_key
        self.http_client = http_client
        self.message_windows: dict[int, MessageWindow] = {}
        self.interior.columnconfigure(0, weight=1)

    def reload(self):
        for widget in self.interior.winfo_children():
            widget.grid_forget()
        for row, contact in enumerate(get_contacts(self.engine)):
            self._add_row(row, contact)

    def _add_row(self, row: int, contact: ContactOutputSchema):
        # Retrieve padding values.
        padx = (0, settings.graphics.horizontal_padding)
        pady = (0, settings.graphics.vertical_padding)

        # Create and insert the name label.
        name_label = ttk.Label(
            master=self.interior,
            text=contact.name,
            anchor='w',
            font=(
                settings.graphics.font_family,
                settings.graphics.font_size,
            ),
        )
        name_label.grid(column=0, row=row, sticky='w', padx=padx, pady=pady)

        message_button = ttk.Button(
            self.interior,
            text='Awaiting Key Exchange',
            state='disabled',
        )
        if contact.fernet_keys:
            message_button.config(
                text='Open Messages',
                state='normal',
                command=(
                    lambda contact=contact:
                        self._open_messages(contact)
                ),
            )
        message_button.grid(
            column=1,
            row=row,
            padx=padx,
            pady=pady,
            sticky='ew',
        )

        remove_button = ttk.Button(
            master=self.interior,
            text='Remove',
            command=(
                lambda contact=contact:
                    self._remove_contact(contact)
            ),
        )
        remove_button.grid(column=2, row=row, padx=0, pady=pady)

    def _open_messages(self, contact: ContactOutputSchema):
        message_window = self.message_windows.get(contact.id)
        if message_window is not None and message_window.winfo_exists():
            message_window.focus()
        else:
            self.message_windows[contact.id] = MessageWindow(
                master=self.winfo_toplevel(),
                engine=self.engine,
                signature_key=self.signature_key,
                http_client=self.http_client,
                contact=contact,
            )

    def _remove_contact(self, contact: ContactOutputSchema):
        confirmation = messagebox.askyesno(
            title='Confirm Contact Deletion',
            message=(
                f'Are you sure you wish to delete {contact.name}? '
                f'this will delete all saved messages.'
            ),
        )
        if confirmation:
            remove_contact(self.engine, contact.id)

class ContactsPane(ttk.Frame):
    def __init__(
            self,
            master: ttk.Notebook,
            engine: Engine,
            signature_key: Ed25519PrivateKey,
            http_client: httpx.Client,
        ):
        # Call the Frame constructor.
        super().__init__(master)
        # Store relevant variables.
        self.engine = engine
        self.signature_key = signature_key
        self.http_client = http_client
        # Create and place widgets.
        self.existing_contacts_frame = _ExistingContactsFrame(
            master=self,
            engine=engine,
            signature_key=signature_key,
            http_client=http_client,
        )
        self.existing_contacts_frame.grid(
            column=0,
            row=1,
            columnspan=2,
            sticky='nsew',
        )
        ttk.Button(
            master=self,
            text='Add Contact',
            command=self._add_contact,
        ).grid(
            column=0,
            row=0,
            sticky='e',
            padx=settings.graphics.horizontal_padding,
            pady=settings.graphics.vertical_padding,
        )
        ttk.Button(
            master=self,
            text='Refresh',
            command=self.existing_contacts_frame.reload,
        ).grid(
            column=1,
            row=0,
            sticky='ew',
            padx=(0, settings.graphics.horizontal_padding),
            pady=settings.graphics.vertical_padding,
        )
        # Configure grid properties.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        # Load the existing contacts.
        self.existing_contacts_frame.reload()

    def _add_contact(self):
        dialog = AddContactDialog(self)
        self.wait_window(dialog)
        while dialog.result is not None:
            contact_input = ContactInputSchema.model_validate(dialog.result)
            try:
                add_contact(self.engine, contact_input)
                break
            except IntegrityError:
                messagebox.showerror(
                    title='Add Contact Error',
                    message='A contact with this name or key already exists.',
                )
            dialog = AddContactDialog(self)
            self.wait_window(dialog)
        if dialog.result is not None:
            self.existing_contacts_frame.reload()
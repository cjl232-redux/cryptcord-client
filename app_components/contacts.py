from tkinter import messagebox, ttk

import httpx

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import Engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app_components.dialogs.contact_dialogs import AddContactDialog
from app_components.messages import MessageWindow
from app_components.scrollable_frames import ScrollableFrame
from database.models import Contact
from database.operations.contacts import get_contacts, remove_contact
from database.schemas.output import ContactOutputSchema
from server.operations import fetch_data, post_exchange_key
from settings import settings

class _ExistingContactsFrame(ScrollableFrame):
    def __init__(
            self,
            master: ttk.Frame,
            engine: Engine,
            signature_key: Ed25519PrivateKey,
        ):
        super().__init__(master)
        self.engine = engine
        self.signature_key = signature_key
        self.message_windows: dict[int, MessageWindow] = {}

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
                text='Message',
                state='normal',
                command=(
                    lambda contact=contact:
                        self._open_messages(contact)
                ),
            )
        message_button.grid(column=1, row=row, padx=padx, pady=pady)

        remove_button = ttk.Button(
            master=self.interior,
            text='Remove',
            command=(
                lambda contact=contact:
                    self._remove_contact(contact)
            ),
        )
        remove_button.grid(column=2, row=row, padx=padx, pady=pady)

    def _open_messages(self, contact: ContactOutputSchema):
        message_window = self.message_windows.get(contact.id)
        if message_window is not None and message_window.winfo_exists():
            message_window.focus()
        else:
            self.message_windows[contact.id] = MessageWindow(
                master=self.winfo_toplevel(),
                engine=self.engine,
                signature_key=self.signature_key,
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
        # Perform an initial load of existing contacts.
        self.existing_contacts_frame.reload()
        # Will need an AFTER in here for server retrieval

    def _add_contact(self, *_):
        dialog = AddContactDialog(self)
        self.wait_window(dialog)
        if dialog.result is not None:
            with Session(self.engine, expire_on_commit=False) as session:
                contact = Contact(**dialog.result.model_dump())
                session.add(contact)
                try:
                    session.commit()
                    self.existing_contacts_frame.reload()
                    # Perform an immediate server retrieval:
                    fetch_data(
                        self.engine,
                        self.signature_key,
                        self.http_client,
                    )
                    if not contact.received_keys:
                        post_exchange_key(
                            self.engine,
                            self.signature_key,
                            self.http_client,
                            contact.id,
                        )
                except IntegrityError:
                    session.rollback()
                    statement = select(
                        Contact
                    ).where(
                        Contact.public_key == dialog.result.public_key,
                    )
                    if session.scalar(statement) is None:
                        messagebox.showerror(
                            title='Add Contact Failure',
                            message='A contact with this name already exists.'
                        )
                    else:
                        messagebox.showerror(
                            title='Add Contact Failure',
                            message='A contact with this key already exists.'
                        )
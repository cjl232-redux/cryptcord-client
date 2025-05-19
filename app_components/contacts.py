import binascii
import sqlite3
import tkinter as tk
import tkinter.ttk as ttk
from base64 import b64decode, urlsafe_b64encode
from contextlib import closing
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from tkinter import filedialog, messagebox

from app_components.scrollable_frames import VerticalScrollableFrame
from database_functions import add_contact, get_existing_contacts



class ContactDetailsDialog(tk.Toplevel):
    def __init__(
            self,
            master,
            name: str = None,
            public_key: str = None,
            existing_names: set[str] = None,
            existing_public_keys: set[str] = None,
            *args,
            **kwargs,
        ):
        # Call the base constructor, then grab all events.
        super().__init__(master, *args, **kwargs)
        self.grab_set()

        # Configure window properties.
        self.title='Contact Details'
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', self.cancel)

        # Properly handle default values for existing names and keys.
        self.existing_names = existing_names
        if self.existing_names is None:
            self.existing_names: set[str] = set()
        self.existing_public_keys = existing_public_keys
        if self.existing_public_keys is None:
            self.existing_public_keys: set[str] = set()

        # If a name and key are supplied, remove these from the above sets.
        if name is not None:
            self.existing_names.discard(name)
        if public_key is not None:
            self.existing_public_keys.discard(name)
        
        # Create the child elements.
        intro_text = ttk.Label(
            master=self,
            text=(
                'Specify a unique name and a Base64-encoded 32-byte public '
                'key for this contact. The public key can be loaded from a '
                'PEM-encoded serialisation.'
            ),
            wraplength=600,
        )
        name_header_label = ttk.Label(self, text='Name:')
        public_key_header_label = ttk.Label(self, text='Public Key:')
        self.name_variable = tk.StringVar(
            master=self,
            value=name,
        )
        self.name_entry = ttk.Entry(
            master=self,
            textvariable=self.name_variable,
        )
        self.public_key_variable = tk.StringVar(
            master=self,
            value=public_key,
        )
        self.public_key_entry = ttk.Entry(
            master=self,
            textvariable=self.public_key_variable,
        )
        browse_button = ttk.Button(self, text='Browse...', command=self.browse)
        submit_button = ttk.Button(self, text='Submit', command=self.submit)
        cancel_button = ttk.Button(self, text='Cancel', command=self.cancel)

        # Place the child elements.
        intro_text.grid(column=0, row=0, sticky='nw', columnspan=3)
        name_header_label.grid(column=0, row=1, sticky='w')
        self.name_entry.grid(column=1, row=1, sticky='ew')
        public_key_header_label.grid(column=0, row=2, sticky='w')
        self.public_key_entry.grid(column=1, row=2, sticky='ew')
        browse_button.grid(column=2, row=2, sticky='ew')
        submit_button.grid(column=1, row=3, sticky='e')
        cancel_button.grid(column=2, row=3, sticky='ew')

        # Finalise grid configuration.
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)


    def browse(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                with open(file_path, 'rb') as file:
                    key = load_pem_public_key(file.read())
                    key_bytes = urlsafe_b64encode(key.public_bytes_raw())
                    self.public_key_variable.set(key_bytes.decode())

            except:
                messagebox.showerror(
                    title='Error',
                    message='Failed to load public key from the chosen file.',
                )
            pass

    # Sigh... I really hate having this all here.
    # I'd much rather it was validated during typing.
    def submit(self):
        # Check for validation errors. Only close the window if there are none.
        if self.name_variable.get() in self.existing_names:
            messagebox.showerror(
                title='Error',
                message='A contact with this name already exists.',
            )
            self.name_entry.focus()
        elif self.public_key_variable.get() in self.existing_public_keys:
            messagebox.showerror(
                title='Error',
                message='A contact with this public key already exists.',
            )
            self.public_key_entry.focus()
        else:
            try:
                key = self.public_key_variable.get()
                decoded_key = b64decode(key, altchars='-_', validate=True)
                if len(decoded_key) != 32:
                    raise ValueError()
                self.result = (
                    self.name_variable.get(),
                    urlsafe_b64encode(decoded_key).decode(),
                )
                self.destroy()
            except:                    
                messagebox.showerror(
                    title='Error',
                    message=(
                        'This public key is not a valid Base64 encoding of a '
                        '32-byte value.'
                    ),
                )
                self.public_key_entry.focus()

    def cancel(self):
        self.result = None
        self.destroy()


class ExistingContactsFrame(VerticalScrollableFrame):
    def __init__(self, master, client_db: sqlite3.Connection, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.name_labels: list[ttk.Label] = []
        self.client_db = client_db
        self.load_contacts()

    def load_contacts(self):
        for child in self.interior.winfo_children():
            child.grid_forget()
        with closing(self.client_db.cursor()) as cursor:
            cursor.execute(' '.join([
                'SELECT',
                '    contacts.id,',
                '    contacts.name,',
                '    pending_exchanges.id IS NOT NULL AS exchange_pending,',
                '    encryption_keys.id IS NOT NULL AS exchange_complete',
                'FROM',
                '    contacts',
                'LEFT JOIN',
                '    encryption_keys',
                'ON',
                '    contacts.id = encryption_keys.contact_id',
                'LEFT JOIN',
                '    pending_exchanges',
                'ON',
                '    contacts.id = pending_exchanges.contact_id',
                'ORDER BY',
                '    contacts.name',
            ]))
            for i, contact in enumerate(cursor.fetchall()):
                label = ttk.Label(self.interior, text=contact[1])
                label.grid(column=0, row=i, sticky='w', pady=(0, 5,))
                remove_button = ttk.Button(
                    master=self.interior,
                    text='Remove',
                    command=lambda id=contact[0]: self.remove_contact(id),
                )
                remove_button.grid(column=1, row=i, pady=(0, 5,))
            self.interior.columnconfigure(0, weight=1)

    def remove_contact(self, id: int):
        client_db: sqlite3.Connection = self.winfo_toplevel().client_db
        with closing(client_db.cursor()) as cursor:
            cursor.execute('SELECT name FROM contacts WHERE id = ?', (id,))
            response = messagebox.askyesno(
                title='Confirm Contact Deletion',
                message=(
                    f'Are you sure you wish to delete {cursor.fetchone()[0]}? '
                    f'This will permanently delete any shared keys and '
                    f'saved messages.'
                ),
            )
            if response:
                cursor.execute('DELETE FROM contacts WHERE id = ?', (id,))
                self.load_contacts()
                

class ContactsPane(ttk.Frame):
    def __init__(self, master, client_db: sqlite3.Connection, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.client_db = client_db
        self.add_button = ttk.Button(
            master=self,
            text='Add Contact',
            command=self.add_contact,
        )
        self.add_button.grid(column=0, row=0)
        self.existing_contacts = ExistingContactsFrame(
            master=self,
            client_db=self.client_db,
            scroll_speed=5,
        )
        self.refresh_button = ttk.Button(
            master=self,
            text='Refresh',
            command=self.existing_contacts.load_contacts,
        )
        self.refresh_button.grid(column=1, row=0)
        self.existing_contacts.grid(
            column=0,
            row=1,
            columnspan=2,
            sticky='nsew',
            padx=(5, 0,),
            pady=(5, 0,),
        )
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

    def refresh_contacts(self):
        self.existing_contacts.grid_forget()
        self.existing_contacts = ExistingContactsFrame(self, self.client_db)
        self.existing_contacts.grid(column=0, row=1, columnspan=2)

    def add_contact(self):
        conn: sqlite3.Connection = self.winfo_toplevel().db_connection
        current_contacts = get_existing_contacts(conn)
        dialog = ContactDetailsDialog(
            self,
            existing_names=set([x[0] for x in current_contacts]),
            existing_public_keys=set([x[1] for x in current_contacts]),
        )
        self.wait_window(dialog)
        if dialog.result:
            name, key = dialog.result
            add_contact(self.winfo_toplevel().db_connection, name, key)
            self.refresh_contacts()
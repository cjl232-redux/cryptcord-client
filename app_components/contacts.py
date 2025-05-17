import sqlite3
import tkinter as tk
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
from contextlib import closing
from app_components.scrollable_frames import VerticalScrollableFrame

class AddContactDialog(tk.Toplevel):
    def __init__(self, client_db: sqlite3.Connection, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        self.add_button = ttk.Button(self, text='Add Contact')
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

    
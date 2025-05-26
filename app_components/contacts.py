import sqlite3

from contextlib import closing
from tkinter import messagebox, ttk

from app_components.dialogs.contact_dialogs import AddContactDialog
from app_components.messages import MessageWindow
from app_components.scrollable_frames import VerticalFrame
from database_functions import add_contact

class ExistingContactsFrame(VerticalFrame):
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
                message_button = ttk.Button(
                    master=self.interior,
                    text='Message',
                    command=lambda id=contact[0]: self.open_messages(id),
                )
                message_button.grid(column=1, row=i, pady=(0, 5,))
                remove_button = ttk.Button(
                    master=self.interior,
                    text='Remove',
                    command=lambda id=contact[0]: self.remove_contact(id),
                )
                remove_button.grid(column=2, row=i, pady=(0, 5,))
            self.interior.columnconfigure(0, weight=1)

    def open_messages(self, id: int):
        local_database = self.winfo_toplevel().db_connection
        MessageWindow(self.winfo_toplevel(), id, local_database)

    def remove_contact(self, id: int):
        db_connection = self.winfo_toplevel().db_connection
        with closing(db_connection.cursor()) as cursor:
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
                

# Need to remake this. Rely on pulling database from top level.
class _ContactsPane(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.message_windows: dict[int, MessageWindow] = {}
        self.after(1000, self.update)

    def update(self):
        self.message_windows[len(self.message_windows)] = MessageWindow(self, None, None)
        self.after(1000, self.update)


class ContactsPane(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.client_db = self.winfo_toplevel().db_connection
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
        db_connection = self.winfo_toplevel().db_connection
        dialog = AddContactDialog(self, db_connection)
        self.wait_window(dialog)
        if dialog.result:
            name = dialog.result['name']
            public_key = dialog.result['public_key']
            add_contact(db_connection, name, public_key)
            self.refresh_contacts()
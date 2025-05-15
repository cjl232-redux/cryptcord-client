import sqlite3
import tkinter as tk
from contextlib import closing
from tkinter import ttk

class ContactEntry(ttk.Frame):
    def __init__(
            self,
            master,
            id: int,
            name: str,
            exchanged: bool,
            *args, 
            **kwargs,
        ):
        super().__init__(master, *args, **kwargs)
        self.id = id
        self.name_label = ttk.Label(self, text=name)
        self.name_label.grid(row=0, column=0)
        self.message_button = ttk.Button(self, text='No Key')
        if exchanged:
            self.message_button.config(text='Message')
        self.message_button.grid(row=0, column=1)

class ContactEntries(ttk.Frame):
    def __init__(self, master, client_db: sqlite3.Connection, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.entries = []
        self.scrollbar = ttk.Scrollbar(self)
        self.scrollbar.grid(column=1, row=0)
        self.canvas = tk.Canvas(self, yscrollcommand=self.scrollbar.set)
        self.canvas.grid(column=0, row=0)
        with closing(client_db.cursor()) as cursor:
            cursor.execute((
                'SELECT '
                '   contacts.id, '
                '   contacts.nickname, '
                '   encryption_keys.id IS NOT NULL as exchange_complete '
                'FROM '
                '   contacts '
                'LEFT JOIN '
                '   encryption_keys '
                'ON '
                '   contacts.id = encryption_keys.contact_id '
                'ORDER BY '
                '   contacts.nickname '
            ))
            for i, contact in enumerate(cursor.fetchall()):
                entry = ContactEntry(
                    master=self.canvas,
                    id=contact[0],
                    name=contact[1],
                    exchanged=contact[2],
                )
                entry.grid(column=0, row=i)
                self.entries.append(entry)
                for j in range(100):
                    entry = ContactEntry(
                        master=self.canvas,
                        id=contact[0],
                        name=contact[1],
                        exchanged=contact[2],
                    )
                    entry.grid(column=0, row=i + j)
                    self.entries.append(entry)

class ContactsPane(ttk.Frame):
    def __init__(self, master, client_db: sqlite3.Connection, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.client_db = client_db
        self.add_button = ttk.Button(self, text='Add Contact')
        self.add_button.grid(column=0, row=0)
        self.refresh_button = ttk.Button(
            master=self,
            text='Refresh',
            command=self.refresh_contacts,
        )
        self.refresh_button.grid(column=1, row=0)
        self.contact_entries = ContactEntries(self, self.client_db)
        self.contact_entries.grid(column=0, row=1, columnspan=2)

    def refresh_contacts(self):
        self.contact_entries.grid_forget()
        self.contact_entries = ContactEntries(self, self.client_db)
        self.contact_entries.grid(column=0, row=1, columnspan=2)

    
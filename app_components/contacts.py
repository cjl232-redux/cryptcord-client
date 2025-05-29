import json
import sqlite3

from base64 import b64decode, b64encode
from contextlib import closing
from tkinter import messagebox, ttk

from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app_components.dialogs.contact_dialogs import AddContactDialog
from app_components.messages import MessageWindow
from app_components.scrollable_frames import VerticalFrame
from database.models import Contact

# Button to send exchange request
# Function for periodic retrieval of exchange keys
# For messages: periodic refresh. Store last refresh time (on startup, take
# it from the maximum value saved in messages)

class _ExistingContactsFrame(VerticalFrame):
    def __init__(
            self,
            master: ttk.Frame,
            engine: Engine,
            signature_key: ed25519.Ed25519PrivateKey,
            scroll_speed: int = 5,
        ):
        super().__init__(
            master=master,
            scroll_speed=scroll_speed,
        )
        #self.name_labels: list[ttk.Label] = []
        self.engine = engine
        self.signature_key = signature_key
        self.load_contacts()
        #self.after(2000, self._retrieve_keys)

    def load_contacts(self):
        for child in self.interior.winfo_children():
            child.grid_forget()
        with Session(self.engine) as session:
            statement = select(Contact).order_by(Contact.name)
            for i, contact in enumerate(session.scalars(statement)):
                label = ttk.Label(self.interior, text=contact.name)
                label.grid(column=0, row=i, sticky='w', pady=(0, 5,))
                remove_button = ttk.Button(
                    master=self.interior,
                    text='Remove',
                    command=lambda id=contact.id: self._remove_contact(id),
                )
                remove_button.grid(column=1, row=i, pady=(0, 5,))
        self.interior.columnconfigure(0, weight=1)

    #     with closing(self.client_db.cursor()) as cursor:
    #         cursor.execute(' '.join([
    #             'SELECT',
    #             '    contacts.id,',
    #             '    contacts.name,',
    #             '    contacts.ed25519_public_key,',
    #             '    pending_exchanges.id IS NOT NULL AS exchange_pending,',
    #             '    encryption_keys.id IS NOT NULL AS exchange_complete',
    #             'FROM',
    #             '    contacts',
    #             'LEFT JOIN',
    #             '    encryption_keys',
    #             'ON',
    #             '    contacts.id = encryption_keys.contact_id',
    #             'LEFT JOIN',
    #             '    pending_exchanges',
    #             'ON',
    #             '    contacts.id = pending_exchanges.contact_id',
    #             'ORDER BY',
    #             '    contacts.name',
    #         ]))
    #         for i, contact in enumerate(cursor.fetchall()):
    #             print(contact)
    #             label = ttk.Label(self.interior, text=contact[1])
    #             label.grid(column=0, row=i, sticky='w', pady=(0, 5,))
    #             key_status = ttk.Label(self.interior, text='Pending')
    #             if contact[4]:
    #                 key_status.config(text='Exchanged')
    #             elif not contact[3]:
    #                 self._post_key(contact[0], contact[2])
    #             key_status.grid(column=1, row=i, sticky='w', pady=(0, 5,))
    #             message_button = ttk.Button(
    #                 master=self.interior,
    #                 text='Message',
    #                 command=lambda id=contact[0]: self.open_messages(id),
    #             )
    #             message_button.grid(column=2, row=i, pady=(0, 5,))
    #             remove_button = ttk.Button(
    #                 master=self.interior,
    #                 text='Remove',
    #                 command=lambda id=contact[0]: self.remove_contact(id),
    #             )
    #             remove_button.grid(column=3, row=i, pady=(0, 5,))
    #         self.interior.columnconfigure(0, weight=1)

    # def open_messages(self, id: int):
    #     local_database = self.winfo_toplevel().db_connection
    #     MessageWindow(self.winfo_toplevel(), id, local_database)

    def _remove_contact(self, id: int):
        with Session(self.engine) as session:
            contact = session.get_one(Contact, id)
            response = messagebox.askyesno(
                title='Confirm Contact Deletion',
                message=(
                    f'Are you sure you wish to delete {contact.name}? This '
                    f'will delete all saved messages.'
                ),
            )
            if response:
                session.delete(contact)
                session.commit()
                self.load_contacts()

    #     db_connection = self.winfo_toplevel().db_connection
    #     with closing(db_connection.cursor()) as cursor:
    #         cursor.execute('SELECT name FROM contacts WHERE id = ?', (id,))
    #         response = messagebox.askyesno(
    #             title='Confirm Contact Deletion',
    #             message=(
    #                 f'Are you sure you wish to delete {cursor.fetchone()[0]}? '
    #                 f'This will permanently delete any shared keys and '
    #                 f'saved messages.'
    #             ),
    #         )
    #         if response:
    #             cursor.execute('DELETE FROM contacts WHERE id = ?', (id,))
    #             self.load_contacts()

    # def _post_key(self, recipient_id, recipient_public_key):
    #     signature_key = self.winfo_toplevel().signature_key
    #     key = x25519.X25519PrivateKey.generate()
    #     b64_public_key = b64encode(key.public_key().public_bytes_raw())
    #     server_connection = self.winfo_toplevel().server_context
    #     data = {
    #         'command': 'POST_KEY',
    #         'recipient_public_key': recipient_public_key,
    #         'public_exchange_key': b64_public_key.decode(),
    #         'signature': b64encode(signature_key.sign(key.public_key().public_bytes_raw())).decode(),
    #     }
    #     response: dict = server_connection.send_request(data)
    #     print(response)
    #     if response.get('status') == 201:
    #         self.client_db.execute(
    #             (
    #                 'INSERT INTO '
    #                 '  pending_exchanges(contact_id, x25519_private_key) '
    #                 '  VALUES(?, ?)'
    #             ),
    #             (recipient_id, b64encode(key.private_bytes_raw()).decode()),
    #         )
    #         self.client_db.commit()


        


#     def _retrieve_keys(self):
#         server_connection = self.winfo_toplevel().server_context
#         response = server_connection.send_request({'command': 'RETRIEVE_KEYS'})
#         for row in response['data']:
#             # Check if they're a contact
#             with closing(self.client_db.cursor()) as cursor:
#                 cursor.execute(
#                     ' '.join([
#                        'SELECT',
#                        '  contacts.id,',
#                        '  pending_exchanges.x25519_private_key',
#                        'FROM',
#                        '  contacts',
#                        'LEFT JOIN',
#                        '  pending_exchanges',
#                        'ON',
#                        '  contacts.id = pending_exchanges.contact_id',
#                        'WHERE',
#                        '  contacts.ed25519_public_key = ?',
#                     ]),
#                     (row[0],),
#                 )
#                 result = cursor.fetchone()
            
#             # If they're not registered, skip to the next contact.
#             if result is None:
#                 print('unregistered contact')
#                 continue
#             elif result[1] is None:
#                 continue

#             # Construct the relevant keys:
#             try:
#                 verification_key = ed25519.Ed25519PublicKey.from_public_bytes(
#                     data=b64decode(row[0]),
#                 )
#                 private_exchange_key = x25519.X25519PrivateKey.from_private_bytes(
#                     data=b64decode(result[1]),
#                 )
#                 public_exchange_key = x25519.X25519PublicKey.from_public_bytes(
#                     data=b64decode(row[1]),
#                 )
#                 verification_key.verify(b64decode(row[2]), b64decode(row[1]))
#             except:
#                 print('verification failed')
#                 continue

#             # Add the combined key to the database.
#             combined_key = private_exchange_key.exchange(public_exchange_key)
#             self.client_db.execute(
#                 'INSERT INTO encryption_keys(contact_id, shared_secret_key) VALUES(?, ?)',
#                 (result[0], b64encode(combined_key).decode()),
#             )
#             self.client_db.execute(
#                 'DELETE FROM pending_exchanges WHERE contact_id = ?',
#                 (result[0],),
#             )
#             self.client_db.commit()
#         self.after(3000, self._retrieve_keys)

                

# # Need to remake this. Rely on pulling database from top level.
# # Change in plan, pass it.
# class _ContactsPane(ttk.Frame):
#     def __init__(self, master, *args, **kwargs):
#         super().__init__(master, *args, **kwargs)
#         self.message_windows: dict[int, MessageWindow] = {}
#         self.after(1000, self.update)

#     def update(self):
#         self.message_windows[len(self.message_windows)] = MessageWindow(self, None, None)
#         self.after(1000, self.update)


class ContactsPane(ttk.Frame):
    def __init__(
            self,
            master: ttk.Frame,
            engine: Engine,
            signature_key: ed25519.Ed25519PrivateKey,
        ):
        super().__init__(master)
        self.engine = engine
        self.signature_key = signature_key

        self.add_button = ttk.Button(
            master=self,
            text='Add Contact',
            command=self._add_contact,
        )
        self.add_button.grid(column=0, row=0)

        self.existing_contacts = _ExistingContactsFrame(
            master=self,
            engine=self.engine,
            signature_key=self.signature_key,
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


    def _add_contact(self):
        # Retrieve existing names and keys.
        with Session(self.engine) as session:
            used_names: set[str] = set()
            used_public_keys: set[str] = set()
            for contact in session.scalars(select(Contact)):
                used_names.add(contact.name)
                used_public_keys.add(contact.public_key)
        # Construct and wait for the dialog.
        dialog = AddContactDialog(self, used_names, used_public_keys)
        self.wait_window(dialog)
        if dialog.result:
            with Session(self.engine) as session:
                contact = Contact(
                    name=dialog.result['name'],
                    public_key=dialog.result['public_key'],
                )
                session.add(contact)
                session.commit()
            self.existing_contacts.load_contacts()
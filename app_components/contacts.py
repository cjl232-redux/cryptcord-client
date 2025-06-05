from tkinter import messagebox, ttk
from typing import Any

from cryptography.hazmat.primitives.asymmetric import ed25519
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app_components.dialogs.contact_dialogs import AddContactDialog
from app_components.messages import MessageWindow
from app_components.scrollable_frames import ScrollableFrame
from app_components.settings import SettingsSchema
from database.models import Contact
from database.schemas.output import ContactOutputSchema

class _ExistingContactsFrame(ScrollableFrame):
    def __init__(
            self,
            master: ttk.Frame,
            engine: Engine,
            signature_key: ed25519.Ed25519PrivateKey,
            settings: SettingsSchema,
            scroll_speed: int = 5,
            *args: tuple[Any],
            **kwargs: dict[str, Any],
    ):
        super().__init__(master, scroll_speed, *args, **kwargs)
        self.engine = engine
        self.signature_key = signature_key
        self.settings = settings
        self.message_windows: dict[int, MessageWindow] = {}

    def reload(self):
        for widget in self.interior.winfo_children():
            widget.grid_forget()
        with Session(self.engine) as session:
            statement = select(Contact).order_by(Contact.name)
            contacts = (
                ContactOutputSchema.model_validate(contact)
                for contact in session.scalars(statement)
            )
            for row, contact in enumerate(contacts):
                ttk.Label(
                    master=self.interior,
                    text=contact.name,
                ).grid(
                    column=0,
                    row=row,
                    sticky='w',
                    pady=(0, 5),
                )
                ttk.Button(
                    master=self.interior,
                    text='Message',
                    command=lambda contact=contact: self._open_messages(contact),
                ).grid(
                    column=1,
                    row=row,
                    pady=(0, 5),
                )
                ttk.Button(
                    master=self.interior,
                    text='Remove',
                    command=lambda id=contact.id: self._remove_contact(id),
                ).grid(
                    column=2,
                    row=row,
                    pady=(0, 5),
                )

    def _open_messages(
            self,
            contact: ContactOutputSchema,
        ):
        message_window = self.message_windows.get(contact.id)
        if message_window is not None and message_window.winfo_exists():
            message_window.focus()
        else:
            self.message_windows[contact.id] = MessageWindow(
                master=self,
                engine=self.engine,
                signature_key=self.signature_key,
                contact_id=contact.id,
                contact_name=contact.name,
                contact_verification_key=contact.verification_key,
            )

    def _remove_contact(self, id: int):
        message_window = self.message_windows.get(id)
        if message_window is not None and message_window.winfo_exists():
            message_window.destroy()
        with Session(self.engine) as session:
            contact_obj = session.get_one(Contact, id)
            contact = ContactOutputSchema.model_validate(contact_obj)
            confirmation = messagebox.askyesno(
                title='Confirm Contact Deletion',
                message=(
                    f'Are you sure you wish to delete {contact.name}? '
                    f'this will delete all saved messages.'
                ),
            )
            if confirmation:
                session.delete(contact_obj)
                session.commit()
                self.reload()

class ContactsPane(ttk.Frame):
    def __init__(
            self,
            master: ttk.Notebook,
            engine: Engine,
            signature_key: ed25519.Ed25519PrivateKey,
            settings: SettingsSchema,
        ):
        super().__init__(master)
        self.engine = engine

        self.existing_contacts_frame = _ExistingContactsFrame(
            master=self,
            engine=engine,
            signature_key=signature_key,
            settings=settings,
        )
        self.existing_contacts_frame.grid(
            column=0,
            row=1,
            columnspan=2,
            sticky='nsew',
            padx=(10, 10),
            pady=(5, 10),
        )
        ttk.Button(
            master=self,
            text='Add Contact',
            command=self._add_contact,
        ).grid(
            column=0,
            row=0,
            sticky='e',
            padx=(10, 5),
            pady=(10, 5),
        )
        ttk.Button(
            master=self,
            text='Refresh',
            command=self.existing_contacts_frame.reload,
        ).grid(
            column=1,
            row=0,
            sticky='ew',
            padx=(5, 10),
            pady=(10, 5),
        )
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.existing_contacts_frame.reload()

    def _add_contact(self, *_):
        # Retrieve existing names and keys.
        with Session(self.engine) as session:
            used_names: set[str] = set()
            used_public_keys: set[ed25519.Ed25519PublicKey] = set()
            existing_contacts = (
                ContactOutputSchema.model_validate(contact)
                for contact in session.scalars(select(Contact))
            )
            for contact in existing_contacts:
                used_names.add(contact.name)
                used_public_keys.add(contact.verification_key)
        # Construct the dialog and await a result.
        dialog = AddContactDialog(
            master=self,
            used_names=used_names,
            used_public_keys=used_public_keys,
        )
        self.wait_window(dialog)
        if dialog.result:
            # Needs to be a contact output object, or rather an input one
            with Session(self.engine) as session:
                contact = Contact(**dialog.result.model_dump())
                session.add(contact)
                session.commit()
            self.existing_contacts_frame.reload()






   #     def _add_contact(self):
#         # Retrieve existing names and keys.
#         with Session(self.engine) as session:
#             used_names: set[str] = set()
#             used_public_keys: set[str] = set()
#             for contact in session.scalars(select(Contact)):
#                 used_names.add(contact.name)
#                 used_public_keys.add(contact.public_key)
#         # Construct and wait for the dialog.
#         dialog = AddContactDialog(self, used_names, used_public_keys)
#         self.wait_window(dialog)
#         if dialog.result:
#             with Session(self.engine) as session:
#                 contact = Contact(
#                     name=dialog.result['name'],
#                     public_key=dialog.result['public_key'],
#                 )
#                 session.add(contact)
#                 session.commit()
#             self.existing_contacts.retrieve_contacts()



# class ContactsPane(ttk.Frame):
#     def __init__(
#             self,
#             master: ttk.Frame,
#             engine: Engine,
#             signature_key: ed25519.Ed25519PrivateKey,
#             settings: dict[str, Any]
#         ):
#         # Call the parent constructor and store values.
#         super().__init__(master)
#         self.engine = engine
#         self.signature_key = signature_key

#         # Create and place the contacts list.
#         self.existing_contacts = _ExistingContactsFrame(
#             master=self,
#             engine=self.engine,
#             signature_key=self.signature_key,
#             scroll_speed=5,
#         )
#         self.existing_contacts.grid(
#             column=0,
#             row=1,
#             columnspan=2,
#             sticky='nsew',
#             padx=10,
#             pady=(5, 10,),
#         )
#         self.columnconfigure(0, weight=1)
#         self.rowconfigure(1, weight=1)

#         # Create and place control buttons.
#         self.add_button = ttk.Button(
#             master=self,
#             text='Add Contact',
#             command=self._add_contact,
#         )
#         self.add_button.grid(
#             column=0,
#             row=0,
#             sticky='e',
#             padx=(10, 5),
#             pady=(10, 5),
#         )
#         self.refresh_button = ttk.Button(
#             master=self,
#             text='Refresh',
#             command=self.existing_contacts.retrieve_contacts,
#         )
#         self.refresh_button.grid(
#             column=1,
#             row=0,
#             sticky='ew',
#             padx=(5, 10),
#             pady=(10, 5),
#         )

#         # Use the signature key to pre-prepare retrieval requests.
#         # Probably avoid this, since it's a lot more code overall if I
#         # pre-prepare every time. Although... I could condense this!
#         # TODO: utility function somewhere to do it
#         retrieve_keys_request_data = {
#             'action': 'retrieve_keys',
#         }
#         signature_bytes = signature_key.sign(
#             data=json.dumps(retrieve_keys_request_data).encode(),
#         )
#         public_key_bytes = signature_key.public_key().public_bytes_raw()
#         retrieve_keys_request: dict[str, Any] = {
#             'data': retrieve_keys_request_data,
#             'signature': b64encode(signature_bytes).decode(),
#             'public_key': b64encode(public_key_bytes).decode(),
#         }
#         self.retrieve_keys_request = json.dumps(retrieve_keys_request).encode()



#     def _add_contact(self):
#         # Retrieve existing names and keys.
#         with Session(self.engine) as session:
#             used_names: set[str] = set()
#             used_public_keys: set[str] = set()
#             for contact in session.scalars(select(Contact)):
#                 used_names.add(contact.name)
#                 used_public_keys.add(contact.public_key)
#         # Construct and wait for the dialog.
#         dialog = AddContactDialog(self, used_names, used_public_keys)
#         self.wait_window(dialog)
#         if dialog.result:
#             with Session(self.engine) as session:
#                 contact = Contact(
#                     name=dialog.result['name'],
#                     public_key=dialog.result['public_key'],
#                 )
#                 session.add(contact)
#                 session.commit()
#             self.existing_contacts.retrieve_contacts()

#     # def _retrieve_keys(self):
#     #     request = 
#     #     pass
#     # Likely need to pass through a connection context too












# import json
# import sqlite3

# from base64 import b64decode, b64encode
# from contextlib import closing
# from tkinter import messagebox, ttk
# from typing import Any

# from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
# from sqlalchemy import Engine, select
# from sqlalchemy.orm import Session

# from app_components.dialogs.contact_dialogs import AddContactDialog
# from app_components.messages import MessageWindow
# from app_components.scrollable_frames import ScrollableFrame
# from database.models import Contact

# # Button to send exchange request
# # Function for periodic retrieval of exchange keys
# # For messages: periodic refresh. Store last refresh time (on startup, take
# # it from the maximum value saved in messages)

# class _ExistingContactsFrame(ScrollableFrame):
#     def __init__(
#             self,
#             master: ttk.Frame,
#             engine: Engine,
#             signature_key: ed25519.Ed25519PrivateKey,
#             scroll_speed: int = 5,
#         ):
#         super().__init__(
#             master=master,
#             scroll_speed=scroll_speed,
#         )
#         self.engine = engine
#         self.signature_key = signature_key
#         self.retrieve_contacts()
#         self.opened_message_windows: dict[int, MessageWindow] = {}
#         #self.after(2000, self._retrieve_keys)

#     def retrieve_contacts(self):
#         for child in self.interior.winfo_children():
#             child.grid_forget()
#         with Session(self.engine) as session:
#             statement = select(Contact).order_by(Contact.name)
#             for i, contact in enumerate(session.scalars(statement)):
#                 label = ttk.Label(self.interior, text=contact.name)
#                 label.grid(column=0, row=i, sticky='w', pady=(0, 5,))
#                 message_button = ttk.Button(
#                     master=self.interior,
#                     text='Message',
#                     command=lambda id=contact.id: self._open_messages(id),
#                 )
#                 message_button.grid(column=1, row=i, pady=(0, 5,))
#                 remove_button = ttk.Button(
#                     master=self.interior,
#                     text='Remove',
#                     command=lambda id=contact.id: self._remove_contact(id),
#                 )
#                 remove_button.grid(column=2, row=i, pady=(0, 5,))
#         self.interior.columnconfigure(0, weight=1)

#     def _open_messages(self, contact_id: int):
#         window = self.opened_message_windows.get(contact_id)
#         if window is not None and window.winfo_exists():
#             window.focus()
#         else:
#             self.opened_message_windows[contact_id] = MessageWindow(
#                 master=self.winfo_toplevel(),
#                 engine=self.engine,
#                 signature_key=self.signature_key,
#                 contact_id=contact_id,
#             )

#     def _remove_contact(self, id: int):
#         with Session(self.engine) as session:
#             contact = session.get_one(Contact, id)
#             response = messagebox.askyesno(
#                 title='Confirm Contact Deletion',
#                 message=(
#                     f'Are you sure you wish to delete {contact.name}? This '
#                     f'will delete all saved messages.'
#                 ),
#             )
#             if response:
#                 session.delete(contact)
#                 session.commit()
#                 self.retrieve_contacts()

#     #     db_connection = self.winfo_toplevel().db_connection
#     #     with closing(db_connection.cursor()) as cursor:
#     #         cursor.execute('SELECT name FROM contacts WHERE id = ?', (id,))
#     #         response = messagebox.askyesno(
#     #             title='Confirm Contact Deletion',
#     #             message=(
#     #                 f'Are you sure you wish to delete {cursor.fetchone()[0]}? '
#     #                 f'This will permanently delete any shared keys and '
#     #                 f'saved messages.'
#     #             ),
#     #         )
#     #         if response:
#     #             cursor.execute('DELETE FROM contacts WHERE id = ?', (id,))
#     #             self.load_contacts()

#     # def _post_key(self, recipient_id, recipient_public_key):
#     #     signature_key = self.winfo_toplevel().signature_key
#     #     key = x25519.X25519PrivateKey.generate()
#     #     b64_public_key = b64encode(key.public_key().public_bytes_raw())
#     #     server_connection = self.winfo_toplevel().server_context
#     #     data = {
#     #         'command': 'POST_KEY',
#     #         'recipient_public_key': recipient_public_key,
#     #         'public_exchange_key': b64_public_key.decode(),
#     #         'signature': b64encode(signature_key.sign(key.public_key().public_bytes_raw())).decode(),
#     #     }
#     #     response: dict = server_connection.send_request(data)
#     #     print(response)
#     #     if response.get('status') == 201:
#     #         self.client_db.execute(
#     #             (
#     #                 'INSERT INTO '
#     #                 '  pending_exchanges(contact_id, x25519_private_key) '
#     #                 '  VALUES(?, ?)'
#     #             ),
#     #             (recipient_id, b64encode(key.private_bytes_raw()).decode()),
#     #         )
#     #         self.client_db.commit()


        


# #     def _retrieve_keys(self):
# #         server_connection = self.winfo_toplevel().server_context
# #         response = server_connection.send_request({'command': 'RETRIEVE_KEYS'})
# #         for row in response['data']:
# #             # Check if they're a contact
# #             with closing(self.client_db.cursor()) as cursor:
# #                 cursor.execute(
# #                     ' '.join([
# #                        'SELECT',
# #                        '  contacts.id,',
# #                        '  pending_exchanges.x25519_private_key',
# #                        'FROM',
# #                        '  contacts',
# #                        'LEFT JOIN',
# #                        '  pending_exchanges',
# #                        'ON',
# #                        '  contacts.id = pending_exchanges.contact_id',
# #                        'WHERE',
# #                        '  contacts.ed25519_public_key = ?',
# #                     ]),
# #                     (row[0],),
# #                 )
# #                 result = cursor.fetchone()
            
# #             # If they're not registered, skip to the next contact.
# #             if result is None:
# #                 print('unregistered contact')
# #                 continue
# #             elif result[1] is None:
# #                 continue

# #             # Construct the relevant keys:
# #             try:
# #                 verification_key = ed25519.Ed25519PublicKey.from_public_bytes(
# #                     data=b64decode(row[0]),
# #                 )
# #                 private_exchange_key = x25519.X25519PrivateKey.from_private_bytes(
# #                     data=b64decode(result[1]),
# #                 )
# #                 public_exchange_key = x25519.X25519PublicKey.from_public_bytes(
# #                     data=b64decode(row[1]),
# #                 )
# #                 verification_key.verify(b64decode(row[2]), b64decode(row[1]))
# #             except:
# #                 print('verification failed')
# #                 continue

# #             # Add the combined key to the database.
# #             combined_key = private_exchange_key.exchange(public_exchange_key)
# #             self.client_db.execute(
# #                 'INSERT INTO encryption_keys(contact_id, shared_secret_key) VALUES(?, ?)',
# #                 (result[0], b64encode(combined_key).decode()),
# #             )
# #             self.client_db.execute(
# #                 'DELETE FROM pending_exchanges WHERE contact_id = ?',
# #                 (result[0],),
# #             )
# #             self.client_db.commit()
# #         self.after(3000, self._retrieve_keys)

                

# # # Need to remake this. Rely on pulling database from top level.
# # # Change in plan, pass it.
# # class _ContactsPane(ttk.Frame):
# #     def __init__(self, master, *args, **kwargs):
# #         super().__init__(master, *args, **kwargs)
# #         self.message_windows: dict[int, MessageWindow] = {}
# #         self.after(1000, self.update)

# #     def update(self):
# #         self.message_windows[len(self.message_windows)] = MessageWindow(self, None, None)
# #         self.after(1000, self.update)


# class ContactsPane(ttk.Frame):
#     def __init__(
#             self,
#             master: ttk.Frame,
#             engine: Engine,
#             signature_key: ed25519.Ed25519PrivateKey,
#             settings: dict[str, Any]
#         ):
#         # Call the parent constructor and store values.
#         super().__init__(master)
#         self.engine = engine
#         self.signature_key = signature_key

#         # Create and place the contacts list.
#         self.existing_contacts = _ExistingContactsFrame(
#             master=self,
#             engine=self.engine,
#             signature_key=self.signature_key,
#             scroll_speed=5,
#         )
#         self.existing_contacts.grid(
#             column=0,
#             row=1,
#             columnspan=2,
#             sticky='nsew',
#             padx=10,
#             pady=(5, 10,),
#         )
#         self.columnconfigure(0, weight=1)
#         self.rowconfigure(1, weight=1)

#         # Create and place control buttons.
#         self.add_button = ttk.Button(
#             master=self,
#             text='Add Contact',
#             command=self._add_contact,
#         )
#         self.add_button.grid(
#             column=0,
#             row=0,
#             sticky='e',
#             padx=(10, 5),
#             pady=(10, 5),
#         )
#         self.refresh_button = ttk.Button(
#             master=self,
#             text='Refresh',
#             command=self.existing_contacts.retrieve_contacts,
#         )
#         self.refresh_button.grid(
#             column=1,
#             row=0,
#             sticky='ew',
#             padx=(5, 10),
#             pady=(10, 5),
#         )

#         # Use the signature key to pre-prepare retrieval requests.
#         # Probably avoid this, since it's a lot more code overall if I
#         # pre-prepare every time. Although... I could condense this!
#         # TODO: utility function somewhere to do it
#         retrieve_keys_request_data = {
#             'action': 'retrieve_keys',
#         }
#         signature_bytes = signature_key.sign(
#             data=json.dumps(retrieve_keys_request_data).encode(),
#         )
#         public_key_bytes = signature_key.public_key().public_bytes_raw()
#         retrieve_keys_request: dict[str, Any] = {
#             'data': retrieve_keys_request_data,
#             'signature': b64encode(signature_bytes).decode(),
#             'public_key': b64encode(public_key_bytes).decode(),
#         }
#         self.retrieve_keys_request = json.dumps(retrieve_keys_request).encode()



#     def _add_contact(self):
#         # Retrieve existing names and keys.
#         with Session(self.engine) as session:
#             used_names: set[str] = set()
#             used_public_keys: set[str] = set()
#             for contact in session.scalars(select(Contact)):
#                 used_names.add(contact.name)
#                 used_public_keys.add(contact.public_key)
#         # Construct and wait for the dialog.
#         dialog = AddContactDialog(self, used_names, used_public_keys)
#         self.wait_window(dialog)
#         if dialog.result:
#             with Session(self.engine) as session:
#                 contact = Contact(
#                     name=dialog.result['name'],
#                     public_key=dialog.result['public_key'],
#                 )
#                 session.add(contact)
#                 session.commit()
#             self.existing_contacts.retrieve_contacts()

#     # def _retrieve_keys(self):
#     #     request = 
#     #     pass
#     # Likely need to pass through a connection context too
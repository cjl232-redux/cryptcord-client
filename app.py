import tkinter as tk

from base64 import urlsafe_b64decode
from tkinter import messagebox

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError as SQLAlchemyArgumentError

from app_components.body import Body
from app_components.dialogs.key_dialogs import SignatureKeyDialog
from database.models import Base as BaseDatabaseModel
from settings import settings

class Application(tk.Tk):
    def __init__(self):
        # Call the Tk constructor and hide the resulting window.
        super().__init__()
        self.withdraw()        
        # Set all window properties.
        self.title(settings.window_name)
        # Attempt to connect to the local database.
        try:
            self.engine = create_engine(settings.local_database.url)
            BaseDatabaseModel.metadata.create_all(self.engine)
        # If this fails, show an error message and terminate the application.
        except SQLAlchemyArgumentError:
            messagebox.showerror(
                title='Invalid Database URL',
                message='Fatal error: invalid local database URL in settings.',
            )
            self.destroy()
            return
        # Load the user's signature key through a dialog.
        signature_key_dialog = SignatureKeyDialog(self)
        self.wait_window(signature_key_dialog)
        if signature_key_dialog.result is not None:
            self.signature_key = Ed25519PrivateKey.from_private_bytes(
                urlsafe_b64decode(signature_key_dialog.result.signature_key),
            )
        else:
            self.destroy()
            return
        # Create and place the application body.
        Body(self, self.engine, self.signature_key).grid(column=0, row=0)
        # Restore the window.
        self.deiconify()

        

        # # Retrieve the local database url from settings, or set a default.
        # database_url: str = 'sqlite:///database.db'

        # try:
        #     # Attempt to start the engine with the provided url.
        #     self.engine = create_engine(database_url, echo=False)
        #     event.listen(self.engine, "before_cursor_execute", explain_query)
        # except:
        #     # If an exception is raised, terminate with a message.
        #     messagebox.showerror(
        #         title='Invalid Database Path',
        #         message=(
        #             f'The local database file path specified in '
        #             f'{SETTINGS_FILE_PATH} is invalid.'
        #         ),
        #     )
        #     self.destroy()
        #     return
        # # Restore the main window and render all children.
        # self.deiconify()
        # self.body = Body(
        #     master=self,
        #     engine=self.engine,
        #     signature_key=self.signature_key,
        #     settings=None,
        # )
        # self.body.grid(column=0, row=0, sticky='nsew', padx=5, pady=5)
        # self.grid_columnconfigure(0, weight=1)
        # self.grid_rowconfigure(0, weight=1)

        # Set up the task manager.
        # self.task_manager = TaskManager(
        #     master=self,
        #     engine=self.engine,
        #     signature_key=self.signature_key,
        #     frequency_ms=300,
        # )

        # Test
        # from base64 import b64encode
        # data = {
        #     'command': 'SEND_MESSAGE2',
        #     'recipient_public_key': 'rwaj4ykXFOTzVsGcmxXNGVHsbmZiqne+B1R/KJODNB0=',
        #     'encrypted_message': 'Main app calling Kirby.',
        #     'signature': b64encode(self.signature_key.sign('Main app calling Kirby.'.encode())).decode(),
        # }
        # response = self.server_context.send_request(data)
        # print(response)
    def _tasks(self):
        server_interface.retrieve_messages(
            url=RETRIEVE_MESSAGES_URL,
            engine=self.engine,
            public_key=self.base64_public_key,
            contact_dict=self.contact_dict,
            min_datetime=None,
        )
        # retrieval_data: dict[str, Any] = {
        #     'public_key': self.base64_public_key,
        # }
        # response = requests.post(
        #     url=RETRIEVE_MESSAGES_URL,
        #     json=retrieval_data,
        # )
        # print(response.json())
        # response = requests.post(
        #     url=RETRIEVE_KEY_EXCHANGES_URL,
        #     json=retrieval_data,
        # )
        # print(response.json())
        self.after(SERVER_RETRIEVE_REFRESH_TIME, self._tasks)

        pass

if __name__ == '__main__':
    Application().mainloop()


# from sqlalchemy import event
# from sqlalchemy.engine import Engine
# import logging

# logging.basicConfig()
# logger = logging.getLogger("sqlalchemy.explain")
# logger.setLevel(logging.INFO)

# def explain_query(conn, cursor, statement, parameters, context, executemany):
#     if statement.lstrip().upper().startswith("SELECT"):
#         try:
#             explain_stmt = f"EXPLAIN QUERY PLAN {statement}"
#             cursor.execute(explain_stmt, parameters)
#             plan = cursor.fetchall()
#             logger.info("Query: %s", statement)
#             logger.info("Parameters: %s", parameters)
#             logger.info("EXPLAIN plan:")
#             for row in plan:
#                 logger.info(row)
#         except Exception as e:
#             logger.warning("EXPLAIN failed: %s", e)

# # Pass through contact dict
# # Need to pass through the network connection handler too - OLD

# import os
# import tkinter as tk

# from base64 import b64decode, b64encode
# from tkinter import messagebox
# from typing import Any

# import yaml

# from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
# from sqlalchemy import create_engine

# from app_components.body import Body
# from app_components.dialogs.private_key_dialogs import SignatureKeyDialog
# from app_components.dialogs.server_dialogs import ServerDialog
# #from app_components.tasks import TaskManager
# #from app_components import server_interface
# from database import models
# from settings import settings
# from server import operations as server_operations
# #from sideline import operations

# SETTINGS_FILE_PATH = 'settings.yaml'


# # Temporarily work with constant URLs, load them in from settings later.
# RETRIEVE_MESSAGES_URL = 'http://127.0.0.1:8000/messages/retrieve'
# RETRIEVE_KEY_EXCHANGES_URL = 'http://127.0.0.1:8000/key_exchanges/retrieve'
# SERVER_RETRIEVE_REFRESH_TIME = 3000


# class Application(tk.Tk):
#     def __init__(self):
#         # Call the Tk constructor, then withdraw the main window.
#         super().__init__()
#         self.withdraw()
        
#         # Set basic properties.
#         self.title('Cryptcord')

#         # Retrieve the local database url from settings, or set a default.
#         database_url: str = 'sqlite:///database.db'

#         try:
#             # Attempt to start the engine with the provided url.
#             self.engine = create_engine(database_url, echo=False)
#             event.listen(self.engine, "before_cursor_execute", explain_query)
#         except:
#             # If an exception is raised, terminate with a message.
#             messagebox.showerror(
#                 title='Invalid Database Path',
#                 message=(
#                     f'The local database file path specified in '
#                     f'{SETTINGS_FILE_PATH} is invalid.'
#                 ),
#             )
#             self.destroy()
#             return
#         # TODO review error handling
#         # TODO encryption of database according to private key

#         # Ensure the database has the required tables.
#         models.Base.metadata.drop_all(self.engine)
#         models.Base.metadata.create_all(self.engine)

#         # Load the user's signature key via a custom dialog.
#         signature_key_dialog = SignatureKeyDialog(self)
#         self.wait_window(signature_key_dialog)

#         # Halt initialisation and close the application if no key is loaded.
#         if signature_key_dialog.result is None:
#             self.destroy()
#             return
        
#         # Otherwise, initialise a key object from the dialog.
#         self.signature_key = Ed25519PrivateKey.from_private_bytes(
#             data=b64decode(signature_key_dialog.result['signature_key']),
#         )
#         # server_operations.post_exchange_key(
#         #     self.engine,
#         #     self.signature_key,
#         #     2,
#         # )

#         # Store the Base64-encoded public key for use in requests.
#         self.public_key = self.signature_key.public_key()
#         self.public_key_bytes = self.public_key.public_bytes_raw()
#         self.base64_public_key = b64encode(self.public_key_bytes).decode()

#         # Get the server information with a dialog.
#         server_dialog = ServerDialog(self, title='Server Connection')
#         self.wait_window(server_dialog)

#         # Halt initialisation and close the application on a cancel.
#         if server_dialog.result is None:
#             self.destroy()
#             return
        
#         # # # Otherwise, initialise the server context.
#         # self.server_interface = server_interface.ServerInterface(
#         #     host=server_dialog.result['ip_address'],
#         #     port=int(server_dialog.result['port_number']),
#         #     signature_key=self.signature_key,
#         # )

#         # Restore the main window and render all children.
#         self.deiconify()
#         self.body = Body(
#             master=self,
#             engine=self.engine,
#             signature_key=self.signature_key,
#             settings=None,
#         )
#         self.body.grid(column=0, row=0, sticky='nsew', padx=5, pady=5)
#         self.grid_columnconfigure(0, weight=1)
#         self.grid_rowconfigure(0, weight=1)

#         # Set up the task manager.
#         # self.task_manager = TaskManager(
#         #     master=self,
#         #     engine=self.engine,
#         #     signature_key=self.signature_key,
#         #     frequency_ms=300,
#         # )

#         # Test
#         # from base64 import b64encode
#         # data = {
#         #     'command': 'SEND_MESSAGE2',
#         #     'recipient_public_key': 'rwaj4ykXFOTzVsGcmxXNGVHsbmZiqne+B1R/KJODNB0=',
#         #     'encrypted_message': 'Main app calling Kirby.',
#         #     'signature': b64encode(self.signature_key.sign('Main app calling Kirby.'.encode())).decode(),
#         # }
#         # response = self.server_context.send_request(data)
#         # print(response)
#     def _tasks(self):
#         server_interface.retrieve_messages(
#             url=RETRIEVE_MESSAGES_URL,
#             engine=self.engine,
#             public_key=self.base64_public_key,
#             contact_dict=self.contact_dict,
#             min_datetime=None,
#         )
#         # retrieval_data: dict[str, Any] = {
#         #     'public_key': self.base64_public_key,
#         # }
#         # response = requests.post(
#         #     url=RETRIEVE_MESSAGES_URL,
#         #     json=retrieval_data,
#         # )
#         # print(response.json())
#         # response = requests.post(
#         #     url=RETRIEVE_KEY_EXCHANGES_URL,
#         #     json=retrieval_data,
#         # )
#         # print(response.json())
#         self.after(SERVER_RETRIEVE_REFRESH_TIME, self._tasks)

#         pass

# if __name__ == '__main__':
#     Application().mainloop()
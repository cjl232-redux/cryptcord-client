from sqlalchemy import event
import logging

logging.basicConfig()
logger = logging.getLogger("sqlalchemy.explain")
logger.setLevel(logging.INFO)

def explain_query(conn, cursor, statement, parameters, context, executemany):
    if statement.lstrip().upper().startswith("SELECT"):
        try:
            explain_stmt = f"EXPLAIN QUERY PLAN {statement}"
            cursor.execute(explain_stmt, parameters)
            plan = cursor.fetchall()
            logger.info("Query: %s", statement)
            logger.info("Parameters: %s", parameters)
            logger.info("EXPLAIN plan:")
            for row in plan:
                logger.info(row)
        except Exception as e:
            logger.warning("EXPLAIN failed: %s", e)


# TODO consider contact field for last fetch (probably bad idea)
# TODO streamline database querying
# New thought: persistent session for each window
# Also seems bad though

import tkinter as tk

from base64 import urlsafe_b64decode
from tkinter import messagebox

import httpx

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError as SQLAlchemyArgumentError

from app_components.body import Body
from app_components.dialogs.key_dialogs import SignatureKeyDialog
from database.models import Base as BaseDatabaseModel
from database.operations.operations import create_fernet_keys
from server.operations import (
    post_pending_exchange_keys,
    fetch_data,
)
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
            event.listen(self.engine, "before_cursor_execute", explain_query)
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
            self.signature_key = signature_key_dialog.result.signature_key
        else:
            self.destroy()
            return
        # Set up an indicator of server connection.
        self.connected = False
        # Create a HTTP client to use in requests.
        self.http_client = httpx.Client()
        # Create and place the application body.
        body = Body(self, self.engine, self.signature_key, self.http_client)
        body.grid(column=0, row=0, sticky='nsew')
        # Configure grid properties.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        # Restore the window.
        self.deiconify()
        # Set up repeating calls.
        print('starting local ops')
        self.local_operations()
        print('starting server ops')
        self.server_retrieval()
        print('finished ops')

    def local_operations(self):
        create_fernet_keys(self.engine)
        self.after(
            int(settings.functionality.local_operations_interval * 1000),
            self.local_operations,
        )

    def server_retrieval(self):
        try:
            fetch_data(
                self.engine,
                self.signature_key,
                self.http_client,
            )
            post_pending_exchange_keys(
                self.engine,
                self.signature_key,
                self.http_client,
            )
        except httpx.ConnectError:
            pass
        self.after(
            int(settings.functionality.server_retrieval_interval * 1000),
            self.server_retrieval,
        )


if __name__ == '__main__':
    Application().mainloop()
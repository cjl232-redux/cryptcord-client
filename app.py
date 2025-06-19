import os
import time
import tkinter as tk

from threading import Thread
from tkinter import messagebox

import httpx

from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError as SQLAlchemyArgumentError

from app_components.body import Body
from app_components.dialogs.key_dialogs import SignatureKeyDialog
from database.models import Base as BaseDatabaseModel
from database.operations.fernet_keys import create_fernet_keys
from server.operations import (
    check_connection,
    post_initial_contact_keys,
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
        # Create a HTTP client to use in requests.
        self.http_client = httpx.Client(
            timeout=settings.server.request_timeout,
        )
        # Set up an indicator of server connection.
        self.connected = check_connection(self.http_client)
        # Create and place the application body.
        self.body = Body(
            master=self,
            engine=self.engine,
            signature_key=self.signature_key,
            http_client=self.http_client,
            connected=self.connected,
        )
        self.body.grid(column=0, row=0, sticky='nsew')
        # Configure grid properties.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        # Set up the exit protocol.
        self.protocol('WM_DELETE_WINDOW', self._on_close)
        # Set up repeating calls.
        self.server_thread = Thread(target=self.operations, daemon=True)
        self.server_thread.start()
        # Restore the window.
        self.deiconify()

    def operations(self):
        while self.winfo_exists():
            try:
                if self.connected:
                    fetch_data(
                        self.engine,
                        self.signature_key,
                        self.http_client,
                    )
                    post_initial_contact_keys(
                        self.engine,
                        self.signature_key,
                        self.http_client,
                    )
                    post_pending_exchange_keys(
                        self.engine,
                        self.signature_key,
                        self.http_client,
                    )
                else:
                    self.connected = check_connection(self.http_client)
            except httpx.NetworkError:
                self.connected = False
            create_fernet_keys(self.engine)
            self.body.set_connection_display(self.connected)
            time.sleep(settings.server.operations_sleep)
    
    def _on_close(self):
        path = f'{settings.local_database.url}-journal'
        if os.path.exists(path):
            os.remove(path)



if __name__ == '__main__':
    Application().mainloop()
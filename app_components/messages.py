import tkinter as tk

from datetime import datetime
from tkinter import messagebox, ttk
from zoneinfo import ZoneInfo

import httpx

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from app_components.scrollable_frames import ScrollableFrame
from database.models import Message, MessageType
from database.schemas.output import (
    ContactOutputSchema,
    MessageOutputSchema,
)
from server.exceptions import ClientError, ServerError
from server.operations import check_connection, post_message
from settings import settings

class MessageWindow(tk.Toplevel):
    def __init__(
            self,
            master: tk.Widget | tk.Tk | tk.Toplevel,
            engine: Engine,
            signature_key: Ed25519PrivateKey,
            http_client: httpx.Client,
            contact: ContactOutputSchema,
        ):
        # Call the TopLevel constructor.
        super().__init__(master)
        # Rename the window to the contact name.
        self.title(contact.name)
        # Store supplied values that are required for methods.
        self.engine = engine
        self.signature_key = signature_key
        self.contact = contact
        self.http_client = http_client
        # Store metadata on loaded messages.
        self.loaded_nonces: list[str] = list()
        self.last_message_timestamp = datetime.min
        # Create and place widgets.
        self.message_log = ScrollableFrame(self)
        self.message_log.grid(
            column=0,
            row=0,
            padx=settings.graphics.horizontal_padding,
            pady=settings.graphics.vertical_padding,
            sticky='nsew',
        )
        self.input_box = tk.Text(
            self,
            height=2,
            font=(
                settings.graphics.font_family,
                settings.graphics.font_size,
            ),
        )
        self.input_box.grid(
            column=0,
            row=1,
            padx=settings.graphics.horizontal_padding,
            pady=(0, settings.graphics.vertical_padding),
            sticky='nsew',
        )
        # Configure grid properties.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.message_log.interior.columnconfigure(1, weight=1, minsize=100)
        # Load in existing messages and set up regular updates.
        self._update_message_log()
        # Finalise and focus on the input box.
        self.input_box.focus()
        self.input_box.bind('<Return>', self._post_message)
        self.input_box.bind('<Shift-Return>', lambda *_: None)

    def _update_message_log(self):
        query = (
            select(Message)
            .where(Message.contact_id == self.contact.id)
            .where(Message.timestamp >= self.last_message_timestamp)
            .where(~Message.nonce.in_(self.loaded_nonces))
        )
        with Session(self.engine) as session:
            messages = (
                MessageOutputSchema.model_validate(message)
                for message in session.scalars(query)
            )
            for message in messages:
                row = len(self.loaded_nonces)
                if row == 0:
                    pady = 0
                else:
                    pady = (settings.graphics.vertical_padding, 0)

                author_label = ttk.Label(
                    master=self.message_log.interior,
                    anchor='nw',
                    font=settings.get_font_bold(),
                )
                if message.message_type == MessageType.SENT.value:
                    author_label.config(text='You:')
                else:
                    author_label.config(text=f'{self.contact.name}:')
                author_label.grid(column=0, row=row, sticky='nw', pady=pady)

                message_label = ttk.Label(
                    master=self.message_log.interior,
                    text=message.text,
                    font=settings.get_font(),
                    anchor='nw',
                )
                message_label.bind(
                    sequence='<Configure>',
                    func=(
                        lambda _, label=message_label:
                            label.config(
                                wraplength=label.winfo_width() - 5,
                            )
                    )
                )
                message_label.grid(
                    column=1,
                    row=len(self.loaded_nonces),
                    sticky='nsew',
                    ipadx=settings.graphics.horizontal_padding,
                    padx=settings.graphics.horizontal_padding,
                    pady=pady,
                )

                datetime_label = ttk.Label(
                    master=self.message_log.interior,
                    text=message.timestamp.astimezone(
                        ZoneInfo('Europe/London'),
                    ).strftime(
                        '%Y-%m-%d %H:%M',
                    ),
                    font=settings.get_font(),
                    anchor='nw',
                )
                datetime_label.grid(column=2, row=row, sticky='nw', pady=pady)
                self.loaded_nonces.append(hex(message.nonce))
                self.last_message_timestamp = message.timestamp
        self.after(
            ms=int(settings.functionality.message_refresh_rate * 1000),
            func=self._update_message_log,
        )
    
    def _post_message(self, *_):
        """
        Post a message to the contact.

        If the input box contains text, then encrypt it using a Fernet key,
        assemble and send a post request, then store the message using the
        response timestamp and nonce.
        """
        # Retrieve the message text and ensure it isn't empty.
        plaintext = self.input_box.get('1.0', tk.END).rstrip()
        if not plaintext:
            self.input_box.delete('1.0', tk.END)
            return 'break'
        try:
            if not check_connection(self.http_client):
                raise httpx.ConnectError('')
            post_message(
                self.engine,
                self.signature_key,
                self.http_client,
                plaintext,
                self.contact,
            )
            self._update_message_log()
            self.input_box.delete('1.0', tk.END)
        except httpx.ConnectError:
            messagebox.showerror(
                title='Connection Error',
                message='Post failed: the server could not be reached.',
            )
        except ClientError as e:
            messagebox.showerror(
                title='Client Error',
                message=f'Post failed: {str(e)}.',
            )
        except ServerError as e:
            messagebox.showerror(
                title='Server Error',
                message=f'Post failed: {str(e)}.',
            )
        finally:
            self.input_box.focus()
        return 'break'
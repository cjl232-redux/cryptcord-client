import os
import tkinter as tk
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from tkinter import filedialog, messagebox, ttk

# TODO: Unlike the below, actually todo - enforce ed25519 on key load

# TODO: rework validation. Should be done on clicking submit for encrypted
# and put up a message if failed. Alternatively: just go through to the password entry?
# Sadly, I think that's smarter... I'll implement this soon
# Although... now that I'm thinking this through, maybe I should genuinely
# Keep the current approach on each startup?
# Yeah, I'm happier with that. Maybe just make it conditional on whether there's
# An existing filepath, the label, that is. More detailed description if there's no (valid) key path in the settings
# That lets me keep this thing I'm fond of, as long as I change the validation.

class _SignatureKeyEntryFrame(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.file_path_header_label = ttk.Label(
            master=self,
            text='File Path:',
        )
        self.file_path_header_label.grid(
            column=0,
            row=0,
            sticky='w',
            padx=(0, 5),
        )
        self.file_path_content_label = ttk.Label(
            self,
            text='No file selected.',
            borderwidth=2,
            relief='solid',
            anchor='w',
        )
        self.file_path_content_label.grid(
            column=1,
            row=0,
            sticky='nesw',
            padx=(5, 5),
        )
        self.browse_button = ttk.Button(self, text='Browse...')
        self.browse_button.grid(column=2, row=0, padx=(5, 0))
        self.invalid_file_warning = ttk.Label(
            master=self,
            text='The selected file is in an invalid format.',
            foreground='red',
        )
        self.missing_file_warning = ttk.Label(
            master=self,
            text='The selected file could not be found.',
            foreground='red',
        )
        self.password = tk.StringVar()
        self.password_label = ttk.Label(self, text='Password:')
        self.password_entry = ttk.Entry(
            master=self,
            show='•',
            textvariable=self.password,
        )
        self.show_password = tk.BooleanVar(self)
        self.show_password_button = ttk.Button(
            master=self,
            text='Show/Hide',
            command=self.toggle_password_visibility,
        )
        self.show_password.trace_add('write', self.update_password_visibility)
        self.columnconfigure(1, weight=1)

    def toggle_password_visibility(self):
        self.show_password.set(not self.show_password.get())

    def update_password_visibility(self, var, index, mode):
        if self.show_password.get():
            self.password_entry.config(show='')
        else:
            self.password_entry.config(show='•')

    def show_password_entry(self):
        self.show_password.set(False)
        self.password_entry.delete(0, tk.END)
        self.password_label.grid(
            column=0,
            row=1,
            sticky='w',
            padx=(0, 5),
            pady=(10, 0),
        )
        self.password_entry.grid(
            column=1,
            row=1,
            sticky='we',
            padx=(5, 5),
            pady=(10, 0),
        )
        self.show_password_button.grid(
            column=2,
            row=1,
            sticky='w',
            padx=(5, 0),
            pady=(10, 0),
        )
    
    def hide_password_entry(self):
        self.password_entry.delete(0, tk.END)
        self.password_label.grid_forget()
        self.password_entry.grid_forget()
        self.show_password_button.grid_forget()

    def show_invalid_file_warning(self):
        self.invalid_file_warning.grid(
            column=0,
            row=1,
            columnspan=3,
            sticky='we',
            pady=(10, 0),
        )

    def hide_invalid_file_warning(self):
        self.invalid_file_warning.grid_forget()

    def show_missing_file_warning(self):
        self.missing_file_warning.grid(
            column=0,
            row=1,
            columnspan=3,
            sticky='we',
            pady=(10, 0)
        )

    def hide_missing_file_warning(self):
        self.missing_file_warning.grid_forget()

class _FooterButtonFrame(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.submit_button = ttk.Button(self, text='Submit', state='disabled')
        self.submit_button.grid(column=1, row=0, sticky='se', padx=(0, 5))
        self.cancel_button = ttk.Button(self, text='Cancel')
        self.cancel_button.grid(column=2, row=0, sticky='se', padx=(5, 0))
        self.columnconfigure(index=0, weight=1)

class SignatureKeyDialog(tk.Toplevel):
    def __init__(self, master, file_path : str = None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.grab_set()
        self.file_path = file_path
        self.signature_key = None
        self.title('Signature Key')
        self.protocol('WM_DELETE_WINDOW', self.cancel)
        self.intro_text = ttk.Label(
            master=self,
            text=(
                'Using this program requires a private signature key. This '
                'will allow your contacts to confirm your identity when '
                'receiving messages and establishing shared encryption keys. '
                'If you already have one, please select a PEM-encoded '
                'serialialisation of the private key, providing the password '
                'if it is encrypted. Otherwise, please generate and '
                'serialise a key pair, provide your contacts with the public '
                'key, then select the private key.'
            ),
            wraplength=600,
        )
        self.entry_frame = _SignatureKeyEntryFrame(self)
        self.entry_frame.browse_button.config(command=self.browse)
        self.footer_button_frame = _FooterButtonFrame(self)
        self.footer_button_frame.submit_button.config(command=self.submit)
        self.footer_button_frame.cancel_button.config(command=self.cancel)

        # Arrange overall dialog layout:
        self.intro_text.grid(
            column=0,
            row=0,
            sticky='nw',
            padx=10,
            pady=(10, 5),
        )
        self.entry_frame.grid(
            column=0,
            row=1,
            sticky='we',
            padx=10,
            pady=(5, 5),
        )
        self.footer_button_frame.grid(
            column=0,
            row=2,
            sticky='swe',
            padx=10,
            pady=(5, 10),
        )
        self.columnconfigure(index=0, weight=1)
        self.rowconfigure(index=2, weight=1)

        # If an existing file path exists, check it.
        if self.file_path is not None:
            self.check_file_path()

    def check_file_path(self):
        self.entry_frame.file_path_content_label.config(text=self.file_path)
        self.entry_frame.hide_invalid_file_warning()
        self.entry_frame.hide_missing_file_warning()
        self.entry_frame.hide_password_entry()
        self.footer_button_frame.submit_button.config(state='disabled')
        self.unbind('<Return>')
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'rb') as file:
                    key_data = file.read()
                self.signature_key = load_pem_private_key(key_data, None)
                self.footer_button_frame.submit_button.config(state='normal')
                self.bind('<Return>', self.submit)
            except TypeError:
                self.entry_frame.show_password_entry()
                self.entry_frame.password_entry.focus()
                self.footer_button_frame.submit_button.config(state='normal')
                self.bind('<Return>', self.submit)
            except:
                self.entry_frame.show_invalid_file_warning()
        else:
            self.entry_frame.show_missing_file_warning()

    def browse(self):
        # Adjust this to have a separate file handler that gets
        # called on construction if settings has one. Add return bind to TypeError
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path = file_path
            self.check_file_path()
    
    def submit(self, _ = None):
        if self.file_path:
            try:
                password = None
                if self.entry_frame.password_entry.get():
                    password = self.entry_frame.password_entry.get().encode()
                with open(self.file_path, 'rb') as file:
                    key_data = file.read()
                self.signature_key = load_pem_private_key(key_data, password)            
                self.destroy()
            except:
                if self.entry_frame.password_entry.grid_info():
                    messagebox.showerror(
                        title='Incorrect Password',
                        message='The provided password is incorrect.',
                    )
                    self.entry_frame.password_entry.focus()
                    self.entry_frame.password_entry.delete(0, tk.END)
                else:
                    messagebox.showerror(
                        title='Load Error',
                        message=(
                            'The specified key could not be loaded. This '
                            'usually means it has been moved, deleted, or '
                            'modified on disk.'
                        ),
                    )
        else:
            messagebox.showerror(
                title='Missing File Path',
                message='No file path has been provided.',
            )

    def cancel(self):
        self.file_path = None
        self.signature_key = None
        self.destroy()

class PasswordEntryDialog(tk.Toplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.private_key = None
        self.title('Signature Key Password')
        self.label = ttk.Label(
            master=self,
            text='Please enter the password to decrypt your signature key.',
        )
        self.label.grid(column=0, row=0, columnspan=2)
        self.password_entry = ttk.Entry(self, show='•')
        self.password_entry.grid(column=0, row=1, sticky='ew')
        self.show_password = tk.BooleanVar(self)
        self.show_password_button = ttk.Button(
            master=self,
            text='Show/Hide',
            command=self.toggle_password_visibility,
        )
        self.show_password_button.grid(column=1, row=1)
        self.submit_button = ttk.Button(
            master=self,
            text='Submit',
            command=self.submit,
        )
        self.submit_button.grid(column=0, row=2, sticky='e')
        self.cancel_button = ttk.Button(
            master=self,
            text='Cancel',
            command=self.cancel,
        )
        self.cancel_button.grid(column=1, row=2)
        self.columnconfigure(0, weight=1)
        self.protocol('WM_DELETE_WINDOW', self.cancel)

    def toggle_password_visibility(self):
        self.show_password.set(not self.show_password.get())
        if self.show_password.get():
            self.password_entry.config(show='')
        else:
            self.password_entry.config(show='•')

    def submit(self):
        pass

    def cancel(self):
        self.private_key = None
        self.destroy()

import tkinter as tk

from dataclasses import dataclass
from tkinter import messagebox, ttk
from typing import Callable

from app_components.dialogs import fields

@dataclass
class DescriptionData:
    text: str
    wrap_length: int | None = None

type Validator = Callable[[dict[str, str]], str | None]

class Dialog(tk.Toplevel):
    def __init__(
            self,
            master,
            title: str,
            description_data: DescriptionData = None,
            fields: dict[str, fields.Field] = None,
            validators: list[Validator] = None,
            x_padding: int = 6,
            y_padding: int = 2,
            *args,
            **kwargs,
        ):
        # Call the base constructor.
        super().__init__(master, *args, **kwargs)

        # Fill in default lists and dicts.
        if fields is None:
            fields = {}
        if validators is None:
            validators = []

        # Grab all incoming events and set window properties.
        self.grab_set()
        self.title(title)
        self.protocol('WM_DELETE_WINDOW', self._cancel)

        # Track the current row.
        row = 0
        
        # If provided, place the description text.
        if description_data is not None:
            label = ttk.Label(
                master=self,
                text=description_data.text,
                wraplength=description_data.wrap_length,
            )
            label.grid(
                column=0,
                row=row,
                columnspan=3,
                sticky='new',
                padx=x_padding,
                pady=(y_padding, y_padding // 2),
            )
            row += 1
        
        # Create and place widgets for each field.
        first_field = True
        self.stringvars: dict[str, tk.StringVar] = {}
        for key, field in fields.items():
            label, entry, button, var = field.load_widgets(self)
            entry.bind('<Return>', lambda _: self._submit())
            if first_field:
                entry.focus()
                first_field = False
            label.grid(
                column=0,
                row=row,
                sticky='w',
                padx=(
                    x_padding,
                    x_padding // 2,
                ),
                pady=(
                    y_padding if row == 0 else y_padding // 2,
                    y_padding // 2,
                ),
            )
            entry.grid(
                column=1,
                row=row,
                sticky='ew',
                padx=(
                    x_padding // 2,
                    x_padding // 2,
                ),
                pady=(
                    y_padding if row == 0 else y_padding // 2,
                    y_padding // 2,
                ),
            )
            if button is not None:
                button.grid(
                    column=2,
                    row=row,
                    sticky='ew',
                    padx=(
                        x_padding // 2,
                        x_padding,
                    ),
                    pady=(
                        y_padding if row == 0 else y_padding // 2,
                        y_padding // 2,
                    ),
                )
            self.stringvars[key] = var
            row += 1

        # Add in command buttons.
        submit_button = ttk.Button(self, text='Submit', command=self._submit)
        submit_button.grid(
            column=1,
            row=row,
            sticky='e',
            padx=(0, x_padding // 2),
            pady=(y_padding if row == 0 else y_padding // 2, y_padding),
        )
        submit_button.bind('<Return>', lambda _: self._submit())
        cancel_button = ttk.Button(self, text='Cancel', command=self._cancel)
        cancel_button.grid(
            column=2,
            row=row,
            sticky='ew',
            padx=(x_padding // 2, x_padding),
            pady=(y_padding if row == 0 else y_padding // 2, y_padding),
        )
        cancel_button.bind('<Return>', lambda _: self._cancel())

        # Configure the grid.
        self.columnconfigure(1, weight=1)

        # Store provided validators.
        self.validators = validators
        if self.validators is None:
            self.validators = []

    def _submit(self, *_):
        result = {x: y.get() for x, y in self.stringvars.items()}
        errors: list[str] = []
        for validator in self.validators:
            message = validator(result)
            if message:
                errors.append(message)
        if len(errors) == 1:
            messagebox.showerror(
                title='Validation Error',
                message=errors[0],
            )
            self.result = None
        elif errors:
            message = f'The following errors occured:\n{'\n• '.join(errors)}'
            messagebox.showerror(
                title='Validation Error',
                message=message,
            )
            self.result = None
        else:
            self.result = result
            self.destroy()

    def _cancel(self, *_):
        self.result = None
        self.destroy()
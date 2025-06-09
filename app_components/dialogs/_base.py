
import tkinter as tk

from tkinter import messagebox, ttk
from typing import Any, Callable

from pydantic import BaseModel

from app_components.dialogs import fields

# @dataclass
# class DescriptionData:
#     text: str
#     wrap_length: int | None = ...

type Validator = Callable[[dict[str, str]], str | None]

class Dialog(tk.Toplevel):
    def __init__(
            self,
            master: tk.Widget | tk.Tk | tk.Toplevel,
            title: str,
            description_kwargs: dict[str, Any] | None = None,
            fields: dict[str, fields.Field] | None = None,
            validators: list[Validator] | None = None,
            x_padding: int = 6,
            y_padding: int = 2,
            input_schema: type[BaseModel] | None = None,
        ):
        # Call the base constructor.
        super().__init__(master)
        self.input_schema = input_schema

        # Fill in default lists and dicts, then store the validators.
        if description_kwargs is None:
            description_kwargs = {}
        if fields is None:
            fields = {}
        if validators is None:
            validators = []
        self.validators = validators

        # Grab all incoming events and set window properties.
        self.grab_set()
        self.title(title)
        self.protocol('WM_DELETE_WINDOW', self._cancel)
        
        # If provided, place the description text.
        if 'text' in description_kwargs:
            label = ttk.Label(self, **description_kwargs)
            label.grid(
                column=0,
                row=0,
                columnspan=3,
                sticky='new',
                padx=x_padding,
                pady=(y_padding, y_padding // 2),
            )

        # Create and place all the relevant widgets.
        self.stringvars: dict[str, tk.StringVar] = {}
        start_row = int('text' in description_kwargs)
        for row, (key, field) in enumerate(fields.items(), start_row):
            label, entry, button, var = field.load_widgets(self)
            entry.bind('<Return>', lambda _: self._submit())
            if row == start_row:
                entry.focus()
            row_ypad = (
                y_padding if row == 0 else y_padding // 2,
                y_padding // 2,
            )
            label.grid(
                column=0,
                row=row,
                sticky='w',
                padx=(x_padding, x_padding // 2),
                pady=row_ypad,
            )
            entry.grid(
                column=1,
                row=row,
                sticky='ew',
                padx=(x_padding // 2, x_padding // 2),
                pady=row_ypad,
            )
            if button is not None:
                button.grid(
                    column=2,
                    row=row,
                    sticky='ew',
                    padx=(x_padding // 2, x_padding),
                    pady=row_ypad,
                )
            self.stringvars[key] = var

        # Add in command buttons.
        end_row = start_row + len(self.stringvars)
        end_row_ypad = (
            y_padding if end_row == 0 else y_padding // 2,
            y_padding,
        )
        submit_button = ttk.Button(self, text='Submit', command=self._submit)
        submit_button.grid(
            column=1,
            row=end_row,
            sticky='e',
            padx=(0, x_padding // 2),
            pady=end_row_ypad,
        )
        submit_button.bind('<Return>', lambda _: self._submit())
        cancel_button = ttk.Button(self, text='Cancel', command=self._cancel)
        cancel_button.grid(
            column=2,
            row=end_row,
            sticky='ew',
            padx=(x_padding // 2, x_padding),
            pady=end_row_ypad,
        )
        cancel_button.bind('<Return>', lambda _: self._cancel())

        # Configure the grid.
        self.columnconfigure(1, weight=1)


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
            try:
                if self.input_schema is not None:
                    self.result = self.input_schema.model_validate(result)
                else:
                    self.result = result
                self.destroy()
            except Exception as e:
                messagebox.showerror(title='Validation Error', message=str(e))


    def _cancel(self, *_):
        self.result = None
        self.destroy()
# Use NOTIMPLEMENTEDERROR
# TODO work out how to type hint providing a default model instance. Maybe use isinstance with the registered type.

import tkinter as tk

from dataclasses import dataclass
from tkinter import messagebox, ttk
from typing import Any, Callable

from pydantic import BaseModel, ValidationError
from pydantic_core import PydanticUndefined

from settings import settings

def _print_value(_: tk.Entry, v: tk.StringVar):
    print(v.get())

@dataclass
class FieldButtonData:
    text: str = 'Click Me!'
    callable: Callable[[tk.Entry, tk.StringVar], None] = _print_value

@dataclass
class FieldPropertiesData:
    hidden: bool = True


class _DescriptionFrame(ttk.Frame):
    def __init__(self, master: 'BaseDialog[Any]', text: str):
        super().__init__(master)
        self.label = ttk.Label(
            self,
            text=text,
            anchor='nw',
            wraplength=settings.graphics.dialogs.description_wrap_length,
        )
        if text:
            self.label.grid(
                column=0,
                row=0,
                sticky='nsew',
                padx=settings.graphics.dialogs.horizontal_padding,
                pady=(settings.graphics.dialogs.vertical_padding, 0),
            )
            self.label.bind('<Configure>', self._adjust_wrap)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
    
    def _adjust_wrap(self, event: tk.Event): # type: ignore
        self.label.config(wraplength=event.width)


class _FieldsFrame(ttk.Frame):
    def __init__(self, master: 'BaseDialog[Any]', model: type[BaseModel]):
        # Call the base constructor.
        super().__init__(master)
        # Alias the padding settings.
        horizontal_padding = settings.graphics.dialogs.horizontal_padding
        vertical_padding = settings.graphics.dialogs.vertical_padding
        field_padding = settings.graphics.dialogs.field_gap
        # Create a dict to hold variables and a list to hold entry widgets.
        self.entries: list[ttk.Entry] = list()
        self.variables: dict[str, tk.StringVar] = dict()
        # Create the body for each model field.
        for i, (key, value) in enumerate(model.model_fields.items()):
            row_padding = (vertical_padding if i == 0 else field_padding, 0)
            label = ttk.Label(
                master=self,
                text=key,
                anchor='w',
                font=(
                    settings.graphics.font_family,
                    settings.graphics.font_size,
                    'bold',
                ),
            )
            if value.title:
                label.config(text=f'{value.title}:')
            label.grid(
                column=0,
                row=i,
                sticky='w',
                padx=(horizontal_padding, 0),
                pady=row_padding,
            )
            self.variables[key] = tk.StringVar(
                self,
                value.default if value.default != PydanticUndefined else None,
            )
            entry = ttk.Entry(self, textvariable=self.variables[key])
            entry.grid(
                column=1,
                row=i,
                sticky='ew',
                padx=horizontal_padding,
                pady=row_padding,
            )
            if i == 0:
                entry.focus()
            self.entries.append(entry)
            for metadata in value.metadata:
                if isinstance(metadata, FieldPropertiesData):
                    if metadata.hidden:
                        entry.config(show='●')
                elif isinstance(metadata, FieldButtonData):
                    var = self.variables[key]
                    button = ttk.Button(
                        master=self,
                        text=metadata.text,
                        command=(
                            lambda e=entry, v=var, metadata=metadata:
                                metadata.callable(e, v)
                        ),
                    )
                    button.bind(
                        sequence='<Return>',
                        func=(
                            lambda *_, e=entry, v=var, metadata=metadata:
                                metadata.callable(e, v)
                        ),
                    )
                    button.grid(
                        column=2,
                        row=i,
                        sticky='ew',
                        padx=(0, horizontal_padding),
                        pady=row_padding,
                    )
        # Set grid parameters.
        self.columnconfigure(1, weight=1)


class _ButtonFrame(ttk.Frame):
    def __init__(self, master: 'BaseDialog[Any]'):
        super().__init__(master)
        self.submit_button = ttk.Button(self, text='Submit')
        self.submit_button.grid(
            column=0,
            row=0,
            sticky='w',
            padx=settings.graphics.dialogs.horizontal_padding,
            pady=settings.graphics.dialogs.vertical_padding,
        )
        self.cancel_button = ttk.Button(self, text='Cancel')
        self.cancel_button.grid(
            column=1,
            row=0,
            sticky='w',
            padx=(0, settings.graphics.dialogs.horizontal_padding),
            pady=settings.graphics.dialogs.vertical_padding,
        )        
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

class BaseDialog[T: BaseModel](tk.Toplevel):
    TITLE: str = 'Dialog'
    DESCRIPTION: str = ''
    VALIDATION_MODEL: type[T] | None = None

    def __init__(self, master: tk.Widget | tk.Tk | tk.Toplevel):
        # Call the base constructor.
        super().__init__(master)
        # Confirm there is a validation model.
        if self.VALIDATION_MODEL is None:
            raise NotImplementedError(
                'Subclasses must implement a VALIDATION_MODEL attribute.',
            )
        # Set window properties and disable resizing.
        self.title(self.TITLE)
        self.protocol('WM_DELETE_WINDOW', self._cancel)
        # Focus the window and grab all incoming events.
        self.focus()
        self.grab_set()
        # Create and place the body elements.
        description_frame = _DescriptionFrame(self, self.DESCRIPTION)
        description_frame.grid(column=0, row=0, sticky='nsew')
        self._fields_frame = _FieldsFrame(self, self.VALIDATION_MODEL)
        self._fields_frame.grid(column=0, row=1, sticky='nsew')
        button_frame = _ButtonFrame(self)
        button_frame.submit_button.config(command=self._submit)
        button_frame.cancel_button.config(command=self._cancel)
        button_frame.grid(column=0, row=2, sticky='nsew')
        # Bind the enter key to the submit function for all fields.
        for entry in self._fields_frame.entries:
            entry.bind('<Return>', self._submit)
        # Bind the enter key for the submit and cancel buttons.
        button_frame.submit_button.bind('<Return>', self._submit)
        button_frame.cancel_button.bind('<Return>', self._cancel)
        # Configure grid properties.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
    
    def _submit(self, *_):
        assert self.VALIDATION_MODEL is not None
        values = {
            key: value.get()
            for key, value in self._fields_frame.variables.items()
            if value.get()
        }
        try:
            self.result = self.VALIDATION_MODEL.model_validate(values)
            self.destroy()
        except ValidationError as e:
            text = 'The following errors occured:'
            for error in e.errors():
                error['msg'] = error['msg'].replace('Value error, ', '')
                text += (
                    f'\n{str(error['loc'][0]).replace('_', ' ').title()}: '
                    f'{error['msg'][0].lower()}{error['msg'][1:]}.'
                )
            messagebox.showerror('Error', text)

    def _cancel(self, *_):
        self.result = None
        self.destroy()
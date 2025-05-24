from dataclasses import dataclass
from typing import Callable
import tkinter as tk
from tkinter import filedialog, ttk
from app_components import dialogs

@dataclass
class ButtonData:
    text: str
    command: Callable[['Field', ttk.Entry, tk.StringVar], None]


class Field:
    def __init__(
            self,
            name: str,
            default: str = None,
            read_only: bool = False,
            button_data: ButtonData = None,            
        ):
        self.name = name
        self.default = default
        self.read_only = read_only
        self.button_data = button_data

    def load_widgets(
            self,
            dialog,
        ) -> tuple[ttk.Label, ttk.Entry, ttk.Button | None, tk.StringVar]:
        var = tk.StringVar(dialog, value=self.default)
        label = ttk.Label(dialog, text=f'{self.name}:')
        entry = ttk.Entry(dialog, textvariable=var)
        if self.read_only:
            entry.config(state='disabled')
        if self.button_data is not None:
            command = self.button_data.command
            bound_command = lambda x=self, y=entry, z=var: command(x, y, z)
            button = ttk.Button(
                master=dialog,
                text=self.button_data.text,
                command=bound_command,
            )
            button.bind('<Return>', lambda _: bound_command())
        else:
            button = None
        return label, entry, button, var
    
class PasswordField(Field):
    def __init__(self, name: str = 'Password', *args, **kwargs):
        super().__init__(
            name=name,
            button_data=self._button_data,
            *args,
            **kwargs,
        )
    
    def load_widgets(
            self,
            dialog,
        ) -> tuple[ttk.Label, ttk.Entry, ttk.Button | None, tk.StringVar]:
        label, entry, button, var = super().load_widgets(dialog)
        entry.config(show='●')
        return label, entry, button, var

    def _toggle_visibility(entry: ttk.Entry, _: tk.StringVar):
        entry.config(show='●' if entry.cget('show') == '' else '')
        entry.focus()

    _button_data = ButtonData('Show/Hide', _toggle_visibility)

class FilePathField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(button_data=self._button_data, *args, **kwargs)

    def _browse(_: ttk.Entry, variable: tk.StringVar):
        variable.set(filedialog.askopenfilename())

    _button_data = ButtonData('Browse...', _browse)

from dataclasses import dataclass
from typing import Callable
import tkinter as tk
from tkinter import ttk

@dataclass
class ButtonData:
    text: str
    command: Callable[['Field', ttk.Entry, tk.StringVar], None]



class Field:
    def __init__(
            self,
            name: str,
            default: str | None = None,
            read_only: bool = False,
            button_data: ButtonData | None = None,
            hide_input: bool = False,
        ):
        self.name = name
        self.default = default
        self.read_only = read_only
        self.button_data = button_data
        self.hide_input = hide_input

    def load_widgets(
            self,
            dialog: tk.Toplevel,
        ) -> tuple[ttk.Label, ttk.Entry, ttk.Button | None, tk.StringVar]:
        var = tk.StringVar(dialog, value=self.default)
        label = ttk.Label(dialog, text=f'{self.name}:')
        entry = ttk.Entry(dialog, textvariable=var)
        if self.read_only:
            entry.config(state='disabled')
        if self.hide_input:
            entry.config(show='●')
        if self.button_data is not None:
            command = self.button_data.command
            bound_command = lambda x=self, y=entry, z=var: command(x, y, z)
            button = ttk.Button(
                master=dialog,
                text=self.button_data.text,
                command=bound_command,
            )
            button.bind('<Return>', lambda *_: bound_command())
        else:
            button = None
        return label, entry, button, var

    
class PasswordField(Field):
    def __init__(self, name: str = 'Password'):
        super().__init__(
            name=name,
            button_data=ButtonData('Show/Hide', self._toggle_visibility),
            hide_input=True,
        )

    @staticmethod
    def _toggle_visibility(field: Field, entry: ttk.Entry, _: tk.StringVar):
        entry.config(show='●' if entry.cget('show') == '' else '')
        entry.focus()
    

# class FilePathField(Field):
#     def __init__(self, *args, **kwargs):
#         super().__init__(button_data=self._button_data, *args, **kwargs)

#     def _browse(self, _: ttk.Entry, variable: tk.StringVar):
#         variable.set(filedialog.askopenfilename())

#     _button_data = ButtonData('Browse...', _browse)
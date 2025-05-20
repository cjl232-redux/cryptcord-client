from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List, Dict


class Validator:
    def __init__(self, test: Callable[[str], bool], message: str) -> None:
        self.test = test
        self.message = message
        self.is_valid: bool = False
        self._label: Optional[ttk.Label] = None

    def attach_to(self, parent: tk.Widget, row: int, columnspan: int = 2) -> None:
        """Create and grid the error‐message label (initially hidden)."""
        lbl = ttk.Label(parent, text=self.message, style='ValidationError.TLabel')
        lbl.grid(column=0, row=row, columnspan=columnspan, sticky='w')
        lbl.grid_remove()
        self._label = lbl

    def validate(self, value: str) -> bool:
        valid = self.test(value)
        self.is_valid = valid
        if self._label:
            if valid:
                self._label.grid_remove()
            else:
                self._label.grid()
        return valid


class BaseField:
    def __init__(
        self,
        name: str,
        default: str = '',
        validators: Optional[List[Validator]] = None,
    ) -> None:
        self.name = name
        self.variable = tk.StringVar(value=default)
        self.validators = validators or []
        self._label: Optional[ttk.Label] = None
        self._entry: Optional[ttk.Entry] = None
        self._extra_widgets: List[tk.Widget] = []

    def create_widgets(self, parent: tk.Widget) -> None:
        """Instantiate label, entry, and any validator labels."""
        self._label = ttk.Label(parent, text=f"{self.name}:")
        self._entry = ttk.Entry(parent, textvariable=self.variable)
        for v in self.validators:
            v.attach_to(parent, row=0)  # placeholder row

        # Bind validation on every change
        self.variable.trace_add("write", lambda *_: self.run_validators())

    def run_validators(self) -> bool:
        value = self.variable.get()
        return all(v.validate(value) for v in self.validators)

    def grid(self, parent: tk.Widget, row: int) -> int:
        """Place label, entry, validators, return the next free row."""
        assert self._label and self._entry
        self._label.grid(column=0, row=row, sticky='w')
        self._entry.grid(column=1, row=row, sticky='ew')
        row += 1
        for v in self.validators:
            # reposition each validator label
            assert v._label
            v._label.grid(column=0, row=row, columnspan=2, sticky='w')
            if v.is_valid:
                v._label.grid_remove()
            row += 1
        return row


class PasswordField(BaseField):
    def __init__(self, name: str, default: str = '', validators: Optional[List[Validator]] = None) -> None:
        super().__init__(name, default, validators)
        self.show_password = tk.BooleanVar(value=False)
        self._toggle_btn: Optional[ttk.Button] = None

    def create_widgets(self, parent: tk.Widget) -> None:
        super().create_widgets(parent)
        # override entry to hide text
        assert self._entry
        self._entry.config(show='●')
        # add show/hide button
        btn = ttk.Button(parent, text='Show', command=self._toggle)
        self._extra_widgets.append(btn)
        self._toggle_btn = btn

    def _toggle(self) -> None:
        assert self._entry and self._toggle_btn
        if self.show_password.get():
            self._entry.config(show='●')
            self._toggle_btn.config(text='Show')
            self.show_password.set(False)
        else:
            self._entry.config(show='')
            self._toggle_btn.config(text='Hide')
            self.show_password.set(True)

    def grid(self, parent: tk.Widget, row: int) -> int:
        # place label + entry + button
        assert self._label and self._entry and self._toggle_btn
        self._label.grid(column=0, row=row, sticky='w')
        self._entry.grid(column=1, row=row, sticky='ew')
        self._toggle_btn.grid(column=2, row=row, sticky='ew')
        row += 1
        # then validators
        for v in self.validators:
            assert v._label
            v._label.grid(column=0, row=row, columnspan=3, sticky='w')
            if v.is_valid:
                v._label.grid_remove()
            row += 1
        return row


class Dialog(tk.Toplevel):
    def __init__(
        self,
        master: tk.Widget,
        title: str,
        text: Optional[str] = None,
        fields: Optional[Dict[str, BaseField]] = None,
    ) -> None:
        super().__init__(master)
        self.title(title)
        self.grab_set()
        self.protocol('WM_DELETE_WINDOW', self.cancel)

        # style for validation errors
        style = ttk.Style(self)
        style.configure('ValidationError.TLabel', foreground='red')

        # intro text
        row = 0
        if text:
            lbl = ttk.Label(self, text=text)
            lbl.grid(column=0, row=row, columnspan=3, sticky='w')
            row += 1

        self.fields = fields or {}
        # create widgets
        for f in self.fields.values():
            f.create_widgets(self)

        # place each field
        for f in self.fields.values():
            row = f.grid(self, row)

        # submit & cancel
        self._submit = ttk.Button(self, text='Submit', command=self.submit)
        self._cancel = ttk.Button(self, text='Cancel', command=self.cancel)
        self._submit.grid(column=1, row=row, sticky='e')
        self._cancel.grid(column=2, row=row, sticky='ew')

        self.columnconfigure(1, weight=1)
        self._update_submit_state()

    def _update_submit_state(self) -> None:
        if all(f.run_validators() for f in self.fields.values()):
            self._submit.state(('!disabled',))
        else:
            self._submit.state(('disabled',))

    def submit(self) -> None:
        self.result = {name: f.variable.get() for name, f in self.fields.items()}
        self.destroy()

    def cancel(self) -> None:
        self.result = None
        self.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()

    dlg = Dialog(
        master=root,
        title='Login',
        text='Enter your credentials:',
        fields={
            'username': BaseField(
                name='Username',
                validators=[Validator(lambda s: len(s) >= 3, "Must be ≥ 3 chars")],
            ),
            'password': PasswordField(name='Password'),
        }
    )
    root.wait_window(dlg)
    print(dlg.result)

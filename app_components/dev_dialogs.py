from dataclasses import dataclass
from typing import Callable
import tkinter as tk
from tkinter import messagebox, ttk

@dataclass
class ButtonData:
    text: str
    command: Callable[[ttk.Entry, ttk.Button, tk.StringVar], None]

@dataclass
class DescriptionData:
    text: str
    wrap_length: int | None = None


@dataclass
class Validator:
    test: Callable[[dict[str, str]], bool]
    failure_message: str

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
            dialog: 'Dialog',
        ) -> tuple[ttk.Label, ttk.Entry, ttk.Button | None, tk.StringVar]:
        var = tk.StringVar(dialog, value=self.default)
        label = ttk.Label(dialog, text=f'{self.name}:')
        entry = ttk.Entry(dialog, textvariable=var)
        if self.read_only:
            entry.config(state='disabled')
        if self.button_data is not None:
            button = ttk.Button(
                master=dialog,
                text=self.button_data.text,
                command=lambda x=entry, y=var: self.button_data.command(x, y)
            )
        else:
            button = None
        return label, entry, button, var
    
class PasswordField(Field):
    def __init__(self):
        super().__init__(
            name='Password',
            button_data=ButtonData('Show/Hide', self.toggle_visibility)
        )
    
    def load_widgets(
            self,
            dialog: 'Dialog',
        ) -> tuple[ttk.Label, ttk.Entry, ttk.Button | None, tk.StringVar]:
        label, entry, button, var = super().load_widgets(dialog)
        entry.config(show='●')
        return label, entry, button, var

    def toggle_visibility(self, entry: ttk.Entry, _: tk.StringVar):
        entry.config(show='●' if entry.cget('show') == '' else '')


class Dialog(tk.Toplevel):
    def __init__(
            self,
            master,
            title: str,
            description_data: DescriptionData = None,
            fields: dict[str, Field] = None,
            validators: list[Validator] = None,
            x_padding: int = 6,
            y_padding: int = 2,
            *args,
            **kwargs,
        ):
        # Call the base constructor.
        super().__init__(master, *args, **kwargs)

        # Grab all incoming events and set window properties.
        self.grab_set()
        self.title(title)
        self.protocol('WM_DELETE_WINDOW', self.cancel)

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
        self.stringvars = {}
        for key, field in fields.items():
            label, entry, button, var = field.load_widgets(self)
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
        submit_button = ttk.Button(self, text='Submit', command=self.submit)
        submit_button.grid(
            column=1,
            row=row,
            sticky='e',
            padx=(0, x_padding // 2),
            pady=(y_padding if row == 0 else y_padding // 2, y_padding),
        )
        cancel_button = ttk.Button(self, text='Cancel', command=self.cancel)
        cancel_button.grid(
            column=2,
            row=row,
            sticky='ew',
            padx=(x_padding // 2, x_padding),
            pady=(y_padding if row == 0 else y_padding // 2, y_padding),
        )

        # Configure the grid.
        self.columnconfigure(1, weight=1)

        # Store provided validators.
        self.validators = validators
        if self.validators is None:
            self.validators = []

    def submit(self):
        result = {x: y.get() for x, y in self.stringvars.items()}
        errors: list[str] = []
        for validator in self.validators:
            if not validator.test(result):
                errors.append(f'• {validator.failure_message}')
        if errors:
            messagebox.showerror(
                title='Validation Error',
                message=f'The following errors occured:\n{'\n'.join(errors)}',
            )
        else:
            self.result = result
            self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()

if __name__ == '__main__':
   
    from secrets import token_hex
    app = tk.Tk()
    ttk.Entry(app).grid(column=0, row=0)
    app.withdraw()
    dialog = Dialog(
        master=app,
        title='Kirby',
        description_data=DescriptionData('Contrary to popular belief, Lorem Ipsum is not simply random text. It has roots in a piece of classical Latin literature from 45 BC, making it over 2000 years old. Richard McClintock, a Latin professor at Hampden-Sydney College in Virginia, looked up one of the more obscure Latin words, consectetur, from a Lorem Ipsum passage, and going through the cites of the word in classical literature, discovered the undoubtable source. Lorem Ipsum comes from sections 1.10.32 and 1.10.33 of "de Finibus Bonorum et Malorum" (The Extremes of Good and Evil) by Cicero, written in 45 BC. This book is a treatise on the theory of ethics, very popular during the Renaissance. The first line of Lorem Ipsum, "Lorem ipsum dolor sit amet..", comes from a line in section 1.10.32.', 600),
        fields={
            'username': Field(
                name='Username',
                button_data=ButtonData(
                    text='Click Me!',
                    command= lambda e, v: print(f'Username: {v.get()}'),
                ),
            ),
            'email': Field(
                name='Email',
                button_data=ButtonData(
                    text='Click Me!',
                    command= lambda e, v: print(f'Email: {v.get()}'),
                ),
            ),
            'hex': Field(
                name='Hex',
                read_only=True,
                button_data=ButtonData(
                    text='Generate',
                    command=lambda e, v: v.set(token_hex(16)),
                ),
            ),
            'password': PasswordField(),
        },
        validators=[
            Validator(lambda x: x['username'], 'Username is required.'),
            Validator(lambda x: x['email'], 'Email is required.')
        ]
    )
    app.wait_window(dialog)
    print(dialog.result)
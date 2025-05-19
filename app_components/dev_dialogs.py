from typing import Callable
import tkinter as tk
from tkinter import ttk

#IMPORTANT NOTE: CONSIDER REWORK SO THERE'S ONLY ONE MESSAGE PER ROW
# ALLOWS PREVENTING UNEVEN GAPS USING THE INVISIBLE APPROACH
# Switch out validation dynamic for display callbacks and listing errors on submit

# Use this to make GENERALISABLE dialogues.

# Concept: class per entry, with a label, a set of validators+warnings, etc
# But grid structure them at the dialog level for column consistency
# I think I can move the validation calls up to the BaseField class

class Validator():
    def __init__(self, test: Callable[[str], bool], message: str):
        self.test = test
        self.message = message
        self.state: bool = False
        self.label: ttk.Label = None

class BaseField():
    def __init__(
            self,
            name: str,
            validators: list[Validator] = None,
            default: str = None,
        ):
        self.name = name
        self.variable = tk.StringVar(value=default)
        self.label = None
        self.entry = None
        self.button = None
        self.validators = validators
        if self.validators is None:
            self.validators = []
        for validator in self.validators:
            validator.state = validator.test(self.variable.get())
        
    def initialise_widgets(self, master):
        self.label = ttk.Label(master, text=f'{self.name}:')
        self.entry = ttk.Entry(master, textvariable=self.variable)

    def is_valid(self):
        return all([x.state for x in self.validators])




class PasswordField(BaseField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_password = tk.BooleanVar(value=False)

    def initialise_widgets(self, master):
        super().initialise_widgets(master)
        self.entry.config(show='●')
        self.button = ttk.Button(
            master=master,
            text='Show',
            command=self.toggle_password_visibility,
        )
    
    def toggle_password_visibility(self):
        self.show_password.set(not self.show_password.get())
        if self.show_password.get():
            self.button.config(text='Hide')
            self.entry.config(show='')
        else:
            self.button.config(text='Show')
            self.entry.config(show='●')

    



type FieldDict = dict[str, BaseField | PasswordField]

class Dialog(tk.Toplevel):
    def __init__(
            self,
            master,
            title: str,
            intro_text: str = None,
            fields: FieldDict = None,
            *args,
            **kwargs,
        ):
        # Call the base constructor and store the provided fields.
        super().__init__(master, *args, **kwargs)
        self.fields = fields
        if self.fields is None:
            self.fields = {}

        # Set styles.
        style = ttk.Style(self)
        print(style.layout('TLabel'))
        style.configure(
            style='ValidationError.TLabel',
            foreground='red',
        )

        # Grab all incoming events and set up the basic window properties.
        self.grab_set()
        self.title(title)
        self.protocol('WM_DELETE_WINDOW', self.cancel)

        # Store the current row for consistent placement.
        current_row = -1

        # Create and place the introductory text, if provided.
        if intro_text:
            current_row += 1
            self.text = ttk.Label(self, text=intro_text)
            self.text.grid(column=0, row=0, columnspan=3, sticky='w')
            print()

        # Create, but do not yet place, the submit and cancel buttons.
        self.submit_button = ttk.Button(
            master=self,
            text='Submit',
            command=self.submit,
            state='normal' if self.is_valid() else 'disabled',
        )
        self.cancel_button = ttk.Button(
            master=self,
            text='Cancel',
            command=self.cancel,
        )

        # Create extra rows for each field.
        for key, value in self.fields.items():
            # Initialise the field widgets.
            self.fields[key].initialise_widgets(self)

            # Move to a new row and place the field components.
            current_row += 1
            value.label.grid(column=0, row=current_row, sticky='w')
            value.entry.grid(column=1, row=current_row, sticky='ew')
            if value.button is not None:
                value.button.grid(column=2, row=current_row, sticky='ew')

            # Create extra rows for each validation.
            for validator in value.validators:
                # Move to a new row, position the error message, then hide it.
                current_row += 1
                validator.label = ttk.Label(
                    master=self,
                    text=validator.message,
                    style='ValidationError.TLabel',
                )
                validator.label.grid(
                    column=0,
                    row=current_row,
                    columnspan=2,
                    sticky='w',
                )

                # Set the test as a trace.
                def make_callback(key: str, validator: Validator):
                    def _callback(*_):
                        print(fields[key].variable.get())
                        if validator.test(fields[key].variable.get()):
                            validator.label.config(text='')
                            validator.state = True
                            if self.is_valid():
                                self.submit_button.config(state='normal')
                        else:
                            validator.label.config(text=validator.message)
                            validator.state = False
                            self.submit_button.config(state='disabled')
                    return _callback
                _callback = make_callback(key, validator)
                _callback(self.fields[key].variable)
                self.fields[key].variable.trace_add('write', _callback)


        # Place the submit and cancel buttons.
        current_row += 1
        self.submit_button.grid(column=1, row=current_row, sticky='e')
        self.cancel_button.grid(column=2, row=current_row, sticky='ew')

        self.columnconfigure(1, weight=1)
        # MOVE THE ABOVE- MAYBE DON'T

    def is_valid(self):
        return all(x.is_valid() for x in self.fields.values())

    def submit(self):
        self.result = {x: self.fields[x].variable.get() for x in self.fields}
        self.destroy()
    
    def cancel(self):
        self.result = None
        self.destroy()

if __name__ == '__main__':
    import tkinter as tk
    import tkinter.ttk as ttk

    def stylename_elements_options(stylename):
        '''Function to expose the options of every element associated to a widget
        stylename.'''
        try:
            # Get widget elements
            style = ttk.Style()
            layout = str(style.layout(stylename))
            print('Stylename = {}'.format(stylename))
            print('Layout    = {}'.format(layout))
            elements=[]
            for n, x in enumerate(layout):
                if x=='(':
                    element=""
                    for y in layout[n+2:]:
                        if y != ',':
                            element=element+str(y)
                        else:
                            elements.append(element[:-1])
                            break
            print('\nElement(s) = {}\n'.format(elements))

            # Get options of widget elements
            for element in elements:
                print('{0:30} options: {1}'.format(
                    element, style.element_options(element)))

        except tk.TclError:
            print('_tkinter.TclError: "{0}" in function'
                'widget_elements_options({0}) is not a regonised stylename.'
                .format(stylename))

    stylename_elements_options('my.TEntry')
    exit()
    app = tk.Tk()
    ttk.Entry(app).grid(column=0, row=0)
    app.withdraw()
    dialog = Dialog(
        master=app,
        title='Kirby',
        intro_text='Lorem Ipsum',
        fields={
            'username': BaseField(
                name='Username',
                validators=[
                    Validator(lambda x: x == 'ALMOST', 'FALSE ALWAYS'),
                ],
            ),
            'password': PasswordField('Password'),
        }
    )
    app.wait_window(dialog)
    print(dialog.result)
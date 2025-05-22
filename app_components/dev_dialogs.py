from dataclasses import dataclass
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

# I need a complete rethink here...
# Widgets MUST be created during dialog construction.
# Maybe make a dict in that constructor of str to StringVar
# Then for each Field object, have a display function using those
# And a create_widgets function
# Maybe validate at the dialog level? That allows combinations.
# Strip out the idea of conditional displays. Now just go for callables.

class Validator():
    pass

type _VarDict = dict[str, tk.StringVar]

@dataclass
class ButtonData:
    text: str
    command: Callable[[ttk.Entry, ttk.Button, tk.StringVar], None]

# Need a button command here
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
    
    # def create_variable(self) -> tk.StringVar:
    #     return tk.StringVar(value=self.default)

    def load_widgets(
            self,
            dialog: 'Dialog',
            row: int,
        ) -> tuple[ttk.Label, ttk.Entry, ttk.Button | None, tk.StringVar]:
        var = tk.StringVar(dialog, value=self.default)
        label = ttk.Label(dialog, text=f'{self.name}:')
        label.grid(column=0, row=row, sticky='w')
        entry = ttk.Entry(dialog, textvariable=var)
        if self.read_only:
            entry.config(state='disabled')
        entry.grid(column=1, row=row, sticky='ew')
        if self.button_data is not None:
            button = ttk.Button(
                master=dialog,
                text=self.button_data.text,
                command=lambda x=entry, y=var: self.button_data.command(x, y)
            )
            button.grid(column=2, row=row, sticky='ew')
        else:
            button = None
        return label, entry, button, var
    
class PasswordField(Field):
    def __init__(self):
        super().__init__(
            name='Password',
            button_data=ButtonData('Show/Hide', self.toggle_visibility)
        )
    
    def load_widgets(self, dialog, row):
        label, entry, button, var = super().load_widgets(dialog, row)
        entry.config(show='●')
        return label, entry, button, var

    def toggle_visibility(self, entry: ttk.Entry, _: tk.StringVar):
        entry.config(show='●' if entry.cget('show') == '' else '')




    # def create_widgets(
    #         self,
    #         dialog: 'Dialog',
    #     ) -> tuple[ttk.Label, ttk.Entry, ButtonVarBundle | None]:
    #     if self.button_data is not None:
    #         variable = tk.StringVar(value=self.default)
    #     else:
    #         variable = None
    #     label = ttk.Label(dialog, text=f'{self.name}:')
    #     entry = ttk.Entry(dialog, textvariable=variable)
    #     if self.read_only:
    #         entry.config(state='disabled')
    #     if self.button_data is not None:
    #         button = ttk.Button(
    #             master=dialog,
    #             text=self.button_data.text,
    #             command=lambda var=variable: self.button_data.command(var),
    #         )
    #         button_var_bundle = ButtonVarBundle(button, variable)
    #     else:
    #         button_var_bundle = None
    #     return label, entry, button_var_bundle


class Dialog(tk.Toplevel):
    def __init__(
            self,
            master,
            title: str,
            description: str = None,
            fields: dict[str, Field] = None,
            validators: list[Callable[[dict[str, str]], bool]] = None,
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
        if description is not None:
            label = ttk.Label(self, text=description)
            label.grid(column=0, row=row, columnspan=3)
            row += 1
        
        # Create widgets for each field.
        self.stringvars = {}
        for key, field in fields.items():
            self.stringvars[key] = field.load_widgets(self, row)[-1]
            row += 1

        # Add in command buttons.
        submit_button = ttk.Button(self, text='Submit', command=self.submit)
        submit_button.grid(column=1, row=row, sticky='e')
        cancel_button = ttk.Button(self, text='Cancel', command=self.cancel)
        cancel_button.grid(column=2, row=row, sticky='ew')

        # Configure the grid.
        self.columnconfigure(1, weight=1)

        # # Loop over the supplied fields and create widgets.
        # for key, field in fields.items():
        #     stringvar = self.stringvars[key]
        #     label, entry, button = field.create_widgets(self, stringvar)
        #     label.grid(column=0, row=row, sticky='w')
        #     entry.grid(column=1, row=row, sticky='ew')
        #     if button is not None:
        #         button.grid(column=2, row=row, sticky='ew')
        #     row += 1


        # Set styles.
        style = ttk.Style(self)

    def submit(self):
        result = {x: y.get() for x, y in self.stringvars.items()}
        # Validate
        self.result = result
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()




# class Validator():
#     def __init__(self, test: Callable[[str], bool], message: str):
#         self.test = test
#         self.message = message
#         self.state: bool = False
#         self.label: ttk.Label = None

# class BaseField():
#     def __init__(
#             self,
#             name: str,
#             validators: list[Validator] = None,
#             default: str = None,
#             visibility_criteria: Callable[[dict[str, tk.StringVar]], bool] = lambda: True,
#         ):
#         self.name = name
#         self.variable = tk.StringVar(value=default)
#         self.label = None
#         self.entry = None
#         self.button = None
#         self.validators = validators
#         if self.validators is None:
#             self.validators = []
#         for validator in self.validators:
#             validator.state = validator.test(self.variable.get())
        
#     def initialise_widgets(self, master):
#         self.label = ttk.Label(master, text=f'{self.name}:')
#         self.entry = ttk.Entry(master, textvariable=self.variable)

#     def is_valid(self):
#         return all([x.state for x in self.validators])




# class PasswordField(BaseField):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.show_password = tk.BooleanVar(value=False)

#     def initialise_widgets(self, master):
#         super().initialise_widgets(master)
#         self.entry.config(show='●')
#         self.button = ttk.Button(
#             master=master,
#             text='Show',
#             command=self.toggle_password_visibility,
#         )
    
#     def toggle_password_visibility(self):
#         self.show_password.set(not self.show_password.get())
#         if self.show_password.get():
#             self.button.config(text='Hide')
#             self.entry.config(show='')
#         else:
#             self.button.config(text='Show')
#             self.entry.config(show='●')

    



# type FieldDict = dict[str, BaseField | PasswordField]

# class Dialog(tk.Toplevel):
#     def __init__(
#             self,
#             master,
#             title: str,
#             text: str = None,
#             fields: FieldDict = None,
#             *args,
#             **kwargs,
#         ):
#         # Call the base constructor.
#         super().__init__(master, *args, **kwargs)

#         # Fully initialise and store the provided fields.
#         self.fields = fields
#         if self.fields is None:
#             self.fields = {}
#         for value in self.fields.values():
#             value.initialise_widgets(self)


#         # Set styles.
#         style = ttk.Style(self)
#         print(style.layout('TLabel'))
#         style.configure(
#             style='ValidationError.TLabel',
#             foreground='red',
#         )

#         # Grab all incoming events and set up the basic window properties.
#         self.grab_set()
#         self.title(title)
#         self.protocol('WM_DELETE_WINDOW', self.cancel)

#         # Store the current row for consistent placement.
#         current_row = -1

#         # Create and place the introductory text, if provided.
#         if text:
#             current_row += 1
#             self.text = ttk.Label(self, text=text)
#             self.text.grid(column=0, row=0, columnspan=3, sticky='w')
#             print()

#         # Create, but do not yet place, the submit and cancel buttons.
#         self.submit_button = ttk.Button(
#             master=self,
#             text='Submit',
#             command=self.submit,
#             state='normal' if self.is_valid() else 'disabled',
#         )
#         self.cancel_button = ttk.Button(
#             master=self,
#             text='Cancel',
#             command=self.cancel,
#         )

#         # Create extra rows for each field.
#         for key, value in self.fields.items():
#             # Initialise the field widgets.
#             self.fields[key].initialise_widgets(self)

#             # Move to a new row and place the field components.
#             current_row += 1
#             value.label.grid(column=0, row=current_row, sticky='w')
#             value.entry.grid(column=1, row=current_row, sticky='ew')
#             if value.button is not None:
#                 value.button.grid(column=2, row=current_row, sticky='ew')

#             # Create extra rows for each validation.
#             for validator in value.validators:
#                 # Move to a new row, position the error message, then hide it.
#                 current_row += 1
#                 validator.label = ttk.Label(
#                     master=self,
#                     text=validator.message,
#                     style='ValidationError.TLabel',
#                 )
#                 validator.label.grid(
#                     column=0,
#                     row=current_row,
#                     columnspan=2,
#                     sticky='w',
#                 )

#                 # Set the test as a trace.
#                 def make_callback(key: str, validator: Validator):
#                     def _callback(*_):
#                         print(fields[key].variable.get())
#                         if validator.test(fields[key].variable.get()):
#                             validator.label.config(text='')
#                             validator.state = True
#                             if self.is_valid():
#                                 self.submit_button.config(state='normal')
#                         else:
#                             validator.label.config(text=validator.message)
#                             validator.state = False
#                             self.submit_button.config(state='disabled')
#                     return _callback
#                 _callback = make_callback(key, validator)
#                 _callback(self.fields[key].variable)
#                 self.fields[key].variable.trace_add('write', _callback)


#         # Place the submit and cancel buttons.
#         current_row += 1
#         self.submit_button.grid(column=1, row=current_row, sticky='e')
#         self.cancel_button.grid(column=2, row=current_row, sticky='ew')

#         self.columnconfigure(1, weight=1)
#         # MOVE THE ABOVE- MAYBE DON'T

#     def is_valid(self):
#         return all(x.is_valid() for x in self.fields.values())

#     def submit(self):
#         self.result = {x: self.fields[x].variable.get() for x in self.fields}
#         self.destroy()
    
#     def cancel(self):
#         self.result = None
#         self.destroy()

if __name__ == '__main__':
    # import tkinter as tk
    # import tkinter.ttk as ttk

    # def stylename_elements_options(stylename):
    #     '''Function to expose the options of every element associated to a widget
    #     stylename.'''
    #     try:
    #         # Get widget elements
    #         style = ttk.Style()
    #         layout = str(style.layout(stylename))
    #         print('Stylename = {}'.format(stylename))
    #         print('Layout    = {}'.format(layout))
    #         elements=[]
    #         for n, x in enumerate(layout):
    #             if x=='(':
    #                 element=""
    #                 for y in layout[n+2:]:
    #                     if y != ',':
    #                         element=element+str(y)
    #                     else:
    #                         elements.append(element[:-1])
    #                         break
    #         print('\nElement(s) = {}\n'.format(elements))

    #         # Get options of widget elements
    #         for element in elements:
    #             print('{0:30} options: {1}'.format(
    #                 element, style.element_options(element)))

    #     except tk.TclError:
    #         print('_tkinter.TclError: "{0}" in function'
    #             'widget_elements_options({0}) is not a regonised stylename.'
    #             .format(stylename))

    # stylename_elements_options('my.TEntry')
    # exit()
    from secrets import token_hex
    app = tk.Tk()
    ttk.Entry(app).grid(column=0, row=0)
    app.withdraw()
    dialog = Dialog(
        master=app,
        title='Kirby',
        description='Lorem Ipsum',
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
        }
    )
    app.wait_window(dialog)
    print(dialog.result)
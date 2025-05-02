import tkinter as tk
import tkinter.ttk as ttk

class MessageEntry(ttk.Entry):
    def __init__(self, *args, **kwargs):
        self.text_variable = tk.StringVar()
        super().__init__(*args, **kwargs, textvariable=self.text_variable)
        self.bind('<Return>', self.output)

    def output(self, event):
        value = self.text_variable.get()
        if value:
            print(value)
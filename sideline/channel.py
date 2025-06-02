import tkinter as tk
import tkinter.ttk as ttk

class Channel(ttk.Frame):
    def __init__(self, master, channel_name, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.channel_name = channel_name
        self.label = ttk.Label(self, text=self.channel_name)
        self.label.pack()
        self.entry_value = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.entry_value)
        self.entry.bind('<Return>', self.attempt_send)
        self.entry.pack()

    def attempt_send(self, event):
        if self.entry_value.get():
            print(f'{self.channel_name}: {self.entry_value.get()}')
            self.entry_value.set('')
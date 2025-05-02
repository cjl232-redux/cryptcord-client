import tkinter as tk
import tkinter.ttk as ttk

class Settings(tk.Toplevel):
    pass

class Channel(ttk.Frame):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.settings = None
        self.btn = ttk.Button(
            self,
            text='Settings',
        )
        self.btn.grid(column=0, row=0)
        self.label = ttk.Label(self, text=name)
        self.label.grid(column=0, row=1)
        self.entry_field = ttk.Entry(self)
        self.entry_field.grid(column=0, row=2)
        self.entry_field.bind('<Return>', self.print_text)
    
    def print_text(self, event):
        if self.entry_field.get():
            print(f'{self.name}: {self.entry_field.get()}')
            self.entry_field.delete(0, tk.END)

    def load_messages(self, event):
        pass


class Server(ttk.Notebook):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def load_channels(self, channels):
        for channel in channels:
            self.add(Channel(name=channel), text=channel)

class SettingsPopout(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class HeaderBar(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_popout = None
        self.settings_button = ttk.Button(
            master=self,
            command=self.open_settings,
            text='Settings',
        )
        self.settings_button.grid(column=0, row=0)

    def open_settings(self):
        if self.settings_popout and self.settings_popout.winfo_exists():
            self.settings_popout.lift()
        else:
            self.settings_popout = SettingsPopout()

class ActiveServer(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_bar = ttk.Notebook

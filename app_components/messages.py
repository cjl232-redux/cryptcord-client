import sqlite3
import tkinter as tk

from tkinter import ttk

from app_components.scrollable_frames import VerticalFrame, VerticalText

# Ideally want to make return (NOT shift return) send message
# And tab move to the next widget per usual, not insert a tab (easier?)

# First is done. We'll see about the second, may be simple.
# Not trivial, at least... may have to ditch the idea of a scrollabletext class
# Just program in dynamic text size instead

class MessageWindow(tk.Toplevel):
    def __init__(
            self,
            master,
            contact_id: int,
            local_database: sqlite3.Connection,
            *args,
            **kwargs,
        ):
        super().__init__(master, *args, **kwargs)
        self.message_log = VerticalFrame(self)
        self.log_size = 0
        self.message_log.grid(
            column=0,
            row=0,
            padx=10,
            pady=(10, 5,),
            sticky='nsew',
        )

        self.input_box = VerticalText(master=self, text_height=2)
        self.input_box.grid(
            column=0,
            row=1,
            padx=10,
            pady=(5, 10,),
            sticky='nsew',
        )

        self.input_box.text.bind('<Return>', self._send_message)
        self.input_box.text.bind('<Shift-Return>', lambda *_: None)

        self.rowconfigure(0, weight=1)

        button = ttk.Button(self)
        button.grid(column=0, row=2)

    def _send_message(self, *_):
        message = self.input_box.text.get('1.0', tk.END).rstrip()
        if message:
            label = ttk.Label(master=self.message_log.interior, text=message)
            label.grid(column=0, row=self.log_size, sticky='w')
            self.log_size += 1
        self.input_box.text.delete('1.0', tk.END)
        return 'break'

    def _refresh(self):
        self.var.set(self.var.get() + 'a')
        self.after(100, self._refresh)

if __name__ == '__main__':
    app = tk.Tk()
    text = tk.Text(app)
    text.grid(column=0, row=0, sticky='nsew')
    def _submit(*_):
        val = text.get('1.0', f'{tk.END}-1c')
        if val:
            print(val)
            text.delete('1.0', tk.END)
        return 'break'

    text.bind('<Return>', _submit)
    text.bind('<Shift-Return>', lambda *_: None)
    app.mainloop()
import tkinter as tk
# This is a bad idea after all
class ParentApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Parent-Child Command Passing Example")

        self.child = ChildFrame(self, self.parent_method)
        self.child.pack(padx=10, pady=10)

    def parent_method(self):
        print("Parent method was called by the child!")

class ChildFrame(tk.Frame):
    def __init__(self, parent, command_to_parent):
        super().__init__(parent)
        self.command_to_parent = command_to_parent

        self.button = tk.Button(self, text="Call Parent Method", command=self.call_parent)
        self.button.pack()

    def call_parent(self):
        self.command_to_parent()
app = ParentApp()
app.mainloop()
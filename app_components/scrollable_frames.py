import tkinter as tk
import tkinter.ttk as ttk

# Definitely room to streamline this...

class VerticalFrame(ttk.Frame):
    def __init__(self, master, scroll_speed: int = 2, *args, **kwargs):
        # Call the base constructor.
        super().__init__(master, *args, **kwargs)

        # Store values.
        self.scroll_speed = scroll_speed

        # Create and place the canvas and scrollbar.
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(
            master=self,
            orient='vertical',
            command=self.canvas.yview,
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(column=0, row=0, sticky='nsew')
        self.scrollbar.grid(column=1, row=0, sticky='ns')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Create and place the interior frame.
        self.interior = ttk.Frame(self.canvas)
        self.window = self.canvas.create_window(0, 0, window=self.interior, anchor='nw')

        # Define and assign callbacks.
        def _on_configure_canvas(event):
            self.canvas.itemconfig(self.window, width=event.width)
        self.canvas.bind('<Configure>', _on_configure_canvas)
        def _on_configure_interior(_):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.interior.bind('<Configure>', _on_configure_interior)

        # Bind and unbind a mousewheel callback based on the cursor position.
        self.canvas.bind('<Enter>', self._bind_mousewheel)
        self.canvas.bind('<Leave>', self._unbind_mousewheel)
        
    def _on_mousewheel(self, event):
        if event.delta <= 0:
            self.canvas.yview_scroll(self.scroll_speed, 'units')
        else:
            self.canvas.yview_scroll(-self.scroll_speed, 'units')

    def _bind_mousewheel(self, *_):
        self.winfo_toplevel().unbind('<MouseWheel>')
        self.winfo_toplevel().bind('<MouseWheel>', self._on_mousewheel)
    def _unbind_mousewheel(self, *_):
        self.winfo_toplevel().unbind('<MouseWheel>')


class VerticalText(ttk.Frame):
    def __init__(
            self,
            master,
            scroll_speed: int = 2,
            text_height: int = 24,
            *args,
            **kwargs,
        ):
        # Store values.
        self.scroll_speed = scroll_speed

        # Call the base constructor.
        super().__init__(master, *args, **kwargs)

        # Create and place the canvas and scrollbar.
        self.text = tk.Text(self, height=text_height)
        self.text.grid(column=0, row=0, sticky='nsew')
        self.scrollbar = ttk.Scrollbar(
            master=self,
            orient='vertical',
            command=self.text.yview,
        )
        self.scrollbar.grid(column=1, row=0, sticky='ns')
        self.text.configure(yscrollcommand=self.scrollbar.set)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Bind and unbind a mousewheel callback based on the cursor position.
        self.text.bind('<Enter>', self._bind_mousewheel)
        self.text.bind('<Leave>', self._unbind_mousewheel)
        
    def _on_mousewheel(self, event):
        if event.delta <= 0:
            self.text.yview_scroll(self.scroll_speed, 'units')
        else:
            self.text.yview_scroll(-self.scroll_speed, 'units')

    def _bind_mousewheel(self, *_):
        self.winfo_toplevel().bind('<MouseWheel>', self._on_mousewheel)
    def _unbind_mousewheel(self, *_):
        self.winfo_toplevel().unbind('<MouseWheel>')


if __name__ == '__main__':
    class SampleApp(tk.Tk):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.frame = VerticalFrame(self)
            self.frame.grid(column=0, row=0, sticky='nsew')
            self.label = ttk.Label(self, text="Shrink the window to activate the scrollbar.")
            self.button = ttk.Button(self, text='add', command=self.add_buttons)
            self.button.grid(column=0, row=1)
            self.buttons = []
            self.add_buttons()
            self.columnconfigure(0, weight=1)
            self.rowconfigure(0, weight=1)
        
        def add_buttons(self):
            for i in range(len(self.buttons), len(self.buttons) + 10):
                label = ttk.Label(self.frame.interior, text=f"Button {i + 1}")
                label.grid(column=0, row=i, sticky='w', padx=5, pady=2)
                self.buttons.append(label)
            self.frame.interior.columnconfigure(0, weight=1)


    app = SampleApp()
    app.mainloop()
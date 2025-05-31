import tkinter as tk

from tkinter import ttk
from typing import Any

class ScrollableFrame(ttk.Frame):
    def __init__(
            self,
            master: tk.Widget | tk.Toplevel | tk.Tk,
            scroll_speed: int = 5,
            *args: tuple[Any],
            **kwargs: dict[str, Any],
        ):
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
        self.scrollbar.grid(column=1, row=0, sticky='nse')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Create and place the interior frame.
        self.interior = ttk.Frame(self.canvas)
        id = self.canvas.create_window(0, 0, window=self.interior, anchor='nw')

        # Define and assign callbacks.
        def _on_configure_canvas(event: 'tk.Event[tk.Canvas]'):
            self.canvas.itemconfig(id, width=event.width)
        self.canvas.bind('<Configure>', _on_configure_canvas)
        def _on_configure_interior(_):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.interior.bind('<Configure>', _on_configure_interior)

        # Bind and unbind a mousewheel callback based on the cursor position.
        self.bind('<Enter>', self._bind_mousewheel)
        self.bind('<Leave>', self._unbind_mousewheel)

                
    def _on_mousewheel(self, event: 'tk.Event[Any]'):
        top, bottom = self.canvas.yview()
        if bottom - top >= 1.0:
            return
        if event.delta <= 0:
            self.canvas.yview_scroll(self.scroll_speed, 'units')
        else:
            self.canvas.yview_scroll(-self.scroll_speed, 'units')

    def _bind_mousewheel(self, *_):
        self.winfo_toplevel().bind('<MouseWheel>', self._on_mousewheel)

    def _unbind_mousewheel(self, *_):
        self.winfo_toplevel().unbind('<MouseWheel>')
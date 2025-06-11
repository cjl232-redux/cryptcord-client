import tkinter as tk

from tkinter import ttk
from typing import Any

from settings import settings

class ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Widget | tk.Toplevel | tk.Tk):
        # Call the Frame constructor.
        super().__init__(master)        
        # Create and place the canvas and scrollbar.
        self.canvas = tk.Canvas(
            master=self,
            highlightthickness=0,
        )
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
        # Create and place the interior frame, simulating padding.
        self.interior = ttk.Frame(self.canvas)
        self.canvas.create_line(2, 2, 2, 2)
        id = self.canvas.create_window(
            settings.graphics.horizontal_padding,
            settings.graphics.vertical_padding,
            window=self.interior,
            anchor='nw',
        )
        # Define and assign callbacks.
        def _on_configure_canvas(event: 'tk.Event[tk.Canvas]'):
            self.canvas.itemconfig(id, width=event.width)
        self.canvas.bind('<Configure>', _on_configure_canvas)
        def _on_configure_interior(_):
            bbox = self.canvas.bbox('all')
            x, y, width, height = bbox
            if height < self.canvas.winfo_height():
                bbox = x, y, width, self.canvas.winfo_height()
            self.canvas.configure(scrollregion=bbox)
        self.interior.bind('<Configure>', _on_configure_interior)
        # Bind and unbind a mousewheel callback based on the cursor position.
        self.bind('<Enter>', self._bind_mousewheel)
        self.bind('<Leave>', self._unbind_mousewheel)
                
    def _on_mousewheel(self, event: 'tk.Event[Any]'):
        top, bottom = self.canvas.yview()
        if bottom - top >= 1.0:
            return
        if event.delta <= 0:
            self.canvas.yview_scroll(
                settings.functionality.scroll_speed,
                'units',
            )
        else:
            self.canvas.yview_scroll(
                -settings.functionality.scroll_speed,
                'units',
            )

    def _bind_mousewheel(self, *_):
        self.winfo_toplevel().bind('<MouseWheel>', self._on_mousewheel)

    def _unbind_mousewheel(self, *_):
        self.winfo_toplevel().unbind('<MouseWheel>')
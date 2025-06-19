import tkinter as tk

from tkinter import ttk
from typing import Any

from settings import settings

class ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Widget | tk.Tk | tk.Toplevel):
        super().__init__(master)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            master=self,
            orient='vertical',
            command=self.canvas.yview,
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        # Place an interior padding frame that will fill the canvas.
        padding_frame = tk.Frame(self.canvas)
        canvas_window = self.canvas.create_window(
            0,
            0,
            window=padding_frame,
            anchor='nw',
        )
        self.interior = tk.Frame(padding_frame)
        self.interior.grid(
            row=0,
            column=0,
            padx=settings.graphics.horizontal_padding,
            pady=settings.graphics.vertical_padding,
            sticky='nsew',
        )
        padding_frame.columnconfigure(0, weight=1)
        padding_frame.rowconfigure(0, weight=1)
        # Define and bind configure responses.
        def on_canvas_configure(event: 'tk.Event[tk.Canvas]'):
            self.canvas.itemconfig(canvas_window, width=event.width)
        self.canvas.bind("<Configure>", on_canvas_configure)
        def on_padding_configure(event: 'tk.Event[ttk.Frame]'):
            bbox = self.canvas.bbox('all')
            yview = self.canvas.yview()
            x0, y0, x1, y1 = bbox
            content_height = y1 - y0
            canvas_height = self.canvas.winfo_height()
            true_height = max(content_height, canvas_height)
            self.canvas.configure(scrollregion=(x0, y0, x1, y0 + true_height))
            if yview[1] == 1.0:
                self.canvas.yview_moveto(1.0)

        padding_frame.bind('<Configure>', on_padding_configure) # type: ignore
        # Bind and unbind a mousewheel callback based on the cursor position.
        def on_mousewheel(event: 'tk.Event[Any]'):
            y0, y1 = self.canvas.yview()
            if y1 - y0 >= 1.0:
                return
            elif event.delta <= 0:
                self.canvas.yview_scroll(
                    settings.functionality.scroll_speed,
                    'units',
                )
            else:
                self.canvas.yview_scroll(
                    -settings.functionality.scroll_speed,
                    'units',
                )
        def bind_mousewheel(*_):
            self.winfo_toplevel().bind('<MouseWheel>', on_mousewheel)
        def unbind_mousewheel(*_):
            self.winfo_toplevel().unbind('<MouseWheel>')
        self.bind('<Enter>', bind_mousewheel)
        self.bind('<Leave>', unbind_mousewheel)
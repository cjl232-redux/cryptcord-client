import tkinter as tk
import tkinter.ttk as ttk

class VerticalScrollableFrame(ttk.Frame):
    def __init__(self, master, scroll_speed: int = 2, *args, **kwargs):
        # Call the base constructor.
        super().__init__(master, *args, **kwargs)

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
        # def _on_configure_canvas(event):
        #     self.canvas.itemconfig(self.window, width=event.width)
        # self.canvas.bind('<Configure>', _on_configure_canvas)
            
        def _on_configure_interior(_):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.interior.bind('<Configure>', _on_configure_interior)

        # Define and assign a callback for scrolling with the mouse wheel.
        def _on_mousewheel(event):
            if event.delta <= 0:
                self.canvas.yview_scroll(scroll_speed, 'units')
            else:
                self.canvas.yview_scroll(-scroll_speed, 'units')
        self.canvas.bind('<MouseWheel>', _on_mousewheel)


if __name__ == '__main__':
    class SampleApp(tk.Tk):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.frame = VerticalScrollableFrame(self)
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
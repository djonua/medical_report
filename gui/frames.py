import tkinter as tk
from tkinter import ttk

class CollapsibleFrame(ttk.Frame):
    def __init__(self, parent, text="", *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        
        self.show = tk.BooleanVar()
        self.show.set(False)
        
        self.title_frame = ttk.Frame(self)
        self.title_frame.pack(fill="x", expand=1)
        
        ttk.Label(self.title_frame, text=text).pack(side="left", padx=5)
        self.toggle_button = ttk.Checkbutton(
            self.title_frame, 
            width=2, 
            text='+', 
            command=self.toggle,
            variable=self.show, 
            style='Toolbutton'
        )
        self.toggle_button.pack(side="left")
        
        self.sub_frame = ttk.Frame(self, relief="sunken", borderwidth=1)
    
    def toggle(self):
        if self.show.get():
            self.sub_frame.pack(fill="x", expand=1)
            self.toggle_button.configure(text='-')
        else:
            self.sub_frame.pack_forget()
            self.toggle_button.configure(text='+') 
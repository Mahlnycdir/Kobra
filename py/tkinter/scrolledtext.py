"""Nachbau von tkinter.scrolledtext (Scrollen uebernimmt die Oberflaeche)."""
from tkinter import Frame, Text, Scrollbar, Pack, Grid, Place
from tkinter.constants import RIGHT, LEFT, Y, BOTH

__all__ = ["ScrolledText"]


class ScrolledText(Text):
    def __init__(self, master=None, **kw):
        self.frame = Frame(master)
        self.vbar = Scrollbar(self.frame)
        Text.__init__(self, self.frame, **kw)
        Text.pack(self, side=LEFT, fill=BOTH, expand=True)
        for m in ("pack", "pack_configure", "pack_forget", "pack_info", "grid", "grid_configure",
                  "grid_forget", "grid_remove", "grid_info", "place", "place_configure", "place_forget"):
            setattr(self, m, getattr(self.frame, m))

    def __str__(self):
        return str(self.frame)

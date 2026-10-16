"""Nachbau von tkinter.colorchooser."""
import pyide_gui as _g


def askcolor(color=None, **options):
    if isinstance(color, (tuple, list)):
        color = "#%02x%02x%02x" % tuple(int(c) for c in color[:3])
    res = _g.sync_call("dialog", {"type": "color", "title": str(options.get("title") or "Farbe wählen"),
                                  "initial": color or "#3366cc"})
    if not res:
        return (None, None)
    h = str(res).lstrip("#")
    return ((int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)), "#" + h.lower())


class Chooser:
    def __init__(self, master=None, **options):
        self.options = options

    def show(self, color=None, **options):
        return askcolor(color, **self.options)

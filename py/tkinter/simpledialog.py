"""Nachbau von tkinter.simpledialog."""
import pyide_gui as _g
import tkinter as _tk
from tkinter import messagebox as _mb


def _ask(kind, title, prompt, kw):
    payload = {"type": "input", "kind": kind, "title": str(title or ""), "prompt": str(prompt or ""),
               "initial": "" if kw.get("initialvalue") is None else str(kw.get("initialvalue")),
               "min": kw.get("minvalue"), "max": kw.get("maxvalue"), "show": kw.get("show")}
    while True:
        res = _g.sync_call("dialog", payload)
        if res is None:
            return None
        if kind == "string":
            return str(res)
        try:
            val = int(res) if kind == "int" else float(res)
        except (TypeError, ValueError):
            _mb.showwarning("Ungültige Eingabe", "Bitte eine %s eingeben." %
                            ("ganze Zahl" if kind == "int" else "Zahl"))
            payload["initial"] = str(res)
            continue
        lo, hi = kw.get("minvalue"), kw.get("maxvalue")
        if lo is not None and val < lo:
            _mb.showwarning("Zu klein", "Der Wert muss mindestens %s sein." % lo)
            continue
        if hi is not None and val > hi:
            _mb.showwarning("Zu groß", "Der Wert darf höchstens %s sein." % hi)
            continue
        return val


def askstring(title, prompt, **kw):
    return _ask("string", title, prompt, kw)


def askinteger(title, prompt, **kw):
    return _ask("int", title, prompt, kw)


def askfloat(title, prompt, **kw):
    return _ask("float", title, prompt, kw)


class Dialog(_tk.Toplevel):
    """Basisklasse fuer eigene Dialoge (body/buttonbox/apply)."""

    def __init__(self, parent, title=None):
        _tk.Toplevel.__init__(self, parent)
        if title:
            self.title(title)
        self.parent = parent
        self.result = None
        body = _tk.Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)
        self.buttonbox()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        if self.initial_focus:
            self.initial_focus.focus_set()
        self.wait_window(self)

    def body(self, master):
        return None

    def buttonbox(self):
        box = _tk.Frame(self)
        _tk.Button(box, text="OK", width=10, command=self.ok).pack(side="left", padx=5, pady=5)
        _tk.Button(box, text="Abbrechen", width=10, command=self.cancel).pack(side="left", padx=5, pady=5)
        box.pack()

    def ok(self, event=None):
        if not self.validate():
            return
        self.withdraw()
        self.apply()
        self.cancel()

    def cancel(self, event=None):
        self.destroy()

    def validate(self):
        return 1

    def apply(self):
        pass


class SimpleDialog:
    def __init__(self, master, text="", buttons=[], default=None, cancel=None, title=None, class_=None):
        self.text = text
        self.buttons = list(buttons)
        self.title = title
        self.default = default

    def go(self):
        res = _g.sync_call("dialog", {"type": "message", "title": str(self.title or ""), "message": self.text,
                                      "icon": "question", "buttons": self.buttons})
        try:
            return self.buttons.index(res)
        except ValueError:
            return self.default

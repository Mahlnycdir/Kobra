"""Nachbau von tkinter.filedialog – waehlt Dateien aus dem aktuellen Projekt."""
import os
import pyide_gui as _g


def _types(filetypes):
    out = []
    for ft in filetypes or ():
        try:
            name, pat = ft
        except (TypeError, ValueError):
            continue
        pats = pat.split() if isinstance(pat, str) else list(pat)
        out.append([str(name), [str(p) for p in pats]])
    return out


def _ask(mode, kw):
    payload = {"type": "file", "mode": mode, "title": str(kw.get("title") or ""),
               "filetypes": _types(kw.get("filetypes")), "initialfile": kw.get("initialfile") or "",
               "defaultextension": kw.get("defaultextension") or "", "cwd": os.getcwd(),
               "initialdir": str(kw.get("initialdir") or "")}
    res = _g.sync_call("dialog", payload)
    if not res:
        return () if mode == "openmany" else ""
    if mode == "openmany":
        return tuple(os.path.join(os.getcwd(), p) for p in res)
    path = os.path.join(os.getcwd(), res)
    if mode == "dir":
        os.makedirs(path, exist_ok=True)
    return path


def askopenfilename(**options):
    return _ask("open", options)


def askopenfilenames(**options):
    return _ask("openmany", options)


def asksaveasfilename(**options):
    return _ask("save", options)


def askdirectory(**options):
    return _ask("dir", options)


def askopenfile(mode="r", **options):
    name = askopenfilename(**options)
    return open(name, mode) if name else None


def askopenfiles(mode="r", **options):
    return [open(n, mode) for n in askopenfilenames(**options)]


def asksaveasfile(mode="w", **options):
    name = asksaveasfilename(**options)
    return open(name, mode) if name else None


class FileDialog:
    def __init__(self, master, title=None):
        self.title = title

    def go(self, dir_or_file=".", pattern="*", default="", key=None):
        return askopenfilename(title=self.title)


class LoadFileDialog(FileDialog):
    pass


class SaveFileDialog(FileDialog):
    def go(self, dir_or_file=".", pattern="*", default="", key=None):
        return asksaveasfilename(title=self.title, initialfile=default)


class Open:
    def __init__(self, master=None, **options):
        self.options = options

    def show(self, **options):
        o = dict(self.options)
        o.update(options)
        return askopenfilename(**o)


class SaveAs(Open):
    def show(self, **options):
        o = dict(self.options)
        o.update(options)
        return asksaveasfilename(**o)


class Directory(Open):
    def show(self, **options):
        o = dict(self.options)
        o.update(options)
        return askdirectory(**o)

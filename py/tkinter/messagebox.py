"""Nachbau von tkinter.messagebox – Dialoge erscheinen in der IDE."""
import pyide_gui as _g

ERROR = "error"
INFO = "info"
QUESTION = "question"
WARNING = "warning"
ABORTRETRYIGNORE = "abortretryignore"
OK = "ok"
OKCANCEL = "okcancel"
RETRYCANCEL = "retrycancel"
YESNO = "yesno"
YESNOCANCEL = "yesnocancel"
ABORT = "abort"
RETRY = "retry"
IGNORE = "ignore"
CANCEL = "cancel"
YES = "yes"
NO = "no"


class Message:
    command = None

    def __init__(self, master=None, **options):
        self.master = master
        self.options = options

    def show(self, **options):
        o = dict(self.options)
        o.update(options)
        return _show(o.get("title"), o.get("message"), o.get("icon", INFO), o.get("type", OK),
                     o.get("detail"), o.get("default"))


def _show(title=None, message=None, icon=INFO, type=OK, detail=None, default=None):
    buttons = {OK: [OK], OKCANCEL: [OK, CANCEL], YESNO: [YES, NO], YESNOCANCEL: [YES, NO, CANCEL],
               RETRYCANCEL: [RETRY, CANCEL], ABORTRETRYIGNORE: [ABORT, RETRY, IGNORE]}.get(type, [OK])
    payload = {"type": "message", "title": str(title or ""), "message": str(message or ""),
               "detail": str(detail or ""), "icon": icon, "buttons": buttons, "default": default}
    res = _g.sync_call("dialog", payload)
    if res is None:
        _g.op("dialog_async", payload)
        _g.flush()
        return buttons[0] if type in (OK,) else None
    return res


def showinfo(title=None, message=None, **options):
    return _show(title, message, options.get("icon", INFO), OK, options.get("detail"))


def showwarning(title=None, message=None, **options):
    return _show(title, message, WARNING, OK, options.get("detail"))


def showerror(title=None, message=None, **options):
    return _show(title, message, ERROR, OK, options.get("detail"))


def askquestion(title=None, message=None, **options):
    return _show(title, message, QUESTION, options.get("type", YESNO), options.get("detail"))


def askokcancel(title=None, message=None, **options):
    return _show(title, message, QUESTION, OKCANCEL, options.get("detail")) == OK


def askyesno(title=None, message=None, **options):
    return _show(title, message, QUESTION, YESNO, options.get("detail")) == YES


def askyesnocancel(title=None, message=None, **options):
    s = _show(title, message, QUESTION, YESNOCANCEL, options.get("detail"))
    if s == CANCEL or s is None:
        return None
    return s == YES


def askretrycancel(title=None, message=None, **options):
    return _show(title, message, WARNING, RETRYCANCEL, options.get("detail")) == RETRY

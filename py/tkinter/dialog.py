import pyide_gui as _g

DIALOG_ICON = "questhead"


class Dialog:
    def __init__(self, master=None, cnf={}, **kw):
        cnf = dict(cnf)
        cnf.update(kw)
        strings = list(cnf.get("strings", ("OK",)))
        res = _g.sync_call("dialog", {"type": "message", "title": str(cnf.get("title", "")),
                                      "message": str(cnf.get("text", "")), "icon": "question",
                                      "buttons": strings})
        try:
            self.num = strings.index(res)
        except ValueError:
            self.num = cnf.get("default", 0)

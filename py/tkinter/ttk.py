"""ttk-Nachbau (themed widgets) fuer PyIDE."""
import tkinter as _tk
import pyide_gui as _g
from tkinter import _norm_key, _cnfmerge, _wire_value, Variable, TclError

__all__ = ["Button", "Checkbutton", "Combobox", "Entry", "Frame", "Label", "Labelframe", "LabelFrame",
           "Menubutton", "Notebook", "Panedwindow", "PanedWindow", "Progressbar", "Radiobutton",
           "Scale", "Scrollbar", "Separator", "Sizegrip", "Spinbox", "Style", "Treeview",
           "LabeledScale", "OptionMenu", "tclobjs_to_py", "setup_master"]

_styles = {".": {}}
_theme = ["aqua"]


def tclobjs_to_py(adict):
    return adict


def setup_master(master=None):
    return master or _tk._get_default_root()


class Style:
    def __init__(self, master=None):
        self.master = master

    def configure(self, style, query_opt=None, **kw):
        if query_opt is not None:
            return _styles.get(style, {}).get(_norm_key(query_opt), "")
        if not kw:
            return dict(_styles.get(style, {}))
        d = _styles.setdefault(style, {})
        for k, v in kw.items():
            d[_norm_key(k)] = v
        _restyle(style)
        return None

    def map(self, style, query_opt=None, **kw):
        if kw:
            d = _styles.setdefault(style, {})
            m = d.setdefault("_map", {})
            for k, v in kw.items():
                m[_norm_key(k)] = v
            _restyle(style)
        return {}

    def lookup(self, style, option, state=None, default=None):
        v = _styles.get(style, {}).get(_norm_key(option))
        if v is None:
            v = _styles.get(".", {}).get(_norm_key(option), default if default is not None else "")
        return v

    def layout(self, style, layoutspec=None):
        return []

    def element_create(self, elementname, etype, *args, **kw):
        pass

    def element_names(self):
        return ()

    def element_options(self, elementname):
        return ()

    def theme_create(self, themename, parent=None, settings=None):
        pass

    def theme_settings(self, themename, settings):
        for style, spec in (settings or {}).items():
            if "configure" in spec:
                self.configure(style, **spec["configure"])

    def theme_names(self):
        return ("aqua", "clam", "alt", "default", "classic")

    def theme_use(self, themename=None):
        if themename is None:
            return _theme[0]
        _theme[0] = themename
        _g.op("ttk_theme", themename)


def _restyle(style):
    for obj in list(_g._S.objects.values()):
        if isinstance(obj, _TtkMixin):
            st = obj._style_name()
            if style == "." or st == style or st.endswith("." + style) or style.endswith(st):
                _g.op("cfg", obj._w, {"_style": obj._effective_style()})


class _TtkMixin:
    _ttk = True
    _ttk_class = "TWidget"

    def _style_name(self):
        return str(self._opts.get("style") or self._ttk_class)

    def _effective_style(self):
        out = {}
        out.update({k: v for k, v in _styles.get(".", {}).items() if not k.startswith("_")})
        out.update({k: v for k, v in _styles.get(self._ttk_class, {}).items() if not k.startswith("_")})
        name = self._style_name()
        if name != self._ttk_class:
            parts = name.split(".")
            for i in range(len(parts) - 1, -1, -1):
                out.update({k: v for k, v in _styles.get(".".join(parts[i:]), {}).items() if not k.startswith("_")})
        return {k: _wire_value(k, v) for k, v in out.items()}

    def winfo_class(self):
        return self._ttk_class

    def state(self, statespec=None):
        cur = set(getattr(self, "_states", set()))
        if statespec is None:
            return tuple(cur)
        if isinstance(statespec, str):
            statespec = statespec.split()
        old = tuple(cur)
        for s in statespec:
            if s.startswith("!"):
                cur.discard(s[1:])
            else:
                cur.add(s)
        self._states = cur
        if "disabled" in cur:
            self._opts["state"] = "disabled"
        elif self._opts.get("state") == "disabled":
            self._opts["state"] = "normal"
        if "readonly" in cur:
            self._opts["state"] = "readonly"
        _g.op("cfg", self._w, {"state": self._opts.get("state", "normal")})
        return old

    def instate(self, statespec, callback=None, *args, **kw):
        cur = set(getattr(self, "_states", set()))
        if self._opts.get("state") == "disabled":
            cur.add("disabled")
        if isinstance(statespec, str):
            statespec = statespec.split()
        ok = all((s[1:] not in cur) if s.startswith("!") else (s in cur) for s in statespec)
        if ok and callback:
            return callback(*args, **kw)
        return ok

    def identify(self, x, y):
        return ""

    def _options_changed(self, kw):
        if "style" in kw:
            _g.op("cfg", self._w, {"_style": self._effective_style()})
        super()._options_changed(kw)


class Widget(_TtkMixin, _tk.Widget):
    def __init__(self, master, widgetname, kw=None):
        _tk.Widget.__init__(self, master, widgetname, kw or {})


class Button(_TtkMixin, _tk.Button):
    _ttk_class = "TButton"


class Checkbutton(_TtkMixin, _tk.Checkbutton):
    _ttk_class = "TCheckbutton"


class Radiobutton(_TtkMixin, _tk.Radiobutton):
    _ttk_class = "TRadiobutton"


class Entry(_TtkMixin, _tk.Entry):
    _ttk_class = "TEntry"


class Frame(_TtkMixin, _tk.Frame):
    _ttk_class = "TFrame"


class Label(_TtkMixin, _tk.Label):
    _ttk_class = "TLabel"


class Labelframe(_TtkMixin, _tk.LabelFrame):
    _ttk_class = "TLabelframe"


LabelFrame = Labelframe


class Menubutton(_TtkMixin, _tk.Menubutton):
    _ttk_class = "TMenubutton"


class Scrollbar(_TtkMixin, _tk.Scrollbar):
    _ttk_class = "TScrollbar"


class Separator(_TtkMixin, _tk.Widget):
    _tkcls = "Separator"
    _ttk_class = "TSeparator"
    _defaults = {"orient": "horizontal"}


class Sizegrip(_TtkMixin, _tk.Widget):
    _tkcls = "Sizegrip"
    _ttk_class = "TSizegrip"


class Spinbox(_TtkMixin, _tk.Spinbox):
    _ttk_class = "TSpinbox"

    def set(self, value):
        self._set_value(str(value))


class Scale(_TtkMixin, _tk.Scale):
    _ttk_class = "TScale"
    _defaults = {"from": 0, "to": 1.0, "orient": "horizontal", "resolution": 0, "length": 100,
                 "showvalue": 0}

    def _init_widget(self, kw):
        _tk.Scale._init_widget(self, kw)
        if "value" in kw:
            self._value = float(kw.pop("value"))

    def _ui_event(self, ev):
        if ev.get("k") == "val":
            x = float(ev.get("v", 0))
            v = self._var()
            if v is not None:
                v._from_ui(int(round(x)) if isinstance(v, _tk.IntVar) else x)
            else:
                self._value = x
            cmd = self._opts.get("command")
            if callable(cmd):
                _g._safe_call(cmd, str(x))


class Progressbar(_TtkMixin, _tk.Widget):
    _tkcls = "Progressbar"
    _ttk_class = "Horizontal.TProgressbar"
    _defaults = {"orient": "horizontal", "length": 100, "mode": "determinate", "maximum": 100, "value": 0}

    def _init_widget(self, kw):
        self._timer = None

    def _options_changed(self, kw):
        v = kw.get("variable")
        if isinstance(v, Variable):
            _g.op("var", v._name, v.get())
        _TtkMixin._options_changed(self, kw)

    def _get(self):
        v = self._opts.get("variable")
        if isinstance(v, Variable):
            try:
                return float(v.get())
            except Exception:
                return 0.0
        return float(self._opts.get("value", 0) or 0)

    def _set(self, x):
        v = self._opts.get("variable")
        if isinstance(v, Variable):
            v.set(x if not isinstance(v, _tk.IntVar) else int(x))
        self.configure(value=x)

    def step(self, amount=1.0):
        x = self._get() + float(amount)
        mx = float(self.cget("maximum") or 100)
        if x >= mx:
            x = x - mx
        self._set(x)

    def start(self, interval=None):
        interval = int(interval or 50)
        if self.cget("mode") == "indeterminate":
            _g.op("cfg", self._w, {"_anim": True})
            return

        def tick():
            self.step()
            self._timer = self.after(interval, tick)
        self.stop()
        self._timer = self.after(interval, tick)

    def stop(self):
        if self._timer:
            self.after_cancel(self._timer)
            self._timer = None
        _g.op("cfg", self._w, {"_anim": False})

    def __setitem__(self, key, value):
        self.configure({key: value})


class Combobox(Entry):
    _tkcls = "Combobox"
    _ttk_class = "TCombobox"
    _defaults = {"width": 20, "state": "normal", "values": ()}

    def current(self, newindex=None):
        vals = self._vals()
        if newindex is None:
            try:
                return vals.index(self.get())
            except ValueError:
                return -1
        self.set(vals[int(newindex)])
        return None

    def _vals(self):
        v = self._opts.get("values") or ()
        if isinstance(v, str):
            return _tk._tcl_split(v)
        return [str(x) for x in v]

    def set(self, value):
        self._set_value(str(value))

    def _ui_event(self, ev):
        if ev.get("k") == "val":
            self._set_value(ev.get("v", ""), from_ui=True)
            if ev.get("pick"):
                self._fire_event("Virtual", {"name": "<<ComboboxSelected>>"})
        elif ev.get("k") == "post":
            pc = self._opts.get("postcommand")
            if callable(pc):
                _g._safe_call(pc)


class Notebook(_TtkMixin, _tk.Widget):
    _tkcls = "Notebook"
    _ttk_class = "TNotebook"

    def _init_widget(self, kw):
        self._tabs = []          # [(widget, opts)]
        self._current = None
        self._master_info()

    def _pyide_sync(self):
        tabs = []
        for w, o in self._tabs:
            d = {"w": w._w}
            for k, v in o.items():
                d[k] = _wire_value(k, v)
            tabs.append(d)
        cur = self._tabs[self._current][0]._w if self._current is not None and self._current < len(self._tabs) else None
        _g.op("tabs", self._w, tabs, cur)

    def _find(self, tab_id):
        if isinstance(tab_id, int):
            return tab_id
        if tab_id in ("current",):
            return self._current
        if tab_id == "end":
            return len(self._tabs)
        for i, (w, o) in enumerate(self._tabs):
            if w is tab_id or w._w == str(tab_id):
                return i
        try:
            return int(tab_id)
        except (TypeError, ValueError):
            raise TclError("invalid tab %s" % tab_id)

    def add(self, child, **kw):
        kw = {_norm_key(k): v for k, v in kw.items()}
        for i, (w, o) in enumerate(self._tabs):
            if w is child:
                o.update(kw)
                _g.mark_dirty(self)
                return
        child._manager = "notebook"
        child._mopts = {}
        self._tabs.append((child, kw))
        if self._current is None:
            self._current = 0
        _g.mark_dirty(self)

    def insert(self, pos, child, **kw):
        kw = {_norm_key(k): v for k, v in kw.items()}
        child._manager = "notebook"
        self._tabs.insert(self._find(pos), (child, kw))
        if self._current is None:
            self._current = 0
        _g.mark_dirty(self)

    def forget(self, tab_id):
        i = self._find(tab_id)
        w, _ = self._tabs.pop(i)
        w._manager = None
        _g.op("forget", w._w)
        if not self._tabs:
            self._current = None
        elif self._current >= len(self._tabs):
            self._current = len(self._tabs) - 1
        _g.mark_dirty(self)

    def hide(self, tab_id):
        i = self._find(tab_id)
        self._tabs[i][1]["state"] = "hidden"
        _g.mark_dirty(self)

    def select(self, tab_id=None):
        if tab_id is None:
            return self._tabs[self._current][0]._w if self._current is not None else ""
        i = self._find(tab_id)
        if i != self._current:
            self._current = i
            _g.mark_dirty(self)
            self._fire_event("Virtual", {"name": "<<NotebookTabChanged>>"})
        return None

    def tab(self, tab_id, option=None, **kw):
        i = self._find(tab_id)
        o = self._tabs[i][1]
        if option is not None and not kw:
            return o.get(_norm_key(option), "")
        if kw:
            o.update({_norm_key(k): v for k, v in kw.items()})
            _g.mark_dirty(self)
            return None
        return dict(o)

    def tabs(self):
        return tuple(w._w for w, _ in self._tabs)

    def index(self, tab_id):
        if tab_id == "end":
            return len(self._tabs)
        return self._find(tab_id)

    def enable_traversal(self):
        pass

    def _ui_event(self, ev):
        if ev.get("k") == "tab":
            i = int(ev.get("i", 0))
            if i != self._current:
                self._current = i
                _g.mark_dirty(self)
                self._fire_event("Virtual", {"name": "<<NotebookTabChanged>>"})


class Panedwindow(_TtkMixin, _tk.PanedWindow):
    _ttk_class = "TPanedwindow"

    def insert(self, pos, child, **kw):
        self.add(child, **kw)

    def pane(self, pane, option=None, **kw):
        return {}

    def sashpos(self, index, newpos=None):
        return 0


PanedWindow = Panedwindow


class Treeview(_TtkMixin, _tk.Widget):
    _tkcls = "Treeview"
    _ttk_class = "Treeview"
    _defaults = {"show": "tree headings", "selectmode": "extended", "height": 10, "columns": ()}

    def _init_widget(self, kw):
        self._items = {"": {"children": [], "text": "", "values": [], "open": True, "tags": []}}
        self._parents = {}
        self._headings = {}
        self._colopts = {}
        self._sel = []
        self._focus = ""
        self._tagcfg = {}
        self._auto = 0
        self._last_row = ""

    def _columns(self):
        c = self._opts.get("columns") or ()
        if isinstance(c, str):
            c = c.split()
        return [str(x) for x in c]

    def _options_changed(self, kw):
        _g.mark_dirty(self)
        _TtkMixin._options_changed(self, kw)

    def _pyide_sync(self):
        def build(iid):
            it = self._items[iid]
            return {"id": iid, "text": str(it.get("text", "")), "values": [str(v) for v in it.get("values", [])],
                    "open": bool(it.get("open")), "tags": list(it.get("tags", [])),
                    "image": _wire_value("image", it.get("image")),
                    "children": [build(c) for c in it["children"]]}
        heads = {}
        for col, o in self._headings.items():
            heads[col] = {k: _wire_value(k, v) for k, v in o.items()}
        cols = {}
        for col, o in self._colopts.items():
            cols[col] = {k: _wire_value(k, v) for k, v in o.items()}
        tags = {t: {k: _wire_value(k, v) for k, v in o.items()} for t, o in self._tagcfg.items()}
        show = self._opts.get("show", "tree headings")
        if isinstance(show, (list, tuple)):
            show = " ".join(show)
        disp = self._opts.get("displaycolumns", "#all")
        if isinstance(disp, (list, tuple)):
            disp = [str(d) for d in disp]
        _g.op("tree", self._w, {"columns": self._columns(), "headings": heads, "colopts": cols,
                                "rows": [build(c) for c in self._items[""]["children"]], "sel": self._sel,
                                "show": show, "tags": tags, "display": disp})

    def insert(self, parent, index, iid=None, **kw):
        parent = str(parent) if parent is not None else ""
        if parent not in self._items:
            raise TclError('Item %s not found' % parent)
        if iid is None:
            self._auto += 1
            iid = "I%03X" % self._auto
        iid = str(iid)
        if iid in self._items:
            raise TclError('Item %s already exists' % iid)
        it = {"children": [], "text": "", "values": [], "open": False, "tags": []}
        for k, v in kw.items():
            k = _norm_key(k)
            if k == "values" and isinstance(v, str):
                v = _tk._tcl_split(v)
            if k == "tags" and isinstance(v, str):
                v = v.split()
            it[k] = list(v) if k in ("values", "tags") else v
        self._items[iid] = it
        self._parents[iid] = parent
        ch = self._items[parent]["children"]
        if index in ("end", "END") or index is None:
            ch.append(iid)
        else:
            ch.insert(int(index), iid)
        _g.mark_dirty(self)
        return iid

    def item(self, item, option=None, **kw):
        it = self._items[str(item)]
        if option is not None and not kw:
            o = _norm_key(option)
            v = it.get(o, "")
            return tuple(v) if o in ("values", "tags") else v
        if kw:
            for k, v in kw.items():
                k = _norm_key(k)
                if k in ("values", "tags") and isinstance(v, str):
                    v = _tk._tcl_split(v) if k == "values" else v.split()
                it[k] = list(v) if k in ("values", "tags") else v
            _g.mark_dirty(self)
            return None
        return {"text": it.get("text", ""), "values": tuple(it.get("values", [])) or "",
                "open": int(bool(it.get("open"))), "tags": tuple(it.get("tags", [])) or "",
                "image": it.get("image", "")}

    def set(self, item, column=None, value=None):
        it = self._items[str(item)]
        cols = self._columns()
        vals = list(it.get("values", []))
        while len(vals) < len(cols):
            vals.append("")
        if column is None:
            return dict(zip(cols, vals))
        ci = cols.index(column) if column in cols else int(str(column).lstrip("#")) - 1
        if value is None:
            return vals[ci]
        vals[ci] = value
        it["values"] = vals
        _g.mark_dirty(self)
        return None

    def delete(self, *items):
        for item in items:
            item = str(item)
            if item not in self._items:
                continue
            for c in list(self._items[item]["children"]):
                self.delete(c)
            p = self._parents.pop(item, "")
            if item in self._items[p]["children"]:
                self._items[p]["children"].remove(item)
            del self._items[item]
            if item in self._sel:
                self._sel.remove(item)
        _g.mark_dirty(self)

    def detach(self, *items):
        self.delete(*items)

    def get_children(self, item=None):
        return tuple(self._items[str(item or "")]["children"])

    def set_children(self, item, *newchildren):
        self._items[str(item)]["children"] = [str(c) for c in newchildren]
        _g.mark_dirty(self)

    def parent(self, item):
        return self._parents.get(str(item), "")

    def index(self, item):
        p = self.parent(item)
        return self._items[p]["children"].index(str(item))

    def next(self, item):
        p = self.parent(item)
        ch = self._items[p]["children"]
        i = ch.index(str(item))
        return ch[i + 1] if i + 1 < len(ch) else ""

    def prev(self, item):
        p = self.parent(item)
        ch = self._items[p]["children"]
        i = ch.index(str(item))
        return ch[i - 1] if i > 0 else ""

    def move(self, item, parent, index):
        item = str(item)
        old = self._parents.get(item, "")
        self._items[old]["children"].remove(item)
        ch = self._items[str(parent)]["children"]
        if index in ("end",):
            ch.append(item)
        else:
            ch.insert(int(index), item)
        self._parents[item] = str(parent)
        _g.mark_dirty(self)

    reattach = move

    def exists(self, item):
        return str(item) in self._items

    def heading(self, column, option=None, **kw):
        column = str(column)
        d = self._headings.setdefault(column, {})
        if option is not None and not kw:
            return d.get(_norm_key(option), "")
        if kw:
            for k, v in kw.items():
                d[_norm_key(k)] = v
            _g.mark_dirty(self)
            return None
        return dict(d)

    def column(self, column, option=None, **kw):
        column = str(column)
        d = self._colopts.setdefault(column, {})
        if option is not None and not kw:
            return d.get(_norm_key(option), "")
        if kw:
            for k, v in kw.items():
                d[_norm_key(k)] = v
            _g.mark_dirty(self)
            return None
        return dict(d)

    def selection(self, selop=None, items=None):
        if selop is None:
            return tuple(self._sel)
        return tuple(self._sel)

    def selection_set(self, *items):
        items = _tk._flatten(items)
        self._sel = [str(i) for i in items]
        _g.mark_dirty(self)
        self._fire_event("Virtual", {"name": "<<TreeviewSelect>>"})

    def selection_add(self, *items):
        for i in _tk._flatten(items):
            if str(i) not in self._sel:
                self._sel.append(str(i))
        _g.mark_dirty(self)

    def selection_remove(self, *items):
        for i in _tk._flatten(items):
            if str(i) in self._sel:
                self._sel.remove(str(i))
        _g.mark_dirty(self)

    def selection_toggle(self, *items):
        for i in _tk._flatten(items):
            i = str(i)
            if i in self._sel:
                self._sel.remove(i)
            else:
                self._sel.append(i)
        _g.mark_dirty(self)

    def focus(self, item=None):
        if item is None:
            return self._focus
        self._focus = str(item)
        return None

    def see(self, item):
        p = self._parents.get(str(item))
        while p:
            self._items[p]["open"] = True
            p = self._parents.get(p)
        _g.mark_dirty(self)

    def tag_configure(self, tagname, option=None, **kw):
        d = self._tagcfg.setdefault(tagname, {})
        if kw:
            for k, v in kw.items():
                d[_norm_key(k)] = v
            _g.mark_dirty(self)
            return None
        if option:
            return d.get(_norm_key(option), "")
        return dict(d)

    def tag_has(self, tagname, item=None):
        if item is None:
            return tuple(i for i, it in self._items.items() if tagname in it.get("tags", []))
        return tagname in self._items[str(item)].get("tags", [])

    def tag_bind(self, tagname, sequence=None, callback=None):
        return self.bind(sequence, callback, "+")

    def identify_row(self, y):
        return self._last_row

    def identify_column(self, x):
        return getattr(self, "_last_col", "#0")

    def identify_region(self, x, y):
        return "cell" if self._last_row else "nothing"

    def identify_element(self, x, y):
        return ""

    def identify(self, component, x, y):
        return self.identify_row(y) if component == "row" else ""

    def bbox(self, item, column=None):
        return ""

    def xview(self, *a):
        return (0.0, 1.0)

    def yview(self, *a):
        return (0.0, 1.0)

    def _fire_event(self, typ, ev):
        if "row" in ev:
            self._last_row = ev.get("row") or ""
            self._last_col = ev.get("col") or "#0"
        return _tk.Misc._fire_event(self, typ, ev)

    def _ui_event(self, ev):
        k = ev.get("k")
        if k == "tsel":
            self._sel = [str(s) for s in ev.get("sel", [])]
            if self._sel:
                self._focus = self._sel[-1]
                self._last_row = self._sel[-1]
            self._fire_event("Virtual", {"name": "<<TreeviewSelect>>"})
        elif k == "topen":
            iid = str(ev.get("id"))
            if iid in self._items:
                self._items[iid]["open"] = bool(ev.get("open"))
                self._fire_event("Virtual", {"name": "<<TreeviewOpen>>" if ev.get("open") else "<<TreeviewClose>>"})
        elif k == "head":
            cmd = self._headings.get(str(ev.get("col")), {}).get("command")
            if callable(cmd):
                _g._safe_call(cmd)


class LabeledScale(Frame):
    def __init__(self, master=None, variable=None, from_=0, to=10, **kw):
        Frame.__init__(self, master, **kw)
        self._variable = variable or _tk.IntVar(master)
        self.label = Label(self, textvariable=self._variable)
        self.label.pack(side="top")
        self.scale = Scale(self, variable=self._variable, from_=from_, to=to)
        self.scale.pack(side="top", fill="x")

    @property
    def value(self):
        return self._variable.get()

    @value.setter
    def value(self, val):
        self._variable.set(val)


class OptionMenu(Menubutton):
    def __init__(self, master, variable, default=None, *values, **kwargs):
        self._variable = variable
        self._command = kwargs.pop("command", None)
        kwargs.pop("direction", None)
        style = kwargs.pop("style", None)
        self._values_list = [str(v) for v in values]
        cnf = {"textvariable": variable, "values": self._values_list}
        if style:
            cnf["style"] = style
        _tk.Widget.__init__(self, master, "menubutton", cnf, kwargs)
        if default is not None and variable is not None:
            variable.set(default)

    _tkcls = "OptionMenu"

    def set_menu(self, default=None, *values):
        self._values_list = [str(v) for v in values]
        self.configure(values=self._values_list)
        if default is not None and self._variable is not None:
            self._variable.set(default)

    def _ui_event(self, ev):
        if ev.get("k") == "val":
            v = ev.get("v", "")
            if self._variable is not None:
                self._variable._from_ui(v)
            if callable(self._command):
                _g._safe_call(self._command, v)

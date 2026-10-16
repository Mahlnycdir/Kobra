"""tkinter-Nachbau fuer PyIDE.

Bildet die tkinter-API nach und zeichnet die Fenster in der IDE (HTML statt Tk).
Die meisten Programme laufen unveraendert. Nicht unterstuetzt: Tcl-Skripte,
eigene Tk-Erweiterungen und einige selten genutzte Optionen.
"""
import re as _re
import sys as _sys

import pyide_gui as _g
from tkinter.constants import *  # noqa: F401,F403

TkVersion = 8.6
TclVersion = 8.6
READABLE = 2
WRITABLE = 4
EXCEPTION = 8
wantobjects = 1

_default_root = None
_support_default_root = True
_varnum = 0
_quit_stack = []


class TclError(Exception):
    pass


class EventType(str):
    pass


# ------------------------------------------------------------ Hilfsfunktionen
def _flatten(seq):
    res = []
    for item in seq:
        if isinstance(item, (tuple, list)):
            res.extend(_flatten(item))
        elif item is not None:
            res.append(item)
    return res


def _cnfmerge(cnf, kw=None):
    out = {}
    if isinstance(cnf, dict):
        out.update(cnf)
    elif isinstance(cnf, (list, tuple)):
        for c in cnf:
            if isinstance(c, dict):
                out.update(c)
    if kw:
        out.update(kw)
    return out


_ALIASES = {
    "bg": "background", "fg": "foreground", "bd": "borderwidth",
    "from_": "from", "in_": "in", "class_": "class",
    "invcmd": "invalidcommand", "vcmd": "validatecommand",
}


def _norm_key(k):
    k = str(k).lstrip("-")
    k = _ALIASES.get(k, k)
    if k.endswith("_") and k[:-1] in ("from", "in", "class"):
        k = k[:-1]
    return k


def _pixels(v, default=0):
    """Tk-Bildschirmmasse (10, '2c', '1i', '5m', '12p') in Pixel."""
    if v is None or v == "":
        return default
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    try:
        unit = s[-1]
        if unit in "cimp":
            num = float(s[:-1])
            return num * {"c": 37.795, "i": 96.0, "m": 3.7795, "p": 1.3333}[unit]
        return float(s)
    except ValueError:
        return default


def _pad(v):
    if v is None:
        return [0, 0]
    if isinstance(v, (tuple, list)):
        if len(v) == 1:
            return [_pixels(v[0]), _pixels(v[0])]
        return [_pixels(v[0]), _pixels(v[1])]
    if isinstance(v, str) and " " in v.strip():
        a, b = v.split()[:2]
        return [_pixels(a), _pixels(b)]
    p = _pixels(v)
    return [p, p]


def _tcl_split(s):
    """Tcl-Liste ('{Times New Roman} 12 bold') in Teile zerlegen."""
    out, buf, depth = [], "", 0
    for ch in str(s):
        if ch == "{":
            if depth:
                buf += ch
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth:
                buf += ch
        elif ch.isspace() and depth == 0:
            if buf:
                out.append(buf)
                buf = ""
        else:
            buf += ch
    if buf:
        out.append(buf)
    return out


_NAMED_FONTS = {}


def _font_spec(f):
    if f is None or f == "":
        return None
    if hasattr(f, "_spec"):
        return f._spec()
    if isinstance(f, str):
        if f in _NAMED_FONTS:
            return _NAMED_FONTS[f]._spec()
        if f.startswith("Tk"):
            return {"named": f}
        parts = _tcl_split(f)
    else:
        parts = [str(p) for p in f]
    spec = {"family": parts[0] if parts else "TkDefaultFont"}
    if len(parts) > 1:
        try:
            spec["size"] = int(float(parts[1]))
        except ValueError:
            parts.insert(1, "")
    for p in parts[2:]:
        p = p.lower()
        if p == "bold":
            spec["weight"] = "bold"
        elif p == "italic":
            spec["slant"] = "italic"
        elif p == "underline":
            spec["underline"] = True
        elif p == "overstrike":
            spec["overstrike"] = True
    return spec


def _wire_value(key, value, owner=None):
    """Optionswert fuer die Oberflaeche aufbereiten."""
    if value is None:
        return None
    if isinstance(value, Variable):
        return value._name
    if isinstance(value, Image):
        return value.name
    if isinstance(value, Misc):
        return value._w
    if key == "font":
        return _font_spec(value)
    if callable(value):
        return True
    if key in ("width", "height", "borderwidth", "padx", "pady", "length", "wraplength",
               "highlightthickness", "sliderlength", "insertwidth", "selectborderwidth"):
        if isinstance(value, str) and value and value[-1] in "cimp":
            return _pixels(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    if isinstance(value, (tuple, list)):
        return [_wire_value(key, v) for v in value]
    if isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def _tclstr(v):
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _get_default_root(what=None):
    global _default_root
    if not _support_default_root:
        raise RuntimeError("No master specified and tkinter is configured to not support default root")
    if _default_root is None or not _default_root._alive:
        if what:
            # wie in Python 3.10+: implizit ein Fenster erzeugen
            pass
        _default_root = Tk()
    return _default_root


def NoDefaultRoot():
    global _support_default_root, _default_root
    _support_default_root = False
    _default_root = None


def getint(s):
    return int(float(s))


def getdouble(s):
    return float(s)


def getboolean(s):
    if isinstance(s, str):
        return s.lower() in ("1", "true", "yes", "on")
    return bool(s)


def mainloop(n=0):
    _get_default_root("mainloop").mainloop(n)


def image_names():
    return tuple(Image._registry.keys())


def image_types():
    return ("photo", "bitmap")


# ------------------------------------------------------------- Variablen
class Variable:
    _default = ""
    _registry = {}

    def __init__(self, master=None, value=None, name=None):
        global _varnum
        if master is None and _support_default_root:
            master = _default_root
        self._root = master._root() if master is not None else None
        if name is None:
            name = "PY_VAR%d" % _varnum
            _varnum += 1
        self._name = name
        self._traces = []
        existing = Variable._registry.get(name)
        if value is not None:
            self._value = self._coerce(value)
        elif existing is not None:
            self._value = existing._value
        else:
            self._value = self._default
        Variable._registry[name] = self
        _g.op("var", name, self._value)

    def _coerce(self, v):
        return v

    def __str__(self):
        return self._name

    def __repr__(self):
        return "<%s %s=%r>" % (type(self).__name__, self._name, self._value)

    def set(self, value):
        self._set(self._coerce(value), from_ui=False)

    initialize = set

    def _set(self, value, from_ui):
        self._value = value
        if not from_ui:
            _g.op("var", self._name, value)
        self._fire("write")

    def get(self):
        return self._value

    def _fire(self, mode):
        for modes, cb in list(self._traces):
            if mode in modes or (mode == "write" and "w" in modes) or (mode == "read" and "r" in modes):
                _g._safe_call(cb, self._name, "", mode)

    def trace_add(self, mode, callback):
        if isinstance(mode, str):
            mode = (mode,)
        name = "trace%d_%s" % (len(self._traces), id(callback))
        self._traces.append((tuple(mode), callback))
        return name

    def trace_remove(self, mode, cbname):
        self._traces = [t for t in self._traces
                        if "trace%d_%s" % (self._traces.index(t), id(t[1])) != cbname]

    def trace_info(self):
        return [(m, "cb") for m, _ in self._traces]

    def trace_variable(self, mode, callback):
        m = {"w": "write", "r": "read", "u": "unset"}.get(mode, mode)
        return self.trace_add(m, callback)

    trace = trace_variable

    def trace_vdelete(self, mode, cbname):
        self.trace_remove(mode, cbname)

    def trace_vinfo(self):
        return self.trace_info()

    def __eq__(self, other):
        return isinstance(other, Variable) and other._name == self._name

    def __hash__(self):
        return hash(self._name)

    def _from_ui(self, value):
        self._set(self._coerce_ui(value), from_ui=True)

    def _coerce_ui(self, v):
        try:
            return self._coerce(v)
        except (TypeError, ValueError):
            return v


class StringVar(Variable):
    _default = ""

    def _coerce(self, v):
        return v if isinstance(v, str) else str(v)

    def get(self):
        v = self._value
        return v if isinstance(v, str) else str(v)


class IntVar(Variable):
    _default = 0

    def _coerce(self, v):
        if isinstance(v, bool):
            return int(v)
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                return 0
            return int(float(v))
        return int(v)

    def get(self):
        v = self._value
        try:
            return self._coerce(v)
        except (TypeError, ValueError):
            raise TclError('expected integer but got "%s"' % v)


class DoubleVar(Variable):
    _default = 0.0

    def _coerce(self, v):
        if isinstance(v, str) and v.strip() == "":
            return 0.0
        return float(v)

    def get(self):
        try:
            return float(self._value)
        except (TypeError, ValueError):
            raise TclError('expected floating-point number but got "%s"' % self._value)


class BooleanVar(Variable):
    _default = False

    def _coerce(self, v):
        if isinstance(v, str):
            return v.strip().lower() in ("1", "true", "yes", "on")
        return bool(v)

    def get(self):
        return bool(self._coerce(self._value))


# --------------------------------------------------------------- Ereignisse
class Event:
    def __repr__(self):
        attrs = {k: v for k, v in self.__dict__.items() if v not in ("??", None)}
        return "<%s event %s>" % (getattr(self, "type", "?"), attrs)


_MODIFIERS = {
    "Control": "Control", "Shift": "Shift", "Lock": "Lock", "Alt": "Alt", "Option": "Alt",
    "Meta": "Meta", "Command": "Meta", "Mod1": "Meta", "Mod2": "Alt",
    "B1": "B1", "B2": "B2", "B3": "B3", "B4": "B4", "B5": "B5",
    "Button1": "B1", "Button2": "B2", "Button3": "B3",
    "Double": "Double", "Triple": "Triple", "Quadruple": "Triple", "Any": "Any",
}
_TYPES = {
    "ButtonPress": "ButtonPress", "Button": "ButtonPress", "ButtonRelease": "ButtonRelease",
    "Motion": "Motion", "KeyPress": "KeyPress", "Key": "KeyPress", "KeyRelease": "KeyRelease",
    "Enter": "Enter", "Leave": "Leave", "FocusIn": "FocusIn", "FocusOut": "FocusOut",
    "Configure": "Configure", "MouseWheel": "MouseWheel", "Destroy": "Destroy", "Map": "Map",
    "Unmap": "Unmap", "Expose": "Expose", "Visibility": "Visibility", "Activate": "Activate",
    "Deactivate": "Deactivate",
}
_CHAR_KEYSYMS = {
    " ": "space", "!": "exclam", '"': "quotedbl", "#": "numbersign", "$": "dollar",
    "%": "percent", "&": "ampersand", "'": "apostrophe", "(": "parenleft", ")": "parenright",
    "*": "asterisk", "+": "plus", ",": "comma", "-": "minus", ".": "period", "/": "slash",
    ":": "colon", ";": "semicolon", "<": "less", "=": "equal", ">": "greater", "?": "question",
    "@": "at", "[": "bracketleft", "\\": "backslash", "]": "bracketright", "^": "asciicircum",
    "_": "underscore", "`": "grave", "{": "braceleft", "|": "bar", "}": "braceright", "~": "asciitilde",
}


def _parse_sequence(seq):
    """'<Control-Button-1>' -> (typ, detail, modifiers)"""
    seq = str(seq)
    if seq.startswith("<<") and seq.endswith(">>"):
        return ("Virtual", seq, frozenset())
    if not seq.startswith("<"):
        ch = seq[-1:]
        return ("KeyPress", _CHAR_KEYSYMS.get(ch, ch), frozenset())
    body = seq
    # mehrere Ereignisse hintereinander: nur das letzte zaehlt
    m = list(_re.finditer(r"<([^<>]+)>", seq))
    if m:
        body = m[-1].group(1)
    parts = body.split("-")
    mods, typ, detail = set(), None, None
    for p in parts:
        if p == "" and detail is None:
            detail = "minus"
            continue
        if typ is None and detail is None and p in _MODIFIERS:
            mods.add(_MODIFIERS[p])
        elif typ is None and detail is None and p in _TYPES:
            typ = _TYPES[p]
        else:
            detail = p
    if typ is None:
        if detail is None:
            raise TclError('bad event pattern "%s"' % seq)
        if detail.isdigit() and len(detail) == 1:
            typ = "ButtonPress"
        else:
            typ = "KeyPress"
    if typ in ("ButtonPress", "ButtonRelease") and detail is not None:
        try:
            detail = int(detail)
        except ValueError:
            pass
    if typ == "MouseWheel":
        detail = None
    return (typ, detail, frozenset(mods))


_JS_TYPES = {
    "ButtonPress": "down", "ButtonRelease": "up", "Motion": "move", "KeyPress": "key",
    "KeyRelease": "keyup", "Enter": "enter", "Leave": "leave", "FocusIn": "focus",
    "FocusOut": "blur", "Configure": "configure", "MouseWheel": "wheel",
}

# tag -> [(pattern, func, sequence)]
_bindings = {}
_func_names = {}


def _register_binding(tag, sequence, func, add):
    pat = _parse_sequence(sequence)
    lst = _bindings.setdefault(tag, [])
    if not add:
        lst[:] = [b for b in lst if b[0] != pat]
    name = "%d%s" % (id(func), getattr(func, "__name__", "func"))
    _func_names[name] = func
    lst.append((pat, func, sequence, name))
    _announce_bindings(tag)
    return name


def _announce_bindings(tag):
    types = set()
    for (typ, detail, mods), _f, _s, _n in _bindings.get(tag, []):
        js = _JS_TYPES.get(typ)
        if js:
            types.add(js)
        if typ == "Motion" and mods & {"B1", "B2", "B3"}:
            types.add("drag")
        if typ == "ButtonPress" and "Double" in mods:
            types.add("dbl")
    _g.op("bind", tag, sorted(types))


def _unbind(tag, sequence, funcid=None):
    pat = _parse_sequence(sequence)
    lst = _bindings.get(tag, [])
    lst[:] = [b for b in lst if not (b[0] == pat and (funcid is None or b[3] == funcid))]
    _announce_bindings(tag)


def _match(pattern, ev_typ, ev):
    typ, detail, mods = pattern
    if typ != ev_typ:
        return -1
    state = ev.get("state") or []
    score = 0
    if detail is not None:
        if typ in ("ButtonPress", "ButtonRelease"):
            if ev.get("num") != detail:
                return -1
        elif typ in ("KeyPress", "KeyRelease"):
            if ev.get("keysym") != detail:
                return -1
        elif typ == "Virtual":
            if ev.get("name") != detail:
                return -1
        score += 10
    need = set(mods) - {"Double", "Triple", "Any"}
    if not need.issubset(set(state)):
        return -1
    if "Double" in mods:
        if not ev.get("dbl"):
            return -1
        score += 5
    score += len(need)
    return score


def _make_event(widget, ev, typ):
    e = Event()
    e.widget = widget
    e.type = EventType(typ)
    e.serial = 0
    e.time = int(ev.get("time", 0))
    e.x = int(round(ev.get("x", 0)))
    e.y = int(round(ev.get("y", 0)))
    e.x_root = int(round(ev.get("X", e.x)))
    e.y_root = int(round(ev.get("Y", e.y)))
    e.num = ev.get("num", "??")
    e.char = ev.get("char", "")
    e.keysym = ev.get("keysym", "??")
    e.keycode = ev.get("keycode", 0)
    e.keysym_num = ev.get("keycode", 0)
    e.delta = int(ev.get("delta", 0))
    e.width = ev.get("width", "??")
    e.height = ev.get("height", "??")
    st = 0
    for i, m in enumerate(("Shift", "Lock", "Control", "Meta", "Alt")):
        if m in (ev.get("state") or []):
            st |= 1 << i
    for i, b in enumerate(("B1", "B2", "B3")):
        if b in (ev.get("state") or []):
            st |= 1 << (8 + i)
    e.state = st
    e.focus = False
    e.send_event = False
    return e


def _fire_tags(tags, widget, ev, typ, event_obj=None):
    e = event_obj or _make_event(widget, ev, typ)
    for tag in tags:
        best, best_score = None, -1
        for pat, func, _seq, _name in _bindings.get(tag, []):
            s = _match(pat, typ, ev)
            if s > best_score:
                best, best_score = func, s
        if best is not None:
            res = _g._safe_call(best, e)
            if res == "break":
                return "break"
    return None


# ------------------------------------------------------------------- Misc
class _TkApp:
    """Ersatz fuer den Tcl-Interpreter (root.tk)."""

    def __init__(self):
        self._vars = {}
        self._cmds = {}

    def call(self, *args):
        args = _flatten(args)
        if not args:
            return ""
        a0 = str(args[0])
        if a0 == "tk" and len(args) > 1 and args[1] == "scaling":
            return 1.3333
        if a0 == "tk" and len(args) > 1 and args[1] == "windowingsystem":
            return "x11"
        if a0 == "info" and len(args) > 1 and args[1] == "patchlevel":
            return "8.6.13"
        if a0 in self._cmds:
            return self._cmds[a0](*args[1:])
        return ""

    def eval(self, script):
        return ""

    def getint(self, s):
        return getint(s)

    def getdouble(self, s):
        return getdouble(s)

    def getboolean(self, s):
        return getboolean(s)

    def splitlist(self, s):
        if isinstance(s, (tuple, list)):
            return tuple(s)
        return tuple(_tcl_split(s))

    split = splitlist

    def createcommand(self, name, func):
        self._cmds[name] = func

    def deletecommand(self, name):
        self._cmds.pop(name, None)

    def globalsetvar(self, name, value):
        v = Variable._registry.get(name)
        if v:
            v.set(value)
        self._vars[name] = value

    setvar = globalsetvar

    def globalgetvar(self, name):
        v = Variable._registry.get(name)
        return v.get() if v else self._vars.get(name, "")

    getvar = globalgetvar

    def wantobjects(self, *a):
        return 1

    def willdispatch(self):
        pass

    def mainloop(self, n=0):
        mainloop(n)

    def dooneevent(self, flags=0):
        _g.update()
        return 0

    def record(self, s):
        return ""

    def adderrorinfo(self, s):
        pass

    def exprstring(self, s):
        return str(s)

    def interpaddr(self):
        return 0


class Misc:
    _last_child_ids = None
    _w = "."
    _alive = True
    _tkcls = "Misc"
    _defaults = {}
    _ttk = False
    _style_class = None

    # ----------------------------------------------------- Optionen
    def _pre_options(self, kw):
        """Wird vor dem Senden aufgerufen; kann Optionen abfangen."""
        return kw

    def _wire(self, opts):
        out = {}
        for k, v in opts.items():
            if k in ("class", "name"):
                continue
            out[k] = _wire_value(k, v, self)
        return out

    def configure(self, cnf=None, **kw):
        if cnf is None and not kw:
            res = {}
            for k in set(self._defaults) | set(self._opts):
                res[k] = (k, k, k, self._defaults.get(k, ""), self.cget(k))
            return res
        if isinstance(cnf, str) and not kw:
            k = _norm_key(cnf)
            return (k, k, k, self._defaults.get(k, ""), self.cget(k))
        kw = {_norm_key(k): v for k, v in _cnfmerge(cnf, kw).items()}
        kw = self._pre_options(kw)
        if not kw:
            return None
        self._opts.update(kw)
        self._options_changed(kw)
        _g.op("cfg", self._w, self._wire(kw))
        return None

    config = configure

    def _options_changed(self, kw):
        pass

    def cget(self, key):
        key = _norm_key(key)
        if key in self._opts:
            v = self._opts[key]
            if isinstance(v, Variable):
                return v._name
            return v
        return self._defaults.get(key, "")

    __getitem__ = cget

    def __setitem__(self, key, value):
        self.configure({key: value})

    def keys(self):
        return sorted(set(self._defaults) | set(self._opts))

    def __str__(self):
        return self._w

    def __repr__(self):
        return "<%s.%s object %s>" % (self.__class__.__module__, self.__class__.__qualname__, self._w)

    # ---------------------------------------------------------- Zeit
    def after(self, ms, func=None, *args):
        if func is None:
            import time
            time.sleep(float(ms) / 1000.0)
            return None
        if ms == "idle":
            ms = 0
        return _g.add_timer(ms, func, args)

    def after_idle(self, func, *args):
        return _g.add_timer(0, func, args)

    def after_cancel(self, id):
        if id:
            _g.cancel_timer(id)

    def after_info(self, id=None):
        return tuple(_g._S.timer_funcs.keys())

    # -------------------------------------------------------- Schleife
    def mainloop(self, n=0):
        root = self._root()
        flag = [False]
        _quit_stack.append(flag)
        try:
            _g.run_loop(lambda: flag[0] or not root._alive)
        finally:
            _quit_stack.remove(flag)

    def quit(self):
        if _quit_stack:
            _quit_stack[-1][0] = True

    def update(self):
        _g.update()

    def update_idletasks(self):
        _g.flush()

    def wait_window(self, window=None):
        if window is None:
            window = self
        _g.run_loop(lambda: not window._alive)

    def wait_variable(self, name="PY_VAR"):
        var = name if isinstance(name, Variable) else Variable._registry.get(str(name))
        if var is None:
            return
        changed = [False]
        var._traces.append((("write",), lambda *a: changed.__setitem__(0, True)))
        _g.run_loop(lambda: changed[0])

    waitvar = wait_variable

    def wait_visibility(self, window=None):
        _g.flush()

    def dooneevent(self, *a):
        _g.update()

    # -------------------------------------------------------- Bindungen
    def bind(self, sequence=None, func=None, add=None):
        return self._bind_tag(self._w, sequence, func, add)

    def _bind_tag(self, tag, sequence, func, add):
        if sequence is None:
            return tuple(b[2] for b in _bindings.get(tag, []))
        if func is None:
            for b in _bindings.get(tag, []):
                if b[2] == sequence:
                    return b[3]
            return ""
        if isinstance(func, str):
            return ""
        return _register_binding(tag, sequence, func, add)

    def unbind(self, sequence, funcid=None):
        _unbind(self._w, sequence, funcid)

    def bind_all(self, sequence=None, func=None, add=None):
        return self._bind_tag("all", sequence, func, add)

    def unbind_all(self, sequence):
        _unbind("all", sequence)

    def bind_class(self, className, sequence=None, func=None, add=None):
        return self._bind_tag("class:" + className, sequence, func, add)

    def unbind_class(self, className, sequence):
        _unbind("class:" + className, sequence)

    def bindtags(self, tagList=None):
        if tagList is None:
            return tuple(self._bindtags())
        self._custom_tags = [str(t) for t in tagList]
        return None

    def _bindtags(self):
        if getattr(self, "_custom_tags", None):
            return self._custom_tags
        top = self.winfo_toplevel()
        tags = [self._w, "class:" + self.winfo_class()]
        if top is not self:
            tags.append(top._w)
        tags.append("all")
        return tags

    def event_add(self, virtual, *sequences):
        pass

    def event_delete(self, virtual, *sequences):
        pass

    def event_info(self, virtual=None):
        return ()

    def event_generate(self, sequence, **kw):
        typ, detail, mods = _parse_sequence(sequence)
        ev = dict(kw)
        if typ == "Virtual":
            ev["name"] = detail
        elif typ in ("ButtonPress", "ButtonRelease"):
            ev.setdefault("num", detail if detail is not None else 1)
        elif typ in ("KeyPress", "KeyRelease"):
            ev.setdefault("keysym", detail or ev.get("keysym", ""))
        ev["state"] = list(mods)
        if "Double" in mods:
            ev["dbl"] = True
        self._fire_event(typ, ev)

    def _fire_event(self, typ, ev):
        return _fire_tags(self._bindtags(), self, ev, typ)

    # ---------------------------------------------------- Fokus usw.
    def focus_set(self):
        _Focus.widget = self
        _g.op("focus", self._w)

    focus = focus_set

    def focus_force(self):
        self.focus_set()

    def focus_get(self):
        return _Focus.widget

    def focus_displayof(self):
        return _Focus.widget

    def focus_lastfor(self):
        return _Focus.widget

    def tk_focusNext(self):
        return None

    def tk_focusPrev(self):
        return None

    def grab_set(self):
        pass

    def grab_set_global(self):
        pass

    def grab_release(self):
        pass

    def grab_current(self):
        return None

    def grab_status(self):
        return None

    def bell(self, displayof=0):
        _g.op("bell")

    def lift(self, aboveThis=None):
        _g.op("raise", self._w)

    tkraise = lift

    def lower(self, belowThis=None):
        _g.op("lower", self._w)

    def option_add(self, pattern, value, priority=None):
        _Options.db[pattern] = value

    def option_clear(self):
        _Options.db.clear()

    def option_get(self, name, className):
        return _Options.db.get(name, "")

    def option_readfile(self, fileName, priority=None):
        pass

    def tk_setPalette(self, *args, **kw):
        pass

    def tk_bisque(self):
        pass

    def clipboard_clear(self, **kw):
        _Clipboard.text = ""

    def clipboard_append(self, string, **kw):
        _Clipboard.text += str(string)
        _g.op("clipboard", _Clipboard.text)

    def clipboard_get(self, **kw):
        return _Clipboard.text

    def selection_get(self, **kw):
        return _Clipboard.text

    def register(self, func, subst=None, needcleanup=1):
        name = "%dcb_%s" % (id(func), getattr(func, "__name__", "f"))
        _func_names[name] = func
        self._root().tk._cmds[name] = func
        return name

    _register = register

    def deletecommand(self, name):
        _func_names.pop(name, None)

    def nametowidget(self, name):
        name = str(name)
        if isinstance(name, Misc):
            return name
        root = self._root()
        if name == ".":
            return root
        w = root
        for part in name.lstrip(".").split("."):
            if part:
                w = w.children[part]
        return w

    _nametowidget = nametowidget

    def _root(self):
        w = self
        while getattr(w, "master", None) is not None:
            w = w.master
        return w

    def getvar(self, name="PY_VAR"):
        return self._root().tk.globalgetvar(name)

    def setvar(self, name="PY_VAR", value="1"):
        self._root().tk.globalsetvar(name, value)

    def getint(self, s):
        return getint(s)

    def getdouble(self, s):
        return getdouble(s)

    def getboolean(self, s):
        return getboolean(s)

    def _getints(self, s):
        return tuple(int(x) for x in _tcl_split(s)) if s else None

    def _nametowidget_or_none(self, name):
        try:
            return self.nametowidget(name)
        except Exception:
            return None

    # --------------------------------------------------------- winfo
    def _geom(self):
        g = _g.geometry_of(self._w)
        if not g:
            w = _pixels(self._opts.get("width"), 1) if self._tkcls in ("Canvas", "Frame", "Toplevel", "Tk") else 1
            h = _pixels(self._opts.get("height"), 1) if self._tkcls in ("Canvas", "Frame", "Toplevel", "Tk") else 1
            return [0, 0, w or 1, h or 1, 0, 0, w or 1, h or 1]
        return g

    def winfo_width(self):
        return int(round(self._geom()[2]))

    def winfo_height(self):
        return int(round(self._geom()[3]))

    def winfo_x(self):
        return int(round(self._geom()[0]))

    def winfo_y(self):
        return int(round(self._geom()[1]))

    def winfo_rootx(self):
        return int(round(self._geom()[4]))

    def winfo_rooty(self):
        return int(round(self._geom()[5]))

    def winfo_reqwidth(self):
        g = self._geom()
        return int(round(g[6] if len(g) > 6 else g[2]))

    def winfo_reqheight(self):
        g = self._geom()
        return int(round(g[7] if len(g) > 7 else g[3]))

    def winfo_geometry(self):
        g = self._geom()
        return "%dx%d+%d+%d" % (g[2], g[3], g[0], g[1])

    def winfo_screenwidth(self):
        return int(_g._S.screen[0])

    def winfo_screenheight(self):
        return int(_g._S.screen[1])

    def winfo_vrootwidth(self):
        return self.winfo_screenwidth()

    def winfo_vrootheight(self):
        return self.winfo_screenheight()

    def winfo_screenmmwidth(self):
        return int(self.winfo_screenwidth() / 3.78)

    def winfo_screenmmheight(self):
        return int(self.winfo_screenheight() / 3.78)

    def winfo_fpixels(self, number):
        return _pixels(number)

    def winfo_pixels(self, number):
        return int(round(_pixels(number)))

    def winfo_pointerx(self):
        return int(_Pointer.x)

    def winfo_pointery(self):
        return int(_Pointer.y)

    def winfo_pointerxy(self):
        return (int(_Pointer.x), int(_Pointer.y))

    def winfo_children(self):
        return [c for c in self.children.values() if c._alive]

    def winfo_class(self):
        return self._style_class or self._tkcls

    def winfo_name(self):
        return getattr(self, "_name", "tk")

    def winfo_parent(self):
        m = getattr(self, "master", None)
        return m._w if m is not None else ""

    def winfo_toplevel(self):
        w = self
        while w is not None and not isinstance(w, (Tk, Toplevel)):
            w = getattr(w, "master", None)
        return w or self._root()

    def winfo_exists(self):
        return 1 if self._alive else 0

    def winfo_ismapped(self):
        return 1 if self._alive else 0

    def winfo_viewable(self):
        return 1 if self._alive else 0

    def winfo_manager(self):
        return getattr(self, "_manager", None) or ""

    def winfo_id(self):
        return abs(hash(self._w)) % 100000

    def winfo_rgb(self, color):
        res = _g.sync_call("rgb", {"color": color})
        if isinstance(res, list):
            return tuple(int(v) * 257 for v in res)
        return (0, 0, 0)

    def winfo_depth(self):
        return 24

    def winfo_cells(self):
        return 256

    def winfo_visual(self):
        return "truecolor"

    def winfo_server(self):
        return "PyIDE"

    def winfo_containing(self, rootX, rootY, displayof=0):
        return None

    def winfo_atom(self, name, displayof=0):
        return 0

    # ---------------------------------------------------------- Geometrie
    def _master_info(self):
        if not hasattr(self, "_grid_cols"):
            self._grid_cols = {}
            self._grid_rows = {}
            self._propagate = {"pack": True, "grid": True}
        return self

    def grid_columnconfigure(self, index, cnf={}, **kw):
        return self._rowcol("col", index, _cnfmerge(cnf, kw))

    columnconfigure = grid_columnconfigure

    def grid_rowconfigure(self, index, cnf={}, **kw):
        return self._rowcol("row", index, _cnfmerge(cnf, kw))

    rowconfigure = grid_rowconfigure

    def _rowcol(self, which, index, kw):
        self._master_info()
        store = self._grid_cols if which == "col" else self._grid_rows
        if isinstance(index, (list, tuple)):
            indices = list(index)
        elif index == "all":
            indices = sorted({s._mopts.get("column" if which == "col" else "row", 0)
                              for s in self._slaves("grid")})
        else:
            indices = [index]
        if not kw:
            i = indices[0] if indices else 0
            d = store.get(i, {})
            return {"minsize": d.get("minsize", 0), "pad": d.get("pad", 0),
                    "uniform": d.get("uniform"), "weight": d.get("weight", 0)}
        for i in indices:
            if isinstance(i, Misc):
                i = i._mopts.get("column" if which == "col" else "row", 0)
            d = store.setdefault(int(i), {})
            for k, v in kw.items():
                k = _norm_key(k)
                if k in ("weight", "minsize", "pad"):
                    d[k] = _pixels(v) if k != "weight" else int(v)
                elif k == "uniform":
                    d[k] = v
            _g.op("rowcol", self._w, which, int(i), d)
        return None

    def grid_propagate(self, flag=None):
        self._master_info()
        if flag is None:
            return self._propagate["grid"]
        self._propagate["grid"] = bool(flag)
        _g.op("propagate", self._w, "grid", bool(flag))

    def pack_propagate(self, flag=None):
        self._master_info()
        if flag is None:
            return self._propagate["pack"]
        self._propagate["pack"] = bool(flag)
        _g.op("propagate", self._w, "pack", bool(flag))

    propagate = pack_propagate

    def _slaves(self, manager):
        res = []
        for w in _all_widgets_under(self._root()):
            if w._alive and getattr(w, "_manager", None) == manager and w._layout_master() is self:
                res.append(w)
        return res

    def pack_slaves(self):
        return self._slaves("pack")

    slaves = pack_slaves

    def place_slaves(self):
        return self._slaves("place")

    def grid_slaves(self, row=None, column=None):
        res = []
        for w in self._slaves("grid"):
            o = w._mopts
            if row is not None and not (o["row"] <= row < o["row"] + o["rowspan"]):
                continue
            if column is not None and not (o["column"] <= column < o["column"] + o["columnspan"]):
                continue
            res.append(w)
        return list(reversed(res))

    def grid_size(self):
        cols = rows = 0
        for w in self._slaves("grid"):
            o = w._mopts
            cols = max(cols, o["column"] + o["columnspan"])
            rows = max(rows, o["row"] + o["rowspan"])
        return (cols, rows)

    size = grid_size

    def grid_bbox(self, column=None, row=None, col2=None, row2=None):
        g = self._geom()
        return (0, 0, int(g[2]), int(g[3]))

    bbox = grid_bbox

    def grid_anchor(self, anchor=None):
        if anchor is not None:
            _g.op("grid_anchor", self._w, anchor)

    def grid_location(self, x, y):
        return (0, 0)

    def destroy(self):
        if not self._alive:
            return
        for c in list(self.children.values()):
            c.destroy()
        self._alive = False
        if _bindings.get(self._w):
            _fire_tags([self._w], self, {}, "Destroy")
        _bindings.pop(self._w, None)
        _g.unregister(self._w)
        _g.op("destroy", self._w)
        m = getattr(self, "master", None)
        if m is not None:
            m.children.pop(getattr(self, "_name", ""), None)
        if _Focus.widget is self:
            _Focus.widget = None


def _all_widgets_under(w):
    stack = [w]
    while stack:
        x = stack.pop()
        yield x
        stack.extend(reversed(list(x.children.values())))


class _Focus:
    widget = None


class _Pointer:
    x = 0
    y = 0


class _Clipboard:
    text = ""


class _Options:
    db = {}


# ---------------------------------------------------------- Geometrie-Manager
class Pack:
    def pack_configure(self, cnf={}, **kw):
        kw = _cnfmerge(cnf, kw)
        if getattr(self, "_manager", None) == "pack":
            opts = dict(self._mopts)
        else:
            opts = {"side": "top", "fill": "none", "expand": False, "anchor": "center",
                    "padx": [0, 0], "pady": [0, 0], "ipadx": 0, "ipady": 0}
            if getattr(self, "_manager", None):
                _g.op("forget", self._w)
        for k, v in kw.items():
            k = _norm_key(k)
            if k in ("padx", "pady"):
                opts[k] = _pad(v)
            elif k in ("ipadx", "ipady"):
                opts[k] = _pixels(v)
            elif k == "expand":
                opts[k] = getboolean(v) if isinstance(v, str) else bool(v)
            elif k in ("before", "after", "in"):
                opts[k] = v._w if isinstance(v, Misc) else str(v)
            elif k in ("side", "fill", "anchor"):
                opts[k] = str(v)
        self._manager = "pack"
        self._mopts = opts
        _g.op("pack", self._w, opts)
        opts.pop("before", None)
        opts.pop("after", None)

    pack = configure_pack = pack_configure

    def pack_forget(self):
        if getattr(self, "_manager", None) == "pack":
            self._manager = None
            _g.op("forget", self._w)

    forget = pack_forget

    def pack_info(self):
        d = dict(getattr(self, "_mopts", {}))
        d["in"] = self._layout_master()
        return d

    info = pack_info

    def _layout_master(self):
        m = getattr(self, "_mopts", {}).get("in")
        if m:
            try:
                return self.nametowidget(m)
            except Exception:
                pass
        return self.master


class Place:
    def place_configure(self, cnf={}, **kw):
        kw = _cnfmerge(cnf, kw)
        if getattr(self, "_manager", None) == "place":
            opts = dict(self._mopts)
        else:
            opts = {"anchor": "nw"}
            if getattr(self, "_manager", None):
                _g.op("forget", self._w)
        for k, v in kw.items():
            k = _norm_key(k)
            if k in ("x", "y", "width", "height"):
                opts[k] = _pixels(v) if v != "" else None
            elif k in ("relx", "rely", "relwidth", "relheight"):
                opts[k] = float(v) if v != "" else None
            elif k == "in":
                opts[k] = v._w if isinstance(v, Misc) else str(v)
            elif k in ("anchor", "bordermode"):
                opts[k] = str(v)
        self._manager = "place"
        self._mopts = opts
        _g.op("place", self._w, opts)

    place = place_configure

    def place_forget(self):
        if getattr(self, "_manager", None) == "place":
            self._manager = None
            _g.op("forget", self._w)

    def place_info(self):
        return dict(getattr(self, "_mopts", {}))


class Grid:
    def grid_configure(self, cnf={}, **kw):
        kw = _cnfmerge(cnf, kw)
        master = self.master
        if "in" in kw or "in_" in kw:
            master = kw.get("in", kw.get("in_"))
        if getattr(self, "_manager", None) == "grid":
            opts = dict(self._mopts)
        else:
            opts = {"column": 0, "columnspan": 1, "rowspan": 1, "sticky": "",
                    "padx": [0, 0], "pady": [0, 0], "ipadx": 0, "ipady": 0}
            prev = getattr(self, "_grid_removed", None)
            if prev:
                opts.update(prev)
            if "row" not in kw and "row" not in opts:
                nxt = 0
                for s in master._slaves("grid") if isinstance(master, Misc) else []:
                    if s is not self:
                        nxt = max(nxt, s._mopts["row"] + s._mopts["rowspan"])
                opts["row"] = nxt
            if getattr(self, "_manager", None):
                _g.op("forget", self._w)
        for k, v in kw.items():
            k = _norm_key(k)
            if k in ("padx", "pady"):
                opts[k] = _pad(v)
            elif k in ("ipadx", "ipady"):
                opts[k] = _pixels(v)
            elif k in ("row", "column", "rowspan", "columnspan"):
                opts[k] = int(v)
            elif k == "sticky":
                s = "".join(ch for ch in str(v).lower() if ch in "nsew")
                opts[k] = s
            elif k == "in":
                opts[k] = v._w if isinstance(v, Misc) else str(v)
        self._manager = "grid"
        self._mopts = opts
        _g.op("grid", self._w, opts)

    grid = grid_configure

    def grid_forget(self):
        if getattr(self, "_manager", None) == "grid":
            self._manager = None
            _g.op("forget", self._w)

    def grid_remove(self):
        if getattr(self, "_manager", None) == "grid":
            self._grid_removed = dict(self._mopts)
            self._manager = None
            _g.op("forget", self._w)

    def grid_info(self):
        d = dict(getattr(self, "_mopts", {}))
        d["in"] = self._layout_master()
        return d

    location = Misc.grid_location


# --------------------------------------------------------- Fenster (wm)
class Wm:
    def _wm_init(self):
        self._wm = {"title": "tk", "geometry": None, "protocols": {}, "state": "normal",
                    "resizable": (True, True), "attributes": {}}

    def wm_title(self, string=None):
        if string is None:
            return self._wm["title"]
        self._wm["title"] = str(string)
        _g.op("wm", self._w, "title", str(string))

    title = wm_title

    def wm_geometry(self, newGeometry=None):
        if newGeometry is None:
            g = self._geom()
            return "%dx%d+%d+%d" % (g[2], g[3], 0, 0)
        m = _re.match(r"^\s*(?:(\d+)x(\d+))?\s*(?:([+-]-?\d+)([+-]-?\d+))?\s*$", str(newGeometry))
        if not m:
            raise TclError('bad geometry specifier "%s"' % newGeometry)
        if m.group(1):
            w, h = int(m.group(1)), int(m.group(2))
            self._wm["geometry"] = (w, h)
            _g.op("wm", self._w, "geometry", [w, h])
        return ""

    geometry = wm_geometry

    def wm_minsize(self, width=None, height=None):
        if width is None:
            return self._wm.get("minsize", (1, 1))
        self._wm["minsize"] = (width, height)
        _g.op("wm", self._w, "minsize", [width, height])

    minsize = wm_minsize

    def wm_maxsize(self, width=None, height=None):
        if width is None:
            return self._wm.get("maxsize", (self.winfo_screenwidth(), self.winfo_screenheight()))
        self._wm["maxsize"] = (width, height)
        _g.op("wm", self._w, "maxsize", [width, height])

    maxsize = wm_maxsize

    def wm_resizable(self, width=None, height=None):
        if width is None:
            return self._wm["resizable"]
        self._wm["resizable"] = (bool(width), bool(height))

    resizable = wm_resizable

    def wm_protocol(self, name=None, func=None):
        if name is None:
            return tuple(self._wm["protocols"].keys())
        if func is None:
            return self._wm["protocols"].get(name, "")
        self._wm["protocols"][name] = func
        return ""

    protocol = wm_protocol

    def wm_state(self, newstate=None):
        if newstate is None:
            return self._wm["state"]
        self._wm["state"] = newstate
        _g.op("wm", self._w, "state", newstate)

    state = wm_state

    def wm_withdraw(self):
        self.wm_state("withdrawn")

    withdraw = wm_withdraw

    def wm_iconify(self):
        self.wm_state("iconic")

    iconify = wm_iconify

    def wm_deiconify(self):
        self.wm_state("normal")

    deiconify = wm_deiconify

    def wm_attributes(self, *args, **kw):
        if args and len(args) == 1 and not kw:
            return self._wm["attributes"].get(str(args[0]).lstrip("-"), "")
        if not args and not kw:
            return tuple(self._wm["attributes"].items())
        pairs = list(zip(args[::2], args[1::2])) + list(kw.items())
        for k, v in pairs:
            k = str(k).lstrip("-")
            self._wm["attributes"][k] = v
            _g.op("wm", self._w, "attr", [k, v if isinstance(v, (int, float, str, bool)) else str(v)])
        return ""

    attributes = wm_attributes

    def wm_overrideredirect(self, boolean=None):
        if boolean is None:
            return self._wm.get("override", False)
        self._wm["override"] = bool(boolean)
        _g.op("wm", self._w, "override", bool(boolean))

    overrideredirect = wm_overrideredirect

    def wm_iconbitmap(self, *a, **k):
        return ""

    iconbitmap = wm_iconbitmap

    def wm_iconphoto(self, *a, **k):
        return ""

    iconphoto = wm_iconphoto

    def wm_iconname(self, newName=None):
        return ""

    iconname = wm_iconname

    def wm_transient(self, master=None):
        return ""

    transient = wm_transient

    def wm_group(self, pathName=None):
        return ""

    group = wm_group

    def wm_positionfrom(self, who=None):
        return ""

    positionfrom = wm_positionfrom

    def wm_sizefrom(self, who=None):
        return ""

    sizefrom = wm_sizefrom

    def wm_aspect(self, *a):
        return ""

    aspect = wm_aspect

    def wm_frame(self):
        return self._w

    frame = wm_frame

    def wm_focusmodel(self, model=None):
        return "passive"

    focusmodel = wm_focusmodel

    def wm_client(self, name=None):
        return ""

    client = wm_client

    def wm_command(self, value=None):
        return ""

    command = wm_command

    def wm_iconmask(self, bitmap=None):
        return ""

    iconmask = wm_iconmask

    def wm_iconposition(self, x=None, y=None):
        return ""

    iconposition = wm_iconposition

    def wm_iconwindow(self, pathName=None):
        return ""

    iconwindow = wm_iconwindow

    def wm_manage(self, widget):
        pass

    manage = wm_manage

    def wm_forget(self, window):
        pass

    def _close_request(self):
        handler = self._wm["protocols"].get("WM_DELETE_WINDOW")
        if handler:
            _g._safe_call(handler)
        else:
            self.destroy()


class Tk(Misc, Wm):
    _tkcls = "Tk"
    _defaults = {"background": "#ececec", "borderwidth": 0}

    def __init__(self, screenName=None, baseName=None, className="Tk", useTk=True, sync=False, use=None):
        global _default_root
        self.master = None
        self.children = {}
        self._w = "."
        self._name = "tk"
        self._opts = {}
        self._alive = True
        self.tk = _TkApp()
        self._wm_init()
        self._wm["title"] = baseName or self._script_title()
        self._master_info()
        _g.register(self._w, self)
        _g._S.toplevels[self._w] = self
        _g.op("new", self._w, "Tk", None, {"title": self._wm["title"]})
        if _support_default_root and (_default_root is None or not _default_root._alive):
            _default_root = self

    @staticmethod
    def _script_title():
        import os
        try:
            return os.path.splitext(os.path.basename(_sys.argv[0]))[0] or "tk"
        except Exception:
            return "tk"

    def destroy(self):
        global _default_root
        if not self._alive:
            return
        Misc.destroy(self)
        _g._S.toplevels.pop(self._w, None)
        if _default_root is self:
            _default_root = None

    def report_callback_exception(self, exc, val, tb):
        import pyide_runtime
        pyide_runtime.print_user_traceback(exc, val, tb, prefix="Exception in Tkinter callback\n")

    def readprofile(self, baseName, className):
        pass

    def loadtk(self):
        pass

    def _pyide_event(self, ev):
        _dispatch_widget_event(self, ev)

    def __getattr__(self, attr):
        if attr.startswith("_"):
            raise AttributeError(attr)
        return getattr(self.tk, attr)


def Tcl(screenName=None, baseName=None, className="Tk", useTk=False):
    return Tk(screenName, baseName, className, useTk)


# ---------------------------------------------------------------- Widgets
class BaseWidget(Misc):
    _tkcls = "Widget"

    def _setup(self, master, cnf):
        if master is None:
            master = _get_default_root()
        self.master = master
        self.tk = master.tk if hasattr(master, "tk") else _get_default_root().tk
        name = cnf.pop("name", None)
        if not name:
            name = self.__class__.__name__.lower()
            if name[-1].isdigit():
                name += "!"
            if master._last_child_ids is None:
                master._last_child_ids = {}
            count = master._last_child_ids.get(name, 0) + 1
            master._last_child_ids[name] = count
            name = "!%s" % name if count == 1 else "!%s%d" % (name, count)
        self._name = str(name)
        self._w = ("." if master._w == "." else master._w + ".") + self._name
        self.children = {}
        old = master.children.get(self._name)
        if old is not None and old is not self:
            old.destroy()
        master.children[self._name] = self

    def __init__(self, master=None, cnf={}, *args, **kw):
        if isinstance(cnf, str):
            # interne tkinter-Signatur: (master, widgetName, cnf, kw)
            c2 = args[0] if len(args) > 0 else {}
            k2 = args[1] if len(args) > 1 else {}
            cnf = _cnfmerge(c2, k2)
        cnf = _cnfmerge(cnf, kw)
        self._setup(master, cnf)
        self._opts = {}
        self._alive = True
        self._manager = None
        self._mopts = {}
        kw2 = {_norm_key(k): v for k, v in cnf.items()}
        self._init_widget(kw2)
        kw2 = self._pre_options(kw2)
        self._opts.update(kw2)
        _g.register(self._w, self)
        _g.op("new", self._w, self._tkcls, self.master._w, self._create_opts())
        self._options_changed(kw2)
        self._after_create()

    def _init_widget(self, kw):
        pass

    def _create_opts(self):
        o = self._wire(self._opts)
        if self._ttk:
            o["_ttk"] = True
            st = self._effective_style()
            if st:
                o["_style"] = st
        return o

    def _after_create(self):
        pass

    def _pyide_event(self, ev):
        _dispatch_widget_event(self, ev)

    def destroy(self):
        Misc.destroy(self)


def _dispatch_widget_event(widget, ev):
    k = ev.get("k")
    if k == "ev":
        typ = {"down": "ButtonPress", "up": "ButtonRelease", "move": "Motion", "key": "KeyPress",
               "keyup": "KeyRelease", "enter": "Enter", "leave": "Leave", "focus": "FocusIn",
               "blur": "FocusOut", "configure": "Configure", "wheel": "MouseWheel",
               "virtual": "Virtual"}.get(ev.get("t"), ev.get("t"))
        if "X" in ev:
            _Pointer.x, _Pointer.y = ev.get("X", 0), ev.get("Y", 0)
        if typ == "FocusIn":
            _Focus.widget = widget
        if hasattr(widget, "_item_event") and ev.get("item") is not None:
            if widget._item_event(typ, ev) == "break":
                return
        widget._fire_event(typ, ev)
    elif k == "close":
        widget._close_request()
    elif hasattr(widget, "_ui_event"):
        widget._ui_event(ev)


class Widget(BaseWidget, Pack, Place, Grid):
    pass


class Toplevel(BaseWidget, Wm):
    _tkcls = "Toplevel"
    _defaults = {"background": "#ececec", "borderwidth": 0}

    def __init__(self, master=None, cnf={}, **kw):
        self._wm_init()
        self._wm["title"] = kw.pop("title", None) or "Toplevel"
        BaseWidget.__init__(self, master, "toplevel", cnf, kw)
        self._master_info()
        _g._S.toplevels[self._w] = self
        _g.op("wm", self._w, "title", self._wm["title"])

    def destroy(self):
        Misc.destroy(self)
        _g._S.toplevels.pop(self._w, None)


class Frame(Widget):
    _tkcls = "Frame"
    _defaults = {"background": "#ececec", "borderwidth": 0, "relief": "flat", "width": 0, "height": 0}

    def _init_widget(self, kw):
        self._master_info()


class LabelFrame(Frame):
    _tkcls = "LabelFrame"
    _defaults = {"background": "#ececec", "borderwidth": 2, "relief": "groove", "text": ""}


class _TextVarMixin:
    def _options_changed(self, kw):
        v = kw.get("textvariable")
        if isinstance(v, Variable):
            _g.op("var", v._name, v.get())


class Label(_TextVarMixin, Widget):
    _tkcls = "Label"
    _defaults = {"text": "", "background": "#ececec", "foreground": "black", "anchor": "center",
                 "justify": "center", "relief": "flat", "borderwidth": 0, "padx": 1, "pady": 1}


class Message(_TextVarMixin, Widget):
    _tkcls = "Message"
    _defaults = {"text": "", "aspect": 150, "width": 0}


class Button(_TextVarMixin, Widget):
    _tkcls = "Button"
    _defaults = {"text": "", "state": "normal", "relief": "raised", "padx": 3, "pady": 1}

    def invoke(self):
        cmd = self._opts.get("command")
        if callable(cmd) and self.cget("state") != "disabled":
            return cmd()
        return ""

    def flash(self):
        pass

    def _ui_event(self, ev):
        if ev.get("k") == "cmd":
            if self.cget("state") == "disabled":
                return
            cmd = self._opts.get("command")
            if callable(cmd):
                _g._safe_call(cmd)


class Checkbutton(Widget):
    _tkcls = "Checkbutton"
    _defaults = {"text": "", "onvalue": 1, "offvalue": 0, "state": "normal"}

    def _init_widget(self, kw):
        if "variable" not in kw or kw["variable"] is None:
            var = IntVar(self.master, name=self._w)
            kw["variable"] = var

    def _var(self):
        v = self._opts.get("variable")
        if isinstance(v, str):
            v = Variable._registry.get(v)
        return v

    def _options_changed(self, kw):
        v = kw.get("variable")
        if isinstance(v, Variable):
            _g.op("var", v._name, v.get())
        if "onvalue" in kw or "offvalue" in kw or "variable" in kw:
            _g.op("cfg", self._w, {"onvalue": _wire_value("x", self.cget("onvalue")),
                                   "offvalue": _wire_value("x", self.cget("offvalue"))})

    def _is_on(self):
        v = self._var()
        return v is not None and _tclstr(v.get()) == _tclstr(self.cget("onvalue"))

    def select(self):
        v = self._var()
        if v is not None:
            v.set(self.cget("onvalue"))

    def deselect(self):
        v = self._var()
        if v is not None:
            v.set(self.cget("offvalue"))

    def toggle(self):
        if self._is_on():
            self.deselect()
        else:
            self.select()

    def invoke(self):
        if self.cget("state") == "disabled":
            return ""
        self.toggle()
        cmd = self._opts.get("command")
        if callable(cmd):
            return cmd()
        return ""

    def flash(self):
        pass

    def _ui_event(self, ev):
        if ev.get("k") == "cmd":
            self.invoke()


class Radiobutton(Widget):
    _tkcls = "Radiobutton"
    _defaults = {"text": "", "value": "", "state": "normal"}

    def _init_widget(self, kw):
        if "variable" not in kw or kw["variable"] is None:
            kw["variable"] = _shared_radio_var(self.master)

    def _var(self):
        v = self._opts.get("variable")
        if isinstance(v, str):
            v = Variable._registry.get(v)
        return v

    def _options_changed(self, kw):
        v = kw.get("variable")
        if isinstance(v, Variable):
            _g.op("var", v._name, v.get())

    def select(self):
        v = self._var()
        if v is not None:
            v.set(self.cget("value"))

    def deselect(self):
        v = self._var()
        if v is not None:
            v.set("")

    def invoke(self):
        if self.cget("state") == "disabled":
            return ""
        self.select()
        cmd = self._opts.get("command")
        if callable(cmd):
            return cmd()
        return ""

    def flash(self):
        pass

    def _ui_event(self, ev):
        if ev.get("k") == "cmd":
            self.invoke()


def _shared_radio_var(master):
    v = getattr(master, "_radio_var", None)
    if v is None:
        v = StringVar(master, name="selectedButton")
        master._radio_var = v
    return v


class Entry(Widget):
    _tkcls = "Entry"
    _defaults = {"state": "normal", "show": "", "width": 20, "justify": "left"}

    def _init_widget(self, kw):
        self._value = ""
        self._cursor = 0

    def _textvar(self):
        v = self._opts.get("textvariable")
        if isinstance(v, str) and v:
            v = Variable._registry.get(v)
        return v if isinstance(v, Variable) else None

    def _options_changed(self, kw):
        v = kw.get("textvariable")
        if isinstance(v, Variable):
            _g.op("var", v._name, v.get())

    def get(self):
        v = self._textvar()
        if v is not None:
            return str(v.get())
        return self._value

    def _set_value(self, s, from_ui=False):
        v = self._textvar()
        if v is not None:
            if from_ui:
                v._from_ui(s)
            else:
                v.set(s)
        else:
            self._value = s
            if not from_ui:
                _g.op("value", self._w, s)

    def _index(self, index):
        s = self.get()
        if index in ("end", END):
            return len(s)
        if index in ("insert", INSERT):
            return min(self._cursor, len(s))
        if index in ("anchor", "sel.first"):
            return 0
        if index == "sel.last":
            return len(s)
        if isinstance(index, str) and index.startswith("@"):
            return len(s)
        return max(0, min(len(s), int(index)))

    def insert(self, index, string):
        s = self.get()
        i = self._index(index)
        self._set_value(s[:i] + str(string) + s[i:])
        self._cursor = i + len(str(string))

    def delete(self, first, last=None):
        s = self.get()
        a = self._index(first)
        b = a + 1 if last is None else self._index(last)
        if b < a:
            a, b = b, a
        self._set_value(s[:a] + s[b:])
        self._cursor = a

    def icursor(self, index):
        self._cursor = self._index(index)
        _g.op("cursor", self._w, self._cursor)

    def index(self, index):
        return self._index(index)

    def selection_range(self, start, end):
        _g.op("select", self._w, [self._index(start), self._index(end)])

    select_range = selection_range

    def selection_clear(self):
        pass

    select_clear = selection_clear

    def selection_present(self):
        return False

    select_present = selection_present

    def selection_from(self, index):
        pass

    def selection_to(self, index):
        pass

    def selection_adjust(self, index):
        pass

    def scan_mark(self, x):
        pass

    def scan_dragto(self, x):
        pass

    def xview(self, *args):
        return (0.0, 1.0)

    def xview_moveto(self, fraction):
        pass

    def xview_scroll(self, number, what):
        pass

    def _validate(self, new_value, action, ev):
        mode = self.cget("validate")
        vcmd = self._opts.get("validatecommand")
        if not vcmd or mode in ("", "none", None):
            return True
        if mode not in ("key", "all"):
            return True
        func, fargs = vcmd, ()
        if isinstance(vcmd, (tuple, list)):
            func, fargs = vcmd[0], vcmd[1:]
        if isinstance(func, str):
            func = _func_names.get(func) or self._root().tk._cmds.get(func)
        if not callable(func):
            return True
        old = self.get()
        subs = {"%P": new_value, "%s": old, "%d": str(action), "%i": str(ev.get("pos", -1)),
                "%S": ev.get("ins", ""), "%v": str(mode), "%V": "key", "%W": self._w}
        args = [subs.get(a, a) if isinstance(a, str) else a for a in fargs]
        try:
            res = func(*args)
        except Exception:
            _g.report_exception()
            return True
        return bool(res) and str(res).lower() not in ("0", "false")

    def _ui_event(self, ev):
        k = ev.get("k")
        if k == "val":
            new = ev.get("v", "")
            old = self.get()
            action = 1 if len(new) >= len(old) else 0
            if not self._validate(new, action, ev):
                _g.op("value", self._w, old)
                return
            self._cursor = ev.get("cur", len(new))
            self._set_value(new, from_ui=True)
        elif k == "cmd":
            # Spinbox-Pfeile
            if hasattr(self, "_spin"):
                self._spin(ev.get("dir", 1))


class Spinbox(Entry):
    _tkcls = "Spinbox"
    _defaults = {"from": 0, "to": 0, "increment": 1, "width": 20, "wrap": False, "state": "normal"}

    def _after_create(self):
        if not self._textvar() and self._value == "":
            vals = self._values()
            if vals:
                self._value = str(vals[0])
            else:
                self._value = self._fmt(float(self.cget("from") or 0))
            _g.op("value", self._w, self._value)

    def _values(self):
        v = self._opts.get("values")
        if not v:
            return None
        if isinstance(v, str):
            return _tcl_split(v)
        return [str(x) for x in v]

    def _fmt(self, x):
        fmt = self._opts.get("format")
        if fmt:
            try:
                return fmt % x
            except Exception:
                pass
        inc = float(self.cget("increment") or 1)
        if float(x).is_integer() and float(inc).is_integer() and float(self.cget("from") or 0).is_integer():
            return str(int(x))
        return str(round(x, 10))

    def _spin(self, direction):
        vals = self._values()
        cur = self.get()
        if vals:
            try:
                i = vals.index(cur)
            except ValueError:
                i = -1
            i += direction
            if i >= len(vals):
                i = 0 if self.cget("wrap") else len(vals) - 1
            if i < 0:
                i = len(vals) - 1 if self.cget("wrap") else 0
            new = vals[i]
        else:
            lo, hi = float(self.cget("from") or 0), float(self.cget("to") or 0)
            inc = float(self.cget("increment") or 1)
            try:
                x = float(cur)
            except ValueError:
                x = lo
            x += inc * direction
            if x > hi:
                x = lo if self.cget("wrap") else hi
            if x < lo:
                x = hi if self.cget("wrap") else lo
            new = self._fmt(x)
        self._set_value(new)
        cmd = self._opts.get("command")
        if callable(cmd):
            _g._safe_call(cmd)

    def invoke(self, element):
        self._spin(1 if element == "buttonup" else -1)

    def identify(self, x, y):
        return ""


class Scale(Widget):
    _tkcls = "Scale"
    _defaults = {"from": 0, "to": 100, "orient": "vertical", "resolution": 1, "length": 100,
                 "showvalue": 1, "state": "normal", "label": "", "tickinterval": 0}

    def _init_widget(self, kw):
        self._value = float(kw.get("from", 0) or 0)

    def _var(self):
        v = self._opts.get("variable")
        if isinstance(v, str):
            v = Variable._registry.get(v)
        return v if isinstance(v, Variable) else None

    def _options_changed(self, kw):
        v = kw.get("variable")
        if isinstance(v, Variable):
            _g.op("var", v._name, v.get())
        elif "from" in kw and not self._var():
            self.set(self._value)

    def _round(self, x):
        res = float(self.cget("resolution") or 0)
        if res > 0:
            x = round(round(x / res) * res, 10)
        return x

    def get(self):
        v = self._var()
        if v is not None:
            try:
                x = float(v.get())
            except (TypeError, ValueError, TclError):
                x = 0.0
        else:
            x = self._value
        res = float(self.cget("resolution") or 0)
        if res >= 1 and float(res).is_integer():
            return int(round(x))
        return x

    def set(self, value):
        x = self._round(float(value))
        v = self._var()
        if v is not None:
            v.set(x if not isinstance(v, IntVar) else int(round(x)))
        else:
            self._value = x
            _g.op("value", self._w, x)

    def coords(self, value=None):
        return (0, 0)

    def identify(self, x, y):
        return ""

    def _ui_event(self, ev):
        if ev.get("k") == "val":
            x = self._round(float(ev.get("v", 0)))
            v = self._var()
            if v is not None:
                v._from_ui(int(round(x)) if isinstance(v, IntVar) else x)
            else:
                self._value = x
            cmd = self._opts.get("command")
            if callable(cmd):
                val = self.get()
                _g._safe_call(cmd, str(val))


class Scrollbar(Widget):
    _tkcls = "Scrollbar"
    _defaults = {"orient": "vertical", "width": 12}

    def set(self, first, last):
        pass

    def get(self):
        return (0.0, 1.0)

    def activate(self, index=None):
        return ""

    def delta(self, deltax, deltay):
        return 0.0

    def fraction(self, x, y):
        return 0.0

    def identify(self, x, y):
        return ""


class Listbox(Widget):
    _tkcls = "Listbox"
    _defaults = {"selectmode": "browse", "height": 10, "width": 20, "state": "normal"}

    def _init_widget(self, kw):
        self._items = []
        self._sel = []
        self._itemcfg = {}
        self._active = 0
        self._last_y = None
        self._last_index = 0

    def _options_changed(self, kw):
        v = kw.get("listvariable")
        if isinstance(v, Variable):
            val = v.get()
            self._items = list(val) if isinstance(val, (list, tuple)) else _tcl_split(val)
            v._traces.append((("write",), lambda *a: self._from_listvar()))
            _g.mark_dirty(self)

    def _from_listvar(self):
        v = self._opts.get("listvariable")
        if isinstance(v, Variable):
            val = v.get()
            self._items = list(val) if isinstance(val, (list, tuple)) else _tcl_split(val)
            _g.mark_dirty(self)

    def _pyide_sync(self):
        _g.op("items", self._w, [str(i) for i in self._items], self._sel,
              {str(k): self._wire(v) for k, v in self._itemcfg.items()})

    def _idx(self, index):
        if index in ("end", END):
            return len(self._items)
        if index in ("active", ACTIVE):
            return self._active
        if index in ("anchor",):
            return self._sel[0] if self._sel else 0
        if isinstance(index, str) and index.startswith("@"):
            return self._last_index
        return int(index)

    def insert(self, index, *elements):
        i = self._idx(index)
        for k, e in enumerate(elements):
            self._items.insert(i + k, e)
        self._sel = [s if s < i else s + len(elements) for s in self._sel]
        _g.mark_dirty(self)

    def delete(self, first, last=None):
        a = self._idx(first)
        b = a if last is None else self._idx(last)
        if last in ("end", END):
            b = len(self._items) - 1
        del self._items[a:b + 1]
        n = b - a + 1
        self._sel = [s if s < a else s - n for s in self._sel if not (a <= s <= b)]
        _g.mark_dirty(self)

    def get(self, first, last=None):
        a = self._idx(first)
        if last is None:
            return self._items[a] if 0 <= a < len(self._items) else ""
        b = len(self._items) - 1 if last in ("end", END) else self._idx(last)
        return tuple(self._items[a:b + 1])

    def size(self):
        return len(self._items)

    def curselection(self):
        return tuple(sorted(self._sel))

    def selection_set(self, first, last=None):
        a = self._idx(first)
        b = a if last is None else (len(self._items) - 1 if last in ("end", END) else self._idx(last))
        if self.cget("selectmode") in ("browse", "single"):
            self._sel = [a]
        else:
            self._sel = sorted(set(self._sel) | set(range(a, b + 1)))
        _g.mark_dirty(self)

    select_set = selection_set

    def selection_clear(self, first, last=None):
        a = self._idx(first)
        b = a if last is None else (len(self._items) - 1 if last in ("end", END) else self._idx(last))
        self._sel = [s for s in self._sel if not (a <= s <= b)]
        _g.mark_dirty(self)

    select_clear = selection_clear

    def selection_includes(self, index):
        return self._idx(index) in self._sel

    select_includes = selection_includes

    def selection_anchor(self, index):
        pass

    select_anchor = selection_anchor

    def activate(self, index):
        self._active = self._idx(index)

    def see(self, index):
        _g.op("see", self._w, self._idx(index))

    def index(self, index):
        return self._idx(index)

    def nearest(self, y):
        return self._last_index

    def itemconfigure(self, index, cnf=None, **kw):
        kw = {_norm_key(k): v for k, v in _cnfmerge(cnf, kw).items()}
        self._itemcfg.setdefault(self._idx(index), {}).update(kw)
        _g.mark_dirty(self)

    itemconfig = itemconfigure

    def itemcget(self, index, option):
        return self._itemcfg.get(self._idx(index), {}).get(_norm_key(option), "")

    def bbox(self, index):
        return (0, 0, 100, 18)

    def xview(self, *a):
        return (0.0, 1.0)

    def yview(self, *a):
        return (0.0, 1.0)

    def yview_moveto(self, f):
        pass

    def yview_scroll(self, n, what):
        pass

    def scan_mark(self, x, y):
        pass

    def scan_dragto(self, x, y):
        pass

    def _ui_event(self, ev):
        if ev.get("k") == "sel":
            self._sel = list(ev.get("sel", []))
            if self._sel:
                self._active = self._sel[-1]
                self._last_index = self._sel[-1]
            self._fire_event("Virtual", {"name": "<<ListboxSelect>>"})


class Menu(Widget):
    _tkcls = "Menu"
    _defaults = {"tearoff": 1}

    def _init_widget(self, kw):
        self._entries = []

    def _pyide_sync(self):
        out = []
        for e in self._entries:
            d = {"type": e["type"]}
            for k, v in e.items():
                if k in ("type",):
                    continue
                d[k] = _wire_value(k, v)
            if e["type"] == "checkbutton":
                var = e.get("variable")
                d["on"] = bool(var is not None and _tclstr(var.get()) == _tclstr(e.get("onvalue", 1)))
            if e["type"] == "radiobutton":
                var = e.get("variable")
                d["on"] = bool(var is not None and str(var.get()) == str(e.get("value", e.get("label"))))
            out.append(d)
        _g.op("menu", self._w, out)

    def _add(self, typ, kw):
        kw = {_norm_key(k): v for k, v in kw.items()}
        if typ == "checkbutton" and "variable" not in kw:
            kw["variable"] = IntVar(self, name=self._w + ".cb%d" % len(self._entries))
        if typ == "radiobutton" and "variable" not in kw:
            kw["variable"] = _shared_radio_var(self)
        for key in ("variable",):
            var = kw.get(key)
            if isinstance(var, Variable):
                var._traces.append((("write",), lambda *a: _g.mark_dirty(self)))
        kw["type"] = typ
        return kw

    def add(self, itemType, cnf={}, **kw):
        self._entries.append(self._add(itemType, _cnfmerge(cnf, kw)))
        _g.mark_dirty(self)

    def add_command(self, cnf={}, **kw):
        self.add("command", cnf, **kw)

    def add_cascade(self, cnf={}, **kw):
        self.add("cascade", cnf, **kw)

    def add_checkbutton(self, cnf={}, **kw):
        self.add("checkbutton", cnf, **kw)

    def add_radiobutton(self, cnf={}, **kw):
        self.add("radiobutton", cnf, **kw)

    def add_separator(self, cnf={}, **kw):
        self.add("separator", cnf, **kw)

    def insert(self, index, itemType, cnf={}, **kw):
        self._entries.insert(self.index(index), self._add(itemType, _cnfmerge(cnf, kw)))
        _g.mark_dirty(self)

    def insert_command(self, index, cnf={}, **kw):
        self.insert(index, "command", cnf, **kw)

    def insert_cascade(self, index, cnf={}, **kw):
        self.insert(index, "cascade", cnf, **kw)

    def insert_separator(self, index, cnf={}, **kw):
        self.insert(index, "separator", cnf, **kw)

    def insert_checkbutton(self, index, cnf={}, **kw):
        self.insert(index, "checkbutton", cnf, **kw)

    def insert_radiobutton(self, index, cnf={}, **kw):
        self.insert(index, "radiobutton", cnf, **kw)

    def index(self, index):
        if index in ("end", END, "last"):
            return len(self._entries) - 1 if self._entries else None
        if isinstance(index, int):
            return index
        try:
            return int(index)
        except (TypeError, ValueError):
            for i, e in enumerate(self._entries):
                if e.get("label") == index:
                    return i
        raise TclError('bad menu entry index "%s"' % index)

    def delete(self, index1, index2=None):
        a = self.index(index1)
        if a is None:
            return
        b = a if index2 is None else self.index(index2)
        del self._entries[a:b + 1]
        _g.mark_dirty(self)

    def entryconfigure(self, index, cnf=None, **kw):
        i = self.index(index)
        kw = {_norm_key(k): v for k, v in _cnfmerge(cnf, kw).items()}
        self._entries[i].update(kw)
        _g.mark_dirty(self)

    entryconfig = entryconfigure

    def entrycget(self, index, option):
        return self._entries[self.index(index)].get(_norm_key(option), "")

    def type(self, index):
        return self._entries[self.index(index)]["type"]

    def invoke(self, index):
        i = self.index(index)
        if i is None:
            return ""
        e = self._entries[i]
        if e.get("state") == "disabled":
            return ""
        var = e.get("variable")
        if e["type"] == "checkbutton" and isinstance(var, Variable):
            on = _tclstr(var.get()) == _tclstr(e.get("onvalue", 1))
            var.set(e.get("offvalue", 0) if on else e.get("onvalue", 1))
        elif e["type"] == "radiobutton" and isinstance(var, Variable):
            var.set(e.get("value", e.get("label")))
        cmd = e.get("command")
        if callable(cmd):
            return cmd()
        return ""

    def post(self, x, y):
        _g.op("popup", self._w, [x, y])

    def tk_popup(self, x, y, entry=""):
        self.post(x, y)

    def unpost(self):
        _g.op("unpost", self._w)

    def activate(self, index):
        pass

    def xposition(self, index):
        return 0

    def yposition(self, index):
        return 0

    def _ui_event(self, ev):
        if ev.get("k") == "menu":
            try:
                self.invoke(int(ev.get("i")))
            except Exception:
                _g.report_exception()
            _g.mark_dirty(self)


class Menubutton(_TextVarMixin, Widget):
    _tkcls = "Menubutton"
    _defaults = {"text": "", "relief": "raised"}


class OptionMenu(Menubutton):
    _tkcls = "OptionMenu"

    def __init__(self, master, variable, value=None, *values, **kwargs):
        self._variable = variable
        self._command = kwargs.pop("command", None)
        vals = ([value] if value is not None else []) + list(values)
        self._values_list = [str(v) for v in vals]
        cnf = {"textvariable": variable, "values": self._values_list}
        Widget.__init__(self, master, "menubutton", cnf, kwargs)
        self.__menu = Menu(self, name="menu", tearoff=0)
        for v in self._values_list:
            self.__menu.add_command(label=v, command=lambda v=v: self._choose(v))
        self.menuname = self.__menu._w

    def _choose(self, v):
        if self._variable is not None:
            self._variable.set(v)
        if callable(self._command):
            self._command(v)

    def __getitem__(self, name):
        if name == "menu":
            return self.__menu
        return Widget.cget(self, name)

    def _ui_event(self, ev):
        if ev.get("k") == "val":
            v = ev.get("v", "")
            if self._variable is not None:
                self._variable._from_ui(v)
            if callable(self._command):
                _g._safe_call(self._command, v)

    def destroy(self):
        Menubutton.destroy(self)


class PanedWindow(Widget):
    _tkcls = "PanedWindow"
    _defaults = {"orient": "horizontal"}

    def _init_widget(self, kw):
        self._panes = []
        self._master_info()

    def add(self, child, **kw):
        self._panes.append(child)
        child._manager = "pane"
        child._mopts = {"weight": int(kw.get("weight", 1) or 1) if "weight" in kw else 1}
        _g.op("pane_add", self._w, child._w, child._mopts)

    def forget(self, child):
        if child in self._panes:
            self._panes.remove(child)
        _g.op("forget", child._w)

    remove = forget

    def panes(self):
        return list(self._panes)

    def paneconfigure(self, tagOrId, cnf=None, **kw):
        pass

    paneconfig = paneconfigure

    def sash_coord(self, index):
        return (0, 0)

    def sash_place(self, index, x, y):
        pass


# ------------------------------------------------------------------- Text
_INDEX_RE = _re.compile(r"\s*([+-])\s*(\d+)\s*(c|ch|cha|char|chars|l|li|lin|line|lines|i|in|ind|indi|indic|indice|indices)\b|"
                        r"\s*(linestart|lineend|wordstart|wordend)|\s*display\s*|\s*any\s*")


class Text(Widget):
    _tkcls = "Text"
    _defaults = {"width": 80, "height": 24, "wrap": "char", "state": "normal", "undo": False,
                 "font": "TkFixedFont"}

    def _init_widget(self, kw):
        self._content = "\n"
        self._marks = {"insert": 0, "current": 0}
        self._tags = {}          # name -> list[(a, b)]
        self._tagcfg = {}        # name -> opts
        self._tag_order = []
        self._embedded = []
        self._see_end = False

    # -- Index-Rechnung
    def _line_starts(self):
        starts = [0]
        c = self._content
        i = c.find("\n")
        while i != -1:
            starts.append(i + 1)
            i = c.find("\n", i + 1)
        return starts

    def _offset_to_index(self, off):
        before = self._content[:off]
        line = before.count("\n") + 1
        col = off - (before.rfind("\n") + 1)
        return "%d.%d" % (line, col)

    def _base_offset(self, base):
        c = self._content
        if base in ("end", END):
            return len(c)
        if base in self._marks:
            return min(self._marks[base], len(c))
        if base.startswith("@"):
            return max(0, len(c) - 1)
        m = _re.match(r"^(\d+)\.(\d+|end)$", base)
        if m:
            starts = self._line_starts()
            line = int(m.group(1))
            if line < 1:
                return 0
            if line > len(starts) - 1:
                return len(c)
            s = starts[line - 1]
            e = c.find("\n", s)
            if e == -1:
                e = len(c)
            if m.group(2) == "end":
                return e
            return min(s + int(m.group(2)), e)
        m = _re.match(r"^(.+)\.(first|last)$", base)
        if m:
            rng = self._tags.get(m.group(1))
            if not rng:
                raise TclError('text doesn\'t contain any characters tagged with "%s"' % m.group(1))
            return rng[0][0] if m.group(2) == "first" else rng[-1][1]
        raise TclError('bad text index "%s"' % base)

    def _offset(self, index):
        if isinstance(index, (int, float)) and not isinstance(index, bool):
            index = "%s" % index
            if "." not in index:
                index += ".0"
        s = str(index).strip()
        m = _re.match(r"^(@\d+,\d+|\d+\.(?:\d+|end)|[^\s+\-]+)", s)
        if not m:
            raise TclError('bad text index "%s"' % index)
        base = m.group(1)
        off = self._base_offset(base)
        rest = s[m.end():]
        c = self._content
        while rest.strip():
            mm = _INDEX_RE.match(rest)
            if not mm:
                break
            if mm.group(1):
                n = int(mm.group(2)) * (1 if mm.group(1) == "+" else -1)
                unit = mm.group(3)[0]
                if unit in "ci":
                    off = max(0, min(len(c), off + n))
                else:
                    idx = self._offset_to_index(off)
                    line, col = map(int, idx.split("."))
                    off = self._base_offset("%d.%d" % (max(1, line + n), col))
            elif mm.group(4):
                kind = mm.group(4)
                if kind == "linestart":
                    off = c.rfind("\n", 0, off) + 1
                elif kind == "lineend":
                    e = c.find("\n", off)
                    off = len(c) if e == -1 else e
                elif kind == "wordstart":
                    while off > 0 and (c[off - 1].isalnum() or c[off - 1] == "_"):
                        off -= 1
                elif kind == "wordend":
                    while off < len(c) and (c[off].isalnum() or c[off] == "_"):
                        off += 1
            rest = rest[mm.end():]
        return max(0, min(len(c), off))

    def index(self, index):
        off = self._offset(index)
        if str(index).strip().startswith("end") and off == len(self._content):
            # 'end' liegt hinter dem letzten Zeilenumbruch
            return "%d.0" % (self._content.count("\n") + 1)
        return self._offset_to_index(off)

    def compare(self, index1, op, index2):
        a, b = self._offset(index1), self._offset(index2)
        return {"<": a < b, "<=": a <= b, "==": a == b, ">=": a >= b, ">": a > b, "!=": a != b}[op]

    # -- Inhalt
    def get(self, index1, index2=None):
        a = self._offset(index1)
        b = a + 1 if index2 is None else self._offset(index2)
        return self._content[a:b]

    def insert(self, index, chars, *args):
        if self.cget("state") == "disabled":
            return
        chars = str(chars)
        pos = min(self._offset(index), len(self._content) - 1)
        self._content = self._content[:pos] + chars + self._content[pos:]
        n = len(chars)
        for name, rngs in self._tags.items():
            self._tags[name] = [(a + n if a >= pos else a, b + n if b > pos else b) for a, b in rngs]
        for k, v in list(self._marks.items()):
            if v > pos or (k == "insert" and v == pos):
                self._marks[k] = v + n
        tags = args[0] if args else None
        if tags:
            if isinstance(tags, str):
                tags = (tags,)
            for t in tags:
                self._add_range(t, pos, pos + n)
        self._changed()

    def delete(self, index1, index2=None):
        if self.cget("state") == "disabled":
            return
        a = self._offset(index1)
        b = a + 1 if index2 is None else self._offset(index2)
        b = min(b, len(self._content) - 1)
        if b <= a:
            return
        self._content = self._content[:a] + self._content[b:]
        n = b - a

        def fix(x):
            if x <= a:
                return x
            if x >= b:
                return x - n
            return a
        for name, rngs in self._tags.items():
            self._tags[name] = [(fix(x), fix(y)) for x, y in rngs if fix(y) > fix(x)]
        for k, v in list(self._marks.items()):
            self._marks[k] = fix(v)
        self._changed()

    def replace(self, index1, index2, chars, *args):
        a = self.index(index1)
        self.delete(index1, index2)
        self.insert(a, chars, *args)

    def _changed(self):
        _g.mark_dirty(self)
        if _bindings.get(self._w):
            pass

    def _pyide_sync(self):
        text = self._content[:-1]
        styled = any(self._tagcfg.get(t) for t in self._tags if self._tags[t]) or self.cget("state") == "disabled"
        if not styled:
            _g.op("text", self._w, text, None)
        else:
            cuts = {0, len(text)}
            for rngs in self._tags.values():
                for a, b in rngs:
                    cuts.add(min(a, len(text)))
                    cuts.add(min(b, len(text)))
            cuts = sorted(cuts)
            segs = []
            for i in range(len(cuts) - 1):
                a, b = cuts[i], cuts[i + 1]
                if a >= b:
                    continue
                names = [t for t in self._tag_order if any(x <= a and b <= y for x, y in self._tags.get(t, []))]
                segs.append([text[a:b], names])
            _g.op("text", self._w, text, segs)
        if self._see_end:
            _g.op("see", self._w, "end")
            self._see_end = False

    # -- Tags
    def _add_range(self, tag, a, b):
        if tag not in self._tags:
            self._tags[tag] = []
        if tag not in self._tag_order:
            self._tag_order.append(tag)
        rngs = self._tags[tag] + [(a, b)]
        rngs.sort()
        merged = []
        for x, y in rngs:
            if merged and x <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], y))
            else:
                merged.append((x, y))
        self._tags[tag] = merged

    def tag_add(self, tagName, index1, *args):
        indices = (index1,) + args
        pairs = []
        i = 0
        while i < len(indices):
            a = self._offset(indices[i])
            if i + 1 < len(indices):
                b = self._offset(indices[i + 1])
                i += 2
            else:
                b = a + 1
                i += 1
            pairs.append((a, b))
        for a, b in pairs:
            if b > a:
                self._add_range(tagName, a, b)
        _g.mark_dirty(self)

    def tag_remove(self, tagName, index1, index2=None):
        a = self._offset(index1)
        b = a + 1 if index2 is None else self._offset(index2)
        out = []
        for x, y in self._tags.get(tagName, []):
            if y <= a or x >= b:
                out.append((x, y))
            else:
                if x < a:
                    out.append((x, a))
                if y > b:
                    out.append((b, y))
        self._tags[tagName] = out
        _g.mark_dirty(self)

    def tag_delete(self, *tagNames):
        for t in tagNames:
            self._tags.pop(t, None)
            self._tagcfg.pop(t, None)
            if t in self._tag_order:
                self._tag_order.remove(t)
        _g.mark_dirty(self)

    def tag_configure(self, tagName, cnf=None, **kw):
        kw = {_norm_key(k): v for k, v in _cnfmerge(cnf, kw).items()}
        if not kw:
            return self._tagcfg.get(tagName, {})
        self._tagcfg.setdefault(tagName, {}).update(kw)
        if tagName not in self._tag_order:
            self._tag_order.append(tagName)
            self._tags.setdefault(tagName, [])
        _g.op("tagcfg", self._w, tagName, self._wire(self._tagcfg[tagName]))
        _g.mark_dirty(self)

    tag_config = tag_configure

    def tag_cget(self, tagName, option):
        return self._tagcfg.get(tagName, {}).get(_norm_key(option), "")

    def tag_names(self, index=None):
        if index is None:
            return tuple(self._tag_order)
        o = self._offset(index)
        return tuple(t for t in self._tag_order if any(a <= o < b for a, b in self._tags.get(t, [])))

    def tag_ranges(self, tagName):
        out = []
        for a, b in self._tags.get(tagName, []):
            out += [self._offset_to_index(a), self._offset_to_index(b)]
        return tuple(out)

    def tag_nextrange(self, tagName, index1, index2=None):
        a = self._offset(index1)
        for x, y in self._tags.get(tagName, []):
            if y > a:
                return (self._offset_to_index(max(x, a)), self._offset_to_index(y))
        return ()

    def tag_prevrange(self, tagName, index1, index2=None):
        a = self._offset(index1)
        for x, y in reversed(self._tags.get(tagName, [])):
            if x < a:
                return (self._offset_to_index(x), self._offset_to_index(min(y, a)))
        return ()

    def tag_raise(self, tagName, aboveThis=None):
        if tagName in self._tag_order:
            self._tag_order.remove(tagName)
            self._tag_order.append(tagName)
            _g.mark_dirty(self)

    def tag_lower(self, tagName, belowThis=None):
        if tagName in self._tag_order:
            self._tag_order.remove(tagName)
            self._tag_order.insert(0, tagName)
            _g.mark_dirty(self)

    def tag_bind(self, tagName, sequence, func, add=None):
        return self.bind(sequence, func, add)

    def tag_unbind(self, tagName, sequence, funcid=None):
        pass

    # -- Marken
    def mark_set(self, markName, index):
        self._marks[markName] = self._offset(index)
        if markName == "insert":
            _g.op("cursor", self._w, self._marks["insert"])

    def mark_unset(self, *markNames):
        for m in markNames:
            if m not in ("insert", "current"):
                self._marks.pop(m, None)

    def mark_names(self):
        return tuple(self._marks)

    def mark_gravity(self, markName, direction=None):
        return "right"

    def mark_next(self, index):
        return None

    def mark_previous(self, index):
        return None

    # -- Ansicht
    def see(self, index):
        if str(index).startswith("end"):
            self._see_end = True
            _g.mark_dirty(self)
        else:
            _g.op("see", self._w, self._offset(index))

    def yview(self, *args):
        if args and args[0] == "end":
            self.see("end")
        if args and args[0] == "moveto" and float(args[1]) >= 1:
            self.see("end")
        return (0.0, 1.0)

    def yview_moveto(self, fraction):
        if float(fraction) >= 1:
            self.see("end")

    def yview_scroll(self, number, what):
        pass

    def xview(self, *args):
        return (0.0, 1.0)

    def xview_moveto(self, f):
        pass

    def search(self, pattern, index, stopindex=None, forwards=None, backwards=None, exact=None,
               regexp=None, nocase=None, count=None, elide=None):
        start = self._offset(index)
        text = self._content
        stop = self._offset(stopindex) if stopindex else None
        flags = _re.IGNORECASE if nocase else 0
        if backwards:
            region = text[:start] if stop is None else text[stop:start]
            base = 0 if stop is None else stop
            matches = list(_re.finditer(pattern if regexp else _re.escape(pattern), region, flags))
            if not matches:
                return ""
            m = matches[-1]
        else:
            region = text[start:] if stop is None else text[start:stop]
            base = start
            m = _re.search(pattern if regexp else _re.escape(pattern), region, flags)
            if not m and stop is None:
                m = _re.search(pattern if regexp else _re.escape(pattern), text[:start], flags)
                base = 0
            if not m:
                return ""
        if count is not None:
            count.set(m.end() - m.start())
        return self._offset_to_index(base + m.start())

    def bbox(self, index):
        return (0, 0, 8, 16)

    def dlineinfo(self, index):
        return (0, 0, 100, 16, 12)

    def count(self, index1, index2, *options):
        a, b = self._offset(index1), self._offset(index2)
        if "lines" in options:
            return (self._content[a:b].count("\n"),)
        return (b - a,)

    def edit_modified(self, arg=None):
        if arg is None:
            return getattr(self, "_modified", False)
        self._modified = bool(arg)

    def edit_undo(self):
        pass

    def edit_redo(self):
        pass

    def edit_reset(self):
        pass

    def edit_separator(self):
        pass

    def window_create(self, index, cnf={}, **kw):
        pass

    def image_create(self, index, cnf={}, **kw):
        img = _cnfmerge(cnf, kw).get("image")
        self.insert(index, "￼")
        return getattr(img, "name", "")

    def _ui_event(self, ev):
        if ev.get("k") == "text":
            new = ev.get("v", "") + "\n"
            if new != self._content:
                self._content = new
                ln = len(self._content)
                for name, rngs in self._tags.items():
                    self._tags[name] = [(min(a, ln), min(b, ln)) for a, b in rngs if a < ln]
                self._modified = True
                if _bindings.get(self._w):
                    self._fire_event("Virtual", {"name": "<<Modified>>"})
            if "cur" in ev:
                self._marks["insert"] = min(int(ev["cur"]), len(self._content) - 1)


# ------------------------------------------------------------------ Canvas
class Canvas(Widget):
    _tkcls = "Canvas"
    _defaults = {"width": 378, "height": 265, "background": "#ececec", "highlightthickness": 1,
                 "borderwidth": 0, "relief": "flat"}

    def _init_widget(self, kw):
        self._items = {}
        self._order = []
        self._next = 0
        self._item_bindings = {}
        self._current = None

    # -- Hilfen
    def _ids(self, tagOrId):
        if tagOrId is None:
            return []
        if isinstance(tagOrId, int) or (isinstance(tagOrId, str) and tagOrId.isdigit()):
            i = int(tagOrId)
            return [i] if i in self._items else []
        t = str(tagOrId)
        if t == "all":
            return list(self._order)
        if t == "current":
            return [self._current] if self._current in self._items else []
        if any(ch in t for ch in "&|!^()") and t not in ("&&", "||"):
            return [i for i in self._order if _tag_expr(t, self._items[i]["tags"] + [str(i)])]
        return [i for i in self._order if t in self._items[i]["tags"]]

    def _item_wire(self, kw):
        out = {}
        for k, v in kw.items():
            k = _norm_key(k)
            if k == "tags":
                continue
            out[k] = _wire_value(k, v, self)
        return out

    def _create(self, typ, args, kw):
        kw = _cnfmerge(None, kw)
        coords = [float(c) for c in _flatten(args) if not isinstance(c, dict)]
        for a in args:
            if isinstance(a, dict):
                kw.update(a)
        tags = kw.pop("tags", kw.pop("tag", ()))
        if isinstance(tags, str):
            tags = tags.split()
        tags = [str(t) for t in (tags or ())]
        self._next += 1
        iid = self._next
        opts = {_norm_key(k): v for k, v in kw.items()}
        if typ == "window" and isinstance(opts.get("window"), Misc):
            opts["window"]._manager = "canvas"
        self._items[iid] = {"type": typ, "coords": coords, "opts": opts, "tags": tags}
        self._order.append(iid)
        _g.op("cv_new", self._w, iid, typ, coords, self._item_wire(opts), tags)
        return iid

    def create_line(self, *args, **kw):
        return self._create("line", args, kw)

    def create_rectangle(self, *args, **kw):
        return self._create("rectangle", args, kw)

    def create_oval(self, *args, **kw):
        return self._create("oval", args, kw)

    def create_polygon(self, *args, **kw):
        return self._create("polygon", args, kw)

    def create_arc(self, *args, **kw):
        return self._create("arc", args, kw)

    def create_text(self, *args, **kw):
        return self._create("text", args, kw)

    def create_image(self, *args, **kw):
        return self._create("image", args, kw)

    def create_bitmap(self, *args, **kw):
        return self._create("rectangle", args[:2] + (args[0], args[1]) if len(args) >= 2 else args, {})

    def create_window(self, *args, **kw):
        return self._create("window", args, kw)

    # -- Aenderungen
    def coords(self, tagOrId, *args):
        ids = self._ids(tagOrId)
        if not ids:
            return []
        if not args:
            return [float(c) for c in self._items[ids[0]]["coords"]]
        coords = [float(c) for c in _flatten(args)]
        self._items[ids[0]]["coords"] = coords
        _g.op("cv_coords", self._w, ids[0], coords)
        return None

    def move(self, tagOrId, xAmount, yAmount):
        ids = self._ids(tagOrId)
        dx, dy = float(xAmount), float(yAmount)
        for i in ids:
            c = self._items[i]["coords"]
            self._items[i]["coords"] = [v + (dx if k % 2 == 0 else dy) for k, v in enumerate(c)]
        if ids:
            _g.op("cv_move", self._w, ids, dx, dy)

    def moveto(self, tagOrId, x="", y=""):
        ids = self._ids(tagOrId)
        if not ids:
            return
        bb = self._bbox_ids(ids[:1])
        if not bb:
            return
        dx = float(x) - bb[0] if x != "" else 0.0
        dy = float(y) - bb[1] if y != "" else 0.0
        self.move(tagOrId, dx, dy)

    def scale(self, tagOrId, xOrigin, yOrigin, xScale, yScale):
        for i in self._ids(tagOrId):
            c = self._items[i]["coords"]
            new = []
            for k, v in enumerate(c):
                if k % 2 == 0:
                    new.append(float(xOrigin) + (v - float(xOrigin)) * float(xScale))
                else:
                    new.append(float(yOrigin) + (v - float(yOrigin)) * float(yScale))
            self._items[i]["coords"] = new
            _g.op("cv_coords", self._w, i, new)

    def delete(self, *tagsOrIds):
        ids = []
        for t in tagsOrIds:
            ids += self._ids(t)
        ids = list(dict.fromkeys(ids))
        for i in ids:
            item = self._items.pop(i, None)
            if item and item["type"] == "window" and isinstance(item["opts"].get("window"), Misc):
                item["opts"]["window"]._manager = None
            self._order.remove(i)
        if ids:
            _g.op("cv_del", self._w, ids)

    def itemconfigure(self, tagOrId, cnf=None, **kw):
        ids = self._ids(tagOrId)
        kw = {_norm_key(k): v for k, v in _cnfmerge(cnf, kw).items()}
        if not kw:
            if not ids:
                return {}
            o = self._items[ids[0]]["opts"]
            return {k: (k, "", "", "", v) for k, v in o.items()}
        tags = kw.pop("tags", None)
        for i in ids:
            self._items[i]["opts"].update(kw)
            if tags is not None:
                self._items[i]["tags"] = tags.split() if isinstance(tags, str) else [str(t) for t in tags]
        if ids:
            _g.op("cv_cfg", self._w, ids, self._item_wire(kw),
                  self._items[ids[0]]["tags"] if tags is not None else None)

    itemconfig = itemconfigure

    def itemcget(self, tagOrId, option):
        ids = self._ids(tagOrId)
        if not ids:
            return ""
        option = _norm_key(option)
        if option == "tags":
            return " ".join(self._items[ids[0]]["tags"])
        v = self._items[ids[0]]["opts"].get(option, "")
        if isinstance(v, Image):
            return v.name
        return v

    def type(self, tagOrId):
        ids = self._ids(tagOrId)
        return self._items[ids[0]]["type"] if ids else None

    def gettags(self, tagOrId):
        ids = self._ids(tagOrId)
        return tuple(self._items[ids[0]]["tags"]) if ids else ()

    def addtag(self, *args):
        pass

    def addtag_withtag(self, newtag, tagOrId):
        for i in self._ids(tagOrId):
            if newtag not in self._items[i]["tags"]:
                self._items[i]["tags"].append(newtag)
                _g.op("cv_tags", self._w, i, self._items[i]["tags"])

    def addtag_all(self, newtag):
        self.addtag_withtag(newtag, "all")

    def addtag_above(self, newtag, tagOrId):
        pass

    def addtag_below(self, newtag, tagOrId):
        pass

    def addtag_closest(self, newtag, x, y, halo=None, start=None):
        r = self.find_closest(x, y)
        if r:
            self.addtag_withtag(newtag, r[0])

    def addtag_enclosed(self, newtag, x1, y1, x2, y2):
        for i in self.find_enclosed(x1, y1, x2, y2):
            self.addtag_withtag(newtag, i)

    def addtag_overlapping(self, newtag, x1, y1, x2, y2):
        for i in self.find_overlapping(x1, y1, x2, y2):
            self.addtag_withtag(newtag, i)

    def dtag(self, tagOrId, tagToDelete=None):
        if tagToDelete is None:
            tagToDelete = tagOrId
        for i in self._ids(tagOrId):
            if tagToDelete in self._items[i]["tags"]:
                self._items[i]["tags"].remove(tagToDelete)
                _g.op("cv_tags", self._w, i, self._items[i]["tags"])

    def tag_raise(self, tagOrId, aboveThis=None):
        ids = self._ids(tagOrId)
        for i in ids:
            self._order.remove(i)
        if aboveThis is not None and self._ids(aboveThis):
            pos = self._order.index(self._ids(aboveThis)[-1]) + 1
            self._order[pos:pos] = ids
        else:
            self._order.extend(ids)
        if ids:
            _g.op("cv_order", self._w, self._order)

    lift = tkraise = tag_raise

    def tag_lower(self, tagOrId, belowThis=None):
        ids = self._ids(tagOrId)
        for i in ids:
            self._order.remove(i)
        if belowThis is not None and self._ids(belowThis):
            pos = self._order.index(self._ids(belowThis)[0])
            self._order[pos:pos] = ids
        else:
            self._order[0:0] = ids
        if ids:
            _g.op("cv_order", self._w, self._order)

    lower = tag_lower

    # -- Suche
    def _item_bbox(self, i):
        it = self._items[i]
        c = it["coords"]
        if not c:
            return None
        t = it["type"]
        o = it["opts"]
        if t in ("text", "image", "window", "bitmap"):
            x, y = c[0], c[1]
            if t == "text":
                spec = _font_spec(o.get("font")) or {}
                size = abs(spec.get("size", 10) or 10) * (1.333 if (spec.get("size", 10) or 10) > 0 else 1)
                lines = str(o.get("text", "")).split("\n")
                w = max((len(l) for l in lines), default=0) * size * 0.6
                h = len(lines) * size * 1.25
            elif t == "image":
                img = o.get("image")
                w = img.width() if isinstance(img, Image) else 0
                h = img.height() if isinstance(img, Image) else 0
            else:
                w = _pixels(o.get("width"), 50)
                h = _pixels(o.get("height"), 20)
            anchor = str(o.get("anchor", "center"))
            if anchor == "center":
                anchor = ""
            x0 = x - w / 2
            y0 = y - h / 2
            if "w" in anchor:
                x0 = x
            if "e" in anchor:
                x0 = x - w
            if "n" in anchor:
                y0 = y
            if "s" in anchor:
                y0 = y - h
            return [x0, y0, x0 + w, y0 + h]
        xs, ys = c[0::2], c[1::2]
        pad = float(o.get("width", 1) or 1) / 2.0
        return [min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad]

    def _bbox_ids(self, ids):
        boxes = [b for b in (self._item_bbox(i) for i in ids) if b]
        if not boxes:
            return None
        return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]

    def bbox(self, *args):
        ids = []
        for a in args:
            ids += self._ids(a)
        bb = self._bbox_ids(ids)
        if bb is None:
            return None
        import math
        return (int(math.floor(bb[0])), int(math.floor(bb[1])), int(math.ceil(bb[2])), int(math.ceil(bb[3])))

    def find_all(self):
        return tuple(self._order)

    def find_withtag(self, tagOrId):
        return tuple(self._ids(tagOrId))

    def find_overlapping(self, x1, y1, x2, y2):
        x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
        res = []
        for i in self._order:
            b = self._item_bbox(i)
            if b and b[0] <= x2 and b[2] >= x1 and b[1] <= y2 and b[3] >= y1:
                if self._items[i]["opts"].get("state") != "hidden":
                    res.append(i)
        return tuple(res)

    def find_enclosed(self, x1, y1, x2, y2):
        res = []
        for i in self._order:
            b = self._item_bbox(i)
            if b and b[0] >= float(x1) and b[2] <= float(x2) and b[1] >= float(y1) and b[3] <= float(y2):
                res.append(i)
        return tuple(res)

    def find_closest(self, x, y, halo=None, start=None):
        best, bd = None, None
        x, y = float(x), float(y)
        for i in self._order:
            b = self._item_bbox(i)
            if not b:
                continue
            dx = max(b[0] - x, 0, x - b[2])
            dy = max(b[1] - y, 0, y - b[3])
            d = dx * dx + dy * dy
            if bd is None or d <= bd:
                best, bd = i, d
        return (best,) if best is not None else ()

    def find_above(self, tagOrId):
        ids = self._ids(tagOrId)
        if not ids:
            return ()
        p = self._order.index(ids[-1])
        return (self._order[p + 1],) if p + 1 < len(self._order) else ()

    def find_below(self, tagOrId):
        ids = self._ids(tagOrId)
        if not ids:
            return ()
        p = self._order.index(ids[0])
        return (self._order[p - 1],) if p > 0 else ()

    def find(self, *args):
        kind = args[0]
        return getattr(self, "find_" + kind)(*args[1:])

    # -- Bindungen fuer Elemente
    def tag_bind(self, tagOrId, sequence=None, func=None, add=None):
        key = str(tagOrId)
        lst = self._item_bindings.setdefault(key, [])
        if sequence is None:
            return tuple(b[2] for b in lst)
        if func is None:
            return ""
        pat = _parse_sequence(sequence)
        if not add:
            lst[:] = [b for b in lst if b[0] != pat]
        lst.append((pat, func, sequence))
        types = set()
        for bl in self._item_bindings.values():
            for (typ, d, mods), f, s in bl:
                js = _JS_TYPES.get(typ)
                if js:
                    types.add(js)
                if typ == "Motion" and mods & {"B1", "B2", "B3"}:
                    types.add("drag")
                if "Double" in mods:
                    types.add("dbl")
        _g.op("cv_bind", self._w, sorted(types))
        return "%d" % id(func)

    def tag_unbind(self, tagOrId, sequence, funcid=None):
        key = str(tagOrId)
        pat = _parse_sequence(sequence)
        lst = self._item_bindings.get(key, [])
        lst[:] = [b for b in lst if b[0] != pat]

    def _item_event(self, typ, ev):
        iid = ev.get("item")
        self._current = iid
        if iid not in self._items:
            return None
        keys = ["all"] + list(self._items[iid]["tags"]) + [str(iid)]
        e = _make_event(self, ev, typ)
        for key in keys:
            best, score = None, -1
            for pat, func, _s in self._item_bindings.get(key, []):
                s = _match(pat, typ, ev)
                if s > score:
                    best, score = func, s
            if best is not None:
                if _g._safe_call(best, e) == "break":
                    return "break"
        return None

    # -- Ansicht
    def canvasx(self, screenx, gridspacing=None):
        return float(screenx)

    def canvasy(self, screeny, gridspacing=None):
        return float(screeny)

    def xview(self, *args):
        return (0.0, 1.0)

    def yview(self, *args):
        return (0.0, 1.0)

    def xview_moveto(self, f):
        pass

    def yview_moveto(self, f):
        pass

    def xview_scroll(self, n, what):
        pass

    def yview_scroll(self, n, what):
        pass

    def scan_mark(self, x, y):
        pass

    def scan_dragto(self, x, y, gain=10):
        pass

    def postscript(self, cnf={}, **kw):
        return ""

    def focus(self, *args):
        if not args:
            return ""
        return None

    def icursor(self, *args):
        pass

    def dchars(self, *args):
        pass

    def insert(self, *args):
        pass

    def index(self, *args):
        return 0

    def select_clear(self):
        pass

    def select_item(self):
        return None


def _tag_expr(expr, tags):
    py = expr.replace("&&", " and ").replace("||", " or ").replace("^", " != ").replace("!", " not ")
    names = _re.findall(r"[A-Za-z_][A-Za-z0-9_.]*", expr)
    env = {n: (n in tags) for n in names if n not in ("and", "or", "not")}
    try:
        return bool(eval(py, {"__builtins__": {}}, env))
    except Exception:
        return False


# ------------------------------------------------------------------- Bilder
class Image:
    _registry = {}
    _count = 0

    def __init__(self, imgtype, name=None, cnf={}, master=None, **kw):
        if name is None:
            Image._count += 1
            name = "pyimage%d" % Image._count
        self.name = name
        self._type = imgtype
        self._opts = {}
        self._w = 0
        self._h = 0
        self._mime = "image/png"
        self._data = None
        self._pixels = None
        Image._registry[name] = self
        kw = _cnfmerge(cnf, kw)
        self.configure(**kw)

    def __str__(self):
        return self.name

    def __del__(self):
        pass

    def configure(self, **kw):
        for k, v in kw.items():
            k = _norm_key(k)
            self._opts[k] = v
        if "file" in kw and kw["file"]:
            with open(kw["file"], "rb") as f:
                self._load(f.read())
        elif "data" in kw and kw["data"]:
            data = kw["data"]
            if isinstance(data, str):
                import base64
                try:
                    data = base64.b64decode(data)
                except Exception:
                    data = data.encode("latin-1")
            self._load(bytes(data))
        elif ("width" in kw or "height" in kw) and self._data is None:
            self._w = int(_pixels(kw.get("width", self._w)))
            self._h = int(_pixels(kw.get("height", self._h)))
            self._blank()

    config = configure

    def _load(self, data):
        w, h, mime = _g.image_size(data)
        self._w, self._h, self._mime = w, h, mime
        self._data = data
        self._pixels = None
        import base64
        _g.op("img", self.name, mime, base64.b64encode(data).decode("ascii"), w, h)

    def _blank(self):
        self._data = None
        self._pixels = bytearray(self._w * self._h * 4)
        _g.mark_dirty(self)

    def _pyide_sync(self):
        if self._pixels is not None:
            import base64
            _g.op("img_rgba", self.name, base64.b64encode(bytes(self._pixels)).decode("ascii"), self._w, self._h)

    def cget(self, option):
        return self._opts.get(_norm_key(option), "")

    __getitem__ = cget

    def __setitem__(self, key, value):
        self.configure(**{key: value})

    def height(self):
        return self._h

    def width(self):
        return self._w

    def type(self):
        return self._type

    def _pyide_json(self):
        return self.name


class PhotoImage(Image):
    def __init__(self, name=None, cnf={}, master=None, **kw):
        Image.__init__(self, "photo", name, cnf, master, **kw)

    def blank(self):
        if self._w and self._h:
            self._blank()

    def _derived(self, w, h, op_name, args):
        img = PhotoImage()
        img._w, img._h, img._mime = int(w), int(h), self._mime
        img._data = self._data
        if self._pixels is not None:
            img._pixels = bytearray(img._w * img._h * 4)
            sx = self._w / float(max(1, img._w))
            sy = self._h / float(max(1, img._h))
            for y in range(img._h):
                for x in range(img._w):
                    si = (int(y * sy) * self._w + int(x * sx)) * 4
                    di = (y * img._w + x) * 4
                    img._pixels[di:di + 4] = self._pixels[si:si + 4]
            _g.mark_dirty(img)
        else:
            _g.op("img_scaled", img.name, self.name, img._w, img._h)
        return img

    def copy(self):
        return self._derived(self._w, self._h, "copy", ())

    def zoom(self, x, y=""):
        y = x if y == "" else y
        return self._derived(self._w * int(x), self._h * int(y), "zoom", (x, y))

    def subsample(self, x, y=""):
        y = x if y == "" else y
        return self._derived(max(1, self._w // int(x)), max(1, self._h // int(y)), "subsample", (x, y))

    def _ensure_pixels(self):
        if self._pixels is None:
            if not self._w or not self._h:
                raise TclError("image has no size")
            res = _g.sync_call("img_pixels", {"name": self.name})
            if isinstance(res, str):
                import base64
                self._pixels = bytearray(base64.b64decode(res))
            else:
                self._pixels = bytearray(self._w * self._h * 4)

    def put(self, data, to=None):
        if self._w == 0 and to is not None:
            pass
        rows = self._parse_put(data)
        x0, y0 = 0, 0
        x1 = y1 = None
        if to is not None:
            to = list(to) if isinstance(to, (tuple, list)) else [int(v) for v in str(to).split()]
            x0, y0 = int(to[0]), int(to[1])
            if len(to) >= 4:
                x1, y1 = int(to[2]), int(to[3])
        need_w = max(self._w, x0 + (max(len(r) for r in rows) if rows else 0), x1 or 0)
        need_h = max(self._h, y0 + len(rows), y1 or 0)
        if self._pixels is None and self._data is None:
            self._w, self._h = need_w, need_h
            self._pixels = bytearray(self._w * self._h * 4)
        self._ensure_pixels()
        if need_w > self._w or need_h > self._h:
            old, ow, oh = self._pixels, self._w, self._h
            self._w, self._h = need_w, need_h
            self._pixels = bytearray(self._w * self._h * 4)
            for y in range(oh):
                self._pixels[y * self._w * 4:(y * self._w + ow) * 4] = old[y * ow * 4:(y + 1) * ow * 4]
        if x1 is not None and len(rows) == 1 and len(rows[0]) == 1:
            r, g, b = rows[0][0]
            for y in range(y0, min(y1, self._h)):
                for x in range(x0, min(x1, self._w)):
                    i = (y * self._w + x) * 4
                    self._pixels[i:i + 4] = bytes((r, g, b, 255))
        else:
            for dy, row in enumerate(rows):
                y = y0 + dy
                if y >= self._h:
                    break
                for dx, (r, g, b) in enumerate(row):
                    x = x0 + dx
                    if x >= self._w:
                        break
                    i = (y * self._w + x) * 4
                    self._pixels[i] = r
                    self._pixels[i + 1] = g
                    self._pixels[i + 2] = b
                    self._pixels[i + 3] = 255
        _g.mark_dirty(self)

    def _parse_put(self, data):
        if isinstance(data, (tuple, list)):
            rows = []
            for row in data:
                if isinstance(row, (tuple, list)):
                    rows.append([_rgb(c) for c in row])
                else:
                    rows.append([_rgb(c) for c in _tcl_split(row)])
            return rows
        s = str(data).strip()
        if s.startswith("{"):
            return [[_rgb(c) for c in r.split()] for r in _re.findall(r"\{([^}]*)\}", s)]
        return [[_rgb(c) for c in s.split()]]

    def get(self, x, y):
        self._ensure_pixels()
        i = (int(y) * self._w + int(x)) * 4
        return (self._pixels[i], self._pixels[i + 1], self._pixels[i + 2])

    def transparency_get(self, x, y):
        self._ensure_pixels()
        return self._pixels[(int(y) * self._w + int(x)) * 4 + 3] == 0

    def transparency_set(self, x, y, boolean):
        self._ensure_pixels()
        self._pixels[(int(y) * self._w + int(x)) * 4 + 3] = 0 if boolean else 255
        _g.mark_dirty(self)

    def write(self, filename, format=None, from_coords=None):
        self._ensure_pixels()
        _write_png(filename, self._w, self._h, self._pixels)

    def data(self, format=None, **kw):
        return ""


class BitmapImage(Image):
    def __init__(self, name=None, cnf={}, master=None, **kw):
        Image.__init__(self, "bitmap", name, cnf, master)


_COLOR_NAMES = {
    "black": (0, 0, 0), "white": (255, 255, 255), "red": (255, 0, 0), "green": (0, 255, 0),
    "blue": (0, 0, 255), "yellow": (255, 255, 0), "cyan": (0, 255, 255), "magenta": (255, 0, 255),
    "gray": (190, 190, 190), "grey": (190, 190, 190), "orange": (255, 165, 0), "purple": (160, 32, 240),
    "brown": (165, 42, 42), "pink": (255, 192, 203), "darkgreen": (0, 100, 0), "darkblue": (0, 0, 139),
    "darkred": (139, 0, 0), "lightblue": (173, 216, 230), "lightgreen": (144, 238, 144),
    "navy": (0, 0, 128), "gold": (255, 215, 0), "violet": (238, 130, 238), "silver": (192, 192, 192),
}


def _rgb(c):
    if isinstance(c, (tuple, list)):
        return tuple(int(v) for v in c[:3])
    c = str(c).strip().lower().replace(" ", "")
    if c.startswith("#"):
        h = c[1:]
        n = len(h) // 3
        if n == 0:
            return (0, 0, 0)
        vals = [int(h[i * n:(i + 1) * n], 16) for i in range(3)]
        if n == 1:
            return tuple(v * 17 for v in vals)
        if n == 2:
            return tuple(vals)
        return tuple(v >> (4 * (n - 2)) for v in vals)
    m = _re.match(r"^gr[ae]y(\d+)$", c)
    if m:
        v = int(round(int(m.group(1)) * 2.55))
        return (v, v, v)
    if c in _COLOR_NAMES:
        return _COLOR_NAMES[c]
    import pyide_colors
    return pyide_colors.to_rgb(c) or (0, 0, 0)


def _write_png(filename, w, h, rgba):
    import struct
    import zlib
    raw = b"".join(b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    with open(filename, "wb") as f:
        f.write(png)


# kleine Hilfsklassen, die manche Programme importieren
class CallWrapper:
    def __init__(self, func, subst, widget):
        self.func = func

    def __call__(self, *args):
        return self.func(*args)


class XView:
    def xview(self, *args):
        return (0.0, 1.0)


class YView:
    def yview(self, *args):
        return (0.0, 1.0)


Studbutton = Button
Tributton = Button

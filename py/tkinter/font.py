"""Nachbau von tkinter.font."""
import pyide_gui as _g
import tkinter as _tk

NORMAL = "normal"
ROMAN = "roman"
BOLD = "bold"
ITALIC = "italic"

_count = [0]


def nametofont(name, root=None):
    if name in _tk._NAMED_FONTS:
        return _tk._NAMED_FONTS[name]
    f = Font(name=name, exists=True)
    return f


class Font:
    def __init__(self, root=None, font=None, name=None, exists=False, **options):
        spec = {"family": "TkDefaultFont", "size": 13, "weight": "normal", "slant": "roman",
                "underline": 0, "overstrike": 0}
        if name in _DEFAULTS:
            spec.update(_DEFAULTS[name])
        if font is not None:
            s = _tk._font_spec(font) or {}
            spec.update({k: v for k, v in s.items() if k != "named"})
        for k, v in options.items():
            spec[k] = v
        if name is None:
            _count[0] += 1
            name = "font%d" % _count[0]
        self.name = name
        self._s = spec
        _tk._NAMED_FONTS[name] = self

    def _spec(self):
        s = {"family": self._s.get("family"), "size": int(float(self._s.get("size", 13)))}
        if self._s.get("weight") == "bold":
            s["weight"] = "bold"
        if self._s.get("slant") == "italic":
            s["slant"] = "italic"
        if self._s.get("underline"):
            s["underline"] = True
        if self._s.get("overstrike"):
            s["overstrike"] = True
        return s

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Font) and other.name == self.name

    def __hash__(self):
        return hash(self.name)

    def actual(self, option=None, displayof=None):
        if option:
            return self._s.get(option)
        return dict(self._s)

    def cget(self, option):
        return self._s.get(option)

    __getitem__ = cget

    def config(self, **options):
        if not options:
            return dict(self._s)
        self._s.update(options)
        _g.op("font_changed", self.name, self._spec())
        for obj in list(_g._S.objects.values()):
            f = getattr(obj, "_opts", {}).get("font") if hasattr(obj, "_opts") else None
            if f is self or f == self.name:
                _g.op("cfg", obj._w, {"font": self._spec()})
        return None

    configure = config

    def __setitem__(self, key, value):
        self.configure(**{key: value})

    def copy(self):
        return Font(**self._s)

    def measure(self, text, displayof=None):
        res = _g.sync_call("measure", {"font": self._spec(), "text": str(text)})
        if isinstance(res, (int, float)):
            return int(round(res))
        size = abs(int(self._s.get("size", 13)))
        return int(len(str(text)) * size * 0.62)

    def metrics(self, *options, **kw):
        size = abs(int(self._s.get("size", 13))) * 1.333
        m = {"ascent": int(size * 0.8), "descent": int(size * 0.25), "linespace": int(size * 1.25),
             "fixed": 1 if "mono" in str(self._s.get("family")).lower() or "courier" in str(self._s.get("family")).lower() else 0}
        if options:
            return m.get(options[0].lstrip("-"))
        return m


_DEFAULTS = {
    "TkDefaultFont": {"family": "TkDefaultFont", "size": 13},
    "TkTextFont": {"family": "TkDefaultFont", "size": 13},
    "TkFixedFont": {"family": "TkFixedFont", "size": 12},
    "TkHeadingFont": {"family": "TkDefaultFont", "size": 13, "weight": "bold"},
    "TkMenuFont": {"family": "TkDefaultFont", "size": 13},
    "TkCaptionFont": {"family": "TkDefaultFont", "size": 13, "weight": "bold"},
    "TkSmallCaptionFont": {"family": "TkDefaultFont", "size": 11},
    "TkIconFont": {"family": "TkDefaultFont", "size": 12},
    "TkTooltipFont": {"family": "TkDefaultFont", "size": 11},
}


def families(root=None, displayof=None):
    return ("Helvetica", "Arial", "Times", "Times New Roman", "Courier", "Courier New", "Menlo",
            "Georgia", "Verdana", "Avenir", "Futura", "Gill Sans", "Palatino", "Trebuchet MS",
            "TkDefaultFont", "TkFixedFont")


def names(root=None):
    return tuple(_tk._NAMED_FONTS.keys()) + tuple(k for k in _DEFAULTS if k not in _tk._NAMED_FONTS)

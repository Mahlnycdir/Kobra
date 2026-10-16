"""PyQt/PySide-Nachbau fuer PyIDE.

Deckt die gaengigen Bausteine ab: Fenster, Layouts, Buttons, Eingabefelder,
Listen, Tabellen, Tabs, Menues, Dialoge, Timer, Signale/Slots und einfaches
Zeichnen mit QPainter (paintEvent).
"""
import inspect as _inspect
import sys as _sys
import time as _time

import pyide_gui as _g

QT_VERSION_STR = "6.8.0"
PYQT_VERSION_STR = "6.8.0"
qVersion = lambda: QT_VERSION_STR  # noqa: E731


# =================================================================== Enums
def _enum(name, **members):
    cls = type(name, (), dict(members))
    return cls


class _GlobalColor(str):
    pass


class Qt:
    AlignmentFlag = _enum("AlignmentFlag", AlignLeft=0x1, AlignLeading=0x1, AlignRight=0x2, AlignTrailing=0x2,
                          AlignHCenter=0x4, AlignJustify=0x8, AlignAbsolute=0x10, AlignTop=0x20,
                          AlignBottom=0x40, AlignVCenter=0x80, AlignBaseline=0x100, AlignCenter=0x84)
    Orientation = _enum("Orientation", Horizontal=1, Vertical=2)
    MouseButton = _enum("MouseButton", NoButton=0, LeftButton=1, RightButton=2, MiddleButton=4)
    KeyboardModifier = _enum("KeyboardModifier", NoModifier=0, ShiftModifier=0x02000000,
                             ControlModifier=0x04000000, AltModifier=0x08000000, MetaModifier=0x10000000)
    CheckState = _enum("CheckState", Unchecked=0, PartiallyChecked=1, Checked=2)
    PenStyle = _enum("PenStyle", NoPen=0, SolidLine=1, DashLine=2, DotLine=3, DashDotLine=4, DashDotDotLine=5)
    BrushStyle = _enum("BrushStyle", NoBrush=0, SolidPattern=1)
    PenCapStyle = _enum("PenCapStyle", FlatCap=0, SquareCap=0x10, RoundCap=0x20)
    PenJoinStyle = _enum("PenJoinStyle", MiterJoin=0, BevelJoin=0x40, RoundJoin=0x80)
    GlobalColor = _enum("GlobalColor", **{n: _GlobalColor(c) for n, c in {
        "white": "#ffffff", "black": "#000000", "red": "#ff0000", "darkRed": "#800000",
        "green": "#00ff00", "darkGreen": "#008000", "blue": "#0000ff", "darkBlue": "#000080",
        "cyan": "#00ffff", "darkCyan": "#008080", "magenta": "#ff00ff", "darkMagenta": "#800080",
        "yellow": "#ffff00", "darkYellow": "#808000", "gray": "#a0a0a4", "darkGray": "#808080",
        "lightGray": "#c0c0c0", "transparent": "rgba(0,0,0,0)", "color0": "#ffffff", "color1": "#000000"}.items()})
    WindowType = _enum("WindowType", Widget=0, Window=1, Dialog=3, Tool=0xB, FramelessWindowHint=0x800,
                       WindowStaysOnTopHint=0x40000, CustomizeWindowHint=0x02000000)
    WidgetAttribute = _enum("WidgetAttribute", WA_DeleteOnClose=55, WA_TranslucentBackground=120,
                            WA_StyledBackground=93)
    FocusPolicy = _enum("FocusPolicy", NoFocus=0, TabFocus=1, ClickFocus=2, StrongFocus=11, WheelFocus=15)
    CursorShape = _enum("CursorShape", ArrowCursor=0, PointingHandCursor=13, CrossCursor=2, WaitCursor=3,
                        IBeamCursor=4, OpenHandCursor=17, ClosedHandCursor=18)
    ScrollBarPolicy = _enum("ScrollBarPolicy", ScrollBarAsNeeded=0, ScrollBarAlwaysOff=1, ScrollBarAlwaysOn=2)
    TextFormat = _enum("TextFormat", PlainText=0, RichText=1, AutoText=2, MarkdownText=3)
    ItemDataRole = _enum("ItemDataRole", DisplayRole=0, DecorationRole=1, EditRole=2, ToolTipRole=3,
                         CheckStateRole=10, UserRole=0x100)
    ItemFlag = _enum("ItemFlag", NoItemFlags=0, ItemIsSelectable=1, ItemIsEditable=2, ItemIsDragEnabled=4,
                     ItemIsDropEnabled=8, ItemIsUserCheckable=16, ItemIsEnabled=32)
    SortOrder = _enum("SortOrder", AscendingOrder=0, DescendingOrder=1)
    AspectRatioMode = _enum("AspectRatioMode", IgnoreAspectRatio=0, KeepAspectRatio=1,
                            KeepAspectRatioByExpanding=2)
    TransformationMode = _enum("TransformationMode", FastTransformation=0, SmoothTransformation=1)
    TextInteractionFlag = _enum("TextInteractionFlag", NoTextInteraction=0, TextSelectableByMouse=1,
                                TextSelectableByKeyboard=2, LinksAccessibleByMouse=4, TextEditable=16)
    ContextMenuPolicy = _enum("ContextMenuPolicy", NoContextMenu=0, DefaultContextMenu=1, CustomContextMenu=3)
    FillRule = _enum("FillRule", OddEvenFill=0, WindingFill=1)
    ConnectionType = _enum("ConnectionType", AutoConnection=0, DirectConnection=1, QueuedConnection=2)
    TimerType = _enum("TimerType", PreciseTimer=0, CoarseTimer=1, VeryCoarseTimer=2)
    LayoutDirection = _enum("LayoutDirection", LeftToRight=0, RightToLeft=1)
    DockWidgetArea = _enum("DockWidgetArea", LeftDockWidgetArea=1, RightDockWidgetArea=2,
                           TopDockWidgetArea=4, BottomDockWidgetArea=8)
    ToolButtonStyle = _enum("ToolButtonStyle", ToolButtonIconOnly=0, ToolButtonTextOnly=1,
                            ToolButtonTextBesideIcon=2, ToolButtonTextUnderIcon=3)
    Key = _enum("Key", Key_Escape=0x01000000, Key_Tab=0x01000001, Key_Backtab=0x01000002,
                Key_Backspace=0x01000003, Key_Return=0x01000004, Key_Enter=0x01000005,
                Key_Insert=0x01000006, Key_Delete=0x01000007, Key_Pause=0x01000008, Key_Home=0x01000010,
                Key_End=0x01000011, Key_Left=0x01000012, Key_Up=0x01000013, Key_Right=0x01000014,
                Key_Down=0x01000015, Key_PageUp=0x01000016, Key_PageDown=0x01000017,
                Key_Shift=0x01000020, Key_Control=0x01000021, Key_Meta=0x01000022, Key_Alt=0x01000023,
                Key_Space=0x20, Key_Plus=0x2b, Key_Minus=0x2d, Key_Comma=0x2c, Key_Period=0x2e,
                Key_Slash=0x2f, Key_Asterisk=0x2a, Key_Equal=0x3d,
                **{"Key_%s" % chr(c): c for c in range(0x41, 0x5b)},
                **{"Key_%d" % d: 0x30 + d for d in range(10)},
                **{"Key_F%d" % i: 0x01000030 + i - 1 for i in range(1, 13)})


def _flatten_enums(cls):
    for name, val in list(vars(cls).items()):
        if isinstance(val, type) and not name.startswith("_"):
            for k, v in vars(val).items():
                if not k.startswith("_") and not hasattr(cls, k):
                    setattr(cls, k, v)


_flatten_enums(Qt)

_KEYS_BY_NAME = {
    "Escape": Qt.Key_Escape, "Tab": Qt.Key_Tab, "BackSpace": Qt.Key_Backspace, "Return": Qt.Key_Return,
    "Delete": Qt.Key_Delete, "Home": Qt.Key_Home, "End": Qt.Key_End, "Left": Qt.Key_Left,
    "Up": Qt.Key_Up, "Right": Qt.Key_Right, "Down": Qt.Key_Down, "Prior": Qt.Key_PageUp,
    "Next": Qt.Key_PageDown, "Shift_L": Qt.Key_Shift, "Control_L": Qt.Key_Control, "Alt_L": Qt.Key_Alt,
    "Meta_L": Qt.Key_Meta, "space": Qt.Key_Space,
}


def _key_code(keysym, char):
    if keysym in _KEYS_BY_NAME:
        return _KEYS_BY_NAME[keysym]
    if keysym and keysym.startswith("F") and keysym[1:].isdigit():
        return 0x01000030 + int(keysym[1:]) - 1
    if char:
        return ord(char.upper())
    return 0


def _mods(lst):
    m = 0
    for name, v in (("Shift", Qt.ShiftModifier), ("Control", Qt.ControlModifier), ("Alt", Qt.AltModifier),
                    ("Meta", Qt.MetaModifier)):
        if name in (lst or []):
            m |= v
    return m


# ============================================================ Signale/Slots
_nparams_cache = {}


def _nparams(func):
    key = id(getattr(func, "__func__", func))
    if key in _nparams_cache:
        return _nparams_cache[key]
    n = None
    try:
        sig = _inspect.signature(func)
        n = 0
        for p in sig.parameters.values():
            if p.kind in (p.VAR_POSITIONAL,):
                n = None
                break
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD):
                n += 1
    except (TypeError, ValueError):
        n = None
    _nparams_cache[key] = n
    return n


class _Sender:
    stack = []


class _BoundSignal:
    def __init__(self, owner, name, types=()):
        self._owner = owner
        self._name = name
        self._slots = []
        self._types = types

    def connect(self, slot, *args, **kw):
        self._slots.append(slot)
        if hasattr(self._owner, "_signal_connected"):
            self._owner._signal_connected(self._name)
        return slot

    def disconnect(self, slot=None):
        if slot is None:
            self._slots = []
        else:
            self._slots = [s for s in self._slots if s != slot]

    def emit(self, *args):
        if getattr(self._owner, "_blocked", False):
            return
        _Sender.stack.append(self._owner)
        try:
            for s in list(self._slots):
                if isinstance(s, _BoundSignal):
                    s.emit(*args)
                    continue
                n = _nparams(s)
                a = args if n is None else args[:n]
                _g._safe_call(s, *a)
        finally:
            _Sender.stack.pop()

    def __getitem__(self, types):
        return self

    def __call__(self, *args):
        self.emit(*args)


class pyqtSignal:
    def __init__(self, *types, name=None, **kw):
        self._types = types
        self._name = name

    def __set_name__(self, owner, name):
        if self._name is None:
            self._name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        sigs = obj.__dict__.setdefault("_signals", {})
        b = sigs.get(self._name)
        if b is None:
            b = sigs[self._name] = _BoundSignal(obj, self._name, self._types)
        return b


Signal = pyqtSignal
pyqtBoundSignal = _BoundSignal


def pyqtSlot(*args, **kw):
    def deco(f):
        return f
    if len(args) == 1 and callable(args[0]) and not isinstance(args[0], type):
        return args[0]
    return deco


Slot = pyqtSlot


def pyqtProperty(type_, fget=None, fset=None, **kw):
    return property(fget, fset)


Property = pyqtProperty


# ============================================================ Grundtypen
class QPoint:
    def __init__(self, x=0, y=0):
        if isinstance(x, QPoint):
            x, y = x._x, x._y
        self._x, self._y = x, y

    def x(self):
        return self._x

    def y(self):
        return self._y

    def setX(self, v):
        self._x = v

    def setY(self, v):
        self._y = v

    def __add__(self, o):
        return type(self)(self._x + o._x, self._y + o._y)

    def __sub__(self, o):
        return type(self)(self._x - o._x, self._y - o._y)

    def __mul__(self, f):
        return type(self)(self._x * f, self._y * f)

    def __eq__(self, o):
        return isinstance(o, QPoint) and (self._x, self._y) == (o._x, o._y)

    def __repr__(self):
        return "%s(%s, %s)" % (type(self).__name__, self._x, self._y)

    def manhattanLength(self):
        return abs(self._x) + abs(self._y)

    def toPoint(self):
        return QPoint(int(round(self._x)), int(round(self._y)))

    def toPointF(self):
        return QPointF(self._x, self._y)


class QPointF(QPoint):
    def __init__(self, x=0.0, y=0.0):
        if isinstance(x, QPoint):
            x, y = x._x, x._y
        self._x, self._y = float(x), float(y)


class QSize:
    def __init__(self, w=0, h=0):
        self._w, self._h = w, h

    def width(self):
        return self._w

    def height(self):
        return self._h

    def setWidth(self, w):
        self._w = w

    def setHeight(self, h):
        self._h = h

    def __repr__(self):
        return "QSize(%s, %s)" % (self._w, self._h)

    def __eq__(self, o):
        return isinstance(o, QSize) and (self._w, self._h) == (o._w, o._h)

    def scaled(self, w, h, mode=0):
        return QSize(w, h)


QSizeF = QSize


class QRect:
    def __init__(self, *a):
        if len(a) == 4:
            self._x, self._y, self._w, self._h = a
        elif len(a) == 2 and isinstance(a[0], QPoint) and isinstance(a[1], QSize):
            self._x, self._y, self._w, self._h = a[0].x(), a[0].y(), a[1].width(), a[1].height()
        elif len(a) == 2 and isinstance(a[0], QPoint):
            self._x, self._y = a[0].x(), a[0].y()
            self._w, self._h = a[1].x() - a[0].x(), a[1].y() - a[0].y()
        else:
            self._x = self._y = self._w = self._h = 0

    def x(self):
        return self._x

    def y(self):
        return self._y

    def width(self):
        return self._w

    def height(self):
        return self._h

    left = x
    top = y

    def right(self):
        return self._x + self._w - 1

    def bottom(self):
        return self._y + self._h - 1

    def center(self):
        return QPoint(self._x + self._w // 2 if isinstance(self._w, int) else self._x + self._w / 2,
                      self._y + self._h // 2 if isinstance(self._h, int) else self._y + self._h / 2)

    def size(self):
        return QSize(self._w, self._h)

    def topLeft(self):
        return QPoint(self._x, self._y)

    def bottomRight(self):
        return QPoint(self.right(), self.bottom())

    def contains(self, *a):
        p = a[0] if isinstance(a[0], QPoint) else QPoint(a[0], a[1])
        return self._x <= p.x() < self._x + self._w and self._y <= p.y() < self._y + self._h

    def intersects(self, r):
        return not (r._x >= self._x + self._w or r._x + r._w <= self._x or
                    r._y >= self._y + self._h or r._y + r._h <= self._y)

    def adjusted(self, a, b, c, d):
        return type(self)(self._x + a, self._y + b, self._w - a + c, self._h - b + d)

    def translated(self, dx, dy=None):
        if isinstance(dx, QPoint):
            dx, dy = dx.x(), dx.y()
        return type(self)(self._x + dx, self._y + dy, self._w, self._h)

    def moveTo(self, x, y=None):
        if isinstance(x, QPoint):
            x, y = x.x(), x.y()
        self._x, self._y = x, y

    def setWidth(self, w):
        self._w = w

    def setHeight(self, h):
        self._h = h

    def isEmpty(self):
        return self._w <= 0 or self._h <= 0

    def __repr__(self):
        return "%s(%s, %s, %s, %s)" % (type(self).__name__, self._x, self._y, self._w, self._h)


class QRectF(QRect):
    pass


class QLine:
    def __init__(self, *a):
        if len(a) == 2:
            self.p1_, self.p2_ = QPoint(a[0]), QPoint(a[1])
        else:
            self.p1_, self.p2_ = QPoint(a[0], a[1]), QPoint(a[2], a[3])

    def p1(self):
        return self.p1_

    def p2(self):
        return self.p2_


QLineF = QLine


class QMargins:
    def __init__(self, l=0, t=0, r=0, b=0):
        self.m = (l, t, r, b)


class QColor:
    _NAMES = {"white": (255, 255, 255), "black": (0, 0, 0), "red": (255, 0, 0), "green": (0, 128, 0),
              "lime": (0, 255, 0), "blue": (0, 0, 255), "yellow": (255, 255, 0), "cyan": (0, 255, 255),
              "magenta": (255, 0, 255), "gray": (128, 128, 128), "grey": (128, 128, 128),
              "orange": (255, 165, 0), "purple": (128, 0, 128), "darkgreen": (0, 100, 0),
              "darkblue": (0, 0, 139), "darkred": (139, 0, 0), "lightgray": (211, 211, 211),
              "lightblue": (173, 216, 230), "navy": (0, 0, 128), "pink": (255, 192, 203),
              "brown": (165, 42, 42), "transparent": (0, 0, 0)}

    def __init__(self, *a):
        self._r = self._g = self._b = 0
        self._a = 255
        if not a:
            return
        if len(a) >= 3:
            self._r, self._g, self._b = int(a[0]), int(a[1]), int(a[2])
            if len(a) > 3:
                self._a = int(a[3])
            return
        v = a[0]
        if isinstance(v, QColor):
            self._r, self._g, self._b, self._a = v._r, v._g, v._b, v._a
            return
        s = str(v).strip()
        if s.startswith("rgba"):
            self._a = 0
            return
        if s.startswith("#"):
            h = s[1:]
            if len(h) == 3:
                h = "".join(c * 2 for c in h)
            if len(h) == 8:
                self._a = int(h[0:2], 16)
                h = h[2:]
            self._r, self._g, self._b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return
        if isinstance(v, int):
            self._r, self._g, self._b = (v >> 16) & 255, (v >> 8) & 255, v & 255
            return
        rgb = self._NAMES.get(s.lower())
        if rgb is None:
            import pyide_colors
            rgb = pyide_colors.to_rgb(s)
        if rgb:
            self._r, self._g, self._b = rgb
            if s.lower() == "transparent":
                self._a = 0

    @staticmethod
    def fromRgb(r, g, b, a=255):
        return QColor(r, g, b, a)

    @staticmethod
    def fromHsv(h, s, v, a=255):
        import colorsys
        r, g, b = colorsys.hsv_to_rgb((h % 360) / 360.0, s / 255.0, v / 255.0)
        return QColor(int(r * 255), int(g * 255), int(b * 255), a)

    @staticmethod
    def fromHsvF(h, s, v, a=1.0):
        return QColor.fromHsv(h * 360, s * 255, v * 255, int(a * 255))

    @staticmethod
    def fromRgbF(r, g, b, a=1.0):
        return QColor(int(r * 255), int(g * 255), int(b * 255), int(a * 255))

    def red(self):
        return self._r

    def green(self):
        return self._g

    def blue(self):
        return self._b

    def alpha(self):
        return self._a

    def setAlpha(self, a):
        self._a = int(a)

    def setRed(self, v):
        self._r = int(v)

    def setGreen(self, v):
        self._g = int(v)

    def setBlue(self, v):
        self._b = int(v)

    def getRgb(self):
        return (self._r, self._g, self._b, self._a)

    def name(self, *a):
        return "#%02x%02x%02x" % (self._r, self._g, self._b)

    def isValid(self):
        return True

    def lighter(self, f=150):
        k = f / 100.0
        return QColor(min(255, int(self._r * k)), min(255, int(self._g * k)), min(255, int(self._b * k)), self._a)

    def darker(self, f=200):
        k = 100.0 / f
        return QColor(int(self._r * k), int(self._g * k), int(self._b * k), self._a)

    def _css(self):
        if self._a == 255:
            return self.name()
        return "rgba(%d,%d,%d,%.3f)" % (self._r, self._g, self._b, self._a / 255.0)

    def __repr__(self):
        return "QColor(%d, %d, %d, %d)" % (self._r, self._g, self._b, self._a)


def _css_color(c):
    if c is None:
        return None
    if isinstance(c, QColor):
        return c._css()
    if isinstance(c, QBrush):
        return c._css()
    if isinstance(c, (tuple, list)):
        return QColor(*c)._css()
    return QColor(c)._css() if not isinstance(c, str) or not c.startswith("rgb") else c


class QPen:
    def __init__(self, *a, **kw):
        self._color = "#000000"
        self._width = 1
        self._style = Qt.SolidLine
        self._cap = Qt.SquareCap
        self._join = Qt.BevelJoin
        if a:
            if isinstance(a[0], QPen):
                o = a[0]
                self._color, self._width, self._style = o._color, o._width, o._style
            elif isinstance(a[0], int) and not isinstance(a[0], _GlobalColor) and a[0] in (0, 1, 2, 3, 4, 5):
                self._style = a[0]
            else:
                self._color = _css_color(a[0])
                if len(a) > 1:
                    self._width = a[1]
                if len(a) > 2:
                    self._style = a[2]
                if len(a) > 3:
                    self._cap = a[3]

    def setColor(self, c):
        self._color = _css_color(c)

    def color(self):
        return QColor(self._color) if self._color.startswith("#") else QColor()

    def setWidth(self, w):
        self._width = w

    setWidthF = setWidth

    def width(self):
        return self._width

    widthF = width

    def setStyle(self, s):
        self._style = s

    def style(self):
        return self._style

    def setCapStyle(self, c):
        self._cap = c

    def setJoinStyle(self, j):
        self._join = j

    def setCosmetic(self, b):
        pass

    def setDashPattern(self, p):
        pass

    def _spec(self):
        if self._style == Qt.NoPen:
            return None
        return {"c": self._color, "w": self._width, "s": self._style,
                "cap": {0: "butt", 0x10: "square", 0x20: "round"}.get(self._cap, "square"),
                "join": {0: "miter", 0x40: "bevel", 0x80: "round"}.get(self._join, "bevel")}


class QBrush:
    def __init__(self, *a):
        self._color = "#000000"
        self._style = Qt.SolidPattern
        if a:
            if isinstance(a[0], QBrush):
                self._color, self._style = a[0]._color, a[0]._style
            elif isinstance(a[0], int) and not isinstance(a[0], _GlobalColor) and a[0] in (0, 1) and len(a) == 1:
                self._style = a[0]
            else:
                self._color = _css_color(a[0])
                if len(a) > 1:
                    self._style = a[1]

    def setColor(self, c):
        self._color = _css_color(c)

    def color(self):
        return QColor(self._color) if self._color.startswith("#") else QColor()

    def setStyle(self, s):
        self._style = s

    def style(self):
        return self._style

    def _css(self):
        return None if self._style == Qt.NoBrush else self._color


class QFont:
    Thin, Light, Normal, Medium, DemiBold, Bold, Black = 100, 300, 400, 500, 600, 700, 900
    Weight = _enum("Weight", Thin=100, Light=300, Normal=400, Medium=500, DemiBold=600, Bold=700, Black=900)

    def __init__(self, family="", pointSize=-1, weight=-1, italic=False):
        if isinstance(family, QFont):
            o = family
            family, pointSize, weight, italic = o._family, o._size, o._weight, o._italic
        self._family = family or "system-ui"
        self._size = pointSize if pointSize and pointSize > 0 else 13
        self._px = None
        self._weight = weight if weight and weight > 0 else 400
        if 0 < self._weight < 100:
            self._weight = {25: 300, 50: 400, 57: 500, 63: 600, 75: 700, 87: 900}.get(self._weight, 400)
        self._italic = italic
        self._underline = False

    def setPointSize(self, s):
        self._size = s
        self._px = None

    setPointSizeF = setPointSize

    def pointSize(self):
        return self._size

    pointSizeF = pointSize

    def setPixelSize(self, s):
        self._px = s

    def pixelSize(self):
        return self._px or int(self._size * 1.333)

    def setBold(self, b):
        self._weight = 700 if b else 400

    def bold(self):
        return self._weight >= 600

    def setItalic(self, b):
        self._italic = bool(b)

    def italic(self):
        return self._italic

    def setUnderline(self, b):
        self._underline = bool(b)

    def setWeight(self, w):
        self._weight = int(w)

    def weight(self):
        return self._weight

    def setFamily(self, f):
        self._family = f

    def family(self):
        return self._family

    def setStyleHint(self, *a):
        pass

    def setLetterSpacing(self, *a):
        pass

    def _spec(self):
        return {"family": self._family, "px": self._px or self._size * 1.333, "weight": self._weight,
                "italic": self._italic, "underline": self._underline}


class QFontMetrics:
    def __init__(self, font):
        self._f = font

    def _measure(self, text):
        res = _g.sync_call("measure", {"qfont": self._f._spec(), "text": str(text)})
        if isinstance(res, (int, float)):
            return int(round(res))
        return int(len(str(text)) * self._f.pixelSize() * 0.58)

    def horizontalAdvance(self, text, *a):
        return self._measure(text)

    width = horizontalAdvance

    def boundingRect(self, text):
        return QRect(0, 0, self._measure(text), self.height())

    def height(self):
        return int(self._f.pixelSize() * 1.25)

    def ascent(self):
        return int(self._f.pixelSize() * 0.8)

    def descent(self):
        return int(self._f.pixelSize() * 0.25)

    def lineSpacing(self):
        return self.height()


QFontMetricsF = QFontMetrics


class QFontDatabase:
    @staticmethod
    def families(*a):
        return ["Helvetica", "Arial", "Times New Roman", "Courier New", "Menlo", "Georgia"]

    @staticmethod
    def systemFont(kind):
        return QFont("Menlo" if kind == 1 else "system-ui")

    FixedFont = 1
    GeneralFont = 0


class QPixmap:
    def __init__(self, *a):
        self._name = None
        self._w = self._h = 0
        self._fill = None
        if a and isinstance(a[0], str):
            try:
                with open(a[0], "rb") as f:
                    data = f.read()
                self._set_data(data)
            except OSError:
                pass
        elif a and isinstance(a[0], QPixmap):
            self._name, self._w, self._h = a[0]._name, a[0]._w, a[0]._h
        elif len(a) >= 2:
            self._w, self._h = int(a[0]), int(a[1])
        elif a and isinstance(a[0], QSize):
            self._w, self._h = a[0].width(), a[0].height()

    def _set_data(self, data):
        import base64
        w, h, mime = _g.image_size(data)
        self._name = _g.new_id("pix")
        self._w, self._h = w, h
        _g.op("img", self._name, mime, base64.b64encode(data).decode("ascii"), w, h)

    @staticmethod
    def fromImage(img):
        return img if isinstance(img, QPixmap) else QPixmap()

    def loadFromData(self, data, fmt=None):
        self._set_data(bytes(data))
        return True

    def load(self, path):
        with open(path, "rb") as f:
            self._set_data(f.read())
        return True

    def width(self):
        return self._w

    def height(self):
        return self._h

    def size(self):
        return QSize(self._w, self._h)

    def rect(self):
        return QRect(0, 0, self._w, self._h)

    def isNull(self):
        return self._name is None and self._fill is None

    def scaled(self, *a, **kw):
        p = QPixmap(self)
        if a and isinstance(a[0], QSize):
            w, h = a[0].width(), a[0].height()
            mode = a[1] if len(a) > 1 else 0
        else:
            w, h = a[0], a[1]
            mode = a[2] if len(a) > 2 else 0
        if mode == 1 and self._w and self._h:
            k = min(w / float(self._w), h / float(self._h))
            w, h = int(self._w * k), int(self._h * k)
        p._w, p._h = int(w), int(h)
        return p

    def scaledToWidth(self, w, *a):
        h = int(self._h * w / float(self._w)) if self._w else w
        return self.scaled(w, h)

    def scaledToHeight(self, h, *a):
        w = int(self._w * h / float(self._h)) if self._h else h
        return self.scaled(w, h)

    def fill(self, color=None):
        self._fill = _css_color(color or "white")

    def save(self, *a, **kw):
        return False


QImage = QPixmap
QBitmap = QPixmap


class QIcon:
    def __init__(self, *a):
        self._pix = QPixmap(*a) if a and isinstance(a[0], str) else (a[0] if a and isinstance(a[0], QPixmap) else None)

    @staticmethod
    def fromTheme(name, fallback=None):
        return QIcon()

    def isNull(self):
        return self._pix is None


class QKeySequence:
    def __init__(self, s=""):
        self._s = s

    def toString(self):
        return str(self._s)

    New, Open, Save, Quit, Copy, Paste, Cut, Undo, Redo, Close, Find = range(11)
    StandardKey = _enum("StandardKey", New=0, Open=1, Save=2, Quit=3, Copy=4, Paste=5, Cut=6, Undo=7,
                        Redo=8, Close=9, Find=10)


class QValidator:
    def __init__(self, *a):
        self._args = a


class QIntValidator(QValidator):
    pass


class QDoubleValidator(QValidator):
    pass


class QRegularExpressionValidator(QValidator):
    pass


class QRegularExpression:
    def __init__(self, p=""):
        self.p = p


class QPolygon(list):
    def __init__(self, pts=()):
        super().__init__(pts)

    def append(self, p):
        super().append(p)

    def __lshift__(self, p):
        self.append(p)
        return self


QPolygonF = QPolygon


class QPainterPath:
    def __init__(self, start=None):
        self._cmds = []
        if start is not None:
            self.moveTo(start)

    def _pt(self, a):
        if len(a) == 1:
            return [a[0].x(), a[0].y()]
        return [a[0], a[1]]

    def moveTo(self, *a):
        self._cmds.append(["M"] + self._pt(a))

    def lineTo(self, *a):
        self._cmds.append(["L"] + self._pt(a))

    def quadTo(self, *a):
        pts = []
        for p in a:
            pts += [p.x(), p.y()] if isinstance(p, QPoint) else [p]
        self._cmds.append(["Q"] + pts)

    def cubicTo(self, *a):
        pts = []
        for p in a:
            pts += [p.x(), p.y()] if isinstance(p, QPoint) else [p]
        self._cmds.append(["C"] + pts)

    def closeSubpath(self):
        self._cmds.append(["Z"])

    def addRect(self, *a):
        r = a[0] if isinstance(a[0], QRect) else QRect(*a)
        self._cmds.append(["R", r.x(), r.y(), r.width(), r.height()])

    def addEllipse(self, *a):
        if len(a) == 1:
            r = a[0]
            x, y, w, h = r.x(), r.y(), r.width(), r.height()
        elif len(a) == 3:
            c, rx, ry = a
            x, y, w, h = c.x() - rx, c.y() - ry, 2 * rx, 2 * ry
        else:
            x, y, w, h = a
        self._cmds.append(["E", x, y, w, h])

    def addText(self, *a):
        pass


# ============================================================= Ereignisse
class QEvent:
    Type = _enum("Type", None_=0, MouseButtonPress=2, MouseButtonRelease=3, MouseMove=5, KeyPress=6,
                 KeyRelease=7, Resize=14, Close=19, Paint=12, Show=17, Hide=18, Enter=10, Leave=11, Wheel=31)
    MouseButtonPress, MouseButtonRelease, MouseMove, KeyPress, KeyRelease = 2, 3, 5, 6, 7

    def __init__(self, t=0):
        self._t = t
        self._accepted = True

    def type(self):
        return self._t

    def accept(self):
        self._accepted = True

    def ignore(self):
        self._accepted = False

    def isAccepted(self):
        return self._accepted

    def setAccepted(self, b):
        self._accepted = bool(b)


class QMouseEvent(QEvent):
    def __init__(self, t, x, y, button, buttons, mods, gx=None, gy=None):
        QEvent.__init__(self, t)
        self._x, self._y = x, y
        self._b, self._bs, self._m = button, buttons, mods
        self._gx = gx if gx is not None else x
        self._gy = gy if gy is not None else y

    def x(self):
        return int(round(self._x))

    def y(self):
        return int(round(self._y))

    def pos(self):
        return QPoint(self.x(), self.y())

    def position(self):
        return QPointF(self._x, self._y)

    def localPos(self):
        return QPointF(self._x, self._y)

    def globalPos(self):
        return QPoint(int(self._gx), int(self._gy))

    def globalPosition(self):
        return QPointF(self._gx, self._gy)

    def globalX(self):
        return int(self._gx)

    def globalY(self):
        return int(self._gy)

    def button(self):
        return self._b

    def buttons(self):
        return self._bs

    def modifiers(self):
        return self._m


class QWheelEvent(QMouseEvent):
    def __init__(self, x, y, delta, mods):
        QMouseEvent.__init__(self, QEvent.Type.Wheel, x, y, 0, 0, mods)
        self._d = delta

    def angleDelta(self):
        return QPoint(0, self._d)

    def delta(self):
        return self._d


class QKeyEvent(QEvent):
    def __init__(self, t, key, mods, text=""):
        QEvent.__init__(self, t)
        self._k, self._m, self._text = key, mods, text

    def key(self):
        return self._k

    def modifiers(self):
        return self._m

    def text(self):
        return self._text

    def isAutoRepeat(self):
        return False


class QResizeEvent(QEvent):
    def __init__(self, size, old):
        QEvent.__init__(self, QEvent.Type.Resize)
        self._s, self._o = size, old

    def size(self):
        return self._s

    def oldSize(self):
        return self._o


class QCloseEvent(QEvent):
    def __init__(self):
        QEvent.__init__(self, QEvent.Type.Close)


class QPaintEvent(QEvent):
    def __init__(self, rect):
        QEvent.__init__(self, QEvent.Type.Paint)
        self._r = rect

    def rect(self):
        return self._r


class QShowEvent(QEvent):
    pass


class QTimerEvent(QEvent):
    def __init__(self, tid):
        QEvent.__init__(self, 1)
        self._id = tid

    def timerId(self):
        return self._id


# ================================================================ QObject
class QObject:
    destroyed = pyqtSignal()
    objectNameChanged = pyqtSignal(str)

    def __init__(self, parent=None, *args, **kwargs):
        self._parent = parent
        self._qchildren = []
        self._objname = ""
        self._blocked = False
        self._props = {}
        if isinstance(parent, QObject):
            parent._qchildren.append(self)
        self._apply_kwargs(kwargs)

    def _apply_kwargs(self, kwargs):
        for k, v in kwargs.items():
            attr = getattr(type(self), k, None)
            if isinstance(attr, pyqtSignal):
                getattr(self, k).connect(v)
                continue
            setter = getattr(self, "set" + k[:1].upper() + k[1:], None)
            if callable(setter):
                setter(v)

    def parent(self):
        return self._parent

    def setParent(self, parent, *a):
        if isinstance(self._parent, QObject) and self in self._parent._qchildren:
            self._parent._qchildren.remove(self)
        self._parent = parent
        if isinstance(parent, QObject):
            parent._qchildren.append(self)

    def children(self):
        return list(self._qchildren)

    def setObjectName(self, name):
        self._objname = str(name)

    def objectName(self):
        return self._objname

    def findChild(self, typ, name=""):
        for c in self.findChildren(typ, name):
            return c
        return None

    def findChildren(self, typ, name=""):
        res = []
        stack = list(self._qchildren)
        while stack:
            c = stack.pop(0)
            if isinstance(c, typ) and (not name or c._objname == name):
                res.append(c)
            stack.extend(c._qchildren)
        return res

    def blockSignals(self, b):
        old = self._blocked
        self._blocked = bool(b)
        return old

    def signalsBlocked(self):
        return self._blocked

    def sender(self):
        return _Sender.stack[-1] if _Sender.stack else None

    def deleteLater(self):
        if isinstance(self, QWidget):
            _g.add_timer(0, self._destroy, ())

    def installEventFilter(self, f):
        pass

    def removeEventFilter(self, f):
        pass

    def setProperty(self, name, value):
        self._props[name] = value
        return True

    def property(self, name):
        return self._props.get(name)

    def startTimer(self, ms, *a):
        t = QTimer(self)
        tid = id(t) % 100000
        t.timeout.connect(lambda: self.timerEvent(QTimerEvent(tid)))
        t.start(ms)
        self._props.setdefault("_timers", {})[tid] = t
        return tid

    def killTimer(self, tid):
        t = self._props.get("_timers", {}).pop(tid, None)
        if t:
            t.stop()

    def timerEvent(self, e):
        pass

    def moveToThread(self, thread):
        pass

    def thread(self):
        return None

    def metaObject(self):
        return None

    def isWidgetType(self):
        return isinstance(self, QWidget)

    def event(self, e):
        return False

    def tr(self, text, *a):
        return text


class QCoreApplication(QObject):
    _instance = None
    aboutToQuit = pyqtSignal()

    def __init__(self, argv=None, *a):
        QObject.__init__(self)
        QCoreApplication._instance = self
        self._argv = list(argv or _sys.argv)
        self._quit = False
        self._code = 0
        self._app_name = ""

    @staticmethod
    def instance():
        return QCoreApplication._instance

    def arguments(self):
        return self._argv

    def exec(self):
        self._quit = False
        _g.run_loop(lambda: self._quit or not _qt_windows_open())
        self.aboutToQuit.emit()
        return self._code

    exec_ = exec

    @staticmethod
    def quit():
        app = QCoreApplication._instance
        if app:
            app._quit = True

    @staticmethod
    def exit(code=0):
        app = QCoreApplication._instance
        if app:
            app._code = code
            app._quit = True

    @staticmethod
    def processEvents(*a):
        _g.update()

    def setApplicationName(self, n):
        self._app_name = n

    def applicationName(self):
        return self._app_name

    def setOrganizationName(self, n):
        pass

    def setApplicationVersion(self, v):
        pass

    @staticmethod
    def setAttribute(*a):
        pass

    @staticmethod
    def translate(ctx, text, *a):
        return text


class QGuiApplication(QCoreApplication):
    @staticmethod
    def primaryScreen():
        return _Screen()

    @staticmethod
    def screens():
        return [_Screen()]

    @staticmethod
    def clipboard():
        return _Clipboard()

    def setFont(self, f):
        _g.op("qt_appfont", f._spec())

    @staticmethod
    def font():
        return QFont()

    @staticmethod
    def setOverrideCursor(*a):
        pass

    @staticmethod
    def restoreOverrideCursor():
        pass

    @staticmethod
    def keyboardModifiers():
        return 0

    @staticmethod
    def setHighDpiScaleFactorRoundingPolicy(*a):
        pass


class _Screen:
    def geometry(self):
        return QRect(0, 0, int(_g._S.screen[0]), int(_g._S.screen[1]))

    availableGeometry = geometry

    def size(self):
        return QSize(int(_g._S.screen[0]), int(_g._S.screen[1]))

    availableSize = size

    def logicalDotsPerInch(self):
        return 96.0

    def devicePixelRatio(self):
        return 2.0


class _Clipboard:
    _text = ""

    def setText(self, t, *a):
        _Clipboard._text = str(t)
        _g.op("clipboard", str(t))

    def text(self, *a):
        return _Clipboard._text

    def clear(self, *a):
        _Clipboard._text = ""


class QApplication(QGuiApplication):
    _stylesheet = ""

    def __init__(self, argv=None, *a):
        QGuiApplication.__init__(self, argv)
        _g.op("qt_app")

    def setStyle(self, style):
        pass

    def style(self):
        return _Style()

    def setStyleSheet(self, css):
        QApplication._stylesheet = str(css)
        _g.op("qt_appcss", str(css))

    def styleSheet(self):
        return QApplication._stylesheet

    @staticmethod
    def desktop():
        return _Desktop()

    @staticmethod
    def topLevelWidgets():
        return [w for w in _g._S.toplevels.values() if isinstance(w, QWidget)]

    allWidgets = topLevelWidgets

    @staticmethod
    def activeWindow():
        w = QApplication.topLevelWidgets()
        return w[-1] if w else None

    @staticmethod
    def beep():
        _g.op("bell")

    def setPalette(self, p):
        pass

    def palette(self):
        return QPalette()

    def setWindowIcon(self, i):
        pass

    def setQuitOnLastWindowClosed(self, b):
        pass


class _Desktop:
    def screenGeometry(self, *a):
        return _Screen().geometry()

    availableGeometry = screenGeometry

    def width(self):
        return int(_g._S.screen[0])

    def height(self):
        return int(_g._S.screen[1])


class _Style:
    def standardIcon(self, *a):
        return QIcon()

    def pixelMetric(self, *a):
        return 16

    def objectName(self):
        return "fusion"


class QStyleFactory:
    @staticmethod
    def create(name):
        return _Style()

    @staticmethod
    def keys():
        return ["Fusion", "Windows"]


class QStyle:
    SP_DialogOkButton = SP_DialogCancelButton = SP_MessageBoxInformation = SP_FileIcon = SP_DirIcon = 0
    StandardPixmap = _enum("StandardPixmap", SP_DialogOkButton=0, SP_FileIcon=1, SP_DirIcon=2)


class QPalette:
    Window, WindowText, Base, Text, Button, ButtonText, Highlight = range(7)
    ColorRole = _enum("ColorRole", Window=0, WindowText=1, Base=2, Text=3, Button=4, ButtonText=5, Highlight=6,
                      Background=0, Foreground=1)
    Background, Foreground = 0, 1

    def __init__(self, *a):
        self._c = {}

    def setColor(self, *a):
        role, color = a[-2], a[-1]
        self._c[role] = _css_color(color)

    def color(self, *a):
        return QColor(self._c.get(a[-1], "#ffffff"))

    def setBrush(self, *a):
        self.setColor(a[-2], a[-1])


def _qt_windows_open():
    return any(isinstance(w, QWidget) for w in _g._S.toplevels.values())


# ================================================================ QTimer
class QTimer(QObject):
    timeout = pyqtSignal()

    def __init__(self, parent=None, **kw):
        QObject.__init__(self, parent, **kw)
        self._interval = 0
        self._single = False
        self._tid = None
        self._active = False

    def setInterval(self, ms):
        self._interval = int(ms)

    def interval(self):
        return self._interval

    def setSingleShot(self, b):
        self._single = bool(b)

    def isSingleShot(self):
        return self._single

    def setTimerType(self, t):
        pass

    def start(self, ms=None):
        if ms is not None:
            self._interval = int(ms)
        self.stop()
        self._active = True
        self._tid = _g.add_timer(self._interval, self._fire)

    def _fire(self):
        if not self._active:
            return
        if self._single:
            self._active = False
        else:
            self._tid = _g.add_timer(max(1, self._interval), self._fire)
        self.timeout.emit()

    def stop(self):
        self._active = False
        if self._tid:
            _g.cancel_timer(self._tid)
            self._tid = None

    def isActive(self):
        return self._active

    def remainingTime(self):
        return self._interval if self._active else -1

    @staticmethod
    def singleShot(ms, *args):
        func = args[-1]
        if isinstance(func, _BoundSignal):
            func = func.emit
        _g.add_timer(int(ms), func)


class QElapsedTimer:
    def __init__(self):
        self._t = None

    def start(self):
        self._t = _time.monotonic()

    def restart(self):
        old = self.elapsed()
        self.start()
        return old

    def elapsed(self):
        return int((_time.monotonic() - (self._t or _time.monotonic())) * 1000)

    def isValid(self):
        return self._t is not None


class QThread(QObject):
    """Kein echtes Threading im Browser: run() laeuft beim start() direkt."""
    started = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._running = False

    def start(self, *a):
        def go():
            self._running = True
            self.started.emit()
            self.run()
            self._running = False
            self.finished.emit()
        _g.add_timer(0, go)

    def run(self):
        pass

    def quit(self):
        pass

    def wait(self, *a):
        return True

    def isRunning(self):
        return self._running

    def isFinished(self):
        return not self._running

    @staticmethod
    def msleep(ms):
        _time.sleep(ms / 1000.0)

    @staticmethod
    def sleep(s):
        _time.sleep(s)

    @staticmethod
    def currentThread():
        return None

    def terminate(self):
        pass

    def requestInterruption(self):
        pass

    def isInterruptionRequested(self):
        return False


class QRunnable:
    def run(self):
        pass

    def setAutoDelete(self, b):
        pass


class QThreadPool(QObject):
    @staticmethod
    def globalInstance():
        return QThreadPool()

    def start(self, runnable, *a):
        _g.add_timer(0, runnable.run)

    def maxThreadCount(self):
        return 1


class QMutex:
    def lock(self):
        pass

    def unlock(self):
        pass


class QSettings(QObject):
    _store = {}

    def __init__(self, *a, **kw):
        QObject.__init__(self)

    def setValue(self, k, v):
        QSettings._store[k] = v

    def value(self, k, default=None, type=None):
        v = QSettings._store.get(k, default)
        return type(v) if type and v is not None else v

    def contains(self, k):
        return k in QSettings._store

    def remove(self, k):
        QSettings._store.pop(k, None)

    def sync(self):
        pass


class QDateTime:
    def __init__(self, dt=None):
        import datetime
        self._dt = dt or datetime.datetime.now()

    @staticmethod
    def currentDateTime():
        return QDateTime()

    def toString(self, fmt="yyyy-MM-dd hh:mm:ss"):
        return _qt_fmt(self._dt, fmt)

    def toPyDateTime(self):
        return self._dt

    def date(self):
        return QDate(self._dt.date())

    def time(self):
        return QTime(self._dt.time())

    def toSecsSinceEpoch(self):
        return int(self._dt.timestamp())

    def toMSecsSinceEpoch(self):
        return int(self._dt.timestamp() * 1000)


class QDate:
    def __init__(self, *a):
        import datetime
        if len(a) == 3:
            self._d = datetime.date(*a)
        elif a:
            self._d = a[0]
        else:
            self._d = datetime.date.today()

    @staticmethod
    def currentDate():
        return QDate()

    def toString(self, fmt="yyyy-MM-dd"):
        return _qt_fmt(self._d, fmt)

    def year(self):
        return self._d.year

    def month(self):
        return self._d.month

    def day(self):
        return self._d.day

    def toPyDate(self):
        return self._d

    def addDays(self, n):
        import datetime
        return QDate(self._d + datetime.timedelta(days=n))


class QTime:
    def __init__(self, *a):
        import datetime
        if a and isinstance(a[0], int):
            self._t = datetime.time(*a)
        elif a:
            self._t = a[0]
        else:
            self._t = datetime.datetime.now().time()

    @staticmethod
    def currentTime():
        return QTime()

    def toString(self, fmt="hh:mm:ss"):
        return _qt_fmt(self._t, fmt)

    def hour(self):
        return self._t.hour

    def minute(self):
        return self._t.minute

    def second(self):
        return self._t.second

    def msec(self):
        return self._t.microsecond // 1000


def _qt_fmt(d, fmt):
    rep = [("yyyy", "%Y"), ("yy", "%y"), ("MMMM", "%B"), ("MMM", "%b"), ("MM", "%m"), ("dddd", "%A"),
           ("ddd", "%a"), ("dd", "%d"), ("HH", "%H"), ("hh", "%H"), ("mm", "%M"), ("ss", "%S"), ("AP", "%p"),
           ("ap", "%p")]
    out = str(fmt)
    for a, b in rep:
        out = out.replace(a, b)
    try:
        return d.strftime(out)
    except Exception:
        return str(d)


class QUrl:
    def __init__(self, s=""):
        self._s = s

    def toString(self):
        return self._s

    @staticmethod
    def fromLocalFile(p):
        return QUrl(p)

    def toLocalFile(self):
        return self._s


class QDesktopServices:
    @staticmethod
    def openUrl(url):
        _g.op("open_url", url.toString() if isinstance(url, QUrl) else str(url))
        return True


# ================================================================ Widgets
_AUTO_EVENTS = ("mousePressEvent", "mouseReleaseEvent", "mouseMoveEvent", "mouseDoubleClickEvent",
                "wheelEvent", "keyPressEvent", "keyReleaseEvent", "paintEvent", "resizeEvent",
                "enterEvent", "leaveEvent")


class QSizePolicy:
    Fixed, Minimum, Maximum, Preferred, Expanding, MinimumExpanding, Ignored = 0, 1, 4, 5, 7, 3, 13
    Policy = _enum("Policy", Fixed=0, Minimum=1, Maximum=4, Preferred=5, Expanding=7, MinimumExpanding=3,
                   Ignored=13)

    def __init__(self, h=5, v=5, *a):
        self._h, self._v = h, v

    def horizontalPolicy(self):
        return self._h

    def verticalPolicy(self):
        return self._v

    def setHorizontalStretch(self, s):
        pass

    def setVerticalStretch(self, s):
        pass

    def setHeightForWidth(self, b):
        pass


class QWidget(QObject):
    _kind = "Widget"
    windowTitleChanged = pyqtSignal(str)
    customContextMenuRequested = pyqtSignal(QPoint)

    def __init__(self, parent=None, *args, **kwargs):
        flags = kwargs.pop("flags", None)
        if args and isinstance(args[0], int):
            flags = args[0]
        QObject.__init__(self, parent)
        self._id = _g.new_id("q")
        self._title = ""
        self._layout = None
        self._visible = None   # None = Standard (Kind sichtbar, Fenster versteckt)
        self._enabled = True
        self._size = None
        self._pos = None
        self._css = ""
        self._font = None
        self._tooltip = ""
        self._announced = None
        self._paint_pending = False
        self._is_window = False
        self._modal = False
        _g.register(self._id, self)
        _g.op("qt_new", self._id, self._kind, self._parent_id(), self._init_opts())
        self._apply_kwargs(kwargs)
        _g.mark_dirty(self)

    # --- interne Helfer
    def _parent_id(self):
        p = self._parent
        while p is not None and not isinstance(p, QWidget):
            p = getattr(p, "_parent", None)
        return p._id if isinstance(p, QWidget) else None

    def _init_opts(self):
        return {}

    def _cfg(self, **opts):
        _g.op("qt_cfg", self._id, opts)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name in _AUTO_EVENTS and "_id" in self.__dict__:
            self._announced = None
            _g.mark_dirty(self)

    def _handler_names(self):
        out = []
        for n in _AUTO_EVENTS:
            if n in self.__dict__:
                out.append(n)
                continue
            attr = getattr(type(self), n, None)
            if attr is not None and not getattr(attr, "_pyide_builtin", False):
                out.append(n)
        return out

    def _pyide_sync(self):
        names = self._handler_names()
        if names != self._announced:
            self._announced = names
            _g.op("qt_events", self._id, names)
        if self._paint_pending and "paintEvent" in names:
            self._paint_pending = False
            self._do_paint()

    def _do_paint(self):
        w, h = self.width(), self.height()
        painter_cmds = []
        _PaintTarget.stack.append(painter_cmds)
        try:
            self.paintEvent(QPaintEvent(QRect(0, 0, w, h)))
        except Exception:
            _g.report_exception()
        finally:
            _PaintTarget.stack.pop()
        _g.op("qt_paint", self._id, painter_cmds)

    def _signal_connected(self, name):
        pass

    # --- Sichtbarkeit / Fenster
    def show(self):
        self._visible = True
        if self._parent_id() is None or self._is_window:
            self._is_window = True
            _g._S.toplevels[self._id] = self
            _g.op("qt_window", self._id, {"title": self._title or self._default_title(),
                                           "size": self._size, "modal": self._modal})
        else:
            self._cfg(visible=True)
        self._paint_pending = True
        _g.mark_dirty(self)
        for c in self.findChildren(QWidget):
            c._paint_pending = True
            _g.mark_dirty(c)

    def _default_title(self):
        try:
            import os
            return os.path.splitext(os.path.basename(_sys.argv[0]))[0]
        except Exception:
            return "python"

    def showMaximized(self):
        self.show()
        _g.op("qt_wm", self._id, "maximize", True)

    showFullScreen = showMaximized

    def showNormal(self):
        self.show()

    def showMinimized(self):
        self.show()

    def hide(self):
        self._visible = False
        if self._is_window:
            _g.op("qt_wm", self._id, "hide", True)
        else:
            self._cfg(visible=False)

    def setVisible(self, b):
        if b:
            self.show()
        else:
            self.hide()

    def setHidden(self, b):
        self.setVisible(not b)

    def isVisible(self):
        return bool(self._visible) if self._is_window or self._parent_id() is None else self._visible is not False

    def isHidden(self):
        return not self.isVisible()

    def isWindow(self):
        return self._is_window or self._parent_id() is None

    def close(self):
        ev = QCloseEvent()
        _g._safe_call(self.closeEvent, ev)
        if not ev.isAccepted():
            return False
        self._visible = False
        if self._is_window:
            _g._S.toplevels.pop(self._id, None)
            _g.op("qt_close", self._id)
        else:
            self._cfg(visible=False)
        return True

    def _destroy(self):
        for c in list(self._qchildren):
            if isinstance(c, QWidget):
                c._destroy()
        _g._S.toplevels.pop(self._id, None)
        _g.unregister(self._id)
        _g.op("destroy", self._id)

    def setWindowTitle(self, t):
        self._title = str(t)
        _g.op("qt_wm", self._id, "title", self._title)
        self.windowTitleChanged.emit(self._title)

    def windowTitle(self):
        return self._title

    def setWindowIcon(self, icon):
        pass

    def setWindowFlags(self, flags):
        if flags & 1 and self._parent is not None:
            self._is_window = True

    def setWindowFlag(self, *a):
        pass

    def windowFlags(self):
        return 0

    def setWindowModality(self, m):
        self._modal = bool(m)

    def setWindowOpacity(self, o):
        _g.op("qt_wm", self._id, "opacity", float(o))

    def raise_(self):
        _g.op("raise", self._id)

    def activateWindow(self):
        pass

    def window(self):
        w = self
        while isinstance(w._parent, QWidget) and not w._is_window:
            w = w._parent
        return w

    # --- Groesse / Position
    def resize(self, *a):
        w, h = (a[0].width(), a[0].height()) if isinstance(a[0], QSize) else (int(a[0]), int(a[1]))
        self._size = [w, h]
        self._cfg(size=[w, h])
        self._paint_pending = True
        _g.mark_dirty(self)

    def move(self, *a):
        x, y = (a[0].x(), a[0].y()) if isinstance(a[0], QPoint) else (a[0], a[1])
        self._pos = [x, y]
        self._cfg(pos=[x, y])

    def setGeometry(self, *a):
        if isinstance(a[0], QRect):
            x, y, w, h = a[0].x(), a[0].y(), a[0].width(), a[0].height()
        else:
            x, y, w, h = a
        self._pos = [x, y]
        self.resize(w, h)
        self._cfg(pos=[x, y])

    def _geom(self):
        g = _g.geometry_of(self._id)
        if not g:
            w, h = self._size or [100, 30]
            x, y = self._pos or [0, 0]
            return [x, y, w, h]
        return g

    def width(self):
        return int(round(self._geom()[2]))

    def height(self):
        return int(round(self._geom()[3]))

    def x(self):
        return int(round(self._geom()[0]))

    def y(self):
        return int(round(self._geom()[1]))

    def size(self):
        return QSize(self.width(), self.height())

    def pos(self):
        return QPoint(self.x(), self.y())

    def rect(self):
        return QRect(0, 0, self.width(), self.height())

    def geometry(self):
        g = self._geom()
        return QRect(int(g[0]), int(g[1]), int(g[2]), int(g[3]))

    frameGeometry = geometry

    def sizeHint(self):
        return QSize(self.width(), self.height())

    minimumSizeHint = sizeHint

    def mapToGlobal(self, p):
        g = self._geom()
        return QPoint(p.x() + int(g[4] if len(g) > 4 else 0), p.y() + int(g[5] if len(g) > 5 else 0))

    def mapFromGlobal(self, p):
        g = self._geom()
        return QPoint(p.x() - int(g[4] if len(g) > 4 else 0), p.y() - int(g[5] if len(g) > 5 else 0))

    def mapTo(self, w, p):
        return p

    def mapFrom(self, w, p):
        return p

    def setFixedSize(self, *a):
        w, h = (a[0].width(), a[0].height()) if isinstance(a[0], QSize) else (a[0], a[1])
        self._size = [w, h]
        self._cfg(fixed=[w, h], size=[w, h])

    def setFixedWidth(self, w):
        self._cfg(fixedW=w)

    def setFixedHeight(self, h):
        self._cfg(fixedH=h)

    def setMinimumSize(self, *a):
        w, h = (a[0].width(), a[0].height()) if isinstance(a[0], QSize) else (a[0], a[1])
        self._cfg(minW=w, minH=h)

    def setMaximumSize(self, *a):
        w, h = (a[0].width(), a[0].height()) if isinstance(a[0], QSize) else (a[0], a[1])
        self._cfg(maxW=w, maxH=h)

    def setMinimumWidth(self, w):
        self._cfg(minW=w)

    def setMinimumHeight(self, h):
        self._cfg(minH=h)

    def setMaximumWidth(self, w):
        self._cfg(maxW=w)

    def setMaximumHeight(self, h):
        self._cfg(maxH=h)

    def adjustSize(self):
        pass

    def updateGeometry(self):
        pass

    def setSizePolicy(self, *a):
        if len(a) == 1 and isinstance(a[0], QSizePolicy):
            h, v = a[0]._h, a[0]._v
        else:
            h, v = a[0], a[1]
        self._cfg(grow=[h in (7, 3, 13), v in (7, 3, 13)])

    def sizePolicy(self):
        return QSizePolicy()

    def setContentsMargins(self, *a):
        if len(a) == 1 and isinstance(a[0], QMargins):
            a = a[0].m
        self._cfg(margins=list(a))

    # --- Aussehen
    def setStyleSheet(self, css):
        self._css = str(css)
        self._cfg(css=self._css)

    def styleSheet(self):
        return self._css

    def setFont(self, f):
        self._font = f
        self._cfg(font=f._spec())

    def font(self):
        return self._font or QFont()

    def fontMetrics(self):
        return QFontMetrics(self.font())

    def setToolTip(self, t):
        self._tooltip = str(t)
        self._cfg(tooltip=self._tooltip)

    def toolTip(self):
        return self._tooltip

    def setStatusTip(self, t):
        pass

    def setWhatsThis(self, t):
        pass

    def setEnabled(self, b):
        self._enabled = bool(b)
        self._cfg(enabled=self._enabled)

    def setDisabled(self, b):
        self.setEnabled(not b)

    def isEnabled(self):
        return self._enabled

    def setCursor(self, c):
        pass

    def unsetCursor(self):
        pass

    def setMouseTracking(self, b):
        self._cfg(tracking=bool(b))

    def hasMouseTracking(self):
        return False

    def setAttribute(self, *a):
        pass

    def testAttribute(self, *a):
        return False

    def setAutoFillBackground(self, b):
        pass

    def setPalette(self, pal):
        bg = pal._c.get(QPalette.Window) or pal._c.get(QPalette.Base)
        fg = pal._c.get(QPalette.WindowText) or pal._c.get(QPalette.Text)
        css = ""
        if bg:
            css += "background-color:%s;" % bg
        if fg:
            css += "color:%s;" % fg
        if css:
            self._cfg(css=self._css + ";" + css)

    def palette(self):
        return QPalette()

    def setFocus(self, *a):
        _g.op("focus", self._id)

    def clearFocus(self):
        pass

    def hasFocus(self):
        return False

    def setFocusPolicy(self, p):
        pass

    def setContextMenuPolicy(self, p):
        pass

    def setAcceptDrops(self, b):
        pass

    def grabMouse(self):
        pass

    def releaseMouse(self):
        pass

    def grabKeyboard(self):
        pass

    def releaseKeyboard(self):
        pass

    def setUpdatesEnabled(self, b):
        pass

    def addAction(self, action):
        pass

    def addActions(self, actions):
        pass

    def setLayoutDirection(self, d):
        pass

    def setGraphicsEffect(self, e):
        pass

    def grab(self, *a):
        return QPixmap()

    def isActiveWindow(self):
        return True

    def winId(self):
        return 0

    def screen(self):
        return _Screen()

    # --- Layout
    def setLayout(self, layout):
        if layout is None:
            return
        self._layout = layout
        layout._owner = self
        layout._adopt(self)
        _g.op("qt_setlayout", self._id, layout._id)

    def layout(self):
        return self._layout

    def parentWidget(self):
        p = self._parent
        return p if isinstance(p, QWidget) else None

    def setParent(self, parent, *a):
        QObject.setParent(self, parent)
        if parent is None:
            self._is_window = True
        _g.op("qt_parent", self._id, self._parent_id())

    # --- Zeichnen
    def update(self, *a):
        self._paint_pending = True
        _g.mark_dirty(self)

    def repaint(self, *a):
        self._paint_pending = True
        _g.mark_dirty(self)
        _g.flush()

    # --- Standard-Handler (ueberschreibbar)
    def paintEvent(self, e):
        pass

    def mousePressEvent(self, e):
        pass

    def mouseReleaseEvent(self, e):
        pass

    def mouseMoveEvent(self, e):
        pass

    def mouseDoubleClickEvent(self, e):
        pass

    def wheelEvent(self, e):
        pass

    def keyPressEvent(self, e):
        p = self.parentWidget()
        if p is not None and "keyPressEvent" in (p._announced or []):
            p.keyPressEvent(e)

    def keyReleaseEvent(self, e):
        pass

    def resizeEvent(self, e):
        pass

    def closeEvent(self, e):
        e.accept()

    def showEvent(self, e):
        pass

    def hideEvent(self, e):
        pass

    def enterEvent(self, e):
        pass

    def leaveEvent(self, e):
        pass

    def focusInEvent(self, e):
        pass

    def focusOutEvent(self, e):
        pass

    def contextMenuEvent(self, e):
        pass

    for _n in _AUTO_EVENTS + ("closeEvent",):
        locals()[_n]._pyide_builtin = True
    del _n

    def _pyide_geometry_changed(self, old, new):
        if old is None or (old[2], old[3]) != (new[2], new[3]):
            names = self._announced or []
            if "resizeEvent" in names:
                _g._safe_call(self.resizeEvent, QResizeEvent(QSize(int(new[2]), int(new[3])),
                                                             QSize(int(old[2]), int(old[3])) if old else QSize()))
            if "paintEvent" in names:
                self._paint_pending = True
                _g.mark_dirty(self)

    def _pyide_event(self, ev):
        k = ev.get("k")
        if k == "close":
            self.close()
            return
        e = ev.get("e")
        if e == "mouse":
            t = ev.get("t")
            btn = {1: Qt.LeftButton, 2: Qt.MiddleButton, 3: Qt.RightButton}.get(ev.get("b", 1), Qt.LeftButton)
            typ = {"press": QEvent.MouseButtonPress, "release": QEvent.MouseButtonRelease,
                   "move": QEvent.MouseMove, "dbl": 4}.get(t, 2)
            me = QMouseEvent(typ, ev.get("x", 0), ev.get("y", 0), btn if t != "move" else Qt.NoButton,
                             btn if ev.get("down") else Qt.NoButton, _mods(ev.get("mods")), ev.get("X"), ev.get("Y"))
            handler = {"press": "mousePressEvent", "release": "mouseReleaseEvent", "move": "mouseMoveEvent",
                       "dbl": "mouseDoubleClickEvent"}.get(t)
            if handler:
                _g._safe_call(getattr(self, handler), me)
        elif e == "wheel":
            _g._safe_call(self.wheelEvent, QWheelEvent(ev.get("x", 0), ev.get("y", 0), ev.get("delta", 0),
                                                       _mods(ev.get("mods"))))
        elif e == "key":
            ke = QKeyEvent(QEvent.KeyPress if ev.get("t") == "press" else QEvent.KeyRelease,
                           _key_code(ev.get("keysym", ""), ev.get("char", "")), _mods(ev.get("mods")),
                           ev.get("char", ""))
            _g._safe_call(self.keyPressEvent if ev.get("t") == "press" else self.keyReleaseEvent, ke)
        elif e == "enter":
            _g._safe_call(self.enterEvent, QEvent(10))
        elif e == "leave":
            _g._safe_call(self.leaveEvent, QEvent(11))
        else:
            self._ui_event(ev)

    def _ui_event(self, ev):
        pass



class QFrame(QWidget):
    _kind = "Frame"
    NoFrame, Box, Panel, StyledPanel, HLine, VLine, WinPanel = 0, 1, 2, 6, 4, 5, 3
    Plain, Raised, Sunken = 0x10, 0x20, 0x30
    Shape = _enum("Shape", NoFrame=0, Box=1, Panel=2, StyledPanel=6, HLine=4, VLine=5)
    Shadow = _enum("Shadow", Plain=0x10, Raised=0x20, Sunken=0x30)

    def setFrameShape(self, s):
        self._cfg(shape=s)

    def setFrameShadow(self, s):
        pass

    def setFrameStyle(self, s):
        self._cfg(shape=s & 0xF)

    def setLineWidth(self, w):
        pass

    def setMidLineWidth(self, w):
        pass


class QLabel(QFrame):
    _kind = "Label"
    linkActivated = pyqtSignal(str)

    def __init__(self, text="", parent=None, *a, **kw):
        if isinstance(text, QWidget) and parent is None:
            text, parent = "", text
        self._text = str(text)
        QFrame.__init__(self, parent, **kw)

    def _init_opts(self):
        return {"text": self._text}

    def setText(self, t):
        self._text = str(t)
        self._cfg(text=self._text, pixmap=None)

    def text(self):
        return self._text

    def setNum(self, n):
        self.setText(str(n))

    def clear(self):
        self.setText("")

    def setAlignment(self, a):
        self._cfg(align=int(a))

    def alignment(self):
        return 0

    def setWordWrap(self, b):
        self._cfg(wrap=bool(b))

    def setPixmap(self, pix):
        self._cfg(pixmap={"name": pix._name, "w": pix._w, "h": pix._h, "fill": pix._fill} if pix else None)

    def setScaledContents(self, b):
        self._cfg(scaled=bool(b))

    def setTextFormat(self, f):
        self._cfg(fmt=int(f))

    def setOpenExternalLinks(self, b):
        pass

    def setTextInteractionFlags(self, f):
        pass

    def setBuddy(self, w):
        pass

    def setIndent(self, i):
        pass

    def setMargin(self, m):
        self._cfg(margins=[m, m, m, m])


class QAbstractButton(QWidget):
    clicked = pyqtSignal(bool)
    pressed = pyqtSignal()
    released = pyqtSignal()
    toggled = pyqtSignal(bool)

    def __init__(self, *args, **kw):
        text, parent = "", None
        for a in args:
            if isinstance(a, str):
                text = a
            elif isinstance(a, QWidget):
                parent = a
        self._text = text
        self._checkable = False
        self._checked = False
        self._group = None
        QWidget.__init__(self, parent, **kw)

    def _init_opts(self):
        return {"text": self._text}

    def setText(self, t):
        self._text = str(t)
        self._cfg(text=self._text)

    def text(self):
        return self._text

    def setCheckable(self, b):
        self._checkable = bool(b)
        self._cfg(checkable=self._checkable)

    def isCheckable(self):
        return self._checkable

    def setChecked(self, b):
        b = bool(b)
        if b == self._checked:
            return
        self._checked = b
        self._cfg(checked=b)
        if b and self._exclusive_group():
            for other in self._exclusive_group():
                if other is not self and other._checked:
                    other._checked = False
                    other._cfg(checked=False)
                    other.toggled.emit(False)
                    other._state_changed()
        self.toggled.emit(b)
        self._state_changed()

    def _state_changed(self):
        pass

    def _exclusive_group(self):
        return None

    def isChecked(self):
        return self._checked

    def toggle(self):
        self.setChecked(not self._checked)

    def click(self):
        if not self._enabled:
            return
        if self._checkable:
            if not (self._checked and self._exclusive_group()):
                self.setChecked(not self._checked)
        self.clicked.emit(self._checked)
        if self._group is not None:
            self._group._clicked(self)

    animateClick = click

    def setIcon(self, icon):
        p = getattr(icon, "_pix", None)
        self._cfg(icon={"name": p._name, "w": p._w, "h": p._h} if p is not None and p._name else None)

    def setIconSize(self, s):
        pass

    def setShortcut(self, s):
        pass

    def setAutoRepeat(self, b):
        pass

    def setAutoExclusive(self, b):
        pass

    def _ui_event(self, ev):
        if ev.get("e") == "clicked":
            self.pressed.emit()
            self.released.emit()
            self.click()


class QPushButton(QAbstractButton):
    _kind = "PushButton"

    def setDefault(self, b):
        pass

    def setAutoDefault(self, b):
        pass

    def setFlat(self, b):
        self._cfg(flat=bool(b))

    def setMenu(self, menu):
        self._menu = menu
        self.clicked.connect(lambda *a: menu.exec(self.mapToGlobal(QPoint(0, self.height()))))


class QToolButton(QPushButton):
    _kind = "PushButton"

    def setToolButtonStyle(self, s):
        pass

    def setPopupMode(self, m):
        pass

    def setDefaultAction(self, a):
        self.setText(a.text())
        self.clicked.connect(lambda *x: a.trigger())

    def setArrowType(self, t):
        pass

    def setAutoRaise(self, b):
        pass


class QCheckBox(QAbstractButton):
    _kind = "CheckBox"
    stateChanged = pyqtSignal(int)
    checkStateChanged = pyqtSignal(int)

    def __init__(self, *a, **kw):
        QAbstractButton.__init__(self, *a, **kw)
        self._checkable = True

    def _state_changed(self):
        self.stateChanged.emit(2 if self._checked else 0)
        self.checkStateChanged.emit(2 if self._checked else 0)

    def checkState(self):
        return Qt.Checked if self._checked else Qt.Unchecked

    def setCheckState(self, s):
        self.setChecked(int(s) == 2 or s is True)

    def setTristate(self, b=True):
        pass

    def _ui_event(self, ev):
        if ev.get("e") == "clicked":
            self.setChecked(not self._checked)
            self.clicked.emit(self._checked)


class QRadioButton(QAbstractButton):
    _kind = "RadioButton"

    def __init__(self, *a, **kw):
        QAbstractButton.__init__(self, *a, **kw)
        self._checkable = True

    def _exclusive_group(self):
        if self._group is not None and self._group._exclusive:
            return self._group._buttons
        p = self.parentWidget()
        if p is None:
            return None
        return [c for c in p.findChildren(QRadioButton) if c.parentWidget() is p and c._group is None]

    def _ui_event(self, ev):
        if ev.get("e") == "clicked":
            if not self._checked:
                self.setChecked(True)
            self.clicked.emit(True)
            if self._group is not None:
                self._group._clicked(self)


class QButtonGroup(QObject):
    buttonClicked = pyqtSignal(object)
    idClicked = pyqtSignal(int)
    buttonToggled = pyqtSignal(object, bool)

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._buttons = []
        self._ids = {}
        self._exclusive = True

    def addButton(self, b, bid=-1):
        self._buttons.append(b)
        b._group = self
        self._ids[id(b)] = bid if bid != -1 else -(len(self._buttons) + 1)

    def removeButton(self, b):
        if b in self._buttons:
            self._buttons.remove(b)
            b._group = None

    def buttons(self):
        return list(self._buttons)

    def checkedButton(self):
        for b in self._buttons:
            if b._checked:
                return b
        return None

    def checkedId(self):
        b = self.checkedButton()
        return self._ids.get(id(b), -1) if b else -1

    def id(self, b):
        return self._ids.get(id(b), -1)

    def button(self, bid):
        for b in self._buttons:
            if self._ids.get(id(b)) == bid:
                return b
        return None

    def setExclusive(self, b):
        self._exclusive = bool(b)

    def _clicked(self, b):
        self.buttonClicked.emit(b)
        self.idClicked.emit(self._ids.get(id(b), -1))


class QLineEdit(QWidget):
    _kind = "LineEdit"
    textChanged = pyqtSignal(str)
    textEdited = pyqtSignal(str)
    returnPressed = pyqtSignal()
    editingFinished = pyqtSignal()
    Normal, NoEcho, Password, PasswordEchoOnEdit = 0, 1, 2, 3
    EchoMode = _enum("EchoMode", Normal=0, NoEcho=1, Password=2, PasswordEchoOnEdit=3)

    def __init__(self, *args, **kw):
        text, parent = "", None
        for a in args:
            if isinstance(a, str):
                text = a
            elif isinstance(a, QWidget):
                parent = a
        self._text = text
        self._validator = None
        QWidget.__init__(self, parent, **kw)

    def _init_opts(self):
        return {"text": self._text}

    def text(self):
        return self._text

    def setText(self, t):
        t = str(t)
        changed = t != self._text
        self._text = t
        self._cfg(text=t)
        if changed:
            self.textChanged.emit(t)

    def clear(self):
        self.setText("")

    def insert(self, t):
        self.setText(self._text + str(t))

    def setPlaceholderText(self, t):
        self._cfg(placeholder=str(t))

    def placeholderText(self):
        return ""

    def setReadOnly(self, b):
        self._cfg(readonly=bool(b))

    def isReadOnly(self):
        return False

    def setEchoMode(self, m):
        self._cfg(echo=int(m))

    def setMaxLength(self, n):
        self._cfg(maxlen=int(n))

    def setAlignment(self, a):
        self._cfg(align=int(a))

    def setValidator(self, v):
        self._validator = v
        if isinstance(v, QIntValidator):
            self._cfg(inputmode="numeric")
        elif isinstance(v, QDoubleValidator):
            self._cfg(inputmode="decimal")

    def setInputMask(self, m):
        pass

    def setClearButtonEnabled(self, b):
        pass

    def selectAll(self):
        pass

    def setCompleter(self, c):
        pass

    def setFrame(self, b):
        pass

    def hasAcceptableInput(self):
        return True

    def setCursorPosition(self, p):
        pass

    def cursorPosition(self):
        return len(self._text)

    def _ui_event(self, ev):
        e = ev.get("e")
        if e == "text":
            t = ev.get("v", "")
            if t != self._text:
                self._text = t
                self.textEdited.emit(t)
                self.textChanged.emit(t)
        elif e == "return":
            self.returnPressed.emit()
            self.editingFinished.emit()
        elif e == "blur":
            self.editingFinished.emit()


class QTextEdit(QFrame):
    _kind = "TextEdit"
    textChanged = pyqtSignal()
    cursorPositionChanged = pyqtSignal()
    NoWrap, WidgetWidth = 0, 1
    LineWrapMode = _enum("LineWrapMode", NoWrap=0, WidgetWidth=1)

    def __init__(self, *args, **kw):
        text, parent = "", None
        for a in args:
            if isinstance(a, str):
                text = a
            elif isinstance(a, QWidget):
                parent = a
        self._text = text
        self._html = None
        QFrame.__init__(self, parent, **kw)

    def _init_opts(self):
        return {"text": self._text}

    def toPlainText(self):
        return self._text

    def setPlainText(self, t):
        self._text = str(t)
        self._html = None
        self._cfg(text=self._text, html=None)
        self.textChanged.emit()

    def setText(self, t):
        t = str(t)
        if "<" in t and ">" in t:
            self.setHtml(t)
        else:
            self.setPlainText(t)

    def setHtml(self, h):
        import re
        self._html = str(h)
        self._text = re.sub(r"<[^>]+>", "", self._html)
        self._cfg(html=self._html)
        self.textChanged.emit()

    def toHtml(self):
        return self._html or self._text

    def setMarkdown(self, m):
        self.setPlainText(m)

    def toMarkdown(self):
        return self._text

    def append(self, t):
        t = str(t)
        if self._html is not None:
            self._html += "<br>" + t
            self._text += "\n" + t
            self._cfg(html=self._html, scroll=True)
        else:
            self._text = (self._text + "\n" + t) if self._text else t
            self._cfg(text=self._text, scroll=True)
        self.textChanged.emit()

    appendPlainText = append

    def appendHtml(self, h):
        if self._html is None:
            import html as _h
            self._html = _h.escape(self._text).replace("\n", "<br>")
        self._html += ("<br>" if self._html else "") + str(h)
        self._cfg(html=self._html, scroll=True)

    def insertPlainText(self, t):
        self._text += str(t)
        self._cfg(text=self._text, scroll=True)
        self.textChanged.emit()

    def insertHtml(self, h):
        self.appendHtml(h)

    def clear(self):
        self.setPlainText("")

    def setReadOnly(self, b):
        self._cfg(readonly=bool(b))

    def isReadOnly(self):
        return False

    def setPlaceholderText(self, t):
        self._cfg(placeholder=str(t))

    def setLineWrapMode(self, m):
        self._cfg(wrap=int(m) != 0)

    def setWordWrapMode(self, m):
        pass

    def setAcceptRichText(self, b):
        pass

    def setTabStopDistance(self, d):
        pass

    def setTabStopWidth(self, d):
        pass

    def moveCursor(self, *a):
        self._cfg(scroll=True)

    def ensureCursorVisible(self):
        self._cfg(scroll=True)

    def textCursor(self):
        return _TextCursor(self)

    def setTextCursor(self, c):
        pass

    def verticalScrollBar(self):
        return _ScrollBar(self)

    def document(self):
        return _Document(self)

    def setFontPointSize(self, s):
        pass

    def setCurrentFont(self, f):
        self.setFont(f)

    def setTextColor(self, c):
        pass

    def setUndoRedoEnabled(self, b):
        pass

    def setMaximumBlockCount(self, n):
        pass

    def _ui_event(self, ev):
        if ev.get("e") == "text":
            self._text = ev.get("v", "")
            self._html = None
            self.textChanged.emit()


QPlainTextEdit = type("QPlainTextEdit", (QTextEdit,), {"_kind": "TextEdit"})
QTextBrowser = type("QTextBrowser", (QTextEdit,), {"_kind": "TextEdit",
                                                   "setOpenExternalLinks": lambda self, b: None})


class _TextCursor:
    End, Start = 11, 1
    MoveOperation = _enum("MoveOperation", End=11, Start=1)

    def __init__(self, edit):
        self._e = edit

    def movePosition(self, *a):
        return True

    def insertText(self, t, *a):
        self._e.insertPlainText(t)

    def insertHtml(self, h):
        self._e.appendHtml(h)

    def selectedText(self):
        return ""

    def position(self):
        return len(self._e._text)


class _ScrollBar:
    def __init__(self, w):
        self._w = w

    def setValue(self, v):
        self._w._cfg(scroll=True)

    def maximum(self):
        return 0

    def value(self):
        return 0


class _Document:
    def __init__(self, e):
        self._e = e

    def toPlainText(self):
        return self._e._text

    def setDefaultFont(self, f):
        pass

    def isModified(self):
        return False

    def setModified(self, b):
        pass

    def blockCount(self):
        return self._e._text.count("\n") + 1


class QComboBox(QWidget):
    _kind = "ComboBox"
    currentIndexChanged = pyqtSignal(int)
    currentTextChanged = pyqtSignal(str)
    activated = pyqtSignal(int)
    textActivated = pyqtSignal(str)
    editTextChanged = pyqtSignal(str)

    def __init__(self, parent=None, **kw):
        self._items = []
        self._data = []
        self._index = -1
        QWidget.__init__(self, parent, **kw)

    def _sync_items(self):
        self._cfg(items=list(self._items), index=self._index)

    def addItem(self, *a):
        text = a[0] if isinstance(a[0], str) else (a[1] if len(a) > 1 else "")
        data = a[1] if isinstance(a[0], str) and len(a) > 1 else (a[2] if len(a) > 2 else None)
        self._items.append(str(text))
        self._data.append(data)
        if self._index < 0:
            self._index = 0
            self._sync_items()
            self.currentIndexChanged.emit(0)
            self.currentTextChanged.emit(self._items[0])
        else:
            self._sync_items()

    def addItems(self, texts):
        for t in texts:
            self.addItem(str(t))

    def insertItem(self, i, text, data=None):
        self._items.insert(i, str(text))
        self._data.insert(i, data)
        if self._index < 0:
            self._index = 0
        self._sync_items()

    def insertItems(self, i, texts):
        for k, t in enumerate(texts):
            self.insertItem(i + k, t)

    def removeItem(self, i):
        del self._items[i]
        del self._data[i]
        if self._index >= len(self._items):
            self._index = len(self._items) - 1
        self._sync_items()

    def clear(self):
        self._items, self._data, self._index = [], [], -1
        self._sync_items()

    def count(self):
        return len(self._items)

    def currentIndex(self):
        return self._index

    def currentText(self):
        return self._items[self._index] if 0 <= self._index < len(self._items) else ""

    def currentData(self, role=None):
        return self._data[self._index] if 0 <= self._index < len(self._data) else None

    def itemText(self, i):
        return self._items[i]

    def itemData(self, i, role=None):
        return self._data[i]

    def setItemText(self, i, t):
        self._items[i] = str(t)
        self._sync_items()

    def setCurrentIndex(self, i):
        i = int(i)
        if i == self._index:
            return
        self._index = i
        self._cfg(index=i)
        self.currentIndexChanged.emit(i)
        self.currentTextChanged.emit(self.currentText())

    def setCurrentText(self, t):
        if t in self._items:
            self.setCurrentIndex(self._items.index(t))

    def findText(self, t, *a):
        return self._items.index(t) if t in self._items else -1

    def findData(self, d, *a):
        return self._data.index(d) if d in self._data else -1

    def setEditable(self, b):
        self._cfg(editable=bool(b))

    def setPlaceholderText(self, t):
        pass

    def setMaxVisibleItems(self, n):
        pass

    def setSizeAdjustPolicy(self, p):
        pass

    def _ui_event(self, ev):
        if ev.get("e") == "index":
            i = int(ev.get("v", 0))
            self.activated.emit(i)
            if i != self._index:
                self._index = i
                self.currentIndexChanged.emit(i)
                self.currentTextChanged.emit(self.currentText())
            self.textActivated.emit(self.currentText())


class QAbstractSlider(QWidget):
    valueChanged = pyqtSignal(int)
    sliderMoved = pyqtSignal(int)
    sliderPressed = pyqtSignal()
    sliderReleased = pyqtSignal()
    rangeChanged = pyqtSignal(int, int)

    def __init__(self, *args, **kw):
        orient, parent = Qt.Vertical, None
        for a in args:
            if isinstance(a, QWidget):
                parent = a
            elif isinstance(a, int):
                orient = a
        self._min, self._max, self._value, self._step = 0, 99, 0, 1
        self._orient = orient
        QWidget.__init__(self, parent, **kw)

    def _init_opts(self):
        return {"min": self._min, "max": self._max, "value": self._value, "orient": self._orient}

    def setOrientation(self, o):
        self._orient = o
        self._cfg(orient=o)

    def setMinimum(self, v):
        self._min = v
        self._cfg(min=v)
        if self._value < v:
            self.setValue(v)

    def setMaximum(self, v):
        self._max = v
        self._cfg(max=v)
        if self._value > v:
            self.setValue(v)

    def setRange(self, a, b):
        self._min, self._max = a, b
        self._cfg(min=a, max=b)
        self.setValue(min(max(self._value, a), b))
        self.rangeChanged.emit(a, b)

    def minimum(self):
        return self._min

    def maximum(self):
        return self._max

    def setValue(self, v):
        v = min(max(type(self._value)(v) if not isinstance(self._value, int) else int(round(v)), self._min), self._max)
        if v == self._value:
            return
        self._value = v
        self._cfg(value=v)
        self.valueChanged.emit(v)

    def value(self):
        return self._value

    def setSingleStep(self, s):
        self._step = s
        self._cfg(step=s)

    def singleStep(self):
        return self._step

    def setPageStep(self, s):
        pass

    def setTickPosition(self, p):
        pass

    def setTickInterval(self, i):
        pass

    def setTracking(self, b):
        pass

    def setInvertedAppearance(self, b):
        pass

    def setNotchesVisible(self, b):
        pass

    def setWrapping(self, b):
        pass

    def _ui_event(self, ev):
        if ev.get("e") == "value":
            v = ev.get("v", 0)
            v = int(round(float(v))) if isinstance(self._value, int) else float(v)
            if v != self._value:
                self._value = v
                self.sliderMoved.emit(v)
                self.valueChanged.emit(v)
        elif ev.get("e") == "release":
            self.sliderReleased.emit()


class QSlider(QAbstractSlider):
    _kind = "Slider"
    NoTicks, TicksAbove, TicksBelow, TicksBothSides = 0, 1, 2, 3
    TickPosition = _enum("TickPosition", NoTicks=0, TicksAbove=1, TicksBelow=2, TicksBothSides=3,
                         TicksLeft=1, TicksRight=2)


class QDial(QAbstractSlider):
    _kind = "Slider"


class QScrollBar(QAbstractSlider):
    _kind = "Slider"


class QSpinBox(QWidget):
    _kind = "SpinBox"
    valueChanged = pyqtSignal(int)
    textChanged = pyqtSignal(str)
    editingFinished = pyqtSignal()
    _cast = int

    def __init__(self, parent=None, **kw):
        self._min, self._max, self._value, self._step = 0, 99, 0, 1
        self._decimals = 0
        self._prefix = self._suffix = ""
        QWidget.__init__(self, parent, **kw)

    def _init_opts(self):
        return {"min": self._min, "max": self._max, "value": self._value, "step": self._step,
                "decimals": self._decimals}

    def setMinimum(self, v):
        self._min = self._cast(v)
        self._cfg(min=self._min)
        if self._value < self._min:
            self.setValue(self._min)

    def setMaximum(self, v):
        self._max = self._cast(v)
        self._cfg(max=self._max)
        if self._value > self._max:
            self.setValue(self._max)

    def setRange(self, a, b):
        self._min, self._max = self._cast(a), self._cast(b)
        self._cfg(min=self._min, max=self._max)
        self.setValue(min(max(self._value, self._min), self._max))

    def minimum(self):
        return self._min

    def maximum(self):
        return self._max

    def setSingleStep(self, s):
        self._step = s
        self._cfg(step=s)

    def setValue(self, v):
        v = min(max(self._cast(v), self._min), self._max)
        if self._cast is float:
            v = round(v, self._decimals)
        if v == self._value:
            return
        self._value = v
        self._cfg(value=v)
        self.valueChanged.emit(v)
        self.textChanged.emit(self.text())

    def value(self):
        return self._value

    def text(self):
        return "%s%s%s" % (self._prefix, self._value, self._suffix)

    def cleanText(self):
        return str(self._value)

    def setPrefix(self, p):
        self._prefix = p
        self._cfg(prefix=p)

    def setSuffix(self, s):
        self._suffix = s
        self._cfg(suffix=s)

    def setDecimals(self, d):
        self._decimals = int(d)
        self._cfg(decimals=self._decimals)

    def setWrapping(self, b):
        pass

    def setAlignment(self, a):
        pass

    def setButtonSymbols(self, b):
        pass

    def setReadOnly(self, b):
        self._cfg(readonly=bool(b))

    def setSpecialValueText(self, t):
        pass

    def stepUp(self):
        self.setValue(self._value + self._step)

    def stepDown(self):
        self.setValue(self._value - self._step)

    def _ui_event(self, ev):
        if ev.get("e") == "value":
            try:
                v = self._cast(float(ev.get("v", 0)))
            except (TypeError, ValueError):
                return
            v = min(max(v, self._min), self._max)
            if v != self._value:
                self._value = v
                self.valueChanged.emit(v)
                self.textChanged.emit(self.text())
            self._cfg(value=v)


class QDoubleSpinBox(QSpinBox):
    valueChanged = pyqtSignal(float)
    _cast = float

    def __init__(self, parent=None, **kw):
        QSpinBox.__init__(self, parent, **kw)
        self._value = 0.0
        self._min, self._max = 0.0, 99.99
        self._decimals = 2
        self._step = 1.0
        self._cfg(**self._init_opts())


class QProgressBar(QWidget):
    _kind = "ProgressBar"
    valueChanged = pyqtSignal(int)

    def __init__(self, parent=None, **kw):
        self._min, self._max, self._value = 0, 100, 0
        self._fmt = "%p%"
        QWidget.__init__(self, parent, **kw)

    def _init_opts(self):
        return {"min": self._min, "max": self._max, "value": self._value}

    def setRange(self, a, b):
        self._min, self._max = a, b
        self._cfg(min=a, max=b)

    def setMinimum(self, v):
        self._min = v
        self._cfg(min=v)

    def setMaximum(self, v):
        self._max = v
        self._cfg(max=v)

    def setValue(self, v):
        self._value = int(v)
        self._cfg(value=self._value)
        self.valueChanged.emit(self._value)

    def value(self):
        return self._value

    def minimum(self):
        return self._min

    def maximum(self):
        return self._max

    def reset(self):
        self.setValue(self._min)

    def setFormat(self, f):
        self._fmt = f
        self._cfg(format=f)

    def setTextVisible(self, b):
        self._cfg(textVisible=bool(b))

    def setOrientation(self, o):
        pass

    def setAlignment(self, a):
        pass

    def setInvertedAppearance(self, b):
        pass


class QListWidgetItem:
    def __init__(self, *args):
        self._text = ""
        self._data = {}
        self._list = None
        self._checked = None
        self._flags = 0
        for a in args:
            if isinstance(a, str):
                self._text = a
            elif isinstance(a, QListWidget):
                a.addItem(self)

    def text(self):
        return self._text

    def setText(self, t):
        self._text = str(t)
        if self._list:
            self._list._sync()

    def data(self, role=0):
        if role == 0:
            return self._text
        return self._data.get(role)

    def setData(self, role, value):
        if role == 0:
            self.setText(value)
        else:
            self._data[role] = value

    def setCheckState(self, s):
        self._checked = int(s) == 2
        if self._list:
            self._list._sync()

    def checkState(self):
        return Qt.Checked if self._checked else Qt.Unchecked

    def setFlags(self, f):
        self._flags = f

    def flags(self):
        return self._flags

    def setForeground(self, c):
        self._data["fg"] = _css_color(c.color() if isinstance(c, QBrush) else c)

    def setBackground(self, c):
        self._data["bg"] = _css_color(c.color() if isinstance(c, QBrush) else c)

    def setToolTip(self, t):
        pass

    def setIcon(self, i):
        pass

    def setTextAlignment(self, a):
        pass

    def setSelected(self, b):
        if self._list and b:
            self._list.setCurrentItem(self)

    def isSelected(self):
        return bool(self._list) and self._list.currentItem() is self

    def listWidget(self):
        return self._list

    def setFont(self, f):
        pass

    def setSizeHint(self, s):
        pass


class QAbstractItemView(QFrame):
    NoEditTriggers, DoubleClicked, AllEditTriggers = 0, 2, 31
    SingleSelection, MultiSelection, ExtendedSelection, NoSelection = 1, 2, 3, 0
    SelectRows, SelectItems, SelectColumns = 1, 0, 2
    EditTrigger = _enum("EditTrigger", NoEditTriggers=0, DoubleClicked=2, AllEditTriggers=31)
    SelectionMode = _enum("SelectionMode", SingleSelection=1, MultiSelection=2, ExtendedSelection=3,
                          NoSelection=0)
    SelectionBehavior = _enum("SelectionBehavior", SelectRows=1, SelectItems=0, SelectColumns=2)

    def setEditTriggers(self, t):
        self._cfg(editable=int(t) != 0)

    def setSelectionMode(self, m):
        self._cfg(selmode=int(m))

    def setSelectionBehavior(self, b):
        pass

    def setAlternatingRowColors(self, b):
        self._cfg(alternate=bool(b))

    def setDragDropMode(self, m):
        pass

    def setHorizontalScrollBarPolicy(self, p):
        pass

    def setVerticalScrollBarPolicy(self, p):
        pass

    def scrollToBottom(self):
        self._cfg(scroll=True)

    def scrollToItem(self, *a):
        pass

    def scrollTo(self, *a):
        pass

    def setIconSize(self, s):
        pass

    def setWordWrap(self, b):
        pass


class QListWidget(QAbstractItemView):
    _kind = "ListWidget"
    itemClicked = pyqtSignal(object)
    itemDoubleClicked = pyqtSignal(object)
    currentRowChanged = pyqtSignal(int)
    currentItemChanged = pyqtSignal(object, object)
    itemSelectionChanged = pyqtSignal()
    currentTextChanged = pyqtSignal(str)
    itemChanged = pyqtSignal(object)
    itemActivated = pyqtSignal(object)

    def __init__(self, parent=None, **kw):
        self._items = []
        self._row = -1
        self._multi = []
        QAbstractItemView.__init__(self, parent, **kw)

    def _sync(self):
        self._cfg(items=[{"t": i._text, "c": i._checked, "fg": i._data.get("fg"), "bg": i._data.get("bg")}
                         for i in self._items], row=self._row)

    def addItem(self, item):
        if not isinstance(item, QListWidgetItem):
            item = QListWidgetItem(str(item))
        item._list = self
        self._items.append(item)
        self._sync()

    def addItems(self, items):
        for i in items:
            it = QListWidgetItem(str(i))
            it._list = self
            self._items.append(it)
        self._sync()

    def insertItem(self, row, item):
        if not isinstance(item, QListWidgetItem):
            item = QListWidgetItem(str(item))
        item._list = self
        self._items.insert(row, item)
        self._sync()

    def takeItem(self, row):
        if 0 <= row < len(self._items):
            it = self._items.pop(row)
            it._list = None
            if self._row >= len(self._items):
                self._row = len(self._items) - 1
            self._sync()
            return it
        return None

    def item(self, row):
        return self._items[row] if 0 <= row < len(self._items) else None

    def row(self, item):
        return self._items.index(item) if item in self._items else -1

    def count(self):
        return len(self._items)

    def clear(self):
        self._items = []
        self._row = -1
        self._sync()

    def currentRow(self):
        return self._row

    def setCurrentRow(self, r):
        old = self.currentItem()
        self._row = r
        self._cfg(row=r)
        self.currentRowChanged.emit(r)
        self.currentItemChanged.emit(self.currentItem(), old)
        self.itemSelectionChanged.emit()

    def currentItem(self):
        return self.item(self._row)

    def setCurrentItem(self, item):
        self.setCurrentRow(self.row(item))

    def selectedItems(self):
        if self._multi:
            return [self._items[i] for i in self._multi if 0 <= i < len(self._items)]
        it = self.currentItem()
        return [it] if it else []

    def findItems(self, text, flags=0):
        return [i for i in self._items if text in i._text]

    def sortItems(self, order=0):
        self._items.sort(key=lambda i: i._text, reverse=bool(order))
        self._sync()

    def setSortingEnabled(self, b):
        pass

    def editItem(self, item):
        pass

    def openPersistentEditor(self, item):
        pass

    def _ui_event(self, ev):
        e = ev.get("e")
        if e == "row":
            r = int(ev.get("v", -1))
            old = self.currentItem()
            self._multi = list(ev.get("multi") or [])
            if r != self._row:
                self._row = r
                self.currentRowChanged.emit(r)
                self.currentItemChanged.emit(self.currentItem(), old)
                if self.currentItem():
                    self.currentTextChanged.emit(self.currentItem()._text)
            self.itemSelectionChanged.emit()
            if self.currentItem():
                self.itemClicked.emit(self.currentItem())
        elif e == "dbl":
            it = self.item(int(ev.get("v", -1)))
            if it:
                self.itemDoubleClicked.emit(it)
                self.itemActivated.emit(it)
        elif e == "check":
            it = self.item(int(ev.get("r", -1)))
            if it:
                it._checked = bool(ev.get("v"))
                self.itemChanged.emit(it)


class QTableWidgetItem:
    def __init__(self, text="", *a):
        self._text = str(text)
        self._data = {}
        self._table = None
        self._flags = 63
        self._checked = None

    def text(self):
        return self._text

    def setText(self, t):
        self._text = str(t)
        if self._table:
            self._table._sync()

    def data(self, role=0):
        return self._text if role in (0, 2) else self._data.get(role)

    def setData(self, role, v):
        if role in (0, 2):
            self.setText(v)
        else:
            self._data[role] = v

    def setFlags(self, f):
        self._flags = f

    def flags(self):
        return self._flags

    def setTextAlignment(self, a):
        self._data["align"] = int(a)

    def setForeground(self, c):
        self._data["fg"] = _css_color(c.color() if isinstance(c, QBrush) else c)

    def setBackground(self, c):
        self._data["bg"] = _css_color(c.color() if isinstance(c, QBrush) else c)

    def setCheckState(self, s):
        self._checked = int(s) == 2

    def checkState(self):
        return Qt.Checked if self._checked else Qt.Unchecked

    def setToolTip(self, t):
        pass

    def setFont(self, f):
        pass

    def row(self):
        return self._table._pos_of(self)[0] if self._table else -1

    def column(self):
        return self._table._pos_of(self)[1] if self._table else -1


class _HeaderView:
    Stretch, ResizeToContents, Interactive, Fixed = 1, 3, 0, 2
    ResizeMode = _enum("ResizeMode", Stretch=1, ResizeToContents=3, Interactive=0, Fixed=2)

    def __init__(self, table=None):
        self._t = table

    def __getattr__(self, name):
        def anything(*a, **k):
            if name in ("setSectionResizeMode", "setStretchLastSection") and self._t is not None:
                self._t._cfg(stretch=True)
            return None
        return anything


QHeaderView = _HeaderView


class QTableWidget(QAbstractItemView):
    _kind = "TableWidget"
    cellClicked = pyqtSignal(int, int)
    cellDoubleClicked = pyqtSignal(int, int)
    cellChanged = pyqtSignal(int, int)
    itemChanged = pyqtSignal(object)
    itemClicked = pyqtSignal(object)
    currentCellChanged = pyqtSignal(int, int, int, int)
    itemSelectionChanged = pyqtSignal()

    def __init__(self, *args, **kw):
        rows = cols = 0
        parent = None
        nums = [a for a in args if isinstance(a, int)]
        for a in args:
            if isinstance(a, QWidget):
                parent = a
        if len(nums) >= 2:
            rows, cols = nums[0], nums[1]
        self._rows, self._cols = rows, cols
        self._cells = {}
        self._hlabels = []
        self._vlabels = []
        self._cur = (-1, -1)
        self._editable = True
        QAbstractItemView.__init__(self, parent, **kw)
        self._sync()

    def _pos_of(self, item):
        for k, v in self._cells.items():
            if v is item:
                return k
        return (-1, -1)

    def _sync(self):
        cells = {}
        for (r, c), it in self._cells.items():
            if r < self._rows and c < self._cols:
                cells["%d,%d" % (r, c)] = {"t": it._text, "fg": it._data.get("fg"), "bg": it._data.get("bg"),
                                           "ro": not (it._flags & 2)}
        _g.mark_dirty(self)
        self._pending_cells = cells

    def _pyide_sync(self):
        cells = getattr(self, "_pending_cells", None)
        if cells is not None:
            self._pending_cells = None
            self._cfg(rows=self._rows, cols=self._cols, cells=cells, hlabels=self._hlabels, vlabels=self._vlabels)
        QAbstractItemView._pyide_sync(self)

    def setRowCount(self, n):
        self._rows = int(n)
        self._sync()

    def setColumnCount(self, n):
        self._cols = int(n)
        self._sync()

    def rowCount(self):
        return self._rows

    def columnCount(self):
        return self._cols

    def insertRow(self, r):
        self._cells = {((rr + 1 if rr >= r else rr), c): v for (rr, c), v in self._cells.items()}
        self._rows += 1
        self._sync()

    def removeRow(self, r):
        self._cells = {((rr - 1 if rr > r else rr), c): v for (rr, c), v in self._cells.items() if rr != r}
        self._rows = max(0, self._rows - 1)
        self._sync()

    def insertColumn(self, c):
        self._cells = {(r, (cc + 1 if cc >= c else cc)): v for (r, cc), v in self._cells.items()}
        self._cols += 1
        self._sync()

    def removeColumn(self, c):
        self._cells = {(r, (cc - 1 if cc > c else cc)): v for (r, cc), v in self._cells.items() if cc != c}
        self._cols = max(0, self._cols - 1)
        self._sync()

    def setItem(self, r, c, item):
        if not isinstance(item, QTableWidgetItem):
            item = QTableWidgetItem(str(item))
        item._table = self
        self._cells[(r, c)] = item
        self._sync()

    def item(self, r, c):
        return self._cells.get((r, c))

    def takeItem(self, r, c):
        it = self._cells.pop((r, c), None)
        self._sync()
        return it

    def setHorizontalHeaderLabels(self, labels):
        self._hlabels = [str(x) for x in labels]
        if len(self._hlabels) > self._cols:
            self._cols = len(self._hlabels)
        self._sync()

    def setVerticalHeaderLabels(self, labels):
        self._vlabels = [str(x) for x in labels]
        self._sync()

    def setHorizontalHeaderItem(self, c, item):
        while len(self._hlabels) <= c:
            self._hlabels.append(str(len(self._hlabels) + 1))
        self._hlabels[c] = item.text() if isinstance(item, QTableWidgetItem) else str(item)
        self._sync()

    def horizontalHeaderItem(self, c):
        return QTableWidgetItem(self._hlabels[c]) if c < len(self._hlabels) else None

    def horizontalHeader(self):
        return _HeaderView(self)

    def verticalHeader(self):
        return _HeaderView()

    def setCellWidget(self, r, c, w):
        pass

    def clear(self):
        self._cells = {}
        self._hlabels = []
        self._sync()

    def clearContents(self):
        self._cells = {}
        self._sync()

    def currentRow(self):
        return self._cur[0]

    def currentColumn(self):
        return self._cur[1]

    def currentItem(self):
        return self._cells.get(self._cur)

    def setCurrentCell(self, r, c):
        self._cur = (r, c)

    def selectedItems(self):
        it = self.currentItem()
        return [it] if it else []

    def resizeColumnsToContents(self):
        pass

    def resizeRowsToContents(self):
        pass

    def setColumnWidth(self, c, w):
        pass

    def setRowHeight(self, r, h):
        pass

    def setSortingEnabled(self, b):
        pass

    def setShowGrid(self, b):
        pass

    def sortItems(self, c, order=0):
        rows = []
        for r in range(self._rows):
            rows.append([self._cells.get((r, cc)) for cc in range(self._cols)])

        def key(row):
            it = row[c]
            t = it._text if it else ""
            try:
                return (0, float(t), "")
            except ValueError:
                return (1, 0, t)
        rows.sort(key=key, reverse=bool(order))
        self._cells = {}
        for r, row in enumerate(rows):
            for cc, it in enumerate(row):
                if it is not None:
                    self._cells[(r, cc)] = it
        self._sync()

    def _ui_event(self, ev):
        e = ev.get("e")
        r, c = int(ev.get("r", -1)), int(ev.get("c", -1))
        if e == "cell":
            old = self._cur
            self._cur = (r, c)
            self.cellClicked.emit(r, c)
            if self.item(r, c):
                self.itemClicked.emit(self.item(r, c))
            self.currentCellChanged.emit(r, c, old[0], old[1])
            self.itemSelectionChanged.emit()
        elif e == "dbl":
            self.cellDoubleClicked.emit(r, c)
        elif e == "edit":
            it = self._cells.get((r, c))
            if it is None:
                it = QTableWidgetItem("")
                it._table = self
                self._cells[(r, c)] = it
            it._text = str(ev.get("v", ""))
            self.cellChanged.emit(r, c)
            self.itemChanged.emit(it)


QTableView = QTableWidget
QListView = QListWidget


class QTreeWidgetItem:
    def __init__(self, *args):
        self._texts = []
        self._children = []
        self._parent = None
        for a in args:
            if isinstance(a, (list, tuple)):
                self._texts = [str(x) for x in a]
            elif isinstance(a, QTreeWidget):
                a.addTopLevelItem(self)
            elif isinstance(a, QTreeWidgetItem):
                a.addChild(self)

    def text(self, c):
        return self._texts[c] if c < len(self._texts) else ""

    def setText(self, c, t):
        while len(self._texts) <= c:
            self._texts.append("")
        self._texts[c] = str(t)

    def addChild(self, it):
        it._parent = self
        self._children.append(it)

    def child(self, i):
        return self._children[i]

    def childCount(self):
        return len(self._children)

    def parent(self):
        return self._parent

    def setExpanded(self, b):
        pass

    def setData(self, *a):
        pass

    def data(self, *a):
        return None


class QTreeWidget(QAbstractItemView):
    _kind = "TableWidget"
    itemClicked = pyqtSignal(object, int)

    def __init__(self, parent=None, **kw):
        self._top = []
        self._headers = []
        QAbstractItemView.__init__(self, parent, **kw)

    def setHeaderLabels(self, labels):
        self._headers = list(labels)
        self._sync()

    def setColumnCount(self, n):
        pass

    def addTopLevelItem(self, it):
        self._top.append(it)
        self._sync()

    def addTopLevelItems(self, its):
        self._top.extend(its)
        self._sync()

    def topLevelItem(self, i):
        return self._top[i]

    def topLevelItemCount(self):
        return len(self._top)

    def clear(self):
        self._top = []
        self._sync()

    def _flat(self):
        out = []

        def walk(it, depth):
            out.append((it, depth))
            for c in it._children:
                walk(c, depth + 1)
        for t in self._top:
            walk(t, 0)
        return out

    def _sync(self):
        flat = self._flat()
        cols = max([len(self._headers)] + [len(it._texts) for it, _ in flat] + [1])
        cells = {}
        for r, (it, depth) in enumerate(flat):
            for c in range(cols):
                t = it.text(c)
                if c == 0:
                    t = "   " * depth + ("▸ " if it._children else "") + t
                cells["%d,%d" % (r, c)] = {"t": t, "ro": True}
        self._cfg(rows=len(flat), cols=cols, cells=cells, hlabels=self._headers, vlabels=[])

    def _ui_event(self, ev):
        if ev.get("e") == "cell":
            flat = self._flat()
            r = int(ev.get("r", -1))
            if 0 <= r < len(flat):
                self.itemClicked.emit(flat[r][0], int(ev.get("c", 0)))


class QGroupBox(QWidget):
    _kind = "GroupBox"
    toggled = pyqtSignal(bool)
    clicked = pyqtSignal(bool)

    def __init__(self, *args, **kw):
        title, parent = "", None
        for a in args:
            if isinstance(a, str):
                title = a
            elif isinstance(a, QWidget):
                parent = a
        self._gtitle = title
        QWidget.__init__(self, parent, **kw)

    def _init_opts(self):
        return {"title": self._gtitle}

    def setTitle(self, t):
        self._gtitle = str(t)
        self._cfg(title=self._gtitle)

    def title(self):
        return self._gtitle

    def setCheckable(self, b):
        pass

    def setChecked(self, b):
        pass

    def isChecked(self):
        return True

    def setFlat(self, b):
        pass

    def setAlignment(self, a):
        pass


class QTabWidget(QWidget):
    _kind = "TabWidget"
    currentChanged = pyqtSignal(int)
    tabCloseRequested = pyqtSignal(int)
    North, South, West, East = 0, 1, 2, 3
    TabPosition = _enum("TabPosition", North=0, South=1, West=2, East=3)

    def __init__(self, parent=None, **kw):
        self._tabs = []
        self._index = -1
        QWidget.__init__(self, parent, **kw)

    def _sync(self):
        self._cfg(tabs=[[w._id, t] for w, t in self._tabs], index=self._index)

    def addTab(self, w, *args):
        label = args[-1] if args else ""
        if not isinstance(label, str):
            label = ""
        QObject.setParent(w, self)
        self._tabs.append((w, str(label)))
        if self._index < 0:
            self._index = 0
        self._sync()
        return len(self._tabs) - 1

    def insertTab(self, i, w, label):
        QObject.setParent(w, self)
        self._tabs.insert(i, (w, str(label)))
        if self._index < 0:
            self._index = 0
        self._sync()
        return i

    def removeTab(self, i):
        self._tabs.pop(i)
        if self._index >= len(self._tabs):
            self._index = len(self._tabs) - 1
        self._sync()

    def count(self):
        return len(self._tabs)

    def widget(self, i):
        return self._tabs[i][0] if 0 <= i < len(self._tabs) else None

    def indexOf(self, w):
        for i, (x, _) in enumerate(self._tabs):
            if x is w:
                return i
        return -1

    def currentIndex(self):
        return self._index

    def currentWidget(self):
        return self.widget(self._index)

    def setCurrentIndex(self, i):
        if i != self._index:
            self._index = i
            self._sync()
            self.currentChanged.emit(i)

    def setCurrentWidget(self, w):
        self.setCurrentIndex(self.indexOf(w))

    def setTabText(self, i, t):
        w, _ = self._tabs[i]
        self._tabs[i] = (w, str(t))
        self._sync()

    def tabText(self, i):
        return self._tabs[i][1]

    def setTabsClosable(self, b):
        pass

    def setMovable(self, b):
        pass

    def setTabPosition(self, p):
        pass

    def setDocumentMode(self, b):
        pass

    def setTabEnabled(self, i, b):
        pass

    def setTabToolTip(self, i, t):
        pass

    def tabBar(self):
        return _HeaderView()

    def clear(self):
        self._tabs = []
        self._index = -1
        self._sync()

    def _ui_event(self, ev):
        if ev.get("e") == "tab":
            self.setCurrentIndex(int(ev.get("v", 0)))


class QStackedWidget(QFrame):
    _kind = "Stacked"
    currentChanged = pyqtSignal(int)

    def __init__(self, parent=None, **kw):
        self._pages = []
        self._index = -1
        QFrame.__init__(self, parent, **kw)

    def _sync(self):
        self._cfg(pages=[w._id for w in self._pages], index=self._index)

    def addWidget(self, w):
        QObject.setParent(w, self)
        self._pages.append(w)
        if self._index < 0:
            self._index = 0
        self._sync()
        return len(self._pages) - 1

    insertWidget = lambda self, i, w: self.addWidget(w)  # noqa: E731

    def removeWidget(self, w):
        if w in self._pages:
            self._pages.remove(w)
            self._index = min(self._index, len(self._pages) - 1)
            self._sync()

    def count(self):
        return len(self._pages)

    def widget(self, i):
        return self._pages[i] if 0 <= i < len(self._pages) else None

    def indexOf(self, w):
        return self._pages.index(w) if w in self._pages else -1

    def currentIndex(self):
        return self._index

    def currentWidget(self):
        return self.widget(self._index)

    def setCurrentIndex(self, i):
        if i != self._index:
            self._index = i
            self._sync()
            self.currentChanged.emit(i)

    def setCurrentWidget(self, w):
        self.setCurrentIndex(self.indexOf(w))


class QScrollArea(QFrame):
    _kind = "ScrollArea"

    def __init__(self, parent=None, **kw):
        self._inner = None
        QFrame.__init__(self, parent, **kw)

    def setWidget(self, w):
        self._inner = w
        QObject.setParent(w, self)
        self._cfg(inner=w._id)

    def widget(self):
        return self._inner

    def setWidgetResizable(self, b):
        pass

    def setHorizontalScrollBarPolicy(self, p):
        pass

    def setVerticalScrollBarPolicy(self, p):
        pass

    def verticalScrollBar(self):
        return _ScrollBar(self)

    def horizontalScrollBar(self):
        return _ScrollBar(self)

    def ensureWidgetVisible(self, w):
        pass

    def setAlignment(self, a):
        pass


class QSplitter(QFrame):
    _kind = "Splitter"
    splitterMoved = pyqtSignal(int, int)

    def __init__(self, *args, **kw):
        orient, parent = Qt.Horizontal, None
        for a in args:
            if isinstance(a, QWidget):
                parent = a
            elif isinstance(a, int):
                orient = a
        self._orient = orient
        self._parts = []
        QFrame.__init__(self, parent, **kw)
        self._cfg(orient=orient)

    def addWidget(self, w):
        QObject.setParent(w, self)
        self._parts.append(w)
        self._cfg(parts=[p._id for p in self._parts])

    insertWidget = lambda self, i, w: self.addWidget(w)  # noqa: E731

    def setSizes(self, sizes):
        self._cfg(sizes=list(sizes))

    def sizes(self):
        return [100] * len(self._parts)

    def setStretchFactor(self, i, f):
        pass

    def setOrientation(self, o):
        self._cfg(orient=o)

    def setHandleWidth(self, w):
        pass

    def setChildrenCollapsible(self, b):
        pass

    def count(self):
        return len(self._parts)

    def widget(self, i):
        return self._parts[i]


class QDateEdit(QLineEdit):
    dateChanged = pyqtSignal(object)

    def __init__(self, *a, **kw):
        QLineEdit.__init__(self, *[x for x in a if isinstance(x, QWidget)], **kw)
        self._date = QDate()
        self.setText(self._date.toString())

    def date(self):
        return self._date

    def setDate(self, d):
        self._date = d
        self.setText(d.toString())

    def setCalendarPopup(self, b):
        pass

    def setDisplayFormat(self, f):
        pass


class QTimeEdit(QLineEdit):
    timeChanged = pyqtSignal(object)

    def time(self):
        return QTime()

    def setTime(self, t):
        self.setText(t.toString())

    def setDisplayFormat(self, f):
        pass


class QLCDNumber(QLabel):
    def __init__(self, *args, **kw):
        parent = next((a for a in args if isinstance(a, QWidget)), None)
        QLabel.__init__(self, "0", parent, **kw)
        self._cfg(lcd=True)

    def display(self, v):
        self.setText(str(v))

    def setDigitCount(self, n):
        pass

    def setSegmentStyle(self, s):
        pass

    def value(self):
        try:
            return float(self._text)
        except ValueError:
            return 0.0


# ------------------------------------------------------------- Aktionen/Menues
class QAction(QObject):
    triggered = pyqtSignal(bool)
    toggled = pyqtSignal(bool)
    hovered = pyqtSignal()

    def __init__(self, *args, **kw):
        text, parent, icon = "", None, None
        for a in args:
            if isinstance(a, str):
                text = a
            elif isinstance(a, QIcon):
                icon = a
            elif isinstance(a, QObject):
                parent = a
        self._text = text
        self._checkable = False
        self._checked = False
        self._enabled = True
        self._shortcut = ""
        self._data = None
        self._sep = False
        self._menu = None
        self._aid = _g.new_id("act")
        QObject.__init__(self, parent, **kw)
        _g.register(self._aid, self)

    def text(self):
        return self._text

    def setText(self, t):
        self._text = str(t)
        self._changed()

    def setCheckable(self, b):
        self._checkable = bool(b)
        self._changed()

    def isCheckable(self):
        return self._checkable

    def setChecked(self, b):
        if bool(b) != self._checked:
            self._checked = bool(b)
            self.toggled.emit(self._checked)
            self._changed()

    def isChecked(self):
        return self._checked

    def setEnabled(self, b):
        self._enabled = bool(b)
        self._changed()

    def isEnabled(self):
        return self._enabled

    def setShortcut(self, s):
        self._shortcut = s.toString() if isinstance(s, QKeySequence) else str(s)
        self._changed()

    def setShortcuts(self, s):
        pass

    def setStatusTip(self, t):
        pass

    def setToolTip(self, t):
        pass

    def setIcon(self, i):
        pass

    def setData(self, d):
        self._data = d

    def data(self):
        return self._data

    def setSeparator(self, b):
        self._sep = bool(b)

    def setMenu(self, m):
        self._menu = m

    def menu(self):
        return self._menu

    def setVisible(self, b):
        pass

    def setShortcutContext(self, c):
        pass

    def trigger(self):
        if not self._enabled:
            return
        if self._checkable:
            self.setChecked(not self._checked)
        self.triggered.emit(self._checked)

    def _changed(self):
        for m in _MENUS:
            if self in m._actions:
                _g.mark_dirty(m)

    def _spec(self):
        if self._sep:
            return {"sep": True}
        d = {"id": self._aid, "text": self._text.replace("&", ""), "enabled": self._enabled,
             "checkable": self._checkable, "checked": self._checked, "shortcut": self._shortcut}
        if self._menu is not None:
            d["sub"] = [a._spec() for a in self._menu._actions]
        return d

    def _pyide_event(self, ev):
        self.trigger()


class QActionGroup(QObject):
    triggered = pyqtSignal(object)

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._acts = []

    def addAction(self, a):
        self._acts.append(a)
        a.triggered.connect(lambda *x, a=a: self._on(a))
        return a

    def _on(self, a):
        for o in self._acts:
            if o is not a and o._checked:
                o._checked = False
                o._changed()
        if not a._checked:
            a._checked = True
            a._changed()
        self.triggered.emit(a)

    def setExclusive(self, b):
        pass

    def checkedAction(self):
        for a in self._acts:
            if a._checked:
                return a
        return None


_MENUS = []


class QMenu(QWidget):
    _kind = "Menu"
    triggered = pyqtSignal(object)
    aboutToShow = pyqtSignal()

    def __init__(self, *args, **kw):
        title, parent = "", None
        for a in args:
            if isinstance(a, str):
                title = a
            elif isinstance(a, QWidget):
                parent = a
        self._mtitle = title
        self._actions = []
        QWidget.__init__(self, parent, **kw)
        _MENUS.append(self)

    def title(self):
        return self._mtitle

    def setTitle(self, t):
        self._mtitle = str(t)
        _g.mark_dirty(self)

    def addAction(self, *args, **kw):
        if args and isinstance(args[0], QAction):
            act = args[0]
        else:
            text = next((a for a in args if isinstance(a, str)), "")
            act = QAction(text, self)
            for a in args:
                if callable(a) and not isinstance(a, (str, QIcon)):
                    act.triggered.connect(a)
                elif isinstance(a, (QKeySequence,)):
                    act.setShortcut(a)
            if "triggered" in kw:
                act.triggered.connect(kw["triggered"])
        act.triggered.connect(lambda *x, act=act: self.triggered.emit(act))
        self._actions.append(act)
        _g.mark_dirty(self)
        return act

    def addActions(self, acts):
        for a in acts:
            self.addAction(a)

    def addMenu(self, m):
        if isinstance(m, str):
            m = QMenu(m, self)
        act = QAction(m._mtitle, self)
        act._menu = m
        self._actions.append(act)
        _g.mark_dirty(self)
        return m

    def addSeparator(self):
        a = QAction("", self)
        a._sep = True
        self._actions.append(a)
        _g.mark_dirty(self)
        return a

    def clear(self):
        self._actions = []
        _g.mark_dirty(self)

    def actions(self):
        return list(self._actions)

    def menuAction(self):
        a = QAction(self._mtitle)
        a._menu = self
        return a

    def _pyide_sync(self):
        _g.op("qt_menu", self._id, self._mtitle.replace("&", ""), [a._spec() for a in self._actions])
        for b in _MENUBARS:
            if self in b._menus:
                _g.mark_dirty(b)

    def exec(self, pos=None, *a):
        self.aboutToShow.emit()
        p = pos or QPoint(0, 0)
        _g.flush()
        res = _g.sync_call("menu", {"items": [x._spec() for x in self._actions], "x": p.x(), "y": p.y()})
        if res:
            obj = _g._S.objects.get(res)
            if isinstance(obj, QAction):
                obj.trigger()
                return obj
        return None

    exec_ = popup = exec


_MENUBARS = []


class QMenuBar(QWidget):
    _kind = "MenuBar"
    triggered = pyqtSignal(object)

    def __init__(self, parent=None):
        self._menus = []
        self._loose = []
        QWidget.__init__(self, parent)
        _MENUBARS.append(self)

    def addMenu(self, m):
        if isinstance(m, str):
            m = QMenu(m, self)
        self._menus.append(m)
        _g.mark_dirty(self)
        return m

    def addAction(self, *args):
        act = args[0] if args and isinstance(args[0], QAction) else QAction(
            next((a for a in args if isinstance(a, str)), ""), self)
        for a in args:
            if callable(a) and not isinstance(a, (str, QAction)):
                act.triggered.connect(a)
        m = QMenu(act.text(), self)
        m._direct = act
        self._menus.append(m)
        _g.mark_dirty(self)
        return act

    def clear(self):
        self._menus = []
        _g.mark_dirty(self)

    def setNativeMenuBar(self, b):
        pass

    def _pyide_sync(self):
        menus = []
        for m in self._menus:
            d = getattr(m, "_direct", None)
            if d is not None:
                menus.append({"title": d.text().replace("&", ""), "direct": d._aid})
            else:
                menus.append({"title": m._mtitle.replace("&", ""), "items": [a._spec() for a in m._actions]})
        _g.op("qt_menubar", self._id, menus)


class QStatusBar(QWidget):
    _kind = "StatusBar"
    messageChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        self._msg = ""
        self._tid = None
        QWidget.__init__(self, parent)

    def showMessage(self, text, timeout=0):
        self._msg = str(text)
        self._cfg(text=self._msg)
        self.messageChanged.emit(self._msg)
        if self._tid:
            _g.cancel_timer(self._tid)
        if timeout:
            self._tid = _g.add_timer(timeout, self.clearMessage)

    def clearMessage(self):
        self._msg = ""
        self._cfg(text="")

    def currentMessage(self):
        return self._msg

    def addWidget(self, w, stretch=0):
        QObject.setParent(w, self)
        _g.op("qt_status_add", self._id, w._id, False)

    def addPermanentWidget(self, w, stretch=0):
        QObject.setParent(w, self)
        _g.op("qt_status_add", self._id, w._id, True)

    def removeWidget(self, w):
        pass

    def setSizeGripEnabled(self, b):
        pass


class QToolBar(QWidget):
    _kind = "ToolBar"
    actionTriggered = pyqtSignal(object)

    def __init__(self, *args, **kw):
        parent = next((a for a in args if isinstance(a, QWidget)), None)
        QWidget.__init__(self, parent)

    def addAction(self, *args):
        act = args[0] if args and isinstance(args[0], QAction) else QAction(
            next((a for a in args if isinstance(a, str)), ""), self)
        for a in args:
            if callable(a) and not isinstance(a, (str, QAction, QIcon)):
                act.triggered.connect(a)
        b = QPushButton(act.text().replace("&", ""), self)
        b.clicked.connect(lambda *x: act.trigger())
        _g.op("qt_tool_add", self._id, b._id)
        return act

    def addWidget(self, w):
        QObject.setParent(w, self)
        _g.op("qt_tool_add", self._id, w._id)

    def addSeparator(self):
        pass

    def setMovable(self, b):
        pass

    def setIconSize(self, s):
        pass

    def setToolButtonStyle(self, s):
        pass

    def setFloatable(self, b):
        pass

    def setOrientation(self, o):
        pass


class QMainWindow(QWidget):
    _kind = "MainWindow"

    def __init__(self, parent=None, *a, **kw):
        QWidget.__init__(self, parent, **kw)
        self._central = None
        self._menubar = None
        self._statusbar = None
        self._is_window = parent is None or self._is_window

    def setCentralWidget(self, w):
        self._central = w
        QObject.setParent(w, self)
        _g.op("qt_central", self._id, w._id)

    def centralWidget(self):
        return self._central

    def menuBar(self):
        if self._menubar is None:
            self._menubar = QMenuBar(self)
            _g.op("qt_setmenubar", self._id, self._menubar._id)
        return self._menubar

    def setMenuBar(self, mb):
        self._menubar = mb
        QObject.setParent(mb, self)
        _g.op("qt_setmenubar", self._id, mb._id)

    def statusBar(self):
        if self._statusbar is None:
            self._statusbar = QStatusBar(self)
            _g.op("qt_setstatusbar", self._id, self._statusbar._id)
        return self._statusbar

    def setStatusBar(self, sb):
        self._statusbar = sb
        QObject.setParent(sb, self)
        _g.op("qt_setstatusbar", self._id, sb._id)

    def addToolBar(self, *args):
        tb = args[-1]
        if isinstance(tb, str):
            tb = QToolBar(tb, self)
        QObject.setParent(tb, self)
        _g.op("qt_addtoolbar", self._id, tb._id)
        return tb

    def addDockWidget(self, area, dock, *a):
        QObject.setParent(dock, self)
        _g.op("qt_addtoolbar", self._id, dock._id)

    def setUnifiedTitleAndToolBarOnMac(self, b):
        pass

    def setDockOptions(self, o):
        pass


class QDockWidget(QWidget):
    _kind = "GroupBox"

    def __init__(self, title="", parent=None, *a):
        self._gtitle = title if isinstance(title, str) else ""
        if isinstance(title, QWidget):
            parent = title
        QWidget.__init__(self, parent)

    def _init_opts(self):
        return {"title": self._gtitle}

    def setWidget(self, w):
        lay = QVBoxLayout()
        lay.addWidget(w)
        self.setLayout(lay)

    def setFeatures(self, f):
        pass

    def setAllowedAreas(self, a):
        pass


# ------------------------------------------------------------------ Dialoge
class QDialog(QWidget):
    _kind = "Widget"
    accepted = pyqtSignal()
    rejected = pyqtSignal()
    finished = pyqtSignal(int)
    Accepted, Rejected = 1, 0
    DialogCode = _enum("DialogCode", Accepted=1, Rejected=0)

    def __init__(self, parent=None, *a, **kw):
        QWidget.__init__(self, parent, **kw)
        self._is_window = True
        self._result = 0
        self._done = False

    def exec(self):
        self._done = False
        self._modal = True
        self.show()
        _g.run_loop(lambda: self._done or not self.isVisible())
        if not self._done:
            self._result = 0
        self.close()
        return self._result

    exec_ = exec

    def open(self):
        self.show()

    def done(self, r):
        self._result = r
        self._done = True
        self.finished.emit(r)
        self.hide()
        _g._S.toplevels.pop(self._id, None)
        _g.op("qt_close", self._id)

    def accept(self):
        self.done(1)
        self.accepted.emit()

    def reject(self):
        self.done(0)
        self.rejected.emit()

    def result(self):
        return self._result

    def setModal(self, b):
        self._modal = bool(b)

    def setSizeGripEnabled(self, b):
        pass


class QDialogButtonBox(QWidget):
    _kind = "Widget"
    accepted = pyqtSignal()
    rejected = pyqtSignal()
    clicked = pyqtSignal(object)
    Ok, Cancel, Yes, No, Save, Close, Apply, Reset, Help, Discard = (0x400, 0x400000, 0x4000, 0x10000, 0x800,
                                                                      0x200000, 0x2000000, 0x4000000,
                                                                      0x1000000, 0x800000)
    StandardButton = _enum("StandardButton", Ok=0x400, Cancel=0x400000, Yes=0x4000, No=0x10000, Save=0x800,
                           Close=0x200000, Apply=0x2000000, Reset=0x4000000, Help=0x1000000,
                           Discard=0x800000)
    _LABELS = {0x400: "OK", 0x400000: "Abbrechen", 0x4000: "Ja", 0x10000: "Nein", 0x800: "Speichern",
               0x200000: "Schließen", 0x2000000: "Anwenden", 0x4000000: "Zurücksetzen", 0x1000000: "Hilfe",
               0x800000: "Verwerfen"}
    _ACCEPT = {0x400, 0x4000, 0x800, 0x2000000}

    def __init__(self, *args, **kw):
        buttons, parent = 0, None
        for a in args:
            if isinstance(a, QWidget):
                parent = a
            elif isinstance(a, int):
                buttons = a
        QWidget.__init__(self, parent, **kw)
        lay = QHBoxLayout()
        lay.addStretch()
        self.setLayout(lay)
        self._lay = lay
        self._btns = {}
        if buttons:
            self.setStandardButtons(buttons)

    def setStandardButtons(self, buttons):
        for code, label in self._LABELS.items():
            if buttons & code:
                b = QPushButton(label)
                self._btns[code] = b
                self._lay.addWidget(b)
                b.clicked.connect(lambda *x, code=code, b=b: self._on(code, b))

    def addButton(self, b, role=None):
        if isinstance(b, str):
            b = QPushButton(b)
        self._lay.addWidget(b)
        b.clicked.connect(lambda *x, b=b: self.clicked.emit(b))
        return b

    def button(self, code):
        return self._btns.get(code)

    def _on(self, code, b):
        self.clicked.emit(b)
        if code in self._ACCEPT:
            self.accepted.emit()
        elif code in (0x400000, 0x200000, 0x10000, 0x800000):
            self.rejected.emit()


class QMessageBox(QDialog):
    NoButton, Ok, Save, SaveAll, Open, Yes, YesToAll, No, NoToAll, Abort, Retry, Ignore, Close, Cancel, \
        Discard, Help, Apply, Reset = (0, 0x400, 0x800, 0x1000, 0x2000, 0x4000, 0x8000, 0x10000, 0x20000,
                                       0x40000, 0x80000, 0x100000, 0x200000, 0x400000, 0x800000, 0x1000000,
                                       0x2000000, 0x4000000)
    StandardButton = _enum("StandardButton", NoButton=0, Ok=0x400, Save=0x800, Open=0x2000, Yes=0x4000,
                           No=0x10000, Abort=0x40000, Retry=0x80000, Ignore=0x100000, Close=0x200000,
                           Cancel=0x400000, Discard=0x800000, Help=0x1000000, Apply=0x2000000)
    NoIcon, Information, Warning, Critical, Question = 0, 1, 2, 3, 4
    Icon = _enum("Icon", NoIcon=0, Information=1, Warning=2, Critical=3, Question=4)
    AcceptRole, RejectRole, YesRole, NoRole, ActionRole = 0, 1, 5, 6, 3
    ButtonRole = _enum("ButtonRole", AcceptRole=0, RejectRole=1, YesRole=5, NoRole=6, ActionRole=3)
    _LABELS = {0x400: "OK", 0x800: "Speichern", 0x1000: "Alle speichern", 0x2000: "Öffnen", 0x4000: "Ja",
               0x8000: "Ja für alle", 0x10000: "Nein", 0x20000: "Nein für alle", 0x40000: "Abbrechen",
               0x80000: "Wiederholen", 0x100000: "Ignorieren", 0x200000: "Schließen", 0x400000: "Abbrechen",
               0x800000: "Verwerfen", 0x1000000: "Hilfe", 0x2000000: "Anwenden", 0x4000000: "Zurücksetzen"}

    def __init__(self, *args, **kw):
        parent = next((a for a in args if isinstance(a, QWidget)), None)
        QDialog.__init__(self, parent)
        self._icon = 0
        self._mtitle = ""
        self._text = ""
        self._info = ""
        self._detail = ""
        self._buttons = 0x400
        self._custom = []
        self._clicked = None
        strs = [a for a in args if isinstance(a, str)]
        ints = [a for a in args if isinstance(a, int) and not isinstance(a, bool)]
        if ints:
            self._icon = ints[0]
            if len(ints) > 1:
                self._buttons = ints[1]
        if strs:
            self._mtitle = strs[0]
            if len(strs) > 1:
                self._text = strs[1]

    def setIcon(self, i):
        self._icon = int(i)

    def setText(self, t):
        self._text = str(t)

    def text(self):
        return self._text

    def setInformativeText(self, t):
        self._info = str(t)

    def setDetailedText(self, t):
        self._detail = str(t)

    def setWindowTitle(self, t):
        self._mtitle = str(t)

    def setStandardButtons(self, b):
        self._buttons = int(b)

    def setDefaultButton(self, b):
        pass

    def setEscapeButton(self, b):
        pass

    def setTextFormat(self, f):
        pass

    def addButton(self, b, role=0):
        if isinstance(b, int):
            self._buttons |= b
            return None
        if isinstance(b, str):
            b = QPushButton(b)
        self._custom.append(b)
        return b

    def clickedButton(self):
        return self._clicked

    def exec(self):
        labels, codes = [], []
        for code in sorted(self._LABELS):
            if self._buttons & code:
                labels.append(self._LABELS[code])
                codes.append(code)
        for b in self._custom:
            labels.append(b.text())
            codes.append(b)
        icon = {1: "info", 2: "warning", 3: "error", 4: "question"}.get(self._icon, "info")
        res = _g.sync_call("dialog", {"type": "message", "title": self._mtitle, "message": self._text,
                                      "detail": "\n\n".join(x for x in (self._info, self._detail) if x),
                                      "icon": icon, "buttons": labels})
        if res is None:
            _g.op("dialog_async", {"type": "message", "title": self._mtitle, "message": self._text,
                                   "icon": icon, "buttons": labels[:1] or ["OK"]})
            return codes[0] if codes and isinstance(codes[0], int) else 0x400
        try:
            pick = codes[labels.index(res)]
        except ValueError:
            pick = codes[-1] if codes else 0
        if not isinstance(pick, int):
            self._clicked = pick
            pick.clicked.emit(False)
            return self._custom.index(pick)
        self._clicked = None
        return pick

    exec_ = exec

    @staticmethod
    def _static(icon, parent, title, text, buttons, default):
        m = QMessageBox(parent)
        m._icon, m._mtitle, m._text, m._buttons = icon, str(title), str(text), int(buttons)
        return m.exec()

    @staticmethod
    def information(parent, title, text, buttons=0x400, default=0):
        return QMessageBox._static(1, parent, title, text, buttons, default)

    @staticmethod
    def warning(parent, title, text, buttons=0x400, default=0):
        return QMessageBox._static(2, parent, title, text, buttons, default)

    @staticmethod
    def critical(parent, title, text, buttons=0x400, default=0):
        return QMessageBox._static(3, parent, title, text, buttons, default)

    @staticmethod
    def question(parent, title, text, buttons=0x4000 | 0x10000, default=0):
        return QMessageBox._static(4, parent, title, text, buttons, default)

    @staticmethod
    def about(parent, title, text):
        QMessageBox._static(1, parent, title, text, 0x400, 0)

    @staticmethod
    def aboutQt(parent, title=""):
        QMessageBox._static(1, parent, "Über Qt", "PyIDE Qt-Nachbau (kein echtes Qt)", 0x400, 0)


class QInputDialog(QDialog):
    @staticmethod
    def _ask(kind, title, label, initial, mn=None, mx=None, items=None, echo=0):
        res = _g.sync_call("dialog", {"type": "input", "kind": kind, "title": str(title), "prompt": str(label),
                                      "initial": "" if initial is None else str(initial), "min": mn, "max": mx,
                                      "items": items, "show": "*" if echo == 2 else None})
        return res

    @staticmethod
    def getText(parent, title, label, echo=0, text="", *a, **kw):
        if isinstance(echo, str):
            text, echo = echo, 0
        res = QInputDialog._ask("string", title, label, kw.get("text", text), echo=echo)
        return (str(res), True) if res is not None else ("", False)

    @staticmethod
    def getMultiLineText(parent, title, label, text="", *a):
        res = QInputDialog._ask("string", title, label, text)
        return (str(res), True) if res is not None else ("", False)

    @staticmethod
    def getInt(parent, title, label, value=0, min=-2147483647, max=2147483647, step=1, *a, **kw):
        while True:
            res = QInputDialog._ask("int", title, label, kw.get("value", value), min, max)
            if res is None:
                return (int(value), False)
            try:
                v = int(float(res))
            except ValueError:
                continue
            if min <= v <= max:
                return (v, True)

    @staticmethod
    def getDouble(parent, title, label, value=0.0, min=-2147483647.0, max=2147483647.0, decimals=1, *a, **kw):
        while True:
            res = QInputDialog._ask("float", title, label, kw.get("value", value), min, max)
            if res is None:
                return (float(value), False)
            try:
                v = float(res)
            except ValueError:
                continue
            if min <= v <= max:
                return (round(v, decimals), True)

    @staticmethod
    def getItem(parent, title, label, items, current=0, editable=True, *a, **kw):
        items = [str(i) for i in items]
        res = QInputDialog._ask("item", title, label, items[current] if items else "", items=items)
        return (str(res), True) if res is not None else (items[current] if items else "", False)


class QFileDialog(QDialog):
    @staticmethod
    def _types(filt):
        out = []
        for part in str(filt or "").split(";;"):
            part = part.strip()
            if not part:
                continue
            import re
            m = re.match(r"(.*)\((.*)\)", part)
            if m:
                out.append([m.group(1).strip(), m.group(2).split()])
        return out

    @staticmethod
    def _ask(mode, caption, directory, filt):
        import os
        res = _g.sync_call("dialog", {"type": "file", "mode": mode, "title": str(caption or ""),
                                      "filetypes": QFileDialog._types(filt), "initialfile": "",
                                      "cwd": os.getcwd(), "initialdir": str(directory or "")})
        if not res:
            return None
        if mode == "openmany":
            return [os.path.join(os.getcwd(), p) for p in res]
        return os.path.join(os.getcwd(), res)

    @staticmethod
    def getOpenFileName(parent=None, caption="", directory="", filter="", *a, **kw):
        p = QFileDialog._ask("open", caption, directory, kw.get("filter", filter))
        return (p or "", filter if p else "")

    @staticmethod
    def getOpenFileNames(parent=None, caption="", directory="", filter="", *a, **kw):
        p = QFileDialog._ask("openmany", caption, directory, filter)
        return (p or [], filter if p else "")

    @staticmethod
    def getSaveFileName(parent=None, caption="", directory="", filter="", *a, **kw):
        p = QFileDialog._ask("save", caption, directory, filter)
        return (p or "", filter if p else "")

    @staticmethod
    def getExistingDirectory(parent=None, caption="", directory="", *a, **kw):
        p = QFileDialog._ask("dir", caption, directory, "")
        if p:
            import os
            os.makedirs(p, exist_ok=True)
        return p or ""


class QColorDialog(QDialog):
    @staticmethod
    def getColor(initial=None, parent=None, title="", *a):
        init = _css_color(initial) if initial is not None else "#3366cc"
        res = _g.sync_call("dialog", {"type": "color", "title": str(title or "Farbe wählen"), "initial": init})
        c = QColor(res) if res else QColor()
        c._valid = bool(res)
        c.isValid = lambda: bool(res)
        return c


class QFontDialog(QDialog):
    @staticmethod
    def getFont(initial=None, *a):
        return (initial or QFont(), False)


class QProgressDialog(QDialog):
    canceled = pyqtSignal()

    def __init__(self, label="", cancel="", mn=0, mx=100, parent=None, *a):
        QDialog.__init__(self, parent if isinstance(parent, QWidget) else None)
        lay = QVBoxLayout()
        self._label = QLabel(label)
        self._bar = QProgressBar()
        self._bar.setRange(mn, mx)
        lay.addWidget(self._label)
        lay.addWidget(self._bar)
        self.setLayout(lay)

    def setValue(self, v):
        self._bar.setValue(v)
        if not self.isVisible():
            self.show()
        _g.update()

    def value(self):
        return self._bar.value()

    def setLabelText(self, t):
        self._label.setText(t)

    def setMinimumDuration(self, ms):
        pass

    def setWindowModality(self, m):
        pass

    def wasCanceled(self):
        return False

    def setAutoClose(self, b):
        pass

    def setRange(self, a, b):
        self._bar.setRange(a, b)

    def setMaximum(self, m):
        self._bar.setMaximum(m)


class QShortcut(QObject):
    activated = pyqtSignal()

    def __init__(self, key=None, parent=None, *a):
        QObject.__init__(self, parent)


class QSystemTrayIcon(QObject):
    @staticmethod
    def isSystemTrayAvailable():
        return False


class QSpacerItem:
    def __init__(self, w=0, h=0, hp=5, vp=5):
        self._w, self._h, self._hp, self._vp = w, h, hp, vp


# ------------------------------------------------------------------ Layouts
class QLayout(QObject):
    _kind = "VBox"
    SetFixedSize, SetDefaultConstraint, SetMinimumSize, SetNoConstraint = 3, 0, 2, 1
    SizeConstraint = _enum("SizeConstraint", SetFixedSize=3, SetDefaultConstraint=0, SetMinimumSize=2)

    def __init__(self, parent=None):
        QObject.__init__(self, None)
        self._id = _g.new_id("l")
        self._items = []
        self._owner = None
        _g.op("qt_layout", self._id, self._kind)
        if isinstance(parent, QWidget):
            parent.setLayout(self)

    def _adopt(self, owner):
        self._owner = owner
        for kind, obj, _ in self._items:
            if kind == "w":
                if obj._parent is not owner:
                    QObject.setParent(obj, owner)
            elif kind == "l":
                obj._adopt(owner)

    def _add(self, kind, obj, opts):
        self._items.append((kind, obj, opts))
        if kind == "w":
            if self._owner is not None:
                QObject.setParent(obj, self._owner)
            _g.op("qt_ladd", self._id, "w", obj._id, opts)
            if obj._visible is None:
                obj._paint_pending = True
                _g.mark_dirty(obj)
        elif kind == "l":
            if self._owner is not None:
                obj._adopt(self._owner)
            _g.op("qt_ladd", self._id, "l", obj._id, opts)
        else:
            _g.op("qt_ladd", self._id, kind, None, opts)

    def addWidget(self, w, *args, **kw):
        stretch = args[0] if args and isinstance(args[0], int) else kw.get("stretch", 0)
        align = args[1] if len(args) > 1 else kw.get("alignment", 0)
        self._add("w", w, {"stretch": stretch, "align": int(align or 0)})

    def addLayout(self, l, stretch=0):
        self._add("l", l, {"stretch": stretch})

    def addItem(self, item):
        if isinstance(item, QSpacerItem):
            self._add("stretch", None, {"stretch": 1 if item._hp == 7 or item._vp == 7 else 0,
                                        "size": max(item._w, item._h)})

    def addSpacerItem(self, item):
        self.addItem(item)

    def addStretch(self, stretch=0):
        self._add("stretch", None, {"stretch": stretch or 1})

    def addSpacing(self, size):
        self._add("space", None, {"size": size})

    def insertWidget(self, index, w, stretch=0, alignment=0):
        self._items.insert(index, ("w", w, {"stretch": stretch}))
        if self._owner is not None:
            QObject.setParent(w, self._owner)
        _g.op("qt_ladd", self._id, "w", w._id, {"stretch": stretch, "index": index, "align": int(alignment or 0)})

    def insertLayout(self, index, l, stretch=0):
        self._items.insert(index, ("l", l, {"stretch": stretch}))
        _g.op("qt_ladd", self._id, "l", l._id, {"stretch": stretch, "index": index})

    def insertStretch(self, index, stretch=0):
        _g.op("qt_ladd", self._id, "stretch", None, {"stretch": stretch or 1, "index": index})

    def insertSpacing(self, index, size):
        _g.op("qt_ladd", self._id, "space", None, {"size": size, "index": index})

    def removeWidget(self, w):
        self._items = [i for i in self._items if i[1] is not w]
        _g.op("qt_lremove", self._id, w._id)

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        if 0 <= i < len(self._items):
            return _LayoutItem(self._items[i])
        return None

    def takeAt(self, i):
        if 0 <= i < len(self._items):
            it = self._items.pop(i)
            if it[0] == "w":
                _g.op("qt_lremove", self._id, it[1]._id)
            return _LayoutItem(it)
        return None

    def setSpacing(self, s):
        _g.op("qt_lcfg", self._id, {"spacing": s})

    def spacing(self):
        return 6

    def setContentsMargins(self, *a):
        if len(a) == 1 and isinstance(a[0], QMargins):
            a = a[0].m
        _g.op("qt_lcfg", self._id, {"margins": list(a)})

    def setAlignment(self, *a):
        if len(a) == 1:
            _g.op("qt_lcfg", self._id, {"align": int(a[0])})

    def setSizeConstraint(self, c):
        pass

    def setStretch(self, i, s):
        pass

    def setStretchFactor(self, w, s):
        pass

    def parentWidget(self):
        return self._owner

    def setDirection(self, d):
        pass

    def update(self):
        pass

    def activate(self):
        return True


class _LayoutItem:
    def __init__(self, item):
        self._it = item

    def widget(self):
        return self._it[1] if self._it[0] == "w" else None

    def layout(self):
        return self._it[1] if self._it[0] == "l" else None

    def spacerItem(self):
        return None


class QBoxLayout(QLayout):
    LeftToRight, RightToLeft, TopToBottom, BottomToTop = 0, 1, 2, 3
    Direction = _enum("Direction", LeftToRight=0, RightToLeft=1, TopToBottom=2, BottomToTop=3)

    def __init__(self, direction=2, parent=None):
        if isinstance(direction, QWidget):
            direction, parent = 2, direction
        self._kind = "HBox" if direction in (0, 1) else "VBox"
        QLayout.__init__(self, parent)


class QVBoxLayout(QBoxLayout):
    def __init__(self, parent=None):
        QBoxLayout.__init__(self, 2, parent)


class QHBoxLayout(QBoxLayout):
    def __init__(self, parent=None):
        QBoxLayout.__init__(self, 0, parent)


class QGridLayout(QLayout):
    _kind = "Grid"

    def addWidget(self, w, row=None, col=0, rowspan=1, colspan=1, alignment=0, **kw):
        if row is None:
            row = len(self._items)
        if not isinstance(rowspan, int) or isinstance(rowspan, bool):
            rowspan = 1
        if colspan and not isinstance(colspan, int):
            alignment, colspan = colspan, 1
        if rowspan and isinstance(rowspan, int) and rowspan > 0x10 and colspan == 1:
            alignment, rowspan = rowspan, 1
        self._add("w", w, {"row": row, "col": col, "rowspan": rowspan, "colspan": colspan,
                           "align": int(alignment or 0)})

    def addLayout(self, l, row=0, col=0, rowspan=1, colspan=1, alignment=0):
        self._add("l", l, {"row": row, "col": col, "rowspan": rowspan, "colspan": colspan})

    def setColumnStretch(self, c, s):
        _g.op("qt_lcfg", self._id, {"colstretch": [c, s]})

    def setRowStretch(self, r, s):
        _g.op("qt_lcfg", self._id, {"rowstretch": [r, s]})

    def setColumnMinimumWidth(self, c, w):
        _g.op("qt_lcfg", self._id, {"colmin": [c, w]})

    def setRowMinimumHeight(self, r, h):
        pass

    def setHorizontalSpacing(self, s):
        _g.op("qt_lcfg", self._id, {"hspacing": s})

    def setVerticalSpacing(self, s):
        _g.op("qt_lcfg", self._id, {"vspacing": s})

    def rowCount(self):
        return max([o.get("row", 0) + o.get("rowspan", 1) for _, _, o in self._items] + [0])

    def columnCount(self):
        return max([o.get("col", 0) + o.get("colspan", 1) for _, _, o in self._items] + [0])

    def itemAtPosition(self, r, c):
        for it in self._items:
            if it[2].get("row") == r and it[2].get("col") == c:
                return _LayoutItem(it)
        return None


class QFormLayout(QGridLayout):
    _kind = "Form"
    LabelRole, FieldRole, SpanningRole = 0, 1, 2
    ItemRole = _enum("ItemRole", LabelRole=0, FieldRole=1, SpanningRole=2)

    def __init__(self, parent=None):
        self._row = 0
        QGridLayout.__init__(self, parent)

    def addRow(self, *args):
        if len(args) == 1:
            a = args[0]
            if isinstance(a, QLayout):
                QGridLayout.addLayout(self, a, self._row, 0, 1, 2)
            else:
                QGridLayout.addWidget(self, a, self._row, 0, 1, 2)
        else:
            label, field = args[0], args[1]
            if isinstance(label, str):
                label = QLabel(label)
            QGridLayout.addWidget(self, label, self._row, 0)
            if isinstance(field, QLayout):
                QGridLayout.addLayout(self, field, self._row, 1)
            else:
                QGridLayout.addWidget(self, field, self._row, 1)
        self._row += 1

    def insertRow(self, row, *args):
        self.addRow(*args)

    def setLabelAlignment(self, a):
        pass

    def setFormAlignment(self, a):
        pass

    def setFieldGrowthPolicy(self, p):
        pass

    def setRowWrapPolicy(self, p):
        pass

    def rowCount(self):
        return self._row


QStackedLayout = QVBoxLayout


# ------------------------------------------------------------------ QPainter
class _PaintTarget:
    stack = []


class QPainter:
    Antialiasing, TextAntialiasing, SmoothPixmapTransform, HighQualityAntialiasing = 1, 2, 4, 8
    RenderHint = _enum("RenderHint", Antialiasing=1, TextAntialiasing=2, SmoothPixmapTransform=4)
    CompositionMode = _enum("CompositionMode", CompositionMode_SourceOver=0)

    def __init__(self, device=None):
        self._cmds = None
        self._pen = QPen()
        self._brush = None
        self._font = None
        self._active = False
        if device is not None:
            self.begin(device)

    def begin(self, device):
        if _PaintTarget.stack:
            self._cmds = _PaintTarget.stack[-1]
        else:
            self._cmds = []
            if isinstance(device, QWidget):
                device._paint_pending = True
                _g.mark_dirty(device)
        self._active = True
        self._cmds.append(["reset"])
        self._cmds.append(["pen", self._pen._spec()])
        self._cmds.append(["brush", None])
        return True

    def end(self):
        self._active = False
        return True

    def isActive(self):
        return self._active

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.end()

    def _c(self, *a):
        if self._cmds is not None:
            self._cmds.append(list(a))

    def setRenderHint(self, *a):
        pass

    setRenderHints = setRenderHint

    def setPen(self, p):
        if isinstance(p, QPen):
            self._pen = p
        elif isinstance(p, int) and not isinstance(p, _GlobalColor) and p == 0:
            self._pen = QPen(Qt.NoPen)
        else:
            self._pen = QPen(p)
        self._c("pen", self._pen._spec())

    def pen(self):
        return self._pen

    def setBrush(self, b):
        if isinstance(b, QBrush):
            self._brush = b._css()
        elif isinstance(b, int) and not isinstance(b, _GlobalColor) and b == 0:
            self._brush = None
        elif b is None:
            self._brush = None
        else:
            self._brush = _css_color(b)
        self._c("brush", self._brush)

    def brush(self):
        return QBrush(self._brush) if self._brush else QBrush(Qt.NoBrush)

    def setFont(self, f):
        self._font = f
        self._c("font", f._spec())

    def font(self):
        return self._font or QFont()

    def fontMetrics(self):
        return QFontMetrics(self.font())

    def setOpacity(self, o):
        self._c("alpha", float(o))

    def save(self):
        self._c("save")

    def restore(self):
        self._c("restore")

    def translate(self, *a):
        if isinstance(a[0], QPoint):
            a = (a[0].x(), a[0].y())
        self._c("translate", a[0], a[1])

    def rotate(self, deg):
        self._c("rotate", deg)

    def scale(self, sx, sy):
        self._c("scale", sx, sy)

    def resetTransform(self):
        self._c("identity")

    def setClipRect(self, *a):
        r = a[0] if isinstance(a[0], QRect) else QRect(*a[:4])
        self._c("clip", r.x(), r.y(), r.width(), r.height())

    def setCompositionMode(self, m):
        pass

    def setViewport(self, *a):
        pass

    def setWindow(self, *a):
        pass

    @staticmethod
    def _rect(a):
        if isinstance(a[0], QRect):
            r = a[0]
            return [r.x(), r.y(), r.width(), r.height()], a[1:]
        return list(a[:4]), a[4:]

    def drawLine(self, *a):
        if len(a) == 1:
            ln = a[0]
            self._c("line", ln.p1().x(), ln.p1().y(), ln.p2().x(), ln.p2().y())
        elif len(a) == 2:
            self._c("line", a[0].x(), a[0].y(), a[1].x(), a[1].y())
        else:
            self._c("line", a[0], a[1], a[2], a[3])

    def drawLines(self, *a):
        lines = a[0] if len(a) == 1 else a
        for ln in lines:
            self.drawLine(ln)

    def drawRect(self, *a):
        r, _ = self._rect(a)
        self._c("rect", *r)

    def drawRects(self, rects):
        for r in rects:
            self.drawRect(r)

    def drawRoundedRect(self, *a):
        r, rest = self._rect(a)
        rx = rest[0] if rest else 5
        ry = rest[1] if len(rest) > 1 else rx
        self._c("rrect", r[0], r[1], r[2], r[3], rx, ry)

    def fillRect(self, *a):
        r, rest = self._rect(a)
        c = rest[0] if rest else "black"
        self._c("fill", r[0], r[1], r[2], r[3], _css_color(c))

    def eraseRect(self, *a):
        r, _ = self._rect(a)
        self._c("clear", *r)

    def drawEllipse(self, *a):
        if len(a) == 3 and isinstance(a[0], QPoint):
            c, rx, ry = a
            self._c("ellipse", c.x() - rx, c.y() - ry, 2 * rx, 2 * ry)
        else:
            r, _ = self._rect(a)
            self._c("ellipse", *r)

    def drawArc(self, *a):
        r, rest = self._rect(a)
        self._c("arc", r[0], r[1], r[2], r[3], rest[0] / 16.0, rest[1] / 16.0, "arc")

    def drawPie(self, *a):
        r, rest = self._rect(a)
        self._c("arc", r[0], r[1], r[2], r[3], rest[0] / 16.0, rest[1] / 16.0, "pie")

    def drawChord(self, *a):
        r, rest = self._rect(a)
        self._c("arc", r[0], r[1], r[2], r[3], rest[0] / 16.0, rest[1] / 16.0, "chord")

    def _points(self, a):
        pts = a[0] if len(a) == 1 and isinstance(a[0], (list, tuple)) else a
        out = []
        for p in pts:
            if isinstance(p, QPoint):
                out += [p.x(), p.y()]
            elif isinstance(p, (int, float)):
                out.append(p)
        return out

    def drawPolygon(self, *a, **kw):
        if a and isinstance(a[0], (list, tuple)):
            a = (a[0],)
        self._c("poly", self._points(a), True)

    def drawConvexPolygon(self, *a):
        self.drawPolygon(*a)

    def drawPolyline(self, *a):
        self._c("poly", self._points(a), False)

    def drawPoint(self, *a):
        if isinstance(a[0], QPoint):
            self._c("point", a[0].x(), a[0].y())
        else:
            self._c("point", a[0], a[1])

    def drawPoints(self, *a):
        for i in range(0, len(self._points(a)), 2):
            pts = self._points(a)
            self._c("point", pts[i], pts[i + 1])

    def drawText(self, *a):
        if isinstance(a[0], QRect):
            r = a[0]
            flags = a[1] if len(a) > 2 else 0
            text = a[-1]
            self._c("textr", r.x(), r.y(), r.width(), r.height(), int(flags), str(text))
        elif isinstance(a[0], QPoint):
            self._c("text", a[0].x(), a[0].y(), str(a[1]))
        elif len(a) >= 6:
            self._c("textr", a[0], a[1], a[2], a[3], int(a[4]), str(a[5]))
        else:
            self._c("text", a[0], a[1], str(a[2]))

    def drawPath(self, path):
        self._c("path", path._cmds)

    def fillPath(self, path, brush):
        self._c("save")
        self.setBrush(brush)
        self._c("pen", None)
        self._c("path", path._cmds)
        self._c("restore")

    def strokePath(self, path, pen):
        self._c("save")
        self.setPen(pen)
        self._c("brush", None)
        self._c("path", path._cmds)
        self._c("restore")

    def drawPixmap(self, *a):
        pix = next((x for x in a if isinstance(x, QPixmap)), None)
        if pix is None or not pix._name:
            return
        if isinstance(a[0], QRect):
            r = a[0]
            self._c("img", pix._name, r.x(), r.y(), r.width(), r.height())
        elif isinstance(a[0], QPoint):
            self._c("img", pix._name, a[0].x(), a[0].y(), pix._w, pix._h)
        elif len(a) >= 5 and isinstance(a[4], QPixmap):
            self._c("img", pix._name, a[0], a[1], a[2], a[3])
        else:
            self._c("img", pix._name, a[0], a[1], pix._w, pix._h)

    drawImage = drawPixmap

    def viewport(self):
        return QRect(0, 0, 0, 0)

    def device(self):
        return None


class QLinearGradient:
    def __init__(self, *a):
        self._stops = []

    def setColorAt(self, pos, c):
        self._stops.append((pos, _css_color(c)))


QRadialGradient = QConicalGradient = QLinearGradient


class QTransform:
    def __init__(self, *a):
        pass

    def rotate(self, a):
        return self

    def scale(self, a, b):
        return self

    def translate(self, a, b):
        return self


class QGraphicsDropShadowEffect(QObject):
    def setBlurRadius(self, r):
        pass

    def setOffset(self, *a):
        pass

    def setColor(self, c):
        pass


QGraphicsOpacityEffect = QGraphicsDropShadowEffect


# ---------------------------------------------------------------- Hilfen
class QCompleter(QObject):
    def __init__(self, *a):
        QObject.__init__(self)

    def setCaseSensitivity(self, c):
        pass

    def setFilterMode(self, m):
        pass


class QStandardPaths:
    DocumentsLocation, AppDataLocation, HomeLocation, TempLocation = 1, 17, 8, 7
    StandardLocation = _enum("StandardLocation", DocumentsLocation=1, AppDataLocation=17, HomeLocation=8,
                             TempLocation=7)

    @staticmethod
    def writableLocation(loc):
        import os
        return os.getcwd()


class QDir:
    @staticmethod
    def homePath():
        import os
        return os.getcwd()

    @staticmethod
    def currentPath():
        import os
        return os.getcwd()


class QFile:
    @staticmethod
    def exists(p):
        import os
        return os.path.exists(p)


class QFileInfo:
    def __init__(self, p):
        self._p = p

    def fileName(self):
        import os
        return os.path.basename(self._p)

    def exists(self):
        import os
        return os.path.exists(self._p)

    def absoluteFilePath(self):
        import os
        return os.path.abspath(self._p)


class QSound:
    @staticmethod
    def play(f):
        pass


class QEventLoop(QObject):
    def exec(self):
        self._quit = False
        _g.run_loop(lambda: self._quit)
        return 0

    exec_ = exec

    def quit(self):
        self._quit = True


class QSignalBlocker:
    def __init__(self, obj):
        self._o = obj
        self._old = obj.blockSignals(True)

    def unblock(self):
        self._o.blockSignals(self._old)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.unblock()


QVariant = object
QAbstractListModel = QAbstractTableModel = QObject
QModelIndex = object
QItemSelectionModel = QObject
QStringListModel = QObject
QStandardItemModel = QObject
QStandardItem = QListWidgetItem
QStyledItemDelegate = QObject
QSortFilterProxyModel = QObject

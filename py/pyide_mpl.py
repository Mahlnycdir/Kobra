"""matplotlib-Backend fuer PyIDE: Abbildungen erscheinen in der Konsole.

plt.show() zeigt die Abbildung, plt.pause() und Animationen (FuncAnimation)
aktualisieren dasselbe Bild laufend."""
import base64
import io
import time

import pyide_gui as _g
from matplotlib.backend_bases import FigureManagerBase, TimerBase, _Backend
from matplotlib.backends.backend_agg import FigureCanvasAgg

_live = {}   # key -> figure (offene, live aktualisierte Abbildungen)
_count = [0]


def reset():
    _live.clear()


def has_live():
    """True, solange eine gezeigte Abbildung noch laufende Timer (Animation) hat."""
    for fig in list(_live.values()):
        for t in getattr(fig.canvas, "_pyide_timers", []):
            if getattr(t, "_tid", None):
                return True
    return False


def _key(fig):
    k = getattr(fig, "_pyide_key", None)
    if k is None:
        _count[0] += 1
        k = "fig%d" % _count[0]
        fig._pyide_key = k
    return k


class _FigSync:
    def __init__(self, fig):
        self.fig = fig

    def _pyide_sync(self):
        send_figure(self.fig)

    def _pyide_event(self, ev):
        if ev.get("k") == "close":
            close_figure(self.fig)


def send_figure(fig):
    canvas = fig.canvas
    if not isinstance(canvas, FigureCanvasAgg):
        canvas = FigureCanvasPyIDE(fig)
    canvas.draw()
    w, h = canvas.get_width_height(physical=True)
    rgba = bytes(canvas.buffer_rgba())
    png = None
    try:
        from PIL import Image
        buf = io.BytesIO()
        Image.frombuffer("RGBA", (w, h), rgba, "raw", "RGBA", 0, 1).save(buf, format="PNG", compress_level=1)
        png = buf.getvalue()
    except Exception:
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        png = buf.getvalue()
    key = _key(fig)
    _g.op("mpl", key, base64.b64encode(png).decode("ascii"), w, h, fig.get_label() or "")


def flush_figures():
    """Am Programmende: noch nicht gezeigte Abbildungen ausgeben."""
    from matplotlib._pylab_helpers import Gcf
    for manager in Gcf.get_all_fig_managers():
        fig = manager.canvas.figure
        if getattr(fig, "_pyide_shown", False) and _key(fig) not in _live:
            continue
        send_figure(fig)
        fig._pyide_shown = True
    _g.flush()


def close_figure(fig):
    from matplotlib._pylab_helpers import Gcf
    key = _key(fig)
    _live.pop(key, None)
    _g.unregister(key)
    for manager in Gcf.get_all_fig_managers():
        if manager.canvas.figure is fig:
            for t in list(getattr(fig.canvas, "_pyide_timers", [])):
                t.stop()
            Gcf.destroy(manager)
            break
    _g.op("mpl_closed", key)


class TimerPyIDE(TimerBase):
    def __init__(self, *args, **kwargs):
        self._tid = None
        super().__init__(*args, **kwargs)

    def _timer_start(self):
        self._timer_stop()
        self._tid = _g.add_timer(max(1, int(self._interval)), self._tick)

    def _tick(self):
        self._tid = None
        self._on_timer()
        if self.callbacks and not self._single and self._tid is None:
            self._tid = _g.add_timer(max(1, int(self._interval)), self._tick)

    def _timer_stop(self):
        if self._tid:
            _g.cancel_timer(self._tid)
            self._tid = None

    def _timer_set_interval(self):
        if self._tid:
            self._timer_start()


class FigureCanvasPyIDE(FigureCanvasAgg):
    _timer_cls = TimerPyIDE

    def new_timer(self, *args, **kwargs):
        t = super().new_timer(*args, **kwargs)
        if not hasattr(self, "_pyide_timers"):
            self._pyide_timers = []
        self._pyide_timers.append(t)
        return t

    def draw_idle(self, *args, **kwargs):
        fig = self.figure
        key = _key(fig)
        if key in _live:
            _g.mark_dirty(_live_sync(fig))

    def start_event_loop(self, timeout=0):
        _g.flush()
        end = time.monotonic() + max(0.0, float(timeout or 0))
        while True:
            _g.update()
            rest = end - time.monotonic()
            if rest <= 0:
                break
            time.sleep(min(rest, 0.02))

    def flush_events(self):
        _g.update()


_syncs = {}


def _live_sync(fig):
    key = _key(fig)
    s = _syncs.get(key)
    if s is None:
        s = _syncs[key] = _FigSync(fig)
        _g.register(key, s)
    return s


class FigureManagerPyIDE(FigureManagerBase):
    def show(self):
        fig = self.canvas.figure
        key = _key(fig)
        _live[key] = fig
        _live_sync(fig)
        send_figure(fig)
        fig._pyide_shown = True
        _g.flush()


FigureCanvasPyIDE.manager_class = FigureManagerPyIDE


@_Backend.export
class _BackendPyIDE(_Backend):
    FigureCanvas = FigureCanvasPyIDE
    FigureManager = FigureManagerPyIDE

    @classmethod
    def show(cls, *args, block=None, **kwargs):
        from matplotlib._pylab_helpers import Gcf
        managers = Gcf.get_all_fig_managers()
        animated = []
        for m in managers:
            fig = m.canvas.figure
            m.show()
            if getattr(m.canvas, "_pyide_timers", None):
                animated.append(fig)
        if block is False:
            return
        if animated:
            # Animation: laufen lassen, bis alle animierten Abbildungen geschlossen sind
            keys = [_key(f) for f in animated]
            if not _g.run_loop(lambda: not any(k in _live for k in keys)):
                return
        else:
            for m in managers:
                _live.pop(_key(m.canvas.figure), None)
            Gcf.destroy_all()

    @staticmethod
    def mainloop():
        pass

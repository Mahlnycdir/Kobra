"""Gemeinsamer Kern des GUI-Emulators (tkinter- und Qt-Nachbau).

Python haelt das Modell aller Fenster/Widgets und schickt Zeichen-Operationen
(ops) als JSON an die Oberflaeche. Ereignisse (Klicks, Tasten, Eingaben) kommen
als JSON-Listen zurueck und werden hier verteilt.

Zwei Betriebsarten:
  * "sync"  – ein Service-Worker-Kanal erlaubt blockierendes Warten. mainloop()
              blockiert dann wie im echten tkinter.
  * "async" – Fallback ohne Kanal: mainloop() kehrt sofort zurueck, Ereignisse
              werden spaeter per Callback verteilt.
"""
import heapq
import itertools
import json
import sys
import time
import traceback

try:  # im Browser vom Worker registriert
    import pyide_js as _js  # type: ignore
except Exception:  # pragma: no cover - Tests ausserhalb des Browsers
    _js = None


class _S:
    ops = []
    next_id = 0
    objects = {}          # id -> Objekt mit _pyide_event(ev)
    timers = []           # heap (due, seq, tid)
    timer_funcs = {}      # tid -> (func, args)
    timer_seq = itertools.count(1)
    toplevels = {}        # id -> Fenster-Objekt (offen)
    geometry = {}         # id -> [x, y, w, h]
    geom_dirty = True
    loop_level = 0
    quit_level = None
    dispatching = False
    dirty = {}            # id(obj) -> obj, Zustand wird beim flush gesendet
    after_dispatch = []   # Hooks nach Ereignissen (z.B. Dateien zuruecksyncen)
    screen = (390, 844)


def new_id(prefix="w"):
    _S.next_id += 1
    return "%s%d" % (prefix, _S.next_id)


def register(obj_id, obj):
    _S.objects[obj_id] = obj


def unregister(obj_id):
    _S.objects.pop(obj_id, None)
    _S.geometry.pop(obj_id, None)


def op(*args):
    _S.ops.append(list(args))
    _S.geom_dirty = True
    if len(_S.ops) > 4000:
        flush()


def mark_dirty(obj):
    """Objekt sendet seinen Zustand erst beim naechsten flush() (z.B. Text-Inhalt)."""
    _S.dirty[id(obj)] = obj
    _S.geom_dirty = True


def flush():
    if _S.dirty:
        pending = list(_S.dirty.values())
        _S.dirty.clear()
        for obj in pending:
            try:
                obj._pyide_sync()
            except Exception:
                report_exception()
    if not _S.ops:
        return
    data = json.dumps(_S.ops, default=_json_default)
    _S.ops = []
    if _js is not None:
        _js.send(data)
    else:
        _test_sink.append(json.loads(data))


_test_sink = []


def _json_default(o):
    if hasattr(o, "_pyide_json"):
        return o._pyide_json()
    if isinstance(o, (set, tuple)):
        return list(o)
    if isinstance(o, bytes):
        return o.decode("latin-1")
    return str(o)


def has_sync():
    try:
        return bool(_js is not None and _js.has_sync())
    except Exception:
        return False


def sync_call(kind, payload):
    """Blockierender Aufruf an die Oberflaeche (Dialoge, Layout-Abfragen)."""
    flush()
    if _js is None:
        return _test_sync(kind, payload)
    if not has_sync():
        return None
    res = _js.sync(kind, json.dumps(payload, default=_json_default))
    if res is None:
        return None
    try:
        return json.loads(str(res))
    except Exception:
        return None


def _test_sync(kind, payload):  # wird in Tests ersetzt
    return None


# ---------------------------------------------------------------- Timer
def add_timer(ms, func, args=()):
    tid = "after#%d" % next(_S.timer_seq)
    due = time.monotonic() + max(0, float(ms)) / 1000.0
    heapq.heappush(_S.timers, (due, next(_S.timer_seq), tid))
    _S.timer_funcs[tid] = (func, args)
    _schedule_async_tick()
    return tid


def cancel_timer(tid):
    _S.timer_funcs.pop(tid, None)


def _next_delay_ms():
    while _S.timers and _S.timers[0][2] not in _S.timer_funcs:
        heapq.heappop(_S.timers)
    if not _S.timers:
        return None
    return max(0, int((_S.timers[0][0] - time.monotonic()) * 1000))


def run_due_timers():
    now = time.monotonic()
    ran = 0
    while _S.timers and _S.timers[0][0] <= now and ran < 500:
        _, _, tid = heapq.heappop(_S.timers)
        entry = _S.timer_funcs.pop(tid, None)
        if entry is None:
            continue
        func, args = entry
        ran += 1
        _safe_call(func, *args)
    return _next_delay_ms()


def _safe_call(func, *args):
    try:
        return func(*args)
    except SystemExit:
        raise
    except Exception:
        report_exception()
    return None


def report_exception():
    """Fehler in Callbacks wie tkinter: ausgeben, aber weiterlaufen."""
    etype, value, tb = sys.exc_info()
    try:
        import pyide_runtime
        pyide_runtime.print_user_traceback(etype, value, tb, prefix="Exception in Tkinter callback\n")
    except Exception:
        traceback.print_exception(etype, value, tb)


# ----------------------------------------------------------- Ereignisse
def dispatch(events):
    if isinstance(events, str):
        events = json.loads(events) if events else []
    for ev in events:
        k = ev.get("k")
        if k == "geom":
            for wid, g in ev.get("g", {}).items():
                old = _S.geometry.get(wid)
                _S.geometry[wid] = g
                obj = _S.objects.get(wid)
                if obj is not None and old != g and hasattr(obj, "_pyide_geometry_changed"):
                    _safe_call(obj._pyide_geometry_changed, old, g)
            continue
        target = _S.objects.get(ev.get("w"))
        if target is None:
            continue
        try:
            target._pyide_event(ev)
        except SystemExit:
            raise
        except Exception:
            report_exception()
    flush()
    for hook in list(_S.after_dispatch):
        try:
            hook()
        except Exception:
            pass


def process_idle():
    """Vom Worker aufgerufen, wenn kein Python-Code laeuft (Async-Modus)."""
    delay = run_due_timers()
    flush()
    return -1 if delay is None else delay


def _schedule_async_tick():
    if _js is None or _S.loop_level > 0:
        return
    try:
        _js.wake()
    except Exception:
        pass


def update(wait=False):
    """Ausstehende Operationen senden und anstehende Ereignisse verarbeiten."""
    flush()
    if _js is None or not has_sync():
        run_due_timers()
        flush()
        return
    try:
        evs = _js.poll(0)
    except Exception:
        evs = None
    if evs:
        dispatch(str(evs))
    run_due_timers()
    flush()


def refresh_geometry():
    if not _S.geom_dirty:
        return
    res = sync_call("layout", {})
    if isinstance(res, dict):
        _S.geometry.update(res)
        _S.geom_dirty = False


def geometry_of(wid):
    refresh_geometry()
    return _S.geometry.get(wid)


class LoopUnavailable(Exception):
    pass


def run_loop(until):
    """Blockierende Ereignisschleife. Liefert False, wenn nicht moeglich."""
    flush()
    if _js is None or not has_sync():
        return False
    _S.loop_level += 1
    try:
        while not until():
            delay = run_due_timers()
            flush()
            if until():
                break
            timeout = 25000 if delay is None else min(delay, 25000)
            try:
                evs = _js.poll(int(timeout))
            except Exception:
                return False
            if evs:
                dispatch(str(evs))
        return True
    finally:
        _S.loop_level -= 1
        flush()


def windows_open():
    return bool(_S.toplevels)


def reset():
    """Vor jedem Programmlauf: alles vergessen."""
    _S.ops = []
    _S.dirty = {}
    _S.objects = {}
    _S.timers = []
    _S.timer_funcs = {}
    _S.toplevels = {}
    _S.geometry = {}
    _S.geom_dirty = True
    _S.loop_level = 0
    if _js is not None:
        try:
            _js.send(json.dumps([["reset"]]))
        except Exception:
            pass


# ------------------------------------------------------------- Bilder
def image_size(data):
    """Breite/Hoehe aus PNG/GIF/JPEG-Bytes lesen."""
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            import struct
            w, h = struct.unpack(">II", data[16:24])
            return w, h, "image/png"
        if data[:6] in (b"GIF87a", b"GIF89a"):
            import struct
            w, h = struct.unpack("<HH", data[6:10])
            return w, h, "image/gif"
        if data[:2] == b"\xff\xd8":
            import struct
            i = 2
            while i < len(data):
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2):
                    h, w = struct.unpack(">HH", data[i + 5:i + 9])
                    return w, h, "image/jpeg"
                seglen = struct.unpack(">H", data[i + 2:i + 4])[0]
                i += 2 + seglen
        if data[:2] in (b"P6", b"P3", b"P5"):
            parts = data.split(None, 4)
            return int(parts[1]), int(parts[2]), "image/x-portable-pixmap"
    except Exception:
        pass
    return 0, 0, "application/octet-stream"

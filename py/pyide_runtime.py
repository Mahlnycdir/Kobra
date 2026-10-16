"""Laufzeit-Helfer der IDE: Programme ausfuehren, Fehler anzeigen,
Vervollstaendigung (jedi), Pruefung (pyflakes), Formatierung (black)."""
import ast
import builtins
import importlib
import importlib.abc
import importlib.util
import io
import json
import os
import sys
import time
import traceback
import types

import pyide_gui as _g

try:
    import pyide_js as _js  # type: ignore
except Exception:  # Tests
    _js = None

LIB_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_ROOT = "/home/pyodide/projects"


class _State:
    project_dir = None
    main_ns = None
    snapshot = {}
    last_sync = 0.0
    jedi_projects = {}
    last_completions = []
    running = False


def _notify(kind, **data):
    data["type"] = kind
    if _js is not None:
        try:
            _js.notify(json.dumps(data))
        except Exception:
            pass


# ------------------------------------------------------------ Import-Hooks
_ALIASES = {"PIL.ImageTk": "pyide_imagetk"}
_POST_HOOKS = {}


class _AliasLoader(importlib.abc.Loader):
    def __init__(self, target):
        self.target = target

    def create_module(self, spec):
        return importlib.import_module(self.target)

    def exec_module(self, module):
        pass


class _HookLoader(importlib.abc.Loader):
    def __init__(self, inner, hook):
        self.inner = inner
        self.hook = hook

    def create_module(self, spec):
        return self.inner.create_module(spec)

    def exec_module(self, module):
        self.inner.exec_module(module)
        try:
            self.hook(module)
        except Exception:
            pass

    def __getattr__(self, name):
        return getattr(self.inner, name)


class _Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname in _ALIASES:
            return importlib.util.spec_from_loader(fullname, _AliasLoader(_ALIASES[fullname]))
        hook = _POST_HOOKS.get(fullname)
        if hook:
            for finder in sys.meta_path:
                if finder is self:
                    continue
                find = getattr(finder, "find_spec", None)
                if not find:
                    continue
                spec = find(fullname, path, target)
                if spec is not None and spec.loader is not None:
                    spec.loader = _HookLoader(spec.loader, hook)
                    return spec
        return None


def _patch_pil_image(mod):
    def show(self, title=None, **kw):
        send_pil_image(self, title)
    mod.Image.show = show


def send_pil_image(img, title=None):
    import base64
    buf = io.BytesIO()
    im = img
    if im.mode not in ("RGB", "RGBA", "L", "LA", "P"):
        im = im.convert("RGBA")
    im.save(buf, format="PNG", compress_level=1)
    _g.op("mpl", None, base64.b64encode(buf.getvalue()).decode("ascii"), im.width, im.height, title or "")
    _g.flush()


_POST_HOOKS["PIL.Image"] = _patch_pil_image


def setup():
    """Einmal nach dem Start des Workers."""
    if LIB_DIR not in sys.path:
        sys.path.insert(0, LIB_DIR)
    if not any(isinstance(f, _Finder) for f in sys.meta_path):
        sys.meta_path.insert(0, _Finder())
    os.environ["MPLBACKEND"] = "module://pyide_mpl"
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.dont_write_bytecode = True
    os.makedirs(PROJECTS_ROOT, exist_ok=True)
    _g._S.after_dispatch.append(maybe_sync_files)


# ---------------------------------------------------------------- Ausfuehren
_GUI_MODULES = ("tkinter", "PyQt5", "PyQt6", "PySide6", "PySide2", "pyide_qt", "pyide_imagetk", "turtle")


def _purge_modules(project_dir):
    for name, mod in list(sys.modules.items()):
        f = getattr(mod, "__file__", None) or ""
        if f.startswith(project_dir + os.sep):
            del sys.modules[name]
        elif name.split(".")[0] in _GUI_MODULES:
            del sys.modules[name]
    if "PIL.ImageTk" in sys.modules:
        del sys.modules["PIL.ImageTk"]
        pil = sys.modules.get("PIL")
        if pil is not None and hasattr(pil, "ImageTk"):
            try:
                delattr(pil, "ImageTk")
            except Exception:
                pass


def run_file(project_dir, rel_path, argv_json="[]"):
    """Fuehrt eine Datei des Projekts als __main__ aus."""
    argv = json.loads(argv_json) if isinstance(argv_json, str) else list(argv_json or [])
    _State.project_dir = project_dir
    _g.reset()
    _purge_modules(project_dir)
    try:
        import pyide_mpl
        pyide_mpl.reset()
    except Exception:
        pass
    os.chdir(project_dir)
    abs_path = os.path.join(project_dir, rel_path)
    sys.path[:] = [p for p in sys.path if not p.startswith(PROJECTS_ROOT)]
    script_dir = os.path.dirname(abs_path)
    sys.path.insert(0, project_dir)
    if script_dir != project_dir:
        sys.path.insert(0, script_dir)
    importlib.invalidate_caches()
    sys.argv = [rel_path] + [str(a) for a in argv]
    main = types.ModuleType("__main__")
    main.__file__ = abs_path
    main.__builtins__ = builtins
    main.__spec__ = None
    sys.modules["__main__"] = main
    _State.main_ns = main.__dict__
    _State.snapshot = snapshot(project_dir)
    _State.last_sync = time.monotonic()
    exit_code = 0
    _State.running = True
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            source = f.read()
        code = compile(source, abs_path, "exec")
        exec(code, main.__dict__)
    except SystemExit as e:
        exit_code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        if e.code not in (None, 0) and not isinstance(e.code, int):
            print(e.code, file=sys.stderr)
    except BaseException:
        etype, value, tb = sys.exc_info()
        print_user_traceback(etype, value, tb)
        exit_code = 1
    finally:
        _State.running = False
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass
        _g.flush()
    gui = _g.windows_open()
    try:
        import pyide_mpl
        pyide_mpl.flush_figures()
        gui = gui or pyide_mpl.has_live()
    except Exception:
        pass
    return json.dumps({"gui": bool(gui), "exit": exit_code})


def gui_alive():
    try:
        import pyide_mpl
        live = pyide_mpl.has_live()
    except Exception:
        live = False
    return bool(_g.windows_open() or live)


def _rel(path):
    pd = _State.project_dir
    if pd and path.startswith(pd + os.sep):
        return path[len(pd) + 1:]
    return path


def print_user_traceback(etype, value, tb, prefix=""):
    frames = traceback.extract_tb(tb)
    keep = []
    for i, fr in enumerate(frames):
        fn = fr.filename
        if fn == __file__ or (fn.startswith(LIB_DIR) and i != len(frames) - 1):
            continue
        if fn.startswith("/lib/python") and "pyodide" in fn and i != len(frames) - 1:
            continue
        keep.append(fr)
    out = prefix
    if keep:
        out += "Traceback (most recent call last):\n"
        for fr in keep:
            out += '  File "%s", line %s, in %s\n' % (_rel(fr.filename), fr.lineno, fr.name)
            if fr.line:
                out += "    %s\n" % fr.line.strip()
    lines = traceback.format_exception_only(etype, value)
    out += "".join(lines).replace((_State.project_dir or "\0") + os.sep, "")
    sys.stderr.write(out)
    try:
        sys.stderr.flush()
    except Exception:
        pass
    if isinstance(value, ModuleNotFoundError) and value.name:
        mod = value.name.split(".")[0]
        _notify("missing-module", module=mod, package=_pip_name(mod))
    if isinstance(value, ImportError) and "tkinter" in str(value):
        pass


_PIP_NAMES = {"cv2": "opencv-python", "sklearn": "scikit-learn", "PIL": "pillow", "yaml": "pyyaml",
              "bs4": "beautifulsoup4", "skimage": "scikit-image", "dateutil": "python-dateutil",
              "Crypto": "pycryptodome", "attr": "attrs", "google.protobuf": "protobuf"}


def _pip_name(mod):
    return _PIP_NAMES.get(mod, mod)


# --------------------------------------------------------------- Dateisync
def snapshot(root):
    snap = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git")]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            try:
                st = os.stat(p)
            except OSError:
                continue
            snap[os.path.relpath(p, root)] = (st.st_mtime, st.st_size)
    return snap


def changed_files(root=None):
    """Vom Programm geschriebene/geloeschte Dateien seit dem letzten Abgleich."""
    root = root or _State.project_dir
    if not root:
        return json.dumps({"changed": [], "deleted": []})
    new = snapshot(root)
    old = _State.snapshot
    changed = [p for p, v in new.items() if old.get(p) != v]
    deleted = [p for p in old if p not in new]
    _State.snapshot = new
    return json.dumps({"changed": changed, "deleted": deleted})


def note_written(rel_paths_json):
    """Die IDE hat Dateien geschrieben – nicht als Programmaenderung melden."""
    root = _State.project_dir
    if not root:
        return
    for rel in json.loads(rel_paths_json):
        p = os.path.join(root, rel)
        try:
            st = os.stat(p)
            _State.snapshot[rel] = (st.st_mtime, st.st_size)
        except OSError:
            _State.snapshot.pop(rel, None)


def maybe_sync_files():
    now = time.monotonic()
    if now - _State.last_sync < 2.0:
        return
    _State.last_sync = now
    _notify("files-maybe-changed")


# ------------------------------------------------------------------ REPL
def repl(source):
    """Fuehrt Konsolen-Eingaben aus. Unterstuetzt auch 'await' auf oberster Ebene;
    dann wird eine Coroutine zurueckgegeben, die der Worker abwartet."""
    import inspect
    ns = _State.main_ns
    if ns is None:
        main = types.ModuleType("__main__")
        main.__builtins__ = builtins
        sys.modules["__main__"] = main
        ns = _State.main_ns = main.__dict__
    filename = "<eingabe>"
    flags = ast.PyCF_ALLOW_TOP_LEVEL_AWAIT
    try:
        tree = ast.parse(source, filename, "exec")
        last = tree.body[-1] if tree.body else None
        if isinstance(last, ast.Expr):
            code1 = compile(ast.Module(body=tree.body[:-1], type_ignores=[]), filename, "exec", flags=flags)
            code2 = compile(ast.Expression(last.value), filename, "eval", flags=flags)
        else:
            code1 = compile(tree, filename, "exec", flags=flags)
            code2 = None
    except SyntaxError:
        etype, value, tb = sys.exc_info()
        print_user_traceback(etype, value, None)
        return None

    def show(val):
        if val is not None:
            ns["_"] = val
            print(repr(val))

    def finish():
        _g.flush()
        try:
            import pyide_mpl
            pyide_mpl.flush_figures()
        except Exception:
            pass

    is_async = bool(code1.co_flags & inspect.CO_COROUTINE) or bool(code2 is not None and code2.co_flags & inspect.CO_COROUTINE)
    if not is_async:
        try:
            exec(code1, ns)
            if code2 is not None:
                show(eval(code2, ns))
        except SystemExit:
            pass
        except BaseException:
            etype, value, tb = sys.exc_info()
            print_user_traceback(etype, value, tb)
        finally:
            finish()
        return None

    async def run_async():
        try:
            r = eval(code1, ns)
            if inspect.iscoroutine(r):
                await r
            if code2 is not None:
                v = eval(code2, ns)
                if inspect.iscoroutine(v):
                    v = await v
                show(v)
        except SystemExit:
            pass
        except BaseException:
            etype, value, tb = sys.exc_info()
            print_user_traceback(etype, value, tb)
        finally:
            finish()
    return run_async()


def variables():
    ns = _State.main_ns or {}
    out = []
    for k, v in ns.items():
        if k.startswith("__") or isinstance(v, types.ModuleType) or k in ("_",):
            continue
        if isinstance(v, (types.FunctionType, type, types.BuiltinFunctionType)):
            kind = "Funktion" if not isinstance(v, type) else "Klasse"
            out.append({"n": k, "t": kind, "v": getattr(v, "__qualname__", k)})
            continue
        t = type(v).__name__
        try:
            if hasattr(v, "shape") and hasattr(v, "dtype"):
                r = "%s %s %s" % (t, tuple(v.shape), v.dtype)
            else:
                r = repr(v)
        except Exception:
            r = "<?>"
        if len(r) > 160:
            r = r[:157] + "…"
        extra = ""
        try:
            if isinstance(v, (list, tuple, dict, set, str)):
                extra = " (%d)" % len(v)
        except Exception:
            pass
        out.append({"n": k, "t": t + extra, "v": r})
    out.sort(key=lambda d: (d["t"] in ("Funktion", "Klasse"), d["n"].lower()))
    return json.dumps(out)


# --------------------------------------------------------- IntelliSense
def _jedi_project(project_dir):
    import jedi
    p = _State.jedi_projects.get(project_dir)
    if p is None:
        p = jedi.Project(project_dir, added_sys_path=[LIB_DIR], smart_sys_path=True)
        _State.jedi_projects[project_dir] = p
    return p


def _script(code, path, project_dir):
    import jedi
    return jedi.Script(code, path=path, project=_jedi_project(project_dir))


def complete(code, line, col, path, project_dir):
    try:
        s = _script(code, path, project_dir)
        comps = s.complete(int(line), int(col))
    except Exception:
        return "[]"
    _State.last_completions = comps[:200]
    out = []
    for i, c in enumerate(comps[:200]):
        out.append({"i": i, "n": c.name, "t": c.type, "c": c.complete})
    return json.dumps(out)


def completion_info(index):
    try:
        c = _State.last_completions[int(index)]
    except Exception:
        return "{}"
    try:
        sigs = [s.to_string() for s in c.get_signatures()][:3]
    except Exception:
        sigs = []
    try:
        doc = c.docstring(raw=True)
    except Exception:
        doc = ""
    return json.dumps({"sig": sigs, "doc": (doc or "")[:2500], "mod": c.module_name or ""})


def signatures(code, line, col, path, project_dir):
    try:
        s = _script(code, path, project_dir)
        sigs = s.get_signatures(int(line), int(col))
    except Exception:
        return "[]"
    out = []
    for sg in sigs[:2]:
        try:
            params = [p.to_string() for p in sg.params]
        except Exception:
            params = []
        try:
            doc = sg.docstring(raw=True)
        except Exception:
            doc = ""
        out.append({"name": sg.name, "params": params, "index": sg.index, "doc": (doc or "")[:600]})
    return json.dumps(out)


def help_at(code, line, col, path, project_dir):
    try:
        s = _script(code, path, project_dir)
        names = s.help(int(line), int(col)) or s.infer(int(line), int(col))
    except Exception:
        return "{}"
    if not names:
        return "{}"
    n = names[0]
    try:
        sigs = [x.to_string() for x in n.get_signatures()][:3]
    except Exception:
        sigs = []
    try:
        doc = n.docstring(raw=True)
    except Exception:
        doc = ""
    return json.dumps({"name": n.name, "full": n.full_name or n.name, "type": n.type, "sig": sigs,
                       "doc": (doc or "")[:4000]})


def goto(code, line, col, path, project_dir):
    try:
        s = _script(code, path, project_dir)
        res = s.goto(int(line), int(col), follow_imports=True)
    except Exception:
        return "{}"
    for r in res:
        mp = str(r.module_path or "")
        if mp.startswith(project_dir + os.sep) and r.line:
            return json.dumps({"path": os.path.relpath(mp, project_dir), "line": r.line, "col": r.column or 0})
        if mp == path and r.line:
            return json.dumps({"path": None, "line": r.line, "col": r.column or 0})
    if res:
        return json.dumps({"external": res[0].full_name or res[0].name})
    return "{}"


def references(code, line, col, path, project_dir):
    try:
        s = _script(code, path, project_dir)
        refs = s.get_references(int(line), int(col), scope="file")
    except Exception:
        return "[]"
    return json.dumps([{"line": r.line, "col": r.column, "len": len(r.name)} for r in refs if r.line])


def rename(code, line, col, new_name, path, project_dir):
    try:
        s = _script(code, path, project_dir)
        refs = s.get_references(int(line), int(col), scope="file")
    except Exception:
        return "[]"
    return json.dumps([{"line": r.line, "col": r.column, "len": len(r.name)} for r in refs
                       if r.line and (not r.module_path or str(r.module_path) == path)])


# ---------------------------------------------------------------- Pruefen
_IGNORE_FLAKES = ("ImportStarUsed", "ImportStarUsage", "ImportStarNotPermitted")
_ERROR_FLAKES = ("UndefinedName", "UndefinedLocal", "UndefinedExport", "ReturnOutsideFunction",
                 "YieldOutsideFunction", "ContinueOutsideLoop", "BreakOutsideLoop", "DuplicateArgument",
                 "TooManyExpressionsInStarredAssignment", "StringDotFormatMissingArgument",
                 "PercentFormatMissingArgument", "ForwardAnnotationSyntaxError")
_MSG_DE = {
    "UnusedImport": "'%s' wird importiert, aber nicht verwendet",
    "UnusedVariable": "Variable '%s' wird zugewiesen, aber nie verwendet",
    "UndefinedName": "'%s' ist nicht definiert",
    "RedefinedWhileUnused": "'%s' wird neu definiert, bevor es verwendet wurde (Zeile %r)",
    "UndefinedLocal": "Lokale Variable '%s' (definiert in Zeile %r) wird vor der Zuweisung verwendet",
    "ImportShadowedByLoopVar": "Import '%s' (Zeile %r) wird von der Schleifenvariable überdeckt",
    "FStringMissingPlaceholders": "f-String ohne Platzhalter",
    "IsLiteral": "Vergleich mit 'is' bei einem Literal – meinst du '=='?",
}


def lint(code, path):
    diags = []
    try:
        tree = compile(code, path, "exec", ast.PyCF_ONLY_AST)
    except SyntaxError as e:
        msg = e.msg
        diags.append({"l": e.lineno or 1, "c": e.offset or 1, "el": e.end_lineno or e.lineno or 1,
                      "ec": e.end_offset or (e.offset or 1) + 1, "m": _syntax_de(msg), "s": "error"})
        return json.dumps(diags)
    except Exception:
        return "[]"
    try:
        from pyflakes import checker
    except ImportError:
        return json.dumps(diags)
    try:
        w = checker.Checker(tree, filename=path)
    except Exception:
        return json.dumps(diags)
    for m in w.messages:
        name = type(m).__name__
        if name in _IGNORE_FLAKES:
            continue
        try:
            text = (_MSG_DE.get(name) or m.message) % m.message_args
        except Exception:
            text = m.message % m.message_args
        if name == "UndefinedName" and m.message_args and m.message_args[0] in ("__file__",):
            continue
        diags.append({"l": m.lineno, "c": (getattr(m, "col", 0) or 0) + 1, "m": text,
                      "s": "error" if name in _ERROR_FLAKES else "warning"})
    return json.dumps(diags)


def _syntax_de(msg):
    table = [
        ("invalid syntax", "Ungültige Syntax"),
        ("expected ':'", "Hier fehlt ein Doppelpunkt ':'"),
        ("unexpected indent", "Unerwartete Einrückung"),
        ("expected an indented block", "Hier wird ein eingerückter Block erwartet"),
        ("unindent does not match any outer indentation level", "Die Einrückung passt zu keiner äußeren Ebene"),
        ("unterminated string literal", "Zeichenkette nicht geschlossen"),
        ("was never closed", "Klammer wurde nie geschlossen"),
        ("unmatched", "Klammer ohne Gegenstück"),
        ("EOL while scanning string literal", "Zeichenkette nicht geschlossen"),
    ]
    for en, de in table:
        if en in msg:
            return "%s (%s)" % (de, msg)
    return msg


def format_code(code):
    try:
        import black
    except ImportError:
        return json.dumps({"error": "missing"})
    try:
        out = black.format_str(code, mode=black.Mode(line_length=88))
        return json.dumps({"code": out})
    except Exception as e:
        return json.dumps({"error": str(e).split("\n")[0]})


def outline(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "[]"
    out = []

    def walk(nodes, depth):
        for n in nodes:
            if isinstance(n, ast.ClassDef):
                out.append({"n": n.name, "k": "class", "l": n.lineno, "d": depth})
                walk(n.body, depth + 1)
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in n.args.args]
                out.append({"n": "%s(%s)" % (n.name, ", ".join(args)), "k": "def", "l": n.lineno, "d": depth})
            elif depth == 0 and isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name) and t.id.isupper():
                        out.append({"n": t.id, "k": "const", "l": n.lineno, "d": depth})
            elif depth == 0 and isinstance(n, ast.If):
                try:
                    if "__main__" in ast.unparse(n.test):
                        out.append({"n": "if __name__ == '__main__'", "k": "main", "l": n.lineno, "d": 0})
                except Exception:
                    pass
    walk(tree.body, 0)
    return json.dumps(out)


def _local_module_files(roots, parts):
    """Dateien im Projekt, die zu einem Modulnamen gehoeren (oder leer)."""
    for root in roots:
        files = []
        for i in range(1, len(parts) + 1):
            p = os.path.join(root, *parts[:i])
            if os.path.isfile(p + ".py"):
                files.append(p + ".py")
                return files
            init = os.path.join(p, "__init__.py")
            if os.path.isdir(p):
                if os.path.isfile(init):
                    files.append(init)
                continue
            break
        if files:
            return files
    return []


def needed_imports(project_dir, entry_rel):
    """Externe Pakete, die die Startdatei (und ihre lokalen Module) importieren."""
    entry = os.path.join(project_dir, entry_rel)
    roots = [os.path.dirname(entry), project_dir]
    seen, external, queue = set(), set(), [entry]
    while queue:
        path = queue.pop()
        if path in seen:
            continue
        seen.add(path)
        try:
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except Exception:
            continue
        here = os.path.dirname(path)
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                names = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom):
                if n.level:
                    base = here
                    for _ in range(n.level - 1):
                        base = os.path.dirname(base)
                    mod = (n.module or "").split(".") if n.module else []
                    queue.extend(_local_module_files([base], mod) if mod else [])
                    for a in n.names:
                        queue.extend(_local_module_files([base], mod + [a.name]))
                    continue
                if not n.module:
                    continue
                names = [n.module] + [n.module + "." + a.name for a in n.names]
            else:
                continue
            for name in names:
                parts = name.split(".")
                local = _local_module_files(roots, parts)
                if local:
                    queue.extend(local)
                elif name.count(".") == 0 or not _local_module_files(roots, parts[:1]):
                    external.add(parts[0])
    return json.dumps(sorted(external))


def imports_of(code):
    """Top-Level-Paketnamen, die ein Skript importiert."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "[]"
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                names.add(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            names.add(n.module.split(".")[0])
    return json.dumps(sorted(names))

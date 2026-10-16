"""Packt die Python-Hilfsdateien (py/) in py-bundle.json, die der Worker laedt.

Aufruf:  python3 tools/build_bundle.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "py")
OUT = os.path.join(ROOT, "py-bundle.json")

files = {}
for dirpath, dirnames, filenames in os.walk(SRC):
    dirnames[:] = [d for d in dirnames if d != "__pycache__"]
    for fn in sorted(filenames):
        if not fn.endswith(".py"):
            continue
        full = os.path.join(dirpath, fn)
        rel = os.path.relpath(full, SRC).replace(os.sep, "/")
        with open(full, encoding="utf-8") as f:
            files[rel] = f.read()

with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"files": files}, f, ensure_ascii=False, separators=(",", ":"))
print(f"{len(files)} Dateien -> {OUT} ({os.path.getsize(OUT) // 1024} KB)")

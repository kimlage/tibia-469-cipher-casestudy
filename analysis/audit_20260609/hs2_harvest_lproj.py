#!/usr/bin/env python3
"""Harvest real DE/PL/PT (and EN reference) text from local macOS localization
.strings files (binary or text plists). Local data only - no network."""
import os, plistlib, re, sys, json

ROOTS = ["/System/Library", "/Applications"]
LANGS = {"de": ["de.lproj"], "pl": ["pl.lproj"], "pt": ["pt.lproj", "pt_PT.lproj", "pt-PT.lproj", "pt_BR.lproj", "pt-BR.lproj"]}
OUT = "./tmp/audit_20260609"

MAXFILES = 4000
collected = {k: [] for k in LANGS}
seen = {k: set() for k in LANGS}
counts = {k: 0 for k in LANGS}

def lang_of(path):
    for lg, names in LANGS.items():
        for nm in names:
            if os.sep + nm + os.sep in path:
                return lg
    return None

nfiles = 0
for root in ROOTS:
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # prune: only descend into dirs likely to hold lproj
        if ".lproj" in dirpath and lang_of(dirpath + os.sep) is None:
            dirnames[:] = []
            continue
        lg = lang_of(dirpath + os.sep)
        if lg is None:
            continue
        for fn in filenames:
            if not fn.endswith(".strings"):
                continue
            p = os.path.join(dirpath, fn)
            nfiles += 1
            if nfiles > MAXFILES:
                break
            try:
                with open(p, "rb") as f:
                    data = f.read()
                if data[:6] == b"bplist":
                    d = plistlib.loads(data)
                    vals = [v for v in d.values() if isinstance(v, str)]
                else:
                    txt = data.decode("utf-16") if data[:2] in (b"\xff\xfe", b"\xfe\xff") else data.decode("utf-8", "ignore")
                    vals = re.findall(r'=\s*"((?:[^"\\]|\\.)*)"\s*;', txt)
            except Exception:
                continue
            for v in vals:
                v = v.strip()
                if len(v) < 12 or "%" in v or v in seen[lg]:
                    continue
                seen[lg].add(v)
                collected[lg].append(v)
                counts[lg] += len(v)
        if nfiles > MAXFILES:
            break
    if nfiles > MAXFILES:
        break

print("files scanned:", nfiles)
for lg in LANGS:
    print(lg, "strings:", len(collected[lg]), "chars:", counts[lg])
json.dump(collected, open(f"{OUT}/lproj_harvest.json", "w"))
print("WROTE lproj_harvest.json")

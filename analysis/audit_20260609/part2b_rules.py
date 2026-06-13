#!/usr/bin/env python3
"""Part 2b: how functional is omit/retain in coarser feature subsets?
For each subset: in-sample max accuracy of any rule on those features (on 50
pathcount=1 books) AND honest LOBO accuracy of the lookup-table rule
(fallback = per-code majority, then global majority)."""
import json
from collections import Counter, defaultdict
import numpy as np

occ = json.load(open('./tmp/audit_20260609/occurrences.json'))
data = [o for o in occ if o['pc'] == 1]
print("n =", len(data))

SUBSETS = {
    'x': ('x',),
    'x,prev': ('x', 'prev'),
    'x,prev,start': ('x', 'prev', 'start'),
    'x,prev,nxt': ('x', 'prev', 'nxt'),
    'x,wpar': ('x', 'wpar'),
    'prev': ('prev',),
    'x,prev,wpar': ('x', 'prev', 'wpar'),
    'x,prev,mod2': ('x', 'prev', 'mod2'),
    'x,nxt': ('x', 'nxt'),
    'full': ('x', 'prev', 'nxt', 'mod2', 'mod3', 'wpar', 'start'),
}

def key(o, fs):
    return tuple(o[f] for f in fs)

books = sorted(set(o['book'] for o in data))
glob_major = int(sum(o['omitted'] for o in data) * 2 > len(data))

print(f"{'subset':16s} {'#sig':>5s} {'maxacc_in':>9s} {'LOBO_table':>10s}")
for name, fs in SUBSETS.items():
    labs = defaultdict(Counter)
    for o in data:
        labs[key(o, fs)][o['omitted']] += 1
    maxacc = sum(max(c.values()) for c in labs.values()) / len(data)
    # LOBO lookup table
    correct = 0
    for b in books:
        tr = [o for o in data if o['book'] != b]
        te = [o for o in data if o['book'] == b]
        tab = defaultdict(Counter)
        codetab = defaultdict(Counter)
        for o in tr:
            tab[key(o, fs)][o['omitted']] += 1
            codetab[o['x']][o['omitted']] += 1
        for o in te:
            k = key(o, fs)
            if k in tab:
                pred = tab[k].most_common(1)[0][0]
            elif o['x'] in codetab:
                pred = codetab[o['x']].most_common(1)[0][0]
            else:
                pred = glob_major
            correct += pred == o['omitted']
    print(f"{name:16s} {len(labs):5d} {maxacc:9.4f} {correct/len(data):10.4f}")

# the single contradictory full signature
labs = defaultdict(list)
for o in data:
    labs[key(o, SUBSETS['full'])].append(o)
for k, os_ in labs.items():
    s = set(o['omitted'] for o in os_)
    if len(s) == 2:
        print("\ncontradictory full signature:", k, "occurrences:")
        for o in os_:
            print("  ", o['book'], "t=", o['t'], "code", o['c'], "omitted", o['omitted'])

# wpar marginal
for w in (0, 1):
    sel = [o['omitted'] for o in data if o['wpar'] == w]
    print(f"wpar={w}: {sum(sel)}/{len(sel)} = {sum(sel)/len(sel):.3f}")
# per-code rates on the 50 books
print("\nper-code omit rates (50 books):")
for c in sorted(set(o['c'] for o in data)):
    sel = [o['omitted'] for o in data if o['c'] == c]
    print(f"  {c}: {sum(sel)}/{len(sel)} = {sum(sel)/len(sel):.3f}")

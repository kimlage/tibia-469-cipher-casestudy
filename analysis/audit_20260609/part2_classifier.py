#!/usr/bin/env python3
"""Part 2: predict omit/retain per 0X occurrence on the 50 pathcount=1 books.
Leave-one-book-out CV. Features: code value, prev written digit, next written
digit, code position mod 2/3, written-offset parity, book-start flag.
"""
import sqlite3, json
import numpy as np
from collections import Counter

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()
cur.execute("SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1")
SYM = dict(cur.fetchall()); print("codes:", len(SYM))

cur.execute("""SELECT bookid, digits, CAST(insertedzeros AS INT), decodedbase
               FROM sheet__books GROUP BY bookid""")
books = {b: (d, iz, base) for b, d, iz, base in cur.fetchall()}
print("books:", len(books))

cur.execute("SELECT bookid, pathcount FROM row0_omission_probe_book_items WHERE run_id=1")
pathcount = dict(cur.fetchall())

cur.execute("""SELECT bookid, omitted_positions_json, reconstructed_code_stream
               FROM row0_code_symbol_probe_books WHERE run_id=1""")
probe = {b: (set(json.loads(o)), cs.split()) for b, o, cs in cur.fetchall()}
print("probe books:", len(probe))

# Build occurrence table for ALL books (flag pathcount); written-stream offsets
occ = []  # dicts
for bookid, (digits, iz, base) in books.items():
    omit, codes = probe[bookid]
    i = 0  # written offset
    for t, c in enumerate(codes, start=1):
        omitted = t in omit
        wlen = 1 if omitted else 2
        if c[0] == '0':
            prev = digits[i-1] if i > 0 else 'S'
            nxt = digits[i+wlen] if i + wlen < len(digits) else 'E'
            occ.append(dict(book=bookid, t=t, c=c, x=c[1], omitted=int(omitted),
                            prev=prev, nxt=nxt, mod2=t % 2, mod3=t % 3,
                            wpar=i % 2, start=int(t == 1), pc=pathcount[bookid]))
        i += wlen
    assert i == len(digits), bookid

print("total 0X occurrences (all 70 books):", len(occ))
print("omitted:", sum(o['omitted'] for o in occ), "retained:", sum(1-o['omitted'] for o in occ))

data = [o for o in occ if o['pc'] == 1]
print("occurrences on 50 pathcount=1 books:", len(data),
      "omitted:", sum(o['omitted'] for o in data))

# sanity: marginal signals from the brief
def rate(sel):
    s = [o['omitted'] for o in sel]
    return (sum(s), len(s), sum(s)/len(s) if s else float('nan'))
print("after prev='1':", rate([o for o in occ if o['prev']=='1']))
print("after prev='8':", rate([o for o in occ if o['prev']=='8']))
print("book-start:", rate([o for o in occ if o['start']==1]))
print("code 07:", rate([o for o in occ if o['c']=='07']))
print("code 02:", rate([o for o in occ if o['c']=='02']))

# encode features
PREV_VALS = ['S'] + [str(d) for d in range(10)]
NXT_VALS = ['E'] + [str(d) for d in range(10)]
def feats(o):
    v = []
    v += [1 if o['x'] == str(d) else 0 for d in range(10)]
    v += [1 if o['prev'] == p else 0 for p in PREV_VALS]
    v += [1 if o['nxt'] == p else 0 for p in NXT_VALS]
    v += [o['mod2'], o['mod3'] == 0, o['mod3'] == 1, o['wpar'], o['start']]
    return [float(x) for x in v]

X = np.array([feats(o) for o in data])
y = np.array([o['omitted'] for o in data])
groups = np.array([o['book'] for o in data])

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier

def lobo(model_fn):
    correct = 0
    for b in np.unique(groups):
        tr, te = groups != b, groups == b
        m = model_fn()
        m.fit(X[tr], y[tr])
        correct += (m.predict(X[te]) == y[te]).sum()
    return correct / len(y)

# baselines
# majority class
maj = max(Counter(y).items(), key=lambda kv: kv[1])
print(f"\nmajority-class baseline: {maj[1]/len(y):.4f} (predict {maj[0]})")
# per-code majority, leave-one-book-out
correct = 0
for b in np.unique(groups):
    tr = [o for o in data if o['book'] != b]
    te = [o for o in data if o['book'] == b]
    bycode = {}
    for c in set(o['c'] for o in data):
        sel = [o['omitted'] for o in tr if o['c'] == c]
        bycode[c] = int(sum(sel) * 2 > len(sel)) if sel else 0
    correct += sum(1 for o in te if bycode[o['c']] == o['omitted'])
print(f"per-code-majority LOBO baseline: {correct/len(y):.4f}")

accs = {}
accs['logreg'] = lobo(lambda: LogisticRegression(max_iter=2000, C=1.0))
accs['tree_d4'] = lobo(lambda: DecisionTreeClassifier(max_depth=4, random_state=0))
accs['tree_d8'] = lobo(lambda: DecisionTreeClassifier(max_depth=8, random_state=0))
accs['gbm'] = lobo(lambda: GradientBoostingClassifier(random_state=0))
accs['rf'] = lobo(lambda: RandomForestClassifier(n_estimators=300, random_state=0))
for k, v in accs.items():
    print(f"LOBO accuracy {k}: {v:.4f}")

# full-data in-sample fit (upper bound on deterministic rule with these features)
m = GradientBoostingClassifier(random_state=0).fit(X, y)
ins = (m.predict(X) == y).mean()
print(f"in-sample GBM accuracy (overfit bound): {ins:.4f}")
# check: is the mapping (features)->label even a function? count contradictions
sig = Counter()
lab = {}
contra = 0
for o in data:
    key = (o['x'], o['prev'], o['nxt'], o['mod2'], o['mod3'], o['wpar'], o['start'])
    if key in lab and lab[key] != o['omitted']:
        contra += 1
    lab.setdefault(key, o['omitted'])
    sig[key] += 1
# proper contradiction count: distinct keys with both labels
both = 0; nocc = 0
labs = {}
for o in data:
    key = (o['x'], o['prev'], o['nxt'], o['mod2'], o['mod3'], o['wpar'], o['start'])
    labs.setdefault(key, set()).add(o['omitted'])
for k, s in labs.items():
    if len(s) == 2:
        both += 1
        nocc += sig[k]
print(f"feature signatures: {len(labs)} total; {both} carry BOTH labels, covering {nocc} occurrences")
maxfit = 0
for k, s in labs.items():
    if len(s) == 2:
        cnt = Counter(o['omitted'] for o in data if (o['x'],o['prev'],o['nxt'],o['mod2'],o['mod3'],o['wpar'],o['start'])==k)
        maxfit += max(cnt.values())
    else:
        maxfit += sig[k]
print(f"max possible accuracy of ANY deterministic rule on these features (in-sample): {maxfit/len(y):.4f}")

# save occurrence table for part 3
with open('./tmp/audit_20260609/occurrences.json', 'w') as f:
    json.dump(occ, f)
print("saved occurrences.json")

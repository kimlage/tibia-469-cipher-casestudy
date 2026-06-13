#!/usr/bin/env python3
"""Part 2: Is omit/retain a deterministic context rule?
Leave-one-book-out CV on the 50 pathcount=1 books (unambiguous labels).
Models: per-code majority, decision trees, gradient boosting, logistic.
Permutation control: labels shuffled within code class.
"""
import json, numpy as np
from collections import defaultdict
from scipy.stats import chi2_contingency

OUT = "./tmp/audit_20260609"
occ = json.load(open(f"{OUT}/occurrences.json"))
print(f"[load] occurrences = {len(occ)}")

# ---- marginal checks (full 70-book canonical set) ----
by_prev = defaultdict(lambda: [0, 0])
for o in occ:
    by_prev[o["prev"]][o["label"]] += 1
cats = sorted(by_prev)
table = np.array([[by_prev[c][0], by_prev[c][1]] for c in cats])
chi2, pv, dof, _ = chi2_contingency(table)
print(f"[marginal] prev-digit chi2={chi2:.1f} dof={dof} p={pv:.2e}")
for c in cats:
    r, m = by_prev[c][0], by_prev[c][1]
    print(f"   prev={c}: omitted {m}/{m+r} = {m/(m+r):.2f}")
bs = [(o["label"]) for o in occ if o["bookstart"]]
print(f"[marginal] book-start occurrences: {len(bs)}, omitted frac = {np.mean(bs):.2f}")
by_code = defaultdict(lambda: [0, 0])
for o in occ:
    by_code[o["code"]][o["label"]] += 1
for c in sorted(by_code):
    r, m = by_code[c][0], by_code[c][1]
    print(f"   code={c}: omitted {m}/{m+r} = {m/(m+r):.2f}")

# ---- build clean dataset: pathcount==1 books ----
clean = [o for o in occ if o["pathcount"] == 1]
books = sorted(set(o["bookid"] for o in clean), key=int)
print(f"\n[clean] occurrences={len(clean)} books={len(books)} omitted={sum(o['label'] for o in clean)}")

CAT = ["code", "prev", "next_first"]
NUM = ["next_is0X", "imod2", "imod3", "pmod2", "bookstart", "relpos"]
cat_levels = {f: sorted(set(o[f] for o in clean)) for f in CAT}

def featurize(data):
    X = []
    for o in data:
        row = []
        for f in CAT:
            row += [1.0 if o[f] == lv else 0.0 for lv in cat_levels[f]]
        row += [float(o[f]) for f in NUM]
        X.append(row)
    return np.array(X)

X = featurize(clean)
y = np.array([o["label"] for o in clean])
g = np.array([o["bookid"] for o in clean])
print(f"[features] X shape = {X.shape}")

from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression

def lobo_acc(model_fn, X, y, g, books):
    correct = 0
    for b in books:
        tr, te = g != b, g == b
        if te.sum() == 0:
            continue
        if len(set(y[tr])) == 1:
            pred = np.full(te.sum(), y[tr][0])
        else:
            m = model_fn()
            m.fit(X[tr], y[tr])
            pred = m.predict(X[te])
        correct += (pred == y[te]).sum()
    return correct / len(y)

def percode_majority_acc(data, books):
    correct = 0
    for b in books:
        tr = [o for o in data if o["bookid"] != b]
        te = [o for o in data if o["bookid"] == b]
        maj = {}
        cnt = defaultdict(lambda: [0, 0])
        for o in tr:
            cnt[o["code"]][o["label"]] += 1
        glob = int(sum(o["label"] for o in tr) * 2 > len(tr))
        for c, (r, m) in cnt.items():
            maj[c] = int(m > r)
        for o in te:
            pred = maj.get(o["code"], glob)
            correct += pred == o["label"]
    return correct / len(data)

base_majority = max(np.mean(y), 1 - np.mean(y))
print(f"\n[baseline] global majority class accuracy = {base_majority:.4f}")
acc_pc = percode_majority_acc(clean, books)
print(f"[baseline] per-code majority LOBO accuracy = {acc_pc:.4f}")

models = {
    "tree_d3": lambda: DecisionTreeClassifier(max_depth=3, random_state=0),
    "tree_d5": lambda: DecisionTreeClassifier(max_depth=5, random_state=0),
    "tree_full": lambda: DecisionTreeClassifier(random_state=0),
    "rf200": lambda: RandomForestClassifier(n_estimators=200, random_state=0, n_jobs=-1),
    "hgb": lambda: HistGradientBoostingClassifier(random_state=0),
    "logreg": lambda: LogisticRegression(max_iter=2000, C=1.0),
}
accs = {}
for name, fn in models.items():
    accs[name] = lobo_acc(fn, X, y, g, books)
    print(f"[model] {name}: LOBO accuracy = {accs[name]:.4f}")
best_name = max(accs, key=accs.get)
best_acc = accs[best_name]
print(f"\n[RESULT] best held-out accuracy = {best_acc:.4f} ({best_name}); threshold for deterministic rule = 0.95")

# permutation control: shuffle labels within code class, redo LOBO with best model + per-code baseline delta
rng = np.random.default_rng(469)
code_arr = np.array([o["code"] for o in clean])
nperm = 200
perm_accs = []
fn = models[best_name]
for it in range(nperm):
    yp = y.copy()
    for c in np.unique(code_arr):
        idx = np.where(code_arr == c)[0]
        yp[idx] = rng.permutation(yp[idx])
    perm_accs.append(lobo_acc(fn, X, yp, g, books))
perm_accs = np.array(perm_accs)
z = (best_acc - perm_accs.mean()) / perm_accs.std()
pgt = (perm_accs >= best_acc).mean()
print(f"[control] within-code label permutation (n={nperm}): mean={perm_accs.mean():.4f} sd={perm_accs.std():.4f} max={perm_accs.max():.4f}")
print(f"[control] real best acc z = {z:.2f}, empirical p = {pgt:.4f} ({(perm_accs >= best_acc).sum()}/{nperm})")

# inspect the fitted tree on full clean data for interpretability
from sklearn.tree import export_text
feat_names = []
for f in CAT:
    feat_names += [f"{f}={lv}" for lv in cat_levels[f]]
feat_names += NUM
t = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X, y)
print("\n[tree_d3 rules on full clean data]")
print(export_text(t, feature_names=feat_names))
in_acc = t.score(X, y)
print(f"[tree_d3 in-sample accuracy] {in_acc:.4f}")
t5 = DecisionTreeClassifier(max_depth=5, random_state=0).fit(X, y)
print(f"[tree_d5 in-sample accuracy] {t5.score(X, y):.4f}")
tf = DecisionTreeClassifier(random_state=0).fit(X, y)
print(f"[tree_full in-sample accuracy] {tf.score(X, y):.4f} (leaves={tf.get_n_leaves()})")

json.dump(dict(accs=accs, best=best_name, best_acc=best_acc, percode=acc_pc,
               perm_mean=float(perm_accs.mean()), perm_sd=float(perm_accs.std()),
               perm_p=float(pgt), z=float(z)), open(f"{OUT}/classifier_results.json", "w"))
print("[saved] classifier_results.json")

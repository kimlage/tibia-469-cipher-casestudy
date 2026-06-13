#!/usr/bin/env python3
"""Post-hoc leakage adjudication for the split-half homophonic solve.

Question: does the learned 99->26 map transfer to held-out code contexts the
solver never saw, or only to shared/repeated code n-grams and code-frequency
(Zipf) structure?

For each learned assignment:
  z_all    = held z on all real windows (as in hs4)
  z_novel4 = held z restricted to windows whose code 4-gram does NOT occur
             anywhere in the training stream (pure out-of-sample contexts)
Null: 1000 permutations of the learned letter multiset over the 99 codes.
Also: letter concentration of decrypts, distinct letters used.
Synthetic-EN reference: same restriction on a freshly built (seeded) synthetic
homophonic cipher of Alice -> shows genuine language retains z under the
novel-window restriction.
"""
import json, math, random, sys
import numpy as np

OUT = "./tmp/audit_20260609"
sys.argv = ["x", "none"]
src = open(f"{OUT}/hs4_protocol.py").read()
exec(src)  # mode='none': defines everything, runs no phase

# re-derive the real-phase assignments (solver is fully seeded/deterministic,
# identical params to run_real in hs4: seed=SEED+11, R_RESTARTS, SA_STEPS)
res = {}
for key, lang, pins in (("real_en_free", "en", None), ("real_en_pinned", "en", PINS),
                        ("real_de_free", "de", None), ("real_de_pinned", "de", PINS),
                        ("real_pl_free", "pl", None), ("real_pt_free", "pt", None)):
    a, tot = solve(train_stream, lm[lang], pins=pins, seed=SEED + 11, tag=key)
    res[key] = {"assign": [int(x) for x in a], "train_total": tot}
    print(f"rederived {key} train_mean={tot/train_stream.nwin_real:.4f}", flush=True)

# train 4-gram (code-level) set, real windows only
def real_window_starts(st):
    ws = []
    for s in range(st.L - 3):
        if not st.is_sent[s:s + 4].any():
            ws.append(s)
    return np.array(ws, dtype=np.int64)

tr_ws = real_window_starts(train_stream)
tr_4g = {tuple(train_stream.code[s:s + 4]) for s in tr_ws}
he_ws = real_window_starts(held_stream)
he_novel = np.array([s for s in he_ws
                     if tuple(held_stream.code[s:s + 4]) not in tr_4g], dtype=np.int64)
print(f"held real windows {len(he_ws)}, novel-4gram windows {len(he_novel)} "
      f"({len(he_novel)/len(he_ws):.1%})", flush=True)

def z_restricted(st, T, assign, ws, draws=1000, seed=5):
    def sc(a):
        d = st.decrypt(a)
        return float(T[d[ws], d[ws + 1], d[ws + 2], d[ws + 3]].sum())
    obs = sc(assign)
    rng = np.random.default_rng(seed)
    nulls = np.array([sc(rng.permutation(assign)) for _ in range(draws)])
    z = (obs - nulls.mean()) / nulls.std()
    return obs, nulls.mean(), nulls.std(), z, float((nulls >= obs).mean())

def letter_stats(st, assign):
    m = ~st.is_sent
    letts = assign[st.code[m]]
    cnt = np.bincount(letts, minlength=26).astype(float)
    p = cnt / cnt.sum()
    ent = -np.sum(p[p > 0] * np.log2(p[p > 0]))
    top = "".join(chr(97 + i) for i in np.argsort(-cnt)[:6])
    return len(np.unique(letts)), ent, top

summary = {}
for key, lang in (("real_en_free", "en"), ("real_en_pinned", "en"),
                  ("real_de_free", "de"), ("real_de_pinned", "de"),
                  ("real_pl_free", "pl"), ("real_pt_free", "pt")):
    if key not in res:
        continue
    assign = np.array(res[key]["assign"], dtype=np.int64)
    T = lm[lang]
    oa, ma, sa_, za, pa = z_restricted(held_stream, T, assign, he_ws, seed=5)
    on, mn, sn, zn, pn = z_restricted(held_stream, T, assign, he_novel, seed=6)
    nl, ent, top = letter_stats(train_stream, assign)
    print(f"{key}: z_all={za:.2f} (p={pa:.4f})  z_novel4={zn:.2f} (p={pn:.4f}) "
          f"mean_novel={on/len(he_novel):.4f} | letters={nl} H={ent:.2f} top={top}",
          flush=True)
    summary[key] = {"z_all": za, "p_all": pa, "z_novel4": zn, "p_novel4": pn,
                    "novel_windows": int(len(he_novel)),
                    "letters_used": int(nl), "letter_entropy_bits": float(ent),
                    "top_letters": top}

# --- synthetic-EN reference with fixed seed, same restriction ---
ctrl = json.load(open(f"{OUT}/hs_control_plaintexts.json"))
rng = random.Random(777)
Tn, Hn = train_stream.nwin_real + 3, held_stream.nwin_real + 3
plain = ctrl["en"][:Tn + Hn]
cipher, truth = make_homophonic(plain, NC, rng)
tr, he = cipher[:Tn], cipher[Tn:]
st_tr, st_he = Stream([tr]), Stream([he])
T = lm["en"]
assign, tot = solve(st_tr, T, restarts=16, steps=SA_STEPS, seed=778, tag="SYN-REF")
m = ~st_he.is_sent
acc = float((assign[st_he.code[m]] == truth[st_he.code[m]]).mean())
s_ws = real_window_starts(st_he)
s_tr4 = {tuple(st_tr.code[s:s + 4]) for s in real_window_starts(st_tr)}
s_nov = np.array([s for s in s_ws if tuple(st_he.code[s:s + 4]) not in s_tr4],
                 dtype=np.int64)
oa, ma, sa_, za, pa = z_restricted(st_he, T, assign, s_ws, seed=7)
on, mn, sn, zn, pn = z_restricted(st_he, T, assign, s_nov, seed=8)
print(f"SYN-REF: held_acc={acc:.3f} z_all={za:.2f} z_novel4={zn:.2f} "
      f"novel_windows={len(s_nov)}/{len(s_ws)}", flush=True)
summary["synth_en_ref"] = {"held_acc": acc, "z_all": za, "z_novel4": zn,
                           "novel_windows": int(len(s_nov)),
                           "total_windows": int(len(s_ws))}

json.dump(summary, open(f"{OUT}/hs_leakage.json", "w"), indent=1)
print("DONE", flush=True)

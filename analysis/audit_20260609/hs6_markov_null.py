#!/usr/bin/env python3
"""Non-linguistic structured control: does generic low-order CODE structure
(no language at all) reproduce the held-out z of 5-8 seen on the real corpus?

Generate train/held-sized streams from a code-level order-1 Markov chain
fitted on the real train stream (definitely not language; preserves code
bigram statistics only). Run the IDENTICAL pipeline: SA solve with EN LM on
the Markov 'train' stream, score the Markov 'held' stream, 1000
multiset-permutation null. Repeat 3 seeds.

If z >> 3 here, the real-data held z of 5-8 is fully consistent with
non-linguistic code-level structure and cannot count as evidence of language.
"""
import json, random, sys
import numpy as np

OUT = "./tmp/audit_20260609"
sys.argv = ["x", "none"]
exec(open(f"{OUT}/hs4_protocol.py").read())

# fit order-1 Markov on train stream (real transitions only, within fragments)
M = np.ones((NC, NC)) * 0.1  # smoothing
start = np.ones(NC) * 0.1
for f in train_frags_tok:
    ids = [code2i[t] for t in f]
    start[ids[0]] += 1
    for a, b in zip(ids, ids[1:]):
        M[a, b] += 1
Mp = M / M.sum(1, keepdims=True)
sp = start / start.sum()

def gen(n, rng):
    out = [int(rng.choice(NC, p=sp))]
    for _ in range(n - 1):
        out.append(int(rng.choice(NC, p=Mp[out[-1]])))
    return out

Tn, Hn = train_stream.nwin_real + 3, held_stream.nwin_real + 3
summary = {}
for s in (101, 202, 303):
    rng = np.random.default_rng(s)
    tr, he = gen(Tn, rng), gen(Hn, rng)
    st_tr, st_he = Stream([tr]), Stream([he])
    T = lm["en"]
    assign, tot = solve(st_tr, T, restarts=R_RESTARTS, steps=SA_STEPS,
                        seed=s, tag=f"MKV-{s}")
    obs, mu, sd, z, p = held_z(st_he, T, assign, seed=s + 1)
    txt = to_text(st_tr, assign)[:160]
    print(f"[MKV-{s}] train_mean={tot/st_tr.nwin_real:.4f} held z={z:.2f} "
          f"p={p:.4f}", flush=True)
    print(f"[MKV-{s}] train decrypt: {txt}", flush=True)
    summary[f"markov_{s}"] = {"train_mean": tot / st_tr.nwin_real,
                              "z": z, "p": p, "sample": txt}
json.dump(summary, open(f"{OUT}/hs_markov_null.json", "w"), indent=1)
print("DONE", flush=True)

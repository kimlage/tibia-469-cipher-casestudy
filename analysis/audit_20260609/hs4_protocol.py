#!/usr/bin/env python3
"""Internal homophonic solve (99 codes -> 26 letters) with split-half held-out
validation, shuffle control, and synthetic solvable control.

Protocol (pre-registered):
  1. Split 70 books 35/35 (seed 469). Dedupe train half (containment + >=10-token
     affix merge, same as full-corpus dedupe). Extract held-out NOVEL stream:
     positions not covered by any >=12-token module shared with the train half,
     internally deduped (first occurrence kept).
  2. SA homophonic solver (single-code reassign + code-pair letter swap moves,
     adaptive T), scored by interpolated char 4-gram LM (EN/DE/PL/PT).
  3. Derive assignment on train stream only; score held-out novel stream;
     null = 1000 permutations of the learned letter multiset over the 99 codes.
  4. Controls: (a) token-shuffled train+held streams; (b) synthetic flattening
     homophonic ciphers of real EN (Alice, excluded from LM) and DE (composed
     CONTROL_DE, excluded from LM), length-matched, identical pipeline,
     with true-key accuracy. Pipeline must solve (b) or test has no power.
  5. Full-dedup-corpus solves (EN/DE, free + pinned 34=B/78=E/67=A) for
     readability inspection + dictionary-coverage z (EN).
PROMISING requires held-out z>=3 AND readable words. Otherwise NULL_RESULT
provided control (b) is solved.
"""
import json, math, random, sys, time
import numpy as np

OUT = "./tmp/audit_20260609"
A, SENT = 26, 26
MINOV = 10        # dedupe merge overlap (tokens), same as full-corpus dedupe
MASK_L = 12       # held-vs-train module mask length (tokens)
SEED = 469
R_RESTARTS = 24
SA_STEPS = 150000
NULL_DRAWS = 1000

rng_global = random.Random(SEED)

# ---------------- data ----------------
corp = json.load(open(f"{OUT}/hs_corpus.json"))
books = {b: v for b, v in corp["books"].items()}
bids = sorted(books, key=int)
codes_sorted = sorted({t for v in books.values() for t in v})
NC = len(codes_sorted)
code2i = {c: i for i, c in enumerate(codes_sorted)}
print("codes", NC, "books", len(bids), flush=True)

PINS_CODES = {"34": "b", "78": "e", "67": "a"}
PINS = {code2i[c]: ord(l) - 97 for c, l in PINS_CODES.items()}

# ---------------- dedupe helpers (same logic as hs1) ----------------
def contains(big, small):
    n, m = len(big), len(small)
    for i in range(n - m + 1):
        if big[i:i + m] == small:
            return True
    return False

def assemble(book_ids):
    frags = sorted([(b, tuple(books[b])) for b in book_ids], key=lambda x: -len(x[1]))
    kept = []
    for bid, t in frags:
        if any(contains(kt, t) for _, kt in [(k[0], k[1]) for k in kept]):
            continue
        kept.append([[bid], t])
    def best_overlap(a, b):
        mx = min(len(a), len(b))
        for L in range(mx, MINOV - 1, -1):
            if a[-L:] == b[:L]:
                return L
        return 0
    changed = True
    while changed:
        changed = False
        best = (0, -1, -1)
        for i in range(len(kept)):
            for j in range(len(kept)):
                if i == j: continue
                ov = best_overlap(kept[i][1], kept[j][1])
                if ov > best[0]:
                    best = (ov, i, j)
        if best[0] >= MINOV:
            ov, i, j = best
            merged = kept[i][1] + kept[j][1][ov:]
            ids = kept[i][0] + kept[j][0]
            for a_ in sorted((i, j), reverse=True):
                kept.pop(a_)
            kept.append([ids, merged])
            changed = True
    return [list(k[1]) for k in kept]

# ---------------- split ----------------
perm = bids[:]
rng_global.shuffle(perm)
train_books, held_books = sorted(perm[:35], key=int), sorted(perm[35:], key=int)
print("train_books", train_books, flush=True)
print("held_books", held_books, flush=True)

train_frags_tok = assemble(train_books)
train_tok_count = sum(len(f) for f in train_frags_tok)
print("train frags", len(train_frags_tok), "tokens", train_tok_count, flush=True)

# held-out novel extraction
def ngrams_of(seq, L):
    return {tuple(seq[i:i + L]) for i in range(len(seq) - L + 1)}

train_ngrams = set()
for f in train_frags_tok:
    train_ngrams |= ngrams_of(f, MASK_L)

held_novel_frags = []
seen_held = set()
shared_tok = novel_tok = 0
for b in held_books:
    seq = books[b]
    n = len(seq)
    cover = [False] * n
    for i in range(n - MASK_L + 1):
        t = tuple(seq[i:i + MASK_L])
        if t in train_ngrams or t in seen_held:
            for j in range(i, i + MASK_L):
                cover[j] = True
    seen_held |= ngrams_of(seq, MASK_L)
    i = 0
    while i < n:
        if not cover[i]:
            j = i
            while j < n and not cover[j]:
                j += 1
            if j - i >= 4:
                held_novel_frags.append(seq[i:j])
                novel_tok += j - i
            i = j
        else:
            shared_tok += 1
            i += 1
print("held novel frags", len(held_novel_frags), "novel tokens", novel_tok,
      "masked tokens", shared_tok, flush=True)

# full-corpus dedup fragments (from hs1)
full_frags_tok = [f["tokens"] for f in corp["fragments"]]
full_tok_count = sum(len(f) for f in full_frags_tok)

# ---------------- stream construction ----------------
class Stream:
    def __init__(self, frags_codes):
        arr = []
        for f in frags_codes:
            arr.extend(code2i[t] if isinstance(t, str) else t for t in f)
            arr.extend([-1, -1, -1])
        arr = arr[:-3] if arr else arr
        self.code = np.array(arr, dtype=np.int64)
        self.L = len(arr)
        self.is_sent = self.code < 0
        self.nwin_real = 0
        for s in range(self.L - 3):
            if not self.is_sent[s:s + 4].any():
                self.nwin_real += 1
        self.pos = [np.where(self.code == c)[0] for c in range(NC)]
        self.W = []
        for c in range(NC):
            ws = set()
            for p in self.pos[c]:
                for s in range(max(0, p - 3), min(self.L - 4, p) + 1):
                    ws.add(s)
            self.W.append(np.array(sorted(ws), dtype=np.int64))
        self.counts = np.array([len(p) for p in self.pos], dtype=np.int64)

    def decrypt(self, assign):
        d = np.full(self.L, SENT, dtype=np.int64)
        m = ~self.is_sent
        d[m] = assign[self.code[m]]
        return d

def full_score(T, dec, L):
    if L < 4:
        return 0.0
    return float(T[dec[:-3], dec[1:-2], dec[2:-1], dec[3:]].sum())

# ---------------- SA solver ----------------
def solve(stream, T, restarts=R_RESTARTS, steps=SA_STEPS, pins=None, seed=0,
          tag=""):
    rng = random.Random(seed)
    nprng = np.random.default_rng(seed)
    p1 = lm_p1[id(T)]
    best_assign, best_total = None, -1e18
    for r in range(restarts):
        assign = nprng.choice(A, size=NC, p=p1)
        if pins:
            for c, l in pins.items():
                assign[c] = l
        dec = stream.decrypt(assign)
        total = full_score(T, dec, stream.L)
        # adaptive T0: std of candidate deltas at start
        deltas = []
        for _ in range(120):
            c = rng.randrange(NC)
            if pins and c in pins: continue
            new = rng.randrange(A)
            if new == assign[c]: continue
            w = stream.W[c]
            old_s = float(T[dec[w], dec[w + 1], dec[w + 2], dec[w + 3]].sum())
            dec[stream.pos[c]] = new
            new_s = float(T[dec[w], dec[w + 1], dec[w + 2], dec[w + 3]].sum())
            dec[stream.pos[c]] = assign[c]
            deltas.append(new_s - old_s)
        T0 = max(np.std(deltas), 1.0) if deltas else 5.0
        T1 = T0 / 400.0
        cool = (T1 / T0) ** (1.0 / steps)
        temp = T0
        cur_best_total, cur_best = total, assign.copy()
        for step in range(steps):
            temp *= cool
            if rng.random() < 0.85:
                # single reassignment
                c = rng.randrange(NC)
                if pins and c in pins:
                    continue
                old_l = assign[c]
                new = rng.randrange(A)
                if new == old_l:
                    continue
                w = stream.W[c]
                old_s = float(T[dec[w], dec[w + 1], dec[w + 2], dec[w + 3]].sum())
                dec[stream.pos[c]] = new
                new_s = float(T[dec[w], dec[w + 1], dec[w + 2], dec[w + 3]].sum())
                delta = new_s - old_s
                if delta >= 0 or rng.random() < math.exp(delta / temp):
                    assign[c] = new
                    total += delta
                else:
                    dec[stream.pos[c]] = old_l
            else:
                # swap letters of two codes
                c1 = rng.randrange(NC); c2 = rng.randrange(NC)
                if c1 == c2 or (pins and (c1 in pins or c2 in pins)):
                    continue
                l1, l2 = assign[c1], assign[c2]
                if l1 == l2:
                    continue
                w = np.union1d(stream.W[c1], stream.W[c2])
                old_s = float(T[dec[w], dec[w + 1], dec[w + 2], dec[w + 3]].sum())
                dec[stream.pos[c1]] = l2; dec[stream.pos[c2]] = l1
                new_s = float(T[dec[w], dec[w + 1], dec[w + 2], dec[w + 3]].sum())
                delta = new_s - old_s
                if delta >= 0 or rng.random() < math.exp(delta / temp):
                    assign[c1], assign[c2] = l2, l1
                    total += delta
                else:
                    dec[stream.pos[c1]] = l1; dec[stream.pos[c2]] = l2
            if total > cur_best_total:
                cur_best_total, cur_best = total, assign.copy()
        if cur_best_total > best_total:
            best_total, best_assign = cur_best_total, cur_best.copy()
        print(f"  [{tag}] restart {r}: best_total={cur_best_total:.1f} "
              f"mean={cur_best_total/stream.nwin_real:.4f}", flush=True)
    return best_assign, best_total

# ---------------- held-out validation ----------------
def held_z(stream, T, assign, draws=NULL_DRAWS, seed=1):
    dec = stream.decrypt(assign)
    obs = full_score(T, dec, stream.L)
    nprng = np.random.default_rng(seed)
    nulls = np.empty(draws)
    for i in range(draws):
        a2 = nprng.permutation(assign)
        nulls[i] = full_score(T, stream.decrypt(a2), stream.L)
    mu, sd = nulls.mean(), nulls.std()
    z = (obs - mu) / sd
    p_emp = float((nulls >= obs).mean())
    return obs, mu, sd, z, p_emp

# ---------------- dictionary coverage (EN readability metric) ----------------
WORDS = set()
for w in open("/usr/share/dict/words", encoding="utf-8", errors="ignore"):
    w = w.strip().lower()
    if len(w) >= 3 and w.isalpha():
        WORDS.add(w)

def dict_coverage(letter_str):
    n = len(letter_str)
    best = [0] * (n + 1)
    for i in range(n):
        best[i + 1] = max(best[i + 1], best[i])
        for L in range(3, min(12, n - i) + 1):
            if letter_str[i:i + L] in WORDS:
                best[i + L] = max(best[i + L], best[i] + L)
    return best[n] / max(n, 1)

def to_text(stream, assign):
    d = stream.decrypt(assign)
    return "".join(chr(97 + x) if x < A else "|" for x in d)

# ---------------- LMs ----------------
lm = {}
lm_p1 = {}
for lg in ("en", "de", "pl", "pt"):
    z = np.load(f"{OUT}/hs_lm_{lg}.npz")
    lm[lg] = z["T"]
    lm_p1[id(lm[lg])] = z["p1"]
print("LMs loaded", flush=True)

train_stream = Stream(train_frags_tok)
held_stream = Stream(held_novel_frags)
full_stream = Stream(full_frags_tok)
print("train stream L", train_stream.L, "real windows", train_stream.nwin_real, flush=True)
print("held stream L", held_stream.L, "real windows", held_stream.nwin_real, flush=True)
print("full stream L", full_stream.L, "real windows", full_stream.nwin_real, flush=True)

results = {"meta": {
    "train_books": train_books, "held_books": held_books,
    "train_tokens": int(train_tok_count), "held_novel_tokens": int(novel_tok),
    "held_masked_tokens": int(shared_tok), "mask_L": MASK_L,
    "sa_steps": SA_STEPS, "restarts": R_RESTARTS, "null_draws": NULL_DRAWS}}

mode = sys.argv[1] if len(sys.argv) > 1 else "all"

# =================== PHASE B: synthetic solvable control ===================
def make_homophonic(plain, ncodes, rng):
    letters = sorted(set(plain))
    freq = {l: plain.count(l) / len(plain) for l in letters}
    alloc = {l: max(1, round(freq[l] * ncodes)) for l in letters}
    # largest-remainder fix to total ncodes
    while sum(alloc.values()) > ncodes:
        l = max((l for l in alloc if alloc[l] > 1), key=lambda l: alloc[l] / max(freq[l], 1e-9))
        alloc[l] -= 1
    while sum(alloc.values()) < ncodes:
        l = max(alloc, key=lambda l: freq[l] / alloc[l])
        alloc[l] += 1
    key = {}
    nxt = 0
    for l in letters:
        key[l] = list(range(nxt, nxt + alloc[l]))
        nxt += alloc[l]
    cipher = [rng.choice(key[l]) for l in plain]
    truth = np.full(ncodes, -1, dtype=np.int64)
    for l, cs in key.items():
        for c in cs:
            truth[c] = ord(l) - 97
    return cipher, truth

def synth_control(lang, plain_chars, tag):
    rng = random.Random(SEED + hash(tag) % 1000)
    Tn, Hn = train_stream.nwin_real + 3, held_stream.nwin_real + 3
    need = Tn + Hn
    plain = plain_chars[:need]
    print(f"[{tag}] plaintext len {len(plain)} (want {need})", flush=True)
    cipher, truth = make_homophonic(plain, NC, rng)
    tr = cipher[:min(Tn, len(cipher) * 2 // 3)]
    he = cipher[len(tr):]
    st_tr, st_he = Stream([tr]), Stream([he])
    T = lm[lang]
    assign, tot = solve(st_tr, T, restarts=R_RESTARTS, steps=SA_STEPS,
                        seed=SEED + 7, tag=tag)
    # token-weighted accuracy
    def acc(st):
        m = ~st.is_sent
        cs = st.code[m]
        return float((assign[cs] == truth[cs]).mean())
    obs, mu, sd, z, p = held_z(st_he, T, assign, seed=SEED + 8)
    txt = to_text(st_he, assign)[:200]
    cov = dict_coverage(to_text(st_he, assign).replace("|", "")) if lang == "en" else None
    print(f"[{tag}] train_acc={acc(st_tr):.3f} held_acc={acc(st_he):.3f} "
          f"held z={z:.2f} p={p:.4f} cov={cov}", flush=True)
    print(f"[{tag}] held decrypt: {txt}", flush=True)
    return {"train_acc": acc(st_tr), "held_acc": acc(st_he),
            "held_obs": obs, "null_mu": mu, "null_sd": sd, "z": z, "p": p,
            "dict_cov": cov, "sample": txt,
            "train_len": len(tr), "held_len": len(he)}

if mode in ("all", "synth"):
    ctrl = json.load(open(f"{OUT}/hs_control_plaintexts.json"))
    results["synth_en"] = synth_control("en", ctrl["en"], "SYNTH-EN")
    results["synth_de"] = synth_control("de", ctrl["de"], "SYNTH-DE")
    json.dump(results, open(f"{OUT}/hs_results_partial.json", "w"), indent=1)

# =================== PHASE C: real data, split-half ===================
def run_real(lang, pins, tag):
    T = lm[lang]
    assign, tot = solve(train_stream, T, pins=pins, seed=SEED + 11, tag=tag)
    obs, mu, sd, z, p = held_z(held_stream, T, assign, seed=SEED + 12)
    train_mean = tot / train_stream.nwin_real
    held_mean = obs / held_stream.nwin_real
    txt = to_text(held_stream, assign)[:200]
    fulltxt = to_text(train_stream, assign)
    cov = dict_coverage(fulltxt.replace("|", "")) if lang == "en" else None
    print(f"[{tag}] train_mean={train_mean:.4f} held z={z:.2f} p={p:.4f} "
          f"held_mean={held_mean:.4f} traincov={cov}", flush=True)
    print(f"[{tag}] held decrypt: {txt}", flush=True)
    print(f"[{tag}] train decrypt: {fulltxt[:200]}", flush=True)
    return {"train_total": tot, "train_mean": train_mean,
            "held_obs": obs, "held_mean": held_mean,
            "null_mu": mu, "null_sd": sd, "z": z, "p": p,
            "train_dict_cov": cov,
            "held_sample": txt, "train_sample": fulltxt[:300],
            "assign": [int(x) for x in assign]}

if mode in ("all", "real"):
    results["real_en_free"] = run_real("en", None, "REAL-EN-free")
    results["real_en_pinned"] = run_real("en", PINS, "REAL-EN-pin")
    results["real_de_free"] = run_real("de", None, "REAL-DE-free")
    results["real_de_pinned"] = run_real("de", PINS, "REAL-DE-pin")
    results["real_pl_free"] = run_real("pl", None, "REAL-PL-free")
    results["real_pt_free"] = run_real("pt", None, "REAL-PT-free")
    json.dump(results, open(f"{OUT}/hs_results_partial.json", "w"), indent=1)

# =================== PHASE D: shuffle control ===================
if mode in ("all", "shuffle"):
    rs = random.Random(SEED + 99)
    def shuffle_frags(frags):
        toks = [t for f in frags for t in f]
        rs.shuffle(toks)
        out, i = [], 0
        for f in frags:
            out.append(toks[i:i + len(f)]); i += len(f)
        return out
    sh_train = Stream([[code2i[t] for t in f] for f in shuffle_frags(train_frags_tok)])
    sh_held = Stream([[code2i[t] for t in f] for f in shuffle_frags(held_novel_frags)])
    for lang in ("en", "de"):
        T = lm[lang]
        assign, tot = solve(sh_train, T, seed=SEED + 13, tag=f"SHUF-{lang}")
        obs, mu, sd, z, p = held_z(sh_held, T, assign, seed=SEED + 14)
        print(f"[SHUF-{lang}] train_mean={tot/sh_train.nwin_real:.4f} "
              f"held z={z:.2f} p={p:.4f}", flush=True)
        results[f"shuffle_{lang}"] = {
            "train_total": tot, "train_mean": tot / sh_train.nwin_real,
            "held_obs": obs, "null_mu": mu, "null_sd": sd, "z": z, "p": p}
    json.dump(results, open(f"{OUT}/hs_results_partial.json", "w"), indent=1)

# =================== PHASE E: full-corpus readability ===================
if mode in ("all", "full"):
    for lang, pins, tag in (("en", None, "FULL-EN-free"), ("en", PINS, "FULL-EN-pin"),
                            ("de", None, "FULL-DE-free"), ("de", PINS, "FULL-DE-pin")):
        T = lm[lang]
        assign, tot = solve(full_stream, T, pins=pins, seed=SEED + 17, tag=tag)
        txt = to_text(full_stream, assign)
        cov = dict_coverage(txt.replace("|", "")) if lang == "en" else None
        # coverage null
        covz = None
        if lang == "en":
            nprng = np.random.default_rng(SEED + 18)
            covs = []
            for _ in range(30):
                a2 = nprng.permutation(assign)
                covs.append(dict_coverage(to_text(full_stream, a2).replace("|", "")))
            covz = (cov - np.mean(covs)) / max(np.std(covs), 1e-9)
        print(f"[{tag}] mean={tot/full_stream.nwin_real:.4f} cov={cov} covz={covz}", flush=True)
        print(f"[{tag}] decrypt[0:400]: {txt[:400]}", flush=True)
        results[f"full_{lang}_{'pin' if pins else 'free'}"] = {
            "total": tot, "mean": tot / full_stream.nwin_real,
            "dict_cov": cov, "cov_z": covz, "sample": txt[:500],
            "assign": [int(x) for x in assign]}

json.dump(results, open(f"{OUT}/hs_results.json", "w"), indent=1)
print("DONE", flush=True)

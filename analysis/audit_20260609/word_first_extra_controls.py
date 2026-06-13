#!/usr/bin/env python3
"""300 extra shuffled-key controls for the word_first scheme only (it had p_emp=0.059
on 100 reps). Tightens the empirical p for the real max -1.1256."""
import sqlite3, random, math
from collections import defaultdict

random.seed(4691)
DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
keys = con.execute("SELECT source_id, title, text FROM external_corpus_sources ORDER BY source_id").fetchall()
books = con.execute("SELECT bookid, MIN(digits) FROM sheet__books GROUP BY bookid ORDER BY CAST(bookid AS INTEGER)").fetchall()
con.close()
print(f"keys={len(keys)} books={len(books)}", flush=True)

def tokenize(text):
    out = []
    for raw in text.split():
        w = "".join(ch for ch in raw.lower() if ch.isalpha())
        if w:
            out.append(w)
    return out

def letters_only(s):
    s = s.lower().replace("ä","ae").replace("ö","oe").replace("ü","ue").replace("ß","ss")
    return "".join(ch for ch in s if "a" <= ch <= "z")

key_words = {sid: tokenize(t) for sid, _, t in keys}

def build_lm(text):
    counts, bigrams = defaultdict(int), defaultdict(int)
    for i in range(len(text) - 2):
        counts[text[i:i+3]] += 1
        bigrams[text[i:i+2]] += 1
    lm = {t: math.log10((c + 0.5) / (bigrams[t[:2]] + 13.0)) for t, c in counts.items()}
    floor = {b: math.log10(0.5 / (tot + 13.0)) for b, tot in bigrams.items()}
    return lm, floor, math.log10(1.0 / 26 ** 1.5)

# Must match main script exactly: EN LM trained on all 33 texts; DE on embedded sample.
import importlib.util
spec = importlib.util.spec_from_file_location("main_mod", "./tmp/audit_20260609/ottendorf_sweep_lmonly.py")
# instead of importing the heavy script, rebuild identically:
EN_TEXT = letters_only(" ".join(t for _, _, t in keys))
exec(open("./tmp/audit_20260609/german_sample.txt").read()) if False else None
# read German sample out of the main script source
src = open("./tmp/audit_20260609/ottendorf_sweep.py").read()
GERMAN_SAMPLE = src.split('GERMAN_SAMPLE = """')[1].split('"""')[0]
DE_TEXT = letters_only(GERMAN_SAMPLE)
print(f"EN letters={len(EN_TEXT)} DE letters={len(DE_TEXT)}", flush=True)

def build_trigram_lm(text_letters):
    counts, bigrams = defaultdict(int), defaultdict(int)
    for i in range(len(text_letters) - 2):
        counts[text_letters[i:i+3]] += 1
        bigrams[text_letters[i:i+2]] += 1
    lm = {}
    for tri, c in counts.items():
        lm[tri] = math.log10((c + 0.5) / (bigrams[tri[:2]] + 0.5 * 26))
    floor = {bg: math.log10(0.5 / (tot + 0.5 * 26)) for bg, tot in bigrams.items()}
    return lm, floor, math.log10(1.0 / 26 ** 1.5)

EN_LM = build_trigram_lm(EN_TEXT)
DE_LM = build_trigram_lm(DE_TEXT)

def lm_score(s, pack):
    lm, floor, default = pack
    n = len(s) - 2
    if n < 3:
        return -99.0
    tot = 0.0
    for i in range(n):
        tri = s[i:i+3]
        v = lm.get(tri)
        if v is None:
            v = floor.get(tri[:2], default)
        tot += v
    return tot / n

def score(s):
    return max(lm_score(s, EN_LM), lm_score(s, DE_LM))

def decode_word_first(digits, words, first_letters):
    nw = len(words)
    out, i, L = [], 0, len(digits)
    while i < L:
        used = False
        for k in (3, 2, 1):
            if i + k <= L:
                v = int(digits[i:i+k])
                if 1 <= v <= nw:
                    out.append(first_letters[v - 1])
                    i += k
                    used = True
                    break
        if not used:
            i += 1
    return "".join(out)

REAL_MAX = -1.1256  # from main run (rounded); recompute exact below for safety
real_max = -1e9
for sid in key_words:
    w = key_words[sid]
    fl = [x[0] for x in w]
    for bid, dg in books:
        sc = score(decode_word_first(dg, w, fl))
        if sc > real_max:
            real_max = sc
print(f"recomputed real max (word_first) = {real_max:.6f}", flush=True)

N = 300
cm = []
for rep in range(N):
    rep_max = -1e9
    for sid in key_words:
        w = key_words[sid][:]
        random.shuffle(w)
        fl = [x[0] for x in w]
        for bid, dg in books:
            sc = score(decode_word_first(dg, w, fl))
            if sc > rep_max:
                rep_max = sc
    cm.append(rep_max)
    if (rep + 1) % 50 == 0:
        print(f"rep {rep+1}/{N}, running ge-count={sum(1 for x in cm if x >= real_max)}", flush=True)

m = sum(cm) / len(cm)
sd = (sum((x - m) ** 2 for x in cm) / (len(cm) - 1)) ** 0.5
nge = sum(1 for x in cm if x >= real_max)
print(f"\nEXTRA CONTROLS word_first: n={N} ctrl_max mean={m:.4f} sd={sd:.4f} "
      f"min={min(cm):.4f} max={max(cm):.4f}")
print(f"n_ctrl_max >= real_max: {nge}/{N} -> p_emp={(1+nge)/(N+1):.4f} "
      f"(combined with first run: {(1+nge+5)/(N+100+1):.4f})")
print(f"z = {(real_max - m)/sd:.3f}")

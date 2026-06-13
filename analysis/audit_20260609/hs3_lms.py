#!/usr/bin/env python3
"""Build character 4-gram LMs (EN, DE, PL, PT) from LOCAL data only.

EN: local Gutenberg dumps (tmp/corpus/pd_text_*.txt, Alice excluded as control
    plaintext) + Tibia in-game book texts (domain-matched English).
DE/PL/PT: composed prose in hs_langdata.py + harvested macOS localization
    strings (lproj_harvest.json) - real language, UI register.
Control plaintexts (never in any LM): Alice in Wonderland slice (EN),
CONTROL_DE composed prose (DE).

Output: hs_lm_<lang>.npz containing log-prob table shape (27,27,27,27)
(index 26 = sentinel, rows zero) + unigram p.
"""
import json, os, re, sys, unicodedata
import numpy as np

OUT = "./tmp/audit_20260609"
CORPUS = "./tmp/corpus"
sys.path.insert(0, OUT)
import hs_langdata as L

A = 26  # letters
S = 27  # with sentinel

DE_MAP = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
          "Ä": "ae", "Ö": "oe", "Ü": "ue"}

def clean(text, lang):
    if lang == "de":
        for k, v in DE_MAP.items():
            text = text.replace(k, v)
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z]+", "", text)
    # collapse same-char runs >2 ("hmmmm", "zzzzz", placeholder runs): these
    # create degenerate constant-letter attractors in the 4-gram LM
    return re.sub(r"(.)\1{2,}", r"\1\1", text)

def en_corpus():
    parts = []
    excl = {"pd_text_f68c7a9dfef8.txt"}  # Alice: reserved control plaintext
    for fn in sorted(os.listdir(CORPUS)):
        if fn.startswith("pd_text_") and fn.endswith(".txt") and fn not in excl:
            parts.append(open(os.path.join(CORPUS, fn), encoding="utf-8", errors="ignore").read())
    tb = json.load(open(os.path.join(CORPUS, "tibia_books_547449b5e385.json")))
    nbook = 0
    for b in tb:
        t = b.get("text") or ""
        dig = sum(c.isdigit() for c in t)
        if len(t) > 50 and dig / max(len(t), 1) < 0.2:  # skip cipher books
            parts.append(t); nbook += 1
    print("EN: gutenberg files", len(parts) - nbook, "tibia books", nbook)
    parts.append(L.TRAIN_EN)
    return clean(" ".join(parts), "en")

RUN3 = re.compile(r"(.)\1\1")

def good_string(s):
    """Reject placeholder/junk localization strings that poison the LM."""
    low = s.lower()
    letters = [c for c in low if c.isalpha()]
    if len(letters) < 8:
        return False
    if RUN3.search(low):
        return False
    from collections import Counter
    cnt = Counter(letters)
    if cnt.most_common(1)[0][1] / len(letters) > 0.4:
        return False
    if len(cnt) < 5:
        return False
    return True

def other_corpus(lang):
    harv = json.load(open(f"{OUT}/lproj_harvest.json"))
    key = {"de": "de", "pl": "pl", "pt": "pt"}[lang]
    keep = [s for s in harv[key] if good_string(s)]
    print(lang, "harvest strings kept", len(keep), "of", len(harv[key]))
    ui = clean(" ".join(keep), lang)
    prose = clean(getattr(L, f"TRAIN_{lang.upper()}"), lang)
    rep = max(1, int(0.25 * len(ui) / len(prose)))  # ~20% prose register
    return ui + prose * rep

def build_lm(txt, lang):
    x = np.frombuffer(txt.encode("ascii"), dtype=np.uint8).astype(np.int64) - 97
    n = len(x)
    print(lang, "clean chars:", n)
    c1 = np.bincount(x, minlength=A).astype(np.float64)
    i2 = x[:-1] * A + x[1:]
    c2 = np.bincount(i2, minlength=A**2).astype(np.float64)
    i3 = i2[:-1] * A + x[2:]
    c3 = np.bincount(i3, minlength=A**3).astype(np.float64)
    i4 = i3[:-1] * A + x[3:]
    c4 = np.bincount(i4, minlength=A**4).astype(np.float64)
    k = 0.25
    p1 = (c1 + k) / (c1 + k).sum()
    p2 = (c2.reshape(A, A) + k) / (c2.reshape(A, A).sum(1, keepdims=True) + k * A)
    p3 = (c3.reshape(A * A, A) + k) / (c3.reshape(A * A, A).sum(1, keepdims=True) + k * A)
    p4 = (c4.reshape(A**3, A) + k) / (c4.reshape(A**3, A).sum(1, keepdims=True) + k * A)
    l4, l3, l2, l1 = 0.60, 0.25, 0.10, 0.05
    # interp[a,b,c,d] = l4*p4(d|abc) + l3*p3(d|bc) + l2*p2(d|c) + l1*p1(d)
    p4r = p4.reshape(A, A, A, A)
    p3r = p3.reshape(A, A, A)[None, :, :, :]
    p2r = p2.reshape(A, A)[None, None, :, :]
    p1r = p1[None, None, None, :]
    P = l4 * p4r + l3 * p3r + l2 * p2r + l1 * p1r
    logP = np.log(P)
    T = np.zeros((S, S, S, S), dtype=np.float64)
    T[:A, :A, :A, :A] = logP
    np.savez_compressed(f"{OUT}/hs_lm_{lang}.npz", T=T, p1=p1, n=n)
    # self-score sanity: mean 4-gram logprob of own corpus sample
    m = min(n - 3, 200000)
    idx = np.arange(m)
    sc = T[x[idx], x[idx + 1], x[idx + 2], x[idx + 3]].mean()
    print(lang, "self mean4glp %.4f" % sc)
    return T

if __name__ == "__main__":
    en = en_corpus()
    build_lm(en, "en")
    for lg in ("de", "pl", "pt"):
        build_lm(other_corpus(lg), lg)
    # control plaintexts
    alice = open(os.path.join(CORPUS, "pd_text_f68c7a9dfef8.txt"), encoding="utf-8", errors="ignore").read()
    alice = alice[3000:]  # skip header/contents
    ctrl_en = clean(alice, "en")
    ctrl_de = clean(L.CONTROL_DE, "de")
    json.dump({"en": ctrl_en[:12000], "de": ctrl_de}, open(f"{OUT}/hs_control_plaintexts.json", "w"))
    print("CTRL_EN chars", min(len(ctrl_en), 12000), "CTRL_DE chars", len(ctrl_de))
    print("DONE")

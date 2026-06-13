#!/usr/bin/env python3
"""Digit-level re-pairing closure attack:
reverse / even-odd interleave / columnar / boustrophedon reorderings of each
book's raw digit string, re-paired into 2-digit codes (no zero reinsertion),
scored on valid-code fraction and chi-square language fit vs EN/DE.
Null model: 200 random digit permutations per book.
READ-ONLY on the DB.
"""
import sqlite3, random, math, json
from collections import Counter

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

# --- load books (dedupe) ---
rows = cur.execute(
    "SELECT bookid, digits FROM sheet__books GROUP BY bookid").fetchall()
print(f"books loaded: {len(rows)}")
assert len(rows) == 70, "expected 70 books"
books = {bid: d for bid, d in rows}
total_digits = sum(len(d) for d in books.values())
print(f"total digits: {total_digits}")
assert total_digits == 11263

# --- load code->symbol map ---
cmap_rows = cur.execute(
    "SELECT code, symbol FROM row0_code_symbol_counts").fetchall()
print(f"code map rows: {len(cmap_rows)}")
assert len(cmap_rows) == 99
code2sym = dict(cmap_rows)
all_codes = {f"{i:02d}" for i in range(100)}
missing = sorted(all_codes - set(code2sym))
print(f"missing codes (invalid pairs): {missing}")

# canonical decoded baseline distribution (with zero reinsertion)
dec_rows = cur.execute(
    "SELECT decodedbase FROM sheet__books GROUP BY bookid").fetchall()
print(f"decodedbase rows: {len(dec_rows)}")
canon_decoded = "".join(r[0] for r in dec_rows)
print(f"canonical decoded symbols (incl *): {len(canon_decoded)}")

# --- letter frequency targets, renormalized over the 13-letter alphabet ---
ALPHA = "ABCEFILNORSTV"
EN = {'A':8.167,'B':1.492,'C':2.782,'D':4.253,'E':12.702,'F':2.228,'G':2.015,
      'H':6.094,'I':6.966,'J':0.153,'K':0.772,'L':4.025,'M':2.406,'N':6.749,
      'O':7.507,'P':1.929,'Q':0.095,'R':5.987,'S':6.327,'T':9.056,'U':2.758,
      'V':0.978,'W':2.360,'X':0.150,'Y':1.974,'Z':0.074}
DE = {'A':6.516,'B':1.886,'C':2.732,'D':5.076,'E':16.396,'F':1.656,'G':3.009,
      'H':4.577,'I':6.550,'J':0.268,'K':1.417,'L':3.437,'M':2.534,'N':9.776,
      'O':2.594,'P':0.670,'Q':0.018,'R':7.003,'S':7.270,'T':6.154,'U':4.166,
      'V':0.846,'W':1.921,'X':0.034,'Y':0.039,'Z':1.134}
def renorm(freq):
    s = sum(freq[c] for c in ALPHA)
    return {c: freq[c]/s for c in ALPHA}
EN13, DE13 = renorm(EN), renorm(DE)

def chi2(counts):
    """chi-square of letter counts (star excluded) vs EN13 and DE13."""
    n = sum(counts[c] for c in ALPHA)
    if n == 0:
        return float('inf'), float('inf'), 0
    en = sum((counts[c] - n*EN13[c])**2 / (n*EN13[c]) for c in ALPHA)
    de = sum((counts[c] - n*DE13[c])**2 / (n*DE13[c]) for c in ALPHA)
    return en, de, n

def score_pairs(digit_str):
    """pair consecutive digits; return (n_pairs, n_valid, letter Counter, star count)"""
    n = len(digit_str) // 2
    valid = 0
    letters = Counter()
    stars = 0
    for i in range(n):
        code = digit_str[2*i:2*i+2]
        sym = code2sym.get(code)
        if sym is None:
            continue
        valid += 1
        if sym == '*':
            stars += 1
        else:
            letters[sym] += 1
    return n, valid, letters, stars

# --- reorderings ---
def reorder_reverse(s): return s[::-1]
def reorder_even_odd(s): return s[0::2] + s[1::2]
def reorder_odd_even(s): return s[1::2] + s[0::2]

def reorder_columnar(s, w):
    """fill row-major width w, read column-major, pad-free."""
    out = []
    n = len(s)
    for c in range(w):
        out.append(s[c::w])
    return "".join(out)

def reorder_boustro_row(s, w):
    """rows of width w, alternate rows reversed (serpentine read)."""
    out = []
    for r in range(0, len(s), w):
        row = s[r:r+w]
        if (r // w) % 2 == 1:
            row = row[::-1]
        out.append(row)
    return "".join(out)

def reorder_boustro_col(s, w):
    """column-major read, alternate columns reversed."""
    out = []
    for c in range(w):
        col = s[c::w]
        if c % 2 == 1:
            col = col[::-1]
        out.append(col)
    return "".join(out)

WIDTHS = range(2, 41)
transforms = [("canonical_raw", lambda s: s),
              ("reverse", reorder_reverse),
              ("even_then_odd", reorder_even_odd),
              ("odd_then_even", reorder_odd_even)]
for w in WIDTHS:
    transforms.append((f"columnar_w{w}", lambda s, w=w: reorder_columnar(s, w)))
for w in WIDTHS:
    transforms.append((f"boustro_row_w{w}", lambda s, w=w: reorder_boustro_row(s, w)))
for w in WIDTHS:
    transforms.append((f"boustro_col_w{w}", lambda s, w=w: reorder_boustro_col(s, w)))
print(f"transforms: {len(transforms)}")

results = {}
for name, fn in transforms:
    tot_pairs = tot_valid = tot_stars = 0
    letters = Counter()
    perbook_validfrac = []
    perbook_chi_en = []
    for bid, d in sorted(books.items()):
        r = fn(d)
        assert len(r) == len(d) and Counter(r) == Counter(d), f"bad transform {name}"
        n, v, lc, st = score_pairs(r)
        tot_pairs += n; tot_valid += v; tot_stars += st
        letters += lc
        perbook_validfrac.append(v / n if n else 1.0)
        ce, _, _ = chi2(lc)
        perbook_chi_en.append(ce)
    en, de, nlet = chi2(letters)
    results[name] = dict(
        pairs=tot_pairs, valid=tot_valid, validfrac=tot_valid/tot_pairs,
        stars=tot_stars, letters=nlet, chi2_en=en, chi2_de=de,
        books_all_valid=sum(1 for f in perbook_validfrac if f == 1.0),
        min_book_validfrac=min(perbook_validfrac),
        mean_book_chi2_en=sum(perbook_chi_en)/len(perbook_chi_en))

# --- canonical decode baseline (with zero reinsertion, from decodedbase) ---
dec_counts = Counter(canon_decoded)
dec_letters = Counter({c: dec_counts.get(c, 0) for c in ALPHA})
den, dde, dn = chi2(dec_letters)
print(f"\nCANONICAL DECODE (decodedbase, zero-reinserted): symbols={len(canon_decoded)} "
      f"stars={dec_counts.get('*',0)} letters={dn} chi2_EN={den:.1f} chi2_DE={dde:.1f}")

# --- null model: 200 random permutations per book ---
random.seed(469)
NTRIAL = 200
null_validfrac, null_chi_en, null_chi_de = [], [], []
for t in range(NTRIAL):
    tot_pairs = tot_valid = 0
    letters = Counter()
    for bid, d in books.items():
        l = list(d)
        random.shuffle(l)
        n, v, lc, st = score_pairs("".join(l))
        tot_pairs += n; tot_valid += v
        letters += lc
    null_validfrac.append(tot_valid/tot_pairs)
    en, de, _ = chi2(letters)
    null_chi_en.append(en); null_chi_de.append(de)

def msd(xs):
    m = sum(xs)/len(xs)
    sd = (sum((x-m)**2 for x in xs)/(len(xs)-1))**0.5
    return m, sd
nv_m, nv_sd = msd(null_validfrac)
ne_m, ne_sd = msd(null_chi_en)
nd_m, nd_sd = msd(null_chi_de)
print(f"\nNULL (200 random perms/book, aggregated): validfrac {nv_m:.5f} +- {nv_sd:.5f}; "
      f"chi2_EN {ne_m:.1f} +- {ne_sd:.1f}; chi2_DE {nd_m:.1f} +- {nd_sd:.1f}")

# --- report ---
base = results["canonical_raw"]
print(f"\n{'transform':<18}{'validfrac':>10}{'allvalid':>9}{'minbook':>9}"
      f"{'chi2_EN':>10}{'chi2_DE':>10}{'z_vf':>8}{'z_chiEN':>9}")
ranked = sorted(results.items(), key=lambda kv: -kv[1]['validfrac'])
for name, r in ranked:
    zvf = (r['validfrac'] - nv_m)/nv_sd if nv_sd else 0
    zce = (r['chi2_en'] - ne_m)/ne_sd if ne_sd else 0
    print(f"{name:<18}{r['validfrac']:>10.5f}{r['books_all_valid']:>9}"
          f"{r['min_book_validfrac']:>9.4f}{r['chi2_en']:>10.1f}{r['chi2_de']:>10.1f}"
          f"{zvf:>8.2f}{zce:>9.2f}")

# winners vs canonical on BOTH criteria
print("\n--- transforms beating canonical_raw on validfrac AND chi2_EN ---")
hits = [(n, r) for n, r in results.items() if n != "canonical_raw"
        and r['validfrac'] > base['validfrac'] and r['chi2_en'] < base['chi2_en']]
print(f"count: {len(hits)}")
for n, r in sorted(hits, key=lambda kv: kv[1]['chi2_en']):
    print(f"  {n}: validfrac={r['validfrac']:.5f} chi2_EN={r['chi2_en']:.1f} "
          f"chi2_DE={r['chi2_de']:.1f} books_all_valid={r['books_all_valid']}")

print("\n--- transforms beating canonical_raw on chi2_DE ---")
hits_de = [(n, r) for n, r in results.items() if n != "canonical_raw"
           and r['validfrac'] > base['validfrac'] and r['chi2_de'] < base['chi2_de']]
print(f"count: {len(hits_de)}")

with open("./tmp/audit_20260609/repairing_results.json", "w") as f:
    json.dump({"results": results,
               "null": {"validfrac": [nv_m, nv_sd], "chi2_en": [ne_m, ne_sd],
                        "chi2_de": [nd_m, nd_sd], "ntrial": NTRIAL},
               "canonical_decode_baseline": {"chi2_en": den, "chi2_de": dde,
                                             "letters": dn,
                                             "stars": dec_counts.get('*', 0)},
               "missing_codes": missing}, f, indent=1)
print("\nwrote repairing_results.json")

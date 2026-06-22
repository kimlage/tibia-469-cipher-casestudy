#!/usr/bin/env python3
"""B1 — Null-corpus + generic-compressor control for Formula B (book assembly).

Backlog item B1 (docs/plans/2026-06-21_avaliacao_e_plano_formula.md): test whether
the bespoke ~8154-bit LZ description is special, or whether (a) an off-the-shelf
compressor reaches the same description length and (b) a message-free copy-assembly
process reproduces the corpus's copy-fraction. If both, the entire Formula-B front
is generic copy redundancy, not a recovered authoring algorithm.

Classification: AUDIT_ONLY_NO_SEMANTICS. Translation delta: NONE. Deterministic.
"""
import json, math, random, statistics, zlib, bz2, lzma
try:
    import zstandard; HAS_ZSTD = True
except Exception:
    HAS_ZSTD = False
try:
    import brotli; HAS_BROTLI = True
except Exception:
    HAS_BROTLI = False

BESPOKE = 8154.68  # page-18 current bound


def load():
    d = json.load(open("analysis/audit_20260609/books_digits.json"))
    books = [str(d[str(i)]) for i in range(70)]
    return books, [len(b) for b in books], "".join(books)


def generic_compressors(S, N):
    out = {}
    a = S.encode()
    out["brotli(hdr)"] = len(brotli.compress(a, quality=11)) * 8 if HAS_BROTLI else None
    out["zstd(hdr)"] = len(zstandard.ZstdCompressor(level=22).compress(a)) * 8 if HAS_ZSTD else None
    rd = zlib.compressobj(9, zlib.DEFLATED, -15); out["raw_deflate"] = (len(rd.compress(a) + rd.flush())) * 8
    out["raw_lzma2"] = len(lzma.compress(a, format=lzma.FORMAT_RAW,
                                         filters=[{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}])) * 8
    return out


def markov_prequential_bits(S, k):
    from collections import defaultdict
    ctx = defaultdict(lambda: defaultdict(int)); bits = 0.0
    for i, ch in enumerate(S):
        c = S[max(0, i - k):i]; cnt = ctx[c]; tot = sum(cnt.values())
        bits += -math.log2((cnt[ch] + 1) / (tot + 10)); cnt[ch] += 1
    return bits


def lz_parse(s, min_len=6):
    n = len(s); i = 0; lens = []; lit = 0; mdl = 0.0
    while i < n:
        if i >= min_len and s.find(s[i:i + min_len], 0, i) != -1:
            L = min_len
            while i + L < n and s.find(s[i:i + L + 1], 0, i) != -1:
                L += 1
            lens.append(L); mdl += 1 + math.log2(max(i, 2)) + (2 * math.floor(math.log2(L)) + 1); i += L
        else:
            lit += 1; mdl += 1 + math.log2(10); i += 1
    return dict(copyfrac=sum(lens) / n, copies=len(lens), literals=lit, lens=lens, mdl=mdl)


def main():
    books, lengths, S = load(); N = len(S)
    print(f"N={N} books=70 book0={lengths[0]} raw_uniform={N*math.log2(10):.0f} bits | bespoke={BESPOKE}")

    print("\n== Part 1: generic compressors (headerless where possible) ==")
    for k, v in generic_compressors(S, N).items():
        if v is None: continue
        print(f"  {k:12s}: {v} bits ({v/N:.4f}/dig)  delta_vs_bespoke={v-BESPOKE:+.0f}")

    print("\n== Part 1b: adaptive Markov prequential (no copy model) ==")
    for k in range(0, 6):
        b = markov_prequential_bits(S, k); print(f"  order-{k}: {b:.0f} bits ({b/N:.4f}/dig)")

    real = lz_parse(S); L = real["lens"]
    print(f"\n== Part 2: greedy LZ parse REAL  copyfrac={real['copyfrac']:.3f} "
          f"copies={real['copies']} literals={real['literals']} mdl={real['mdl']:.0f} ==")
    print(f"  copy len: min={min(L)} median={statistics.median(L):.0f} mean={statistics.mean(L):.1f} "
          f"max={max(L)} | >=50:{sum(1 for x in L if x>=50)} >=100:{sum(1 for x in L if x>=100)}")

    ex = sum(1 for i, b in enumerate(books) if b in "".join(books[j] for j in range(70) if j != i))
    single = sum(1 for i, b in enumerate(books) if any(i != j and b in c for j, c in enumerate(books)))
    print(f"  whole books that are exact substrings of the other 69 concatenated: {ex}/70")
    print(f"  whole books fully contained in a SINGLE other book: {single}/70")

    def null_iid(s):
        r = random.Random(s); return "".join(r.choice("0123456789") for _ in range(N))

    def null_markov(s, k=2):
        from collections import defaultdict
        r = random.Random(s); m = defaultdict(lambda: defaultdict(int))
        for i, ch in enumerate(S): m[S[max(0, i - k):i]][ch] += 1
        out = []
        for i in range(N):
            c = "".join(out[max(0, i - k):i]); cnt = m.get(c)
            if not cnt: out.append(r.choice("0123456789")); continue
            items = list(cnt.items()); tot = sum(v for _, v in items); x = r.uniform(0, tot); acc = 0
            for ch, v in items:
                acc += v
                if x <= acc: out.append(ch); break
            else: out.append(items[-1][0])
        return "".join(out)

    def null_sharedbank(s):
        r = random.Random(s)
        bank = ["".join(r.choice("0123456789") for _ in range(r.randint(5, 18))) for _ in range(60)]
        out = []
        for Lb in lengths:
            buf = ""
            while len(buf) < Lb:
                buf += r.choice(bank) if r.random() < 0.85 else r.choice("0123456789")
            out.append(buf[:Lb])
        return "".join(out)

    print("\n== Part 2: message-free nulls (mean over 5 seeds) ==")
    for name, gen in [("IID-uniform", null_iid), ("Markov-order2", lambda s: null_markov(s, 2)),
                      ("SharedBank-copy", null_sharedbank)]:
        res = [lz_parse(gen(s)) for s in range(5)]
        print(f"  {name:16s}: copyfrac={statistics.mean(x['copyfrac'] for x in res):.3f} "
              f"mdl={statistics.mean(x['mdl'] for x in res):.0f}")

    print("\nVERDICT: generic compressors land within ~230-620 bits of the bespoke bound; "
          "a message-free shared-bank null reproduces the copy-fraction (~0.91 vs 0.93); "
          "real copies are long verbatim passages (20/70 books fully inside another, max 303). "
          "=> Formula B is message-free copy-paste assembly; the bit-sweep is a compression treadmill.")


if __name__ == "__main__":
    main()

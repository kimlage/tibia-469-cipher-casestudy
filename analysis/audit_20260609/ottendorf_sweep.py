#!/usr/bin/env python3
"""
Ottendorf / index-cipher sweep over the 33 local TibiaWiki lore texts.

For each (key text, book) pair, decode the book's digit string under 4 schemes:
  (a) word_first : greedy 1-3 digit word indices into key word list -> first letter of word
  (b) pair_letter: consecutive 2-digit indices (1..100, 00->100) into key letter stream
  (c) word_letter: alternating (greedy 1-3 digit word index, 1 digit letter-within-word)
  (d) tri_letter : consecutive 3-digit indices into key letter stream (mod stream length)

Score each decode with English (trained on the 33 lore texts) and German (embedded
sample) letter-trigram LMs; per-decode score = max(EN, DE) mean log10 prob/trigram.

Null: 100 control reps; each rep shuffles every key's words (fresh permutation),
re-decodes all 33x70 pairs per scheme, records the MAX score over all pairs.
Real max per scheme is compared to the distribution of 100 control maxima
(extreme-value correction for the 2310 comparisons per scheme).
"""
import sqlite3, random, math, json, sys
from collections import defaultdict

random.seed(469)

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
N_CONTROLS = 100
OUT_DIR = "./tmp/audit_20260609"

# ---------- load data ----------
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

keys = cur.execute("SELECT source_id, title, text FROM external_corpus_sources ORDER BY source_id").fetchall()
print(f"key texts loaded: {len(keys)} rows", flush=True)
assert len(keys) == 33, "expected 33 key texts"

books = cur.execute("SELECT bookid, MIN(digits) FROM sheet__books GROUP BY bookid ORDER BY CAST(bookid AS INTEGER)").fetchall()
print(f"books loaded: {len(books)} rows", flush=True)
assert len(books) == 70, "expected 70 books"
total_digits = sum(len(d) for _, d in books)
print(f"total digits across books: {total_digits}", flush=True)
con.close()

# ---------- key preprocessing ----------
def tokenize(text):
    words = []
    for raw in text.split():
        w = "".join(ch for ch in raw.lower() if ch.isalpha())
        if w:
            words.append(w)
    return words

key_words = {}   # source_id -> list of words
key_titles = {}
for sid, title, text in keys:
    key_words[sid] = tokenize(text)
    key_titles[sid] = title
print("key word counts: min=%d max=%d" % (min(len(w) for w in key_words.values()),
                                          max(len(w) for w in key_words.values())), flush=True)

# ---------- trigram LMs ----------
ALPHA = "abcdefghijklmnopqrstuvwxyz"
AIDX = {c: i for i, c in enumerate(ALPHA)}

def letters_only(s):
    s = s.lower()
    s = (s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
           .replace("ß", "ss"))
    return "".join(ch for ch in s if "a" <= ch <= "z")

GERMAN_SAMPLE = """
Als Gregor Samsa eines Morgens aus unruhigen Traeumen erwachte fand er sich in
seinem Bett zu einem ungeheueren Ungeziefer verwandelt Er lag auf seinem
panzerartig harten Ruecken und sah wenn er den Kopf ein wenig hob seinen
gewoelbten braunen von bogenfoermigen Versteifungen geteilten Bauch auf dessen
Hoehe sich die Bettdecke zum gaenzlichen Niedergleiten bereit kaum noch erhalten
konnte Seine vielen im Vergleich zu seinem sonstigen Umfang klaeglich duennen
Beine flimmerten ihm hilflos vor den Augen Was ist mit mir geschehen dachte er
Es war kein Traum Sein Zimmer ein richtiges nur etwas zu kleines Menschenzimmer
lag ruhig zwischen den vier wohlbekannten Waenden Ueber dem Tisch auf dem eine
auseinandergepackte Musterkollektion von Tuchwaren ausgebreitet war Samsa war
Reisender hing das Bild das er vor kurzem aus einer illustrierten Zeitschrift
ausgeschnitten und in einem huebschen vergoldeten Rahmen untergebracht hatte
Es stellte eine Dame dar die mit einem Pelzhut und einer Pelzboa versehen
aufrecht dasass und einen schweren Pelzmuff in dem ihr ganzer Unterarm
verschwunden war dem Beschauer entgegenhob Gregors Blick richtete sich dann
zum Fenster und das truebe Wetter man hoerte Regentropfen auf das Fensterblech
aufschlagen machte ihn ganz melancholisch Wie waere es wenn ich noch ein wenig
weiterschliefe und alle Narrheiten vergaesse dachte er aber das war gaenzlich
undurchfuehrbar denn er war gewoehnt auf der rechten Seite zu schlafen konnte
sich aber in seinem gegenwaertigen Zustand nicht in diese Lage bringen
Es war einmal ein Mann der hatte einen Esel welcher schon lange Jahre
unverdrossen die Saecke in die Muehle getragen hatte Nun aber gingen die
Kraefte des Esels zu Ende so dass er zur Arbeit nicht mehr taugte Da dachte
der Herr daran ihn wegzugehen aber der Esel merkte dass kein guter Wind wehte
lief fort und machte sich auf den Weg nach Bremen dort meinte er koennte er ja
Stadtmusikant werden Als er ein Weilchen fortgegangen war fand er einen
Jagdhund am Wege liegen der jaemmerlich heulte Warum heulst du denn so Packan
fragte der Esel Ach sagte der Hund weil ich alt bin jeden Tag schwaecher werde
und auch nicht mehr auf die Jagd kann wollte mich mein Herr totschiessen Da
hab ich Reissaus genommen Aber womit soll ich nun mein Brot verdienen Weisst
du was sprach der Esel ich gehe nach Bremen und werde dort Stadtmusikant Komm
mit mir und lass dich auch bei der Musik annehmen Ich spiele die Laute und du
schlaegst die Pauken Der Hund war einverstanden und sie gingen mitsammen
weiter Es dauerte nicht lange da sahen sie eine Katze am Wege sitzen die
machte ein Gesicht wie drei Tage Regenwetter Was ist denn dir in die Quere
gekommen alter Bartputzer fragte der Esel Wer kann da lustig sein wenn es
einem an den Kragen geht antwortete die Katze Weil ich nun alt bin meine
Zaehne stumpf werden und ich lieber hinter dem Ofen sitze und spinne als nach
Maeusen herumjage hat mich meine Frau ersaeufen wollen Ich konnte mich zwar
noch davonschleichen aber nun ist guter Rat teuer Wo soll ich jetzt hin Geh
mit uns nach Bremen Du verstehst dich doch auf die Nachtmusik da kannst du
Stadtmusikant werden Die Katze hielt das fuer gut und ging mit Als die drei
so miteinander gingen kamen sie an einem Hof vorbei da sass der Haushahn auf
dem Tor und schrie aus Leibeskraeften Du schreist einem durch Mark und Bein
sprach der Esel was hast du vor Die Hausfrau hat der Koechin befohlen mir
heute Abend den Kopf abzuschlagen Morgen am Sonntag haben sie Gaeste da
wollen sie mich in der Suppe essen Nun schrei ich aus vollem Hals solang ich
noch kann Ei was du Rotkopf sagte der Esel zieh lieber mit uns fort wir gehen
nach Bremen etwas Besseres als den Tod findest du ueberall Du hast eine gute
Stimme und wenn wir mitsammen musizieren wird es gar herrlich klingen Dem
Hahn gefiel der Vorschlag und sie gingen alle vier mitsammen fort Sie konnten
aber die Stadt Bremen an einem Tag nicht erreichen und kamen abends in einen
Wald wo sie uebernachten wollten Der Esel und der Hund legten sich unter
einen grossen Baum die Katze kletterte auf einen Ast und der Hahn flog bis
in den Wipfel wo es am sichersten fuer ihn war
"""

def build_trigram_lm(text_letters):
    counts = defaultdict(int)
    bigrams = defaultdict(int)
    for i in range(len(text_letters) - 2):
        tri = text_letters[i:i+3]
        counts[tri] += 1
        bigrams[tri[:2]] += 1
    # additive smoothing over 26-letter alphabet
    lm = {}
    for tri, c in counts.items():
        lm[tri] = math.log10((c + 0.5) / (bigrams[tri[:2]] + 0.5 * 26))
    floor = {}
    for bg, tot in bigrams.items():
        floor[bg] = math.log10(0.5 / (tot + 0.5 * 26))
    default = math.log10(1.0 / 26 ** 1.5)  # unseen bigram context fallback
    return lm, floor, default

EN_TEXT = letters_only(" ".join(t for _, _, t in keys))
DE_TEXT = letters_only(GERMAN_SAMPLE)
print(f"EN LM training letters: {len(EN_TEXT)}; DE LM training letters: {len(DE_TEXT)}", flush=True)
EN_LM = build_trigram_lm(EN_TEXT)
DE_LM = build_trigram_lm(DE_TEXT)

def lm_score(s, lm_pack):
    lm, floor, default = lm_pack
    n = len(s) - 2
    if n < 3:
        return -99.0  # too short to score
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

# ---------- decode schemes ----------
def decode_word_first(digits, words, first_letters):
    nw = len(words)
    out = []
    i, L = 0, len(digits)
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
            i += 1  # unusable digit (e.g. leading 0 with no valid parse)
    return "".join(out)

def decode_pair_letter(digits, stream):
    n = len(stream)
    out = []
    for i in range(0, len(digits) - 1, 2):
        v = int(digits[i:i+2])
        if v == 0:
            v = 100
        out.append(stream[(v - 1) % n])
    return "".join(out)

def decode_tri_letter(digits, stream):
    n = len(stream)
    out = []
    for i in range(0, len(digits) - 2, 3):
        v = int(digits[i:i+3])
        out.append(stream[(v - 1) % n if v > 0 else n - 1])
    return "".join(out)

def decode_word_letter(digits, words):
    nw = len(words)
    out = []
    i, L = 0, len(digits)
    while i < L:
        used = False
        for k in (3, 2, 1):
            if i + k <= L:
                v = int(digits[i:i+k])
                if 1 <= v <= nw:
                    w = words[v - 1]
                    if i + k < L:
                        d = int(digits[i + k])
                        out.append(w[(d - 1) % len(w)])
                        i += k + 1
                    else:
                        i += k
                    used = True
                    break
        if not used:
            i += 1
    return "".join(out)

SCHEMES = ("word_first", "pair_letter", "word_letter", "tri_letter")

def decode_all_for_key(words):
    """Returns dict scheme -> list of (bookid, score, decoded)."""
    first_letters = [w[0] for w in words]
    stream = "".join(words)
    res = {s: [] for s in SCHEMES}
    for bid, digits in books:
        d1 = decode_word_first(digits, words, first_letters)
        d2 = decode_pair_letter(digits, stream)
        d3 = decode_word_letter(digits, words)
        d4 = decode_tri_letter(digits, stream)
        res["word_first"].append((bid, score(d1), d1))
        res["pair_letter"].append((bid, score(d2), d2))
        res["word_letter"].append((bid, score(d3), d3))
        res["tri_letter"].append((bid, score(d4), d4))
    return res

# ---------- real pass ----------
real = {s: [] for s in SCHEMES}   # (score, sid, bid, decoded)
for sid in key_words:
    r = decode_all_for_key(key_words[sid])
    for s in SCHEMES:
        for bid, sc, dec in r[s]:
            real[s].append((sc, sid, bid, dec))

n_pairs = len(keys) * len(books)
print(f"real decodes per scheme: {len(real[SCHEMES[0]])} (expect {n_pairs})", flush=True)

real_stats = {}
for s in SCHEMES:
    vals = sorted(real[s], reverse=True)
    scores = [v[0] for v in real[s] if v[0] > -90]
    real_stats[s] = {
        "n": len(real[s]),
        "n_scored": len(scores),
        "mean": sum(scores) / len(scores),
        "max": vals[0][0],
        "top5": [(round(v[0], 4), v[1], v[2], v[3][:60]) for v in vals[:5]],
    }
    print(f"[real {s}] n={len(real[s])} mean={real_stats[s]['mean']:.4f} max={vals[0][0]:.4f}", flush=True)

# ---------- control pass ----------
ctrl_max = {s: [] for s in SCHEMES}
ctrl_all_sum = {s: 0.0 for s in SCHEMES}
ctrl_all_sumsq = {s: 0.0 for s in SCHEMES}
ctrl_all_n = {s: 0 for s in SCHEMES}

for rep in range(N_CONTROLS):
    rep_max = {s: -1e9 for s in SCHEMES}
    for sid in key_words:
        w = key_words[sid][:]
        random.shuffle(w)
        r = decode_all_for_key(w)
        for s in SCHEMES:
            for bid, sc, dec in r[s]:
                if sc > rep_max[s]:
                    rep_max[s] = sc
                if sc > -90:
                    ctrl_all_sum[s] += sc
                    ctrl_all_sumsq[s] += sc * sc
                    ctrl_all_n[s] += 1
    for s in SCHEMES:
        ctrl_max[s].append(rep_max[s])
    if (rep + 1) % 10 == 0:
        print(f"control rep {rep+1}/{N_CONTROLS} done", flush=True)

# ---------- evaluation ----------
results = {"n_keys": len(keys), "n_books": len(books), "n_pairs": n_pairs,
           "total_digits": total_digits, "n_controls": N_CONTROLS, "schemes": {}}

for s in SCHEMES:
    cm = ctrl_max[s]
    m = sum(cm) / len(cm)
    sd = (sum((x - m) ** 2 for x in cm) / (len(cm) - 1)) ** 0.5
    real_max = real_stats[s]["max"]
    n_ge = sum(1 for x in cm if x >= real_max)
    p_emp = (1 + n_ge) / (len(cm) + 1)
    z = (real_max - m) / sd if sd > 0 else float("nan")
    # pooled per-pair control stats
    cn = ctrl_all_n[s]
    cmean = ctrl_all_sum[s] / cn
    csd = (ctrl_all_sumsq[s] / cn - cmean ** 2) ** 0.5
    results["schemes"][s] = {
        "real_max": round(real_max, 4),
        "real_mean": round(real_stats[s]["mean"], 4),
        "ctrl_max_mean": round(m, 4), "ctrl_max_sd": round(sd, 4),
        "ctrl_max_min": round(min(cm), 4), "ctrl_max_max": round(max(cm), 4),
        "z_vs_ctrl_max": round(z, 3), "n_ctrl_max_ge_real": n_ge, "p_empirical": round(p_emp, 4),
        "ctrl_pair_mean": round(cmean, 4), "ctrl_pair_sd": round(csd, 4),
        "n_real_pairs_above_ctrl_envelope": sum(1 for v in real[s] if v[0] > max(cm)),
        "top5_real": real_stats[s]["top5"],
    }
    print(f"\n=== {s} ===")
    print(f"real max {real_max:.4f} | ctrl max dist mean {m:.4f} sd {sd:.4f} "
          f"range [{min(cm):.4f},{max(cm):.4f}] | z={z:.2f} | p_emp={p_emp:.4f} "
          f"({n_ge}/{len(cm)} ctrl maxima >= real max)")
    print(f"pairs above full ctrl envelope: {results['schemes'][s]['n_real_pairs_above_ctrl_envelope']}")
    for t in real_stats[s]["top5"]:
        print(f"  top: score={t[0]} key={t[1]} ({key_titles[t[1]][:35]}) book={t[2]} dec='{t[3]}'")

# same-key clustering check: do top decodes concentrate on one key?
for s in SCHEMES:
    vals = sorted(real[s], reverse=True)[:20]
    key_counts = defaultdict(int)
    for v in vals:
        key_counts[v[1]] += 1
    top_key = max(key_counts.items(), key=lambda kv: kv[1])
    results["schemes"][s]["top20_key_concentration"] = {
        "key": top_key[0], "title": key_titles[top_key[0]], "count_of_20": top_key[1]}
    print(f"[{s}] top-20 decode key concentration: key {top_key[0]} "
          f"({key_titles[top_key[0]]}) holds {top_key[1]}/20")

with open(f"{OUT_DIR}/ottendorf_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nresults written to", f"{OUT_DIR}/ottendorf_results.json", flush=True)

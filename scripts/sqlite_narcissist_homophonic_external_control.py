#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import random
import re
import sqlite3
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"

PHRASES = [
    ("AVAR_TAR_TIBIA_ORG_VARIANT", "29639 46781 9063376290 3222011 677 80322429 67538 14805394 6880326 677 62792068657272657261 337011 72683 149630 4378 453 639 578300 986372 2953639"),
    ("KNIGHTMARE_PHRASE", "3478 67 90871 97664 3466 0 345"),
    ("TIBIA_2014_POLL_C", "663 902073 7223 67538 467 80097"),
]

COMMON = {
    "A", "BE", "RUN", "NARCISSIST", "NARCISSISM", "WIT", "THAN", "FOOL", "YOU", "SO", "FAST",
    "FIFTEEN", "STATUES", "IN", "EYE", "EYES", "FAR", "AWAY", "TRUE", "THUS",
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def words_from_phrase(phrase: str) -> list[str]:
    return re.findall(r"\d+", phrase)


def normalize_word(raw: str) -> list[str]:
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) % 2:
        digits = "0" + digits
    return [digits[i : i + 2] for i in range(0, len(digits), 2)]


def decode(words: list[str], mapping: dict[str, str]) -> list[str]:
    out = []
    for word in words:
        pairs = normalize_word(word)
        out.append("".join(mapping.get(pair, "?") for pair in pairs))
    return out


def score(decoded_words: list[str]) -> dict[str, Any]:
    text = " ".join(decoded_words)
    unknown = text.count("?")
    common = sum(1 for word in decoded_words if word in COMMON)
    vowelish = sum(1 for ch in text if ch in "AEIOUY") / max(1, sum(1 for ch in text if ch.isalpha()))
    bad = sum(1 for word in decoded_words if len(word) >= 5 and len(set(word)) <= 2)
    score_value = round(common * 10 + vowelish * 12 - unknown * 3 - bad * 2, 3)
    return {"score": score_value, "common": common, "unknown": unknown, "vowelish": round(vowelish, 3), "bad_low_variety_words": bad, "text": text}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    parser.add_argument("--shuffles", type=int, default=200)
    args = parser.parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    row0 = {}
    for row in cur.execute(
        """
        select code, symbol
        from row0_code_symbol_counts
        where run_id=(select max(run_id) from row0_code_symbol_probe_runs)
        order by code, occurrence_count desc
        """
    ):
        row0.setdefault(str(row["code"]), str(row["symbol"]))
    used_codes = sorted(row0)
    used_symbols = [row0[c] for c in used_codes]
    phrase_results = []
    observed_total = 0.0
    for phrase_id, phrase in PHRASES:
        decoded = decode(words_from_phrase(phrase), row0)
        s = score(decoded)
        observed_total += s["score"]
        phrase_results.append({"phrase_id": phrase_id, "decoded_words": decoded, **s})
    rng = random.Random(469)
    control_scores = []
    for _ in range(args.shuffles):
        shuffled = used_symbols[:]
        rng.shuffle(shuffled)
        mapping = dict(zip(used_codes, shuffled))
        total = 0.0
        for _, phrase in PHRASES:
            total += score(decode(words_from_phrase(phrase), mapping))["score"]
        control_scores.append(total)
    better_or_equal = sum(1 for value in control_scores if value >= observed_total)
    percentile = round(1.0 - better_or_equal / len(control_scores), 4) if control_scores else 0.0
    control_avg = round(sum(control_scores) / len(control_scores), 3) if control_scores else 0.0
    control_max = round(max(control_scores), 3) if control_scores else 0.0
    if percentile >= 0.95 and observed_total > control_avg:
        decision = "NARCISSIST_ROW0_EXTERNAL_DECODE_BEATS_SHUFFLE_CONTROLS_AUDIT_ONLY"
        next_action = "Use row0 mapping as external phrase scaffold, but require phrase-level source before gloss."
    else:
        decision = "NARCISSIST_ROW0_EXTERNAL_DECODE_DOES_NOT_BEAT_CONTROLS"
        next_action = "Keep NARCISSIST as isolated micro-anchor; do not expand phrase gloss."
    cur.executescript(
        """
        create table if not exists narcissist_homophonic_external_control_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            observed_score real not null,
            control_avg real not null,
            control_max real not null,
            percentile real not null,
            phrase_count integer not null,
            shuffle_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        """
    )
    payload = {
        "phrase_results": phrase_results,
        "control_scores_sample": control_scores[:25],
        "scoring_note": "Heuristic control only; not a semantic acceptance gate by itself.",
    }
    cur.execute(
        "insert into narcissist_homophonic_external_control_runs(created_at,observed_score,control_avg,control_max,percentile,phrase_count,shuffle_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?,?,?)",
        (now(), observed_total, control_avg, control_max, percentile, len(PHRASES), args.shuffles, decision, next_action, j(payload)),
    )
    con.commit()
    print(json.dumps({"run_id": cur.lastrowid, "decision": decision, "observed_score": round(observed_total, 3), "control_avg": control_avg, "control_max": control_max, "percentile": percentile, "phrase_results": phrase_results}, ensure_ascii=False))


if __name__ == "__main__":
    main()

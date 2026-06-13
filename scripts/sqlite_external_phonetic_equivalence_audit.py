#!/usr/bin/env python3
import argparse
import datetime as dt
import itertools
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
DICT_DEFAULT = "/usr/share/dict/words"

PHRASES = [
    ("KNIGHTMARE_PHRASE", "BE A TIV TAN BE * VF"),
    ("TIBIA_2014_POLL_C", "IV TRA SO IET FA I*A"),
    ("AVAR_TAR_TIBIA_ORG_VARIANT", "RV? FAI TVANT VARE IN IOLN IET AILN IAVN IN NARCISSIST EIE INT AVV BE FL I? ET* TVS RIV?"),
]

COMMON_ALLOW = {"A", "I", "BE", "IN", "SO", "NARCISSIST"}
TARGETABLE = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ*?")
EQUIV = {
    "V": ["V", "U", "W", "OO", "UE"],
    "T": ["T", "TH"],
    "I": ["I", "Y", "EE"],
    "N": ["N", "M"],
    "*": ["A", "E", "I", "O", "U", "S"],
    "?": [""],
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def load_words(path: str) -> set[str]:
    words = set()
    for line in Path(path).read_text(errors="ignore").splitlines():
        w = re.sub(r"[^A-Za-z]", "", line).upper()
        if w:
            words.add(w)
    words.update(COMMON_ALLOW)
    return words


def variants(word: str, max_variants: int = 2000) -> list[str]:
    pools = []
    for ch in word:
        if ch not in TARGETABLE:
            return [word]
        pools.append(EQUIV.get(ch, [ch]))
    out = []
    for combo in itertools.product(*pools):
        out.append("".join(combo))
        if len(out) >= max_variants:
            break
    return out


def best_word(word: str, dictionary: set[str]) -> dict[str, Any]:
    if word in dictionary:
        return {"literal": word, "best": word, "status": "LITERAL_DICTIONARY", "edit_count": 0}
    candidates = [v for v in variants(word) if v in dictionary]
    if candidates:
        candidates.sort(key=lambda x: (abs(len(x) - len(word)), len(x), x))
        best = candidates[0]
        return {"literal": word, "best": best, "status": "PHONETIC_EQUIV_DICTIONARY", "edit_count": sum(1 for a, b in zip(word, best) if a != b) + abs(len(best) - len(word))}
    return {"literal": word, "best": word, "status": "NO_DICTIONARY_MATCH", "edit_count": 99}


def phrase_score(words: list[dict[str, Any]]) -> dict[str, Any]:
    matched = sum(1 for w in words if w["status"] != "NO_DICTIONARY_MATCH")
    literal = sum(1 for w in words if w["status"] == "LITERAL_DICTIONARY")
    total = len(words)
    ratio = round(matched / total, 3) if total else 0.0
    score = round(ratio * 100 + literal * 3 - sum(min(w["edit_count"], 8) for w in words) * 0.7, 3)
    return {"matched": matched, "literal": literal, "total": total, "match_ratio": ratio, "score": score}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    parser.add_argument("--dict", default=DICT_DEFAULT)
    args = parser.parse_args()
    dictionary = load_words(args.dict)
    results = []
    accepted = 0
    for phrase_id, literal in PHRASES:
        raw_words = literal.split()
        word_results = [best_word(w, dictionary) for w in raw_words]
        sc = phrase_score(word_results)
        normalized = " ".join(w["best"] for w in word_results)
        if phrase_id == "KNIGHTMARE_PHRASE" and sc["match_ratio"] >= 0.85:
            acceptance = "ACCEPT_EXTERNAL_PHONETIC_PHRASE_PROVISIONAL_NO_BOOK_PROMOTION"
            accepted += 1
        elif sc["match_ratio"] >= 0.75 and len(raw_words) <= 8:
            acceptance = "AUDIT_CANDIDATE_EXTERNAL_PHRASE_NO_PROMOTION"
        else:
            acceptance = "REJECT_PHONETIC_PHRASE_TOO_WEAK"
        results.append({"phrase_id": phrase_id, "literal": literal, "normalized": normalized, "acceptance": acceptance, "words": word_results, **sc})
    con = sqlite3.connect(args.db)
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists external_phonetic_equivalence_audit_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            phrase_count integer not null,
            accepted_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists external_phonetic_equivalence_audit_items(
            run_id integer not null,
            phrase_id text not null,
            literal text not null,
            normalized text not null,
            match_ratio real not null,
            score real not null,
            acceptance text not null,
            evidence_json text not null,
            primary key(run_id, phrase_id)
        );
        """
    )
    decision = "EXTERNAL_PHONETIC_EQUIVALENCE_HAS_PROVISIONAL_PHRASE" if accepted else "EXTERNAL_PHONETIC_EQUIVALENCE_NO_ACCEPTED_PHRASE"
    next_action = "Keep accepted phrase external/provisional only; do not promote book gloss from it."
    cur.execute(
        "insert into external_phonetic_equivalence_audit_runs(created_at,phrase_count,accepted_count,decision,next_action,payload_json) values (?,?,?,?,?,?)",
        (now(), len(results), accepted, decision, next_action, j({"results": results, "rules": EQUIV})),
    )
    run_id = cur.lastrowid
    for row in results:
        cur.execute(
            "insert into external_phonetic_equivalence_audit_items(run_id,phrase_id,literal,normalized,match_ratio,score,acceptance,evidence_json) values (?,?,?,?,?,?,?,?)",
            (run_id, row["phrase_id"], row["literal"], row["normalized"], row["match_ratio"], row["score"], row["acceptance"], j(row)),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "accepted_count": accepted, "results": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()

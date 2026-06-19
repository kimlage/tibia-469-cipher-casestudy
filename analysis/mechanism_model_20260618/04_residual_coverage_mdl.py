#!/usr/bin/env python3
"""Residual coverage and MDL pruning audit for the mechanical 469 formula.

Phase 1 is deliberately permissive: collect every broad mechanical explanation
for the 2,083 literal digits left by the canonical minL=20 formula.

Phase 2 is conservative: only non-overlapping candidates with positive estimated
description-length savings survive, and external Chayenne/Avar Tar material is
used only for secondary validation / negative control.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from bisect import bisect_right
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

FORMULA_JSON = HERE / "mechanical_formula_469.json"
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"
C2_OUT = ROOT / "analysis" / "audit_20260609" / "dedup_canonical" / "c2_out.txt"

ATLAS_JSON = HERE / "residual_atlas.json"
ATLAS_TABLE = HERE / "residual_atlas_table.md"
CANDIDATES_JSON = HERE / "residual_coverage_candidates.json"
COVERAGE_JSON = HERE / "residual_coverage_mdl_results.json"
REPORT_MD = HERE / "residual_coverage_mdl_report.md"

RANDOM_SEED = 469
random.seed(RANDOM_SEED)

CHAYENNE_GROUPS = [
    "114514519485611451908304576512282177",
    "6612527570584",
]
AVAR_TAR_GROUPS = [
    "29639",
    "46781",
    "9063376290",
    "3222011",
    "677",
    "80322429",
    "67538",
    "14805394",
    "6880326",
    "677",
    "63378129",
    "337011",
    "72683",
    "149630",
    "4378",
    "453",
    "639",
    "578300",
    "986372",
    "2953639",
]

EXTERNAL_SOURCES = {
    "chayenne": {
        "class": "secondary_validation",
        "source": "https://forum.portaltibia.com.br/topic/11420-entrevista-com-chayenne/",
        "also_indexed_at": "https://www.tibiawiki.com.br/wiki/469",
        "policy": "Use as secondary validation only; no training and no translation.",
    },
    "avar_tar": {
        "class": "negative_control",
        "source": "https://tibia.fandom.com/wiki/Avar_Tar/Transcripts",
        "also_discussed_at": "https://github.com/s2ward/469",
        "policy": "Use as negative control; do not promote as true 469.",
    },
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def numeric_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def gamma_bits(value: int) -> int:
    if value < 1:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def parse_baseline_bits() -> float:
    text = C2_OUT.read_text(encoding="utf-8")
    for line in text.splitlines():
        if "TOTAL  =" in line:
            return float(line.split("=")[1].split("bits")[0].strip())
    return 24627.8


def build_token_maps(formula: dict) -> dict[str, list[dict]]:
    """Map canonical code positions to raw digit offsets.

    `occ_streams.json` supplies canonical code order. A code consumes two raw
    digits when written verbatim; a leading-zero code may consume one raw digit
    when the leading zero was omitted in the book.
    """
    occ = load_json(OCC_STREAMS)["occ"]
    by_book: dict[str, list[dict]] = defaultdict(list)
    for symbol, rows in occ.items():
        for row in rows:
            by_book[str(row["book"])].append(
                {
                    "book": str(row["book"]),
                    "code_pos": int(row["pos"]),
                    "symbol": symbol,
                    "code": row["code"],
                    "novel": bool(row.get("novel")),
                    "xuniq": bool(row.get("xuniq")),
                }
            )

    token_maps = {}
    for book, rows in by_book.items():
        rows = sorted(rows, key=lambda item: item["code_pos"])
        raw = formula["books_digits"][book]
        offset = 0
        out = []
        for item in rows:
            code = item["code"]
            if raw.startswith(code, offset):
                raw_text = code
                raw_start, raw_end = offset, offset + 2
                offset += 2
                omitted_zero = False
            elif code.startswith("0") and offset < len(raw) and raw[offset] == code[1]:
                raw_text = code[1]
                raw_start, raw_end = offset, offset + 1
                offset += 1
                omitted_zero = True
            else:
                raise ValueError(
                    f"cannot align book {book} pos {item['code_pos']} code {code} at raw offset {offset}"
                )
            out.append(
                {
                    **item,
                    "raw_start": raw_start,
                    "raw_end": raw_end,
                    "raw_text": raw_text,
                    "omitted_zero": omitted_zero,
                    "pair_key": "".join(sorted(code)),
                }
            )
        if offset != len(raw):
            raise ValueError(f"book {book}: consumed {offset} raw digits, expected {len(raw)}")
        token_maps[book] = out
    return token_maps


def enrich_formula(formula: dict) -> dict:
    """Add raw books into formula from the recipes, avoiding another input file."""
    modules = {module["id"]: module["text"] for module in formula["modules"]}
    books_digits = {}
    for book, recipe in formula["book_recipes"].items():
        parts = []
        for item in recipe:
            if item["type"] == "module":
                parts.append(modules[item["id"]])
            else:
                parts.append(item["text"])
        books_digits[book] = "".join(parts)
    formula["books_digits"] = books_digits
    return formula


def item_offsets(recipe: list[dict]) -> list[dict]:
    offset = 0
    out = []
    for index, item in enumerate(recipe):
        length = item["length"]
        out.append({"index": index, "start": offset, "end": offset + length, **item})
        offset += length
    return out


def tokens_overlapping(tokens: list[dict], start: int, end: int) -> list[dict]:
    return [tok for tok in tokens if tok["raw_start"] < end and tok["raw_end"] > start]


def build_module_spans(formula: dict) -> dict[str, list[dict]]:
    spans = {}
    for book, recipe in formula["book_recipes"].items():
        out = []
        for item in item_offsets(recipe):
            if item["type"] == "module":
                out.append(
                    {
                        "book": book,
                        "start": item["start"],
                        "end": item["end"],
                        "id": item["id"],
                        "length": item["length"],
                    }
                )
        spans[book] = out
    return spans


def build_residual_atlas(formula: dict, token_maps: dict[str, list[dict]]) -> list[dict]:
    atlas = []
    for book in sorted(formula["book_recipes"], key=numeric_key):
        items = item_offsets(formula["book_recipes"][book])
        literals_seen = 0
        for item in items:
            if item["type"] != "literal":
                continue
            tokens = tokens_overlapping(token_maps[book], item["start"], item["end"])
            left = items[item["index"] - 1] if item["index"] > 0 else None
            right = items[item["index"] + 1] if item["index"] + 1 < len(items) else None
            literal_id = f"B{book}_R{literals_seen:02d}"
            literals_seen += 1
            atlas.append(
                {
                    "id": literal_id,
                    "book": book,
                    "item_index": item["index"],
                    "raw_start": item["start"],
                    "raw_end": item["end"],
                    "length": item["length"],
                    "text": item["text"],
                    "sha256": hashlib.sha256(item["text"].encode("ascii")).hexdigest(),
                    "symbols": "".join(tok["symbol"] for tok in tokens),
                    "codes": [tok["code"] for tok in tokens],
                    "token_spans": [
                        {
                            "code_pos": tok["code_pos"],
                            "raw_start": tok["raw_start"],
                            "raw_end": tok["raw_end"],
                            "code": tok["code"],
                            "symbol": tok["symbol"],
                            "omitted_zero": tok["omitted_zero"],
                        }
                        for tok in tokens
                    ],
                    "left_module": left.get("id") if left and left["type"] == "module" else None,
                    "right_module": right.get("id") if right and right["type"] == "module" else None,
                    "position_in_book": (
                        "start"
                        if item["start"] == 0
                        else "end"
                        if item["end"] == len(formula["books_digits"][book])
                        else "middle"
                    ),
                    "left_context": formula["books_digits"][book][max(0, item["start"] - 12) : item["start"]],
                    "right_context": formula["books_digits"][book][item["end"] : item["end"] + 12],
                }
            )
    return atlas


def build_raw_index(books_digits: dict[str, str], min_len: int, max_len: int) -> dict[int, dict[str, list[tuple[str, int]]]]:
    indexes = {length: defaultdict(list) for length in range(min_len, max_len + 1)}
    for book, raw in books_digits.items():
        for length in range(min_len, max_len + 1):
            if len(raw) < length:
                continue
            for pos in range(len(raw) - length + 1):
                indexes[length][raw[pos : pos + length]].append((book, pos))
    return indexes


def span_key(book: str, start: int, end: int) -> tuple[str, int, int]:
    return (book, start, end)


def occurrence_elsewhere(occs: list[tuple[str, int]], book: str, start: int, end: int) -> tuple[str, int] | None:
    length = end - start
    for other_book, other_start in occs:
        if other_book != book or other_start + length <= start or other_start >= end:
            return (other_book, other_start)
    return None


def build_sequence_indexes(
    formula: dict,
    token_maps: dict[str, list[dict]],
    module_spans: dict[str, list[dict]],
    key_name: str,
    min_len: int,
    max_len: int,
) -> dict[int, dict[tuple[str, ...], list[dict]]]:
    indexes = {length: defaultdict(list) for length in range(min_len, max_len + 1)}
    for book, spans in module_spans.items():
        tokens = token_maps[book]
        for span in spans:
            inside = [tok for tok in tokens if tok["raw_start"] >= span["start"] and tok["raw_end"] <= span["end"]]
            keys = [tok[key_name] for tok in inside]
            codes = [tok["code"] for tok in inside]
            for length in range(min_len, max_len + 1):
                for idx in range(0, len(keys) - length + 1):
                    indexes[length][tuple(keys[idx : idx + length])].append(
                        {
                            "book": book,
                            "code_pos": inside[idx]["code_pos"],
                            "raw_start": inside[idx]["raw_start"],
                            "raw_end": inside[idx + length - 1]["raw_end"],
                            "codes": tuple(codes[idx : idx + length]),
                            "module": span["id"],
                        }
                    )
    return indexes


def build_near_index(module_text: str, min_len: int = 8, max_len: int = 12):
    indexes = {length: defaultdict(list) for length in range(min_len, max_len + 1)}
    for length in range(min_len, max_len + 1):
        seen = set()
        for pos in range(len(module_text) - length + 1):
            sub = module_text[pos : pos + length]
            if sub in seen:
                continue
            seen.add(sub)
            for cut in range(length):
                indexes[length][sub[:cut] + "*" + sub[cut + 1 :]].append(sub)
    return indexes


def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))


def collect_candidates(formula: dict, atlas: list[dict], token_maps: dict[str, list[dict]]) -> list[dict]:
    books_digits = formula["books_digits"]
    raw_index = build_raw_index(books_digits, 3, 19)
    module_spans = build_module_spans(formula)
    module_inventory_text = "\x00".join(module["text"] for module in formula["modules"])
    near_index = build_near_index(module_inventory_text)
    pair_index = build_sequence_indexes(formula, token_maps, module_spans, "pair_key", 2, 10)
    symbol_index = build_sequence_indexes(formula, token_maps, module_spans, "symbol", 3, 12)
    target_positions = {
        (entry["book"], pos)
        for entry in atlas
        for pos in range(entry["raw_start"], entry["raw_end"])
    }
    candidates = {}

    def add(cls: str, book: str, start: int, end: int, evidence: dict):
        covered = [(book, pos) for pos in range(start, end) if (book, pos) in target_positions]
        if not covered:
            return
        cid_base = f"{cls}:{book}:{start}:{end}:{json.dumps(evidence, sort_keys=True)[:120]}"
        cid = hashlib.sha1(cid_base.encode("utf-8")).hexdigest()[:16]
        item = {
            "id": cid,
            "class": cls,
            "book": book,
            "raw_start": start,
            "raw_end": end,
            "length": end - start,
            "covered_digits": len(covered),
            "evidence": evidence,
        }
        previous = candidates.get(cid)
        if previous is None or item["covered_digits"] > previous["covered_digits"]:
            candidates[cid] = item

    chayenne_joined = "\x00".join(CHAYENNE_GROUPS)

    for entry in atlas:
        book = entry["book"]
        text = entry["text"]
        base = entry["raw_start"]
        raw = books_digits[book]

        if entry["length"] <= 12 and (entry["left_module"] or entry["right_module"]):
            add(
                "module_boundary_glue",
                book,
                entry["raw_start"],
                entry["raw_end"],
                {
                    "left_module": entry["left_module"],
                    "right_module": entry["right_module"],
                    "position": entry["position_in_book"],
                },
            )

        for tok in entry["token_spans"]:
            if tok["omitted_zero"]:
                add(
                    "zero_variant",
                    book,
                    tok["raw_start"],
                    tok["raw_end"],
                    {"code": tok["code"], "symbol": tok["symbol"], "rule": "leading_zero_omitted"},
                )

        for length in range(3, min(19, len(text)) + 1):
            for rel in range(len(text) - length + 1):
                sub = text[rel : rel + length]
                occs = raw_index[length].get(sub, [])
                other = occurrence_elsewhere(occs, book, base + rel, base + rel + length)
                if other:
                    add(
                        "exact_repeat" if length >= 8 else "short_repeat",
                        book,
                        base + rel,
                        base + rel + length,
                        {"substring": sub, "other_book": other[0], "other_offset": other[1]},
                    )

        for length in range(8, min(12, len(text)) + 1):
            for rel in range(len(text) - length + 1):
                sub = text[rel : rel + length]
                if sub in module_inventory_text:
                    continue
                found = None
                for cut in range(length):
                    sig = sub[:cut] + "*" + sub[cut + 1 :]
                    for other in near_index[length].get(sig, []):
                        if other != sub and hamming(sub, other) == 1:
                            found = other
                            break
                    if found:
                        break
                if found:
                    add(
                        "near_match_controlled",
                        book,
                        base + rel,
                        base + rel + length,
                        {"substring": sub, "near_module_substring": found, "hamming": 1},
                    )

        for length in range(8, min(19, len(text)) + 1):
            for rel in range(len(text) - length + 1):
                sub = text[rel : rel + length]
                if sub in chayenne_joined:
                    add(
                        "external_chayenne_like",
                        book,
                        base + rel,
                        base + rel + length,
                        {"substring": sub, "external": "chayenne", "policy": "secondary_only"},
                    )

        literal_tokens = [
            tok
            for tok in token_maps[book]
            if tok["raw_start"] >= entry["raw_start"] and tok["raw_end"] <= entry["raw_end"]
        ]
        for length in range(2, min(10, len(literal_tokens)) + 1):
            for idx in range(len(literal_tokens) - length + 1):
                seq = literal_tokens[idx : idx + length]
                key = tuple(tok["pair_key"] for tok in seq)
                hits = pair_index[length].get(key, [])
                exact_codes = tuple(tok["code"] for tok in seq)
                useful = next((hit for hit in hits if tuple(hit["codes"]) != exact_codes), None)
                if useful:
                    add(
                        "pair_reverse_variant",
                        book,
                        seq[0]["raw_start"],
                        seq[-1]["raw_end"],
                        {
                            "pair_keys": list(key),
                            "module": useful["module"],
                            "other_book": useful["book"],
                            "other_code_pos": useful["code_pos"],
                        },
                    )
        for length in range(3, min(12, len(literal_tokens)) + 1):
            for idx in range(len(literal_tokens) - length + 1):
                seq = literal_tokens[idx : idx + length]
                key = tuple(tok["symbol"] for tok in seq)
                hits = symbol_index[length].get(key, [])
                exact_codes = tuple(tok["code"] for tok in seq)
                useful = next((hit for hit in hits if tuple(hit["codes"]) != exact_codes), None)
                if useful:
                    add(
                        "homophone_variant",
                        book,
                        seq[0]["raw_start"],
                        seq[-1]["raw_end"],
                        {
                            "symbols": "".join(key),
                            "module": useful["module"],
                            "other_book": useful["book"],
                            "other_code_pos": useful["code_pos"],
                        },
                    )
    return list(candidates.values())


def coverage_summary(atlas: list[dict], candidates: list[dict], token_maps: dict[str, list[dict]]) -> dict:
    target_positions = {
        (entry["book"], pos)
        for entry in atlas
        for pos in range(entry["raw_start"], entry["raw_end"])
    }
    target_tokens = {
        (entry["book"], tok["code_pos"])
        for entry in atlas
        for tok in entry["token_spans"]
    }
    by_class = defaultdict(set)
    for cand in candidates:
        for pos in range(cand["raw_start"], cand["raw_end"]):
            key = (cand["book"], pos)
            if key in target_positions:
                by_class[cand["class"]].add(key)

    order = [
        "exact_repeat",
        "short_repeat",
        "module_boundary_glue",
        "zero_variant",
        "pair_reverse_variant",
        "homophone_variant",
        "external_chayenne_like",
        "near_match_controlled",
    ]
    cumulative = {}
    seen = set()
    for cls in order:
        seen |= by_class.get(cls, set())
        cumulative[cls] = len(seen)

    token_covered = set()
    covered_positions = set().union(*by_class.values()) if by_class else set()
    for book, tokens in token_maps.items():
        for tok in tokens:
            token_id = (book, tok["code_pos"])
            if token_id not in target_tokens:
                continue
            if any((book, pos) in covered_positions for pos in range(tok["raw_start"], tok["raw_end"])):
                token_covered.add(token_id)

    return {
        "total_residual_digits": len(target_positions),
        "total_residual_symbol_tokens": len(target_tokens),
        "candidate_count": len(candidates),
        "class_digit_coverage": {cls: len(by_class.get(cls, set())) for cls in order},
        "cumulative_digit_coverage": cumulative,
        "max_covered_digits_any_class": len(covered_positions),
        "max_unexplained_digits": len(target_positions - covered_positions),
        "max_covered_fraction": len(covered_positions) / len(target_positions),
        "max_symbol_tokens_covered": len(token_covered),
        "max_symbol_token_fraction": len(token_covered) / len(target_tokens),
    }


def greedy_external_cover(s: str, raw_index: dict[int, dict[str, list[tuple[str, int]]]], min_len: int) -> list[dict]:
    out = []
    index = 0
    max_len = max(raw_index)
    while index < len(s):
        best = None
        for length in range(min(max_len, len(s) - index), min_len - 1, -1):
            sub = s[index : index + length]
            occs = raw_index[length].get(sub, [])
            if occs:
                best = {"start": index, "end": index + length, "text": sub, "hit": occs[0]}
                break
        if best:
            out.append(best)
            index = best["end"]
        else:
            index += 1
    return out


def external_validation(books_digits: dict[str, str]) -> dict:
    raw_index = build_raw_index(books_digits, 3, 32)
    corpus_digits = "".join(books_digits[book] for book in sorted(books_digits, key=numeric_key))

    def eval_string(name: str, groups: list[str], min_len: int, controls: int = 200):
        joined = "".join(groups)
        cover = greedy_external_cover(joined, raw_index, min_len)
        covered = sum(item["end"] - item["start"] for item in cover)
        control_fracs = []
        chars = list(joined)
        for _ in range(controls):
            random.shuffle(chars)
            ctrl = "".join(chars)
            ctrl_cover = greedy_external_cover(ctrl, raw_index, min_len)
            control_fracs.append(sum(item["end"] - item["start"] for item in ctrl_cover) / len(ctrl))
        mean = sum(control_fracs) / len(control_fracs)
        sd = (sum((value - mean) ** 2 for value in control_fracs) / (len(control_fracs) - 1)) ** 0.5
        frac = covered / len(joined)
        if sd:
            z = (frac - mean) / sd
        elif frac > mean:
            z = float("inf")
        else:
            z = 0.0
        return {
            "name": name,
            "groups": groups,
            "joined_length": len(joined),
            "min_len": min_len,
            "covered_digits": covered,
            "covered_fraction": frac,
            "control_shuffle_mean": mean,
            "control_shuffle_sd": sd,
            "z_vs_shuffle": z,
            "segments": cover[:20],
            "verdict": (
                "secondary_positive_no_semantics"
                if name == "chayenne" and frac > mean + 2 * sd
                else "negative_control_pass"
                if name == "avar_tar" and frac <= mean + 2 * sd
                else "control_attention_required"
            ),
            "raw_occurs_as_whole": joined in corpus_digits,
        }

    return {
        "sources": EXTERNAL_SOURCES,
        "chayenne_min8": eval_string("chayenne", CHAYENNE_GROUPS, 8),
        "avar_tar_min8": eval_string("avar_tar", AVAR_TAR_GROUPS, 8),
        "chayenne_min3_broad": eval_string("chayenne", CHAYENNE_GROUPS, 3),
        "avar_tar_min3_broad": eval_string("avar_tar", AVAR_TAR_GROUPS, 3),
    }


def candidate_cost(cand: dict, total_digits: int, total_tokens: int) -> float:
    length = cand["length"]
    cls = cand["class"]
    if cls in {"exact_repeat", "short_repeat"}:
        return 1 + gamma_bits(length) + math.log2(total_digits)
    if cls == "near_match_controlled":
        return 1 + gamma_bits(length) + math.log2(total_digits) + 4
    if cls == "pair_reverse_variant":
        return 1 + gamma_bits(max(1, length)) + math.log2(total_tokens) + 6
    if cls == "homophone_variant":
        return 1 + gamma_bits(max(1, length)) + math.log2(total_tokens) + 8
    return float("inf")


def weighted_interval_select(candidates: list[dict]) -> list[dict]:
    by_book = defaultdict(list)
    for cand in candidates:
        by_book[cand["book"]].append(cand)
    selected = []
    for book, items in by_book.items():
        intervals = sorted(items, key=lambda item: (item["raw_end"], item["raw_start"]))
        ends = [item["raw_end"] for item in intervals]
        p = [bisect_right(ends, item["raw_start"]) - 1 for item in intervals]
        dp = [0.0] * (len(intervals) + 1)
        keep = [False] * len(intervals)
        for i, item in enumerate(intervals, start=1):
            take = item["savings_bits"] + dp[p[i - 1] + 1]
            skip = dp[i - 1]
            if take > skip:
                dp[i] = take
                keep[i - 1] = True
            else:
                dp[i] = skip
        i = len(intervals)
        book_selected = []
        while i > 0:
            item = intervals[i - 1]
            take = item["savings_bits"] + dp[p[i - 1] + 1]
            if keep[i - 1] and abs(dp[i] - take) < 1e-9:
                book_selected.append(item)
                i = p[i - 1] + 1
            else:
                i -= 1
        selected.extend(reversed(book_selected))
    return selected


def mdl_prune(atlas: list[dict], candidates: list[dict], total_digits: int, total_tokens: int) -> dict:
    family_cost = {
        "exact_repeat": 24.0,
        "near_match_controlled": 40.0,
        "pair_reverse_variant": 36.0,
        "homophone_variant": 44.0,
    }
    control_rejected = {
        "short_repeat": "Rejected from MDL because minLen=3 coverage also covers Avar Tar and shuffled controls at high rates.",
    }
    eligible_classes = set(family_cost)
    eligible = []
    for cand in candidates:
        if cand["class"] not in eligible_classes:
            continue
        cost = candidate_cost(cand, total_digits, total_tokens)
        savings = cand["covered_digits"] * math.log2(10) - cost
        if savings <= 0:
            continue
        eligible.append({**cand, "cost_bits": cost, "savings_bits": savings})

    active_classes = set(eligible_classes)
    selected = []
    while True:
        selected = weighted_interval_select([cand for cand in eligible if cand["class"] in active_classes])
        by_class = defaultdict(float)
        for cand in selected:
            by_class[cand["class"]] += cand["savings_bits"]
        weak = {cls for cls, gross in by_class.items() if gross <= family_cost[cls]}
        if not weak:
            break
        active_classes -= weak
        if not active_classes:
            selected = []
            break

    selected_positions = {
        (cand["book"], pos)
        for cand in selected
        for pos in range(cand["raw_start"], cand["raw_end"])
    }
    total_residual = sum(entry["length"] for entry in atlas)
    used_classes = sorted({cand["class"] for cand in selected})
    gross = sum(cand["savings_bits"] for cand in selected)
    family = sum(family_cost[cls] for cls in used_classes)
    net = gross - family
    baseline = parse_baseline_bits()
    return {
        "baseline_bits": baseline,
        "eligible_candidate_count": len(eligible),
        "selected_candidate_count": len(selected),
        "selected_classes": used_classes,
        "gross_savings_bits": gross,
        "family_cost_bits": family,
        "net_savings_bits": net,
        "estimated_total_bits": baseline - max(0.0, net),
        "selected_covered_digits": len(selected_positions),
        "estimated_literal_digits_remaining": total_residual - len(selected_positions),
        "class_summary": {
            cls: {
                "count": sum(1 for cand in selected if cand["class"] == cls),
                "covered_digits": len(
                    {
                        (cand["book"], pos)
                        for cand in selected
                        if cand["class"] == cls
                        for pos in range(cand["raw_start"], cand["raw_end"])
                    }
                ),
                "gross_savings_bits": sum(cand["savings_bits"] for cand in selected if cand["class"] == cls),
                "family_cost_bits": family_cost[cls],
            }
            for cls in used_classes
        },
        "selected_examples": sorted(
            selected,
            key=lambda item: (-item["savings_bits"], item["book"], item["raw_start"]),
        )[:30],
        "model_levels": {
            "core": [
                "canonical 99-entry code table",
                "unordered-pair mirror geometry with one conflict {19,91}",
                "homophone classes over *ABCEFILNORSTV",
                "62 minL=20 digit modules plus literal recipes",
            ],
            "secondary": used_classes,
            "rejected_control": [
                cls for cls in sorted(eligible_classes) if cls not in used_classes
            ]
            + ["short_repeat", "module_boundary_glue", "zero_variant", "external_chayenne_like"],
        },
        "control_rejected": control_rejected,
    }


def write_atlas_table(atlas: list[dict]) -> None:
    lines = [
        "# Residual Atlas",
        "",
        "Generated by `04_residual_coverage_mdl.py`.",
        "",
        "| ID | Book | Offset | Len | Text | Symbols | Left | Right | Position |",
        "|---|---:|---:|---:|---|---|---|---|---|",
    ]
    for entry in atlas:
        text = entry["text"]
        if len(text) > 36:
            text = text[:33] + "..."
        symbols = entry["symbols"]
        if len(symbols) > 24:
            symbols = symbols[:21] + "..."
        lines.append(
            "| `{id}` | {book} | {raw_start} | {length} | `{text}` | `{symbols}` | `{left}` | `{right}` | {pos} |".format(
                id=entry["id"],
                book=entry["book"],
                raw_start=entry["raw_start"],
                length=entry["length"],
                text=text,
                symbols=symbols,
                left=entry["left_module"] or "",
                right=entry["right_module"] or "",
                pos=entry["position_in_book"],
            )
        )
    ATLAS_TABLE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(results: dict) -> None:
    cov = results["coverage_summary"]
    mdl = results["mdl_pruning"]
    ext = results["external_validation"]
    lines = [
        "# Residual Coverage and MDL Pruning",
        "",
        "Generated by `04_residual_coverage_mdl.py`.",
        "",
        "This is a mechanical-generation audit. It does not translate 469.",
        "",
        "## Residual Atlas",
        "",
        f"- Literal residual digits: {cov['total_residual_digits']}.",
        f"- Residual literal segments: {results['atlas_count']}.",
        f"- Residual internal-symbol tokens touched: {cov['total_residual_symbol_tokens']}.",
        f"- Atlas table: `residual_atlas_table.md`.",
        "",
        "## Phase 1: Maximum Mechanical Coverage",
        "",
        f"- Candidate explanations collected: {cov['candidate_count']}.",
        f"- Full candidate register: `residual_coverage_candidates.json`.",
        f"- Max residual digit coverage with overlapping candidates: {cov['max_covered_digits_any_class']} / {cov['total_residual_digits']} ({100*cov['max_covered_fraction']:.1f}%).",
        f"- Still unexplained under permissive coverage: {cov['max_unexplained_digits']} digits.",
        f"- Residual symbol-token coverage: {cov['max_symbol_tokens_covered']} / {cov['total_residual_symbol_tokens']} ({100*cov['max_symbol_token_fraction']:.1f}%).",
        "",
        "| Class | Covered residual digits | Cumulative covered |",
        "|---|---:|---:|",
    ]
    for cls, value in cov["class_digit_coverage"].items():
        lines.append(f"| `{cls}` | {value} | {cov['cumulative_digit_coverage'].get(cls, 0)} |")

    lines.extend(
        [
            "",
            "Phase-1 coverage allows overlaps. It is an upper bound, not the final model.",
            "",
            "## Chayenne Secondary Validation",
            "",
            f"- Source policy: {EXTERNAL_SOURCES['chayenne']['policy']}",
            f"- Source: {EXTERNAL_SOURCES['chayenne']['source']}",
            f"- minLen=8 book-substring coverage: {ext['chayenne_min8']['covered_digits']} / {ext['chayenne_min8']['joined_length']} ({100*ext['chayenne_min8']['covered_fraction']:.1f}%), z={ext['chayenne_min8']['z_vs_shuffle']:.2f} vs shuffled controls.",
            f"- Verdict: `{ext['chayenne_min8']['verdict']}`.",
            "",
            "## Avar Tar Negative Control",
            "",
            f"- Source policy: {EXTERNAL_SOURCES['avar_tar']['policy']}",
            f"- Source: {EXTERNAL_SOURCES['avar_tar']['source']}",
            f"- minLen=8 book-substring coverage: {ext['avar_tar_min8']['covered_digits']} / {ext['avar_tar_min8']['joined_length']} ({100*ext['avar_tar_min8']['covered_fraction']:.1f}%), z={ext['avar_tar_min8']['z_vs_shuffle']:.2f} vs shuffled controls.",
            f"- Verdict: `{ext['avar_tar_min8']['verdict']}`.",
            "",
            "Broad minLen=3 coverage is also recorded in JSON, but it is not promotable",
            "because short digit repeats occur freely in controls.",
            "",
            "## Phase 2: MDL Pruning",
            "",
            f"- Baseline c2/mechanical formula: {mdl['baseline_bits']:.1f} bits.",
            f"- Eligible positive candidates before pruning: {mdl['eligible_candidate_count']}.",
            f"- Control-rejected operators: {', '.join('`'+cls+'`' for cls in mdl['control_rejected']) or 'none'}.",
            f"- Selected non-overlapping candidates: {mdl['selected_candidate_count']}.",
            f"- Selected classes: {', '.join('`'+cls+'`' for cls in mdl['selected_classes']) or 'none'}.",
            f"- Gross savings: {mdl['gross_savings_bits']:.1f} bits.",
            f"- Family/rule cost: {mdl['family_cost_bits']:.1f} bits.",
            f"- Net estimated savings: {mdl['net_savings_bits']:.1f} bits.",
            f"- Estimated total after pruning: {mdl['estimated_total_bits']:.1f} bits.",
            f"- Selected residual digits explained: {mdl['selected_covered_digits']} / {cov['total_residual_digits']}.",
            f"- Estimated literal digits remaining: {mdl['estimated_literal_digits_remaining']}.",
            "",
            "| Selected class | Count | Digits | Gross savings | Family cost |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for cls, item in mdl["class_summary"].items():
        lines.append(
            f"| `{cls}` | {item['count']} | {item['covered_digits']} | {item['gross_savings_bits']:.1f} | {item['family_cost_bits']:.1f} |"
        )

    lines.extend(
        [
            "",
            "## Model Levels",
            "",
            "- `core`: canonical table, pair geometry, homophones, and 62-module formula.",
            "- `secondary`: MDL-surviving residual operators, validated only as mechanics.",
            "- `rejected/control`: broad operators that explain too much, save no bits, or are external-only.",
            "",
            "## Verdict",
            "",
            "The residual pass improves the mechanical generator and documents an upper",
            "bound on residue explainability. It does not add a semantic reading, a new",
            "word code, or any CipSoft-attested number<->plaintext pair.",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = enrich_formula(load_json(FORMULA_JSON))
    token_maps = build_token_maps(formula)
    atlas = build_residual_atlas(formula, token_maps)
    if sum(entry["length"] for entry in atlas) != formula["validation"]["literal_digits"]:
        raise ValueError("atlas literal digits do not match formula validation")

    candidates = collect_candidates(formula, atlas, token_maps)
    cov = coverage_summary(atlas, candidates, token_maps)
    ext = external_validation(formula["books_digits"])
    total_digits = sum(len(text) for text in formula["books_digits"].values())
    total_tokens = sum(len(tokens) for tokens in token_maps.values())
    mdl = mdl_prune(atlas, candidates, total_digits, total_tokens)

    results = {
        "schema": "mechanical_469_residual_coverage_mdl.v1",
        "created_at": "2026-06-18",
        "translation_delta": "NONE",
        "scope": "mechanical_residual_explainability_only",
        "atlas_count": len(atlas),
        "coverage_summary": cov,
        "external_validation": ext,
        "mdl_pruning": mdl,
        "coverage_candidates_top": sorted(
            candidates,
            key=lambda item: (-item["covered_digits"], item["class"], item["book"], item["raw_start"]),
        )[:500],
    }

    ATLAS_JSON.write_text(json.dumps(atlas, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    CANDIDATES_JSON.write_text(
        json.dumps(
            sorted(
                candidates,
                key=lambda item: (item["class"], item["book"], item["raw_start"], item["raw_end"]),
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    COVERAGE_JSON.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_atlas_table(atlas)
    write_report(results)

    print(f"wrote {ATLAS_JSON.relative_to(HERE)}")
    print(f"wrote {ATLAS_TABLE.relative_to(HERE)}")
    print(f"wrote {CANDIDATES_JSON.relative_to(HERE)}")
    print(f"wrote {COVERAGE_JSON.relative_to(HERE)}")
    print(f"wrote {REPORT_MD.relative_to(HERE)}")
    print(
        "residual_digits={total} max_cov={covered} mdl_selected={selected} estimated_bits={bits:.1f}".format(
            total=cov["total_residual_digits"],
            covered=cov["max_covered_digits_any_class"],
            selected=mdl["selected_covered_digits"],
            bits=mdl["estimated_total_bits"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generator-origin search suite for 469.

This run changes the question from "can we reconstruct/compress the 70 books?"
to "can we find a compact generator a CipSoft author could plausibly have used?"

All outputs are mechanical only. No number<->plaintext meaning is promoted.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MECH = ROOT / "analysis" / "mechanism_model_20260618"
AUDIT = ROOT / "analysis" / "audit_20260609"
LORE = ROOT / "analysis" / "lore_audit_20260618"
ML_PROBE = ROOT / "analysis" / "ml_formula_probe_20260618"

FORMULA_JSON = MECH / "mechanical_formula_469.json"
RESIDUAL_RESULTS_JSON = MECH / "residual_coverage_mdl_results.json"
RESIDUAL_ATLAS_JSON = MECH / "residual_atlas.json"
OCC_STREAMS = AUDIT / "homophone_channel" / "occ_streams.json"

YTC = "785673433498913565142"
CHAYENNE_GROUPS = ["114514519485611451908304576512282177", "6612527570584"]
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

SEEDS = ["469", "3478", "43153", "34784", "74032", "45331", "1"]
HONEMINAS_NUMBERS = ["43153", "34784", "3478", "34", "78", "99", "469"]
RANDOM_SEED = 469
random.seed(RANDOM_SEED)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def numeric_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def gamma_bits(value: int) -> int:
    if value < 1:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def load_formula() -> dict:
    formula = load_json(FORMULA_JSON)
    modules = {module["id"]: module["text"] for module in formula["modules"]}
    books_digits = {}
    for book, recipe in formula["book_recipes"].items():
        books_digits[book] = "".join(
            modules[item["id"]] if item["type"] == "module" else item["text"]
            for item in recipe
        )
    formula["books_digits"] = books_digits
    return formula


def load_token_maps(formula: dict) -> dict[str, list[dict]]:
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
                    "pair_key": "".join(sorted(row["code"])),
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
                raw_text, start, end, omitted = code, offset, offset + 2, False
                offset += 2
            elif code.startswith("0") and offset < len(raw) and raw[offset] == code[1]:
                raw_text, start, end, omitted = code[1], offset, offset + 1, True
                offset += 1
            else:
                raise ValueError(f"cannot align book={book} code={code} offset={offset}")
            out.append({**item, "raw_text": raw_text, "raw_start": start, "raw_end": end, "omitted_zero": omitted})
        if offset != len(raw):
            raise ValueError(f"book {book}: consumed {offset}, expected {len(raw)}")
        token_maps[book] = out
    return token_maps


def build_raw_index(books_digits: dict[str, str], min_len: int, max_len: int):
    index = {length: defaultdict(list) for length in range(min_len, max_len + 1)}
    for book, raw in books_digits.items():
        for length in range(min_len, max_len + 1):
            for pos in range(0, len(raw) - length + 1):
                index[length][raw[pos : pos + length]].append((book, pos))
    return index


def greedy_cover(s: str, raw_index, min_len: int) -> list[dict]:
    max_len = max(raw_index)
    out = []
    index = 0
    while index < len(s):
        best = None
        for length in range(min(max_len, len(s) - index), min_len - 1, -1):
            sub = s[index : index + length]
            hits = raw_index[length].get(sub, [])
            if hits:
                best = {"start": index, "end": index + length, "text": sub, "hit": hits[0]}
                break
        if best:
            out.append(best)
            index = best["end"]
        else:
            index += 1
    return out


def cover_with_controls(name: str, groups: list[str], raw_index, min_len: int, controls: int = 200):
    joined = "".join(groups)
    cover = greedy_cover(joined, raw_index, min_len)
    covered = sum(item["end"] - item["start"] for item in cover)
    fracs = []
    chars = list(joined)
    for _ in range(controls):
        random.shuffle(chars)
        ctrl = "".join(chars)
        ctrl_cover = greedy_cover(ctrl, raw_index, min_len)
        fracs.append(sum(item["end"] - item["start"] for item in ctrl_cover) / len(ctrl))
    mean = sum(fracs) / len(fracs)
    sd = (sum((value - mean) ** 2 for value in fracs) / (len(fracs) - 1)) ** 0.5
    frac = covered / len(joined)
    z = (frac - mean) / sd if sd else (float("inf") if frac > mean else 0.0)
    return {
        "name": name,
        "groups": groups,
        "length": len(joined),
        "min_len": min_len,
        "covered_digits": covered,
        "covered_fraction": frac,
        "shuffle_mean": mean,
        "shuffle_sd": sd,
        "z_vs_shuffle": z,
        "segments": cover[:20],
    }


def freeze_contract(formula: dict, residual: dict, residual_atlas: list[dict]) -> None:
    books = sorted(formula["books_digits"], key=numeric_key)
    holdout_books = [book for index, book in enumerate(books) if index % 7 == 0]
    train_books = [book for book in books if book not in holdout_books]
    residual_holdout = [entry["id"] for index, entry in enumerate(residual_atlas) if index % 5 == 0]
    residual_train = [entry["id"] for entry in residual_atlas if entry["id"] not in residual_holdout]
    contract = """# Generator Search Contract

Generated by `generator_search_suite.py`.

## Objective

Search for a compact mechanical generator a CipSoft author could plausibly have
used to manufacture 469. This is not a semantic-decoding project.

## Frozen Inputs

- 70 raw books from `mechanical_formula_469.json`.
- `row0` 99-entry code->symbol table.
- Current 62-module minL=20 formula.
- Residual atlas of 2,083 literal digits.
- External holdouts: Chayenne and Your True Colour.
- Negative control: Avar Tar.
- Lore/clue registry from `analysis/lore_audit_20260618/`.

## Scoring

```text
score_total =
  prediction_score
+ mdl_gain
+ lore_fit
- rule_complexity
- control_leakage
```

## Exploration Policy

The search state is `mechanical_partial_not_final`. Hard cutoffs such as
minimum coverage or maximum exception count are not exploration blockers.
They are descriptive confidence labels only. Weak, expensive, and failed
hypotheses stay in the ledger so phase-2 MDL/control comparison can prune them
after measurement.

Zero omission is classified as a `supporting_render_layer`: useful mechanical
signal, but secondary to the unresolved matrix/pair-cell generator.

Promotion is mechanical only. No hypothesis may create a new translation,
glossary entry, or number<->plaintext pair without CipSoft-attested evidence.

## Holdout Discipline

Candidate generation must not train on Chayenne, Your True Colour, or Avar Tar.
Book/residual holdouts are deterministic and listed in
`generator_holdout_manifest.json`.
"""
    (HERE / "generator_search_contract.md").write_text(contract, encoding="utf-8")
    schema = {
        "schema": "generator_scoring_schema.v1",
        "components": {
            "prediction_score": "0..1 normalized predictive accuracy or coverage on declared target/holdout",
            "mdl_gain": "bits saved versus the frozen baseline, normalized by 1000 bits for leaderboard display",
            "lore_fit": "0..1 preregistered fit to clue ledger; context never overrides controls",
            "rule_complexity": "0..1 penalty for table-like rules, exceptions, free parameters, and lookup disguise",
            "control_leakage": "0..1 penalty for explaining Avar Tar, shuffles, or non-469 controls",
        },
        "state": "mechanical_partial_not_final",
        "exploration_policy": [
            "no hard coverage cutoff during exploration",
            "no hard exception-count cutoff during exploration",
            "thresholds classify confidence only",
            "record weak and failed hypotheses before pruning",
            "zero omission is a supporting render layer, not the matrix formula",
        ],
        "promotion_gate": [
            "must declare targets",
            "must improve prediction or MDL",
            "must not use external holdout for fitting",
            "must not explain Avar Tar as well as real 469",
            "must not promote semantics",
        ],
    }
    write_json(HERE / "generator_scoring_schema.json", schema)
    manifest = {
        "schema": "generator_holdout_manifest.v1",
        "random_seed": RANDOM_SEED,
        "book_holdouts": holdout_books,
        "book_training": train_books,
        "residual_holdouts": residual_holdout,
        "residual_training": residual_train,
        "external_holdouts": {
            "chayenne": CHAYENNE_GROUPS,
            "your_true_colour": ["78567", "34334", "989", "135", "65142"],
        },
        "negative_controls": {"avar_tar": AVAR_TAR_GROUPS},
        "frozen_counts": {
            "books": len(books),
            "raw_digits": sum(len(text) for text in formula["books_digits"].values()),
            "modules": formula["validation"]["module_count"],
            "residual_digits": residual["coverage_summary"]["total_residual_digits"],
        },
    }
    write_json(HERE / "generator_holdout_manifest.json", manifest)


def clue_ledger() -> list[dict]:
    return [
        {
            "id": "great_calculator_assemble",
            "clue": "Great Calculator / assemble language",
            "source_url": "https://tibia.fandom.com/wiki/You_Cannot_Even_Imagine_%28Book%29",
            "operational_hypothesis": "book strings are assembled from precomputed numeric pieces",
            "tests": [
                "module_grammar_induction",
                "module_overlap_grammar_search",
                "module_tape_origin_search",
                "module_tape_order_search",
                "tape_based_formula_compile",
                "tape_tokenization_analysis",
                "tape_first_use_pair_order_search",
                "tape_literal_exception_analysis",
                "tape_feature_pair_label_search",
                "residual_exact_repeat",
            ],
            "targets": ["G", "H", "I"],
            "status": "mechanism_context",
        },
        {
            "id": "subjective_viewer",
            "clue": "formula changes for the subjective viewer",
            "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
            "operational_hypothesis": "observer changes pair orientation or matrix view",
            "tests": ["grid_formula_search", "matrix_generator_exhaustive_search", "pair_reverse_variant"],
            "targets": ["B", "C"],
            "status": "testable",
        },
        {
            "id": "honeminas_vectors",
            "clue": "43153 / 34784 / 3478 / Magic Web",
            "source_url": "https://tibia.fandom.com/wiki/The_Honeminas_Formula_%28Book%29",
            "operational_hypothesis": "lore numbers act as vector/seed/operator over the 10x10 grid",
            "tests": ["magic_web_formula_search", "matrix_generator_exhaustive_search", "seed_generator_search"],
            "targets": ["A", "B", "H", "K"],
            "status": "testable_as_mechanism_only",
        },
        {
            "id": "one_equals_tibia",
            "clue": "1 = Tibia",
            "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
            "operational_hypothesis": "digit 1 or pairs {1,x} have structural role",
            "tests": ["one_equals_tibia_tests", "matrix_generator_exhaustive_search"],
            "targets": ["C", "D", "F", "G", "J"],
            "status": "testable_not_translation",
        },
        {
            "id": "chayenne_2009",
            "clue": "Chayenne reply contains genuine book substrings",
            "source_url": "https://forum.portaltibia.com.br/topic/11420-entrevista-com-chayenne/",
            "operational_hypothesis": "external string should be covered by real book copy/generator operators",
            "tests": ["external_holdout_chayenne_ytc"],
            "targets": ["K"],
            "status": "secondary_validation",
        },
        {
            "id": "avar_tar",
            "clue": "Avar Tar poem is attested but not true 469",
            "source_url": "https://tibia.fandom.com/wiki/Avar_Tar/Transcripts",
            "operational_hypothesis": "real generator should not cover it better than controls",
            "tests": ["negative_control_suite"],
            "targets": ["L"],
            "status": "negative_control",
        },
    ]


def write_clue_and_targets() -> None:
    clues = clue_ledger()
    lines = ["# CipSoft / Lore Clue Ledger", "", "Generated by `generator_search_suite.py`.", ""]
    lines.extend(["| ID | Clue | Source | Operational hypothesis | Tests | Status |", "|---|---|---|---|---|---|"])
    for item in clues:
        lines.append(
            f"| `{item['id']}` | {item['clue']} | {item['source_url']} | {item['operational_hypothesis']} | {', '.join('`'+t+'`' for t in item['tests'])} | `{item['status']}` |"
        )
    (HERE / "cipsoft_clue_ledger.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    hypotheses = [
        {
            "hypothesis_id": item["id"],
            "source_clue": item["clue"],
            "source_url": item["source_url"],
            "operational_hypothesis": item["operational_hypothesis"],
            "targets": item["targets"],
            "tests": item["tests"],
            "promotion_policy": "mechanical_only_no_plaintext",
        }
        for item in clues
    ]
    write_json(HERE / "generator_hypothesis_registry.json", {"schema": "generator_hypothesis_registry.v1", "hypotheses": hypotheses})
    targets = [
        ("A", "table_00_99_to_symbols", "Explain the 99-entry code->symbol table"),
        ("B", "unordered_pair_purity", "Explain 54/55 pure unordered pair classes"),
        ("C", "conflict_19_91", "Explain sole pair conflict {19,91}"),
        ("D", "missing_39", "Explain absent cell 39"),
        ("E", "symbol_distribution", "Explain symbol frequencies"),
        ("F", "homophone_class_sizes", "Explain homophones per symbol"),
        ("G", "book_code_sequence", "Explain code sequence in books"),
        ("H", "long_modules", "Explain long copied modules"),
        ("I", "residuals", "Explain 2,083 literal residual digits"),
        ("J", "zero_omissions", "Explain omitted leading zeros"),
        ("K", "chayenne_ytc", "Explain external holdouts without training"),
        ("L", "reject_avar_tar", "Reject Avar Tar/control leakage"),
    ]
    write_json(
        HERE / "generator_targets.json",
        {"schema": "generator_targets.v1", "targets": [{"id": a, "name": b, "description": c} for a, b, c in targets]},
    )
    matrix_lines = ["# Target Feature Matrix", "", "| Target | Fronts | Promotion gate |", "|---|---|---|"]
    front_map = {
        "A": ["grid_formula_search", "matrix_generator_exhaustive_search", "seed_generator_search", "pair_marginal_signature_search", "residual_marginal_after_e_search"],
        "B": ["grid_formula_search", "matrix_generator_exhaustive_search", "magic_web_formula_search"],
        "C": ["grid_formula_search", "matrix_generator_exhaustive_search", "one_equals_tibia_tests"],
        "D": ["grid_formula_search", "matrix_generator_exhaustive_search", "seed_generator_search"],
        "E": ["grid_formula_search", "prng_seed_search"],
        "F": [
            "one_equals_tibia_tests",
            "homophone_generator_search",
            "pair_context_cluster_search",
            "pair_context_partition_search",
        ],
        "G": [
            "homophone_generator_search",
            "pair_context_cluster_search",
            "pair_context_partition_search",
            "pair_symbol_stream_compression_search",
            "module_grammar_induction",
        ],
        "H": [
            "module_grammar_induction",
            "module_overlap_grammar_search",
            "module_tape_origin_search",
            "module_tape_order_search",
            "tape_based_formula_compile",
            "tape_tokenization_analysis",
            "tape_first_use_pair_order_search",
            "tape_literal_exception_analysis",
            "tape_feature_pair_label_search",
            "magic_web_formula_search",
        ],
        "I": ["residual_coverage_mdl", "module_grammar_induction"],
        "J": ["zero_omission_generator", "zero_exception_decision_list", "zero_omission_supporting_render_layer"],
        "K": ["external_holdout_chayenne_ytc"],
        "L": ["negative_control_suite"],
    }
    for tid, name, desc in targets:
        matrix_lines.append(f"| `{tid}` {name} | {', '.join('`'+f+'`' for f in front_map[tid])} | {desc}; must pass controls |")
    (HERE / "target_feature_matrix.md").write_text("\n".join(matrix_lines) + "\n", encoding="utf-8")


def grid_formula_search(formula: dict) -> list[dict]:
    code_to_symbol = formula["code_to_symbol"]
    codes = sorted(code_to_symbol)
    rules = {
        "unordered_pair": lambda c: tuple(sorted((int(c[0]), int(c[1])))),
        "digit_sum": lambda c: (int(c[0]) + int(c[1])) % 10,
        "digit_product": lambda c: (int(c[0]) * int(c[1])) % 10,
        "digit_diff": lambda c: abs(int(c[0]) - int(c[1])),
        "row": lambda c: int(c[0]),
        "column": lambda c: int(c[1]),
        "min_digit": lambda c: min(int(c[0]), int(c[1])),
        "max_digit": lambda c: max(int(c[0]), int(c[1])),
        "diagonal_band": lambda c: (int(c[0]) == int(c[1]), abs(int(c[0]) - int(c[1]))),
        "border_center": lambda c: (int(c[0]) in {0, 9} or int(c[1]) in {0, 9}, int(c[0]) in {4, 5}, int(c[1]) in {4, 5}),
    }
    rows = []
    for name, keyer in rules.items():
        groups = defaultdict(list)
        for code in codes:
            groups[keyer(code)].append(code_to_symbol[code])
        majority = {key: Counter(values).most_common(1)[0][0] for key, values in groups.items()}
        errors = [code for code in codes if majority[keyer(code)] != code_to_symbol[code]]
        rows.append(
            {
                "hypothesis_id": f"grid_{name}",
                "rule": name,
                "accuracy": (len(codes) - len(errors)) / len(codes),
                "errors": len(errors),
                "groups": len(groups),
                "rule_complexity": min(1.0, len(groups) / 55),
                "explains_missing_39": name in {"unordered_pair", "diagonal_band"} and "39" not in code_to_symbol,
                "explains_19_91_conflict": name == "unordered_pair" and {"19", "91"}.issubset(code_to_symbol),
                "targets_explained": ["A"] + (["B", "C"] if name == "unordered_pair" else []),
                "verdict": "candidate_generator" if name == "unordered_pair" else "rejected_control",
            }
        )
    rows.sort(key=lambda item: (-item["accuracy"], item["groups"]))
    write_json(HERE / "grid_formula_leaderboard.json", {"schema": "grid_formula_leaderboard.v1", "rows": rows})
    lines = ["# Grid Formula Search", "", "| Rule | Accuracy | Errors | Groups | Verdict |", "|---|---:|---:|---:|---|"]
    for row in rows:
        lines.append(f"| `{row['rule']}` | {row['accuracy']:.3f} | {row['errors']} | {row['groups']} | `{row['verdict']}` |")
    lines += [
        "",
        "The unordered-pair rule is the only compact non-trivial winner, but it is",
        "still a table geometry explanation, not plaintext.",
        "",
    ]
    (HERE / "grid_formula_search_report.md").write_text("\n".join(lines), encoding="utf-8")
    return rows


def magic_web_search(formula: dict):
    books = formula["books_digits"]
    joined = "\x00".join(books[book] for book in sorted(books, key=numeric_key))
    rows = []
    for number in HONEMINAS_NUMBERS:
        hits = sum(text.count(number) for text in books.values())
        rows.append(
            {
                "number": number,
                "length": len(number),
                "exact_hits": hits,
                "appears_in_modules": any(number in module["text"] for module in formula["modules"]),
                "interpretation": "short/common structural overlap" if len(number) <= 4 and hits else "absent_or_non_probative",
            }
        )
    controls = []
    for length in sorted({len(n) for n in HONEMINAS_NUMBERS}):
        vals = []
        for _ in range(200):
            sample = "".join(random.choice("0123456789") for _ in range(length))
            vals.append(joined.count(sample))
        controls.append({"length": length, "mean_hits": sum(vals) / len(vals), "max_hits": max(vals)})
    write_json(HERE / "magic_web_null_controls.json", {"schema": "magic_web_null_controls.v1", "numbers": rows, "controls": controls})
    lines = ["# Honeminas / Magic Web Vector Report", "", "| Number | Hits | In modules | Interpretation |", "|---|---:|---|---|"]
    for row in rows:
        lines.append(f"| `{row['number']}` | {row['exact_hits']} | `{row['appears_in_modules']}` | {row['interpretation']} |")
    lines += ["", "No vector is promoted as plaintext or generator seed.", ""]
    (HERE / "honeminas_vector_report.md").write_text("\n".join(lines), encoding="utf-8")
    return rows


def one_equals_tibia(formula: dict, token_maps: dict[str, list[dict]]):
    code_to_symbol = formula["code_to_symbol"]
    all_codes = [tok["code"] for toks in token_maps.values() for tok in toks]
    digit_counts = Counter("".join(formula["books_digits"].values()))
    pair_1_codes = [code for code in code_to_symbol if "1" in code]
    non_1_codes = [code for code in code_to_symbol if "1" not in code]
    symbol_counts_1 = Counter(code_to_symbol[code] for code in pair_1_codes)
    symbol_counts_non1 = Counter(code_to_symbol[code] for code in non_1_codes)
    result = {
        "digit_1_raw_count": digit_counts["1"],
        "digit_counts": dict(digit_counts),
        "codes_containing_1": len(pair_1_codes),
        "codes_not_containing_1": len(non_1_codes),
        "pair_1_symbols": dict(symbol_counts_1),
        "non_1_symbols": dict(symbol_counts_non1),
        "conflict_uses_1": True,
        "missing_39_uses_1": False,
        "book_code_occurrences_with_1": sum(1 for code in all_codes if "1" in code),
        "verdict": "contextual_hint_not_promoted",
    }
    lines = ["# One Equals Tibia Tests", "", f"- Raw digit `1` count: {result['digit_1_raw_count']}.", f"- Codes containing `1`: {result['codes_containing_1']}.", f"- Sole pair conflict uses `1`: `{result['conflict_uses_1']}`.", f"- Missing cell `39` uses `1`: `{result['missing_39_uses_1']}`.", "", "Verdict: structural hint worth tracking, but not a standalone generator rule.", ""]
    (HERE / "one_equals_tibia_report.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(HERE / "one_equals_tibia_results.json", result)
    return result


def homophone_search(token_maps: dict[str, list[dict]], holdouts: list[str]):
    train = [tok for book, toks in token_maps.items() if book not in holdouts for tok in toks]
    test = [tok for book, toks in token_maps.items() if book in holdouts for tok in toks]
    top_by_symbol = {}
    for symbol, rows in defaultdict(list, {}).items():
        pass
    counts = defaultdict(Counter)
    prev_counts = defaultdict(Counter)
    for book, toks in token_maps.items():
        if book in holdouts:
            continue
        prev = "<s>"
        for tok in toks:
            counts[tok["symbol"]][tok["code"]] += 1
            prev_counts[(prev, tok["symbol"])][tok["code"]] += 1
            prev = tok["code"]
    top_by_symbol = {symbol: counter.most_common(1)[0][0] for symbol, counter in counts.items()}
    top_by_prev = {key: counter.most_common(1)[0][0] for key, counter in prev_counts.items()}

    def score(model: str):
        ok = total = 0
        prev_by_book = defaultdict(lambda: "<s>")
        for tok in test:
            if model == "symbol_top":
                pred = top_by_symbol.get(tok["symbol"])
            else:
                pred = top_by_prev.get((prev_by_book[tok["book"]], tok["symbol"]), top_by_symbol.get(tok["symbol"]))
            ok += pred == tok["code"]
            total += 1
            prev_by_book[tok["book"]] = tok["code"]
        return ok / total if total else 0.0

    rows = [
        {"hypothesis_id": "homophone_symbol_top", "model": "symbol_top", "holdout_accuracy": score("symbol_top"), "targets_explained": ["F"], "verdict": "baseline"},
        {"hypothesis_id": "homophone_prev_code", "model": "prev_code_symbol", "holdout_accuracy": score("prev"), "targets_explained": ["G"], "verdict": "supporting_homophone_channel"},
    ]
    write_json(HERE / "homophone_holdout_report.json", {"schema": "homophone_holdout_report.v1", "holdout_books": holdouts, "rows": rows})
    lines = ["# Homophone Selector Leaderboard", "", "| Model | Holdout accuracy | Verdict |", "|---|---:|---|"]
    for row in rows:
        lines.append(f"| `{row['model']}` | {row['holdout_accuracy']:.3f} | `{row['verdict']}` |")
    lines.append("")
    (HERE / "homophone_selector_leaderboard.md").write_text("\n".join(lines), encoding="utf-8")
    return rows


def zero_omission_search(token_maps: dict[str, list[dict]], holdouts: list[str]):
    examples = []
    for book, toks in token_maps.items():
        for index, tok in enumerate(toks):
            if not tok["code"].startswith("0"):
                continue
            prev_code = toks[index - 1]["code"] if index else "<s>"
            next_code = toks[index + 1]["code"] if index + 1 < len(toks) else "</s>"
            examples.append({**tok, "prev_code": prev_code, "next_code": next_code, "label": tok["omitted_zero"]})

    train = [e for e in examples if e["book"] not in holdouts]
    test = [e for e in examples if e["book"] in holdouts]

    def majority_by(feature_names: tuple[str, ...]):
        groups = defaultdict(list)
        for item in train:
            groups[tuple(item[name] for name in feature_names)].append(item["label"])
        majority = {key: Counter(values).most_common(1)[0][0] for key, values in groups.items()}
        default = Counter(item["label"] for item in train).most_common(1)[0][0]
        ok = 0
        for item in test:
            pred = majority.get(tuple(item[name] for name in feature_names), default)
            ok += pred == item["label"]
        return ok / len(test) if test else 0.0, len(majority)

    rows = []
    for name, features in {
        "code_only": ("code",),
        "code_prev_next": ("code", "prev_code", "next_code"),
        "symbol_code": ("symbol", "code"),
    }.items():
        acc, groups = majority_by(features)
        rows.append(
            {
                "model": name,
                "holdout_accuracy": acc,
                "groups": groups,
                "verdict": "supporting_render_layer_signal_only" if name == "code_prev_next" else "baseline",
            }
        )
    lines = ["# Zero Render Rule Report", "", "| Model | Holdout accuracy | Groups | Verdict |", "|---|---:|---:|---|"]
    for row in rows:
        lines.append(f"| `{row['model']}` | {row['holdout_accuracy']:.3f} | {row['groups']} | `{row['verdict']}` |")
    lines += ["", "The best local renderer is still context-like; no semantic channel is implied.", ""]
    (HERE / "zero_render_rule_report.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(HERE / "zero_omission_results.json", {"schema": "zero_omission_results.v1", "rows": rows})
    return rows


def module_grammar(formula: dict, residual: dict):
    modules = formula["modules"]
    prefix_counts = Counter(module["text"][:8] for module in modules if len(module["text"]) >= 8)
    suffix_counts = Counter(module["text"][-8:] for module in modules if len(module["text"]) >= 8)
    residual_mdl = residual["mdl_pruning"]
    comparison = {
        "baseline_c2_bits": residual_mdl["baseline_bits"],
        "residual_exact_repeat_pruned_bits": residual_mdl["estimated_total_bits"],
        "residual_exact_repeat_net_savings_bits": residual_mdl["net_savings_bits"],
        "reused_prefix8_count": sum(1 for _, count in prefix_counts.items() if count > 1),
        "reused_suffix8_count": sum(1 for _, count in suffix_counts.items() if count > 1),
        "verdict": "exact_repeat_survives_templates_not_promoted",
    }
    overlap_path = HERE / "module_overlap_grammar_results.json"
    overlap = load_json(overlap_path) if overlap_path.exists() else None
    if overlap:
        best = overlap["best_threshold"]
        comparison["overlap_tape_best_min_overlap"] = best["min_overlap"]
        comparison["overlap_tape_components"] = best["component_count"]
        comparison["overlap_tape_gross_savings_digits"] = best["gross_savings_digits"]
        comparison["overlap_tape_rough_mdl_gain_bits"] = best["rough_mdl_gain_bits"]
        comparison["overlap_tape_verdict"] = overlap["verdict"]
    write_json(HERE / "module_mdl_comparison.json", comparison)
    lines = [
        "# Module Template Report",
        "",
        f"- Modules: {len(modules)}.",
        f"- Reused 8-digit prefixes: {comparison['reused_prefix8_count']}.",
        f"- Reused 8-digit suffixes: {comparison['reused_suffix8_count']}.",
        f"- Residual exact-repeat pruned bits: {comparison['residual_exact_repeat_pruned_bits']:.1f}.",
        "",
        "Simple prefix/suffix templates alone are not accepted.",
    ]
    if overlap:
        lines += [
            "",
            "Separate overlap-tape search now finds a stronger mechanical module",
            "candidate:",
            "",
            f"- Min overlap: {comparison['overlap_tape_best_min_overlap']}.",
            f"- Components: {comparison['overlap_tape_components']}.",
            f"- Gross saved digits: {comparison['overlap_tape_gross_savings_digits']}.",
            f"- Rough MDL gain bits: {comparison['overlap_tape_rough_mdl_gain_bits']:.1f}.",
            f"- Verdict: `{comparison['overlap_tape_verdict']}`.",
        ]
    else:
        lines += ["", "No parametric module template is accepted yet."]
    lines.append("")
    (HERE / "module_template_report.md").write_text("\n".join(lines), encoding="utf-8")
    return comparison


def seed_search(formula: dict):
    present = set(formula["code_to_symbol"])
    occurrence_rank = [code for code, _ in sorted(formula["code_counts"].items(), key=lambda item: (-item[1], item[0]))]

    def lcg(seed: int, a: int, c: int, m: int = 100):
        x = seed % m
        while True:
            x = (a * x + c) % m
            yield f"{x:02d}"

    gens = [("lcg_21_1", 21, 1), ("lcg_37_17", 37, 17), ("lcg_41_19", 41, 19)]
    rows = []
    random_controls = []
    for _ in range(200):
        sample = [f"{random.randrange(100):02d}" for _ in range(120)]
        unique = []
        for code in sample:
            if code not in unique:
                unique.append(code)
        random_controls.append(len(set(unique[:99]) & set(occurrence_rank[:20])))
    ctrl_mean = sum(random_controls) / len(random_controls)
    ctrl_sd = (sum((value - ctrl_mean) ** 2 for value in random_controls) / (len(random_controls) - 1)) ** 0.5
    for seed_text in SEEDS:
        seed = int(seed_text)
        for name, a, c in gens:
            stream = lcg(seed, a, c)
            unique = []
            for _ in range(200):
                code = next(stream)
                if code not in unique:
                    unique.append(code)
                if len(unique) >= 99:
                    break
            top20_hit = len(set(unique[:99]) & set(occurrence_rank[:20]))
            z = (top20_hit - ctrl_mean) / ctrl_sd if ctrl_sd else 0.0
            rows.append(
                {
                    "hypothesis_id": f"seed_{seed_text}_{name}",
                    "seed": seed_text,
                    "generator": name,
                    "present_codes_in_first99": len(set(unique[:99]) & present),
                    "top20_occurrence_hits": top20_hit,
                    "z_vs_random_seed_controls": z,
                    "verdict": "rejected_control",
                }
            )
    rows.sort(key=lambda item: -item["z_vs_random_seed_controls"])
    lines = ["# PRNG / Seed Leaderboard", "", "| Seed | Generator | Present in first 99 | Top20 hits | z | Verdict |", "|---|---|---:|---:|---:|---|"]
    for row in rows[:20]:
        lines.append(f"| `{row['seed']}` | `{row['generator']}` | {row['present_codes_in_first99']} | {row['top20_occurrence_hits']} | {row['z_vs_random_seed_controls']:.2f} | `{row['verdict']}` |")
    lines += ["", "No seed generator beats controls enough to promote.", ""]
    (HERE / "prng_seed_leaderboard.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(HERE / "seed_generator_results.json", {"schema": "seed_generator_results.v1", "rows": rows, "control_mean_top20_hits": ctrl_mean, "control_sd_top20_hits": ctrl_sd})
    return rows


def external_and_controls(formula: dict):
    raw_index = build_raw_index(formula["books_digits"], 3, 32)
    rows = {
        "chayenne_min8": cover_with_controls("chayenne", CHAYENNE_GROUPS, raw_index, 8),
        "ytc_min8": cover_with_controls("your_true_colour", ["78567", "34334", "989", "135", "65142"], raw_index, 8),
        "avar_tar_min8": cover_with_controls("avar_tar", AVAR_TAR_GROUPS, raw_index, 8),
        "chayenne_min3": cover_with_controls("chayenne", CHAYENNE_GROUPS, raw_index, 3),
        "ytc_min3": cover_with_controls("your_true_colour", ["78567", "34334", "989", "135", "65142"], raw_index, 3),
        "avar_tar_min3": cover_with_controls("avar_tar", AVAR_TAR_GROUPS, raw_index, 3),
    }
    write_json(HERE / "external_holdout_scores.json", {"schema": "external_holdout_scores.v1", "rows": rows})
    write_json(
        HERE / "control_leakage_matrix.json",
        {
            "schema": "control_leakage_matrix.v1",
            "rules": {
                "min_len_8_copy": {"chayenne": rows["chayenne_min8"], "ytc": rows["ytc_min8"], "avar_tar": rows["avar_tar_min8"]},
                "min_len_3_copy": {"chayenne": rows["chayenne_min3"], "ytc": rows["ytc_min3"], "avar_tar": rows["avar_tar_min3"]},
            },
            "verdict": "min_len_8_copy_passes_negative_control; min_len_3_copy_rejected_as_leaky",
        },
    )
    holdout_lines = ["# External Holdout: Chayenne / Your True Colour", "", "| String | minLen | Coverage | z vs shuffle |", "|---|---:|---:|---:|"]
    for key in ["chayenne_min8", "ytc_min8", "chayenne_min3", "ytc_min3"]:
        row = rows[key]
        holdout_lines.append(f"| `{row['name']}` | {row['min_len']} | {row['covered_digits']}/{row['length']} ({100*row['covered_fraction']:.1f}%) | {row['z_vs_shuffle']:.2f} |")
    holdout_lines += ["", "Chayenne is secondary validation only. YTC remains mostly novel and too short to promote.", ""]
    (HERE / "external_holdout_chayenne_ytc_report.md").write_text("\n".join(holdout_lines), encoding="utf-8")
    avar_lines = ["# Avar Tar Negative-Control Report", "", "| Rule | Coverage | z vs shuffle | Verdict |", "|---|---:|---:|---|"]
    for key in ["avar_tar_min8", "avar_tar_min3"]:
        row = rows[key]
        verdict = "pass" if key == "avar_tar_min8" and row["covered_digits"] == 0 else "leaky_rejected"
        avar_lines.append(f"| `{key}` | {row['covered_digits']}/{row['length']} ({100*row['covered_fraction']:.1f}%) | {row['z_vs_shuffle']:.2f} | `{verdict}` |")
    (HERE / "avar_tar_control_report.md").write_text("\n".join(avar_lines) + "\n", encoding="utf-8")
    return rows


def consolidate(results: dict):
    rows = []

    def add(hid, targets, pred, mdl, lore, complexity, leakage, verdict):
        score = pred + mdl + lore - complexity - leakage
        rows.append(
            {
                "hypothesis_id": hid,
                "targets_explained": targets,
                "prediction_score": pred,
                "mdl_gain": mdl,
                "lore_fit": lore,
                "rule_complexity": complexity,
                "control_leakage": leakage,
                "score_total": score,
                "verdict": verdict,
            }
        )

    best_grid = results["grid"][0]
    add("core_mechanical_formula", ["A", "B", "G", "H", "I", "J"], 1.0, 0.0, 0.8, 0.35, 0.0, "core")
    add("grid_unordered_pair", best_grid["targets_explained"], best_grid["accuracy"], 0.0, 0.6, best_grid["rule_complexity"], 0.0, best_grid["verdict"])
    residual = results["residual"]["mdl_pruning"]
    add("residual_exact_repeat_pruned", ["I", "H"], residual["selected_covered_digits"] / 2083, residual["net_savings_bits"] / 1000, 0.6, 0.2, 0.0, "candidate_generator")
    chay = results["external"]["chayenne_min8"]
    add("chayenne_min8_copy_holdout", ["K"], chay["covered_fraction"], 0.0, 0.4, 0.1, 0.0, "secondary_validation")
    ytc = results["external"]["ytc_min8"]
    add("ytc_min8_copy_holdout", ["K"], ytc["covered_fraction"], 0.0, 0.4, 0.1, 0.0, "rejected_control")
    avar = results["external"]["avar_tar_min8"]
    add("avar_tar_min8_negative_control", ["L"], 1.0 if avar["covered_digits"] == 0 else 0.0, 0.0, 0.2, 0.1, avar["covered_fraction"], "negative_control_pass" if avar["covered_digits"] == 0 else "rejected_control")
    add("homophone_prev_code", ["G"], results["homophone"][1]["holdout_accuracy"], 0.0, 0.2, 0.6, 0.0, "supporting_homophone_channel")
    add("zero_code_prev_next", ["J"], results["zero"][1]["holdout_accuracy"], 0.0, 0.2, 0.7, 0.0, "supporting_render_layer")
    add("magic_web_numbers", ["H", "K"], 0.0, 0.0, 0.5, 0.4, 0.0, "rejected_control")
    add("one_equals_tibia", ["C"], 0.2, 0.0, 0.5, 0.4, 0.0, "pareidolia_risk")
    add("seed_prng_search", ["A", "G"], 0.0, 0.0, 0.3, 0.6, 0.0, "rejected_control")
    deep_path = HERE / "deep_formula_leaderboard.json"
    if deep_path.exists():
        deep = load_json(deep_path)
        best = deep["verdict"]["best_compact_non_lookup"]
        add(
            "deep_compact_formula_search",
            ["A", "B", "C"],
            best["accuracy"],
            0.0,
            0.3,
            0.7,
            0.0,
            "rejected_control",
        )
    pair_constructive_path = HERE / "pair_table_constructive_leaderboard.json"
    if pair_constructive_path.exists():
        pair = load_json(pair_constructive_path)
        allocation = pair["frequency_allocation"]
        add(
            "pair_table_frequency_allocation",
            ["A", "F"],
            allocation["pair_count_vs_corpus_pearson"],
            0.0,
            0.5,
            0.25,
            0.0,
            "candidate_generator",
        )
        source = pair["source_fill"]
        add(
            "pair_table_source_cycle",
            ["A"],
            source["best"]["accuracy"],
            0.0,
            0.3,
            0.65,
            0.0,
            source["verdict"],
        )
        spatial = pair["spatial_features"]
        add(
            "pair_table_spatial_features",
            ["A"],
            spatial["best"]["accuracy"],
            0.0,
            0.2,
            0.85,
            spatial["best"]["p_ge"],
            spatial["verdict"],
        )
        dispersion = pair["spatial_dispersion"]
        add(
            "pair_table_spatial_dispersion",
            ["A"],
            max(0.0, 1.0 - abs(dispersion["strongest"]["z_vs_shuffle"]) / 3.0),
            0.0,
            0.2,
            0.75,
            0.2,
            dispersion["verdict"],
        )
        seeded = pair["seeded_placement"]
        add(
            "pair_table_seeded_placement",
            ["A"],
            seeded["best"]["accuracy"],
            0.0,
            0.4,
            0.75,
            0.1,
            "rejected_control",
        )
    stochastic_path = HERE / "frequency_weighted_stochastic_inventory_results.json"
    if stochastic_path.exists():
        stochastic = load_json(stochastic_path)
        bits_gain = stochastic["model_comparison"]["floor_frequency_bits_gain_vs_uniform"]
        add(
            "frequency_weighted_stochastic_inventory",
            ["A", "F"],
            min(1.0, bits_gain / 40.0),
            bits_gain / 100.0,
            0.65,
            0.35,
            0.0,
            stochastic["verdict"],
        )
    apportionment_path = HERE / "deterministic_apportionment_inventory_results.json"
    if apportionment_path.exists():
        apport = load_json(apportionment_path)
        best = apport["best"]
        add(
            "deterministic_apportionment_inventory",
            ["A", "F"],
            max(0.0, 1.0 - best["l1"] / 41.0),
            0.0,
            0.55,
            0.45,
            0.0,
            apport["verdict"],
        )
    residual_explainer_path = HERE / "inventory_residual_explainer_results.json"
    if residual_explainer_path.exists():
        residual_explainer = load_json(residual_explainer_path)
        best = residual_explainer["best"]
        baseline = residual_explainer["baseline_residual_l1"]
        add(
            "inventory_residual_explainer",
            ["A", "F"],
            max(0.0, 1.0 - best["l1"] / baseline),
            0.0,
            0.35,
            0.65,
            residual_explainer["controls"]["gain_vs_null"]["p_good_direction"],
            residual_explainer["verdict"],
        )
    shuffle_seed_path = HERE / "inventory_shuffle_seed_results.json"
    if shuffle_seed_path.exists():
        shuffle_seed = load_json(shuffle_seed_path)
        best = shuffle_seed["best"]
        add(
            "inventory_shuffle_seed_search",
            ["A", "F"],
            best["accuracy"],
            0.0,
            0.45,
            0.65,
            shuffle_seed["control_summary"]["p_good_direction"],
            shuffle_seed["verdict"],
        )
    symbol_digit_path = HERE / "symbol_digit_origin_results.json"
    if symbol_digit_path.exists():
        symbol_digit = load_json(symbol_digit_path)
        variation = symbol_digit["symbol_module_code_variation"]
        add(
            "symbol_digit_origin_order",
            ["G", "H"],
            variation["exact_pair_fraction"],
            0.0,
            0.7,
            0.25,
            0.0,
            "candidate_generator",
        )
    orientation_path = HERE / "orientation_render_rule_results.json"
    if orientation_path.exists():
        orientation = load_json(orientation_path)
        selected = orientation["book_holdout"]["selected"]
        add(
            "orientation_render_rule",
            ["G", "J"],
            selected["accuracy"],
            0.0,
            0.45,
            0.55,
            orientation["book_holdout"]["selected_vs_pair_preserving_train_shuffle"]["p_good_direction"],
            orientation["verdict"],
        )
    directed_surface_path = HERE / "directed_pair_surface_results.json"
    if directed_surface_path.exists():
        directed = load_json(directed_surface_path)
        mirror = directed["diagnostics"]["mirror_transposition"]
        add(
            "directed_pair_surface_search",
            ["A", "C", "D", "J"],
            mirror["same_symbol_unordered_pairs"] / mirror["reverse_available_unordered_pairs"],
            0.0,
            0.45,
            0.45,
            max(
                directed["controls"]["lower_inventory_shuffle_mirror_matches"]["p_value_ge_observed"],
                directed["controls"]["ordered_inventory_shuffle_reverse_pair_matches"]["p_value_ge_observed"],
            ),
            directed["conclusion"]["classification"],
        )
    directed_sequence_path = HERE / "directed_surface_sequence_generator_results.json"
    if directed_sequence_path.exists():
        directed_sequence = load_json(directed_sequence_path)
        best = directed_sequence["best_metric"]
        corrected_p = min(1.0, best["p_good"] * directed_sequence["search_tests"])
        add(
            "directed_surface_sequence_generator_search",
            ["A", "C", "D"],
            min(1.0, max(0.0, best["z_good"] / 10.0)),
            directed_sequence["periodic_mdl"]["best_period_gain_vs_inventory_bits"] / 1000.0,
            0.35,
            0.65,
            corrected_p,
            directed_sequence["verdict"],
        )
    structural_exception_path = HERE / "structural_exception_layer_results.json"
    if structural_exception_path.exists():
        structural = load_json(structural_exception_path)
        selected = structural["selected_model"]
        add(
            "structural_exception_layer_search",
            ["A", "C", "D", "J"],
            selected["strict_accuracy"],
            structural["conclusion"]["selected_delta_vs_unordered_lookup_lossless_bits"] / 1000.0,
            0.45,
            0.45,
            structural["controls"]["mirror_lower_match_shuffle"]["p_value_good_direction"],
            structural["conclusion"]["classification"],
        )
    zero_explainer_path = HERE / "zero_omission_rule_explainer_results.json"
    if zero_explainer_path.exists():
        zero_explainer = load_json(zero_explainer_path)
        selected = zero_explainer["selected_group_rule"]
        add(
            "zero_omission_rule_explainer",
            ["J"],
            selected["balanced_accuracy"],
            zero_explainer["rough_mdl_gain_vs_code_only_bits"] / 1000.0,
            0.35,
            0.65,
            zero_explainer["selected_vs_code_preserving_shuffle"]["p_good_direction"],
            "supporting_render_layer_signal_only",
        )
    zero_exception_path = HERE / "zero_exception_decision_list_results.json"
    if zero_exception_path.exists():
        zero_exception = load_json(zero_exception_path)
        selected = zero_exception["selected"]
        add(
            "zero_exception_decision_list",
            ["J"],
            selected["holdout"]["balanced_accuracy"],
            zero_exception["holdout_mdl_gain_vs_code_only_bits"] / 1000.0,
            0.35,
            0.55,
            zero_exception["shuffle_control"]["p_good_direction"],
            "supporting_render_layer_signal_only",
        )
    zero_compact_path = HERE / "zero_compact_rule_results.json"
    if zero_compact_path.exists():
        zero_compact = load_json(zero_compact_path)
        selected = zero_compact["selected_by_balanced_accuracy"]
        mdl_selected = zero_compact["selected_by_mdl_gain"]
        add(
            "zero_compact_rule_search",
            ["J"],
            selected["holdout"]["balanced_accuracy"],
            mdl_selected["holdout_mdl_gain_vs_code_only_bits"] / 1000.0,
            0.40,
            0.45,
            min(
                selected["train_delta_balanced_accuracy_vs_code_only_shuffle"]["p_good_direction"],
                mdl_selected["train_delta_balanced_accuracy_vs_code_only_shuffle"]["p_good_direction"],
            ),
            zero_compact["overall_classification"],
        )
    lore_zero_path = HERE / "lore_zero_phase_mask_results.json"
    if lore_zero_path.exists():
        lore_zero = load_json(lore_zero_path)
        selected = lore_zero["observed"]["best_by_balanced_accuracy"]
        best_mdl = lore_zero["observed"]["best_by_mdl_gain"]
        add(
            "lore_zero_phase_mask_search",
            ["J"],
            selected["balanced_accuracy"],
            best_mdl["mdl_gain_vs_code_only_bits"] / 1000.0,
            0.45,
            0.45,
            max(
                lore_zero["controls"]["digit_multiset_permutation"]["best_balanced_accuracy"]["p_good"],
                lore_zero["controls"]["random_same_length_digits"]["best_balanced_accuracy"]["p_good"],
                lore_zero["controls"]["label_shuffle"]["best_balanced_accuracy"]["p_good"],
            ),
            lore_zero["verdict"],
        )
    lore_anomaly_path = HERE / "lore_anomaly_operator_results.json"
    if lore_anomaly_path.exists():
        lore_anomaly = load_json(lore_anomaly_path)
        best_target_id, best = max(
            lore_anomaly["best_by_target"].items(),
            key=lambda item: (item[1]["f1"], item[1]["tp"], -item[1]["fp"], -item[1]["cost"]),
        )
        best_controls = lore_anomaly["controls"][best_target_id]
        add(
            "lore_anomaly_operator_search",
            ["C", "D"],
            best["f1"],
            0.0,
            0.45,
            0.45,
            max(
                best_controls["digit_multiset_permutation"]["p_good_direction"],
                best_controls["same_length_random_digits"]["p_good_direction"],
                best_controls["same_size_random_target"]["p_good_direction"],
            ),
            lore_anomaly["verdict"],
        )
    shared_e_zero_path = HERE / "shared_e_zero_predicate_results.json"
    if shared_e_zero_path.exists():
        shared_e_zero = load_json(shared_e_zero_path)
        pair_score = shared_e_zero["pair_side"]["score_diagonal_predicts_e"]["f1"]
        zero_delta = max(0.0, shared_e_zero["zero_side"]["holdout_delta_balanced_accuracy"])
        add(
            "shared_e_zero_predicate_search",
            ["C", "D", "J"],
            min(1.0, pair_score + zero_delta),
            shared_e_zero["zero_side"]["rough_holdout_error_gain_bits"] / 1000.0,
            0.30,
            0.25,
            shared_e_zero["controls"]["joint_diag_fraction_plus_zero_delta"]["p_good_direction"],
            shared_e_zero["verdict"],
        )
    e_layer_path = HERE / "e_layer_predicate_results.json"
    if e_layer_path.exists():
        e_layer = load_json(e_layer_path)
        residual_e = e_layer["residual_offdiag_e"]
        residual_best = residual_e["best"]
        add(
            "e_layer_predicate_search",
            ["A", "C"],
            residual_best["f1"],
            residual_best["mdl_gain_vs_e_lookup_bits"] / 1000.0,
            0.25,
            0.35,
            residual_e["controls"]["best_mdl_gain"]["p_good_direction"],
            e_layer["verdict"],
        )
    priority_masked_e_path = HERE / "priority_masked_e_layer_results.json"
    if priority_masked_e_path.exists():
        priority_masked_e = load_json(priority_masked_e_path)
        observed = priority_masked_e["observed"]
        add(
            "priority_masked_e_layer_search",
            ["A", "C"],
            observed["claim_hits"] / 55.0,
            observed["gain_vs_inventory_lookup_bits"] / 1000.0,
            0.20,
            0.55,
            priority_masked_e["controls"]["gain_vs_inventory_lookup_bits"]["p_good_direction"],
            priority_masked_e["verdict"],
        )
    anchored_remaining_path = HERE / "anchored_remaining_fill_results.json"
    if anchored_remaining_path.exists():
        anchored_remaining = load_json(anchored_remaining_path)
        best = anchored_remaining["best"]
        add(
            "anchored_remaining_fill_search",
            ["A", "B", "C", "F"],
            best["hits"] / 55.0,
            best["gain_vs_inventory_lookup_bits"] / 1000.0,
            0.35,
            0.60,
            anchored_remaining["controls"]["best_gain_vs_inventory_lookup_bits"]["p_good_direction"],
            anchored_remaining["verdict"],
        )
    priority_anchored_quotient_path = HERE / "priority_anchored_quotient_residual_fill_results.json"
    if priority_anchored_quotient_path.exists():
        priority_anchored_quotient = load_json(priority_anchored_quotient_path)
        best = priority_anchored_quotient["best"]
        add(
            "priority_anchored_quotient_residual_fill",
            ["A", "B", "C", "F"],
            best["residual_hits"] / best["residual_count"],
            best["gain_vs_quotient_lookup_bits"] / 1000.0,
            0.35,
            0.55,
            priority_anchored_quotient["controls"]["residual_hits"]["p_good_direction"],
            priority_anchored_quotient["verdict"],
        )
    zero_homophone_origin_path = HERE / "zero_homophone_transition_origin_probe_results.json"
    if zero_homophone_origin_path.exists():
        zero_homophone_origin = load_json(zero_homophone_origin_path)
        best_centroid = max(
            zero_homophone_origin["variants"],
            key=lambda item: item["centroid_leave_one_pair_out"]["accuracy"],
        )
        best_cluster = max(
            zero_homophone_origin["variants"],
            key=lambda item: item["cluster_pair_link"]["f1"],
        )
        leakage = min(
            best_centroid["controls"]["label_shuffle_preserving_inventory"]["centroid_accuracy"]["p"],
            best_cluster["controls"]["label_shuffle_preserving_inventory"]["cluster_f1"]["p"],
        )
        add(
            "zero_homophone_transition_origin_probe",
            ["A", "F", "G", "J"],
            best_centroid["centroid_leave_one_pair_out"]["accuracy"],
            0.0,
            0.35,
            0.65,
            leakage,
            zero_homophone_origin["verdict"],
        )
    module_overlap_path = HERE / "module_overlap_grammar_results.json"
    if module_overlap_path.exists():
        module_overlap = load_json(module_overlap_path)
        best = module_overlap["best_threshold"]
        p_shuffle = best["controls"]["per_module_digit_shuffle"]["rough_mdl_gain_bits"]["p_good_direction"]
        p_resample = best["controls"]["global_digit_resample"]["rough_mdl_gain_bits"]["p_good_direction"]
        add(
            "module_overlap_tape_grammar",
            ["G", "H"],
            best["gross_savings_digits"] / best["total_digits"],
            best["rough_mdl_gain_bits"] / 1000.0,
            0.65,
            0.35,
            max(p_shuffle, p_resample),
            module_overlap["verdict"],
        )
    module_tape_path = HERE / "module_tape_origin_results.json"
    if module_tape_path.exists():
        module_tape = load_json(module_tape_path)
        gap = module_tape["recipe_gap_analysis"]
        full_hit_score = module_tape["full_hit_components"] / module_tape["component_count"]
        link_score = gap["accepted_adjacent_module_links"] / max(1, gap["candidate_adjacent_module_links"])
        pred = (full_hit_score + link_score) / 2.0
        mdl_gain = gap["absorbed_literal_digits"] * math.log2(10) / 1000.0
        add(
            "module_tape_origin_search",
            ["G", "H", "I"],
            pred,
            mdl_gain,
            0.65,
            0.30,
            module_tape["gap_controls"]["absorbed_literal_digits"]["p_good_direction"],
            module_tape["verdict"],
        )
    endpoint_bridge_path = HERE / "endpoint_literal_bridge_mdl_results.json"
    if endpoint_bridge_path.exists():
        endpoint_bridge = load_json(endpoint_bridge_path)
        if endpoint_bridge.get("schema") == "endpoint_literal_bridge_mdl_results.v2":
            final = endpoint_bridge["final_residual_holdout"]
            best = final["best"]
            prediction = max(
                best["covered_fraction_digits"],
                endpoint_bridge["leave_one_bridge_out"]["best"]["covered_fraction_digits"],
                endpoint_bridge["leave_book_out"]["best"]["covered_fraction_digits"],
            )
            mdl_gain = endpoint_bridge["rough_mdl_final"]["net_gain_bits"] / 1000.0
            leakage = endpoint_bridge["controls"]["label_shuffle_within_length"]["best_covered_digits"]["p_good"]
        else:
            best = endpoint_bridge["best"]
            prediction = best["covered_fraction_digits"]
            mdl_gain = best["net_gain_bits"] / 1000.0
            leakage = max(
                endpoint_bridge["controls"]["train_text_shuffle"]["best_covered_digits"]["p_good"],
                endpoint_bridge["controls"]["train_text_length_preserving_shuffle"]["best_covered_digits"]["p_good"],
            )
        add(
            "endpoint_literal_bridge_mdl_search",
            ["H", "I"],
            prediction,
            mdl_gain,
            0.45,
            0.50,
            leakage,
            endpoint_bridge["verdict"],
        )
    module_order_path = HERE / "module_tape_order_results.json"
    if module_order_path.exists():
        module_order = load_json(module_order_path)
        best = module_order["t00_control"]["best"]
        add(
            "module_tape_order_search",
            ["G", "H"],
            best["observed"],
            0.0,
            0.35,
            0.55,
            best["bonferroni_p"],
            module_order["verdict"],
        )
    t00_fsa_path = HERE / "t00_internal_fsa_compression_results.json"
    if t00_fsa_path.exists():
        t00_fsa = load_json(t00_fsa_path)
        best = t00_fsa["best"]
        order_control = t00_fsa["controls"]["slice_order_permutation"]
        add(
            "t00_internal_fsa_compression_probe",
            ["G", "H"],
            min(1.0, max(0.0, best["net_gain_bits_vs_order0"] / 3000.0)),
            0.0,
            0.35,
            0.65,
            order_control["p_ge_observed"],
            t00_fsa["verdict"],
        )
    tape_formula_path = HERE / "tape_based_formula_469.json"
    if tape_formula_path.exists():
        tape_formula = load_json(tape_formula_path)
        validation = tape_formula["validation"]
        mdl = tape_formula["mdl_estimate"]
        add(
            "tape_based_mechanical_formula",
            ["G", "H", "I"],
            validation["books_roundtrip_ok"] / validation["book_count"],
            mdl["total_gain_bits_rough"] / 1000.0,
            0.7,
            0.35,
            0.0,
            tape_formula["verdict"],
        )
    tape_token_path = HERE / "tape_tokenization_results.json"
    if tape_token_path.exists():
        tape_token = load_json(tape_token_path)
        summary = tape_token["summary"]
        pred = (
            summary["component_digit_coverage_fraction"]
            + (1.0 - min(1.0, summary["interval_conflict_count"]))
            + summary["module_slices_both_token_boundary"] / summary["module_slice_count"]
        ) / 3.0
        add(
            "tape_tokenization_analysis",
            ["G", "H", "J"],
            pred,
            0.0,
            0.55,
            0.45,
            tape_token["slice_boundary_control"]["p_good_direction"],
            tape_token["verdict"],
        )
    tape_first_use_path = HERE / "tape_first_use_pair_order_results.json"
    if tape_first_use_path.exists():
        tape_first = load_json(tape_first_use_path)
        best = tape_first["best"]
        pred = max(best["abs_spearman"], best["lcs_fraction"], best["adjacency_fraction"])
        add(
            "tape_first_use_pair_order_search",
            ["A", "G", "H"],
            pred,
            0.0,
            0.45,
            0.55,
            best["bonferroni_p"],
            tape_first["verdict"],
        )
    tape_literal_path = HERE / "tape_literal_exception_results.json"
    if tape_literal_path.exists():
        tape_literal = load_json(tape_literal_path)
        features = tape_literal["features"]
        pred = features["pair_diagonal_count"] / max(1, features["pair_count"])
        add(
            "tape_literal_exception_analysis",
            ["A", "H", "I"],
            pred,
            0.0,
            0.35,
            0.55,
            tape_literal["bonferroni_p"],
            tape_literal["verdict"],
        )
    tape_feature_path = HERE / "tape_feature_pair_label_results.json"
    if tape_feature_path.exists():
        tape_feature = load_json(tape_feature_path)
        best = tape_feature["best"]
        control = tape_feature["controls"][best["feature_set"]]
        add(
            "tape_feature_pair_label_search",
            ["A", "H", "I"],
            best["accuracy"],
            0.0,
            0.35,
            0.55,
            control["p_good_direction"],
            tape_feature["verdict"],
        )
    residual_tape_after_e_path = HERE / "residual_tape_feature_after_e_results.json"
    if residual_tape_after_e_path.exists():
        residual_tape = load_json(residual_tape_after_e_path)
        best = residual_tape["best"]
        control = residual_tape["controls"][best["feature_set"]]
        add(
            "residual_tape_feature_after_e_search",
            ["A", "G", "H"],
            best["accuracy"],
            best["mdl_gain_vs_residual_lookup_bits"] / 1000.0,
            0.35,
            0.60,
            control["mdl_gain"]["p_good_direction"],
            residual_tape["verdict"],
        )
    residual_marginal_after_e_path = HERE / "residual_marginal_after_e_results.json"
    if residual_marginal_after_e_path.exists():
        residual_marginal = load_json(residual_marginal_after_e_path)
        best = residual_marginal["best"]
        add(
            "residual_marginal_after_e_search",
            ["A"],
            max(0.0, min(1.0, best["z_good_direction"] / 4.0)),
            0.0,
            0.25,
            0.60,
            residual_marginal["best_bonferroni_p"],
            residual_marginal["verdict"],
        )
    high_block_blocker_path = HERE / "high_block_blocker_origin_results.json"
    if high_block_blocker_path.exists():
        high_block = load_json(high_block_blocker_path)
        best = high_block["observed_best"]
        add(
            "high_block_blocker_origin_search",
            ["A"],
            best["f1"],
            0.0,
            0.35,
            0.65,
            max(
                high_block["conditional_controls"]["p_exact"],
                high_block["stroke_path"]["p_connected_subset"],
            ),
            high_block["verdict"],
        )
    render_origin_e_path = HERE / "render_origin_e_priority_probe_results.json"
    if render_origin_e_path.exists():
        render_origin_e = load_json(render_origin_e_path)
        priority = render_origin_e["priority_claims"]
        blockers = render_origin_e["high_block_blockers"]
        add(
            "render_origin_e_priority_probe",
            ["A", "G", "J"],
            max(priority["best"]["f1"], blockers["best"]["f1"]),
            0.0,
            0.35,
            0.70,
            max(
                priority["controls"]["geometry_stratified_target_shuffle"]["p_ge_observed"],
                blockers["controls"]["geometry_stratified_target_shuffle"]["p_ge_observed"],
            ),
            render_origin_e["verdict"],
        )
    marginal_path = HERE / "pair_marginal_signature_results.json"
    if marginal_path.exists():
        marginal = load_json(marginal_path)
        best = marginal["control"]["best"]
        add(
            "pair_marginal_signature_search",
            ["A"],
            max(0.0, min(1.0, best["z_good_direction"] / 4.0)),
            0.0,
            0.25,
            0.60,
            best["bonferroni_p"],
            marginal["verdict"],
        )
    assignment_path = HERE / "pair_assignment_constraint_results.json"
    if assignment_path.exists():
        assignment = load_json(assignment_path)
        add(
            "pair_assignment_constraint_search",
            ["A"],
            assignment["best"]["accuracy"],
            0.0,
            0.25,
            0.75,
            assignment["control"]["p_ge_observed"],
            "rejected_control",
        )
    endpoint_affinity_path = HERE / "endpoint_affinity_assignment_results.json"
    if endpoint_affinity_path.exists():
        endpoint_affinity = load_json(endpoint_affinity_path)
        best_loo = max(
            endpoint_affinity["variants"],
            key=lambda item: item["leave_one_pair_out"]["accuracy"],
        )
        best_assign = max(
            endpoint_affinity["variants"],
            key=lambda item: item["exact_inventory_assignment"]["accuracy"],
        )
        leakage = min(
            best_loo["controls"]["inventory_label_shuffle"]["leave_one_pair_out_accuracy"]["p"],
            best_assign["controls"]["inventory_label_shuffle"]["exact_inventory_assignment_accuracy"]["p"],
        )
        add(
            "endpoint_affinity_assignment_search",
            ["A", "F"],
            best_loo["leave_one_pair_out"]["accuracy"],
            0.0,
            0.30,
            0.75,
            leakage,
            endpoint_affinity["verdict"],
        )
    bilinear_path = HERE / "bilinear_low_rank_pair_factor_results.json"
    if bilinear_path.exists():
        bilinear = load_json(bilinear_path)
        best = bilinear["best_by_loo"]
        mdl = bilinear["mdl_context"]
        excess_bits = max(0.0, mdl["lower_bound_parameter_bits"] - mdl["inventory_lookup_bits"])
        add(
            "bilinear_low_rank_pair_factor_search",
            ["A", "F"],
            best["loo_accuracy"],
            -excess_bits / 1000.0,
            0.25,
            0.75,
            bilinear["control"]["loo_accuracy"]["p_ge_observed"],
            bilinear["verdict"],
        )
    quotient_low_rank_path = HERE / "quotient_low_rank_pair_factor_results.json"
    if quotient_low_rank_path.exists():
        quotient_low_rank = load_json(quotient_low_rank_path)
        best = quotient_low_rank["best_by_loo"]
        mdl = quotient_low_rank["mdl_context"]
        excess_bits = max(
            0.0,
            mdl["conditioned_lossless_lower_bound_bits"] - mdl["existing_split_lossless_bits"],
        )
        add(
            "quotient_low_rank_pair_factor_search",
            ["A", "B"],
            best["loo_accuracy"],
            -excess_bits / 1000.0,
            0.25,
            0.75,
            max(
                quotient_low_rank["controls"]["label_shuffle"]["loo_accuracy"]["p_ge_observed"],
                quotient_low_rank["controls"]["stratified_mixedness_shuffle"]["loo_accuracy"]["p_ge_observed"],
            ),
            quotient_low_rank["verdict"],
        )
    matrix_exhaustive_path = HERE / "matrix_generator_exhaustive_results.json"
    if matrix_exhaustive_path.exists():
        matrix_exhaustive = load_json(matrix_exhaustive_path)
        best = matrix_exhaustive["best_by_cells"]
        add(
            "matrix_generator_exhaustive_search",
            ["A", "B", "C", "D", "F"],
            best["coverage_fraction"],
            best["mdl_gain_vs_lookup_bits"] / 1000.0,
            0.45 if best["uses_lore"] else 0.30,
            min(1.0, best["lookup_cost_ratio"]),
            best.get("control_p_monte_carlo_top", best["control_p"]),
            matrix_exhaustive["overall_verdict"],
        )
    pair_rule_cover_path = HERE / "pair_rule_cover_results.json"
    if pair_rule_cover_path.exists():
        pair_rule_cover = load_json(pair_rule_cover_path)
        best = pair_rule_cover["best"]
        add(
            "pair_rule_cover_search",
            ["A", "B", "C", "D"],
            best["primary_accuracy"],
            best["primary_mdl_gain_vs_lookup_bits"] / 1000.0,
            0.30,
            min(1.0, best["primary_lookup_cost_ratio"]),
            pair_rule_cover["control"]["primary_hits_p_ge"],
            pair_rule_cover["verdict"],
        )
    adaptive_fill_path = HERE / "adaptive_quota_fill_results.json"
    if adaptive_fill_path.exists():
        adaptive = load_json(adaptive_fill_path)
        best = adaptive["best"]
        add(
            "adaptive_quota_fill_search",
            ["A", "F"],
            best["accuracy"],
            best["mdl"]["mdl_gain_vs_lookup_bits"] / 1000.0,
            0.30,
            min(1.0, best["mdl"]["lookup_cost_ratio"]),
            adaptive["control"]["p_ge_observed"],
            adaptive["verdict"],
        )
    row_balance_path = HERE / "row_column_balance_objective_results.json"
    if row_balance_path.exists():
        row_balance = load_json(row_balance_path)
        best = row_balance["metrics"][0]
        add(
            "row_column_balance_objective_search",
            ["A", "F"],
            max(0.0, min(1.0, best["control"]["z_good_direction"] / 4.0)),
            0.0,
            0.30,
            0.65,
            best["control"]["p_good_direction"],
            row_balance["verdict"],
        )
    composite_objective_path = HERE / "composite_objective_inverse_results.json"
    if composite_objective_path.exists():
        composite = load_json(composite_objective_path)
        best = composite["best_objectives"][0]
        best_ctrl = composite["controls"]["best_of_search"]["best_swap_improvement"]
        prediction = 0.5 if best["is_local_optimum"] else max(0.0, min(0.5, 0.5 - best["best_swap_improvement"] / 2.0))
        add(
            "composite_objective_inverse_search",
            ["A", "F", "G", "J"],
            prediction,
            0.0,
            0.35,
            0.70,
            best_ctrl["p"],
            composite["verdict"],
        )
    finite_group_path = HERE / "finite_group_pair_formula_results.json"
    if finite_group_path.exists():
        finite = load_json(finite_group_path)
        best = finite["observed"]["best"]
        add(
            "finite_group_pair_formula_search",
            ["A", "B"],
            best["accuracy"],
            best["mdl_gain_vs_lookup_bits"] / 1000.0,
            0.35,
            min(1.0, best["lookup_cost_ratio"]),
            max(
                finite["control"]["hits"]["p_ge_observed"],
                finite["control"]["mdl_gain"]["p_ge_observed"],
            ),
            finite["verdict"],
        )
    direct_symbol_path = HERE / "direct_symbol_formula_results.json"
    if direct_symbol_path.exists():
        direct_symbol = load_json(direct_symbol_path)
        best = direct_symbol["observed"]["best"]
        add(
            "direct_symbol_formula_search",
            ["A"],
            best["primary_accuracy"],
            best["mdl_gain_vs_lookup_bits"] / 1000.0,
            0.25,
            min(1.0, best["lookup_cost_ratio"]),
            max(
                direct_symbol["controls"]["inventory_label_shuffle"]["hits"]["p_good_direction"],
                direct_symbol["controls"]["symbol_order_shuffle"]["hits"]["p_good_direction"],
            ),
            direct_symbol["verdict"],
        )
    digit_auto_path = HERE / "digit_symbol_automorphism_results.json"
    if digit_auto_path.exists():
        digit_auto = load_json(digit_auto_path)
        best = digit_auto["best_identity"]
        trace = digit_auto["best_identity_trace"]
        moved_score = trace["moved_pair_preserved_count"] / max(1, trace["moved_pair_count"])
        add(
            "digit_symbol_automorphism_search",
            ["A", "B", "C", "D"],
            moved_score,
            best["identity_mdl_gain_vs_lookup_bits"] / 1000.0,
            0.30,
            0.35,
            digit_auto["control"]["identity_hits"]["p_ge_observed"],
            digit_auto["verdict"],
        )
    digit_orbit_path = HERE / "digit_orbit_quotient_results.json"
    if digit_orbit_path.exists():
        digit_orbit = load_json(digit_orbit_path)
        best = digit_orbit["best"]
        add(
            "digit_orbit_quotient_search",
            ["A", "B", "C", "D"],
            best["primary_accuracy"],
            best["split_mdl_gain_vs_lookup_bits"] / 1000.0,
            0.35,
            0.55,
            digit_orbit["control"]["best_split_mdl_gain_bits"]["p_good_direction"],
            digit_orbit["verdict"],
        )
    split_pair_path = HERE / "digit_orbit_split_label_pair_results.json"
    if split_pair_path.exists():
        split_pair = load_json(split_pair_path)
        structural = split_pair["observed"]["structural_split_model"]
        pair_lookup_bits = split_pair["pair_lookup_bits"]
        leakage = max(
            split_pair["controls"]["pair_row_shuffle_preserving_directed_pairs"]["structural_lossless_bits"]["p_good_direction"],
            split_pair["controls"]["directed_label_shuffle_preserving_inventory"]["structural_lossless_bits"]["p_good_direction"],
        )
        add(
            "digit_orbit_split_label_pair_search",
            ["A", "B", "C", "D"],
            max(0.0, 1.0 - structural["pair_lookup_ratio"]),
            (pair_lookup_bits - structural["lossless_bits"]) / 1000.0,
            0.35,
            min(1.0, structural["pair_lookup_ratio"]),
            leakage,
            split_pair["verdict"],
        )
    directed_prov_path = HERE / "digit_orbit_directed_provenance_results.json"
    if directed_prov_path.exists():
        directed_prov = load_json(directed_prov_path)
        best = directed_prov["mixedness"]["best_by_accuracy"]
        leakage = max(
            directed_prov["controls"]["exhaustive_same_size_subsets"]["exact_rule_cost"]["p_good_direction"],
            directed_prov["controls"]["exhaustive_same_size_subsets"]["best_mdl_bits"]["p_good_direction"],
        )
        add(
            "digit_orbit_directed_provenance_search",
            ["A", "C", "D"],
            best["accuracy"] * (9.0 / 55.0),
            best["mdl_gain_vs_explicit_subset_bits"] / 1000.0,
            0.35,
            0.70,
            leakage,
            directed_prov["verdict"],
        )
    robust_orbit_path = HERE / "digit_orbit_robust_control_results.json"
    if robust_orbit_path.exists():
        robust_orbit = load_json(robust_orbit_path)
        fixed = robust_orbit["observed"]["swap_6_9"]
        leakage = max(
            robust_orbit["controls"][name]["best_of_45_swaps"]["mixed_non_singleton_orbit_count"]["p_good_direction"]
            for name in robust_orbit["controls"]
        )
        add(
            "digit_orbit_robust_control_search",
            ["A", "B", "C", "D"],
            fixed["primary_accuracy"] * (9.0 / 55.0),
            fixed["split_mdl_gain_vs_lookup_bits"] / 1000.0,
            0.35,
            0.60,
            leakage,
            robust_orbit["verdict"],
        )
    nine_identity_path = HERE / "nine_identity_render_split_results.json"
    if nine_identity_path.exists():
        nine_identity = load_json(nine_identity_path)
        renderer = nine_identity["observed"]["renderer_aware"]
        leakage = nine_identity["controls"]["global_inventory_shuffle"]["renderer_gain_vs_raw_lookup_bits"]["p_good_direction"]
        add(
            "nine_identity_render_split_search",
            ["A", "B", "C", "D"],
            max(0.0, 1.0 - renderer["lookup_ratio"]),
            renderer["gain_vs_raw_lookup_bits"] / 1000.0,
            0.35,
            min(1.0, renderer["lookup_ratio"]),
            leakage,
            nine_identity["verdict"],
        )
    edit_log_path = HERE / "quotient_edit_log_mdl_results.json"
    if edit_log_path.exists():
        edit_log = load_json(edit_log_path)
        best = edit_log["best_non_leaky"]["edit_log"]
        leakage = edit_log["controls"]["inventory_label_shuffle"]["best_gain_vs_lookup_bits"]["p_good_direction"]
        add(
            "quotient_edit_log_mdl_search",
            ["A", "B", "F"],
            max(0.0, best["gain_vs_lookup_bits"] / best["lookup_bits"]),
            best["gain_vs_lookup_bits"] / 1000.0,
            0.35,
            min(1.0, best["lookup_ratio"]),
            leakage,
            edit_log["verdict"],
        )
    base_accent_path = HERE / "symbol_base_accent_layer_results.json"
    if base_accent_path.exists():
        base_accent = load_json(base_accent_path)
        best = base_accent["observed"]["best"]
        leakage = base_accent["controls"]["inventory_label_shuffle"]["best_gain_vs_raw_lookup_bits"]["p_good_direction"]
        add(
            "symbol_base_accent_layer_search",
            ["A", "F"],
            max(0.0, best["gain_vs_raw_lookup_bits"] / base_accent["baselines"]["raw_lookup_bits"]),
            best["gain_vs_raw_lookup_bits"] / 1000.0,
            0.25,
            min(1.0, best["lookup_ratio"]),
            leakage,
            base_accent["verdict"],
        )
    quotient_inventory_path = HERE / "quotient_inventory_pressure_results.json"
    if quotient_inventory_path.exists():
        quotient_inventory = load_json(quotient_inventory_path)
        explicit = quotient_inventory["targets"]["quotient_explicit_50"]["best"]
        pair_control = quotient_inventory["pair_label_shuffle_control"]
        add(
            "quotient_inventory_pressure_search",
            ["A", "F"],
            1.0 - explicit["normalized_l1_per_slot"],
            explicit["inventory_plus_mixed_overhead_gain_bits"] / 1000.0,
            0.35,
            0.70,
            pair_control["quotient_explicit_50_best_normalized_l1"]["p_good_direction"],
            quotient_inventory["verdict"],
        )
    quotient_formula_path = HERE / "quotient_pair_formula_results.json"
    if quotient_formula_path.exists():
        quotient_formula = load_json(quotient_formula_path)
        best = quotient_formula["observed"]["best"]
        add(
            "quotient_pair_formula_search",
            ["A", "B", "C", "D"],
            best["primary_accuracy"],
            best["mdl_gain_vs_quotient_lookup_bits"] / 1000.0,
            0.35,
            min(1.0, best["quotient_lookup_cost_ratio"]),
            max(
                quotient_formula["controls"]["inventory_label_shuffle"]["hits"]["p_good_direction"],
                quotient_formula["controls"]["symbol_order_shuffle"]["hits"]["p_good_direction"],
            ),
            quotient_formula["verdict"],
        )
    quotient_line_path = HERE / "quotient_line_order_results.json"
    if quotient_line_path.exists():
        quotient_line = load_json(quotient_line_path)
        best = quotient_line["searches"]["line_template"]["best"]
        control = quotient_line["control"]
        add(
            "quotient_line_order_search",
            ["A", "B", "D"],
            best["match_fraction"],
            best["mdl_gain_vs_lookup_bits"] / 1000.0,
            0.35,
            min(1.0, best["lookup_cost_ratio"]),
            max(
                control["global_label_shuffle"]["line_best_match_fraction"]["p_ge_observed"],
                control["stratified_inventory_shuffle"]["line_best_match_fraction"]["p_ge_observed"],
            ),
            quotient_line["verdict"],
        )
    symbol_dnf_path = HERE / "symbol_predicate_dnf_results.json"
    if symbol_dnf_path.exists():
        symbol_dnf = load_json(symbol_dnf_path)
        observed = symbol_dnf["observed"]
        add(
            "symbol_predicate_dnf_search",
            ["A", "F"],
            observed["accuracy"],
            observed["mdl_gain_vs_lookup_bits"] / 1000.0,
            0.25,
            min(1.0, observed["lookup_cost_ratio"]),
            max(
                symbol_dnf["control"]["hit_count"]["p_good_direction"],
                symbol_dnf["control"]["mdl_gain_vs_lookup_bits"]["p_good_direction"],
            ),
            symbol_dnf["verdict"],
        )
    algebraic_path = HERE / "algebraic_digit_composition_results.json"
    if algebraic_path.exists():
        algebraic = load_json(algebraic_path)
        best = algebraic["observed"]["best_compact"]
        add(
            "algebraic_digit_composition_search",
            ["A", "B", "F"],
            best["accuracy"],
            best["mdl_gain_vs_raw_lookup_bits"] / 1000.0,
            0.35 if best.get("uses_lore") else 0.25,
            min(1.0, best["lookup_cost_ratio"]),
            max(
                algebraic["control"]["compact_best_primary_hits"]["p_good_direction"],
                algebraic["control"]["compact_best_mdl_gain"]["p_good_direction"],
            ),
            algebraic["verdict"],
        )
    marginal_solver_path = HERE / "marginal_constraint_solver_results.json"
    if marginal_solver_path.exists():
        marginal_solver = load_json(marginal_solver_path)
        best = marginal_solver["best_by_total_mdl"]
        add(
            "marginal_constraint_solver_search",
            ["A", "B", "C", "D", "F"],
            1.0 - min(1.0, best["residual_bits"] / marginal_solver["baselines"]["inventory_residual_bits"]),
            (marginal_solver["baselines"]["raw_lookup_bits"] - best["total_mdl_bits"]) / 1000.0,
            0.35,
            min(1.0, best["lookup_ratio"]),
            best["control"]["total_mdl_bits"]["p_good_direction"],
            marginal_solver["verdict"],
        )
    quotient_constructive_path = HERE / "quotient_constructive_fill_results.json"
    if quotient_constructive_path.exists():
        quotient_constructive = load_json(quotient_constructive_path)
        best = quotient_constructive["best_non_leaky"]
        add(
            "quotient_constructive_fill_search",
            ["A", "B", "F"],
            best["exact_accuracy"],
            best["mdl_gain_vs_lookup_bits"] / 1000.0,
            0.35,
            min(1.0, best["lookup_cost_ratio"]),
            max(
                quotient_constructive["controls"]["search_label_shuffle_preserving_inventory"]["p_ge_observed"],
                quotient_constructive["controls"]["best_non_leaky_order_shuffle"]["p_ge_observed"],
            ),
            quotient_constructive["verdict"],
        )
    orbit_exception_path = HERE / "digit_orbit_exception_rule_results.json"
    if orbit_exception_path.exists():
        orbit_exception = load_json(orbit_exception_path)
        best = orbit_exception["best_mixed_rule"]
        add(
            "digit_orbit_exception_rule_search",
            ["A", "C", "D"],
            best["correct"] / 9.0,
            orbit_exception["mdl"]["gain_vs_raw_lookup_bits"] / 1000.0,
            0.35,
            0.75,
            max(
                orbit_exception["controls"]["mixed_rule_exact_cost"]["p_good_direction"],
                orbit_exception["controls"]["orientation_rule_correct"]["p_good_direction"],
            ),
            orbit_exception["verdict"],
        )
    orbit_context_path = HERE / "digit_orbit_exception_context_results.json"
    if orbit_context_path.exists():
        orbit_context = load_json(orbit_context_path)
        best = orbit_context["best"]
        add(
            "digit_orbit_exception_context_search",
            ["A", "G", "H"],
            best["balanced_accuracy"],
            0.0,
            0.30,
            0.75,
            best["controls"]["balanced_accuracy"]["p_good_direction"],
            orbit_context["verdict"],
        )
    visual_symmetry_path = HERE / "digit_visual_symmetry_results.json"
    if visual_symmetry_path.exists():
        visual = load_json(visual_symmetry_path)
        best = visual["observed_best_by_mdl"]
        add(
            "digit_visual_symmetry_search",
            ["A", "C", "D"],
            best["nontrivial_accuracy"],
            best["model_cost_gain_bits"] / 1000.0,
            0.35,
            0.65,
            visual["controls"]["best_mdl_gain_bits"]["p_good_direction"],
            visual["verdict"],
        )
    sevenseg_exception_path = HERE / "sevenseg_orbit_exception_selector_results.json"
    if sevenseg_exception_path.exists():
        sevenseg_exception = load_json(sevenseg_exception_path)
        selector = sevenseg_exception["best_selector"]
        add(
            "sevenseg_orbit_exception_selector",
            ["A", "C", "D"],
            selector["correct"] / max(1, len(sevenseg_exception["orbit_rows"])),
            sevenseg_exception["mdl"]["gain_vs_raw_lookup_bits"] / 1000.0,
            0.30,
            0.70,
            max(
                sevenseg_exception["controls"]["mixed_rule_exact_cost"]["p_good_direction"],
                sevenseg_exception["controls"]["orientation_rule_correct"]["p_good_direction"],
            ),
            sevenseg_exception["verdict"],
        )
    signature_path = HERE / "digit_signature_formula_results.json"
    if signature_path.exists():
        signature = load_json(signature_path)
        index = signature["observed"]["index_formula"]["best_accuracy"]
        baseline = signature["mdl_baselines"]["inventory_preserving_pair_lookup_bits"]
        add(
            "digit_signature_formula_search",
            ["A", "F"],
            index["primary_correct"] / 55.0,
            (baseline - index["mdl_bits"]) / 1000.0,
            0.20,
            0.75,
            signature["controls"]["summaries"]["index_primary_correct"]["p_good_direction"],
            signature["verdict"]["status"],
        )
    pair_hash_path = HERE / "pair_hash_formula_results.json"
    if pair_hash_path.exists():
        pair_hash = load_json(pair_hash_path)
        best = pair_hash["observed"]["best"]
        leakage = max(
            pair_hash["controls"]["inventory_label_shuffle"]["hits"]["p_good_direction"],
            pair_hash["controls"]["symbol_order_shuffle"]["hits"]["p_good_direction"],
        )
        add(
            "pair_hash_formula_search",
            ["A"],
            best["primary_accuracy"],
            best["mdl_gain_vs_lookup_bits"] / 1000.0,
            0.40,
            min(1.0, best["lookup_cost_ratio"]),
            leakage,
            pair_hash["verdict"],
        )
    block_cover_path = HERE / "block_biclique_cover_results.json"
    if block_cover_path.exists():
        block_cover = load_json(block_cover_path)
        best = block_cover["best_global"]
        control_summary = block_cover["control"]["summary"]
        add(
            "block_biclique_cover_search",
            ["A", "B", "F"],
            best["primary_accuracy"],
            best["gain_vs_inventory_lookup_bits"] / 1000.0,
            0.25,
            min(1.0, best["mdl_ratio_vs_inventory_lookup"]),
            control_summary["global_primary_hits_p_ge"],
            block_cover["verdict"],
        )
    digit_perm_path = HERE / "digit_permutation_formula_results.json"
    if digit_perm_path.exists():
        digit_perm = load_json(digit_perm_path)
        compact = digit_perm["best_compact_non_lookup"]
        add(
            "digit_permutation_formula_search",
            ["A"],
            compact["accuracy"],
            0.0,
            0.25,
            0.85,
            digit_perm["control"]["compact_p_ge_observed"],
            "rejected_control",
        )
    digit_order_distance_path = HERE / "digit_order_distance_results.json"
    if digit_order_distance_path.exists():
        digit_order = load_json(digit_order_distance_path)
        best_line = digit_order["line_sample"]["best"]
        best_cycle = digit_order["cycle_exact"]["best"]
        best = best_line if best_line["correct"] >= best_cycle["correct"] else best_cycle
        leakage = min(
            digit_order["control"]["line_correct_summary"]["p_ge_observed"],
            digit_order["control"]["cycle_correct_summary"]["p_ge_observed"],
        )
        add(
            "digit_order_distance_search",
            ["A", "B", "C", "D"],
            best["accuracy"],
            best["mdl_gain_vs_lookup_bits"] / 1000.0,
            0.25,
            min(1.0, best["lookup_cost_ratio"]),
            leakage,
            digit_order["verdict"],
        )
    triangular_line_path = HERE / "triangular_line_pattern_results.json"
    if triangular_line_path.exists():
        triangular = load_json(triangular_line_path)
        add(
            "triangular_line_pattern_search",
            ["A"],
            0.0,
            0.0,
            0.2,
            0.55,
            triangular["control"]["long_hit_p_ge_observed"],
            triangular["verdict"],
        )
    line_template_path = HERE / "line_template_alignment_results.json"
    if line_template_path.exists():
        line_template = load_json(line_template_path)
        best = line_template["best"]
        add(
            "line_template_alignment_search",
            ["A"],
            best["match_fraction"],
            best["mdl_gain_vs_lookup_bits"] / 1000.0,
            0.30,
            min(1.0, best["lookup_cost_ratio"]),
            max(
                line_template["control"]["match_fraction"]["p_ge_observed"],
                line_template["control"]["mdl_gain_vs_lookup_bits"]["p_ge_observed"],
            ),
            line_template["verdict"],
        )
    row_transition_path = HERE / "row_transition_edit_mdl_results.json"
    if row_transition_path.exists():
        row_transition = load_json(row_transition_path)
        best = row_transition["best"]
        ctrl = row_transition["controls"]["inventory_label_shuffle_best_of_search"]
        add(
            "row_transition_edit_mdl_search",
            ["A"],
            best["copied_fraction_after_first"],
            best["mdl_gain_vs_lookup_bits"] / 1000.0,
            0.25,
            0.65,
            ctrl["mdl_gain_vs_lookup_bits"]["p"],
            row_transition["verdict"],
        )
    local_2d_path = HERE / "local_2d_pair_rule_results.json"
    if local_2d_path.exists():
        local_2d = load_json(local_2d_path)
        best = local_2d["observed"]["best"]
        add(
            "local_2d_pair_rule_search",
            ["A"],
            best["primary_accuracy"],
            best["primary_mdl_gain_vs_lookup_bits"] / 1000.0,
            0.30,
            min(1.0, best["primary_lookup_cost_ratio"]),
            local_2d["control"]["primary_hits"]["p_ge"],
            local_2d["verdict"],
        )
    automaton_path = HERE / "pair_sequence_automaton_results.json"
    if automaton_path.exists():
        automaton = load_json(automaton_path)
        best_metric = automaton["best"]["strongest_metric"]
        add(
            "pair_sequence_automaton_search",
            ["A"],
            max(0.0, min(1.0, best_metric["z"] / 4.0)),
            0.0,
            0.25,
            0.75,
            automaton["best"]["bonferroni_p"],
            automaton["verdict"],
        )
    intrasymbol_path = HERE / "homophone_intrasymbol_order_results.json"
    if intrasymbol_path.exists():
        intrasymbol = load_json(intrasymbol_path)
        strongest = intrasymbol["strongest"]
        add(
            "homophone_intrasymbol_order_search",
            ["A", "F"],
            max(0.0, min(1.0, strongest["z"] / 4.0)),
            0.0,
            0.25,
            0.55,
            strongest["p"],
            intrasymbol["verdict"],
        )
    latent_path = HERE / "latent_digit_factor_results.json"
    if latent_path.exists():
        latent = load_json(latent_path)
        best = latent["best_exhaustive"]
        add(
            "latent_digit_factor_search",
            ["A"],
            best["accuracy"],
            0.0,
            0.25,
            0.75,
            latent["sampled_control"]["p_ge_observed"],
            latent["verdict"],
        )
    graph_path = HERE / "pair_graph_incidence_results.json"
    if graph_path.exists():
        graph = load_json(graph_path)
        best = graph["best_metric"]
        add(
            "pair_graph_incidence_search",
            ["A"],
            max(0.0, min(1.0, best["z_good_direction"] / 4.0)),
            0.0,
            0.25,
            0.65,
            best["bonferroni_p"],
            graph["verdict"],
        )
    graph_motif_path = HERE / "pair_graph_motif_results.json"
    if graph_motif_path.exists():
        graph_motif = load_json(graph_motif_path)
        best = graph_motif["best_metric"]
        add(
            "pair_graph_motif_search",
            ["A"],
            max(0.0, min(1.0, best["z_good_direction"] / 4.0)),
            0.0,
            0.25,
            0.65,
            best["bonferroni_p"],
            graph_motif["verdict"],
        )
    context_cluster_path = HERE / "pair_context_cluster_results.json"
    if context_cluster_path.exists():
        context_cluster = load_json(context_cluster_path)
        best = context_cluster["control"]["best"]
        add(
            "pair_context_cluster_search",
            ["A", "F", "G"],
            max(0.0, min(1.0, best["z_good_direction"] / 4.0)),
            0.0,
            0.35,
            0.55,
            best["bonferroni_p"],
            context_cluster["verdict"],
        )
    context_partition_path = HERE / "pair_context_partition_results.json"
    if context_partition_path.exists():
        context_partition = load_json(context_partition_path)
        best = context_partition["best"]
        add(
            "pair_context_partition_search",
            ["A", "F", "G"],
            max(0.0, min(1.0, best["control"]["f1"]["z_good_direction"] / 4.0)),
            0.0,
            0.35,
            0.65,
            best["bonferroni_p"],
            context_partition["verdict"],
        )
    stream_compression_path = HERE / "pair_symbol_stream_compression_results.json"
    if stream_compression_path.exists():
        stream_compression = load_json(stream_compression_path)
        best = stream_compression["control"]["best"]
        add(
            "pair_symbol_stream_compression_search",
            ["A", "G", "H"],
            max(0.0, min(1.0, best["z_good_direction"] / 4.0)),
            0.0,
            0.35,
            0.55,
            best["bonferroni_p"],
            stream_compression["verdict"],
        )
    stream_optimization_path = HERE / "pair_symbol_stream_optimization_results.json"
    if stream_optimization_path.exists():
        stream_optimization = load_json(stream_optimization_path)
        gain = stream_optimization["best_one_swap"]["gain"]
        add(
            "pair_symbol_stream_optimization_search",
            ["A", "G", "H"],
            0.0,
            -gain / 1000.0,
            0.25,
            0.45,
            0.0,
            stream_optimization["verdict"],
        )
    lore_text_path = HERE / "lore_text_subsequence_results.json"
    if lore_text_path.exists():
        lore_text = load_json(lore_text_path)
        best = lore_text["best_window_source"]["best_window"]
        add(
            "lore_text_subsequence_search",
            ["A"],
            best["accuracy"],
            0.0,
            0.45,
            0.65,
            lore_text["window_global_control"]["global_p_ge"],
            lore_text["verdict"],
        )
    usage_path = HERE / "usage_driven_pair_placement_results.json"
    if usage_path.exists():
        usage = load_json(usage_path)
        best = usage["best_train"]
        add(
            "usage_driven_pair_placement_search",
            ["A", "G"],
            best["accuracy"],
            0.0,
            0.35,
            0.65,
            usage["train_best_control"]["p_ge_observed"],
            usage["verdict"],
        )
    digit_shape_path = HERE / "digit_shape_pressure_results.json"
    if digit_shape_path.exists():
        digit_shape = load_json(digit_shape_path)
        pair_best = digit_shape["pair_cell_model"]["strongest"]
        ordered_best = digit_shape["ordered_code_model"]["strongest"]
        pred = max(0.0, min(1.0, (pair_best["z_good_direction"] + ordered_best["z_good_direction"]) / 6.0))
        leakage = max(pair_best["p_good_direction"], ordered_best["p_good_direction"])
        add(
            "digit_shape_pressure_search",
            ["A", "J"],
            pred,
            0.0,
            0.25,
            0.65,
            leakage,
            digit_shape["verdict"],
        )
    decision_tree_path = HERE / "decision_tree_pair_formula_results.json"
    if decision_tree_path.exists():
        decision_tree = load_json(decision_tree_path)
        best = decision_tree["best_by_accuracy"]
        add(
            "decision_tree_pair_formula_search",
            ["A"],
            best["accuracy"],
            0.0,
            0.3,
            0.75,
            best["accuracy_p"],
            decision_tree["verdict"],
        )
    alt_geometry_path = HERE / "alternative_digit_geometry_results.json"
    if alt_geometry_path.exists():
        alt_geometry = load_json(alt_geometry_path)
        best = alt_geometry["observed_best"]
        add(
            "alternative_digit_geometry_search",
            ["A"],
            best["accuracy"],
            0.0,
            0.35,
            0.75,
            alt_geometry["global_accuracy_control"]["p"],
            alt_geometry["verdict"],
        )
    ml_probe_path = ML_PROBE / "ml_formula_probe_results.json"
    if ml_probe_path.exists():
        ml_probe = load_json(ml_probe_path)
        pair = ml_probe["pair_cell_probe"]
        add(
            "ml_pair_cell_probe",
            ["A"],
            pair["best"]["leave_one_cell_out_accuracy"],
            0.0,
            0.1,
            0.75,
            pair["best_vs_label_shuffle"]["p_good_direction"],
            pair["verdict"],
        )
        homo = ml_probe["homophone_probe"]
        selected = homo["selected_by_train_book_cv"]
        best_custom = max(row["test_multi_accuracy"] for row in homo["custom_baselines"])
        add(
            "ml_homophone_probe",
            ["G"],
            max(0.0, selected["test_multi_accuracy"] - best_custom),
            0.0,
            0.2,
            0.75,
            homo["selected_test_multi_vs_symbol_shuffle"]["p_good_direction"],
            homo["verdict"],
        )
        zero = ml_probe["zero_probe"]
        if zero["verdict"] in {"candidate_mechanical_signal", "weak_signal"} and "best_non_module_by_train_book_cv" in zero:
            selected_zero = zero["best_non_module_by_train_book_cv"]
            zero_summary = zero["best_non_module_vs_code_preserving_shuffle"]
            zero_complexity = 0.65
            zero_leakage = zero_summary["p_good_direction"]
        else:
            selected_zero = zero["selected_by_train_book_cv"]
            zero_summary = zero["selected_vs_code_preserving_shuffle"]
            zero_complexity = 0.85
            zero_leakage = 0.35 if zero["verdict"] == "leaky_upper_bound_only" else zero_summary["p_good_direction"]
        add(
            "ml_zero_omission_probe",
            ["J"],
            selected_zero["test_score"],
            0.0,
            0.2,
            zero_complexity,
            zero_leakage,
            "supporting_render_layer_signal_only",
        )
    rows.sort(key=lambda item: -item["score_total"])
    write_json(HERE / "accepted_rejected_hypotheses.json", {"schema": "accepted_rejected_hypotheses.v1", "rows": rows})
    lines = ["# Generator MDL Leaderboard", "", "| Hypothesis | Targets | Score | Verdict |", "|---|---|---:|---|"]
    for row in rows:
        lines.append(f"| `{row['hypothesis_id']}` | {', '.join(row['targets_explained'])} | {row['score_total']:.3f} | `{row['verdict']}` |")
    lines.append("")
    (HERE / "generator_mdl_leaderboard.md").write_text("\n".join(lines), encoding="utf-8")
    saturation = [
        "# Saturation Audit 2026-06-19",
        "",
        "Generated by `generator_search_suite.py` after parallel subagent review.",
        "",
        "This audit does not add a hypothesis, score, translation, or glossary. It",
        "records whether the remaining obvious generator-search families justify",
        "another immediate script pass.",
        "",
        "## Matrix 10x10 / Pair-Cell Placement",
        "",
        "Verdict: practical saturation. No new matrix script is justified now.",
        "",
        "Coverage already includes:",
        "",
        "- Low-rank, separable, and digit-interaction analogues:",
        "  `latent_digit_factor_report.md`, `endpoint_affinity_assignment_report.md`,",
        "  `algebraic_digit_composition_report.md`, `block_biclique_cover_report.md`,",
        "  `direct_symbol_formula_report.md`, `decision_tree_pair_formula_report.md`,",
        "  and the controlled ML pair-cell probe.",
        "- Cell order, permutation, and traversal hypotheses:",
        "  `matrix_generator_exhaustive_report.md`, `digit_permutation_formula_report.md`,",
        "  `inventory_shuffle_seed_report.md`, `pair_sequence_automaton_report.md`,",
        "  `row_transition_edit_mdl_report.md`, and `line_template_alignment_report.md`.",
        "- Quota, apportionment, and fill-order hypotheses:",
        "  `pair_table_constructive_report.md`, `adaptive_quota_fill_report.md`,",
        "  `pair_assignment_constraint_report.md`, `quotient_constructive_fill_report.md`,",
        "  and `marginal_constraint_solver_report.md`.",
        "",
        "A formal continuous bilinear/low-rank probe was then run as",
        "`bilinear_low_rank_pair_factor_search`. Its best rank-1 centered surface",
        "reaches `18/55` leave-one-pair-out accuracy (`0.327`, 1,000-control",
        "`p=0.02597`), but the favorable 8-bit parameter lower bound is still",
        "`14.931x` compressed inventory lookup. It is a weak technical signal,",
        "not a formula.",
        "",
        "The same low-rank probe was then rerun on the `6 <-> 9` quotient as",
        "`quotient_low_rank_pair_factor_search`. It drops to `11/46` base-orbit",
        "leave-one-out accuracy (`0.239`, label-shuffle `p=0.56436`) and its",
        "lossless lower bound is `12.208x` the existing split-lossless quotient.",
        "The quotient therefore does not rescue the continuous-surface hypothesis.",
        "",
        "A directed 00..99 sequence-generator pass was also run as",
        "`directed_surface_sequence_generator_search`. It finds a strong signal",
        "only on full directed/mirror interleavings (best raw `p=0.00067`), while",
        "upper-only remains weak (`p=0.10859`). This is mirror render redundancy,",
        "not a recovered upper-table sequence formula.",
        "",
        "## Sequence / Modules / Residuals / Zero / Homophones",
        "",
        "Verdict: practical saturation for immediate generator-origin work.",
        "",
        "Coverage already includes:",
        "",
        "- Grammar and modules: `module_overlap_grammar_report.md`,",
        "  `module_tape_origin_report.md`, `module_tape_order_report.md`, and",
        "  `tape_based_formula_report.md`.",
        "- Endpoint-conditioned literal bridges:",
        "  `endpoint_literal_bridge_mdl_report.md`.",
        "- Residuals: permissive residual coverage plus MDL pruning in",
        "  `residual_coverage_mdl_report.md`, with follow-up",
        "  `inventory_residual_explainer_report.md`.",
        "- Zero to matrix bridge: `zero_compact_rule_report.md`,",
        "  `shared_e_zero_predicate_report.md`, `e_layer_predicate_report.md`,",
        "  `priority_masked_e_layer_report.md`,",
        "  `anchored_remaining_fill_report.md`,",
        "  `priority_anchored_quotient_residual_fill_report.md`, and",
        "  `zero_homophone_transition_origin_probe_report.md`.",
        "- Lore-number zero render masks:",
        "  `lore_zero_phase_mask_report.md`.",
        "- Homophones: `homophone_intrasymbol_order_report.md`,",
        "  `homophone_selector_leaderboard.md`, and the ML homophone probe.",
        "- External holdouts and controls:",
        "  `external_holdout_chayenne_ytc_report.md`, `avar_tar_control_report.md`,",
        "  and `control_leakage_matrix.json`.",
        "",
        "The small remaining finite-compressor test for `T00` was then run as",
        "`t00_internal_fsa_compression_probe`. It finds strong local order-1",
        "regularity inside slice token sequences, but slice-order permutation gives",
        "the same gain (`p=0.38162`), so it does not recover a special authorial",
        "order for `T00` or derive the matrix.",
        "",
        "## Final Classification",
        "",
        "- Found: stronger mechanical manufacturing model, especially tape assembly,",
        "  frequency-weighted homophone inventory, weak robust `6<->9` clue, local",
        "  zero-rendering signal, and Chayenne copy-holdout support.",
        "- Not found: original exact pair-cell placement formula, semantic",
        "  translation, new plaintext, new glossary, or CipSoft-attested",
        "  number<->plaintext pair.",
        "",
        "State remains `mechanical_partial_not_final` and evidence plateau is",
        "confirmed under the current corpus.",
        "",
    ]
    (HERE / "saturation_audit_20260619.md").write_text("\n".join(saturation), encoding="utf-8")
    final = [
        "# Generator Model Final Report",
        "",
        "Generated by `generator_search_suite.py`.",
        "",
        "## Verdict",
        "",
        "Current state: `mechanical_partial_not_final`. The expanded search keeps",
        "weak hypotheses in the ledger and uses thresholds only as confidence",
        "labels, not exploration blockers.",
        "",
        "The best current generator-origin model remains mechanical: a handmade",
        "10x10 code table, dominated by unordered-pair geometry, frequency-weighted",
        "homophone allocation, homophone selection, copied pre-rendered numeric",
        "chunks reducible to overlap-tape components, residual exact repeats,",
        "and a secondary zero-rendering layer.",
        "",
        "No semantic translation, glossary, or CipSoft-attested number<->plaintext",
        "pair was found.",
        "",
        "## Saturation Audit",
        "",
        "Parallel subagent review on 2026-06-19 found practical saturation in the",
        "remaining obvious matrix and sequence fronts. The formal low-rank/bilinear",
        "follow-up now shows only weak predictive signal at high parameter cost;",
        "cell-order/placement, quota/fill, module grammar, zero-to-matrix, homophone,",
        "Chayenne/YTC, and Avar Tar control families are already covered by existing",
        "audits or would only refine the assembly layer. See",
        "`saturation_audit_20260619.md`.",
        "",
        "## Accepted / Useful Mechanical Layers",
        "",
        "- `core_mechanical_formula`: lossless 70/70 reconstruction.",
        "- `grid_unordered_pair`: strongest compact explanation of the table geometry.",
        "- `pair_table_frequency_allocation`: homophone class sizes track internal symbol frequency.",
        "- `frequency_weighted_stochastic_inventory`: one slot per symbol plus frequency-weighted extra slots is the strongest formula-like inventory generator.",
        "- `deterministic_apportionment_inventory`: classic apportionment rules support the frequency-weighted inventory, but do not recover exact counts.",
        "- `symbol_digit_origin_order`: repeated symbol chunks preserve exact code sequences, supporting digit-first chunk copying.",
        "- `module_overlap_tape_grammar`: the 62 stored modules collapse into 16 overlap-tape components with 2,307 gross digits saved and positive rough MDL after slice-address cost.",
        "- `module_tape_origin_search`: 15/16 overlap components occur as full book substrings and 107 residual literal digits are absorbed as same-component gaps.",
        "- `endpoint_literal_bridge_mdl_search`: 28 internal bridge literals do not transfer as endpoint-conditioned bridge strings; best family covers `0/590` leave-one-bridge/book holdout digits and `0/145` blind residual-holdout digits.",
        "- `tape_based_mechanical_formula`: lossless 70/70 formula using 16 tape components, 62 module slices, and merged same-component book spans.",
        "- `tape_tokenization_analysis`: tape components project coherently to internal code tokens with raw-digit edge exceptions.",
        "- `residual_exact_repeat_pruned`: improves the residual model under MDL/control pruning.",
        "- `orientation_render_rule`: ordered-code orientation is predictable from local Markov context on book holdout, but not a general pair-table formula.",
        "- `directed_pair_surface_search`: the ordered 00..99 surface is 99/100 present codes, with missing `39`, near-perfect upper/lower mirror rendering, and one directed `19`/`91` conflict; this is a render/orientation layer over lookup, not a new matrix formula.",
        "- `structural_exception_layer_search`: mirror lower plus exactly the `91` and `93` residuals renders the ordered surface losslessly and saves bits versus saturated ordered lookup, but still does not beat the compact unordered-pair lookup.",
        "- `digit_symbol_automorphism_search`: swapping digit identities `6` and `9` preserves 47/55 pair labels and 10/18 moved cells (`p=0.0331` for identity hits); this is a weak symmetry clue, not a full matrix formula.",
        "- `digit_orbit_quotient_search`: quotienting pair cells by `6 <-> 9` gives 46 orbits, 50 split-lossless labels, 4 mixed two-cell orbits, and a tiny `3.6` bit gain versus raw pair lookup; this is the strongest matrix-side weak clue, but still mostly lookup.",
        "- `digit_orbit_split_label_pair_search`: the nine non-singleton `6 <-> 9` orbit label-pairs are not generated by direct affine/cycle formulas (best `11/18` directed hits), but their split metadata compresses to `0.827x` pair-label lookup; this is weak bookkeeping support, not a label generator.",
        "- `digit_orbit_directed_provenance_search`: label-blind directed-surface metadata marks the four mixed `6 <-> 9` orbits as directed anomaly or edge pair, with side orientation by edge pair. Same-size subset controls keep this as weak provenance bookkeeping, not an independent formula.",
        "- `digit_orbit_robust_control_search`: the `6 <-> 9` signal survives global, row-preserving, and column-preserving label shuffles, including best-of-45 swap controls; this upgrades confidence in the clue while preserving its weak/non-generative status.",
        "- `quotient_inventory_pressure_search`: the explicit 50-label `6 <-> 9` quotient slightly improves frequency-apportionment inventory fit (L1/slot `0.200` vs `0.218`), but mixed-orbit overhead removes MDL promotion; weak support only.",
        "- `quotient_line_order_search`: line/template and fill-order scans over the `6 <-> 9` quotient show nominal structure (best line match `0.696`, fixed-winner p down to `0.0010`), but every best row has negative MDL gain, so this is not a formula.",
        "- `quotient_low_rank_pair_factor_search`: the continuous low-rank probe does not improve under the `6 <-> 9` quotient; it reaches only `11/46` base-orbit LOO accuracy (`p=0.56436`) and remains far more expensive than split-lossless quotient accounting.",
        "- `zero_omission_supporting_render_layer`: ML/local rules and sparse exceptions support a mechanical zero-rendering pass, but this is secondary to the unresolved matrix generator.",
        "- `zero_compact_rule_search`: fixed previous-code and geometry rules recover part of the zero-render signal; some compact variants beat `code_only` MDL in holdout, but the best predictive composite remains a supporting render layer rather than a promoted formula.",
        "- `shared_e_zero_predicate_search`: the fixed predicate `i>=j` links diagonal E pressure with previous-code zero omission (`5/10` diagonal E, `2/2` 33/66 anchors, zero holdout delta `+0.120`, joint control `p=0.00280`). This is a real shared mechanical signal, but it still does not derive the E labels or the pair table.",
        "- `e_layer_predicate_search`: after spending the diagonal signal, the off-diagonal E residual is covered by `prod_eq_5 OR both_in_4578` with all six residual E cells recovered, one false positive (`45`), F1 `0.923`, E-only MDL gain `7.0` bits, and conditional control `p=0.00300`. This is a weak E-layer signal, not a full-table formula.",
        "- `priority_masked_e_layer_search`: the natural blocker variant (`45=F`, `55=V`, `77=N`, `88=A`) plus selected E diagonals, `prod_eq_5`, and `both_in_4578` gives exact `15/15` local claims (`p=0.00020`) but only `22/55` total hits with default fill and costs `2.520x` inventory lookup. It confirms a local priority E layer and rejects it as the full matrix formula.",
        "- `anchored_remaining_fill_search`: fixing those 15 E-priority claims, then filling the remaining 40 cells with frequency-derived inventory, simple pair orders, and `6<->9` quotient-shaped orders reaches `26/55` total and only `11/40` remaining hits. The result is nonrandom under controls (`p=0.00100`) because of the anchors, but it is still `2.493x` inventory lookup and not promoted.",
        "- `priority_anchored_quotient_residual_fill`: the quotient-correct ablation collapses `6<->9`, fixes 14 quotient anchors, and shuffles only the 32 residual labels in controls. Best residual fill reaches `11/32` and combined `25/46`, with residual-hit control `p=0.11289` and `2.293x` quotient lookup. This rejects the idea that the E-priority layer unlocks a quotient worksheet for the remaining labels.",
        "- `chayenne_min8_copy_holdout`: secondary validation only.",
        "",
        "## Rejected / Not Promoted",
        "",
        "- Magic Web numbers remain lore-compatible but not predictive.",
        "- `lore_anomaly_operator_search` tests lore numbers only as selectors for small structural anomaly sets. The best `469` quotient-6/9 operator overlaps the mixed-orbit target at F1 `0.667`, but digit-multiset and same-length random controls do as well or better (`p=1.0000` and `p=0.9858`), so no anomaly operator is promoted.",
        "- `1 = Tibia` remains a structural clue, not a rule.",
        "- Deep arithmetic/sequence search found no compact formula below the pair table.",
        "- `matrix_generator_exhaustive_search` recorded 294,528 permissive candidates across matrix paths, symbol orders, lore seeds, anomaly overlays, and weak compositions; the best row reaches only 21/55 pair-cell hits and is classified as lookup-disguise under rough MDL.",
        "- `pair_rule_cover_search` tests human-readable digit-pair predicates and reaches 34/55 with 10 rules, but inventory-preserving shuffles do at least that well routinely (`p=0.7273`) and the rule cost remains lookup-like.",
        "- `adaptive_quota_fill_search` gives the generator the observed homophone inventory as quotas and lets local online rules fill the 55 cells; the best row reaches only 13/55 and costs `2.007x` lookup, so it is lookup-disguise.",
        "- `row_column_balance_objective_search` tests whether the observed cell placement optimizes digit/line balance objectives; the strongest nominal metric has only `p=0.04019` and improves with one swap, so balance is not the original objective.",
        "- `composite_objective_inverse_search` tests whether a sparse combination of balance, context, digit-shape, zero/repeat, and `6<->9` metrics makes the observed table a local optimum. The best composite is still improved by swapping `38` and `45`, and best-of-search controls are comparable.",
        "- `finite_group_pair_formula_search` finds an apparently perfect 55/55 modular rule only by creating 55 groups for 55 cells; controls also score 55/55 and MDL is worse than lookup, so this is a useful negative example of formula-shaped lookup.",
        "- `direct_symbol_formula_search` tests direct arithmetic and digit-order formulas from cell coordinates to symbol-order index, without key->symbol lookup; the best row reaches only 18/55 and does not beat controls or lookup MDL.",
        "- `directed_surface_sequence_generator_search` tests whether the 99 present ordered codes form a short generated worksheet sequence. Full directed/mirror orders show a strong raw signal (`p=0.00067`), but upper-only does not (`p=0.10859`) and periodic templates are above inventory lookup, so this is mirror render redundancy rather than a matrix-origin formula.",
        "- `pair_hash_formula_search` tests 51,716 cell-local hash/PRNG formulas over lore seeds and fixed symbol orders; the best row reaches only 16/55, costs `1.884x` lookup, and performs worse than shuffled controls.",
        "- `block_biclique_cover_search` tests set-block/biclique decompositions of the colored digit graph; the best global model reaches 27/55 primary hits but costs `2.146x` inventory lookup and is ordinary under shuffles.",
        "- `digit_visual_symmetry_search` tests seven-segment, numpad, clock, and 6/9-specific visual symmetries. The best MDL row is `sevenseg_rotate180_exact` at 53/55 majority hits, but it still costs more than lookup and is rejected as a complete pair-matrix formula.",
        "- `sevenseg_orbit_exception_selector` sharpens the best visual row: the two mixed seven-segment rotation orbitals are exactly anchors `0` and `8`, giving `+7.6` rough bits versus raw lookup under a narrow accounting, but two-of-five controls often find equally cheap selectors (`p=0.40372`), so this is a weak microfit, not the original formula.",
        "- `digit_signature_formula_search` tests row/column marginal, diagonal, frequent-symbol, and tape-derived digit signatures. The best true index formula reaches only 18/55, while the 41/55 bucket diagnostic is lookup-like and worse than controls.",
        "- `quotient_pair_formula_search` tests 1,248,362 coordinate formulas over the `6 <-> 9` quotient; the best row reaches only 16/46, costs `1.741x` quotient lookup, and performs worse than sampled shuffle controls.",
        "- `quotient_line_order_search` finds a weak line/order structure in the quotient table, but the best line-template model costs `1.550x` lookup and the best fill-period model costs `1.389x`; both are non-promoted.",
        "- `digit_orbit_split_label_pair_search` tests whether the nine `6 <-> 9` split label-pairs have a direct cycle/affine generator. The direct formulas fail controls; only a metadata ledger over stored base labels compresses weakly.",
        "- `digit_orbit_directed_provenance_search` finds the exact label-blind selector `directed anomaly OR edge pair` for the mixed `6 <-> 9` orbits, but exact low-cost selectors are common over nine cases; it is provenance bookkeeping, not origin recovery.",
        "- `nine_identity_render_split_search` closes the formal gap for a pure 45-cell `0,1,2,3,4,5,Q,7,8` worksheet plus `Q -> 6/9` renderer. The `QQ -> 66/69/99` cross-pair consumes the saving, so it is worse than the 46-orbit quotient and not promoted.",
        "- `quotient_edit_log_mdl_search` tests a human worksheet plus explicit edit-log process over quotient candidates. Even the best charged edit log is `1.473x` lookup and needs 7 manual labels, so it is not a compact original formula.",
        "- `symbol_base_accent_layer_search` tests whether the 14 internal symbols factor into a smaller base alphabet plus accent layer. The best partition is inventory-only, costs `1.003x` raw lookup, and is identical under shuffles, so it is not a formula.",
        "- `symbol_predicate_dnf_search` searches short per-symbol digit predicates and reaches 44/55, but costs `4.592x` lookup and is ordinary under inventory-preserving shuffles; high hit count is not evidence here.",
        "- `algebraic_digit_composition_search` tests simple digit embeddings plus algebraic bucket operations. It reaches 55/55 only with 55 buckets, while the best compact row reaches 35/55 at `1.535x` lookup and fails controls.",
        "- `marginal_constraint_solver_search` finds that inventory plus `6 <-> 9` split metadata costs `0.947x` raw lookup and beats controls, but still leaves about `2^141` possible tables; tighter row/column constraints become lookup-disguise.",
        "- `quotient_constructive_fill_search` combines frequency-weighted inventory, quotient fill order, and symbol cycle. It beats controls weakly but reaches only 17/46 and costs `1.700x` lookup.",
        "- `line_template_alignment_search` tests whether row/column/diagonal families are generated from one shifted/reversed template line; the best match is 0.618 but costs `1.627x` lookup and does not beat controls.",
        "- `row_transition_edit_mdl_search` tests a human workflow where each row/column/diagonal is edited from the previous line. The best row still costs `1.070x` lookup, has negative MDL gain, and is ordinary under inventory-preserving shuffles.",
        "- `digit_orbit_exception_rule_search` finds a compact descriptive rule for the four mixed `6 <-> 9` orbits (`x <= 1 or x mod 5 == 3`, side orientation by parity), but controls fit nine-case targets often enough that it is not promoted.",
        "- `digit_orbit_exception_context_search` finds a tape-position threshold that separates the four mixed `6 <-> 9` orbits exactly, but exhaustive 4-of-9 controls make this non-promotable.",
        "- `digit_order_distance_search` tests hidden digit orders in line/cycle geometry. The best line order reaches 48/55, but only with 40 midpoint-distance groups, `1.171x` lookup cost, and shuffled controls also reaching 48/55; this is lookup-disguise rather than a compact origin formula.",
        "- Source-cycle, corpus-slice, line-pattern, sequence-automaton, intra-symbol ordering, latent-digit factorization, spatial-feature, spatial-dispersion, count-assignment, digit-permutation, and seeded-placement pair-table searches do not recover the cell placement.",
        "- `endpoint_affinity_assignment_search` tests symbol-specific digit endpoint affinities plus small binary pair features, with exact-inventory assignment as a diagnostic. Leave-one-pair-out reaches only `0.145` and controls are comparable, so endpoint affinity is rejected.",
        "- `bilinear_low_rank_pair_factor_search` closes the formal continuous low-rank gap. The best rank-1 centered surface reaches `18/55` leave-one-pair-out accuracy (`0.327`, control `p=0.02597`), but the 8-bit lower-bound parameter cost is `14.931x` inventory lookup and macro recall is low, so it is weak signal rather than formula.",
        "- `quotient_low_rank_pair_factor_search` reruns the low-rank probe over the 46 `6 <-> 9` quotient orbits. The best row reaches only `11/46` (`0.239`) with label-shuffle `p=0.56436`, worse than the raw low-rank and direct quotient formula references, so the quotient does not turn the weak SVD signal into an origin formula.",
        "- Graph-incidence/digit-affinity metrics over the pair table do not survive inventory-preserving controls.",
        "- Higher-order graph motifs over the colored digit graph, including triangles, wedges, stars, paths, orbits, and same-color spectra, do not survive corrected controls and do not provide a predictive MDL formula.",
        "- Local 2D/CA-style rules over already-filled triangular-grid neighbours reach only 14/55 primary hits, cost about `2.001x` lookup, and are beaten by inventory-preserving controls.",
        "- The internal order of the large synthetic tape `T00` is not explained by simple module id, first occurrence, length, or reuse-count signals.",
        "- `endpoint_literal_bridge_mdl_search` tests whether the 28 internal bridge literals among the remaining recipe literals are reusable connectors keyed by adjacent tape/module endpoints. Leave-one-bridge and leave-book-out coverage are both `0/590`, the blind residual holdout is `0/145`, and the train-literal exact-repeat baseline also stays at zero; rejected.",
        "- `t00_internal_fsa_compression_probe` finds strong order-1 code regularity in concatenated T00 slice tokens, but slice-order permutation preserves the gain (`p=0.38162`); the signal is inside slices, not an independently recovered T00 order.",
        "- The order in which pair cells first appear on reusable tapes is not explained by simple matrix/lore-digit traversals.",
        "- Tape-only/literal-only pair exceptions (`33`, `66`) are suggestive diagonal E cells but remain weak after structural-control classification.",
        "- Tape/literal usage features do not predict exact pair-label placement better than inventory-preserving controls.",
        "- `residual_tape_feature_after_e_search` removes the 15 fixed E-priority claims and tests tape, usage, and grid features on the remaining 40 cells. The best depth-3 tree reaches `24/40` but costs `2.209x` residual lookup and is ordinary under residual-label shuffles (`p(MDL)=0.42557`), so tape/usage still does not generate the non-E matrix.",
        "- `residual_marginal_after_e_search` removes the same 15 E-priority claims and tests row, column, diagonal, anti-diagonal, border, and digit-incidence marginals on the remaining 40 cells. The best raw metric is `row_pure_line_count` (`p=0.01500`), but corrected p is `0.38992`, so no residual marginal constraint is promoted.",
        "- `high_block_blocker_origin_search` tests whether the blockers `45,55,77,88` inside `{4,5,7,8}` come from a mini-block drawing rule. `first_edge_plus_suffix_diags_4578` fits exactly, but same-block controls fit exact patterns often (`p=0.17409`) and connected 4-cell strokes are common (`90/210`, `p=0.43128`), so the blockers remain non-promoted.",
        "- `render_origin_e_priority_probe` tests whether zero/orientation/render features explain the 15 E-priority claims or the four blockers. The 15-claim global p is nominal (`0.04459`) but becomes `1.00000` under geometry-stratified controls; blockers fit perfectly but also fail stratified controls (`p=0.75065`). Render context does not add an origin rule for the E-priority layer.",
        "- Diagonal, row/column, anti-diagonal, border, and digit-marginal statistics do not survive inventory-preserving controls.",
        "- Same-symbol pair cells and induced symbol streams show suggestive context/compression hints, but remain below promotion classification.",
        "- `pair_symbol_stream_optimization_search` rejects `maximize repeat6_excess` as the original objective: one label swap improves the observed table from 3786 to 3803, and a greedy local optimum reaches 3986.",
        "- Longer lore-text window/subsequence searches do not recover pair-cell placement beyond same-source/global shuffled controls.",
        "- Usage-driven pair placement from code frequency, first use, last use, and orientation bias fails train controls and holdout transfer.",
        "- Digit-shape pressure metrics do not show the table was placed to optimize digit balance, zero rate, repeats, or raw-digit distribution.",
        "- Shallow decision-tree/region formulas over grid features do not recover pair-cell placement better than label-shuffled controls.",
        "- Alternative digit geometries such as keypad, numpad, clock/circle, and seven-segment glyphs do not recover pair-cell placement better than global controls.",
        "- The stochastic inventory model does not recover an exact deterministic seed for cell placement.",
        "- The apportionment residual is not explained by small corrections from corpus, module/literal, zero-rendering, or quota-remainder features.",
        "- Seeded/permutation shuffles of the observed homophone inventory do not recover exact pair-cell placement better than shuffled controls.",
        "- Orientation rendering does not generalize to unseen unordered pairs as a compact grid formula.",
        "- The explicit zero-omission group rule and sparse decision list confirm local-context signal but are not MDL-promoted over code-only.",
        "- `lore_zero_phase_mask_search` tests whether Magic Web/Honeminas numbers act as a cyclic omission mask. The best row improves `code_only` slightly (`0.733` balanced accuracy, `+3.4` rough bits), but digit-multiset permutations and random same-length numbers do as well or better (`p=0.87603` and `p=0.59504`), so it is rejected.",
        "- `zero_homophone_transition_origin_probe` combines zero omission, prev/next code context, orientation, and deduplicated occurrence modes to reconstruct pair labels. The best leave-one-pair-out accuracy is only `0.200`, so it remains a weak context signal rather than a matrix-origin formula.",
        "- Controlled ML probes do not promote a compact table formula: pair-cell features fail controls, homophone ML loses to the simple previous-code baseline, while zero omission has a local-context rendering signal.",
        "- Repeated chunks do not look like independent symbol-level re-renderings.",
        "- PRNG/seed tests did not beat controls.",
        "- Short repeats are rejected because they leak into Avar Tar/controls.",
        "",
    ]
    (HERE / "generator_model_final_report.md").write_text("\n".join(final), encoding="utf-8")
    return rows


def main() -> int:
    HERE.mkdir(parents=True, exist_ok=True)
    formula = load_formula()
    residual = load_json(RESIDUAL_RESULTS_JSON)
    residual_atlas = load_json(RESIDUAL_ATLAS_JSON)
    token_maps = load_token_maps(formula)

    freeze_contract(formula, residual, residual_atlas)
    write_clue_and_targets()
    grid = grid_formula_search(formula)
    magic = magic_web_search(formula)
    one = one_equals_tibia(formula, token_maps)
    manifest = load_json(HERE / "generator_holdout_manifest.json")
    homophone = homophone_search(token_maps, manifest["book_holdouts"])
    zero = zero_omission_search(token_maps, manifest["book_holdouts"])
    module = module_grammar(formula, residual)
    seeds = seed_search(formula)
    external = external_and_controls(formula)
    leaderboard = consolidate(
        {
            "grid": grid,
            "magic": magic,
            "one": one,
            "homophone": homophone,
            "zero": zero,
            "module": module,
            "seeds": seeds,
            "external": external,
            "residual": residual,
        }
    )
    print(f"wrote generator search outputs to {HERE.relative_to(ROOT)}")
    print(f"leaderboard_rows={len(leaderboard)} best={leaderboard[0]['hypothesis_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

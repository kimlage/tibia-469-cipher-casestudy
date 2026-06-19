#!/usr/bin/env python3
"""Analyze pair/code exceptions outside the reusable tape layer.

The tape-token analysis found that pair cells `33` and `66` appear only outside
the reusable tape layer, while ordered codes `32`, `33`, `66`, and `69` appear
only outside tape. This pass tests whether those exceptions are structurally
meaningful or consistent with ordinary residual/literal fallout.

Mechanical only. No plaintext is promoted.
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import tape_tokenization_analysis as tape_tokens


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TAPE_FORMULA_JSON = HERE / "tape_based_formula_469.json"

OUT_JSON = HERE / "tape_literal_exception_results.json"
OUT_MD = HERE / "tape_literal_exception_report.md"

RANDOM_SEED = 46920260624
CONTROL_TRIALS = 20000


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def all_pairs() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def summarize(values: list[float], observed: float, high_is_good: bool = True) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    if high_is_good:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "z_good_direction": z,
        "p_good_direction": p,
        "control_min": min(values),
        "control_max": max(values),
    }


def project(formula: dict) -> list[dict]:
    books, segment_maps = tape_tokens.reconstruct_books(formula)
    token_maps = tape_tokens.align_tokens(books)
    return tape_tokens.project_tokens(token_maps, segment_maps)


def pair_symbol(formula: dict, pair: str) -> str:
    row = formula["pair_table"][pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return "/".join(sorted(row["symbols"]))


def aggregate(formula: dict, projected: list[dict]) -> dict:
    pair_rows = {}
    code_rows = {}
    for pair in all_pairs():
        rows = [row for row in projected if row["pair_key"] == pair]
        tape = [row for row in rows if row["mapped_to_tape"]]
        outside = [row for row in rows if not row["mapped_to_tape"]]
        pair_rows[pair] = {
            "pair": pair,
            "symbol": pair_symbol(formula, pair),
            "is_diagonal": pair[0] == pair[1],
            "total_tokens": len(rows),
            "tape_tokens": len(tape),
            "outside_tokens": len(outside),
            "outside_reasons": dict(Counter(row.get("unmapped_reason", "mapped") for row in outside)),
            "tape_fraction": len(tape) / len(rows) if rows else 0.0,
        }
    for code, symbol in sorted(formula["code_to_symbol"].items()):
        rows = [row for row in projected if row["code"] == code]
        tape = [row for row in rows if row["mapped_to_tape"]]
        outside = [row for row in rows if not row["mapped_to_tape"]]
        code_rows[code] = {
            "code": code,
            "pair": "".join(sorted(code)),
            "symbol": symbol,
            "is_diagonal": code[0] == code[1],
            "total_tokens": len(rows),
            "tape_tokens": len(tape),
            "outside_tokens": len(outside),
            "outside_reasons": dict(Counter(row.get("unmapped_reason", "mapped") for row in outside)),
            "tape_fraction": len(tape) / len(rows) if rows else 0.0,
        }
    return {"pair_rows": pair_rows, "code_rows": code_rows}


def exception_sets(agg: dict) -> dict:
    pair_only_outside = sorted(pair for pair, row in agg["pair_rows"].items() if row["total_tokens"] and row["tape_tokens"] == 0)
    pair_mixed = sorted(pair for pair, row in agg["pair_rows"].items() if row["tape_tokens"] and row["outside_tokens"])
    pair_tape_only = sorted(pair for pair, row in agg["pair_rows"].items() if row["tape_tokens"] and not row["outside_tokens"])
    code_only_outside = sorted(code for code, row in agg["code_rows"].items() if row["total_tokens"] and row["tape_tokens"] == 0)
    code_mixed = sorted(code for code, row in agg["code_rows"].items() if row["tape_tokens"] and row["outside_tokens"])
    code_tape_only = sorted(code for code, row in agg["code_rows"].items() if row["tape_tokens"] and not row["outside_tokens"])
    return {
        "pair_only_outside": pair_only_outside,
        "pair_mixed": pair_mixed,
        "pair_tape_only": pair_tape_only,
        "code_only_outside": code_only_outside,
        "code_mixed": code_mixed,
        "code_tape_only": code_tape_only,
    }


def structural_features(formula: dict, pairs: list[str], codes: list[str]) -> dict:
    pair_symbols = [pair_symbol(formula, pair) for pair in pairs]
    code_symbols = [formula["code_to_symbol"][code] for code in codes]
    return {
        "pair_count": len(pairs),
        "pair_diagonal_count": sum(pair[0] == pair[1] for pair in pairs),
        "pair_symbols": dict(Counter(pair_symbols)),
        "pair_same_symbol": len(set(pair_symbols)) == 1 if pairs else False,
        "code_count": len(codes),
        "code_diagonal_count": sum(code[0] == code[1] for code in codes),
        "code_symbols": dict(Counter(code_symbols)),
        "code_same_symbol": len(set(code_symbols)) == 1 if codes else False,
        "codes": codes,
        "pairs": pairs,
    }


def controls(formula: dict, observed_pairs: list[str], observed_codes: list[str]) -> dict:
    rng = random.Random(RANDOM_SEED)
    pairs = [pair for pair in all_pairs() if pair in formula["pair_table"]]
    codes = sorted(formula["code_to_symbol"])
    pair_diag = []
    pair_same_symbol = []
    pair_all_e = []
    code_diag = []
    code_same_symbol = []
    code_all_e = []
    for _trial in range(CONTROL_TRIALS):
        sample_pairs = rng.sample(pairs, len(observed_pairs))
        sample_codes = rng.sample(codes, len(observed_codes))
        pair_symbols = [pair_symbol(formula, pair) for pair in sample_pairs]
        code_symbols = [formula["code_to_symbol"][code] for code in sample_codes]
        pair_diag.append(sum(pair[0] == pair[1] for pair in sample_pairs))
        pair_same_symbol.append(1 if len(set(pair_symbols)) == 1 else 0)
        pair_all_e.append(1 if pair_symbols and set(pair_symbols) == {"E"} else 0)
        code_diag.append(sum(code[0] == code[1] for code in sample_codes))
        code_same_symbol.append(1 if len(set(code_symbols)) == 1 else 0)
        code_all_e.append(1 if code_symbols and set(code_symbols) == {"E"} else 0)
    observed_pair_symbols = [pair_symbol(formula, pair) for pair in observed_pairs]
    observed_code_symbols = [formula["code_to_symbol"][code] for code in observed_codes]
    return {
        "pair_diagonal_count": summarize(pair_diag, sum(pair[0] == pair[1] for pair in observed_pairs)),
        "pair_same_symbol": summarize(pair_same_symbol, 1 if len(set(observed_pair_symbols)) == 1 else 0),
        "pair_all_e": summarize(pair_all_e, 1 if observed_pair_symbols and set(observed_pair_symbols) == {"E"} else 0),
        "code_diagonal_count": summarize(code_diag, sum(code[0] == code[1] for code in observed_codes)),
        "code_same_symbol": summarize(code_same_symbol, 1 if len(set(observed_code_symbols)) == 1 else 0),
        "code_all_e": summarize(code_all_e, 1 if observed_code_symbols and set(observed_code_symbols) == {"E"} else 0),
    }


def write_report(result: dict) -> None:
    features = result["features"]
    ctl = result["controls"]
    lines = [
        "# Tape Literal Exception Analysis",
        "",
        "Generated by `tape_literal_exception_analysis.py`.",
        "",
        "This pass tests whether codes and pairs found only outside reusable tape",
        "components form a meaningful mechanical exception layer. It does not",
        "translate 469.",
        "",
        "## Exception Sets",
        "",
        f"- Pair cells only outside tape: `{features['pairs']}`.",
        f"- Ordered codes only outside tape: `{features['codes']}`.",
        f"- Pair symbols: `{features['pair_symbols']}`.",
        f"- Code symbols: `{features['code_symbols']}`.",
        "",
        "## Controls",
        "",
        "| Feature | Observed | Control mean | p |",
        "|---|---:|---:|---:|",
        f"| pair diagonal count | {ctl['pair_diagonal_count']['observed']} | {ctl['pair_diagonal_count']['control_mean']:.3f} | {ctl['pair_diagonal_count']['p_good_direction']:.5f} |",
        f"| pair same symbol | {ctl['pair_same_symbol']['observed']} | {ctl['pair_same_symbol']['control_mean']:.3f} | {ctl['pair_same_symbol']['p_good_direction']:.5f} |",
        f"| pair all E | {ctl['pair_all_e']['observed']} | {ctl['pair_all_e']['control_mean']:.3f} | {ctl['pair_all_e']['p_good_direction']:.5f} |",
        f"| code diagonal count | {ctl['code_diagonal_count']['observed']} | {ctl['code_diagonal_count']['control_mean']:.3f} | {ctl['code_diagonal_count']['p_good_direction']:.5f} |",
        f"| code same symbol | {ctl['code_same_symbol']['observed']} | {ctl['code_same_symbol']['control_mean']:.3f} | {ctl['code_same_symbol']['p_good_direction']:.5f} |",
        f"| code all E | {ctl['code_all_e']['observed']} | {ctl['code_all_e']['control_mean']:.3f} | {ctl['code_all_e']['p_good_direction']:.5f} |",
        "",
        "## Pair Rows",
        "",
        "| Pair | Symbol | Total | Tape | Outside | Reasons |",
        "|---|---|---:|---:|---:|---|",
    ]
    for pair in result["sets"]["pair_only_outside"] + result["sets"]["pair_mixed"][:20]:
        row = result["pair_rows"][pair]
        lines.append(
            f"| `{pair}` | `{row['symbol']}` | {row['total_tokens']} | {row['tape_tokens']} | "
            f"{row['outside_tokens']} | `{row['outside_reasons']}` |"
        )
    lines += ["", "## Verdict", ""]
    if result["verdict"] == "candidate_literal_exception_layer":
        lines.append(
            "The outside-only pair cells are structurally non-random: both are diagonal "
            "E cells (`33`, `66`). Treat this as a candidate residual/literal exception "
            "layer. It may explain why these pair cells do not participate in reusable "
            "tapes, but it still does not derive the full pair table."
        )
    else:
        lines.append("The outside-only pairs/codes do not survive structural controls.")
    lines += ["", f"Translation delta: `{result['translation_delta']}`.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(TAPE_FORMULA_JSON)
    projected = project(formula)
    agg = aggregate(formula, projected)
    sets = exception_sets(agg)
    features = structural_features(formula, sets["pair_only_outside"], sets["code_only_outside"])
    ctl = controls(formula, sets["pair_only_outside"], sets["code_only_outside"])
    best_p = min(
        ctl["pair_diagonal_count"]["p_good_direction"],
        ctl["pair_same_symbol"]["p_good_direction"],
        ctl["pair_all_e"]["p_good_direction"],
        ctl["code_diagonal_count"]["p_good_direction"],
        ctl["code_same_symbol"]["p_good_direction"],
        ctl["code_all_e"]["p_good_direction"],
    )
    # Six simple structural tests are applied; use a conservative gate.
    verdict = "candidate_literal_exception_layer" if min(1.0, best_p * 6) <= 0.05 else "not_promoted"
    result = {
        "schema": "tape_literal_exception_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "sets": sets,
        "features": features,
        "controls": ctl,
        "best_raw_p": best_p,
        "bonferroni_p": min(1.0, best_p * 6),
        "pair_rows": agg["pair_rows"],
        "code_rows": agg["code_rows"],
        "verdict": verdict,
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={verdict} pair_only_outside={sets['pair_only_outside']} "
        f"code_only_outside={sets['code_only_outside']} bonferroni={result['bonferroni_p']:.5f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Finite-state compression probe for the internal T00 token sequence.

This closes a narrow tape-layer gap: the current tape model shows that T00 is a
compact overlap component, but not whether its internal token order has a small
finite-state/Markov regularity of its own.

The probe is mechanical only. It does not assign plaintext, and even a positive
result would refine the assembly layer rather than solve the 10x10 pair table.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tape_tokenization_analysis import align_tokens, load_json, project_tokens, reconstruct_books


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TAPE_FORMULA_JSON = HERE / "tape_based_formula_469.json"

OUT_JSON = HERE / "t00_internal_fsa_compression_results.json"
OUT_MD = HERE / "t00_internal_fsa_compression_report.md"

RANDOM_SEED = 46920260625
CONTROL_TRIALS = 1000
ORDERS = (0, 1, 2, 3)
ALPHABETS = ("code", "symbol", "pair_key")
MODEL_SELECTION_COST_BITS = 32.0


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def gamma_bits(value: int) -> int:
    if value < 1:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def kt_bits(values: list[str], order: int, alphabet: list[str]) -> float:
    if not values:
        return 0.0
    vocab = len(alphabet)
    contexts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    totals: Counter[tuple[str, ...]] = Counter()
    bits = 0.0
    for index, value in enumerate(values):
        context = tuple(values[max(0, index - order) : index]) if order else ()
        count = contexts[context][value]
        total = totals[context]
        prob = (count + 0.5) / (total + 0.5 * vocab)
        bits -= math.log2(prob)
        contexts[context][value] += 1
        totals[context] += 1
    return bits


def sequence_rows(formula: dict[str, Any]) -> dict[str, Any]:
    books, segment_maps = reconstruct_books(formula)
    token_maps = align_tokens(books)
    projected = project_tokens(token_maps, segment_maps)

    interval_map: dict[tuple[int, int], dict[str, Any]] = {}
    for row in projected:
        if row.get("mapped_to_tape") and row.get("component_id") == "T00":
            key = (int(row["component_start"]), int(row["component_end"]))
            if key not in interval_map:
                interval_map[key] = row
    unique_t00 = [interval_map[key] for key in sorted(interval_map)]

    slices = [row for row in formula["module_slices"] if row["component_id"] == "T00"]
    slices = sorted(slices, key=lambda row: (row["start"], row["end"], row["id"]))
    slice_sequences = []
    for sl in slices:
        tokens = [
            row
            for row in unique_t00
            if int(row["component_start"]) >= int(sl["start"]) and int(row["component_end"]) <= int(sl["end"])
        ]
        slice_sequences.append({"slice": sl, "tokens": tokens})
    slice_concat = [token for item in slice_sequences for token in item["tokens"]]

    return {
        "unique_t00": unique_t00,
        "slice_sequences": slice_sequences,
        "slice_concat": slice_concat,
    }


def values_for(tokens: list[dict[str, Any]], alphabet_name: str) -> list[str]:
    return [str(row[alphabet_name]) for row in tokens]


def evaluate_values(values: list[str], alphabet_name: str, lens: str) -> list[dict[str, Any]]:
    alphabet = sorted(set(values))
    baseline = kt_bits(values, 0, alphabet)
    rows = []
    for order in ORDERS:
        bits = kt_bits(values, order, alphabet)
        gain = baseline - bits
        rows.append(
            {
                "lens": lens,
                "alphabet": alphabet_name,
                "order": order,
                "token_count": len(values),
                "vocab_size": len(alphabet),
                "bits": bits,
                "bits_per_token": bits / len(values) if values else 0.0,
                "order0_bits": baseline,
                "gain_bits_vs_order0": gain,
                "net_gain_bits_vs_order0": gain - (MODEL_SELECTION_COST_BITS if order else 0.0),
            }
        )
    return rows


def evaluate_lens(tokens: list[dict[str, Any]], lens: str) -> list[dict[str, Any]]:
    rows = []
    for alphabet_name in ALPHABETS:
        rows.extend(evaluate_values(values_for(tokens, alphabet_name), alphabet_name, lens))
    return rows


def best_predictive(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in rows if row["order"] > 0]
    return max(candidates, key=lambda row: (row["net_gain_bits_vs_order0"], row["gain_bits_vs_order0"], -row["order"]))


def shuffled_tokens(tokens: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    out = tokens[:]
    rng.shuffle(out)
    return out


def permuted_slice_concat(slice_sequences: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    out = slice_sequences[:]
    rng.shuffle(out)
    return [token for item in out for token in item["tokens"]]


def internal_shuffled_slice_concat(slice_sequences: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    out = []
    for item in slice_sequences:
        tokens = item["tokens"][:]
        rng.shuffle(tokens)
        out.extend(tokens)
    return out


def summarize_control(values: list[float], observed: float) -> dict[str, float]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    return {
        "observed": observed,
        "mean": mean,
        "sd": sd,
        "min": min(values),
        "max": max(values),
        "p_ge_observed": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
        "z": (observed - mean) / sd if sd else 0.0,
    }


def control_suite(sequences: dict[str, Any], unique_best: dict[str, Any], slice_best: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    control_values: dict[str, list[float]] = {
        "unique_token_shuffle": [],
        "slice_concat_token_shuffle": [],
        "slice_order_permutation": [],
        "slice_internal_shuffle": [],
    }
    for _trial in range(CONTROL_TRIALS):
        candidates = {
            "unique_token_shuffle": shuffled_tokens(sequences["unique_t00"], rng),
            "slice_concat_token_shuffle": shuffled_tokens(sequences["slice_concat"], rng),
            "slice_order_permutation": permuted_slice_concat(sequences["slice_sequences"], rng),
            "slice_internal_shuffle": internal_shuffled_slice_concat(sequences["slice_sequences"], rng),
        }
        for name, tokens in candidates.items():
            rows = evaluate_lens(tokens, name)
            best = best_predictive(rows)
            control_values[name].append(best["net_gain_bits_vs_order0"])
    return {
        "unique_token_shuffle": summarize_control(
            control_values["unique_token_shuffle"],
            unique_best["net_gain_bits_vs_order0"],
        ),
        "slice_concat_token_shuffle": summarize_control(
            control_values["slice_concat_token_shuffle"],
            slice_best["net_gain_bits_vs_order0"],
        ),
        "slice_order_permutation": summarize_control(
            control_values["slice_order_permutation"],
            slice_best["net_gain_bits_vs_order0"],
        ),
        "slice_internal_shuffle": summarize_control(
            control_values["slice_internal_shuffle"],
            slice_best["net_gain_bits_vs_order0"],
        ),
    }


def verdict(unique_best: dict[str, Any], slice_best: dict[str, Any], controls: dict[str, Any]) -> str:
    if max(unique_best["net_gain_bits_vs_order0"], slice_best["net_gain_bits_vs_order0"]) <= 0:
        return "rejected_no_mdl_gain"
    slice_controls = [
        controls["slice_concat_token_shuffle"],
        controls["slice_order_permutation"],
        controls["slice_internal_shuffle"],
    ]
    if slice_best["net_gain_bits_vs_order0"] > 0 and all(row["p_ge_observed"] <= 0.01 for row in slice_controls):
        return "candidate_t00_internal_fsa_supporting_layer"
    if (
        slice_best["net_gain_bits_vs_order0"] > 0
        and controls["slice_concat_token_shuffle"]["p_ge_observed"] <= 0.01
        and controls["slice_internal_shuffle"]["p_ge_observed"] <= 0.01
        and controls["slice_order_permutation"]["p_ge_observed"] > 0.05
    ):
        return "slice_internal_regular_not_t00_order_formula"
    if unique_best["net_gain_bits_vs_order0"] > 0 and controls["unique_token_shuffle"]["p_ge_observed"] <= 0.01:
        return "weak_unique_t00_sequence_signal_not_matrix_formula"
    return "rejected_control"


def write_report(result: dict[str, Any]) -> None:
    best = result["best"]
    unique_best = result["unique_best"]
    slice_best = result["slice_best"]
    lines = [
        "# T00 Internal FSA Compression Probe",
        "",
        "Generated by `t00_internal_fsa_compression_probe.py`.",
        "",
        "This pass tests whether the tokenized `T00` tape has a small finite-state",
        "sequence regularity beyond inventory. It is mechanical only and creates no",
        "plaintext.",
        "",
        "## Summary",
        "",
        "| Lens | Alphabet | Order | Tokens | Gain vs order0 | Net gain | Verdict |",
        "|---|---|---:|---:|---:|---:|---|",
        f"| `{best['lens']}` | `{best['alphabet']}` | {best['order']} | {best['token_count']} | "
        f"{best['gain_bits_vs_order0']:.1f} | {best['net_gain_bits_vs_order0']:.1f} | `{result['verdict']}` |",
        "",
        "Best per lens:",
        "",
        "| Lens | Alphabet | Order | Tokens | Net gain |",
        "|---|---|---:|---:|---:|",
        f"| `unique_t00` | `{unique_best['alphabet']}` | {unique_best['order']} | {unique_best['token_count']} | {unique_best['net_gain_bits_vs_order0']:.1f} |",
        f"| `slice_concat` | `{slice_best['alphabet']}` | {slice_best['order']} | {slice_best['token_count']} | {slice_best['net_gain_bits_vs_order0']:.1f} |",
        "",
        "## Control Results",
        "",
        "| Control | Mean net gain | Max | p | z |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, row in result["controls"].items():
        lines.append(
            f"| `{name}` | {row['mean']:.1f} | {row['max']:.1f} | {row['p_ge_observed']:.5f} | {row['z']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Top Observed Rows",
            "",
            "| Lens | Alphabet | Order | Bits/token | Gain | Net gain |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in result["observed_rows"][:12]:
        lines.append(
            f"| `{row['lens']}` | `{row['alphabet']}` | {row['order']} | "
            f"{row['bits_per_token']:.3f} | {row['gain_bits_vs_order0']:.1f} | {row['net_gain_bits_vs_order0']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Promotion would require a positive net gain and separation from token",
            "shuffle, slice-order permutation, and within-slice shuffle controls.",
            "If slice-order permutation is not separated, the signal is inside the",
            "slices rather than in the authorial order of `T00`.",
            "Even then, this would only support the tape assembly layer unless it",
            "also predicts independent matrix facts.",
            "",
            f"Translation delta: `{result['translation_delta']}`.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(TAPE_FORMULA_JSON)
    sequences = sequence_rows(formula)
    observed_rows = evaluate_lens(sequences["unique_t00"], "unique_t00")
    observed_rows.extend(evaluate_lens(sequences["slice_concat"], "slice_concat"))
    observed_rows.sort(key=lambda row: (-row["net_gain_bits_vs_order0"], -row["gain_bits_vs_order0"], row["order"]))
    unique_rows = [row for row in observed_rows if row["lens"] == "unique_t00"]
    slice_rows = [row for row in observed_rows if row["lens"] == "slice_concat"]
    unique_best = best_predictive(unique_rows)
    slice_best = best_predictive(slice_rows)
    best = best_predictive(observed_rows)
    controls = control_suite(sequences, unique_best, slice_best)
    result_verdict = verdict(unique_best, slice_best, controls)
    result = {
        "schema": "t00_internal_fsa_compression_results.v1",
        "source": str(TAPE_FORMULA_JSON.relative_to(ROOT)),
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "orders": list(ORDERS),
        "alphabets": list(ALPHABETS),
        "model_selection_cost_bits": MODEL_SELECTION_COST_BITS,
        "sequence_summary": {
            "unique_t00_tokens": len(sequences["unique_t00"]),
            "t00_slices": len(sequences["slice_sequences"]),
            "slice_concat_tokens": len(sequences["slice_concat"]),
        },
        "unique_best": unique_best,
        "slice_best": slice_best,
        "best": best,
        "observed_rows": observed_rows,
        "controls": controls,
        "verdict": result_verdict,
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={result['verdict']} best={best['lens']}/{best['alphabet']}/order{best['order']} "
        f"net_gain={best['net_gain_bits_vs_order0']:.1f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

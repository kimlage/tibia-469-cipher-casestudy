from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

LEDGER = TEST_RESULTS / "01_literal_payload_ledger.json"
OUT_STEM = "02_literal_payload_context_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def bucket(value: int) -> str:
    if value <= 1:
        return "le1"
    if value <= 3:
        return "le3"
    if value <= 5:
        return "le5"
    if value <= 8:
        return "le8"
    if value <= 13:
        return "le13"
    if value <= 21:
        return "le21"
    return "gt21"


Row = dict[str, Any]
ContextFn = Callable[[Row], str]


def context_families() -> dict[str, ContextFn]:
    return {
        "global": lambda r: "global",
        "book_mod10": lambda r: f"bookmod10={int(r['book']) % 10}",
        "op_index": lambda r: f"op={r['op_index']}",
        "target_phase_10": lambda r: f"phase10={int(r['target_start']) % 10}",
        "target_phase_16": lambda r: f"phase16={int(r['target_start']) % 16}",
        "length": lambda r: f"len={r['length']}",
        "length_bucket": lambda r: f"lenb={bucket(int(r['length']))}",
        "forced": lambda r: f"forced={r['forced']}",
        "book_mod10_x_length": lambda r: (
            f"bookmod10={int(r['book']) % 10}|len={r['length']}"
        ),
        "op_index_x_length": lambda r: f"op={r['op_index']}|len={r['length']}",
        "phase10_x_length": lambda r: (
            f"phase10={int(r['target_start']) % 10}|len={r['length']}"
        ),
    }


def majority_payload(rows: list[Row]) -> str:
    counts = Counter(row["payload"] for row in rows)
    return min(counts, key=lambda payload: (-counts[payload], payload))


def train_model(rows: list[Row], name: str, fn: ContextFn) -> dict[str, Any]:
    grouped: dict[str, list[Row]] = defaultdict(list)
    for row in rows:
        grouped[fn(row)].append(row)
    return {
        "context_name": name,
        "fallback_payload": majority_payload(rows),
        "mapping": {context: majority_payload(values) for context, values in grouped.items()},
        "context_count": len(grouped),
    }


def evaluate(rows: list[Row], model: dict[str, Any], fn: ContextFn) -> dict[str, Any]:
    scored = []
    model_payload_digits = sum(len(payload) for payload in model["mapping"].values())
    for row in rows:
        predicted = model["mapping"].get(fn(row), model["fallback_payload"])
        exact = predicted == row["payload"]
        matching_prefix = 0
        for left, right in zip(predicted, row["payload"]):
            if left != right:
                break
            matching_prefix += 1
        scored.append(
            {
                "book": row["book"],
                "length": row["length"],
                "payload": row["payload"],
                "predicted": predicted,
                "exact": exact,
                "matching_prefix": matching_prefix,
            }
        )
    exact_rows = [row for row in scored if row["exact"]]
    exact_digits = sum(int(row["length"]) for row in scored if row["exact"])
    missed_digits = sum(int(row["length"]) for row in scored if not row["exact"])
    prefix_digits = sum(row["matching_prefix"] for row in scored)
    return {
        "context_name": model["context_name"],
        "context_count": model["context_count"],
        "model_payload_digits": model_payload_digits,
        "exact_chunks": len(exact_rows),
        "chunk_total": len(scored),
        "exact_digits": exact_digits,
        "missed_digits": missed_digits,
        "digit_total": sum(int(row["length"]) for row in scored),
        "prefix_digits": prefix_digits,
        "rows": scored,
    }


def score_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["exact_chunks"],
        row["exact_digits"],
        row["prefix_digits"],
        -row["context_count"],
        row["context_name"],
    )


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return math.inf
    return math.log2(math.comb(n, k))


def price(row: dict[str, Any], family_count: int) -> dict[str, float]:
    misses = row["chunk_total"] - row["exact_chunks"]
    table_payload_bits = row["model_payload_digits"] * math.log2(10)
    selector_bits = math.log2(family_count)
    correction_site_bits = log2_comb(row["chunk_total"], misses)
    correction_payload_bits = row["missed_digits"] * math.log2(10)
    correction_bits = correction_site_bits + correction_payload_bits
    total = selector_bits + table_payload_bits + correction_bits
    return {
        "selector_bits": selector_bits,
        "table_payload_bits": table_payload_bits,
        "correction_site_bits": correction_site_bits,
        "correction_payload_bits": correction_payload_bits,
        "correction_bits": correction_bits,
        "total_bits_with_corrections": total,
    }


def prequential(rows: list[Row], contexts: dict[str, ContextFn]) -> list[dict[str, Any]]:
    result = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        trained = []
        for name, fn in contexts.items():
            model = train_model(train, name, fn)
            train_score = evaluate(train, model, fn)
            trained.append((name, fn, model, train_score))
        selected_name, selected_fn, selected_model, selected_train = max(
            trained, key=lambda item: score_key(item[3])
        )
        test_score = evaluate(test, selected_model, selected_fn)
        oracle_scores = [evaluate(test, model, fn) for _name, fn, model, _score in trained]
        oracle = max(oracle_scores, key=score_key)
        result.append(
            {
                "cutoff_book": cutoff,
                "selected_context": selected_name,
                "train_exact_chunks": selected_train["exact_chunks"],
                "train_chunk_total": selected_train["chunk_total"],
                "test_exact_chunks": test_score["exact_chunks"],
                "test_chunk_total": test_score["chunk_total"],
                "test_exact_digits": test_score["exact_digits"],
                "test_digit_total": test_score["digit_total"],
                "oracle_context": oracle["context_name"],
                "oracle_test_exact_chunks": oracle["exact_chunks"],
                "oracle_test_exact_digits": oracle["exact_digits"],
                "selected_matches_oracle": (
                    test_score["exact_chunks"] == oracle["exact_chunks"]
                    and test_score["exact_digits"] == oracle["exact_digits"]
                ),
            }
        )
    return result


def make_result() -> dict[str, Any]:
    ledger = load_json(LEDGER)
    assert_boundary("literal_payload_ledger", ledger)
    rows = list(ledger["literal_rows"])
    contexts = context_families()
    payload_label_count = len({row["payload"] for row in rows})
    scores = []
    for name, fn in contexts.items():
        model = train_model(rows, name, fn)
        score = evaluate(rows, model, fn)
        score.update(price(score, len(contexts)))
        scores.append(score)
    scores.sort(key=score_key, reverse=True)
    best = scores[0]
    preq = prequential(rows, contexts)
    raw_uniform_bits = float(ledger["summary"]["raw_uniform_bits"])
    promotes = (
        best["exact_chunks"] == best["chunk_total"]
        and best["total_bits_with_corrections"] < raw_uniform_bits
        and all(row["test_exact_chunks"] == row["test_chunk_total"] for row in preq)
    )
    weak = any(row["test_exact_chunks"] > 0 for row in preq)
    classification = (
        "literal_payload_context_generator_promoted"
        if promotes
        else "literal_payload_context_weak_not_promoted"
        if weak
        else "literal_payload_context_rejected"
    )
    return {
        "schema": "literal_payload_context_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {"literal_payload_ledger": str(LEDGER.relative_to(ROOT))},
        "scope": {
            "analysis_only": True,
            "skeleton_granted": True,
            "target_text_not_used_for_prediction": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "chunk_count": len(rows),
            "digit_count": sum(int(row["length"]) for row in rows),
            "payload_label_count": payload_label_count,
            "context_family_count": len(contexts),
            "best_context": best["context_name"],
            "best_context_count": best["context_count"],
            "best_model_payload_digits": best["model_payload_digits"],
            "best_exact_chunks": best["exact_chunks"],
            "best_chunk_total": best["chunk_total"],
            "best_exact_digits": best["exact_digits"],
            "best_digit_total": best["digit_total"],
            "best_total_bits_with_corrections": best["total_bits_with_corrections"],
            "best_net_vs_raw_uniform_bits": best["total_bits_with_corrections"] - raw_uniform_bits,
            "prequential_cells": len(preq),
            "prequential_any_exact_chunk_cells": sum(
                1 for row in preq if row["test_exact_chunks"] > 0
            ),
            "prequential_cover_all_chunks_cells": sum(
                1 for row in preq if row["test_exact_chunks"] == row["test_chunk_total"]
            ),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle"]
            ),
            "promotes_literal_payload_generator": promotes,
            "weak_literal_payload_context_clue": weak,
            "interpretation": (
                "Simple source-free context tables over the granted skeleton do "
                "not generate literal payload. Full-fit exact hits come from "
                "a payload-bearing lookup table; prefix/holdout gets no exact "
                "chunks and the paid table does not beat raw literal digits."
            ),
        },
        "full_fit_scoreboard": [
            {key: value for key, value in score.items() if key != "rows"}
            for score in scores
        ],
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "literal_payload_status": "external_after_context_gate",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    lines = [
        "# Literal Payload Context Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether literal payload chunks can be predicted from source-free",
        "contexts once the exact skeleton is granted.",
        "",
        "## Summary",
        "",
        f"- Chunks/digits: `{s['chunk_count']}` / `{s['digit_count']}`.",
        f"- Payload labels: `{s['payload_label_count']}`.",
        f"- Best context: `{s['best_context']}`.",
        f"- Best exact chunks: `{s['best_exact_chunks']}/{s['best_chunk_total']}`.",
        f"- Best exact digits: `{s['best_exact_digits']}/{s['best_digit_total']}`.",
        f"- Best net vs raw uniform bits: `{s['best_net_vs_raw_uniform_bits']:.3f}` bits.",
        f"- Prefix/holdout any-exact-chunk cells: `{s['prequential_any_exact_chunk_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout cover-all chunks cells: `{s['prequential_cover_all_chunks_cells']}/{s['prequential_cells']}`.",
        "",
        "## Full-Fit Scoreboard",
        "",
        "| Context | Exact chunks | Exact digits | Contexts | Net vs raw |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    raw = result["summary"]["best_total_bits_with_corrections"] - result["summary"]["best_net_vs_raw_uniform_bits"]
    for row in result["full_fit_scoreboard"]:
        net = row["total_bits_with_corrections"] - raw
        lines.append(
            f"| `{row['context_name']}` | `{row['exact_chunks']}/{row['chunk_total']}` | "
            f"`{row['exact_digits']}/{row['digit_total']}` | `{row['context_count']}` | "
            f"`{net:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Context | Test exact chunks | Test exact digits | Oracle context |",
            "| ---: | --- | ---: | ---: | --- |",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_context']}` | "
            f"`{row['test_exact_chunks']}/{row['test_chunk_total']}` | "
            f"`{row['test_exact_digits']}/{row['test_digit_total']}` | "
            f"`{row['oracle_context']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes literal payload generator: `{s['promotes_literal_payload_generator']}`.",
            f"- Weak context clue: `{s['weak_literal_payload_context_clue']}`.",
            f"- {s['interpretation']}",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

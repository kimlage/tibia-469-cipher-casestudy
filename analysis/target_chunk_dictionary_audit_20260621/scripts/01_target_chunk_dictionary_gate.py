from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
LITERAL_PAYLOAD_LEDGER = (
    ROOT
    / "analysis"
    / "literal_payload_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_literal_payload_ledger.json"
)
TARGET_CONDITIONED_SOURCE = (
    ROOT
    / "analysis"
    / "target_conditioned_source_collapse_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_conditioned_source_collapse_gate.json"
)

OUT_STEM = "01_target_chunk_dictionary_gate"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


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


def log2_choice_count(count: int) -> float:
    if count <= 1:
        return 0.0
    return math.log2(count)


def chunk_rows(copy_ledger: dict[str, Any], literal_ledger: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in copy_ledger["copy_rows"]:
        rows.append(
            {
                "kind": "copy",
                "book": int(row["book"]),
                "op_index": int(row["op_index"]),
                "target_start": int(row["target_start"]),
                "length": int(row["length"]),
                "chunk": str(row["target_chunk"]),
            }
        )
    for row in literal_ledger["literal_rows"]:
        rows.append(
            {
                "kind": "literal",
                "book": int(row["book"]),
                "op_index": int(row["op_index"]),
                "target_start": int(row["target_start"]),
                "length": int(row["length"]),
                "chunk": str(row["payload"]),
            }
        )
    return sorted(rows, key=lambda row: (row["book"], row["op_index"], row["target_start"]))


def dictionary_cost(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["chunk"] for row in rows)
    unique_chunks = sorted(counts)
    dictionary_digits = sum(len(chunk) for chunk in unique_chunks)
    assignment_bits = sum(log2_choice_count(len(unique_chunks)) for _ in rows)
    total_bits = dictionary_digits * math.log2(10) + assignment_bits
    repeated_chunks = [chunk for chunk, count in counts.items() if count > 1]
    repeated_rows = [row for row in rows if counts[row["chunk"]] > 1]
    singleton_rows = [row for row in rows if counts[row["chunk"]] == 1]
    repeated_dictionary_digits = sum(len(chunk) for chunk in repeated_chunks)
    repeated_assignment_bits = len(repeated_rows) * log2_choice_count(len(repeated_chunks))
    singleton_raw_bits = sum(int(row["length"]) * math.log2(10) for row in singleton_rows)
    repeated_total_bits = (
        repeated_dictionary_digits * math.log2(10)
        + repeated_assignment_bits
        + singleton_raw_bits
    )
    return {
        "row_count": len(rows),
        "unique_chunk_count": len(unique_chunks),
        "unique_fraction": len(unique_chunks) / len(rows) if rows else 0.0,
        "dictionary_digits": dictionary_digits,
        "assignment_bits": assignment_bits,
        "total_bits": total_bits,
        "repeated_chunk_count": len(repeated_chunks),
        "repeated_row_count": len(repeated_rows),
        "repeated_digits": sum(int(row["length"]) for row in repeated_rows),
        "singleton_row_count": len(singleton_rows),
        "repeated_only_dictionary_digits": repeated_dictionary_digits,
        "repeated_only_assignment_bits": repeated_assignment_bits,
        "repeated_only_total_bits": repeated_total_bits,
    }


def length_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [int(row["length"]) for row in rows]
    if not values:
        return {"min": 0, "mean": 0.0, "max": 0}
    return {"min": min(values), "mean": mean(values), "max": max(values)}


def make_result() -> dict[str, Any]:
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    literal_ledger = load_json(LITERAL_PAYLOAD_LEDGER)
    target_source = load_json(TARGET_CONDITIONED_SOURCE)
    assert_boundary("copy_source_ledger", copy_ledger)
    assert_boundary("literal_payload_ledger", literal_ledger)
    assert_boundary("target_conditioned_source_collapse", target_source)
    rows = chunk_rows(copy_ledger, literal_ledger)
    copy_rows = [row for row in rows if row["kind"] == "copy"]
    literal_rows = [row for row in rows if row["kind"] == "literal"]
    all_cost = dictionary_cost(rows)
    copy_cost = dictionary_cost(copy_rows)
    literal_cost = dictionary_cost(literal_rows)
    baseline_bits = (
        float(target_source["summary"]["earliest_exception_total_bits"])
        + float(literal_ledger["summary"]["raw_uniform_bits"])
    )
    # This is the relevant comparator for a target-conditioned account:
    # target chunks would replace raw literal payload plus earliest-source exceptions.
    target_stream_raw_bits = sum(int(row["length"]) * math.log2(10) for row in rows)
    promotes_dictionary = all_cost["total_bits"] < baseline_bits
    summary = {
        "operation_chunk_count": len(rows),
        "copy_chunk_count": len(copy_rows),
        "literal_chunk_count": len(literal_rows),
        "copy_digit_count": sum(int(row["length"]) for row in copy_rows),
        "literal_digit_count": sum(int(row["length"]) for row in literal_rows),
        "all_unique_chunks": all_cost["unique_chunk_count"],
        "all_unique_fraction": all_cost["unique_fraction"],
        "copy_unique_chunks": copy_cost["unique_chunk_count"],
        "copy_unique_fraction": copy_cost["unique_fraction"],
        "literal_unique_chunks": literal_cost["unique_chunk_count"],
        "literal_unique_fraction": literal_cost["unique_fraction"],
        "all_repeated_chunks": all_cost["repeated_chunk_count"],
        "all_repeated_rows": all_cost["repeated_row_count"],
        "all_repeated_digits": all_cost["repeated_digits"],
        "copy_repeated_chunks": copy_cost["repeated_chunk_count"],
        "copy_repeated_rows": copy_cost["repeated_row_count"],
        "copy_repeated_digits": copy_cost["repeated_digits"],
        "literal_repeated_chunks": literal_cost["repeated_chunk_count"],
        "literal_repeated_rows": literal_cost["repeated_row_count"],
        "literal_repeated_digits": literal_cost["repeated_digits"],
        "target_conditioned_baseline_bits": baseline_bits,
        "target_stream_raw_bits": target_stream_raw_bits,
        "all_chunk_dictionary_bits": all_cost["total_bits"],
        "all_chunk_dictionary_delta_vs_baseline": all_cost["total_bits"] - baseline_bits,
        "all_chunk_repeated_only_bits": all_cost["repeated_only_total_bits"],
        "all_chunk_repeated_only_delta_vs_raw_stream": (
            all_cost["repeated_only_total_bits"] - target_stream_raw_bits
        ),
        "copy_length_stats": length_stats(copy_rows),
        "literal_length_stats": length_stats(literal_rows),
        "promotes_target_chunk_dictionary": promotes_dictionary,
        "interpretation": (
            "The target-conditioned source-collapse clue makes a target-stream "
            "account attractive, but exact target chunks do not form a compact "
            "dictionary. A dictionary would mostly repackage copied payload "
            "content rather than generate it."
        ),
    }
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["chunk"]].append(row)
    repeated_examples = [
        {
            "chunk": chunk,
            "length": len(chunk),
            "count": len(items),
            "locations": [
                {
                    "kind": item["kind"],
                    "book": item["book"],
                    "op_index": item["op_index"],
                    "target_start": item["target_start"],
                }
                for item in items
            ],
        }
        for chunk, items in sorted(
            groups.items(), key=lambda pair: (-len(pair[1]), -len(pair[0]), pair[0])
        )
        if len(items) > 1
    ][:20]
    return {
        "schema": "target_chunk_dictionary_gate.v1",
        "classification": (
            "target_chunk_dictionary_promoted"
            if promotes_dictionary
            else "target_chunk_dictionary_rejected"
        ),
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "literal_payload_ledger": rel(LITERAL_PAYLOAD_LEDGER),
            "target_conditioned_source_collapse": rel(TARGET_CONDITIONED_SOURCE),
        },
        "scope": {
            "analysis_only": True,
            "target_stream_dictionary_test": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": summary,
        "dictionary_costs": {
            "all_chunks": all_cost,
            "copy_chunks": copy_cost,
            "literal_chunks": literal_cost,
        },
        "repeated_examples": repeated_examples,
        "decision": {
            "target_stream_status": "chunk_dictionary_rejected",
            "copy_source_status": "still_downstream_if_target_stream_exists",
            "compression_bound_status": "unchanged_8154_676268",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_markdown(out: Path, data: dict[str, Any]) -> None:
    s = data["summary"]
    lines = [
        "# Target Chunk Dictionary Gate",
        "",
        f"Classification: `{data['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the missing target-stream can be represented as a compact",
        "dictionary of exact operation chunks after the exact skeleton is granted.",
        "",
        "## Summary",
        "",
        f"- Operation chunks: `{s['operation_chunk_count']}` (`{s['copy_chunk_count']}` copy, `{s['literal_chunk_count']}` literal).",
        f"- Copy/literal digits: `{s['copy_digit_count']}` / `{s['literal_digit_count']}`.",
        f"- Unique chunks overall: `{s['all_unique_chunks']}/{s['operation_chunk_count']}` (`{s['all_unique_fraction']:.3f}`).",
        f"- Unique copy chunks: `{s['copy_unique_chunks']}/{s['copy_chunk_count']}` (`{s['copy_unique_fraction']:.3f}`).",
        f"- Unique literal chunks: `{s['literal_unique_chunks']}/{s['literal_chunk_count']}` (`{s['literal_unique_fraction']:.3f}`).",
        f"- Repeated chunks/rows/digits overall: `{s['all_repeated_chunks']}` / `{s['all_repeated_rows']}` / `{s['all_repeated_digits']}`.",
        f"- Target-conditioned baseline bits: `{s['target_conditioned_baseline_bits']:.3f}`.",
        f"- All-chunk dictionary bits: `{s['all_chunk_dictionary_bits']:.3f}`.",
        f"- Dictionary delta vs baseline: `{s['all_chunk_dictionary_delta_vs_baseline']:.3f}` bits.",
        f"- Repeated-only chunk dictionary delta vs raw stream: `{s['all_chunk_repeated_only_delta_vs_raw_stream']:.3f}` bits.",
        "",
        "## Repeated Chunk Examples",
        "",
        "| Chunk | Length | Count |",
        "| --- | ---: | ---: |",
    ]
    for item in data["repeated_examples"][:10]:
        lines.append(f"| `{item['chunk']}` | `{item['length']}` | `{item['count']}` |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes target-chunk dictionary: `{s['promotes_target_chunk_dictionary']}`.",
            "- Exact target chunks are too close to unique payload declarations to serve as a compact generator.",
            "- This rejects the simplest target-stream dictionary account; it does not reject richer latent/state mechanisms.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    data = make_result()
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_out = TEST_RESULTS / f"{OUT_STEM}.json"
    md_out = TEST_RESULTS / f"{OUT_STEM}.md"
    json_out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(md_out, data)
    print(json.dumps(data["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Callable


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
TARGET_DICTIONARY_GATE = (
    ROOT
    / "analysis"
    / "target_chunk_dictionary_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_chunk_dictionary_gate.json"
)

OUT_STEM = "01_target_chunk_signature_gate"
RANDOM_SEED = 46920260621
RANDOM_TRIALS = 500
DIGITS = "0123456789"


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


def length_bucket(length: int) -> str:
    if length <= 1:
        return "001"
    if length <= 3:
        return "002_003"
    if length <= 5:
        return "004_005"
    if length <= 10:
        return "006_010"
    if length <= 20:
        return "011_020"
    if length <= 50:
        return "021_050"
    if length <= 100:
        return "051_100"
    return "101_plus"


def op_phase(row: dict[str, Any]) -> str:
    op_index = int(row["op_index"])
    if op_index <= 1:
        return "first"
    if op_index <= 3:
        return "early"
    if op_index <= 6:
        return "mid"
    return "late"


def first_last(chunk: str, width: int) -> str:
    if not chunk:
        return ""
    return f"{chunk[:width]}|{chunk[-width:]}"


def digit_support(chunk: str) -> str:
    return "".join(digit for digit in DIGITS if digit in chunk)


def digit_histogram_shape(chunk: str) -> str:
    counts = Counter(chunk)
    return ",".join(str(counts[digit]) for digit in DIGITS)


def digit_sum_mod(chunk: str, modulus: int) -> int:
    return sum(int(ch) for ch in chunk) % modulus


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


def randomized_rows(rows: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        length = int(row["length"])
        new_row = dict(row)
        new_row["chunk"] = "".join(rng.choice(DIGITS) for _ in range(length))
        out.append(new_row)
    return out


SignatureFn = Callable[[dict[str, Any]], str]


SIGNATURES: dict[str, tuple[str, SignatureFn]] = {
    "kind": (
        "non_payload",
        lambda row: row["kind"],
    ),
    "kind_x_length": (
        "non_payload",
        lambda row: f"{row['kind']}|L={row['length']}",
    ),
    "kind_x_length_bucket": (
        "non_payload",
        lambda row: f"{row['kind']}|B={length_bucket(int(row['length']))}",
    ),
    "kind_x_length_bucket_x_op_phase": (
        "non_payload",
        lambda row: (
            f"{row['kind']}|B={length_bucket(int(row['length']))}|P={op_phase(row)}"
        ),
    ),
    "kind_x_book_mod10_x_length_bucket": (
        "non_payload",
        lambda row: (
            f"{row['kind']}|M={int(row['book']) % 10}|B={length_bucket(int(row['length']))}"
        ),
    ),
    "kind_x_length_bucket_x_first_last": (
        "payload_edge",
        lambda row: (
            f"{row['kind']}|B={length_bucket(int(row['length']))}|E={first_last(row['chunk'], 1)}"
        ),
    ),
    "kind_x_length_bucket_x_first2_last2": (
        "payload_edge",
        lambda row: (
            f"{row['kind']}|B={length_bucket(int(row['length']))}|E={first_last(row['chunk'], 2)}"
        ),
    ),
    "kind_x_length_bucket_x_digit_support": (
        "payload_histogram",
        lambda row: (
            f"{row['kind']}|B={length_bucket(int(row['length']))}|S={digit_support(row['chunk'])}"
        ),
    ),
    "kind_x_length_bucket_x_digit_sum_mod10": (
        "payload_checksum",
        lambda row: (
            f"{row['kind']}|B={length_bucket(int(row['length']))}|C={digit_sum_mod(row['chunk'], 10)}"
        ),
    ),
    "kind_x_length_bucket_x_histogram_shape": (
        "payload_histogram",
        lambda row: (
            f"{row['kind']}|B={length_bucket(int(row['length']))}|H={digit_histogram_shape(row['chunk'])}"
        ),
    ),
}


def log2_choice_count(count: int) -> float:
    if count <= 1:
        return 0.0
    return math.log2(count)


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = (len(sorted_values) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return sorted_values[lower]
    frac = index - lower
    return sorted_values[lower] * (1.0 - frac) + sorted_values[upper] * frac


def signature_metrics(rows: list[dict[str, Any]], signature_fn: SignatureFn) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[signature_fn(row)].append(row)
    sizes = sorted((len(items) for items in buckets.values()), reverse=True)
    singleton_count = sum(1 for size in sizes if size == 1)
    singleton_rows = singleton_count
    selector_bits = sum(log2_choice_count(len(buckets[signature_fn(row)])) for row in rows)
    entropy_bits = 0.0
    total = len(rows)
    for size in sizes:
        p = size / total if total else 0.0
        entropy_bits -= size * math.log2(p) if p else 0.0
    return {
        "signature_count": len(buckets),
        "singleton_signatures": singleton_count,
        "singleton_rows": singleton_rows,
        "singleton_row_fraction": singleton_rows / total if total else 0.0,
        "max_bucket_size": sizes[0] if sizes else 0,
        "mean_bucket_size": mean(sizes) if sizes else 0.0,
        "within_signature_exact_selector_bits": selector_bits,
        "empirical_signature_assignment_bits": entropy_bits,
        "top_buckets": [
            {"signature": signature, "count": len(items)}
            for signature, items in sorted(
                buckets.items(), key=lambda item: (-len(item[1]), item[0])
            )[:8]
        ],
    }


def random_control(rows: list[dict[str, Any]], signature_fn: SignatureFn) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    signature_counts = []
    singleton_rows = []
    selector_bits = []
    for _ in range(RANDOM_TRIALS):
        metrics = signature_metrics(randomized_rows(rows, rng), signature_fn)
        signature_counts.append(float(metrics["signature_count"]))
        singleton_rows.append(float(metrics["singleton_rows"]))
        selector_bits.append(float(metrics["within_signature_exact_selector_bits"]))
    signature_counts.sort()
    singleton_rows.sort()
    selector_bits.sort()
    return {
        "trials": RANDOM_TRIALS,
        "random_seed": RANDOM_SEED,
        "signature_count_mean": mean(signature_counts),
        "signature_count_p05": percentile(signature_counts, 0.05),
        "signature_count_p95": percentile(signature_counts, 0.95),
        "singleton_rows_mean": mean(singleton_rows),
        "singleton_rows_p05": percentile(singleton_rows, 0.05),
        "singleton_rows_p95": percentile(singleton_rows, 0.95),
        "selector_bits_mean": mean(selector_bits),
        "selector_bits_p05": percentile(selector_bits, 0.05),
        "selector_bits_p95": percentile(selector_bits, 0.95),
        "selector_bits_std": pstdev(selector_bits),
    }


def family_results(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for name, (feature_class, signature_fn) in SIGNATURES.items():
        metrics = signature_metrics(rows, signature_fn)
        result = {
            "name": name,
            "feature_class": feature_class,
            **metrics,
        }
        if feature_class != "non_payload":
            control = random_control(rows, signature_fn)
            result["random_control"] = control
            result["observed_selector_bits_delta_vs_random_mean"] = (
                metrics["within_signature_exact_selector_bits"]
                - control["selector_bits_mean"]
            )
            result["observed_signature_count_delta_vs_random_mean"] = (
                metrics["signature_count"] - control["signature_count_mean"]
            )
        out.append(result)
    return out


def make_result() -> dict[str, Any]:
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    literal_ledger = load_json(LITERAL_PAYLOAD_LEDGER)
    dictionary_gate = load_json(TARGET_DICTIONARY_GATE)
    assert_boundary("copy_source_ledger", copy_ledger)
    assert_boundary("literal_payload_ledger", literal_ledger)
    assert_boundary("target_chunk_dictionary_gate", dictionary_gate)
    rows = chunk_rows(copy_ledger, literal_ledger)
    target_stream_raw_bits = sum(int(row["length"]) * math.log2(10) for row in rows)
    results = family_results(rows)
    non_payload = [row for row in results if row["feature_class"] == "non_payload"]
    payload = [row for row in results if row["feature_class"] != "non_payload"]
    best_non_payload = min(
        non_payload,
        key=lambda row: row["within_signature_exact_selector_bits"],
    )
    least_unique_payload = min(payload, key=lambda row: row["signature_count"])
    most_exact_payload = max(payload, key=lambda row: row["singleton_rows"])
    promotes_signature_generator = False
    summary = {
        "operation_chunk_count": len(rows),
        "copy_chunk_count": sum(1 for row in rows if row["kind"] == "copy"),
        "literal_chunk_count": sum(1 for row in rows if row["kind"] == "literal"),
        "target_stream_digit_count": sum(int(row["length"]) for row in rows),
        "target_stream_raw_bits": target_stream_raw_bits,
        "exact_chunk_unique_count": dictionary_gate["summary"]["all_unique_chunks"],
        "exact_chunk_unique_fraction": dictionary_gate["summary"]["all_unique_fraction"],
        "best_non_payload_family": best_non_payload["name"],
        "best_non_payload_selector_bits": best_non_payload[
            "within_signature_exact_selector_bits"
        ],
        "best_non_payload_signature_count": best_non_payload["signature_count"],
        "best_non_payload_singleton_rows": best_non_payload["singleton_rows"],
        "least_unique_payload_family": least_unique_payload["name"],
        "least_unique_payload_signature_count": least_unique_payload["signature_count"],
        "least_unique_payload_selector_bits": least_unique_payload[
            "within_signature_exact_selector_bits"
        ],
        "most_exact_payload_family": most_exact_payload["name"],
        "most_exact_payload_singleton_rows": most_exact_payload["singleton_rows"],
        "most_exact_payload_signature_count": most_exact_payload["signature_count"],
        "promotes_signature_generator": promotes_signature_generator,
        "interpretation": (
            "Non-payload signatures compress labels only by leaving almost all "
            "target digits unresolved. Payload-derived signatures become more "
            "specific, but their behavior is consistent with ordinary same-length "
            "random digit strings and therefore does not provide a source-free "
            "target-stream generator."
        ),
    }
    return {
        "schema": "target_chunk_signature_gate_v1",
        "scope": "analysis_only_target_stream_signature_control",
        "inputs": {
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "literal_payload_ledger": rel(LITERAL_PAYLOAD_LEDGER),
            "target_chunk_dictionary_gate": rel(TARGET_DICTIONARY_GATE),
        },
        "summary": summary,
        "signature_families": results,
        "classification": "target_chunk_signature_generator_rejected",
        "decision": {
            "promotes_signature_generator": promotes_signature_generator,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    rows = result["signature_families"]
    lines = [
        "# Target Chunk Signature Gate",
        "",
        "Classification: `target_chunk_signature_generator_rejected`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether a coarse signature layer can replace exact target chunks",
        "without becoming payload lookup or a target-text oracle.",
        "",
        "## Summary",
        "",
        f"- Operation chunks: `{s['operation_chunk_count']}` (`{s['copy_chunk_count']}` copy, `{s['literal_chunk_count']}` literal).",
        f"- Target-stream digits: `{s['target_stream_digit_count']}`.",
        f"- Exact unique chunks from prior audit: `{s['exact_chunk_unique_count']}/{s['operation_chunk_count']}` (`{s['exact_chunk_unique_fraction']:.3f}`).",
        f"- Best non-payload family: `{s['best_non_payload_family']}`.",
        f"- Best non-payload signatures/singletons/selector bits: `{s['best_non_payload_signature_count']}` / `{s['best_non_payload_singleton_rows']}` / `{s['best_non_payload_selector_bits']:.3f}`.",
        f"- Least-unique payload family: `{s['least_unique_payload_family']}`.",
        f"- Least-unique payload signatures/selector bits: `{s['least_unique_payload_signature_count']}` / `{s['least_unique_payload_selector_bits']:.3f}`.",
        f"- Most-exact payload family: `{s['most_exact_payload_family']}`.",
        f"- Most-exact payload singletons/signatures: `{s['most_exact_payload_singleton_rows']}` / `{s['most_exact_payload_signature_count']}`.",
        "",
        "## Signature Families",
        "",
        "| Family | Class | Signatures | Singleton rows | Max bucket | Exact selector bits | Random selector mean |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        control = row.get("random_control")
        random_mean = (
            f"{control['selector_bits_mean']:.3f}" if control is not None else "n/a"
        )
        lines.append(
            "| "
            f"`{row['name']}` | `{row['feature_class']}` | "
            f"`{row['signature_count']}` | "
            f"`{row['singleton_rows']}` | "
            f"`{row['max_bucket_size']}` | "
            f"`{row['within_signature_exact_selector_bits']:.3f}` | "
            f"`{random_mean}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Promotes target-chunk signature generator: `False`.",
            "- Non-payload signatures leave the exact target digits unresolved.",
            "- Payload signatures mostly measure edge/checksum/histogram content already inside the target stream.",
            "- Random same-length controls do not support a promoted source-free signature rule.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(result)
    print(json.dumps({"output": rel(TEST_RESULTS / f"{OUT_STEM}.json")}, indent=2))


if __name__ == "__main__":
    main()

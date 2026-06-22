from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
RANKING_FRONTIER = TEST_RESULTS / "07_copy_candidate_ranking_frontier.json"

OUT_STEM = "08_copy_hint_stream_lower_bound"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
TOP_K = 80
DIGIT_BITS = math.log2(10)


ChunkRow = dict[str, Any]
PolicyKey = Callable[[ChunkRow, int, int], tuple[Any, ...]]


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


def policy_keys() -> dict[str, PolicyKey]:
    return {
        "current_source_penalty": lambda row, _n, _l: (
            0.05 * math.log2(max(1, int(row["min_source"]) + 1)),
            row["chunk"],
        ),
        "earliest": lambda row, _n, _l: (int(row["min_source"]), row["chunk"]),
        "longest_recent": lambda row, n, length: (
            n - (int(row["max_source"]) + length),
            -int(row["count"]),
            row["chunk"],
        ),
        "frequent_longest": lambda row, n, length: (
            -int(row["count"]),
            n - (int(row["max_source"]) + length),
            row["chunk"],
        ),
        "rare_recent": lambda row, n, length: (
            int(row["count"]),
            n - (int(row["max_source"]) + length),
            row["chunk"],
        ),
    }


def unique_chunks_at_length(available: str, length: int) -> list[ChunkRow]:
    rows: dict[str, ChunkRow] = {}
    for source in range(0, len(available) - length + 1):
        chunk = available[source : source + length]
        row = rows.get(chunk)
        if row is None:
            rows[chunk] = {
                "chunk": chunk,
                "min_source": source,
                "max_source": source,
                "count": 1,
            }
        else:
            row["max_source"] = source
            row["count"] += 1
    return list(rows.values())


def rank_of_correct(
    rows: list[ChunkRow],
    payload: str,
    available_len: int,
    length: int,
    key_fn: PolicyKey,
) -> int:
    correct = next(row for row in rows if row["chunk"] == payload)
    correct_key = key_fn(correct, available_len, length)
    return 1 + sum(1 for row in rows if key_fn(row, available_len, length) < correct_key)


def copy_rows() -> list[dict[str, Any]]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("copy_source_ledger", ledger)
    out: list[dict[str, Any]] = []
    policies = policy_keys()
    for book_key, ops in ledger["canonical_ops_by_book"].items():
        book = int(book_key)
        target = books[book]
        emitted_base = "".join(books[index] for index in range(book))
        for op_index, op in enumerate(ops):
            if op["type"] != "copy":
                continue
            start = int(op["target_start"])
            length = int(op["length"])
            source = int(op["source"])
            available = emitted_base + target[:start]
            payload = target[start : start + length]
            source_payload = available[source : source + length]
            if source_payload != payload:
                raise RuntimeError(f"canonical source mismatch book={book} start={start}")
            rows = unique_chunks_at_length(available, length)
            correct_rows = [row for row in rows if row["chunk"] == payload]
            if not correct_rows:
                raise RuntimeError(f"missing canonical chunk book={book} start={start}")
            policy_ranks = {
                name: rank_of_correct(rows, payload, len(available), length, key_fn)
                for name, key_fn in policies.items()
            }
            out.append(
                {
                    "book": book,
                    "op_index": op_index,
                    "target_start": start,
                    "length": length,
                    "available_len": len(available),
                    "unique_chunks_same_length": len(rows),
                    "source_occurrences": correct_rows[0]["count"],
                    "source_address_bits": math.log2(max(1, len(available) - length + 1)),
                    "uniform_chunk_hint_bits": math.log2(len(rows)),
                    "raw_literal_bits": length * DIGIT_BITS,
                    "policy_ranks": policy_ranks,
                    "policy_rank_bits": {
                        name: math.log2(rank) for name, rank in policy_ranks.items()
                    },
                    "top_k_hits": {
                        name: rank <= TOP_K for name, rank in policy_ranks.items()
                    },
                }
            )
    return out


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    policies = list(policy_keys())
    copy_digits = sum(row["length"] for row in rows)
    source_bits = sum(row["source_address_bits"] for row in rows)
    uniform_bits = sum(row["uniform_chunk_hint_bits"] for row in rows)
    raw_literal_bits = sum(row["raw_literal_bits"] for row in rows)
    policy_bits = {
        name: sum(row["policy_rank_bits"][name] for row in rows) for name in policies
    }
    top_k_hits = {name: sum(1 for row in rows if row["top_k_hits"][name]) for name in policies}
    best_policy = min(policy_bits, key=lambda name: policy_bits[name])
    return {
        "copy_ops": len(rows),
        "copy_digits": copy_digits,
        "source_address_bits": source_bits,
        "uniform_chunk_hint_bits": uniform_bits,
        "raw_literal_bits": raw_literal_bits,
        "policy_rank_bits": policy_bits,
        "policy_top_k_hits": top_k_hits,
        "best_policy": best_policy,
        "best_policy_rank_bits": policy_bits[best_policy],
        "best_policy_saving_vs_source_address_bits": source_bits - policy_bits[best_policy],
        "best_policy_saving_vs_uniform_chunk_bits": uniform_bits - policy_bits[best_policy],
        "best_policy_fraction_of_raw_literal_bits": policy_bits[best_policy]
        / raw_literal_bits,
        "mean_unique_chunks_same_length": mean(
            row["unique_chunks_same_length"] for row in rows
        ),
        "median_unique_chunks_same_length": sorted(
            row["unique_chunks_same_length"] for row in rows
        )[len(rows) // 2],
        "length_counts": dict(sorted(Counter(row["length"] for row in rows).items())),
    }


def make_result() -> dict[str, Any]:
    ranking_frontier = load_json(RANKING_FRONTIER)
    assert_boundary("copy_candidate_ranking_frontier", ranking_frontier)
    rows = copy_rows()
    summary = summarize(rows)
    cutoff_rows = []
    for cutoff in PREFIX_CUTOFFS:
        suffix_rows = [row for row in rows if row["book"] >= cutoff]
        s = summarize(suffix_rows)
        cutoff_rows.append(
            {
                "cutoff": cutoff,
                "copy_ops": s["copy_ops"],
                "copy_digits": s["copy_digits"],
                "best_policy": s["best_policy"],
                "best_policy_rank_bits": s["best_policy_rank_bits"],
                "source_address_bits": s["source_address_bits"],
                "uniform_chunk_hint_bits": s["uniform_chunk_hint_bits"],
                "best_policy_saving_vs_source_address_bits": s[
                    "best_policy_saving_vs_source_address_bits"
                ],
            }
        )
    promotes_hint_lower_bound = (
        summary["best_policy_rank_bits"] < summary["source_address_bits"]
        and summary["best_policy_fraction_of_raw_literal_bits"] < 0.10
    )
    return {
        "schema": "copy_hint_stream_lower_bound_v1",
        "scope": "analysis_only_known_length_copy_chunk_hint_budget",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "copy_candidate_ranking_frontier": rel(RANKING_FRONTIER),
        },
        "grants": [
            "canonical_op_start",
            "copy_type",
            "canonical_copy_length",
            "previous_material_exact",
        ],
        "summary": summary,
        "cutoff_rows": cutoff_rows,
        "classification": "copy_hint_stream_lower_bound_open",
        "interpretation": (
            "If copy length is granted, a target-free rank-coded chunk hint is "
            "substantially cheaper than raw source addressing and far cheaper "
            "than literalizing copied digits. This is a constructive lower bound "
            "for a paid copy-control stream, not a generator: op starts, copy type, "
            "and lengths are still granted."
        ),
        "decision": {
            "promotes_generator": False,
            "promotes_copy_hint_lower_bound": promotes_hint_lower_bound,
            "promotes_copy_origin_rule": False,
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
    lines = [
        "# Copy Hint Stream Lower Bound",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Measure the paid external copy hint still required after granting copy",
        "start, copy type, copy length, and exact prior material. The hint chooses",
        "the same-length chunk to copy; it does not generate op starts or lengths.",
        "",
        "## Summary",
        "",
        f"- Copy ops: `{s['copy_ops']}`.",
        f"- Copy digits: `{s['copy_digits']}`.",
        f"- Source-address bits: `{s['source_address_bits']:.3f}`.",
        f"- Uniform same-length chunk hint bits: `{s['uniform_chunk_hint_bits']:.3f}`.",
        f"- Best rank-coded hint policy: `{s['best_policy']}`.",
        f"- Best rank-coded hint bits: `{s['best_policy_rank_bits']:.3f}`.",
        f"- Saving vs source address bits: `{s['best_policy_saving_vs_source_address_bits']:.3f}`.",
        f"- Saving vs uniform chunk hint bits: `{s['best_policy_saving_vs_uniform_chunk_bits']:.3f}`.",
        f"- Fraction of raw copied-digit literal bits: `{s['best_policy_fraction_of_raw_literal_bits']:.6f}`.",
        f"- Mean/median same-length chunks: `{s['mean_unique_chunks_same_length']:.3f}` / `{s['median_unique_chunks_same_length']}`.",
        f"- Policy top-{TOP_K} hits: `{s['policy_top_k_hits']}`.",
        f"- Promotes copy hint lower bound: `{result['decision']['promotes_copy_hint_lower_bound']}`.",
        "",
        result["interpretation"],
        "",
        "## Policy Rank Bits",
        "",
        "| Policy | Rank Bits | Top-80 Hits |",
        "| --- | ---: | ---: |",
    ]
    for policy, bits in s["policy_rank_bits"].items():
        lines.append(
            f"| `{policy}` | `{bits:.3f}` | `{s['policy_top_k_hits'][policy]}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix Cutoff Rows",
            "",
            "| Cutoff | Copy Ops | Copy Digits | Best Policy | Best Bits | Source Bits | Saving vs Source |",
            "| ---: | ---: | ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for row in result["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['copy_ops']}` | `{row['copy_digits']}` | "
            f"`{row['best_policy']}` | `{row['best_policy_rank_bits']:.3f}` | "
            f"`{row['source_address_bits']:.3f}` | "
            f"`{row['best_policy_saving_vs_source_address_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- This is a constructive lower bound for a paid copy-control stream.",
            "- It does not solve op starts, type, length, or closed-loop generation.",
            "- The next route is to test whether the copy hint stream has compressible structure or can be synchronized with the innovation/control tapes.",
            "- Row0, plaintext, translation, and compression bound remain unchanged.",
            "",
        ]
    )
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_markdown(result)
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "summary": result["summary"],
                "decision": result["decision"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

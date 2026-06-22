from __future__ import annotations

import importlib.util
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

COPY_HINT_LOWER_BOUND_SCRIPT = HERE / "scripts" / "08_copy_hint_stream_lower_bound.py"
COPY_HINT_LOWER_BOUND = TEST_RESULTS / "08_copy_hint_stream_lower_bound.json"

OUT_STEM = "09_copy_hint_stream_structure_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 500
RANDOM_SEED = 46920260623


FeatureFn = Callable[[dict[str, Any]], str]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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


def bucket_rank(rank: int) -> int:
    return int(math.floor(math.log2(rank))) if rank > 0 else 0


def bucket_size(bucket: int) -> int:
    return 1 if bucket == 0 else 2**bucket


def length_bucket(length: int) -> str:
    if length <= 8:
        return "len_0008"
    if length <= 16:
        return "len_0016"
    if length <= 32:
        return "len_0032"
    if length <= 64:
        return "len_0064"
    if length <= 128:
        return "len_0128"
    return "len_0256p"


def count_bucket(value: int) -> str:
    if value <= 1:
        return "count_0001"
    if value <= 2:
        return "count_0002"
    if value <= 4:
        return "count_0004"
    if value <= 8:
        return "count_0008"
    return "count_0016p"


def candidate_bucket(value: int) -> str:
    if value <= 512:
        return "cand_0512"
    if value <= 1024:
        return "cand_1024"
    if value <= 2048:
        return "cand_2048"
    if value <= 4096:
        return "cand_4096"
    return "cand_8192p"


def op_index_bucket(value: int) -> str:
    if value <= 1:
        return "op_01"
    if value <= 3:
        return "op_03"
    if value <= 6:
        return "op_06"
    return "op_07p"


def target_start_bucket(value: int) -> str:
    if value <= 8:
        return "start_0008"
    if value <= 32:
        return "start_0032"
    if value <= 80:
        return "start_0080"
    return "start_0081p"


def feature_fns() -> dict[str, FeatureFn]:
    return {
        "global": lambda _row: "global",
        "length_bucket": lambda row: length_bucket(int(row["length"])),
        "source_occurrence_bucket": lambda row: count_bucket(
            int(row["source_occurrences"])
        ),
        "candidate_count_bucket": lambda row: candidate_bucket(
            int(row["unique_chunks_same_length"])
        ),
        "op_index_bucket": lambda row: op_index_bucket(int(row["op_index"])),
        "target_start_bucket": lambda row: target_start_bucket(
            int(row["target_start"])
        ),
        "length_x_occurrence": lambda row: "|".join(
            [
                length_bucket(int(row["length"])),
                count_bucket(int(row["source_occurrences"])),
            ]
        ),
        "length_x_candidate": lambda row: "|".join(
            [
                length_bucket(int(row["length"])),
                candidate_bucket(int(row["unique_chunks_same_length"])),
            ]
        ),
    }


def logp(counter: Counter[int], key: int, alphabet_size: int) -> float:
    total = sum(counter.values())
    return -math.log2((counter.get(key, 0) + 1) / (total + alphabet_size))


def prepare_rows() -> tuple[list[dict[str, Any]], str]:
    lower_bound = load_json(COPY_HINT_LOWER_BOUND)
    assert_boundary("copy_hint_stream_lower_bound", lower_bound)
    best_policy = lower_bound["summary"]["best_policy"]
    module = load_module("copy_hint_lower_bound_for_structure", COPY_HINT_LOWER_BOUND_SCRIPT)
    rows = module.copy_rows()
    for row in rows:
        rank = int(row["policy_ranks"][best_policy])
        bucket = bucket_rank(rank)
        row["best_policy"] = best_policy
        row["hint_rank"] = rank
        row["hint_rank_bits"] = math.log2(rank)
        row["hint_rank_bucket"] = bucket
        row["hint_bucket_offset_bits"] = math.log2(bucket_size(bucket))
    return rows, best_policy


def code_cost(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    feature_name: str,
    feature_fn: FeatureFn,
) -> dict[str, Any]:
    alphabet = max(row["hint_rank_bucket"] for row in train_rows + test_rows) + 1
    global_counter = Counter(row["hint_rank_bucket"] for row in train_rows)
    counters: dict[str, Counter[int]] = {}
    for row in train_rows:
        counters.setdefault(feature_fn(row), Counter())[row["hint_rank_bucket"]] += 1
    bucket_bits = 0.0
    offset_bits = 0.0
    fallback_rows = 0
    for row in test_rows:
        key = feature_fn(row)
        counter = counters.get(key)
        if counter is None:
            counter = global_counter
            fallback_rows += 1
        bucket_bits += logp(counter, row["hint_rank_bucket"], alphabet)
        offset_bits += row["hint_bucket_offset_bits"]
    rank_bits = sum(row["hint_rank_bits"] for row in test_rows)
    return {
        "feature": feature_name,
        "test_rows": len(test_rows),
        "rank_bits": rank_bits,
        "bucket_bits": bucket_bits,
        "offset_bits": offset_bits,
        "bucket_offset_bits": bucket_bits + offset_bits,
        "saving_vs_rank_bits": rank_bits - (bucket_bits + offset_bits),
        "fallback_rows": fallback_rows,
        "fallback_fraction": fallback_rows / len(test_rows) if test_rows else 0.0,
    }


def cutoff_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    features = feature_fns()
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        feature_results = {
            name: code_cost(train, test, name, fn) for name, fn in features.items()
        }
        best = max(
            feature_results.values(),
            key=lambda item: item["saving_vs_rank_bits"],
        )
        out.append(
            {
                "cutoff": cutoff,
                "train_rows": len(train),
                "test_rows": len(test),
                "best_feature": best["feature"],
                "best_rank_bits": best["rank_bits"],
                "best_bucket_offset_bits": best["bucket_offset_bits"],
                "best_saving_vs_rank_bits": best["saving_vs_rank_bits"],
                "feature_results": feature_results,
            }
        )
    return out


def random_bucket_control(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    observed_buckets = [row["hint_rank_bucket"] for row in rows]
    values = []
    for _trial in range(RANDOM_TRIALS):
        shuffled = observed_buckets[:]
        rng.shuffle(shuffled)
        trial_rows = [dict(row, hint_rank_bucket=bucket) for row, bucket in zip(rows, shuffled)]
        crows = cutoff_rows(trial_rows)
        values.append(sum(row["best_saving_vs_rank_bits"] for row in crows))
    values.sort()
    return {
        "trials": RANDOM_TRIALS,
        "saving_mean": mean(values),
        "saving_p95": values[int(0.95 * (RANDOM_TRIALS - 1))],
        "saving_max": values[-1],
    }


def make_result() -> dict[str, Any]:
    rows, best_policy = prepare_rows()
    crows = cutoff_rows(rows)
    total_rank_bits = sum(row["best_rank_bits"] for row in crows)
    best_total_bucket_offset_bits = sum(
        row["best_bucket_offset_bits"] for row in crows
    )
    total_saving = sum(row["best_saving_vs_rank_bits"] for row in crows)
    controls = random_bucket_control(rows)
    promoted = total_saving > controls["saving_p95"] and total_saving > 0
    return {
        "schema": "copy_hint_stream_structure_gate_v1",
        "scope": "analysis_only_prequential_hint_rank_bucket_structure",
        "inputs": {
            "copy_hint_stream_lower_bound": rel(COPY_HINT_LOWER_BOUND),
        },
        "best_hint_policy": best_policy,
        "features_tested": list(feature_fns()),
        "cutoff_rows": crows,
        "random_bucket_control": controls,
        "summary": {
            "copy_ops": len(rows),
            "total_rank_bits_over_cutoffs": total_rank_bits,
            "best_total_bucket_offset_bits": best_total_bucket_offset_bits,
            "total_saving_vs_rank_bits": total_saving,
            "random_saving_p95": controls["saving_p95"],
            "beats_random_p95": total_saving > controls["saving_p95"],
            "promotes_hint_structure": promoted,
        },
        "classification": (
            "copy_hint_rank_structure_promoted"
            if promoted
            else "copy_hint_rank_structure_not_promoted"
        ),
        "interpretation": (
            "This gate asks whether the paid copy-hint rank stream has simple "
            "prequential structure after the lower-bound grants. It models only "
            "rank buckets plus within-bucket offsets, so exact copy choice remains "
            "external unless the bucket model beats the direct rank code and "
            "shuffle controls."
        ),
        "decision": {
            "promotes_generator": False,
            "promotes_copy_hint_structure": promoted,
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
    c = result["random_bucket_control"]
    lines = [
        "# Copy Hint Stream Structure Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the paid copy-hint rank stream from gate 08 has simple",
        "prequential structure. The gate codes rank buckets using prefix-trained",
        "feature contexts and pays an in-bucket offset; it does not generate copy",
        "choices directly.",
        "",
        "## Summary",
        "",
        f"- Copy ops: `{s['copy_ops']}`.",
        f"- Hint policy: `{result['best_hint_policy']}`.",
        f"- Total direct rank bits over cutoffs: `{s['total_rank_bits_over_cutoffs']:.3f}`.",
        f"- Best bucket+offset bits over cutoffs: `{s['best_total_bucket_offset_bits']:.3f}`.",
        f"- Total saving vs direct rank bits: `{s['total_saving_vs_rank_bits']:.3f}`.",
        f"- Random shuffled-bucket saving p95: `{s['random_saving_p95']:.3f}`.",
        f"- Beats random p95: `{s['beats_random_p95']}`.",
        f"- Promotes hint structure: `{s['promotes_hint_structure']}`.",
        "",
        result["interpretation"],
        "",
        "## Cutoff Rows",
        "",
        "| Cutoff | Train | Test | Best Feature | Rank Bits | Bucket+Offset Bits | Saving |",
        "| ---: | ---: | ---: | --- | ---: | ---: | ---: |",
    ]
    for row in result["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['train_rows']}` | `{row['test_rows']}` | "
            f"`{row['best_feature']}` | `{row['best_rank_bits']:.3f}` | "
            f"`{row['best_bucket_offset_bits']:.3f}` | "
            f"`{row['best_saving_vs_rank_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Random Control",
            "",
            f"- Trials: `{c['trials']}`.",
            f"- Saving mean/p95/max: `{c['saving_mean']:.3f}` / `{c['saving_p95']:.3f}` / `{c['saving_max']:.3f}`.",
            "",
            "## Decision",
            "",
            "- This does not promote a generator or source rule.",
            "- If promoted, it promotes only weak structure in the paid copy-hint stream.",
            "- If not promoted, the copy hint remains an external stream after the gate-08 grants.",
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
                "random_bucket_control": result["random_bucket_control"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

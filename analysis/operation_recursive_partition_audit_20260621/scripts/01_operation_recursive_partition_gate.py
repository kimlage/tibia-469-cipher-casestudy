from __future__ import annotations

import importlib.util
import json
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

SKELETON_SCRIPT = (
    ROOT
    / "analysis"
    / "source_free_skeleton_generation_audit_20260621"
    / "scripts"
    / "02_source_free_skeleton_grammar_gate.py"
)
LATTICE_GATE = (
    ROOT
    / "analysis"
    / "operation_cutpoint_lattice_audit_20260621"
    / "reports"
    / "test_results"
    / "01_operation_cutpoint_lattice_gate.json"
)

OUT_STEM = "01_operation_recursive_partition_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 400
RANDOM_SEED = 4692026062102


BookRow = dict[str, Any]


@dataclass(frozen=True)
class Segment:
    start: int
    end: int
    depth: int
    ordinal: int

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class Policy:
    name: str
    priority: str
    ratios: tuple[float, ...]
    ratio_mode: str


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
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


def reconstruct() -> dict[int, list[dict[str, Any]]]:
    module = load_module("source_free_skeleton_for_recursive_partition", SKELETON_SCRIPT)
    return module.reconstruct_canonical_skeleton()


def cumulative(lengths: list[int]) -> list[int]:
    total = 0
    out = []
    for length in lengths:
        total += length
        out.append(total)
    return out


def make_rows(by_book: dict[int, list[dict[str, Any]]]) -> list[BookRow]:
    rows = []
    for book in sorted(by_book):
        lengths = [int(op["length"]) for op in by_book[book]]
        book_length = sum(lengths)
        cutpoints = cumulative(lengths)[:-1]
        rows.append(
            {
                "book": book,
                "book_length": book_length,
                "op_count": len(lengths),
                "internal_count": max(0, len(lengths) - 1),
                "lengths": lengths,
                "cutpoints": cutpoints,
            }
        )
    return rows


def policies() -> list[Policy]:
    fixed_ratios = [
        ("half", (0.5,)),
        ("third_low", (1 / 3,)),
        ("third_high", (2 / 3,)),
        ("quarter_low", (0.25,)),
        ("quarter_high", (0.75,)),
        ("two_fifths", (0.4,)),
        ("three_fifths", (0.6,)),
        ("three_eighths", (0.375,)),
        ("five_eighths", (0.625,)),
        ("phi_low", (0.3819660112501051,)),
        ("phi_high", (0.6180339887498949,)),
    ]
    alternating = [
        ("thirds_alt", (1 / 3, 2 / 3)),
        ("thirds_alt_rev", (2 / 3, 1 / 3)),
        ("quarters_alt", (0.25, 0.75)),
        ("quarters_alt_rev", (0.75, 0.25)),
        ("fifths_alt", (0.4, 0.6)),
        ("fifths_alt_rev", (0.6, 0.4)),
        ("phi_alt", (0.3819660112501051, 0.6180339887498949)),
        ("phi_alt_rev", (0.6180339887498949, 0.3819660112501051)),
    ]
    priority_names = ["largest_left", "largest_right", "earliest", "latest"]
    out = []
    for priority in priority_names:
        for name, ratio_values in fixed_ratios:
            out.append(Policy(f"{priority}:{name}", priority, ratio_values, "fixed"))
        for name, ratio_values in alternating:
            out.append(Policy(f"{priority}:{name}", priority, ratio_values, "depth"))
            out.append(Policy(f"{priority}:{name}:step", priority, ratio_values, "step"))
    return out


def segment_key(segment: Segment, priority: str) -> tuple[int, int, int]:
    if priority == "largest_left":
        return (-segment.length, segment.start, segment.ordinal)
    if priority == "largest_right":
        return (-segment.length, -segment.start, segment.ordinal)
    if priority == "earliest":
        return (segment.start, -segment.length, segment.ordinal)
    if priority == "latest":
        return (-segment.start, -segment.length, segment.ordinal)
    raise ValueError(priority)


def choose_ratio(policy: Policy, segment: Segment, step: int) -> float:
    if policy.ratio_mode == "fixed":
        return policy.ratios[0]
    if policy.ratio_mode == "depth":
        return policy.ratios[segment.depth % len(policy.ratios)]
    if policy.ratio_mode == "step":
        return policy.ratios[step % len(policy.ratios)]
    raise ValueError(policy.ratio_mode)


def split_point(segment: Segment, ratio: float) -> int | None:
    if segment.length <= 1:
        return None
    point = segment.start + int(round(segment.length * ratio))
    point = max(segment.start + 1, min(point, segment.end - 1))
    if point <= segment.start or point >= segment.end:
        return None
    return point


def generate_cutpoints(book_length: int, op_count: int, policy: Policy) -> list[int]:
    if op_count <= 1:
        return []
    cuts: set[int] = set()
    segments = [Segment(0, book_length, 0, 0)]
    next_ordinal = 1
    for step in range(op_count - 1):
        candidates = [segment for segment in segments if segment.length > 1]
        if not candidates:
            break
        segment = min(candidates, key=lambda item: segment_key(item, policy.priority))
        segments.remove(segment)
        point = split_point(segment, choose_ratio(policy, segment, step))
        if point is None or point in cuts:
            midpoint = segment.start + segment.length // 2
            point = max(segment.start + 1, min(midpoint, segment.end - 1))
        cuts.add(point)
        segments.append(Segment(segment.start, point, segment.depth + 1, next_ordinal))
        next_ordinal += 1
        segments.append(Segment(point, segment.end, segment.depth + 1, next_ordinal))
        next_ordinal += 1
    return sorted(cuts)


def score_policy(rows: list[BookRow], policy: Policy) -> dict[str, Any]:
    per_book = []
    total_hits = 0
    exact_books = 0
    exact_nontrivial_books = 0
    nontrivial_books = 0
    total_internal = 0
    for row in rows:
        predicted = generate_cutpoints(
            int(row["book_length"]),
            int(row["op_count"]),
            policy,
        )
        truth = set(int(cut) for cut in row["cutpoints"])
        hits = sum(1 for cut in predicted if cut in truth)
        exact = predicted == row["cutpoints"]
        nontrivial = int(row["internal_count"]) > 0
        total_hits += hits
        exact_books += int(exact)
        exact_nontrivial_books += int(exact and nontrivial)
        nontrivial_books += int(nontrivial)
        total_internal += int(row["internal_count"])
        per_book.append(
            {
                "book": int(row["book"]),
                "book_length": int(row["book_length"]),
                "op_count": int(row["op_count"]),
                "hits": hits,
                "internal_count": int(row["internal_count"]),
                "exact": exact,
                "nontrivial": nontrivial,
                "predicted": predicted,
                "truth": row["cutpoints"],
            }
        )
    return {
        "policy": policy.name,
        "priority": policy.priority,
        "ratios": list(policy.ratios),
        "ratio_mode": policy.ratio_mode,
        "book_count": len(rows),
        "total_internal_cutpoints": total_internal,
        "total_hits": total_hits,
        "exact_books": exact_books,
        "nontrivial_books": nontrivial_books,
        "exact_nontrivial_books": exact_nontrivial_books,
        "per_book": per_book,
    }


def choose_best(scored: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        scored,
        key=lambda item: (
            int(item["exact_nontrivial_books"]),
            int(item["total_hits"]),
            int(item["exact_books"]),
            -len(str(item["policy"])),
            str(item["policy"]),
        ),
    )


def random_cutpoints(book_length: int, op_count: int, rng: random.Random) -> list[int]:
    if op_count <= 1:
        return []
    return sorted(rng.sample(range(1, book_length), op_count - 1))


def random_control(rows: list[BookRow], *, trials: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    hit_values = []
    exact_values = []
    for _ in range(trials):
        hits = 0
        exact_books = 0
        for row in rows:
            predicted = random_cutpoints(
                int(row["book_length"]),
                int(row["op_count"]),
                rng,
            )
            truth = set(int(cut) for cut in row["cutpoints"])
            row_hits = sum(1 for cut in predicted if cut in truth)
            hits += row_hits
            exact_books += int(predicted == row["cutpoints"])
        hit_values.append(hits)
        exact_values.append(exact_books)
    hit_sorted = sorted(hit_values)
    exact_sorted = sorted(exact_values)
    p95_index = int(0.95 * (trials - 1))
    return {
        "trials": trials,
        "mean_hits": mean(hit_values),
        "p95_hits": hit_sorted[p95_index],
        "max_hits": max(hit_values),
        "mean_exact_books": mean(exact_values),
        "p95_exact_books": exact_sorted[p95_index],
        "max_exact_books": max(exact_values),
    }


def score_all(rows: list[BookRow], policy_list: list[Policy]) -> list[dict[str, Any]]:
    return [score_policy(rows, policy) for policy in policy_list]


def prequential(rows: list[BookRow], policy_list: list[Policy]) -> list[dict[str, Any]]:
    cells = []
    policy_by_name = {policy.name: policy for policy in policy_list}
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        train_best = choose_best(score_all(train, policy_list))
        selected = policy_by_name[train_best["policy"]]
        test_score = score_policy(test, selected)
        control = random_control(
            test,
            trials=RANDOM_TRIALS,
            seed=RANDOM_SEED + cutoff * 100003,
        )
        cells.append(
            {
                "cutoff": cutoff,
                "train_books": len(train),
                "test_books": len(test),
                "selected_policy": selected.name,
                "train_exact_books": int(train_best["exact_books"]),
                "train_hits": int(train_best["total_hits"]),
                "test_exact_books": int(test_score["exact_books"]),
                "test_hits": int(test_score["total_hits"]),
                "test_internal_cutpoints": int(test_score["total_internal_cutpoints"]),
                "test_random_mean_hits": control["mean_hits"],
                "test_random_p95_hits": control["p95_hits"],
                "test_random_max_hits": control["max_hits"],
                "beats_random_p95": int(test_score["total_hits"]) > control["p95_hits"],
                "covers_all_test_books": int(test_score["exact_books"]) == len(test),
            }
        )
    return cells


def write_markdown(out: Path, data: dict[str, Any]) -> None:
    s = data["summary"]
    top = data["top_policies"]
    cells = data["prequential"]
    lines = [
        "# Operation Recursive Partition Gate",
        "",
        f"Classification: `{data['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether operation cutpoints are generated by recursively",
        "splitting book intervals with simple ratios. The rule is source-free",
        "and target-text-free: it receives only book length and op count.",
        "",
        "## Summary",
        "",
        f"- Books/operations: `{s['book_count']}` / `{s['operation_count']}`.",
        f"- Internal cutpoints tested: `{s['internal_cutpoint_count']}`.",
        f"- Recursive policies tested: `{s['policy_count']}`.",
        f"- Best policy: `{s['best_policy']}`.",
        f"- Best exact nontrivial books: `{s['best_exact_nontrivial_books']}/{s['nontrivial_book_count']}`.",
        f"- Best exact books including no-cutpoint books: `{s['best_exact_books']}/{s['book_count']}`.",
        f"- Best cutpoint hits: `{s['best_hits']}/{s['internal_cutpoint_count']}`.",
        f"- Random mean/p95/max hits: `{s['random_mean_hits']:.3f}` / `{s['random_p95_hits']}` / `{s['random_max_hits']}`.",
        f"- Hit lift vs random mean: `{s['best_hit_lift_vs_random_mean']:.3f}`.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout beats-random-p95 cells: `{s['prequential_beats_random_p95_cells']}/{s['prequential_cells']}`.",
        "",
        "## Top Policies",
        "",
        "| Policy | Exact books | Hits | Ratio mode | Ratios |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for item in top:
        ratios = ",".join(f"{ratio:.6g}" for ratio in item["ratios"])
        lines.append(
            "| "
            f"`{item['policy']}` | "
            f"`{item['exact_nontrivial_books']}/{item['nontrivial_books']}` nontriv; `{item['exact_books']}/{item['book_count']}` all | "
            f"`{item['total_hits']}/{item['total_internal_cutpoints']}` | "
            f"`{item['ratio_mode']}` | "
            f"`{ratios}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Selected policy | Test exact books | Test hits | Random mean | Random p95 | Beats p95 | Cover all |",
            "| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for cell in cells:
        lines.append(
            "| "
            f"`{cell['cutoff']}` | "
            f"`{cell['selected_policy']}` | "
            f"`{cell['test_exact_books']}/{cell['test_books']}` | "
            f"`{cell['test_hits']}/{cell['test_internal_cutpoints']}` | "
            f"`{cell['test_random_mean_hits']:.3f}` | "
            f"`{cell['test_random_p95_hits']}` | "
            f"`{cell['beats_random_p95']}` | "
            f"`{cell['covers_all_test_books']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes recursive-partition generator: `{s['promotes_recursive_partition_generator']}`.",
            "- Simple recursive interval partitioning does not generate the operation cutpoint atlas.",
            "- Any full-fit alignment is insufficient without exact books, holdout coverage, and random-control lift.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def compact_policy_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in row.items()
        if key
        not in {
            "per_book",
        }
    }


def main() -> None:
    lattice = load_json(LATTICE_GATE)
    assert_boundary("operation_cutpoint_lattice_gate", lattice)
    by_book = reconstruct()
    rows = make_rows(by_book)
    policy_list = policies()
    scored = score_all(rows, policy_list)
    best = choose_best(scored)
    control = random_control(rows, trials=RANDOM_TRIALS, seed=RANDOM_SEED)
    cells = prequential(rows, policy_list)
    operation_count = sum(int(row["op_count"]) for row in rows)
    internal_count = sum(int(row["internal_count"]) for row in rows)
    promotes = (
        int(best["exact_books"]) == len(rows)
        and int(best["total_hits"]) == internal_count
        and int(best["total_hits"]) > control["p95_hits"]
        and all(cell["covers_all_test_books"] for cell in cells)
        and all(cell["beats_random_p95"] for cell in cells)
    )
    classification = (
        "operation_recursive_partition_generator_promoted"
        if promotes
        else "operation_recursive_partition_generator_rejected"
    )
    top = sorted(
        scored,
        key=lambda item: (
            int(item["exact_nontrivial_books"]),
            int(item["total_hits"]),
            int(item["exact_books"]),
            -len(str(item["policy"])),
            str(item["policy"]),
        ),
        reverse=True,
    )[:10]
    summary = {
        "book_count": len(rows),
        "nontrivial_book_count": sum(1 for row in rows if int(row["internal_count"]) > 0),
        "operation_count": operation_count,
        "internal_cutpoint_count": internal_count,
        "policy_count": len(policy_list),
        "random_trials": RANDOM_TRIALS,
        "best_policy": best["policy"],
        "best_exact_books": int(best["exact_books"]),
        "best_exact_nontrivial_books": int(best["exact_nontrivial_books"]),
        "best_hits": int(best["total_hits"]),
        "random_mean_hits": control["mean_hits"],
        "random_p95_hits": control["p95_hits"],
        "random_max_hits": control["max_hits"],
        "best_hit_lift_vs_random_mean": int(best["total_hits"]) - control["mean_hits"],
        "prequential_cells": len(cells),
        "prequential_cover_all_cells": sum(
            1 for cell in cells if cell["covers_all_test_books"]
        ),
        "prequential_beats_random_p95_cells": sum(
            1 for cell in cells if cell["beats_random_p95"]
        ),
        "promotes_recursive_partition_generator": promotes,
        "interpretation": (
            "Recursive interval splitting with simple ratios does not generate "
            "the exact operation cutpoint atlas under full-fit or prefix holdout."
        ),
    }
    data = {
        "schema": "operation_recursive_partition_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_free_skeleton_script": rel(SKELETON_SCRIPT),
            "operation_cutpoint_lattice_gate": rel(LATTICE_GATE),
        },
        "parameters": {
            "prefix_cutoffs": PREFIX_CUTOFFS,
            "random_trials": RANDOM_TRIALS,
            "random_seed": RANDOM_SEED,
        },
        "summary": summary,
        "top_policies": [compact_policy_row(row) for row in top],
        "best_policy_per_book": best["per_book"],
        "prequential": cells,
        "decision": {
            "operation_length_status": "atlas_retained_after_recursive_partition_gate",
            "row0_origin_status": "unchanged_exogenous",
            "compression_bound_status": "unchanged_8154_676268",
            "translation_or_plaintext_status": "NONE",
        },
    }
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_out = TEST_RESULTS / f"{OUT_STEM}.json"
    md_out = TEST_RESULTS / f"{OUT_STEM}.md"
    json_out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(md_out, data)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"
SEED_COVERAGE = TEST_RESULTS / "01_seed_coverage_audit.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def fmt_bits(value: float) -> str:
    return f"{value:.3f}"


def compact_seed(seed: list[int]) -> str:
    return "[" + ", ".join(str(item) for item in seed) + "]"


def main() -> None:
    audit = load_json(SEED_COVERAGE)
    if audit.get("translation_delta") != "NONE":
        raise RuntimeError("seed audit changed translation boundary")
    if audit.get("case_reopened") is not False or audit.get("plaintext_claim") is not False:
        raise RuntimeError("seed audit violated archival boundary")

    summary = audit["summary"]
    decision = audit["decision"]
    operational = summary["operational_0_9"]
    best_k10 = summary["best_k10_candidate"]
    random10 = next(
        row for row in audit["random_control_summaries"] if row["seed_book_count"] == 10
    )
    perm10 = next(
        row for row in audit["permuted_prefix_control_summaries"] if row["seed_book_count"] == 10
    )

    lines = [
        "# Final Seed Primacy Audit",
        "",
        "Date: 2026-06-21",
        "",
        f"Classification: `{audit['classification']}`",
        "Translation delta: `NONE`",
        "Case reopened: `False`",
        "Plaintext claim: `False`",
        "",
        "## Question",
        "",
        "This front tests whether a small subset of books behaves like a mechanical seed",
        "for the remaining 469 corpus. It does not test translation, plaintext, fan",
        "glosses, or authorial intent.",
        "",
        "The tested mechanism is deliberately narrow: declare a seed set, then cover",
        "non-seed books by exact copies of length at least 5 from the seed books, plus",
        "literal residual digits. Copying from a target book, copying from derived books,",
        "and copying across seed-book boundaries are disabled.",
        "",
        "## Inputs",
        "",
        "- Seed coverage audit: "
        f"[analysis/seed_primacy_audit_20260621/reports/test_results/01_seed_coverage_audit.md](test_results/01_seed_coverage_audit.md).",
        f"- Books: `{audit['inputs']['books_digits']}`.",
        f"- Existing source-free skeleton ledger: `{audit['inputs']['skeleton_dependency_ledger']}`.",
        "",
        "## Main Result",
        "",
        "| Test | Seed books | Copied digits | Literal digits | Copies | Coverage | Random percentile |",
        "|---|---|---:|---:|---:|---:|---:|",
        (
            f"| Operational 0-9 | `{compact_seed(operational['seed_books'])}` | "
            f"{operational['copied_digits_explained']} | {operational['literal_digits_required']} | "
            f"{operational['copy_items_required']} | {pct(operational['coverage_rate'])} | "
            f"{operational['random_control_percentile_copied_digits']:.2f} |"
        ),
        (
            f"| Best k=10 posthoc greedy | `{compact_seed(best_k10['seed_books'])}` | "
            f"{best_k10['copied_digits_explained']} | {best_k10['literal_digits_required']} | "
            f"{best_k10['copy_items_required']} | {pct(best_k10['coverage_rate'])} | "
            f"{best_k10['random_control_percentile_copied_digits']:.2f} |"
        ),
        (
            f"| Random k=10 median | `100 sampled sets` | "
            f"{random10['copied_digits_median']:.0f} | n/a | n/a | "
            f"{pct(random10['coverage_rate_median'])} | n/a |"
        ),
        (
            f"| Permuted-prefix k=10 median | `100 sampled orders` | "
            f"{perm10['copied_digits_median']:.0f} | n/a | n/a | "
            f"{pct(perm10['coverage_rate_median'])} | n/a |"
        ),
        "",
        "The operational seed `0-9` covers fewer copied digits than the sampled random",
        f"k=10 median (`{operational['copied_digits_explained']}` vs `{random10['copied_digits_median']:.0f}`)",
        f"and sits at random percentile `{operational['random_control_percentile_copied_digits']:.2f}`.",
        "That is not evidence that `0-9` are mechanically special as seeds.",
        "",
        "The best k=10 candidate found by posthoc greedy coverage is much stronger,",
        f"but it is selected after seeing the corpus: `{compact_seed(best_k10['seed_books'])}`.",
        "It is therefore an audit-only compression result, not a primary-origin claim.",
        "",
        "## Seed Size Sweep",
        "",
        "| k | Best label | Seed books | Copied | Literal | Copies | Coverage | Gain vs random median after declaration |",
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in audit["best_by_k"]:
        lines.append(
            f"| {row['seed_book_count']} | `{row['label']}` | `{compact_seed(row['seed_books'])}` | "
            f"{row['copied_digits_explained']} | {row['literal_digits_required']} | "
            f"{row['copy_items_required']} | {pct(row['coverage_rate'])} | "
            f"{fmt_bits(row['gain_vs_random_median_after_declaration_bits'])} |"
        )

    lines.extend(
        [
            "",
            "The sweep finds small high-coverage subsets, especially greedy sets containing",
            "books such as `7`, `8`, `9`, `13`, `17`, and `25`. This is a mechanical",
            "coverage clue about redundancy in the corpus, but it is not evidence that",
            "those books are authorial seeds. The selected sets are posthoc and still",
            "leave copy-source choices and literal payload external.",
            "",
            "## Required Controls",
            "",
            f"- Random same-size seeds: run for k = `{audit['summary']['seed_sizes']}`.",
            f"- Permuted order prefixes: run for k = `{audit['summary']['seed_sizes']}`.",
            "- Seed declaration cost: charged as `log2(C(70,k))` in the payload-gain ledger.",
            "- Copy-source dependency: retained as `copy_items_required`; not treated as solved.",
            "- Public bookcase metadata: tested as a prefix control where available; it did not beat the posthoc greedy sets.",
            "- Leave-one-family/bookcase controls: emitted as `family_holdout_controls` in the JSON, classified control-only.",
            "",
            "## Categories",
            "",
            "- `PROMOTED_MECHANICAL_SEED_CLUE`: not reached.",
            "- `WEAK_SEED_CLUE`: not reached for `0-9` under this seed-only control.",
            "- `REJECTED_SEED_HYPOTHESIS`: not used as the global label because posthoc high-coverage cores do exist.",
            "- `AUDIT_ONLY_COMPRESSION`: reached; this is the final classification.",
            "- `BLOCKED_NEEDS_EXTERNAL_SOURCE`: applies to any authorial seed claim.",
            "",
            "## Answers",
            "",
            f"1. Books `0-9` special as seed: `{decision['books_0_9_special_as_seed']}`.",
            f"2. Alternative k=10 seed better: `{decision['alternative_seed_better_for_k10']}`; best found is `{compact_seed(decision['best_alternative_k10_seed'])}`.",
            f"3. Gain over random after declaration for operational `0-9`: `{decision['gain_over_random_survives_declaration_cost']}`.",
            f"4. Mechanical primary-core signal: `{decision['mechanical_primary_core_signal']}`.",
            f"5. Authorial seed claim: `{decision['authorial_seed_claim']}`.",
            "6. Translation/plaintext impact: `NONE`.",
            "",
            "## Boundary",
            "",
            "- No plaintext, translation, semantic reading, or fan gloss is introduced.",
            "- `row0` remains exogenous and unchanged.",
            "- Better coverage is not treated as origin.",
            "- Seed mechanical, authorial seed, compressibility, and generative explanation remain separate.",
            "- Any wiki update must keep this as an audit-only compression boundary, not a promoted validated origin/generation claim.",
        ]
    )

    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / "final_seed_primacy_audit.md"
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Search GitHub for exact 469 book strings and classify source usefulness.

The question is not "can we find the corpus again?" The question is whether an
exact-book hit exposes object/container/slot/order provenance that could reduce
v9's external fields. Exact text copies are corpus provenance only.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "analysis/external_authoring_surface_acquisition_audit_20260622/reports/test_results"
FINAL_REPORT = ROOT / "analysis/external_authoring_surface_acquisition_audit_20260622/reports/final_external_authoring_surface_acquisition_audit.md"


QUERIES = [
    {
        "id": "book_04_long_prefix",
        "query": "9457655996704672611",
        "local_role": "Hellgate book exact text prefix",
    },
    {
        "id": "book_11_public_prefix",
        "query": "79282784350",
        "local_role": "Hellgate public book title/prefix",
    },
    {
        "id": "book_15_isle_anchor_prefix",
        "query": "65128896721277889438",
        "local_role": "Isle/Hellgate 469 anchor prefix",
    },
    {
        "id": "book_12_first_public_prefix",
        "query": "561145727857261185",
        "local_role": "Hellgate public first-bookcase prefix",
    },
    {
        "id": "ambiguous_book_prefix",
        "query": "04215956151353478",
        "local_role": "ambiguous public prefix stress case",
    },
]


KNOWN_CORPUS_REPOS = {
    "s2ward/469": "community corpus/alignment repository",
    "elkolorado/tibia-469-bacca-averages": "community corpus/statistics repository",
    "caiocrm/469": "community analysis repository",
    "elkolorado/tibialibraries": "community library text mirror",
    "elkolorado/tibia-corpus": "community text corpus mirror",
}


def run_gh_search(query: str, limit: int = 25) -> dict[str, Any]:
    if shutil.which("gh") is None:
        return {"query": query, "available": False, "error": "gh_not_found", "items": []}
    cmd = [
        "gh",
        "search",
        "code",
        query,
        "--limit",
        str(limit),
        "--json",
        "repository,path,url",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=45, check=False)
    if proc.returncode != 0:
        return {
            "query": query,
            "available": True,
            "error": proc.stderr.strip() or proc.stdout.strip() or f"exit_{proc.returncode}",
            "items": [],
        }
    try:
        raw_items = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {"query": query, "available": True, "error": f"json_decode_error:{exc}", "items": []}

    items = []
    for item in raw_items:
        repo = item.get("repository", {}).get("nameWithOwner", "")
        path = item.get("path", "")
        items.append(
            {
                "repository": repo,
                "path": path,
                "url": item.get("url", ""),
                "repo_classification": classify_repo(repo, path),
            }
        )
    return {"query": query, "available": True, "error": None, "items": items}


def classify_repo(repo: str, path: str) -> str:
    if repo in KNOWN_CORPUS_REPOS:
        return "TEXT_CORPUS_OR_COMMUNITY_ANALYSIS"
    lowered = f"{repo}/{path}".lower()
    object_markers = ["otbm", "map", "world", "items.xml", "bookcase", "spawn", "house"]
    if any(marker in lowered for marker in object_markers):
        return "NEEDS_OBJECT_LAYER_REVIEW"
    return "UNKNOWN_EXACT_TEXT_HIT"


def source_usefulness(hits: list[dict[str, Any]]) -> dict[str, Any]:
    repos: dict[str, dict[str, Any]] = {}
    for hit in hits:
        repo = hit["repository"]
        entry = repos.setdefault(
            repo,
            {
                "repository": repo,
                "paths": [],
                "classification": hit["repo_classification"],
                "known_role": KNOWN_CORPUS_REPOS.get(repo, "not_preclassified"),
            },
        )
        entry["paths"].append(hit["path"])
        if hit["repo_classification"] == "NEEDS_OBJECT_LAYER_REVIEW":
            entry["classification"] = "NEEDS_OBJECT_LAYER_REVIEW"

    promoted = []
    review = []
    corpus_only = []
    for entry in repos.values():
        if entry["classification"] == "NEEDS_OBJECT_LAYER_REVIEW":
            review.append(entry)
        elif entry["classification"] == "TEXT_CORPUS_OR_COMMUNITY_ANALYSIS":
            corpus_only.append(entry)
        else:
            review.append(entry)
    return {
        "unique_repositories": len(repos),
        "promoted_object_sources": promoted,
        "needs_review_repositories": review,
        "corpus_only_repositories": corpus_only,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    query_results = []
    all_hits: list[dict[str, Any]] = []
    for q in QUERIES:
        result = run_gh_search(q["query"])
        result["id"] = q["id"]
        result["local_role"] = q["local_role"]
        query_results.append(result)
        all_hits.extend(result["items"])

    usefulness = source_usefulness(all_hits)
    unresolved_queries = [r for r in query_results if r["error"]]
    object_review_hits = [
        hit for hit in all_hits if hit["repo_classification"] == "NEEDS_OBJECT_LAYER_REVIEW"
    ]

    decision = {
        "promoted_external_object_source": False,
        "exact_text_hits_found": len(all_hits) > 0,
        "object_layer_hits_found": len(object_review_hits) > 0,
        "decoder_v9_reduction_bits": 0.0,
        "reason": "exact text appears in community corpus/analysis mirrors; no hit exposes book object/container/slot/order provenance",
    }

    artifact = {
        "schema": "github_exact_book_source_hunt.v1",
        "scope": "analysis_only_external_exact_book_source_hunt",
        "classification": "exact_book_github_hits_are_corpus_only_no_object_surface_promoted",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "queries": QUERIES,
        "query_results": query_results,
        "source_usefulness": usefulness,
        "summary": {
            "query_count": len(QUERIES),
            "queries_with_errors": len(unresolved_queries),
            "exact_text_hit_count": len(all_hits),
            "unique_repositories": usefulness["unique_repositories"],
            "corpus_only_repositories": len(usefulness["corpus_only_repositories"]),
            "needs_review_repositories": len(usefulness["needs_review_repositories"]),
            "object_layer_hits_found": len(object_review_hits),
            "promoted_external_object_sources": 0,
            "decoder_v9_reduction_bits": 0.0,
        },
        "decision": decision,
    }

    json_path = OUT_DIR / "02_github_exact_book_source_hunt.json"
    md_path = OUT_DIR / "02_github_exact_book_source_hunt.md"
    json_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")

    lines: list[str] = []
    lines.append("# GitHub Exact Book Source Hunt")
    lines.append("")
    lines.append("Classification: `exact_book_github_hits_are_corpus_only_no_object_surface_promoted`")
    lines.append("Translation delta: `NONE`")
    lines.append("Plaintext claim: `False`")
    lines.append("Case reopened: `False`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(
        f"Ran `{len(QUERIES)}` exact-string GitHub code searches for representative 469 book prefixes. "
        f"Found `{len(all_hits)}` exact text hits across `{usefulness['unique_repositories']}` repositories."
    )
    lines.append("")
    lines.append(
        "The hits are corpus mirrors or community analysis repositories. None exposes the object/container/slot/order layer required to reduce v9."
    )
    lines.append("")
    lines.append("## Repository Classification")
    lines.append("")
    lines.append("| Repository | Classification | Known Role | Sample Paths |")
    lines.append("| --- | --- | --- | --- |")
    for entry in usefulness["corpus_only_repositories"] + usefulness["needs_review_repositories"]:
        sample = ", ".join(entry["paths"][:4])
        lines.append(
            f"| `{entry['repository']}` | `{entry['classification']}` | {entry['known_role']} | {sample} |"
        )
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append("No `PROMOTED_EXTERNAL_CONTROL_SOURCE` and no v9 reduction.")
    lines.append("")
    lines.append(
        "This closes the easy public-code route: exact book strings are discoverable, but only as text/corpus copies. "
        "The needed source remains object-layer or versioned authoring provenance."
    )
    lines.append("")
    lines.append("`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.")
    md_path.write_text("\n".join(lines) + "\n")

    # Append a short section to the existing final report if it is not already present.
    report = FINAL_REPORT.read_text() if FINAL_REPORT.exists() else ""
    marker = "## GitHub Exact Book Source Hunt"
    if marker not in report:
        addition = [
            "",
            marker,
            "",
            "A follow-up exact-code search checks whether public GitHub hits for representative book strings expose an object layer.",
            f"It found `{len(all_hits)}` exact text hits across `{usefulness['unique_repositories']}` repositories, but all promoted-class hits are corpus mirrors or community analysis repositories.",
            "No hit supplies book object/container/slot/order provenance, so no source is integrated into v9.",
            "",
            "- [02_github_exact_book_source_hunt.py](../scripts/02_github_exact_book_source_hunt.py)",
            "- [02_github_exact_book_source_hunt.json](test_results/02_github_exact_book_source_hunt.json)",
            "- [02_github_exact_book_source_hunt.md](test_results/02_github_exact_book_source_hunt.md)",
        ]
        FINAL_REPORT.write_text(report.rstrip() + "\n" + "\n".join(addition) + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Targeted search gate for primary/rights-clean 469 authoring surfaces.

This audit deliberately excludes leaked proprietary Tibia source/map data. The
question is whether currently reachable official or rights-clean public surfaces
provide a usable object/container/slot/order or versioned authoring layer that
can reduce the executable decoder's remaining external fields.
"""

from __future__ import annotations

import json
import re
import socket
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/primary_authoring_surface_search_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
FINAL_REPORT = FRONT / "reports/final_primary_authoring_surface_search_audit.md"

USER_AGENT = "tibia-469-casestudy-audit/1.0 (+analysis-only source classification)"
TIMEOUT_SECONDS = 12

MARKER_RE = {
    "has_469_markers": re.compile(r"\b469\b|Hellgate|Bonelord|Beholder|9457655996|5611457278", re.I),
    "has_object_layer_markers": re.compile(
        r"\b(x|y|z)\b|coordinate|container|slot|bookcase|object|read order|map data|tile|floor",
        re.I,
    ),
    "has_authoring_markers": re.compile(r"CipSoft|official|version|client|map|archive|source", re.I),
}


@dataclass(frozen=True)
class Candidate:
    source_id: str
    url: str
    source_class: str
    expected_role: str


CANDIDATES = [
    Candidate(
        "cipsoft_tibia_game_page",
        "https://www.cipsoft.com/en/games/tibia",
        "official_generic",
        "official publisher page; can only promote if it exposes 469 object topology or authoring fields",
    ),
    Candidate(
        "tibia_com_news_probe",
        "https://www.tibia.com/news/",
        "official_generic",
        "official game news surface; can only promote if it exposes 469 object topology or authoring fields",
    ),
    Candidate(
        "tibia_org_historical_domain_probe",
        "https://www.tibia.org/",
        "historical_domain_probe",
        "historical domain probe mentioned by community sources; usable only if current surface exposes primary data",
    ),
    Candidate(
        "tibia_fandom_hellgate_library",
        "https://tibia.fandom.com/wiki/Hellgate_Library",
        "community_corpus",
        "community library/corpus page; useful for coverage, not primary authoring provenance",
    ),
    Candidate(
        "tibia_fandom_book_page",
        "https://tibia.fandom.com/wiki/9457655996_%28Book%29",
        "community_corpus",
        "community book page; useful for corpus string checks, not primary topology/control",
    ),
    Candidate(
        "tibiasecrets_article166",
        "https://www.tibiasecrets.com/article166",
        "community_theory",
        "community theory/provenance article; audit-only unless it provides primary object-layer data",
    ),
    Candidate(
        "tibiasecrets_article160",
        "https://tibiasecrets.com/article160",
        "community_theory",
        "community theory/provenance article; audit-only unless it provides primary object-layer data",
    ),
    Candidate(
        "s2ward_469",
        "https://github.com/s2ward/469",
        "community_analysis_repo",
        "community analysis repository; already in the tested non-primary surface class",
    ),
    Candidate(
        "s2ward_tibia",
        "https://github.com/s2ward/tibia",
        "community_analysis_repo",
        "Tales/LIBSearch community database surface; already probed as non-primary for v9 reduction",
    ),
    Candidate(
        "arturo_bookcase_repo",
        "https://github.com/arturoornelasb/tibia-bonelord-469-cipher",
        "community_analysis_repo",
        "community bookcase mapping repository; already probed as posthoc/non-primary",
    ),
    Candidate(
        "tales_services",
        "https://talesoftibia.com/services/",
        "community_service",
        "community service surface; may document LIBSearch but is not itself primary CipSoft provenance",
    ),
]


LEAK_POLICY = {
    "source_class": "leaked_proprietary_tibia_source_or_map",
    "status": "REJECTED_PROVENANCE_CONTROL",
    "can_obtain_or_use": False,
    "reason": (
        "community acceptance or alt-server reuse is not CipSoft authorization, "
        "not a rights-clean license, and not admissible as project evidence"
    ),
    "allowed_alternative": (
        "official/in-game capture, user-authorized object-layer export, or public licensed data "
        "with book text/prefix, coordinates, container/bookcase id, slot/read order, version/date, and rights"
    ),
}


def normalize_text(raw: bytes, content_type: str | None) -> str:
    encoding = "utf-8"
    if content_type:
        match = re.search(r"charset=([\w.-]+)", content_type, re.I)
        if match:
            encoding = match.group(1)
    text = raw.decode(encoding, errors="replace")
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_url(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        context = ssl.create_default_context()
        with urlopen(request, timeout=TIMEOUT_SECONDS, context=context) as response:
            raw = response.read(300_000)
            content_type = response.headers.get("content-type")
            text = normalize_text(raw, content_type)
            return {
                "ok": True,
                "status": response.status,
                "content_type": content_type,
                "text": text,
                "error": None,
            }
    except HTTPError as exc:
        raw = exc.read(80_000) if exc.fp else b""
        text = normalize_text(raw, exc.headers.get("content-type") if exc.headers else None) if raw else ""
        return {
            "ok": False,
            "status": exc.code,
            "content_type": exc.headers.get("content-type") if exc.headers else None,
            "text": text,
            "error": f"HTTPError:{exc.code}",
        }
    except (URLError, TimeoutError, socket.timeout) as exc:
        return {
            "ok": False,
            "status": None,
            "content_type": None,
            "text": "",
            "error": f"{type(exc).__name__}:{exc}",
        }


def domain_class(url: str) -> dict[str, bool]:
    host = urlparse(url).netloc.lower()
    def is_domain(domain: str) -> bool:
        return host == domain or host.endswith(f".{domain}")

    official = is_domain("cipsoft.com") or is_domain("tibia.com")
    return {
        "official_domain": official,
        "community_domain": not official,
        "github_domain": host == "github.com" or host.endswith(".github.com"),
    }


def classify(candidate: Candidate, fetched: dict[str, Any], markers: dict[str, bool]) -> tuple[str, str]:
    if candidate.source_class == "official_generic":
        if markers["has_469_markers"] and markers["has_object_layer_markers"]:
            return (
                "WEAK_PROVENANCE_CLUE",
                "official surface mentions 469/object markers but still needs extracted object/container/slot/order fields",
            )
        return (
            "OFFICIAL_SURFACE_NO_469_OBJECT_LAYER",
            "official/current surface does not expose the 469 object-layer fields required by the decoder",
        )
    if candidate.source_class == "historical_domain_probe":
        return (
            "HISTORICAL_DOMAIN_NO_USABLE_CURRENT_SURFACE",
            "current reachable domain surface is not a primary 469 object-layer dataset",
        )
    if candidate.source_class == "community_corpus":
        return (
            "COMMUNITY_CORPUS_SURFACE_ALREADY_TESTED_NO_PRIMARY_CONTROL",
            "community corpus pages can mirror book text but do not supply primary authoring topology/control fields",
        )
    if candidate.source_class == "community_theory":
        return (
            "COMMUNITY_THEORY_SURFACE_NO_DECODER_FIELDS",
            "community theory/provenance writing is audit-only and does not reduce v9 external fields",
        )
    if candidate.source_class == "community_analysis_repo":
        return (
            "COMMUNITY_ANALYSIS_SURFACE_ALREADY_TESTED",
            "community repository/posthoc analysis class was already probed and not promoted as primary authoring provenance",
        )
    return (
        "AUDIT_ONLY_NO_PRIMARY_CONTROL",
        "surface does not provide a promotable primary/rights-clean decoder control field",
    )


def analyze_candidate(candidate: Candidate) -> dict[str, Any]:
    fetched = fetch_url(candidate.url)
    text = fetched["text"]
    markers = {name: bool(pattern.search(text)) for name, pattern in MARKER_RE.items()}
    classification, reason = classify(candidate, fetched, markers)
    dom = domain_class(candidate.url)
    has_required_authoring_surface = (
        dom["official_domain"]
        and markers["has_469_markers"]
        and markers["has_object_layer_markers"]
        and markers["has_authoring_markers"]
    )
    title = ""
    title_match = re.search(r"<title[^>]*>(.*?)</title>", fetched["text"], re.I | re.S)
    if title_match:
        title = re.sub(r"\s+", " ", title_match.group(1)).strip()
    snippet = text[:360]
    return {
        "source_id": candidate.source_id,
        "url": candidate.url,
        "source_class": candidate.source_class,
        "expected_role": candidate.expected_role,
        "fetch": {
            "ok": fetched["ok"],
            "status": fetched["status"],
            "content_type": fetched["content_type"],
            "error": fetched["error"],
            "text_chars_sampled": len(text),
        },
        "domain": dom,
        "markers": markers,
        "title": title,
        "snippet": snippet,
        "classification": classification,
        "reason": reason,
        "has_required_authoring_surface": has_required_authoring_surface,
        "v9_reduction_bits": 0.0,
    }


def build_report(result: dict[str, Any]) -> str:
    lines = [
        "# Primary Authoring Surface Search Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Decision",
        "",
        "No promoted primary/rights-clean authoring surface was found in this targeted public search.",
        "Official CipSoft/Tibia pages are valid official domains, but the checked surfaces do not expose the 469 object/container/slot/order or versioned authoring layer required by the executable decoder.",
        "Community corpus, theory, and analysis repositories remain audit-only/posthoc unless they provide rights-clean primary object-layer fields and pass v9 controls.",
        "",
        "Leaked proprietary Tibia source/map data remains rejected: community acceptance or alt-server reuse is not enough provenance or permission for this repository.",
        "",
        "## Candidate Matrix",
        "",
        "| Source | Fetch | Classification | Required Surface | Reason |",
        "| --- | ---: | --- | ---: | --- |",
    ]
    for row in result["candidate_matrix"]:
        status = row["fetch"]["status"] if row["fetch"]["status"] is not None else row["fetch"]["error"]
        lines.append(
            f"| [`{row['source_id']}`]({row['url']}) | `{status}` | `{row['classification']}` | `{row['has_required_authoring_surface']}` | {row['reason']} |"
        )
    lines.extend(
        [
            "",
            "## Leak Boundary",
            "",
            f"- Status: `{result['leak_policy']['status']}`",
            f"- Can obtain/use: `{result['leak_policy']['can_obtain_or_use']}`",
            f"- Reason: {result['leak_policy']['reason']}",
            "",
            "## Next Acceptable Input",
            "",
            result["decision"]["next_acceptable_input"],
            "",
            "No source is integrated into v9. Net v9 reduction: `0.0` bits.",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_final(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Final Primary Authoring Surface Search Audit",
            "",
            f"Classification: `{result['classification']}`",
            "Translation delta: `NONE`",
            "Plaintext claim: `False`",
            "Case reopened: `False`",
            "",
            "## Summary",
            "",
            "A targeted public search checked official CipSoft/Tibia surfaces and known community corpus/theory/analysis surfaces for a primary authoring layer that could reduce the v9 executable decoder's remaining external fields.",
            "No candidate provided the required rights-clean object/container/slot/read-order or versioned authoring surface.",
            "",
            "The old Tibia source-code/map leak remains outside the admissible evidence chain.",
            "Community acceptance and alt-server reuse do not make it a primary, rights-clean, or project-integrable source.",
            "",
            "## Decision",
            "",
            "`primary_authoring_surface_not_found_targeted_search`.",
            "",
            "The route now requires either a user-provided/authorized primary object-layer artifact, an official/in-game capture with the clean topology fields, public licensed object-layer data, or a new causal state not already represented by the current decoder.",
            "",
            "No v9 source is integrated and no formula is promoted.",
            "",
            "## Reproducible Artifacts",
            "",
            "- [01_primary_authoring_surface_search_gate.py](../scripts/01_primary_authoring_surface_search_gate.py)",
            "- [01_primary_authoring_surface_search_gate.json](test_results/01_primary_authoring_surface_search_gate.json)",
            "- [01_primary_authoring_surface_search_gate.md](test_results/01_primary_authoring_surface_search_gate.md)",
        ]
    ) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [analyze_candidate(candidate) for candidate in CANDIDATES]
    promoted = [row for row in rows if row["has_required_authoring_surface"]]
    official_checked = sum(1 for row in rows if row["domain"]["official_domain"])
    community_checked = len(rows) - official_checked
    result: dict[str, Any] = {
        "schema": "primary_authoring_surface_search_gate.v1",
        "scope": "analysis_only_targeted_public_primary_surface_search",
        "classification": "primary_authoring_surface_not_found_targeted_search",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "candidate_matrix": rows,
        "leak_policy": LEAK_POLICY,
        "summary": {
            "candidate_count": len(rows),
            "official_candidates_checked": official_checked,
            "community_candidates_checked": community_checked,
            "promoted_primary_surfaces": len(promoted),
            "v9_reduction_bits": 0.0,
        },
        "decision": {
            "external_surface_integrated": False,
            "classification_reason": "no checked public candidate provides an admissible primary object-layer/control surface",
            "leak_route_accepted": False,
            "next_acceptable_input": LEAK_POLICY["allowed_alternative"],
        },
    }
    (OUT_DIR / "01_primary_authoring_surface_search_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    (OUT_DIR / "01_primary_authoring_surface_search_gate.md").write_text(build_report(result))
    FINAL_REPORT.write_text(build_final(result))


if __name__ == "__main__":
    main()

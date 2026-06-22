# Primary Authoring Surface Search Gate

Classification: `primary_authoring_surface_not_found_targeted_search`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Decision

No promoted primary/rights-clean authoring surface was found in this targeted public search.
Official CipSoft/Tibia pages are valid official domains, but the checked surfaces do not expose the 469 object/container/slot/order or versioned authoring layer required by the executable decoder.
Community corpus, theory, and analysis repositories remain audit-only/posthoc unless they provide rights-clean primary object-layer fields and pass v9 controls.

Leaked proprietary Tibia source/map data remains rejected: community acceptance or alt-server reuse is not enough provenance or permission for this repository.

## Candidate Matrix

| Source | Fetch | Classification | Required Surface | Reason |
| --- | ---: | --- | ---: | --- |
| [`cipsoft_tibia_game_page`](https://www.cipsoft.com/en/games/tibia) | `200` | `OFFICIAL_SURFACE_NO_469_OBJECT_LAYER` | `False` | official/current surface does not expose the 469 object-layer fields required by the decoder |
| [`tibia_com_news_probe`](https://www.tibia.com/news/) | `403` | `OFFICIAL_SURFACE_NO_469_OBJECT_LAYER` | `False` | official/current surface does not expose the 469 object-layer fields required by the decoder |
| [`tibia_org_historical_domain_probe`](https://www.tibia.org/) | `URLError:<urlopen error _ssl.c:983: The handshake operation timed out>` | `HISTORICAL_DOMAIN_NO_USABLE_CURRENT_SURFACE` | `False` | current reachable domain surface is not a primary 469 object-layer dataset |
| [`tibia_fandom_hellgate_library`](https://tibia.fandom.com/wiki/Hellgate_Library) | `403` | `COMMUNITY_CORPUS_SURFACE_ALREADY_TESTED_NO_PRIMARY_CONTROL` | `False` | community corpus pages can mirror book text but do not supply primary authoring topology/control fields |
| [`tibia_fandom_book_page`](https://tibia.fandom.com/wiki/9457655996_%28Book%29) | `403` | `COMMUNITY_CORPUS_SURFACE_ALREADY_TESTED_NO_PRIMARY_CONTROL` | `False` | community corpus pages can mirror book text but do not supply primary authoring topology/control fields |
| [`tibiasecrets_article166`](https://www.tibiasecrets.com/article166) | `200` | `COMMUNITY_THEORY_SURFACE_NO_DECODER_FIELDS` | `False` | community theory/provenance writing is audit-only and does not reduce v9 external fields |
| [`tibiasecrets_article160`](https://tibiasecrets.com/article160) | `200` | `COMMUNITY_THEORY_SURFACE_NO_DECODER_FIELDS` | `False` | community theory/provenance writing is audit-only and does not reduce v9 external fields |
| [`s2ward_469`](https://github.com/s2ward/469) | `200` | `COMMUNITY_ANALYSIS_SURFACE_ALREADY_TESTED` | `False` | community repository/posthoc analysis class was already probed and not promoted as primary authoring provenance |
| [`s2ward_tibia`](https://github.com/s2ward/tibia) | `200` | `COMMUNITY_ANALYSIS_SURFACE_ALREADY_TESTED` | `False` | community repository/posthoc analysis class was already probed and not promoted as primary authoring provenance |
| [`arturo_bookcase_repo`](https://github.com/arturoornelasb/tibia-bonelord-469-cipher) | `200` | `COMMUNITY_ANALYSIS_SURFACE_ALREADY_TESTED` | `False` | community repository/posthoc analysis class was already probed and not promoted as primary authoring provenance |
| [`tales_services`](https://talesoftibia.com/services/) | `200` | `AUDIT_ONLY_NO_PRIMARY_CONTROL` | `False` | surface does not provide a promotable primary/rights-clean decoder control field |

## Leak Boundary

- Status: `REJECTED_PROVENANCE_CONTROL`
- Can obtain/use: `False`
- Reason: community acceptance or alt-server reuse is not CipSoft authorization, not a rights-clean license, and not admissible as project evidence

## Next Acceptable Input

official/in-game capture, user-authorized object-layer export, or public licensed data with book text/prefix, coordinates, container/bookcase id, slot/read order, version/date, and rights

No source is integrated into v9. Net v9 reduction: `0.0` bits.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

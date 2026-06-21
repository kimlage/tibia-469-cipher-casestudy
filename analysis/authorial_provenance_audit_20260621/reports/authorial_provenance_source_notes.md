# Authorial Provenance Source Notes

Status: `analysis_only`

Translation delta: `NONE`

Plaintext claim: `false`

Case reopened: `false`

This note records source material useful for authorial/provenance reasoning
around Knightmare, Chayenne, and the public 469 framing. It does not promote a
translation, plaintext, row0 origin, or semantic reading.

## Source Ledger

| source | type | useful data | allowed use | limits |
| --- | --- | --- | --- | --- |
| [PortalTibia Chayenne interview, 2009](https://forum.portaltibia.com.br/topic/11420-entrevista-com-chayenne/) | `PRIMARY_INTERVIEW_SOURCE` | Chayenne answers a direct question about the beholder language with two numeric blocks separated by a visible emoticon/image marker and followed by `xD`; she also states language familiarity with German, English, French, fragments of Japanese/Swedish/Orcish/Chakoya, and uses `xD` / `^^;` as favorite emoticons. | Primary evidence for the numeric blocks and the visible separator between them. | No gloss is given. It is not a book->plaintext pair and does not attest a codebook; the exact rendered emoticon is not treated as a canonical byte. |
| [TibiaWiki BR 469 stable page](https://www.tibiawiki.com.br/index.php?stableid=140740&title=469) | `SECONDARY_INDEX` | Records the Chayenne string and frames it as a joke that the language could be translated; also lists common 469 lore hooks such as Knightmare, 15th anniversary, Excalibug, and Wrinkled Bonelord quotes. | Useful source map and cross-reference target. | Secondary page, not primary authority for mechanics or authorship. |
| [s2ward/469 GitHub issue 3](https://github.com/s2ward/469/issues/3) | `COMMUNITY_HYPOTHESIS` | Tests the idea that the Chayenne string might encode binary/5-bit blinking, and observes alignment/padding problems. | Negative-control reference for the 5-eye/binary line of thought. | Community speculation; not evidence for translation or source origin. |
| [SolvingTibia Reddit thread](https://www.reddit.com/r/SolvingTibia/comments/tkam3x/469_a_language_blinked_between_entities/) | `COMMUNITY_SYNTHESIS` | Collects Chayenne, Wrinkled Bonelord, and community hypotheses about 469. | Useful as a map of known public claims and fan theories to audit. | Not primary evidence and not promotable without independent support. |
| [Knightmare profile](https://tibia.fandom.com/wiki/Knightmare) | `AUTHORIAL_CONTEXT` | Public fan-wiki summary of Knightmare as a former content designer and Tibia lore figure. | Broad context for why Knightmare is treated as relevant to the lore/mechanics question. | Not primary proof that he authored row0 or any specific 469 formula. |
| [Rookie interview with Knightmare, 2016](https://rookie.com.pl/blog/14/interview-with-knightmare) | `AUTHORIAL_CONTEXT` | Provides public statements about quest/lore design mindset, mystery, and long-lived Tibia content design. | Context for plausible design style and era constraints. | Does not attest a 469 solution or numeric generation method. |
| [Rookie interview with Knightmare, later](https://rookie.com.pl/blogs/890/interview-with-knightmare) | `AUTHORIAL_CONTEXT` | Additional public statements about old-school Tibia design and player-facing mystery. | Context only. | Does not provide a 469 formula. |
| [CipSoft company page](https://www.cipsoft.com/en/company) and [team page](https://www.cipsoft.com/en/company/team) | `TOOLING_CONTEXT` | Confirms long-running CipSoft/Tibia context and modern company framing. | Background for capability/era discussion. | Modern company pages do not identify the 469 authorial method. |

## Hypothesis Matrix

| hypothesis | current status | basis | blocker |
| --- | --- | --- | --- |
| Chayenne visible separator marks a join between two existing book substrings | `PROMOTED_MECHANICAL_CLUE` | The primary-source split is the only split of the joined 49-digit answer into two substrings attested in the committed 70-book corpus. | It explains a public surface boundary, not the origin of either substring. |
| Chayenne answer is word spacing or phrase segmentation | `REJECTED_CONTROL` | The two chunks occur separately as numeric modules; the joined string does not occur. There is no attested gloss. | Needs primary source with meaning or a reproducible external codebook. |
| Chayenne answer implies direct plaintext translation | `REJECTED_CONTROL` | No plaintext is supplied by Chayenne, and the answer is framed publicly with emoticons. | Needs CipSoft/in-game book->plaintext or symbol table evidence. |
| 5-eye/binary blinking decode of the Chayenne string | `REJECTED_CONTROL` | The raw block lengths and integer bit lengths do not align cleanly to stable 5-bit grouping; community tests also note padding/alignment failures. | Needs a deterministic, externally validated parsing rule. |
| Worksheet/script/module-copy provenance | `WEAK_CLUE` | Chayenne's two numeric blocks are both repeated corpus modules, while their concatenation is not attested. | This can suggest local reuse but does not identify the worksheet, script, or authorial source. |
| Row0 origin from Chayenne/Knightmare public statements | `BLOCKED_NEEDS_EXTERNAL_SOURCE` | The public sources do not provide a row0 table, rule, or derivation. | Needs primary CipSoft/in-game/source-file evidence. |

## Working Interpretation

The strongest new fact from the Chayenne surface is mechanical and narrow:
the visible source separator preserves a unique join between two
corpus-attested numeric modules. This supports a provenance/register clue:
the answer appears to reuse existing 469 book material rather than encode a
separate visible sentence with ordinary word boundaries.

This does not change row0, does not create a translation, and does not reopen
the case. It is useful because it turns the Chayenne quote into a controlled
test object rather than a lore anecdote.

# How to Use AI on a Hard Problem Without Fooling Yourself

### A case study: multi-agent adversarial verification vs. a decade-old game cipher

*An AI research harness spent weeks attacking "Bonelord 469," a cipher inside the MMORPG Tibia that has been publicly unsolved for over a decade. It did not solve it. That is the point. Along the way it caught itself believing a beautiful, complete, 100%-coverage "solution" that was wrong — and the way it caught itself is a method you can reuse on any analysis you run through a language model.*

---

> **Disclaimer.** This is an independent research case study. It is **not affiliated with, authorized by, or endorsed by CipSoft GmbH.** "Tibia" and "Bonelord" are trademarks of CipSoft GmbH, used here nominatively to identify the puzzle under study. No game assets, data files, or book corpora are reproduced; everything below is derived statistics, small re-typeset illustrative tables, and the handful of short phrase fragments already discussed publicly by the player community.

---

## The hook: the model gave us a perfect answer, and it was garbage

Here is the moment that makes this whole write-up worth reading.

We had a candidate solution to a cipher. It was a clean, homophonic two-digit-to-letter map. It decoded **all seventy** of the puzzle's encrypted "books" into readable German — towns, names, words: *Salzberg, Weichstein, Orangenstrasse.* One hundred percent mechanical coverage. No leftover symbols, no "unknown" tokens, nothing swept under a rug. If you had shown it to a layperson — or to a credulous LLM, or honestly to a tired human at 2 a.m. — they would have said: solved.

It was wrong. Not "slightly off." Wrong in the way that matters: it was **pattern-matching noise into language.**

The only reason we knew it was wrong is that we had built a system whose entire job was to *try to destroy our own conclusions before we got attached to them.* When we ran that gorgeous German map against two short phrases whose meaning we already had a handle on, it produced `LTENWEETLAED` where it needed to produce something like "be a wit." Zero overlap. The "solution" collapsed.

That collapse — a refuter and a set of controls killing a result that looked complete — is the actual product of this project. The cipher is a great story. The method is the thing you can take home.

## What "469" is

Inside Tibia, a long-running MMORPG, there is a faction of creatures called Bonelords, and they "speak" and "write" in numbers. Players have catalogued two kinds of artifact:

1. **NPC phrases** — short numeric utterances spoken by Bonelord characters, e.g. a Knightmare's line and an "Evil Eye" line.
2. **Books** — seventy longer strings of digits, presented in-world as written texts.

Together this is known in the community as "the 469 language" (after an in-game item, *book of necromantic rituals* numbered 469, that kicked the whole thing off). It has been picked at by players for more than a decade. Every serious community source — TibiaWiki, the most-developed fan analysis sites, the most authoritative public research repos — says the same thing: **unsolved.** "Closer than ever… remains a mystery." "No verified complete translations exist."

So it is a real, bounded, adversarial target: small enough to brute-force in some directions, hard enough that a decade of smart humans hasn't cracked it, and — crucially — **a place where wishful thinking is rampant**, because numbers-into-words is exactly the kind of task where the human brain (and a large language model) will hallucinate meaning on demand.

That last property is why it's a perfect stress test for AI-assisted analysis.

## Why naive approaches produce convincing nonsense

Give a modern LLM a string of digits and ask "what does this say?" and it will tell you. Confidently. It will find a mapping, apply it, and hand you sentences. This is not a bug you can prompt away; it is the *job* of a model trained to continue text plausibly. The danger isn't that the model lies. The danger is that **it succeeds at the wrong task** — producing fluent, plausible output — and you mistake fluency for correctness.

Decipherment is uniquely vicious here, for a reason worth internalizing because it generalizes far past games:

> When your search space is "all possible substitution maps" and your success metric is "looks like language," you can almost always find a map that wins the metric **by overfitting to the metric**, not by recovering truth.

There are an astronomical number of ways to assign symbols to letters. "Maximize English-likeness" sounds like a principled objective. But with enough symbols and enough freedom, you can squeeze readable-ish text out of *random* data. We proved this on our own puzzle: a **meaningless, random** 13-way merge of English letters fit the book's statistical shape *better* than any linguistically-motivated reduction we tried. The structure that "looked like a language" was an artifact of the optimization, not a signal in the data.

This is pareidolia — the same wiring that sees faces in clouds — running at the scale and speed of a compute cluster. And here's the kicker we hit directly: one string in the puzzle (a much-hyped "NARCISSIST" claim) decodes two completely different ways depending on how you read it. As a Bonelord book it "says" one thing; read as ASCII hex it spells `by herrera` (which turned out to be an unrelated domain-hijack joke). **One string, two confident, incompatible readings.** That is not a clue. That is a warning label. If your method can find meaning in a string two contradictory ways, your method finds meaning everywhere — which means it finds meaning nowhere.

So the entire engineering problem becomes: **how do you let an AI search aggressively for patterns while making it nearly impossible to fool yourself with the patterns it finds?**

## The method: parallel lanes, a refuter, and three controls

The harness has four moving parts. None of them is exotic. The discipline is in wiring them together and *refusing to let the optimistic part win on its own.*

### 1. Parallel agent lanes with structured outputs

Instead of one chat thread meandering toward an answer, the work is split into independent **lanes** — separate agent runs, each with a narrow assignment (test one hypothesis, audit one table, re-derive one statistic) and each required to return a **structured output**: not prose, but fields. A claim, the evidence, the control it beat, a confidence. Structured outputs matter because they make a result *checkable by another program* and stop an agent from burying a weak finding inside confident narration.

### 2. The Refuter — an agent whose only job is to attack

This is the load-bearing idea. We run a dedicated **Refuter** agent whose sole instruction is to *break* a candidate finding. It is not asked "is this right?" — a question models love to answer "yes" to. It is asked "here is a claim; find the reason it is false." And its default verdict is hostile: **if the refuter is uncertain, the claim is treated as refuted, not confirmed.**

Flip the burden of proof. In normal LLM usage the model is a helpful assistant trying to satisfy you, and "I found a solution!" is the satisfying answer. The Refuter inverts the incentive: the satisfying answer is "I knocked it down." You are no longer fighting the model's eagerness — you are *using* it, pointed at your own conclusions.

The refuter earned its keep. It caught two of our **own** mistakes (more below). Building the refutation step in was the single most consequential design choice.

### 3. Three controls — and you must beat the control's MAX

A "signal" only counts if it beats a baseline that *shouldn't* have signal. We ran three:

- **Null control** — random/uniform data of the same shape. If your "structure" doesn't beat noise, it isn't structure.
- **Self-anagram (permutation) control** — take a real encrypted book and *shuffle its own symbols*, keeping the exact multiset. This is the brutal one for decipherment: if your "readable decode" of the real text doesn't clearly beat a decode of a *scrambled* version of that same text, then your method is rewarding the letter *frequencies*, not the letter *order* — i.e., it's rewarding statistics, not language.
- **Holdout** — keep some ground truth back, fit on the rest, and see if your map predicts the held-out part.

The rule that makes controls bite: **you must beat the control's MAX, not its average.** When you draw many random baselines, the *best* of them is your real competitor, because over a big search you'll find a map that beats the average baseline by luck alone. Beating the max is a much higher, much more honest bar.

### 4. The Outcome Ledger — progress is outcome, not activity

The last piece is cultural, and it's the one most teams get wrong. This project had, by the end, accumulated staggering *machinery*: roughly 1,600 database tables, ~550 analysis scripts, tens of thousands of automated runs, hundreds of thousands of "candidate promotions." And its own honest scoreboard recorded: **zero** accepted human-readable book translations.

That gap has a name: **goal-substitution.** The system optimized *activity* — run another iteration, build another probe — because activity is easy to produce and feels like progress. Outcome stayed flat.

The fix is an **Outcome Ledger**: a short list of metrics that measure the *thing you actually want*, where iteration count, script count, and table count are **explicitly not progress.** For this puzzle the ledger tracked things like "cribs reproduced under holdout: 0," "codes confirmed against an external authoritative source (not our own decoder): 0." A round that moves none of those is logged, in plain language, as **"NEGATIVE / plateau confirmed"** — recorded as a *valid outcome*, not a failure to paper over. Decoder self-output and fan guesses are inadmissible as evidence. You don't get to grade your own homework.

## The dramatic moment: rejecting the 100% German "solution"

Now the payoff. Someone in the wider community had published what looked like a finished answer: a homophonic two-digit-to-German map (about 98 codes onto 22 letters) that decoded every one of the seventy books into German text. Surface coverage: total. It is, genuinely, an impressive piece of work, and it *looks* like a solution in every superficial way.

Our system put it through the gate.

- **It failed the cribs.** Applied to the short phrases we had independent handles on, the German map produced `LTENWEETLAED` where the community reading is "be a wit." Zero overlap. A real key opens the locks you already know the shape of; this one didn't.
- **Its outputs had no external support.** The decoded town and proper names had no primary corroboration in the game's actual lore.
- **Its own author disclaimed it.** The repository's README admitted, in writing, "I cannot confirm that the decoded content is the actual intended plaintext," and flagged an "overfitting concern."

So we rejected it. A complete, fluent, zero-leftover decode — refused, because it failed two short independent tests it had no way to fake.

Sit with how counterintuitive that is. The "more impressive" the output (100% coverage!), the *more* suspicious it should make you, because total coverage on an unsolved problem usually means the method has enough freedom to fit anything. **Rejecting the beautiful answer was the most scientifically valuable thing the project ever did.** It is exactly the discipline that separates decipherment from astrology.

## What we did find: two ciphers, not one

Negatives aren't the only result. We did establish a real structural finding with reasonable confidence: **469 is not one cipher, it's two unrelated systems.**

- **The phrases** are *word-codes*: variable-length groups of digits stand for whole words, homophonically (more than one code can mean the same word). From the public Knightmare, Evil Eye, and Elder Bonelord lines, a small internally-consistent codebook falls out:

  | Code (digits) | Word | From phrase |
  |---|---|---|
  | 3478 / 3466 | be | Knightmare |
  | 67 / 0 | a | Knightmare |
  | 90871 | wit | Knightmare |
  | 653 | look | Evil Eye |
  | 768 | at | Evil Eye |
  | 764 | you | Evil Eye / Elder Bonelord |
  | 659 | let | Elder Bonelord |

  *(Illustrative subset, re-typeset. Two codes can spell the same word; that's the homophony.)*

  The honest limit: of all these codes, **exactly one — `764` = "you" — recurs across more than one phrase.** Every other code appears in a single line. That is a thin, brittle generalization, and we say so.

- **The books** use a *completely different* system: a fixed two-digit code maps to one of fourteen symbols. We can prove the books don't use the phrase word-codes at all — the long phrase codes that should appear if they did show up in **zero of seventy** books, far below chance. Whatever the books are, they are not the phrases written long.

## The verified verdict on the books: non-linguistic — and that's a real result

Here is the finding we're most confident in, and it's a *negative*: **the seventy books do not decode to any natural language.** This is not "we got tired." It is five disqualifiers — spanning three independent axes — that all point the same way, each one re-derived from scratch and checked against controls:

1. **The symbol-frequency profile is closer to flat-random than to any language.** Measuring statistical distance from uniform/random and from real languages, the ordering came out **uniform (≈3691) < English (≈4296) < German (≈4850) < Spanish (≈9408)**. The *random* baseline fits the books *better* than English does. Languages don't do that.
2. **Individual symbol frequencies are language-disqualifying.** One symbol runs ~10% where the corresponding letter is ~2–3% in real languages; another runs ~6.6% where it's ~1%; the most common symbol hits ~20.6%, higher than any natural-language letter; meanwhile two symbols that should be common (the analogues of R and O) are near-absent. No language has this fingerprint.
3. **The "it's a reduced alphabet / abjad / syllabary" escape hatch is closed.** A *meaningless random* merge of English fits the books' shape better than any structured reduction, and the books' top symbols are vowel-like, so it isn't a consonant skeleton either. (Fourteen symbols alone isn't damning — Hawaiian gets by on thirteen. It's the *profile plus structure* that disqualifies, not the count.)
4. **The only real sequential structure is verbatim copy-paste, not grammar.** One 19-character fragment appears *identically* in 12 of the 70 books; a 29-char fragment in 9; a 49-char fragment in 7. That's templating — the same block pasted around — not the Markov-like word-and-syntax structure language has.
5. **The code-to-symbol map is reversal-invariant on the unordered digit pair.** The vast majority of codes map to the same symbol as their digit-reverse. A genuine letter cipher has no reason to behave like an order-blind lookup table; this one does. (And the symbol isn't a function of digit-sum either, which kills the "secret math/checksum" theory.)

On top of that, the in-lore "it's secretly numbers/mathemagic" hypothesis was tested across roughly fifty-six dedicated analyses — **all null.**

So the verdict on the book layer is **NO-GO**: under everything we and the public community know, the books are not recoverable natural-language plaintext. That's a *robust, defensible, adversarially-verified negative.* In a field drowning in confident false positives, a clean "no" that you can reproduce is worth more than a pretty "maybe."

## The honest caveats (these are non-negotiable)

A write-up that sells a method has every incentive to over-claim. The whole point of the method is to not do that, so:

- **This is partial and negative, not "I solved 469."** We did not produce a single accepted decoded book. We will not pretend otherwise.
- **The phrase "ground truth" is partly circular.** Our crib validations check against *the project's own decoder's output*, not against text officially attested by CipSoft. The reading "be a wit than be a fool" is **community analysis**, not an official translation. So even the phrase codebook is best described as "internally consistent and useful as a holdout" — *not* externally confirmed truth. We flag this everywhere precisely because it's the kind of thing a hype piece would hide.
- **A clean decode of our own making proves consistency, not correctness.** The book symbols were generated from our own map, so "the map is consistent" is partly tautological. We say so.
- **The real wall is data-starvation, not cleverness.** Once a problem is starved of new ground truth, *more internal iteration cannot help* — it just generates nulls dressed as activity. The only thing that would move this needle is a *new, externally-attested* number↔word pair from the game itself. Cleverness already plateaued; that's the meta-lesson.

## What this means for anyone using AI for analysis

Strip away Tibia and Bonelords and you're left with a pattern that shows up everywhere people point LLMs at real questions — log forensics, market "signals," scientific data mining, anomaly hunting, "what does this dataset say":

1. **Fluent output is not evidence.** A model — like a person — will hand you a clean, confident answer to almost any pattern question. Treat "it produced a result" as the *start* of verification, not the end.
2. **Build a Refuter, and flip the burden of proof.** Don't ask the model if it's right; assign an agent to *break* the claim, and default to "refuted" when it's unsure. You'll be amazed how many beautiful findings don't survive a single adversarial pass.
3. **Controls, and beat the MAX.** Always have a baseline that *shouldn't* contain signal (shuffle your data, randomize labels, hold some out). If your finding doesn't clearly beat the *best* of many such baselines, it's overfitting, not insight.
4. **Coverage and confidence are not correctness.** A "100% solution" on a genuinely hard problem should *raise* your suspicion, not lower it. The German map's perfection was the tell.
5. **Measure outcome, not activity.** Iterations, dashboards, and table counts feel like progress and aren't. Keep an Outcome Ledger of the thing you actually want, and let "negative / plateau confirmed" be a respectable, logged result.

Do these five things and the failure mode that wrecks most AI-assisted analysis — *confidently shipping pareidolia* — gets very hard to fall into. That, not the cipher, is the deliverable.

## The takeaway

If you only take one thing from this: the goal of using AI on a hard problem isn't to get an answer. It's to get an answer *you can't easily talk yourself out of.* Build the machine that tries to talk you out of it — and believe what survives.

The full method and all the evidence are open in this repository — the parallel-lane structure, the Refuter discipline, the three-control gate, and the Outcome Ledger — alongside the complete falsification stack behind the 469 verdict. Start with the [final report](../docs/469_final_report.md) and the [project wiki](../docs/wiki/README.md).

---

*Independent research case study. Not affiliated with or endorsed by CipSoft GmbH. "Tibia" and "Bonelord" are trademarks of CipSoft GmbH, referenced nominatively. No game data files or assets are reproduced here; all figures are derived statistics and small illustrative tables.*

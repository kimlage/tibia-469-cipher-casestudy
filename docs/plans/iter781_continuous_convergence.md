# Plan

Executar a convergência como um ciclo contínuo de batches curtos com `SQLite` como estado canônico. O objetivo não é produzir mais verde operacional; é reduzir contradição semântica real até que livros, contigs e falas fiquem mecanicamente estáveis e semanticamente legíveis, usando paralelismo elástico quando isso realmente acelera o trabalho. Artefatos `.xlsx` passam a ser somente legado a ingerir no banco, nunca mais a base padrão de operação.

Banco operacional interativo: `./data/bonelord_operational.sqlite`.

Banco histórico/lossless para ingestão e recuperação pontual: `./data/bonelord_workbook.sqlite`.

## Scope
- In: orquestração contínua por batches, seleção SQLite-first, reutilização de subagentes, promoção canônica por pacote, logs contínuos, redução de contradição semântica sob guardrails GT e ingestão obrigatória do legado para o banco.
- Out: declarar a linguagem resolvida só por `MODEL_CONVERGED`, abrir promoções massivas sem evidência, ou manter operação padrão baseada em planilha/artefato legado.

## Action items
- [in_progress] Manter `./data/bonelord_operational.sqlite` como estado canônico interativo do projeto, usando `./data/bonelord_workbook.sqlite` apenas como arquivo histórico/lossless para ingestão e recuperação pontual.
- [in_progress] Operar o fluxo em batches de `2–4` lanes paralelas por rodada, podendo subir até `6` quando houver ganho real de throughput e as lanes forem independentes ou com write scope separado.
- [in_progress] Usar SQLite para shortlist, auditoria, status, export Discord, registro de probes, poda de ramos mortos e comparação entre batches antes de qualquer confirmação mecânica estreita.
- [pending] Executar continuamente a lane estrutural para resolver competição de macros/parses em pontos de maior contradição, começando por `Book 55` (`VFETTIITA / VFETTII / ETTIITA / ETTIIT / TAV / IFAI`).
- [pending] Executar continuamente a lane alternativa para abrir sementes fortes fora do corredor atual, priorizando `3478`, rosetta-local Bonelord/Beholder, anchors externos e contigs/livros com maior reaproveitamento.
- [pending] Executar continuamente uma lane de auditoria semântica para ranquear os trechos de maior contradição restante e impedir que texto apenas “plausível” suba para o canônico.
- [pending] Executar continuamente uma lane display-only para estabilizar leitura onde houver ganho claro sem contaminar o decode duro.
- [pending] Promover apenas pacotes pequenos e reversíveis: no máximo 1 hipótese estrutural + 1 hipótese semântica/local por batch canônico, sempre com `GT bad_enforced=0`, `soft=0`, `ExternalRoundTrip` sem regressão e sem aumento de contradição local.
- [pending] Separar o placar operacional em `mechanical progress`, `semantic progress` e `display progress`, tratando cada batch como `PROMOVER`, `MANTER EM SOMBRA` ou `ABANDONAR HIPÓTESE`.
- [pending] Reabrir automaticamente os mesmos subagentes a cada fase seguinte, reaproveitando contexto por lane e só encerrando quando a hipótese for promovida, abandonada ou substituída por uma melhor.
- [pending] Publicar no Discord um log curto por batch com: hipótese testada, motivo, resultado, impacto local de leitura e motivo de promoção/rejeição.
- [pending] Repetir o ciclo sem pausa: `auditar hipótese no SQLite -> classificar -> confirmar mecanicamente de forma estreita -> decidir promoção -> atualizar plano/log -> abrir próximo batch`.
- [pending] Parar somente quando a convergência forte combinar: estabilidade mecânica, ausência de ciclos artificiais conhecidos, leitura local coerente nos trechos de maior risco e nenhuma hipótese de alto valor restante sem teste.

## Status
- [done] Contrato operacional mudou para `SQLite-only` em `./AGENTS.md`; planilhas passam a ser legado a ingerir, não fonte padrão de verdade.
- [done] Banco compacto operacional criado em `./data/bonelord_operational.sqlite` para leituras, shortlists, gates, registros de probes e auditorias sem depender do SQLite histórico pesado.
- [in_progress] Ingestão em lote do legado `.xlsx` para `./data/bonelord_workbook.sqlite` permanece como arquivo histórico/lossless, não como caminho interativo padrão.
- [done] Runner já diferencia `MODEL_CONVERGED` de tradução final e separa progresso mecânico/semântico/display.
- [done] `IVNA -> vain` foi estabilizado no canônico com `GlossaryRetext_LockedTokens`, eliminando um ciclo artificial `vain <-> yawn`.
- [done] Contrato operacional atualizado em `./AGENTS.md` para permitir paralelismo elástico até `6` subagentes quando houver ganho real.
- [in_progress] Batch atual aberto com 4 lanes independentes: estrutural `Book 55`, alternativa forte fora do corredor atual, auditoria semântica e display-only.

## Implementation log
- [done] Este plano passa a tratar qualquer referência a workbook/shadow abaixo como histórico legado. O fluxo operacional vigente é SQLite-first; entradas antigas permanecem apenas como trilha de auditoria do que foi tentado.
- [done] Criado lock por token em `./scripts/bonelord_flow_next_iteration.py` para impedir que retext automático desfaça probes locais na mesma iteração.
- [done] Validado em sombra e promovido no canônico o pacote `IVNA -> vain` sem regressão de GT ou métricas duras.
- [done] Publicado log do avanço no `codex-logs`.
- [done] Atualizado `./AGENTS.md` para formalizar o loop contínuo de convergência e o uso de `2–6` subagentes conforme ganho real.
- [done] Batch expandido fechado: `EI -> ye` descartado por no-op local; `Book 55` boundary probe mantido em sombra por ganho parcial com regressão leve; `AC007` priorizado como próximo probe alternativo forte; pacote display-only seguro aprovado para fila curta.

- [done] Lane alternativa ranqueou `AC007` como melhor probe não-Book55: macro estrutural ancorado, com suporte em 9 livros, mais promissor que uma nova rodada `3478` pura.

- [done] Probe sombra `EI -> ye` com token lock: sem efeito local relevante, descartado por ora.
- [done] Probe sombra estrutural em `Book 55`: remover `VFETTIITA/VFETTII/ETTIITA` + lock em `ETTIIT` melhorou `Book 15` e a primeira metade de `Book 55`, mas ainda não merece promoção canônica por regressão leve de contexto e deriva local (`fair i`).
- [done] Lane alternativa priorizou `AC007` como próximo probe estrutural não-Book55: macro ancorado com suporte em 9 livros, superior a insistir em `3478` puro.
- [done] Lane display-only devolveu pacote seguro para pós-processo tardio: vírgulas duplicadas, espaços antes de pontuação, `i -> I` isolado e reaplicação tardia das regras conservadoras existentes.

- [done] Patchado no runner o `LateDisplayCleanup` (step 115) para `Translation_ContextEnglish_Auto` e `Translation_CodeAware_Auto`.
- [done] Iteracao canonica 782 materializou o cleanup tardio com `ctx_books_changed=69`, `codeaware_books_changed=69`, `repl=474`, sem qualquer regressao em GT, roundtrip ou metricas duras.
- [in_progress] Proximo batch orientado para bloqueios estruturais restantes: `Book 55` e `Crib 6 / FifteenStatues`.

- [done] Recuperado automaticamente o canônico a partir de `./tmp/spreadsheets/bonelord_469_iter129_backup_iter782.xlsx` após corrupção do `.xlsx` (`BadZipFile`). O loop contínuo segue sem pausa.

## Iter 783 - TE shadow decision and next frontier
- `TE -> the` shadow (`./tmp/te_the_probe.xlsx`) finished as a real no-op.
- Shadow state: `Iteration=783`, `ChangedBooksCount=0/70`, `EvidenceAvg=2.33395`, `WeakFrac=0.001047`, `MicroFrac=0.001047`.
- Local readout against canonical on `Books 15/16/54/55`: no meaningful delta.
- Shadow glossary confirmed `TE=the` while canonical remains `TE=to`; the hypothesis did not propagate into useful output.
- Promotion decision: `REJECT`.
- New primary frontier: shared anti-hallucination corridor around sanitized medium-confidence tokens.
- `TTNVVN -> <UNK>`: `occ=11`, `books=11`, notes indicate prior mechanical placeholder `tumtum`, sanitized at `iter565`.
- `TII -> <UNK>`: `occ=6`, `books=6`, notes indicate prior mechanical placeholder `hidy`, sanitized at `iter565`.
- Reason for pivot: this is a repeated global blocker across multiple books and is more leverageable than further Book 55 local surgery.

## Iter 783 - TE no-op; Book55 v7 opened
- `te_the_probe.xlsx` terminou em `Iter 783`, `status=MODEL_CONVERGED`, `GT=0/0/0`, `ExternalRoundTrip pass=14`, `books_changed=0/70`.
- Decisao: descartar `TE -> the` como frente primaria por `no-op` pratico. Nao houve melhora local visivel em `Books 9/15/16/55`.
- Novo lane aberto: `book55_boundary_probe_v7_ta.xlsx` a partir do melhor estado local `v5`.
- Mutacao do `v7`: `TA` desabilitado (`Use_StrictPlus_v108=0`) e adicionado a `Convergence_BlockPromotionTokens` para testar quebra do corredor global remanescente do `Book 55`.

- iter783: descartado `TE->the` por no-op prático; `Book55 v7` descartado por regressão de contexto (`ContextEnglishAvg=5.924392`) sem ganho novo defensável.
- iter783: aberto probe `external_anchor_nocodestream_probe.xlsx` com `ExternalRefs_FillFromCodeStreamV120_Enabled=FALSE` e `AnchorPromotionOnly_Enabled=TRUE` para auditar âncoras externas sem backfill de CodeStream v120.
- iter783: probe `external_anchor_nocodestream_probe.xlsx` fechou limpo mas sem efeito: `AnchorPromotionOnly enabled=1, anchors=27, step30_kept=0, step30_dropped=2187`, sem promoções e sem delta mecânico/semântico. Próxima frente: diagnosticar por que âncoras só podam e não alimentam candidatos promotáveis.
- iter783: instrumentado o funil de AnchorPromotionOnly em ./scripts/bonelord_flow_next_iteration.py para persistir classes e samples do drop em step30/step40 (`AnchorPromotionDrop30/40*`). Próximo rerun: `external_anchor_nocodestream_probe.xlsx` para colher diagnóstico real do platô de âncoras.
- `book55_boundary_probe_v7_ta.xlsx`: melhora local em `Books 15/16/55`, mas nao promotavel por regressao global (`ContextEnglish 5.931417 -> 5.909030`, `OOV 0.109310 -> 0.112203`). Mantido apenas como sombra de referencia.
- `crib6_structure_probe_v2_ffa_ant.xlsx`: no-op pratico; descarta `FFA/ANT` isolados como alavanca suficiente.
- `crib6_structure_probe_v3_iin_ffa_ant.xlsx`: no-op pratico; reforca `IIN` como `boundary suspect`, mas indica que o corredor esta sendo mantido pela familia inteira do token.
- Novo lane aberto: `crib6_structure_probe_v4_iin_family.xlsx`, desabilitando `IINI`, `EEIIIN`, `IINFASI`, `VIEFIIN` sobre a base do `v3`.
- `crib6_structure_probe_v4_iin_family.xlsx`: terminou em `Iter 785` com leitura local inalterada em `Books 15/16/55`; tratar como `no-op` prático e encerrar o eixo `Crib6/IIN-family` por agora.
- Proximo pivot operacional: frente alternativa baseada em âncoras externas/rosetta-local, fora de `Book55` e `Crib6`.
- `crib6_structure_probe_v4_iin_family.xlsx`: melhorou levemente `ContextEnglish/OOV`, mas alterou apenas `Book 60` e nao abriu o corredor ancorado do `Crib 6`; mantido em sombra, nao promovido.
- `book60_iinb_eiinb_probe.xlsx`: aprofundou a mesma direcao com melhora marginal de score, mas o texto local permaneceu semanticamente fraco (`join be I I in be to pilate`).
- Novo lane aberto: `book60_iinb_bt_probe.xlsx`, desabilitando `BTILBETAEN` e `BTILBETA` (2 ocorrencias cada) sobre o probe de `Book 60`.
- `book60_iinb_bt_probe.xlsx`: eixo cortado. Resultado final `Iter 787`, `status=READY` por plateau de skips recorrentes (`iters_since_last_mech=3`, `top_skip=Blocked by Convergence_BlockPromotionTokens (9)`). Nao houve ganho local adicional; abandonar esta familia de podas estruturais.
- Proximo batch deve mudar de familia de hipotese (externals/rosetta-local ou outro corredor), em vez de continuar no eixo `Crib6 -> IIN-family -> Book60 -> BTILBETA*`.
- Novo batch aberto fora do eixo `Crib6/Book60`: `book38_head_macro_probe.xlsx`.
- Hipotese: o `Book 38`, ancorado por `HellgateBook_2364672119`, esta sendo dominado por uma cadeia de macros de cabeca de baixa ocorrencia (`ONAF...` / `EIVE...`) que impõe uma leitura inteira sem lastro semantico suficiente.
- Mutacao: desabilitar e bloquear a familia de macros de cabeca de baixa ocorrencia para forcar split estrutural mais fundo no livro externo.
- Novo batch externo aberto: `hellgate_external_macro_probe.xlsx`, desabilitando o macro unico `ONAFIEIVEINLETFNAASTVAFENTEEAEISETEIVIFASTFNEIEINTAAETTAEILSBEIFEVR` (`occ=1`) ligado ao `HellgateBook_2364672119`.
- Racional: probe pequeno, auditavel, fora do eixo `IIN/Book60`, e ancorado por referencia externa verificada.
- `book38_head_macro_probe.xlsx`: limpo, mas `no-op` pratico (`books_changed=0`, `semantic_objective_promoted=7`, `no_effect_promos` alto). Evidencia adicional de que trocar apenas o alvo nao resolve; o proximo batch precisa mudar a politica de promocao/absorcao.
- `hellgate_external_macro_probe.xlsx`: no-op pratico; desabilitar o macro unico do `HellgateBook_2364672119` nao abriu novas leituras.
- `book38_head_macro_probe.xlsx`: no-op pratico; sem alteracoes locais em relacao ao canonico.
- Novo batch externo aberto: `external_ailbet_probe.xlsx`, desabilitando `AILBET` e `ILBETA` para testar a raiz heuristica `albeit -> played` sob linhas externas verificadas.
- Novo batch de mecanismo: `anchor_only_3478_npc_probe.xlsx`.
- Settings: `AnchorPromotionOnly_Enabled=1`, `MinVerifiedSources=1`, `IncludeExternalNPCStaff=1`, `IncludeExternalBooks=0`, `IncludeAnchorCribs=0`, `Convergence_SemanticObjective_Enabled=0`, `Convergence_EnableNoEffectAnchorEscape=0`.
- Objetivo: expansao exata ao redor de `Knightmare1` e `BonelordName_3478` sem reabsorcao por `SemanticObjective`.
- `anchor_only_3478_npc_probe.xlsx`: mecanismo mudou de fato (`AnchorPromotionOnly=1`, `SemanticObjective=0`), mas ficou `no-op`; filtro de anchors derrubou `2187` candidatos no step30 e nao promoveu nada.
- Novo batch aberto: `anchor_only_3478_all_external_probe.xlsx`, ampliando `AnchorPromotionOnly_IncludeExternalBooks=1` para testar se o corpus de anchors estava estreito demais.
- `anchor_only_3478_all_external_probe.xlsx`: identico ao probe NPC-only (`anchors=8`, `step30_dropped=2187`, `0` promocoes, `0` books mudados). Fechada a hipotese de que o corpus de anchors estava estreito demais.
- Diagnostico consolidado: o bloqueio atual nao esta em trocar alvo, nem em ampliar `ExternalBooks`, nem em podar macros locais. O problema esta em outra camada do metodo de promocao/geracao.
- Patch no runner aplicado em `./scripts/bonelord_flow_next_iteration.py`: adicionada geracao local `mine_macro_candidates_from_anchor_corpus(...)` e encaixe em `_mine_and_try_promote_macros(...)` via setting `AnchorMacroMine_Enabled`.
- Objetivo do patch: permitir que `AnchorPromotionOnly` deixe de ser so filtro e passe a ter um gerador local de macros diretamente sobre `anchor_corpus`.
- `anchor_macromine_runner_patch_probe.xlsx`: primeiro sinal positivo do patch. `step40_kept=3`, `top_skip=No effect in DP metrics (3)`, todos vindos de macros locais de anchor curto (`ILAEN`, `IL`, `LAEN`).
- Diagnostico: o gerador local funciona, mas o corpus de anchors precisa ser mais seletivo para atingir livros. Novo batch aberto: `anchor_macromine_books_only_probe.xlsx` com `IncludeExternalNPCStaff=0`, mantendo `GroundTruth=1` e `ExternalBooks=1`.
- Patch adicional no runner: `collect_anchor_base_corpus(...)` agora faz fallback por linha de `CodeStreamBase_v120` para `DecodedBase` em `ExternalRefs_v115`. Isso corrige o caso em que a coluna existe no schema mas a celula do livro externo esta vazia, zerando indevidamente o `anchor_corpus`.
- Rerun de `anchor_macromine_external_books_v0_probe.xlsx` com fallback corrigido: primeiro ganho operacional real do eixo externo. `anchors=2`, `step30_kept=14`, `step30_dropped=2200`.
- Gargalo seguinte identificado com precisao: `CandidatePriority` eliminou os 14 candidatos (`min_hits=2`, `min_occ=2`) antes da simulacao.
- Novo batch aberto: `anchor_macromine_external_books_v0_priority_probe.xlsx`, relaxando `CandidatePriority_MinBookHits=1`, `CandidatePriority_MinTotalOcc=1`, `Convergence_CandidateCapPerIter=200`.

## 2026-03-06 09:xx BRT - dual lane on CandidatePriority / pre-Step40
- Baseline diagnosis before this batch:
  - `anchor_macromine_external_books_v0_probe.xlsx` finally yielded external-book anchor generation (`anchors=2`, `step30_kept=14`, `step30_dropped=2200`), but `CandidatePriority` killed all 14 before simulation (`priority kept=0, dropped=14`).
  - Re-reading the resulting workbook confirmed no new iteration had been persisted when the first `priority_probe` was run interactively; the file stayed at `CurrentIteration=782`.
- Current lanes opened:
  - `anchor_macromine_external_books_v0_priority_probe.xlsx`: same lane with relaxed `CandidatePriority` (`MinBookHits=1`, `MinTotalOcc=1`, high no-effect tolerance) re-run in detached mode with file logs.
  - `anchor_macromine_external_books_v0_priority_off_probe.xlsx`: parallel shadow lane with `CandidatePriority_Enabled=False` to determine whether the next bottleneck is simulation / monotonic gating.
- Additional code-path diagnosis from `bonelord_flow_next_iteration.py`:
  - After `CandidatePriority`, candidates fall into Step 40 `_simulate_candidate(...)`.
  - Likely next hard skip is still `No effect in DP metrics (not used)` unless semantic-no-effect escape or score-based escape is active.
  - Mechanical approval is written only after Step 40 (`Mechanical promotions approved: ...`).

## 2026-04-23 - SQL-first operational cutover and semantic contradiction pivot
- Interactive default DB switched to `./data/bonelord_operational.sqlite`.
- Historical/lossless ingest DB remains `./data/bonelord_workbook.sqlite`, but it is no longer the standard analysis path because it is too heavy for fast iterative work.
- Current canonical imported state remains `iter=784`, `Status=MODEL_CONVERGED`, `GTBadEnforcedCount=0`, `GTBadAllCount=0`, `GTSoftMismatchCount=0`, `PromotionSkipReasonTop=No effect in DP metrics (not used) (41)`.
- Interpretation changed: `MODEL_CONVERGED` is mechanical convergence only. It must not be treated as language solved because the current text is still semantically unstable.
- New SQL tools:
  - `./scripts/sqlite_semantic_family_report.py`
  - `./scripts/sqlite_semantic_contradiction_rank.py`
- Current reports:
  - `./tmp/semantic_family_vtlrnefie_report.json`
  - `./tmp/semantic_family_ttnvvnnfie_report.json`
  - `./tmp/semantic_contradiction_rank.json`
- Primary frontier: `VTLRNEFIE`.
  - Appears in `11` books and has a large macro family.
  - Base token currently says `fervently`, but child macros preserve `unfertile/fay`.
  - This is likely semantic overlay drift, not reliable translation.
- Secondary frontier: `TTNVVN / TTNVVNNFIE`.
  - Base token was sanitized to `<UNK>`, but child macros still preserve `tumtum`.
  - This indicates anti-hallucination did not propagate through macro translations.
- Next tactical rule:
  - Prioritize contradiction reduction and prefix-child consistency before opening new mechanical confirmation runs.
  - Treat any English word generated only by semantic retext or unreconciled macro inheritance as provisional, not solved.

## 2026-04-23 - Macro recomposition audit
- Added SQL-only macro recomposition audit:
  - `./scripts/sqlite_macro_consistency_audit.py`
  - `./scripts/sqlite_materialize_glossary_audit.py`
  - `./scripts/sqlite_macro_recomposition_audit.py`
  - `./scripts/sqlite_translation_progress_snapshot.py`
- Agent findings:
  - `VTLRNEFIE` is stale semantic/display cache: base says `fervently`; child macros still preserve `unfertile/fay`.
  - `TTNVVN` is stale semantic/display cache: base says `<UNK>`; child macros still preserve `tumtum`.
  - `I*VLVEEIIV` / `evil eye you've` is a mined macro; `evil eye` has Tibia lore support but no direct external roundtrip for the macro.
  - `ETRFEVAS` / `AETRFEV` / `ASTF` / `ITV` are stronger base candidates, but `ITVAETRFEV*` macros are stale/inactive display artifacts.
  - `VIEFIINI/VIEFIIN` is likely display artifact; `AILBET/TAILBE` and `VNCTII` are stronger bases but their macro descendants are contaminated.
- Macro recomposition result:
  - `2977` macros with component lists.
  - `1310` change when recomposed from current audited components.
  - `5` missing components.
- Updated progress snapshot:
  - mechanical convergence: `100.0%`
  - book clean: `61.43%`
  - glossary clean: `85.81%`
  - macro consistency: `14.0%`
  - macro recomposition clean: `56.0%`
  - conservative reliable-read confidence: `68.31%`
- Operational conclusion:
  - The main bottleneck is not iteration count.
  - The main bottleneck is stale macro cache and over-trusting English/anagram render.
  - Next scoring/ranking must use recomposed audited macro text as the evaluation layer before any decode-core promotion.

## 2026-04-23 - External phrase anchor pivot
- Added external phrase anchor audit:
  - `./scripts/sqlite_external_phrase_anchor_audit.py`
- New hard/soft phrase anchors:
  - `653768764` expected `look at you` / `Let me take a look at you`, tied to `The Evil Eye` lore and local legacy source.
  - `65997854764` expected `let me see you`, local legacy source.
- Current model result:
  - `653768764`: `dp=I lo a me`, `codestream=you've a me`, status `MISMATCH`.
  - `65997854764`: `dp=eye the no`, `codestream=eye of far`, status `MISMATCH`.
- Updated progress snapshot:
  - external phrase anchor pass: `0.0%`
  - conservative reliable-read confidence: `58.17%`
- Operational conclusion:
  - External short phrases now outrank book-macro exploration as calibration targets.
  - Do not declare books readable while the short phrase anchors fail.
  - Next decoding batch should use `653768764` and `65997854764` as rosetta-local constraints for short token/code-stream segmentation and omission handling.
- Operational note:
  - At least two detached `bonelord_flow_next_iteration.py` processes are currently running on shadow files and saturating CPU; do not touch canonical while this batch drains.

## 2026-03-06 - Batch: anchor macromine priority rerun (iter 785)
- Diagnóstico confirmado: `CandidatePriority` relaxado deixou o corredor avançar, mas o runner ainda promovia `MACRO_ACTIVE` sem efeito real via `directional escape`.
- Evidência: `iter 785` terminou com `mech_promoted=13`, `books_changed=0`, e as últimas linhas de `CandidatePromotions` mostraram promoções `pass1: directional:evidence_mix` com `dEv=0`, `dWeak=0`, `dMicro=0`, `dSingle=0`.
- Correção aplicada em `./scripts/bonelord_flow_next_iteration.py`: `allow_by_score` não pode mais aprovar candidato `no-effect` quando `gt_soft_delta <= 0`.
- Próximo passo operacional: recriar a sombra de prioridade a partir de `anchor_macromine_external_books_v0_probe.xlsx` e rerodar com o guard novo para localizar o próximo gate real após o bloqueio do falso avanço direcional.

## 2026-03-06T17:23Z - Batch: external-books priority probe
- Rerun concluido em `tmp/anchor_macromine_external_books_v0_priority_probe.xlsx`.
- Resultado: `iter 783`, `status=MODEL_CONVERGED`, `GT=0/0/0`, `books_changed=0/70`.
- Diagnostico refinado:
  - `AnchorPromotionOnly` finalmente deixou `14` candidatos passarem em Step30.
  - `CandidatePriority` relaxado manteve `13` e derrubou `1`.
  - `Step40` aprovou `13`, mas via `directional_escape_promos=13` com delta mecanico zero e sem livros alterados.
  - Portanto o gargalo seguinte nao e mais CandidatePriority; e o regime de aprovacao por directional escape, que mascara ausencia de uso real.
- Proximo probe em preparo: desligar `Convergence_EnableDirectionalEscape` e `Convergence_EnableHardEscape` para forcar skip reasons reais ou aprovacoes com efeito real.

## 2026-03-06T17:25Z - Explorer consolidation
- `Descartes`: `CandidatePriority` so registra `dropped=` agregado; motivos individuais aparecem apenas apos Step40 via `set_candidate_decision(..., SKIP, ...)`.
- Probe minimo confirmado para expor skips reais: desligar `Convergence_EnableDirectionalEscape` e `Convergence_EnableHardEscape`; opcionalmente `PromotionMaxPasses=1` para limpar o dump.
- Confirmacao adicional: macro aprovada pode ser `output-stable` e nao alterar `Books`/`Tokens` se a DP nao a escolher no corpus atual.

## 2026-03-06T17:31Z - Batch: no-directional probe result
- `tmp/anchor_macromine_external_books_v0_no_directional_probe.xlsx` concluiu em `iter 784` com `mech_promoted=0`.
- Leitura correta do iter 784:
  - `anchor-only kept=1`
  - `priority kept=0, dropped=1`
  - `Candidates scanned: 0`
  - `Mechanical promotions approved: 0`
- Conclusao: o probe sem escapes confirmou que o verde anterior vinha do `directional escape`, mas este workbook ja estava contaminado pelo historico do iter 783. Para obter `skip reasons` individuais reais, o proximo probe precisa ser fresco e com `CandidatePriority_Enabled=False`.

## 2026-03-06T17:35Z - Batch: fresh skip dump probe
- `tmp/anchor_macromine_external_books_v0_skipdump_probe.xlsx` concluiu em `iter 785`.
- Resultado central:
  - `AnchorPromotionOnly step30_kept=14`
  - `mech_promoted=0`
  - `PromotionSkips count=14`
  - `PromotionSkips top=No effect in DP metrics (not used) (14)`
  - `status=READY` com block reason de plateau de skips recorrentes.
- Conclusao metodologica:
  - O pipeline de geracao e filtragem agora esta funcional o suficiente para trazer os candidatos ate Step40.
  - O gargalo real nao e mais `CandidatePriority` nem `directional escape`.
  - Os candidatos externos sobreviventes simplesmente nao entram na DP dos livros atuais; sao estruturalmente inuteis para o corpus `Books` no boundary/modelo atual.
- Proximo foco: investigar os 2 anchors externos ativos e medir ocorrencia/reuso real no corpus para decidir entre probe de boundary/source ou abandono dessa familia de anchors.

## 2026-03-06T17:39Z - Anchor source reconciliation
- Exploracao adicional sugeriu que os 2 anchors realmente ativos podem ser `SuperAnchors_Auto` (`SA001`/`SA002`) com reuso literal em multiplos books, e nao apenas os 2 `HellgateBook_*` externos.
- A verificar de forma objetiva: settings de inclusao no probe e presenca dos IDs `iter199_SA001/SA002` em `AnchorCribs_Auto`, `SuperAnchors_Auto` e `AnchorOccurrences_Auto`.
- Se confirmado, o proximo batch deixa de minerar novos anchors externos e passa para probe de extensao/bridge ao redor de `SA001` e `SA002`.

## 2026-03-06T17:40Z - Pivot: superanchors with real reuse
- Verificacao local confirmou que, no probe atual, os `anchors=2` relevantes sao `AC_AUTO_SA199_001` e `AC_AUTO_SA199_002` em `AnchorCribs_Auto`.
- Ambos tem reuso literal em 7 books cada, muito mais promissor do que insistir na familia Hellgate inteira como macro longa.
- Novo batch aberto a partir do canônico: `tmp/anchor_cribs_skipdump_probe.xlsx`.
- Configuracao do batch:
  - `AnchorPromotionOnly_IncludeAnchorCribs=True`
  - `AnchorPromotionOnly_IncludeExternalBooks=False`
  - `CandidatePriority_Enabled=False`
  - escapes desligados
  - `PromotionMaxPasses=1`
  - `AnchorMacroMine_Enabled=True`
- Objetivo: verificar se a familia `SA001/SA002` produz candidatos com efeito real na DP ou se tambem morre por `not used`.

## 2026-03-06T17:44Z - Next diagnostic: bridge windows around SA001/SA002
- `anchor_cribs_skipdump_probe` gerou 3 candidatos internos (`IVIFASTFNEIEI`, `LTASTTNV`, `TTNV`) e todos morreram por `not used`.
- Interpretacao: os superanchors tem reuso real, mas o minerador atual ainda esta escolhendo janelas com ganho nulo para a DP.
- Proximo passo analitico: medir janelas internas de `SA001/SA002` por `books_hit` para abrir um probe de bridge/extension mais agressivo em torno das janelas mais recorrentes, em vez de insistir nos mesmos 3 candidatos.

## 2026-03-06T17:45Z - AnchorCribs concrete targets
- Os alvos concretos desta familia surgiram em `AnchorCribs_Auto` como `AC008`, `AC010` e `AC011`.
- Exemplos:
  - `AC008`: `IFVI*NAESESTIENFATCTIVVTISETEIVIFASTFNEIEI`
  - `AC010`: `ITELBENNAIFIININSBASTFNENIIFINI*LTASTTNV`
  - `AC011`: `NFATCTIVVTISETEIVIFASTFNEIEINTAAET`
- Proximo passo analitico em curso: medir janelas internas com maior `books_hit` para montar um bridge probe mais agressivo em torno desses anchors.

## 2026-03-06T17:47Z - New lane: long windows around AnchorCribs
- Analise de reuso mostrou janelas muito mais promissoras do que os 3 candidatos curtos testados:
  - `ITELBENNAIFIININS` (hits~13)
  - `ISETEIVIFASTFNEIEI` (hits~12)
  - `TEIVIFASTFNEIEI` (hits~12)
- Novo batch aberto: `tmp/anchor_cribs_long_windows_probe.xlsx`.
- Ajustes principais:
  - `MacroMine_MinLen=10`, `MacroMine_MaxLen=20`
  - `MacroMine_MinOcc=4`, `MacroMine_MinBooks=4`
  - `MacroMine_AllowMacroComponents=False`
  - `MacroMine_AllowMarkers=False`
  - `MacroMine_AllowStars=False`
  - `AnchorCribs` only, sem `CandidatePriority`, sem escapes, `PromotionMaxPasses=1`
- Objetivo: forcar o minerador a testar janelas internas longas e multiplamente reutilizadas, em vez de candidatos curtos e triviais.

## 2026-03-06T17:50Z - Parallel ideation batch opened
- Novo batch de exploracao paralelo aberto para buscar ideias de avanço alem do corredor atual de `MacroMine`.
- Frentes pedidas aos subagentes:
  - boundary/DP: por que janelas de alto reuso nao entram na DP
  - geracao/bridge: como testar extensoes uteis ao redor de `AC008/AC010/AC011`
  - estrutural: se o alvo correto passou a ser `BooksDigitModel_v118` / boundary local nos books atingidos
  - metodologico: como medir progresso real e evitar macros output-stable
- Em paralelo local: preparar lane manual de bridge/seeding em torno de `AC008`, `AC010`, `AC011`.

## 2026-03-06T17:54Z - Operational lanes opened from ideation batch
- `Lane 1: Book55 boundary`
  - workbook: `tmp/book55_structural_family_probe.xlsx`
  - acao: desligar familia `VFETTIITA / VFETTII / ETTIITA / ETTIIT / TAV / IFAI`
  - escapes desligados, `SemanticObjective` desligado
- `Lane 3: 3478 alternative`
  - workbook: `tmp/anchor_3478_groundtruth_skipdump_probe.xlsx`
  - acao: `GroundTruth` only, `AnchorMacroMine` ligado, sem `CandidatePriority`, sem escapes
- Objetivo do batch: distinguir entre bloqueio de fronteira local e eixo ancora alternativo mecanicamente util.

## 2026-03-06T17:59Z - Next lane prepared from subagent ideation
- `Lane 2 refined: anchor_cribs_midband_bridge`
  - workbook: `tmp/anchor_cribs_midband_bridge_probe.xlsx`
  - rationale: partir do sucesso parcial do `skipdump`, bloquear o trio trivial (`IVIFASTFNEIEI`, `LTASTTNV`, `TTNV`) e abrir a geracao em faixa media (10-24; n=4..9) para forcar bridges uteis ao redor de `AC008/AC010/AC011`.
  - `CandidatePriority`, escapes, `SemanticObjective` e `StrictMonotonicMechanical` desligados.

## 2026-03-06T18:03Z - Next lane prepared: de-coarsening
- `tmp/anchor_cribs_decoarsen_probe.xlsx` preparado a partir do canônico.
- Hipotese: `AC008/AC010/AC011` nao entram por `superset-swallow` de macros-pai de baixo reuse.
- Acoes no shadow:
  - `AnchorCribs` only, sem `CandidatePriority`, sem escapes, sem `SemanticObjective`
  - `SuperAnchorMacro_Enabled=True`
  - desativacao explicita de 6 macros-pai engolidoras listadas pelo subagente estrutural
  - `Convergence_MonotonicAllowTokenIncrease=True` para diagnostico puro
- Este lane entra assim que uma das 2 execucoes pesadas atuais terminar.

## 2026-03-06T19:06Z - Lane started: anchor_cribs_decoarsen
- `anchor_3478_groundtruth_skipdump_probe` fechou fraco (`anchors=7`, `step30_kept=0`, `mech_promoted=0`).
- `book55_structural_family_probe` fechou forte (`mech_promoted=3`, `books_changed=2`, `Tokens 314->309`, `GT=0/0/0`).
- Diante disso, `anchor_cribs_decoarsen_probe` entrou como proxima lane pesada.
- Hipotese em teste: `superset-swallow` de macros-pai engolindo os spans de `AC008/AC010/AC011`.

## 2026-03-06T19:14Z - Next lane prepared: decoarsen + midband bridge
- O `decoarsen` confirmou `superset-swallow`: mudou diretamente os books `5, 9, 53, 58` sem novas promoções e sem quebrar GT.
- Proxima lane preparada: `tmp/anchor_cribs_decoarsen_midband_probe.xlsx`.
- Estrategia:
  - manter macros-pai engolidoras desligadas
  - `AnchorCribs only`
  - `SuperAnchorMacro_Enabled=True`
  - bloquear `IVIFASTFNEIEI, LTASTTNV, TTNV`
  - `MacroMine` em faixa media (`MinLen=10`, `MaxLen=24`, `NValues=4..9`, `MinOcc=1`, `MinBooks=1`)
- Objetivo: verificar se, uma vez removido o swallow, bridges uteis finalmente nascem e entram na DP.

## 2026-03-14 - Reliability audit: current canonical interpretation
- O canônico deve ser tratado como `menos tóxico` e `mecanicamente estável`, não como tradução semanticamente convergida.
- Taxonomia operacional em uso:
  - `anti-toxic`: contenção local segura; pode entrar no canônico como mitigação.
  - `surface-only`: melhora de display/leitura; não conta como avanço mecânico.
  - `mechanical scaffold`: sombra útil para diagnóstico estrutural; não promover.
  - `local semantic`: único tipo que conta como avanço real de tradução.
  - `discarded`: branch fechado.
- Corredores atualmente mantidos como mais confiáveis:
  - `Books 5/9/53`: leitura menos tóxica no braço direito (`... I in vain`).
  - `Book 54`: melhoria contextual em torno de `IVNA -> vain`, mais forte em contexto/display do que em decode estrito.
  - `Book 59`: limpeza local de superfície, sem semântica nova forte.
- `Book55 exactmacroblock` permanece apenas como `mechanical scaffold` em sombra.
- Fechados em forma direta:
  - `SA001/SA002`
  - `rosetta-local fresh`
  - `3478` direto
  - `AC010` wrappers/workbook
  - `Book38/Hellgate`
  - `Crib6 / Book60 / BTILBETA`
  - `mid-right structural` direto

## 2026-03-14 - Batch closed: AC023, Chay2, AC013
- Workbooks:
  - `tmp/ac023_exact_seed_probe.xlsx`
  - `tmp/chay2_exact_anchor_probe.xlsx`
  - `tmp/ac013_core_seed_probe.xlsx`
- Resultado consolidado:
  - todos terminaram em `status=READY`
  - `GT bad_enforced=0 | bad_all=0 | soft=0`
  - `ChangedBooksCount=0/70`
  - sem uptake local real
- Classificacao:
  - `AC023 exact seed` -> `discarded`
  - `Chay2 exact anchor` -> `discarded`
  - `AC013 core seed` -> `discarded`
- Conclusao metodologica:
  - o gargalo ativo nao esta em semear mais um token exato; esta em spans competitivos, alinhamento estrutural e competicao contra wrappers/incumbentes na DP.

## 2026-03-14 - New active frontier: AC008 structural corridor
- Evidencia do canônico:
  - `AnchorCribs_Auto` mostra um corredor vivo e multi-book:
    - `AC008 = IFVI*NAESESTIENFATCTIVVTISETEIVIFASTFNEIEI`
    - `AC015 = SETBASEFAIFVI*NAESESTIENFATCTIVVTISETEIVIFASTFNEIEI`
    - `AC016 = IFVI*NAESESTIENFATCTIVVTISETEIVIFASTFNEIEINTAAET`
  - `VariantAssemblyBlocks_Auto` no `refBook=9` mostra blocos variantes e estáveis exatamente nesse miolo.
- Batch atual aberto:
  - `tmp/ac008_windowed_struct_pad0_probe.xlsx`
    - janelas locais por âncora
    - `StructuralIgnoreAnchorCribs = all except AC008/AC015/AC016`
    - `StructuralRestrictVotesToAnchorWindows = TRUE`
    - `StructuralAnchorWindowPad = 0`
    - `SuperAnchor` relaxado localmente
    - escapes desligados
  - `tmp/ac008_anchorlocal_macromine_probe.xlsx`
    - mesmo foco estrutural
    - `AnchorMacroMine_Enabled = TRUE`
    - `MacroMine_MinBooks = 1`
    - `MacroMine_MinShare = 0.85`
    - `MacroMine_NValues = 2,3,4,5,6`
    - escapes desligados
  - `tmp/ac008_forceprobe_supersetoff_probe.xlsx`
    - `Convergence_ForceProbeOnly = TRUE`
    - `Convergence_ForceProbeDisableSupersets = TRUE`
    - `Convergence_DiagnoseSwallowedSupersets = TRUE`
- Objetivo do batch:
  - separar 3 falhas diferentes do corredor `AC008`:
    - backbone/alinhamento global ruim
    - span local ainda nao competitivo
    - dominancia por supersets ativos

## 2026-03-14 - Partial result: AC008 forceprobe superset-off
- Workbook: `tmp/ac008_forceprobe_supersetoff_probe.xlsx`
- Resultado:
  - `CurrentIteration=785`
  - `status=READY`
  - `GT=0/0/0`
  - `ChangedBooksCount=0/70`
  - `PromotionSkipCount=1`
  - `PromotionSkipReasonTop=No improvement to target metrics (weak/micro/single), EvidenceAvg, or token-count (1)`
- Classificacao:
  - `discarded`
- Leitura:
  - desligar supersets para `AC008` nao bastou para produzir uptake real na DP
  - a frente estrutural continua viva, mas o bloqueio parece mais ligado ao regime de alinhamento/janela do que a dominancia direta por wrappers
- Acao seguinte:
  - `tmp/ac008_windowed_struct_pad20_probe.xlsx` promovido ao proximo slot ativo

## 2026-03-14 - Partial result: AC008 pad0 and anchor-local macromine
- Workbooks:
  - `tmp/ac008_windowed_struct_pad0_probe.xlsx`
  - `tmp/ac008_anchorlocal_macromine_probe.xlsx`
- Resultado comum:
  - `CurrentIteration=785`
  - `status=MODEL_CONVERGED`
  - `GT=0/0/0`
  - `ChangedBooksCount=3/70`
  - `EvidenceAvg=2.332519`
  - `PromotionSkipReasonTop=No effect in DP metrics (not used) (39)`
- Diff local relevante contra o canônico:
  - livros afetados: `5, 28, 53`
  - regressão tóxica reintroduzida:
    - `of it -> of died`
    - `I in vain -> join vain` no braço direito
- Classificacao:
  - ambos `discarded`
- Conclusao:
  - o corredor `AC008` continua vivo, mas:
    - `pad0` sozinho não serve
    - `anchor-local macromine` sem filtro estrutural mais duro só reabre o ramo tóxico antigo
  - a pressão permanece em:
    - `pad20`
    - `subcluster_min5`
    - `ref5_strong_unique`

## 2026-03-14 - Partial result: AC008 pad20
- Workbook: `tmp/ac008_windowed_struct_pad20_probe.xlsx`
- Resultado:
  - `CurrentIteration=785`
  - `status=MODEL_CONVERGED`
  - `GT=0/0/0`
  - `ChangedBooksCount=3/70`
  - `EvidenceAvg=2.332519`
  - `PromotionSkipReasonTop=No effect in DP metrics (not used) (39)`
- Diff local contra o canônico:
  - novamente `Books 5, 28, 53`
  - novamente a regressão tóxica:
    - `of it -> of died`
    - reaparecimento de `join vain`
- Classificacao:
  - `discarded`
- Conclusao:
  - aumentar a janela local de voto para `pad=20` não limpa a contaminação estrutural deste corredor
  - a frente viva fica reduzida a:
    - `subcluster_min5`
    - `ref5_strong_unique`
    - `ref58_strong_unique`

## 2026-03-14 - Partial result: AC008 subcluster_min5
- Workbook: `tmp/ac008_subcluster_min5_probe.xlsx`
- Resultado:
  - `CurrentIteration=785`
  - `status=MODEL_CONVERGED`
  - `GT=0/0/0`
  - `ChangedBooksCount=3/70`
  - `EvidenceAvg=2.332519`
  - `PromotionSkipReasonTop=No effect in DP metrics (not used) (39)`
- Diff local contra o canônico:
  - novamente `Books 5, 28, 53`
  - novamente a regressão tóxica:
    - `of it -> of died`
    - reaparecimento de `join vain`
- Classificacao:
  - `discarded`
- Conclusao:
  - reduzir o limiar estrutural para `SuperAnchor_MinBooks=5` sem trocar `refBook` não muda a bacia errada
  - o eixo estrutural vivo fica concentrado em:
    - `ref5_strong_unique`
    - `ref58_strong_unique`

## 2026-03-06T20:14Z - Next lane prepared: Book55 boundary refine
- `tmp/book55_boundary_refine_probe.xlsx` preparado a partir do canônico.
- Objetivo: repetir o ganho local do `Book55 boundary`, mas sem reintroduzir os artefatos que o auditor semântico marcou.
- Ajustes:
  - `Convergence_BlockPromotionTokens=IFAI,ETTIIT,ETTIITA`
  - desativar apenas `VFETTIITA` e `VFETTII`
  - manter escapes e `SemanticObjective` desligados
- Critério: o corredor `fool to joy to` some ou estabiliza sem cair em `fair I` / `fool!` e sem piora global material.

## 2026-03-06T20:55Z - Next lane prepared: manual_seed_decoarsen
- O `combo_refine` ainda ficou sujo e nao resolveu a promotabilidade.
- Fallback ativado: `tmp/manual_seed_decoarsen_probe.xlsx`.
- Estrategia:
  - manter o `de-coarsening` dos macros-pai engolidores
  - desligar escapes/semantic/priority
  - adicionar 2 seeds manuais minimos em `Glossary` para spans de alto reuse:
    - `ITELBENNAIFIININS`
    - `TEIVIFASTFNEIEI`
- Objetivo: testar uptake estrutural direto na DP sem depender do gerador atual.

## Batch 2026-03-06T00: parallel continuation
- Status: in_progress
- Goal: keep the continuous convergence loop running with more parallelism.
- Active lanes for this batch:
  - `book55_local_refine_v2`: narrower local suppression to try to keep the mechanical signal from Book 55 while blocking the dirty punctuation/phrase artifacts.
  - `manual_seed_singleton_v1`: one-token manual seed under stricter promotion caps, to test whether a cleaner seed can open uptake without the noisy combo branch.
  - `display_snapshot_guarded_v1`: display-only sanity lane to measure whether readability can improve without contaminating decode.
- Active subagents for this batch:
  - code-path audit for swallowed-span uptake
  - next-experiment design avoiding already-dead corridors
- Notes:
  - Canonical workbook remains protected.
  - Promotion requires GT bad_enforced=0, soft=0, roundtrip stability, and a locally defensible semantic improvement.

### Batch result: 2026-03-06 parallel continuation
- `book55_ifai_only_probe`: GT-clean, mechanically active (`mech_promoted=10`) but semantically still dirty. Local corridor stayed `fair I, fool!`; not promotable.
- `book55_ifai_ettiit_probe`: GT-clean, similar outcome (`mech_promoted=11`) and same local artifact family; not promotable.
- `ac008_decoarsen_isolation_probe`: GT-clean, no promotions, but structural change isolated to Books 5/9/53. Most useful local shift was the corridor around `of it I lo so be I in vain all be`, which is cleaner than the canonical `join yawn` path. Strong structural evidence.
- `ac007_decoarsen_isolation_probe`: GT-clean, no promotions, isolated effect on Books 53/58. Most useful shift was `straight no be, I lo eye` replacing the blunter `beeline eye` corridor. Structural evidence, weaker than AC008.
- `anchor_reexpose_noeffect_probe`: GT-clean no-op. Raising `CandidatePriority_NoEffectSkipThreshold` and capping candidates did not reopen swallowed anchors; Step30 still kept 0.
- Decision:
  - abandon the current `Book55` local clamp family for now
  - keep AC008 as the strongest active structural lead
  - next batch should test whether AC008 improvements persist with mining disabled and then isolate the exact swallow parent inside AC008

### Batch result: AC008 hold and parent isolation
- `ac008_hold_nomine_probe`: exact AC008 improvement persisted with `AnchorMacroMine_Enabled=False`. This confirms the gain is structural and not dependent on fresh macro mining noise.
- `ac008_parent1_probe`: isolated most of the signal on the first AC008 swallow parent. It reproduced the useful changes in Books 9 and 53.
- `ac008_parent2_probe`: no effect.
- `ac008_parent3_probe`: no effect.
- Interpretation:
  - AC008 parent #1 is the primary swallow source.
  - The Book 5 improvement requires either the full AC008 hold or a parent #1 + companion interaction.
- Next batch:
  - test parent pair combinations (1+2, 1+3, 2+3)
  - identify which companion is needed to recover the Book 5 gain
  - if only parent #1 + one companion reproduces the full hold state, that pair becomes the leading candidate for guarded canonical promotion

### Promotion decision: AC008 pair 1+3
- Validation in default regime passed on `ac008_parent13_defaultregime_probe`.
- Signal remained identical to the guarded shadow state:
  - GT bad_enforced=0, soft=0
  - ExternalRoundTrip clean
  - local improvement reproduced in Books 5/9/53
  - no dependency on anchor-only mode or disabled mining
- Decision: promote the AC008 parent pair `1+3` disable to canonical glossary and run the next canonical iteration.

### Canonical promotion applied
- Promoted the validated AC008 parent pair `1+3` to the canonical glossary.
- Canonical `iter 783` remained GT-clean and preserved the local improvement in Books 5/9/53.
- Next structural target: AC007 family decomposition, since it remains the secondary productive corridor and Book55 is still not promotable.

### Telemetry patch + next diagnostic mode
- Added a diagnostic path in `bonelord_flow_next_iteration.py` to distinguish generic `No effect in DP metrics (not used)` from `Swallowed by active superset(s): ...`.
- No promotion rule changed in this patch; it only refines skip attribution for no-effect candidates.
- AC007 decomposition came back weak.
- AC010 singleton seed changed only Book 19 and worsened readability; not promotable.
- Next batch: anchor-only diagnostic shadow with swallowed-superset telemetry enabled and no-effect cooldown relaxed.

### Batch start: AC010 wrapper isolation
- Status: in_progress
- Goal: attack the `AC010 / ITELBENNAIFIININS` corridor directly via wrapper suppression instead of anchor-only regeneration.
- Rationale:
  - AC008 pair `1+3` is now canonically promoted and stable.
  - AC007 decomposition was weak.
  - AC010 singleton seed changed only Book 19 and did not open the intended corridor.
  - The next best hypothesis is that the useful AC010 span is being swallowed by active `TELBENNAIFIININS* / LEITEL...` wrappers.
- Active work:
  - enumerate current active wrappers in Glossary
  - isolate them in parallel shadows
  - require no regression in Books 5/9/53 while checking Books 19/28/58 and any new AC010-local books

### Batch pivot: AC010 precise wrapper peeling
- Broad AC010 group probes (`TEL`, `LEITEL`, `*LEITEL`, `ITEL`) produced no visible book changes.
- Moving to the more precise wrapper ladder suggested by the explorer:
  - pair: `LEITELBENNAIFIININSBASTFNENIIFINI*LTASTTNVVN` + `*LEITELBENNAIFIININSBASTFNENIIFINI*LTASTTNVVN`
  - singleton: `FIFTLEITELBENNAIFIININSBASTFNENIIFINI*LTASTTNVVN`
  - singleton: `FFIFTLEITELBENNAIFIININSBASTFNENIIFINI*LTASTTNVINIVFEIEALVNSBEIEFIANEFIVEIIVNTBB`
  - singleton: `VEIINIAVNALLBEEILEEIEFFIFTLEITELBENNAIFIININSBASTFNENIIFINI*LTASTTNVVNNF`
- Watch books: `9,10,35,40,58,66,69`; guardrails: `5,53`.

### Engineering pivot: forced candidate probes
- Added `Convergence_ForceProbeTokens` so specific inactive tokens can be evaluated even when normal candidate generation is dead.
- First forced-probe batch:
  - pair `LEITELBENNAIFIININSBASTFNENIIFINI*LTASTTNVVN`, `*LEITELBENNAIFIININSBASTFNENIIFINI*LTASTTNVVN`
  - singleton `VEIINIAVNALLBEEILEEIEFFIFTLEITELBENNAIFIININSBASTFNENIIFINI*LTASTTNVVNNF`
- Both run with swallowed-superset telemetry enabled.

### AC010 branch status after forced probes
- `AC010` broad groups, precise wrappers, and singleton probes are effectively exhausted as workbook-only moves.
- Best signal in this branch came only after forced candidate probes.
- `forced_probe_leit_pair` produced real mechanical movement (`books_changed=2`, `Tokens -11`, GT clean) but regressed canonically improved books (`5,53`).
- Telemetry patch succeeded: first concrete `Swallowed by active superset` attribution observed in CandidatePromotions.
- Surgical unswallow shadow removed the regression pressure but still produced no visible book changes.
- Decision: close AC010 as a workbook-probe branch. Next move should be engineering on candidate generation / forced-probe workflows, not more wrapper peeling.

### Engineering pivot: isolated forced probes
- Added two runner controls in `bonelord_flow_next_iteration.py`:
  - `Convergence_ForceProbeOnly`
  - `Convergence_ForceProbeDisableTokens`
- Purpose: evaluate a tiny explicit token set in isolation, while temporarily removing known swallowing/noisy tokens from the local active set.
- First isolated batch will compare:
  - forced-only `LEIT/*LEIT`
  - forced-only `VEIINI...`

### Forced-only probe outcome
- `forced_only_leit_pair_probe` and `forced_only_veiini_probe` converged to the same result.
- They still regress `Book 53`, even after isolating the forced probe and disabling the known swallowing/noisy tokens.
- Conclusion: the AC010 hypothesis is exhausted not only as a workbook branch, but also as an isolated forced-probe branch.
- Next pivot should be code-side generation diagnostics above the current probe layer, or a different corpus/anchor family entirely.

### Engineering fix: forced probe can disable supersets
- `Convergence_ForceProbeTokens` now allows already-active tokens to be explicitly re-evaluated.
- Added `Convergence_ForceProbeDisableSupersets` + `Convergence_ForceProbeDisableSupersetsMax`.
- Rerunning isolated forced probes for `LEIT/*LEIT` and `VEIINI...` with local superset suppression enabled.

### Engineering pivot: ForceProbe family mode + tail closure
- Added `Convergence_ForceProbeSubstrings` + `Convergence_ForceProbeSubstringMaxMatches` in `bonelord_flow_next_iteration.py`.
- Result of first family batch on the swallowed superset family:
  - `prefix` and `core` were no-op (`books_changed=0`).
  - `tail` and `mixed-holdout` were the only lanes with uptake (`books_changed=2`, `Tokens -10`, GT clean).
- Local diff showed the tail gain was not promotable: it regressed the already-good corridor in `Books 5` and `53` by reintroducing `of died ... join`.

### Tail holdout batch
- Added exact-token holdouts against the three toxic parents promoted by `tail_v2`.
- Narrow tail lanes (`*NAESESTIENFATC`, `FAIFVI*NAESESTIENFATC`, `SETBASEFAIFVI*NAESESTIENFATC`) showed:
  - `parent` => pure no-op
  - `core/bridge` => still reintroduced `of died`, so not promotable
- Conclusion: the reusable tail scaffold is not independent under exact-token holdout.

### Engineering pivot: substring-level holdout
- Added `Convergence_ForceProbeDisableSubstrings` to remove active parents containing toxic substrings during local force-probe simulation.
- First substring holdout used:
  - `NTEIEIISETBASE`
  - `SEEIISETBASE`
  - `IVIFASTFNEIEINTAAETTAEFTEITILSBEIIN`
  - `INTAAETTAEFTNE`
- This was still insufficient at first, because the toxic candidate itself could still be promoted.

### Engineering fix: self-block for toxic force-probe substrings
- `Convergence_ForceProbeDisableSubstrings` now also blocks promotion of any forced-probe candidate containing one of the toxic substrings.
- Re-running `core` and `bridge` with self-block produced pure no-op shadows:
  - `core_substr_selfblock`: `books_changed=0`, `Tokens 318->318`
  - `bridge_substr_selfblock`: `books_changed=0`, `Tokens 318->318`
- Interpretation: the tail family has no independent promotable core. Its earlier movement was entirely coupled to the toxic parents.
- Decision: close the tail family branch and stop spending iterations on macro-family peeling here.

### Next pivot
- Move above macro-family level into structural composition / assembly:
  - inspect `AlignedBackbone_Auto`
  - inspect `VariantAssemblyBlocks_Auto`
  - inspect `SuperAnchors_Auto`
- Goal: find whether the real constraint is an assembly rule or boundary composition around the AC008 corridor, not another macro-family variation.

## 2026-03-07 - Canonical promotion landed: mid-right explicit superanchor

- Promoted `BEEILEEIEFFIFTLEITELBENNAIFIININSBAST` from shadow into canonical workbook.
- Locked token in `GlossaryRetext_LockedTokens`.
- Canonical run closed at `Iter 784` with:
  - `status=MODEL_CONVERGED`
  - `GT bad_enforced=0 | bad_all=0 | soft=0`
  - `books_changed=1/70`
  - `Tokens 316->316`
  - `EvAvg delta=0`
- Interpretation: promotion survived cleanly as a stable structural block, but produced only a narrow local effect, consistent with display/surface improvement rather than broad new semantic uptake.
- Follow-up probes in flight:
  - `explicit_midright_rightwrap1_probe.xlsx`
  - `explicit_midright_rightwrap2_probe.xlsx`
  - `book58_altomit_midright_forceprobe.xlsx`

## 2026-03-07 - Main-thread review loop on Book55 family

- Original `book55_fresh_skipdump_probe` reopened toxic regressions in `Books 5, 28, 53` (`of it -> of died`, `be I in vain -> be join vain`) despite mechanical gains.
- Broad lexical blockers did not change the outcome.
- Structural seamblock on `AEFTEI*ILSBEIIN` also failed to change the outcome.
- Root-cause extraction showed the toxic branch is being carried by longer active macros containing `TAEFTEITILSBEIIN` and `TAEFTEITFEIEALVNSBEIEFIANEFI`.
- `book55_exactmacroblock_probe` improved the branch materially:
  - `mech_promoted=6`
  - `books_changed=0`
  - `Tokens 316->307`
  - `GT bad_enforced=0 | bad_all=0 | soft=0`
  - no visible toxic surface regression in books
- `book55_leafholdout_probe` failed and reproduced the toxic profile.
- `book55_secondrung_probe` is the current active rung, adding `IVIFASTFNEIEINTAAETTAEFTEITILSBEIIN` to the exact blocker package.
- Current decision contract for this family:
  - Promote only if mechanical gain survives with zero toxic book flips and ideally some visible local improvement.
  - Keep in shadow if it remains mechanically cleaner than baseline but still lacks readable gain.
  - Abandon if second rung collapses to no-op or reopens the same toxic corridor.

## 2026-03-07 - Book55 branch review outcome

- `book55_exactmacroblock_probe` and `book55_secondrung_probe` converged to the same clean mechanical plateau:
  - `mech_promoted=6`
  - `books_changed=0`
  - `Tokens 316->307`
  - `GT bad_enforced=0 | bad_all=0 | soft=0`
- This means the toxic corridor was contained, but the second rung (`+ IVIFASTFNEIEINTAAETTAEFTEITILSBEIIN`) added no extra benefit.
- Decision: keep the Book55 branch in shadow as a clean-but-ambiguous mechanical branch. Do not promote.
- Next prioritized pivot: `SA002 omit-aware`.

## 2026-03-07 - Book55 promotion threshold clarified

- Subagent consensus matches main-thread reading:
  - `exactmacroblock` is a useful anti-toxic structural scaffold, not semantic promotion.
  - It only remains worth extending if a future rung is strictly better than:
    - `mech_promoted=6`
    - `Tokens 316->307`
    - `books_changed=0`
    - with zero toxic flips and no extra drop in reading metrics.
- If later rungs only repeat this plateau, the Book55 branch should be closed.
- Main-thread focus now shifts to `SA002 omit-aware`.

## 2026-03-07 - SA001/SA002 closure and new pivot

- `book58_altomit_seam_forceprobe_v2` closed as `READY` with `mech_promoted=0`, `books_changed=0`; classified as structural readout / no-op.
- `sa001_exact_anchor_seed_probe` closed as `READY` with `mech_promoted=0`, `books_changed=0`; seed did not enter DP.
- Both SA superanchor pivots are now considered exhausted in their current direct forms.
- Main-thread pivot moved to `anchor_rosetta_local_skipdump_fresh_probe`.

## 2026-03-07 - Hypotheses considered effectively closed

The following branches are now treated as effectively closed unless new evidence appears:
- `TE -> the`
- `Crib6 / IIN-family / Book60 / BTILBETA*`
- direct `3478` under `AnchorPromotionOnly`
- `Book38 / Hellgate head-macro peel`
- `AC010` as wrapper/workbook branch
- tail-peel family around `*NAESESTIENFATC / FAIFVI*...`
- `SA001/SA002` in their current direct forms

`Book55 exactmacroblock` remains shadow-only, not formally closed.

## 2026-03-13 - Reliability matrix (canonical audit)

### Stable enough to keep
- `Book 5 / Book 9 / Book 53` preserve the safer right-arm reading around `of it ... in vain`, i.e. they no longer carry the known toxic `of died / join vain` regressions.
- `Book 54` preserves a local contextual improvement around `IVNA -> vain`, but this is still stronger in context/display than in strict decode.
- `Book 59` preserves a local surface improvement around the mid-right block, but this is primarily punctuation/surface cleanup, not strong new semantics.

### Shadow-only scaffold
- `Book55 exactmacroblock`:
  - useful anti-toxic mechanical scaffold
  - `mech_promoted=6`
  - `Tokens 316->307`
  - `books_changed=0`
  - not semantically promotable

### Discarded / readout only
- `SA002 omit-aware` direct probe
- `SA001 exact seed` direct probe
- `SA001 left flank shortchain`
- `anchor_rosetta_local_skipdump_fresh`
- `mid-right structural` direct family
- direct `3478`
- direct `AC010` wrapper branch
- `Book38/Hellgate` macro peel

### Working reliability reading
- The canonical workbook is mechanically safer than the toxic shadows, but still has very limited strongly reliable semantic gains.
- Most surviving improvements are local and should not be overstated as language-wide convergence.

## 2026-03-13 - Main-thread acceleration

- Opened new parallel explorer fronts for:
  - AC013/017/019/020/021/022 cluster
  - exact external/rosetta anchors under strict regime
  - evidence taxonomy / anti-overclaim operational categories
- Main thread is mapping surviving glossary rows and external anchor sheets directly before choosing the next pivot.

## 2026-03-13 - Operational evidence taxonomy adopted

Evidence classes used by the main thread from now on:
- `anti-toxic`
- `surface-only`
- `mechanical scaffold`
- `local semantic`
- `discarded`

Promotion rule:
- `anti-toxic` can enter canonical as containment, not as translation progress.
- `surface-only` stays display-only.
- `mechanical scaffold` stays shadow-only.
- `local semantic` is the only class that counts as real translation progress.
- `discarded` closes the branch.

## 2026-03-14 - Main-thread admin/review loop
- Tarefa administrativa ativa da thread principal enquanto os lanes rodam:
  - manter um ledger de veredito por frontier
  - impedir reabertura de ramos mortos por inercia
  - vigiar reentrada no basin toxico `Books 5, 28, 53`
- Checklist de revisão para o frontier `AC017/AC019`:
  - qualquer delta em `Books 3, 17, 44, 52, 62, 68` conta como sinal local relevante
  - qualquer reentrada em `Books 5, 28, 53` com `of died / join vain` reprova o lane
  - `GT bad_enforced=0` e `soft=0` continuam obrigatorios
  - se `forceprobe` e `pairprobe` fecharem como no-op ou toxicos, o ombro `AC017/AC019` fecha como ramo de shadow tuning

## 2026-03-22 - Partial result: AC017/AC019 shoulder family
- Workbooks:
  - `tmp/ac017_019_shoulder_forceprobe.xlsx`
  - `tmp/ac017_019_pairprobe.xlsx`
- `shoulder_forceprobe`:
  - `CurrentIteration=785`
  - `status=READY`
  - `GT=0/0/0`
  - `changed_books=[]`
  - classification: `discarded` as clean no-op
- `pairprobe`:
  - `CurrentIteration=785`
  - `status=MODEL_CONVERGED`
  - `GT=0/0/0`
  - `changed_books=[5,28,53]`
  - toxic re-entry: `of died` / `join vain`
  - classification: `discarded`
- Conclusion:
  - the `AC017/AC019` shoulder closes as shallow tuning.
  - next frontier must come from outside `AC008` and outside the `AC013/017/019` shoulder family, or require a deeper runner patch rather than another workbook-only probe.

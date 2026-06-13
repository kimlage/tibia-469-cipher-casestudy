# Plan

Vamos operar o decoding como um loop contínuo de convergência sob restrições: batches curtos, lanes sombra, promoção canônica só com evidência e redução real de contradição, e logs automáticos no Discord sem pausar o fluxo. O objetivo não é mais “rodar iterações”; é eliminar corredores circulares, estabilizar hipóteses boas e abrir novas frentes até a tradução ficar semanticamente legível e auditável.

## Scope
- In:
  - execução contínua por batches com lanes estruturais, semânticas e de âncoras
  - uso controlado de subagentes em ciclos `wait -> close/reuse -> next batch`
  - promoção canônica apenas para ganhos auditáveis em leitura/contradição sem quebrar GT
  - logs automáticos de avanço e bloqueio em `bonelord-logs`
  - critério de parada humano para “tradução final”, separado de `MODEL_CONVERGED`
- Out:
  - tratar `MODEL_CONVERGED` como sinônimo de linguagem resolvida
  - promover hipóteses só porque “cabem” no texto
  - deixar lanes exploratórias mutarem o canônico sem passar por sombra

## Action items
- [in_progress] Formalizar o scheduler de execução contínua: batches de 2–4 lanes, no máximo 6 subagentes, sempre drenando o batch anterior (`wait + close/reuse`) antes do próximo.
- [pending] Manter quatro trilhas permanentes de trabalho: `Structural`, `Anchor`, `Semantic audit`, `Display-only stabilization`, cada uma com score próprio e sem misturar progresso mecânico com progresso de leitura.
- [pending] Executar apenas em workbooks sombra tudo que for hipótese estrutural ou interpretativa; promover para o canônico só quando `GT bad_enforced=0`, `soft=0`, `ExternalRoundTrip` estável e contradição local cair.
- [pending] Usar `GlossaryRetext_LockedTokens` para estabilizar tokens que já provaram ser vítimas de corredores circulares e impedir que o pipeline desfaça probes válidos na mesma iteração.
- [pending] Tratar `Book 55` como bloqueio estrutural de macro competition e abrir probes específicos para a família `VFETTIITA / VFETTII / ETTIITA / ETTIIT / TAV / IFAI`, sem reduzi-la a simples retext lexical.
- [pending] Manter uma frente alternativa contínua para seeds fortes não locais ao `Book 55`, priorizando `3478`, rosetta-local Bonelord/Beholder e outras âncoras externas que possam reduzir contradição semântica real.
- [pending] Publicar logs automáticos a cada batch importante em `bonelord-logs` com: lanes executadas, hipótese testada, resultado, regressões evitadas, e próximo alvo; não pausar para pedir confirmação.
- [pending] Parar apenas quando o runner estiver verde e, além disso, não houver oscilação ativa, os livros/contigs de maior risco estiverem semanticamente coerentes, e as traduções externas auditadas fizerem sentido humano consistente.

## Task status
- [done] Separação entre progresso mecânico, semântico e display no runner.
- [done] Renomeação do estado final técnico para `MODEL_CONVERGED`.
- [done] Criação do lock por token (`GlossaryRetext_LockedTokens`) no runner.
- [done] Estabilização canônica de `IVNA -> vain` após shadow probe limpo.
- [in_progress] Troca do alvo de otimização para redução de contradição semântica sob restrições.
- [in_progress] Preparação do próximo batch estrutural centrado em `Book 55`.
- [pending] Reabertura contínua de batches com subagentes reutilizados por lane.

## Implementation log
- [done] Runner já diferencia progresso real de progresso cosmético e não usa mais `PUZZLE_SOLVED` como proxy de tradução humana.
- [done] O corredor circular `IVNA: vain <-> yawn` foi identificado, isolado em sombra, validado sem regressão e estabilizado no canônico.
- [done] O diagnóstico atual mostra que `Book 55` não é um problema de palavra isolada; é competição de macros/parses.
- [done] O critério operacional agora passa a ser “redução auditável de contradição semântica”, não só melhora mecânica local.
- [in_progress] Abrindo o próximo batch com uma lane estrutural para `Book 55` e uma lane alternativa para sementes fortes fora dele.
- [pending] Consolidar os resultados do batch em probes sombra específicos e seguir promovendo apenas o que sobreviver aos guardrails.

## Open questions
- A família de `Book 55` está supersegmentada por macros espúrios ou subsegmentada por um macro dominante que mascara a fronteira real?
- O seed `3478` vai destravar só nomes/âncoras locais ou consegue irradiar estrutura para além do cluster Bonelord/Beholder?
- Quais livros/contigs devem compor o painel fixo de “risco semântico” para decidir convergência humana, além do GT mecânico?

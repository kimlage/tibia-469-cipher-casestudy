# E5 — Método Declarado do Autor & Lore (web research)

Date: 2026-06-21
Classification: `AUDIT_ONLY_NO_SEMANTICS`
Translation delta: `NONE`
Verdict: `NO_OFFICIAL_KEY_EVER_PUBLISHED` · postura oficial = mistério/flavor; lore de criação = "montado pelo grande calculador"
Plaintext claim: `False` · Case reopened: `False`

Backlog item **E5**: minerar entrevistas/declarações do autor (CipSoft/Chayenne/Knightmare) por um **método de construção declarado** e lore relevante. Acesso: WebSearch + WebFetch. Vários primários bloquearam (403/503/anti-bot) — gaps marcados; substância corroborada por ≥2 fontes independentes.

---

## TL;DR

- **Nenhum ground truth oficial número↔significado foi jamais publicado.** Confirma `CODES_CONFIRMED_EXTERNALLY = 0` do Outcome Ledger.
- **Postura oficial da CipSoft = mistério deliberado + "dicionários são falsos".** (1) Entrevista Chayenne 2009 respondeu à pergunta "dá pra entender a linguagem?" **na própria 469**, como piada. (2) Notícia oficial **"Buried Secrets" (tibia.com, 20/05/2021)**: in-lore, um boss distribuiu **dicionários FALSOS** da linguagem bonelord; um real "nunca foi encontrado".
- **A lore de criação descreve MONTAGEM, não escrita.** Livro *You Cannot Even Imagine*: **"It was me who assisted the great calculator to assemble the bonelords language."** Criação = **assemble** (montar) por um **calculator** — ponte direta com o achado mecânico B1 (montagem por copy-paste, message-free).
- **Corroboração externa do mecanismo (não do significado):** a análise comunitária TibiaSecrets derivou um mapa parcial que **bate 13/13 com a KeyTable canônica do projeto** e o mesmo mecanismo (homofônico, espelho/reversão-invariante, leading-zero). O mantenedor do repo 469 mais citado (s2ward) concluiu: **"I personally no longer believe that decryption is the way."**

→ Convergência total: **mecanismo (B1: copy-assembly)** + **lore ("montado pelo calculador")** + **postura oficial (sem chave, dicionários falsos)** + **estatística do projeto (não-linguístico, row0 hand-built)** apontam todos para o mesmo: **469 é um artefato construído, message-free, com textura matemática/de-montagem mas sem plaintext recuperável.**

---

## Achados por fonte

### Oficial / semi-oficial (CipSoft)

| Fonte | Data | Conteúdo (citação) | Provenance |
|---|---|---|---|
| Entrevista Chayenne (PortalTibia) | 15/05/2009 | Pergunta sobre a linguagem respondida **em 469**: `114514519485611451908304576512282177 :) 6612527570584 xD` — piada deliberada de que "a linguagem poderia ser traduzida para linguagem humana". Sem método revelado. | secundário (search + groundtruthsources); primário 403 |
| Notícia oficial **"Buried Secrets"** (tibia.com/news id=6148) | 20/05/2021 | In-lore: um boss **distribuiu dicionários FALSOS** da linguagem bonelord; um dicionário real "nunca foi encontrado". CipSoft sinaliza que as "traduções/dicionários" em circulação são **fakes**. | secundário (timeline s2ward + search); **primário bloqueado (403/Wayback bloqueado) — GAP** |
| Qualquer par número↔significado oficial | — | **Nenhum, jamais.** | confirmado por ausência em todas as fontes |

### Lore de criação in-game (o "como foi feito")

| Livro/NPC | Citação | Insight |
|---|---|---|
| **You Cannot Even Imagine** | "It was me who assisted **the great calculator** to **assemble** the bonelords language." | criação = **montagem por cálculo** → ponte direta com B1 (assembly) |
| A Wrinkled Bonelord | "It heavily relies on **mathemagic**"; "the name of our race is not fix but a **complex formula**, and as such it always **changes for the subjective viewer**"; "Numbers are essential. They are the secret behind the scenes." | textura matemática + **viewer-dependence** (camada de render/orientação) |
| Beware of the Bonelords | "blinking code with each eye… not only a language but also some kind of **mathematics**" | granularidade variável (eye/blink), math |
| Paradox Tower | "mirrored room… that **could be the cipher** for 469" | a propriedade **espelho/reversão-invariante** é até insinuada na lore |

### Comunidade (corroboração independente do mecanismo)

| Fonte | Achado | Relevância |
|---|---|---|
| **TibiaSecrets article160** ("The Great Tibian Cipher") | mapa parcial: 62=N,79=A,20=R,68=C,65=I,72=S,61=T,34=B,78=E,63=V,37=A,81=I,29=N | **bate 13/13 com a KeyTable do projeto** → corrobora a reconstrução de row0; mesmo mecanismo (homofônico, espelho, leading-zero). Conclusão otimista "solvable but incomplete" — **falsificada pelo projeto** |
| **s2ward/469** (repo mais citado) | "I personally no longer believe that decryption is the way." 71 livros all-números na Hellgate Library; "pares deliberados (esq>dir)" | mantenedor concorda com o veredito; "deliberate" ≠ "traduzível" |
| Isoge/Celesta (2013), German/MHG, etc. | "soluções" que decodificam 469 = "Bonelord" via dicionários de números reais | exemplos das soluções comunitárias **falsificadas** |

---

## Gaps (E5)

1. **Nenhuma declaração pública do desenvolvedor (Knightmare/Arndt Bednarzik ou qualquer dev CipSoft) sobre o MÉTODO de construção** (tabela à mão vs script vs RNG). Aparenta **não existir publicamente**. Esta é a única peça que E5 não pôde fechar — e é exatamente o que destravaria a Fórmula A de forma documental. Caminho restante: contato direto com o autor (fora de escopo) ou um futuro statement oficial.
2. **Verbatim exato da notícia oficial "Buried Secrets" (id=6148) não capturado** — tibia.com 403 e Wayback bloqueado neste ambiente. Substância ("dicionários falsos") corroborada por 2 fontes secundárias; o texto literal fica como gap verificável.
3. **Texto completo de *You Cannot Even Imagine*** — fandom/tibiawiki.com.br 403; passagem-chave ("great calculator… assemble") corroborada 3×, restante do texto não capturado.
4. **Primários bloqueados em massa** neste ambiente: tibia.fandom, tibiawiki.com.br, portaltibia, xenobot, reddit, tibia.com, web.archive.org (403/503/anti-bot). Trabalhei via raw.githubusercontent (s2ward), tibiasecrets (fetchável) e snippets de WebSearch. Recomenda-se re-rodar de um ambiente com acesso a esses domínios para capturar verbatims.

---

## Insights

**Metodológico:** o projeto já tinha registrado essas fontes (groundtruthsources, lore_audit, inspiration_model) mas como *material de validação/mecanismo*. E5 confirma que **não há nada novo a extrair semanticamente da web** — a comunidade tem a mesma parede. O valor de E5 é **negativo-confirmatório** e **convergente**: fecha "talvez exista uma declaração/chave oficial" como `buscado-negativo` (com o gap do verbatim oficial).

**Mecânico:** o mecanismo B1 (copy-assembly de banco) é **espelhado pela lore de criação** ("assemble … great calculator"). Os dois lados — estatística do corpus e mito de criação in-game — contam a mesma história: **montagem por cálculo, não composição de prosa.**

**De lore:** os quatro NPCs/livros (Wrinkled Bonelord, Beware of the Bonelords, You Cannot Even Imagine, Paradox Tower) codificam, em flavor, exatamente as propriedades estruturais que o projeto mediu: **math/calculation** (textura matemática), **subjective viewer** (render/orientação), **mirror** (reversão-invariância), **blinking/eye granularity** (homófonos/arity). Isto é forte evidência de que as propriedades são **design intencional de flavor**, não um canal de mensagem — a lore "explica" o mecanismo sem nunca prometer um plaintext.

## Impacto no Outcome Ledger

- Métricas semânticas: inalteradas (0/0/0-de-70/0). `CODES_CONFIRMED_EXTERNALLY` permanece 0 (nenhuma chave oficial existe).
- A postura oficial 2021 ("dicionários falsos") é **evidência do lado do autor a favor do veredito não-linguístico** — mas é meta-lore, não um par número↔significado, então não move métrica formalmente. Reforça a recomendação de **fechar**.

## Fontes (acessadas nesta sessão)

- s2ward/469 timeline e README (raw.githubusercontent.com) — fetch OK.
- tibiasecrets.com/article160, /article166 — fetch OK.
- WebSearch: entrevista Chayenne 2009, "Buried Secrets" 2021, "You Cannot Even Imagine" / great calculator, Knightmare/Bednarzik.
- Bloqueadas (gaps): tibia.com/news id=6148, tibia.fandom.com (You_Cannot_Even_Imagine, 469), tibiawiki.com.br, portaltibia.com.br, forumarchive.xenobot.net, reddit.com, web.archive.org.

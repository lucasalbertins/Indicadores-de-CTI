# BIA — comparativo entre a modelagem nova e a existente

**Programa:** PR50 — Programa de Bolsas de Incentivo Acadêmico (BIA)
**Fonte:** `prompt/context/Canvas da Estratégia BIA v.2 [consolidado.docx].pdf`
**Referência de estilo:** `src/.../PBPG/PBPG.oml`
**Gerado em:** 22/09/2026 · modelo `claude-opus-5`

Este documento registra o que mudou em relação aos arquivos que já estão em `src/`, e **por quê**. Nenhum arquivo existente foi alterado — tudo abaixo está em `prompt/export/BIA-claude-opus-5-22-09-2026/`, para validação antes de qualquer promoção.

---

## 1. Arquivos gerados

| Arquivo | Corresponde a | Situação |
|---|---|---|
| `BIA.oml` | `src/.../BIA/BIA.oml` | reescrito a partir do canvas v.2 |
| `PA_BIA.oml` | `src/.../BIA/PA_BIA.oml` | reestruturado (métricas movidas para `metricasBIA/`) |
| `metricasBIA/PA1.oml` | — | **novo** |
| `metricasBIA/PA2.oml` | — | **novo** |
| `metricasBIA/PA3.oml` | — | **novo** |
| `metricasBIA/PA4.oml` | — | **novo** |

Os IRIs são idênticos aos de produção, para que os arquivos possam ser movidos para `src/` sem edição. Como `prompt/` está fora do `catalog.xml`, não há conflito enquanto permanecerem aqui.

**Verificação automática executada:** 148 `base:id` declarados, **nenhum duplicado**; todas as referências entre os arquivos novos resolvem; todos os códigos compartilhados referenciados (`PC*`, `EN*`, `FE*`, `AC*`, `SA*`, `PU*`, `FI*`) existem hoje em `description/`.

**Não executado:** `./gradlew owlReason`. Os arquivos estão fora do catálogo, então o reasoner não os enxerga. A validação sintática real só acontece depois de promovidos para `src/` e registrados em `description/bundle.oml`.

---

## 2. Por que o canvas mudou tanto

O `BIA.oml` de `src/` foi construído a partir de uma versão anterior do canvas. O canvas v.2 consolidado é **bem mais enxuto**: 3 parceiros em vez de 7, 6 saídas em vez de 9, 4 fatores externos em vez de 6.

A maior parte das diferenças abaixo não é correção de erro de modelagem — é o canvas que mudou. Onde houve de fato divergência em relação ao canvas, está marcado com **⚠️**.

### Uma dificuldade específica deste canvas

Diferente dos canvas do PBPG e do BPP, **o canvas v.2 do BIA não traz os códigos**. Parceiros, entradas, atividades, saídas, públicos e fatores aparecem apenas como texto corrido; só objetivos e resultados vêm codificados.

Cada associação abaixo é, portanto, uma **interpretação** feita contra o `catalogo-de-codigos.pdf` (versão final 07/07/2026) e contra os nomes reais das instâncias em `description/` — e é exatamente o que precisa da sua validação.

---

## 3. Decisões de mapeamento

### 3.1 Parceiros-chave

Canvas: *IES Públicas · Escolas da Rede Pública · SECTI-PE*

| Item do canvas | Escolhido | Antes | Justificativa |
|---|---|---|---|
| Instituições de Ensino Superior (IES) Públicas | **PC3.3** — ICT/IES – Federais e Estaduais | PC3.1 | ⚠️ `PC3.1` é *"ICT (exceto IES)"* — **exclui explicitamente IES**, o oposto do que o canvas diz. O objetivo geral restringe a "federais ou estaduais", o que casa literalmente com `PC3.3`. |
| Escolas da Rede Pública | **PC3.10** — Escolas de ensino médio (EREM, ETE, outras) | PC1.1, PC1.2 | ⚠️ O catálogo não tem um código único para "rede pública"; separa ensino médio (`PC3.10`) de fundamental (`PC3.11`). O BIA recruta por desempenho no ENEM, logo ensino médio. |
| SECTI-PE | **PC1.1** — SECTI-PE | PC1.1 | correspondência exata, mantida. |

**Removidos:** `PC1.2` (SEPLAG-PE), `PC4.1` (Empresas públicas), `PC4.2` (Empresas privadas), `PC2.9` (Agências internacionais), `PC2.10` (Agências nacionais) — nenhum aparece no canvas v.2.

> **Ponto aberto:** "IES Públicas" também abrange as Autarquias Municipais de Ensino Superior (`PC3.4`), que são públicas. Usei só `PC3.3` porque o objetivo geral diz "federais ou estaduais". Se as autarquias municipais participam do BIA, `PC3.4` deve ser acrescentado.

### 3.2 Entradas

| Item do canvas | Código | Observação |
|---|---|---|
| Orçamento estadual - LOA FACEPE | `EN1.1` | Orçamento estadual - FACEPE |
| Câmaras da FACEPE | `EN3.5` | Câmaras de assessoramento da FACEPE |
| Avaliadores ad-hoc das propostas BIA | `EN3.7` | Avaliadores externos e ad-hoc |
| Recursos humanos de suporte ao BIA | `EN3.1` | RH FACEPE |
| Sistema de informação (AgilFAP) | `EN2.1` | AgilFAP |
| Estratégia estadual de CT&I | `EN5.1` | Estratégia Estadual CT&I |

**Removido:** `EN5.2` (Marco Legal Nacional de CT&I) — ausente do canvas v.2.

### 3.3 Fatores externos — a maior correção

Canvas: 1 oportunidade e 3 ameaças.

| Item do canvas | Escolhido | Antes | Justificativa |
|---|---|---|---|
| **AM** Cortes e contingenciamento de recursos estaduais para CT&I | **FE1.AM2** — Limitação orçamentária do governo do Estado para continuidade das ações | FE1.AM2 ✔ | mantido; é a formulação mais próxima no repositório. |
| **AM** Evasão dos estudantes dos cursos de graduação | **FE4.AM2** — Evasão estudantil | *ausente* | ⚠️ A ameaça central do BIA — o programa existe para combater evasão — **não estava modelada**. |
| **AM** Estrutura administrativa de suporte ao Programa BIA insuficiente | **FE3.AM4** — Estrutura administrativa de suporte ao programa insuficiente | FE2.AM2 | ⚠️ `FE2.AM2` é *"Lentidão e burocracia para investir e manter a infraestrutura"*, que é outra coisa. `FE3.AM4` é correspondência literal. |

**Removidos:** `FE5.OP6`, `FE4.OP1`, `FE2.OP1`, `FE1.AM3` — não constam do canvas v.2.

> **⚠️ Pendência — a oportunidade ficou sem código.** O canvas traz *"Uso dos indicadores do Programa BIA para estimular o aumento das contrapartidas das IES Públicas"*. Não existe instância equivalente em `fatoresExternos/`, e o catálogo só exemplifica fatores externos em vez de padronizá-los.
>
> **Deixei a oportunidade de fora do `condicionadoPor`** em vez de forçá-la num código que não a descreve. Criar a instância nova exige editar um arquivo compartilhado — depende da sua autorização. Sugestão: `FE5.OP14` em `fatoresDinamicaEcossistema.oml`, ou `FE2.OP3` se for lida como fator institucional.

### 3.4 Atividades-chave e saídas

O catálogo **não codifica AC nem SA** — esses códigos são sequenciais por acúmulo em `atividadesChave.oml` (AC1–AC25) e `saidas.oml` (SA1–SA34). O casamento foi por texto.

**Atividades — nenhuma mudança de conteúdo:** `AC1, AC2, AC3, AC4, AC6, AC7`. O arquivo antigo tinha o mesmo conjunto, apenas fora de ordem (`AC1, AC3, AC2, AC4, AC7, AC6`); reordenei para leitura.

**Saídas — reduzidas de 9 para 6:** `SA1, SA2, SA3, SA4, SA6, SA7`.
Removidos: `SA5` (Parcerias formalizadas), `SA8` (Seminário de avaliação), `SA9` (Soluções tecnológicas e inovadoras) — nenhum aparece no canvas v.2, e `SA5` é coerente com o desaparecimento da atividade de gestão de parcerias (`AC5`).

### 3.5 Público-alvo

Canvas — **diretos:** Estudante de graduação · Professores Doutores · IES Públicas. **Indiretos:** Escolas da Rede Pública · Governo · Sociedade.

| Item do canvas | Tipo | Escolhido | Antes | Justificativa |
|---|---|---|---|---|
| Estudante de graduação | direto | `PU1.10` | PU1.10 ✔ | exato. |
| Professores Doutores | direto | **`PU1.5`** — Professores de graduação | PU1.2 | ⚠️ O catálogo separa a família *Professores* (`PU1.3`–`PU1.6`) da família *Pesquisadores* (`PU1.1`, `PU1.2`). `PU1.2` é "Pesquisadores com doutorado" — muda o papel de docente para pesquisador. O canvas diz "Professores", e o BIA atua na graduação → `PU1.5`. |
| IES Públicas | direto | **`PU2.5`** — Instituições de Ensino Públicas ou Privadas | PU1.14 (direto) + PU2.5 (indireto) | ⚠️ O arquivo antigo representava o mesmo conceito **duas vezes**, em famílias diferentes e com tipos contraditórios. Consolidei em `PU2.5`, que é o único código que nomeia instituições de ensino; `PU1.14` é "ICTs", mais amplo. |
| Escolas da Rede Pública | indireto | **`PU2.6`** — Escolas de ensino médio | *ausente* | ⚠️ Público indireto do canvas que não estava modelado. Mesmo critério do `PC3.10`. |
| Governo | indireto | `PU2.2` | PU2.2 ✔ | Órgãos do governo estadual. |
| Sociedade | indireto | `PU5.1` | PU5.1 ✔ | Cidadão e sociedade em geral. |

> **Ponto aberto:** "Professores Doutores" não tem código exato — nenhum código cruza *docência* com *titulação*. `PU1.5` preserva o papel e perde a titulação; `PU1.2` faria o contrário. Se a titulação for o critério decisivo, o caminho correto é propor um código novo ao catálogo, não escolher entre os dois.

### 3.6 Objetivos e resultados

**Sem divergência.** Os 4 objetivos específicos, o objetivo geral e os 4 resultados já estavam corretos, e o mapeamento `buscaAtingir` reproduz fielmente os colchetes do canvas:

- `RE.CP1` ← OB.ES1
- `RE.MP1` ← OB.ES2 **e** OB.ES3 (canvas: `[OB.ES{2,3}]`)
- `RE.LP1`, `RE.LP2` ← OB.ES4

Ajustes textuais apenas: espaço espúrio em `"PIBIC/ FACEPE"` e a descrição do programa, que dizia *"exames vestibulares"* quando o canvas (e o próprio OB.GE do arquivo antigo) diz **ENEM**.

### 3.7 Identificação do programa e versão

| Campo | Antes | Depois | Motivo |
|---|---|---|---|
| `PR50 base:nome` | `"BIA"` | `"Programa de Bolsas de Incentivo Acadêmico"` | nome por extenso do cabeçalho do canvas; alinha com o padrão do PBPG. **Atenção:** consultas que filtram por nome (como `Q7.sparql`) passam a casar pelo nome completo. |
| `CanvasPR50 base:nome` | `"Canvas do BIA"` | `"Canvas do Programa de Bolsas de Incentivo Acadêmico"` | idem. |
| `base:versao` | `V1-Homologado` | `V2-Consolidado` | o canvas é a v.2 consolidada; ainda não homologada. |
| `base:dataCriacao` | `2026-03-11` | `2026-09-22` | data da modelagem. O canvas v.2 não traz data própria — **confirme se há uma data oficial**. |

---

## 4. Métricas e fórmulas

### 4.1 O que havia

`PA_BIA.oml` declarava 16 métricas com apenas nome, descrição, id e fontes. **Nenhuma** tinha `finalidade`, fórmula ou estratificação — ou seja, não eram calculáveis nem avaliáveis contra meta.

### 4.2 Duplicação corrigida

A métrica **"Número Total de Concluintes da Bolsa BIA"** estava declarada **três vezes** — `PA2.ME2`, `PA3.ME2` e `PA4.ME2` — como três indivíduos distintos, com a mesma definição e ids diferentes.

Consolidei em uma única instância, `PA2.ME2`, referenciada pelas três questões via `temMetrica`. É exatamente o denominador comum das taxas de PA2, PA3 e PA4.

`PA3.ME2` e `PA4.ME2` foram removidas. **Os ids das demais métricas não foram renumerados** — `PA3.ME3`, `PA4.ME3`, `PA4.ME4` e `PA4.ME5` mantêm seus identificadores. Isso deixa lacunas visíveis na numeração (não há `PA3.ME2` nem `PA4.ME2`), o que é intencional: renumerar quebraria qualquer referência externa e dificultaria a conferência contra o documento de origem do plano.

### 4.3 Métricas novas

Duas métricas foram acrescentadas porque as taxas existentes eram **incalculáveis sem elas** — a descrição citava um denominador que não existia como métrica:

| Nova | Existe para |
|---|---|
| `PA1.ME4` — Número Total de Bolsistas BIA | denominador de `PA1.ME2` (Taxa Evasão Bolsista) |
| `PA1.ME5` — Taxa Evasão Geral do Curso | divisor de `PA1.ME3`, que compara a evasão do bolsista com a do curso |

### 4.4 Fórmulas OpenMath

22 fórmulas, restritas às três operações já em uso na ontologia — **nenhuma operação nova foi introduzida**:

| Operação | Uso | Qtd. |
|---|---|---|
| `fns1#identity` | contagem lida direto da fonte | 9 |
| `arith1#divide` | razão | 7 |
| `arith1#times` | multiplicação por 100 nas taxas | 6 |

Toda taxa percentual segue o padrão do PBPG — `times(divide(a, b), 100)`, com a divisão aninhada via `tipovalorFormula`. `PA1.ME3` é a única razão pura (`divide`), por comparar duas taxas já percentuais.

Todas as 16 métricas receberam `finalidade`: **Minimizar** para as de evasão (`PA1.ME1`, `PA1.ME2`, `PA1.ME3`, `PA1.ME5`) e **Maximizar** para as demais.

### 4.5 Estratificações

Extraídas das próprias descrições das métricas, que já diziam "desagregado por...": Ano ou Semestre, Grande Área do Conhecimento FACEPE, Curso de Graduação, Região de Desenvolvimento do Estado e — em PA2.ME4/ME5 — Tipo de Programa; em PA3, Atividade Econômica.

Declaradas **uma vez por questão** e compartilhadas entre as métricas daquela questão, em vez de repetidas por métrica.

### 4.6 Desvio de convenção — leia antes de aprovar

No PBPG e no BPP, cada métrica detalhada fica em seu próprio arquivo (`metricasPBPG/PA1.ME1.oml`), e esse arquivo **redeclara** a métrica com um id diferente (`"PA1.ME3_BPP"`) da que está no plano (`"PA1.ME3 - BPP"`). O resultado é que a mesma métrica existe como dois indivíduos no grafo.

Como a orientação foi não duplicar, fiz diferente: **cada métrica é declarada uma única vez**, dentro de `metricasBIA/`, e o `PA_BIA.oml` a referencia. Consequências:

- os arquivos são agrupados **por questão de avaliação** (`PA1.oml`…`PA4.oml`), não um por métrica — 4 arquivos em vez de 16;
- a direção da dependência inverte: `PA_BIA.oml` passa a fazer `extends` de `metricasBIA/*`.

Se a equipe preferir manter um arquivo por métrica, a divisão é mecânica. Se preferir o padrão do BPP com redeclaração, é só dizer — mas aí a duplicação volta.

---

## 5. Resumo quantitativo

| Elemento | Antes | Depois |
|---|---|---|
| Parceiros-chave | 7 | 3 |
| Entradas | 7 | 6 |
| Fatores externos | 6 | 3 (+1 sem código) |
| Atividades-chave | 6 | 6 (mesmo conjunto) |
| Saídas | 9 | 6 |
| Públicos-alvo | 6 | 6 (3 trocados) |
| Objetivos (GE + ES) | 1 + 4 | 1 + 4 |
| Resultados esperados | 4 | 4 |
| Métricas | 16 (3 idênticas entre si) | 16 (−2 duplicatas, +2 novas) |
| Métricas com fórmula | 0 | 16 |
| Fórmulas | 0 | 22 |
| Estratificações | 0 | 16 |

---

## 6. Pendências que dependem de decisão

1. **Oportunidade sem código** (§3.3) — criar a instância em `fatoresExternos/` ou deixar o canvas sem oportunidade modelada.
2. **`PC3.4` — Autarquias Municipais** (§3.1) — incluir entre os parceiros?
3. **"Professores Doutores"** (§3.5) — aceitar `PU1.5`, voltar para `PU1.2`, ou propor código novo ao catálogo.
4. **Anotação de edição no canvas** — `RE.MP1` traz, no PDF, a marca *"(colocar em outro resultado)"*. Modelei o resultado sem ela, mas isso indica que os autores pretendiam desmembrar `RE.MP1`. Se o desmembramento acontecer, o vínculo `OB.ES2`/`OB.ES3 → RE.MP1` muda.
5. **Data oficial da v.2** (§3.7).
6. **Registro no bundle** — ao promover para `src/`, os quatro arquivos de `metricasBIA/` precisam de `includes` em `description/bundle.oml`, senão o reasoner os ignora.
7. **Nome do programa por extenso** (§3.7) — confirma a troca de `"BIA"` pelo nome completo?

---

## 7. O que não foi tocado

Nenhum arquivo existente do repositório foi modificado. Em particular, permanecem intactos os arquivos compartilhados (`parceirosChave/`, `entradas/`, `fatoresExternos/`, `publicosAlvo/`, `atividadesChave.oml`, `saidas.oml`), o `description/bundle.oml` e os arquivos atuais do BIA em `src/`.

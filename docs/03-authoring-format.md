# 03 — Authoring Format (`DocSource`)

`DocSource` is the boundary between content production and formatting. It is
what the thesis agent writes and what a human edits. Getting it right is the
most consequential decision in the project, because everything upstream and
downstream depends on it.

Agents should start from the **current** dialect and playbook:
[`dialect/docsource.md`](../dialect/docsource.md) and
[`playbooks/uni-figmm-thesis/PLAYBOOK.md`](../playbooks/uni-figmm-thesis/PLAYBOOK.md)
([13](13-agent-input.md) is only a pointer). This document is the full target
design. If they disagree about what a build accepts **today**, fix dialect +
playbook first.

## Shape

A `DocSource` is a folder, not a file.

```
thesis-project/
├── document.yaml            manifest: profile, metadata, section order
├── references.bib           bibliography
├── assets/
│   ├── malla-optimizada.png
│   └── mapa-conceptual.png
└── sections/
    ├── 01-planteamiento.md
    ├── 02-objetivos.md
    ├── 03-marco-teorico.md
    ├── 04-diseno-metodologico.md
    ├── 05-administracion.md
    ├── anexo-1-matriz.md
    └── anexo-2-cronograma.md
```

**Structured skeleton, free-form body.** The manifest is small, strict, and
schema-validated. The prose is Markdown, where errors are local and a human can
read it. One file per section, which is how an agent has to work on a 150-page
document anyway.

## Why not JSON

<a name="why-not-json"></a>
The tempting design is to have the agent emit the intermediate representation
directly as JSON. We reject it, and the reason is quantitative.

From the [audit](reference/reference-thesis-audit.md): 216–266 words per page,
and the approved 134-page thesis holds 2,074 paragraphs. A 150-page thesis is
therefore ~33,000–40,000 words — roughly 45,000 tokens of prose across ~2,300
paragraphs.

A nested JSON node for a single paragraph:

```json
{ "type": "paragraph", "children": [ { "type": "text", "text": "…" } ] }
```

That wrapper costs ~20–25 tokens of pure structure per paragraph.

| Format | Structural overhead | Total agent output |
|---|---|---|
| Nested JSON IR | **~50,000 tokens** | ~95,000 tokens |
| Markdown (blank line between paragraphs) | **~3,000 tokens** | ~48,000 tokens |

JSON more than doubles what the agent must write, and the majority of the
addition is punctuation. But cost is the least of it. Three failure arguments
matter more:

1. **Failure is global instead of local.** One unescaped quote in paragraph
   2,000 and the entire document fails to parse. In Markdown, a malformed figure
   block breaks *that figure*; the other 37 render. Across ~2,300 generated
   nodes the probability of at least one malformation is high — what matters is
   the blast radius.
2. **Models are far more reliable in Markdown.** It is pervasive in training
   data. Emitting ~35,000 words of prose inside JSON string literals with
   correct escaping is close to the worst thing you can ask a model to do at
   length.
3. **Nobody can review prose inside JSON.** We want the author and the advisor
   to read and correct the content. Markdown is diffable and reviewable; JSON
   string blobs are not.

The counter-argument — that JSON gives schema validation and constrained
decoding — is real but is satisfied elsewhere: the manifest *is* strict YAML with
a schema, and the prose is validated after parsing, with error locations that
point at a line in a file a person can open.

**So: Markdown + YAML is the authoring format. The JSON-shaped IR exists, but it
is internal to the compiler and is never authored by hand.** This resolves an
ambiguity that a naive design leaves open — whether the agent writes the IR or
writes Markdown. The answer is that those are different layers, and only one of
them is a human-facing contract.

## The manifest

```yaml
schema_version: 1
profile: uni-figmm/thesis-final@2024
language: es-PE

meta:
  institution: Universidad Nacional de Ingeniería
  faculty: Facultad de Ingeniería Geológica Minera y Metalúrgica
  document_kind: TESIS
  title: >-
    Automatización del cálculo y diseño de mallas de perforación optimizadas
  degree_statement: Para obtener el título profesional de Ingeniero de Minas
  author:  { name: "…" }
  advisor: { name: "…", title: "Msc." }
  place: LIMA – PERÚ
  year: 2024
  keywords_es: [mallas de perforación, sobrerotura, costos de sostenimiento]
  keywords_en: [drill grids, overbreak, support costs]

bibliography: references.bib
citation_style: apa-7

frontmatter:
  - cover
  - dedication:      sections/00-dedicatoria.md
  - acknowledgements: sections/00-agradecimientos.md
  - abstract_es:     sections/00-resumen.md
  - abstract_en:     sections/00-abstract.md
  - toc
  - list_of_tables
  - list_of_figures
  - list_of_annexes
  - introduction:    sections/00-introduccion.md

body:
  - sections/01-parte-introductoria.md
  - sections/02-marcos-teorico-conceptual.md
  - sections/03-desarrollo.md
  - sections/04-analisis-resultados.md

backmatter:
  - conclusiones:    sections/90-conclusiones.md
  - recomendaciones: sections/91-recomendaciones.md
  - references
  - annexes:
      page_numbering: { format: arabic, restart: 1 }
      items:
        - sections/anexo-1-precio-voladura.md
        - { file: sections/anexo-8-matriz.md, wide: true }
        - { file: sections/anexo-9-cronograma.md, wide: true }
```

Four things to note:

- **`profile` is versioned.** An institution's requirements change between
  years; documents must be reproducible against the version they were built
  for. The same faculty has two kinds — `thesis-final` and `thesis-proposal` —
  sharing one style layer.
- **Slots come in two flavours.** `cover` and the four index slots are
  **generated** from `meta` and from the document itself — nobody types a table
  of contents. `dedication`, `acknowledgements`, the two abstracts and
  `introduction` are **authored**, so they name a file.
- **Keywords live in `meta`, not in prose.** The approved thesis renders them as
  "Palabras clave — …" and "Keywords — …" at the end of each abstract; that
  formatting is the profile's job.
- **Structural facts are declared; mechanisms are not.** The annexes restart
  page numbering at 1, and two specific annexes are marked `wide: true` because
  their tables need more width than the text block. Note what the manifest does
  *not* say: it never says "landscape". Rotating the page is one medium's way of
  giving content more width, and choosing it belongs to the profile — which is
  what lets the same source produce a landscape section in Word and a scroll
  container in HTML. See
  [Semantic IR](04-semantic-ir.md#the-exception-boundary).

## Section files

Standard Markdown carries most of the load. Headings are headings; lists are
lists; pipe tables are tables; emphasis is emphasis.

Two rules that matter:

**Headings are never numbered by hand.** Write `## Justificación y Alcances`,
not `## 1.2 Justificación y Alcances`. The engine assigns `1.2`. The audited
thesis has three headings numbered `1.1.2.1` because a human did this job; we do
not repeat that.

**Heading level maps to document level.** In a body section file, `#` is the
chapter, `##` is level 2, `###` is level 3. The chapter title text is written
without the `Capítulo III.` prefix — the engine adds it, in the profile's
language and numbering style.

```markdown
# Marcos teórico y conceptual

## Marco teórico

### Sobrerotura en minería subterránea

La sobrerotura es la fracción de sección excavada por encima de la sección
planificada, y se cuantifica como un porcentaje [@vidal2020].

:::equation {#eq:sobrerotura}
\text{Sobrerotura}\,\% = \frac{S_{real} - S_{planificada}}{S_{planificada}} \times 100
:::

Con $S_{real} = 12.4$ m² y $S_{planificada} = 10.8$ m² la sobrerotura es del
14.8%, por encima del umbral discutido en @tbl:fijacion.
```

The engine turns `# Marcos teórico y conceptual` into
"Capítulo II. Marcos teórico y conceptual", numbers `##` as `2.1` and `###` as
`2.1.1`, and tags the equation `(1)`. The author writes none of those.

## Math

Math is the dominant element in this document family — 141 equations in the
approved thesis, 163 in the proposal. It has to be frictionless.

| Form | Syntax | Notes |
|---|---|---|
| Inline | `$…$` | ~115 uses in the approved thesis |
| Display, **numbered** | `:::equation {#eq:name}` | The approved thesis numbers `(1)`…`(47)` |
| Display, unnumbered | `$$…$$` | For equations that are shown but not referenced |

LaTeX notation inside; the backend converts to OMML for Word.

**The reference profile numbers equations**, globally and sequentially, so the
labelled form is the normal one. An author never writes the number — the engine
assigns it. The approved thesis, numbered by hand, has 50 tags for 47 numbers
with duplicates and one out of order.

## Fenced blocks

For the things Markdown cannot express, a **closed** set of fenced blocks. The
syntax is Pandoc's fenced-div notation, which is simple to parse and already
understood by the toolchain we render through.

The block vocabulary is closed on purpose. Every extension is something the
agent can get wrong and something the compiler must handle. Anything not in this
list is left to the manual 5%.

### Figure

```markdown
:::figure {#fig:sobrerotura}
src: assets/sobrerotura.png
title: Imagen representativa de la sobrerotura.
note: El gráfico resalta la zona roja como la sobrerotura.
width: 100%
:::
```

`width` is **relative only** — a percentage of the text block, or `natural`.
Absolute units (`8cm`, `300px`) are rejected by validation: they mean nothing in
HTML and break silently when a profile changes its margins. This is the one
declared presentational exception in the whole data model, and it is bounded on
purpose — see [Semantic IR](04-semantic-ir.md#the-exception-boundary).

The engine renders this as four blocks — label, title, image, note — each with
its own Word style, exactly as the approved thesis does:

```
Figura 1                                      XFIGURAS  ← engine-assigned label
Imagen representativa de la sobrerotura.      X1
[IMAGE]                                       X2
Nota: El gráfico resalta la zona roja…        X3
```

`title` and `note` are separate fields because APA 7 treats them as separate
blocks, and because **the label's style is the source for the Índice de
figuras** — a merged caption string would put the title into the index too. A
single `caption` string cannot express this; see the
[audit](reference/reference-thesis-audit.md#7-caption-pattern--exact-from-the-approved-document).

### Table

```markdown
:::table {#tbl:fijacion}
title: Valores de factor de fijación y relación (S/B) de los tajeos.
note: Fuente Manual de perforación y voladura de rocas (p. 314).
header_repeat: true
---
| Sección | Factor de fijación | Relación S/B |
|---------|--------------------|--------------|
| Tajeo   | 1.45               | 1.25         |
| Contorno| 1.20               | 0.80         |
:::
```

The `---` separates the block's metadata from its Markdown body.

### Labelled equation

```markdown
:::equation {#eq:sobrerotura}
\text{Sobrerotura}\,\% = \frac{S_{real} - S_{planificada}}{S_{planificada}} \times 100
:::
```

Rendered as a centered paragraph with an engine-assigned tag:

```
        [ centered equation ]  (1)
```

### Wide

```markdown
:::wide
(blocks that need more width than the text block)
:::
```

Says what the content needs, not how to give it. For our DOCX profile this
becomes a landscape section; another backend may do something else entirely.
Writing `:::landscape` here would bake a Word page concept into the authoring
format and break that.

### Raw escape hatch

```markdown
:::raw {target=docx}
(backend-specific content, passed through untouched)
:::
```

Deliberately unpleasant to use. It exists so that a blocked document can still
ship, and every use of it is reported as a finding so it does not quietly become
the normal way to do things.

## Cross-references and citations

| Purpose | Syntax | Becomes |
|---|---|---|
| Cross-reference | `@tbl:fijacion`, `@fig:sobrerotura`, `@eq:sobrerotura` | A live Word reference field: "Tabla 5", "Figura 12", "(1)" |
| Section reference | `@sec:marco-teorico` | "sección 2.1" |
| Citation | `[@vidal2020]` | "(Vidal, 2020)" |
| Narrative citation | `@vidal2020` | "Vidal (2020)" |
| Page-specific | `[@vidal2020, p. 14]` | "(Vidal, 2020, p. 14)" |

Citation syntax is Pandoc's, so a standard citation processor and standard
`.bib` files work unmodified, and APA 7 comes from the public style repository
rather than from us. Reimplementing citation styles is a multi-year trap and we
will not enter it.

The approved thesis confirms **APA 7** for the bibliography, with a 1.27 cm
hanging indent. IEEE appears only in the front-matter "how to cite" table — a
faculty form for citing *that* thesis, not the bibliography style — and that
table is out of v1 scope.

## What is deliberately absent

| Absent | Why |
|---|---|
| ORCID iDs, the "how to cite" tables | Institution-specific boilerplate; assigned to the manual 5% |
| Footnotes, endnotes | Zero in all three audited documents |
| Code blocks | Zero in all three audited documents |
| Manual heading, table, figure or equation numbers | The engine's job; every audited document got them wrong |
| Chapter prefixes (`Capítulo II.`) | Generated. The approved thesis is missing one |
| Any font, size, margin, colour or spacing | That is the profile's job, not the author's |
| Page breaks | A style property on the heading, not hand-placed. The approved thesis has 32 manual breaks |
| Absolute widths, orientations, or any other mechanism | The author says what content *needs*; the profile decides how |
| A hand-written table of contents or list of tables | Generated |
| Word style names | Would couple the authoring format to one backend |

The last two rows are the load-bearing ones. The moment an author can write
`{.TITU2}` or "12pt", `DocSource` stops being portable and the future LaTeX
backend becomes a rewrite.

## Validation

Two levels, both before any rendering:

1. **Manifest schema.** Strict. Unknown keys are errors, not warnings —
   silently ignoring a misspelled key is how an agent's output drifts.
2. **Content vocabulary.** Every fenced block is a known type with known fields.
   Every `@ref` resolves to a declared label. Every `src` exists. Every citation
   key is in the bibliography. Heading levels do not skip.

Errors report a file and a line number, because the person fixing them opens
that file.

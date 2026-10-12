# Reference Profile — UNI-FIGMM Thesis (2024–2026)

The first real profile. Every value is derived from the
[Reference Thesis Audit](reference-thesis-audit.md) and marked as **measured**
or **decided**. Nothing is assumed.

- **Institution:** Universidad Nacional de Ingeniería (UNI)
- **Faculty:** Facultad de Ingeniería Geológica Minera y Metalúrgica (FIGMM)
- **Specification:** an **approved, complete, formatted** undergraduate thesis
  (134 pages) — document A in the audit
- **Stability check:** a master's thesis proposal (73 pages) — document B

> **The approved thesis is the specification.** The faculty does not publish its
> template, and no written rulebook is available to us, so this profile is
> derived **~100% from the approved thesis** — a document the faculty
> *accepted*. That is a defensible basis rather than an ideal one: it cannot
> supply prohibition-type rules, and it proves that its own defects were
> tolerated once, not that they are permitted. See
> [D24](../11-decision-log.md#d24--the-approved-thesis-is-the-specification).
>
> Document B's only role is a stability check. Where two documents by different
> authors from the same template agree on a property, that property belongs to
> the **template** rather than to one author's direct formatting. Everything
> marked *stable* below passed that check. Document B is a thesis proposal and
> contributes nothing normative to the style layer.

## Two profiles, one style layer

The two audited documents are different **document kinds** sharing an identical
**style layer**:

| Profile | Source | Structure | Priority |
|---|---|---|---|
| `uni-figmm/thesis-final@2024` | Document A (approved) | Full thesis: chapters I–IV, conclusions, recommendations | **Primary** |
| `uni-figmm/thesis-proposal@2026` | Document B | Proposal: chapters I–V ending in schedule, budget, funding | Secondary |

Both `extends: uni-figmm/base` — which carries page setup, styles, captions,
numbering and pagination, all derived from the approved thesis. Only the
`schema` block differs.

`thesis-final` is the target. `thesis-proposal` is cheap to add once the base
layer exists — a different required-chapter list and nothing else — which is
exactly the test of whether the schema/style seam is real.

---

## Page setup — measured, stable in both documents

| Property | Value |
|---|---|
| Page size | A4 (21.00 × 29.70 cm) |
| Margin left | **3.00 cm** (binding edge) |
| Margin top / bottom / right | **2.50 cm** |
| Annex landscape section | 29.70 × 21.00 cm; margins 3.00 / 2.50 / 2.50 / 2.50 |

**Derived text width, portrait: 15.50 cm.**
**Derived text width, landscape: 24.70 cm.**

**Decision — normalise to 2.50 cm.** One section in *each* audited document has
2.54 cm margins. 2.54 cm is exactly one inch, Word's default, so it was never
deliberately set. Two independent authors producing the same artefact confirms
drift rather than intent.

### Page numbering — three regions, measured

| Region | Orientation | Numbering | Footer |
|---|---|---|---|
| Cover | Portrait | None | None |
| Front matter | Portrait | `lowerRoman` (v … xv observed) | Yes |
| Body | Portrait | Arabic, **restart at 1** (1 … 106 observed) | Yes |
| Annexes | Portrait, then **landscape** for the wide ones | Arabic, **restart at 1** | Yes |

The annexes carry their own page sequence restarting at 1 — the annex index
lists "Anexo 1 … 1", "Anexo 2 … 2". Both documents do this.

Footer: `PAGE \* MERGEFORMAT`, right-aligned, Arial 10pt, paragraph style
`Piedepgina`.

---

## Style hierarchy — measured from the approved document

```
Normal              Arial, justified, line spacing 2.0, space-after 0
│                   size inherited from document defaults: 11pt   ← decided, see below
├── PARRAFOS        + first-line indent 1.27 cm      ← default body paragraph
│   └── NORMALES    + first-line indent 0            ← standalone paragraph
│       ├── TITU1   Arial Bold 14pt, bold, centered, space-after 18pt
│       ├── XANEXOS (inherits)                       ← annex heading + index source
│       └── Dedicatoria  + italic, right-aligned     ← dedication page
├── TITU2           Arial Bold, bold, no indent      ← level-2 heading
│   └── TITU3       + italic                         ← level-3 heading
├── XTABLAS         Arial Bold, bold                 ← table label + index source
├── XFIGURAS        Arial Bold, bold                 ← figure label + index source
├── X1              italic, single-spaced            ← caption title
├── X2              9pt, centered, single-spaced     ← image container / table header cell
├── X3              9pt                              ← caption note / table body cell
├── TDC1            (inherits Normal)                ← index entry
└── Piedepgina      Arial 10pt, right-aligned        ← footer
```

### Semantic role → style mapping

| Semantic role | Style | Source |
|---|---|---|
| `body` | `PARRAFOS` | Measured, stable |
| `body_standalone` | `NORMALES` | Measured, stable |
| `chapter_title` | `TITU1` | Measured, stable |
| `top_level_section_title` | `TITU1` | Measured — same style, different role; see below |
| `heading_2` | `TITU2` | Measured, stable |
| `heading_3` | `TITU3` | Measured, stable |
| `table_label` | `XTABLAS` | Measured (approved doc only) |
| `figure_label` | `XFIGURAS` | Measured (approved doc only) |
| `caption_title` | `X1` | Measured (approved doc only) |
| `caption_note` | `X3` | Measured |
| `image_container` | `X2` | Measured |
| `table_header_cell` | `X2` | Measured |
| `table_body_cell` | `X3` | Measured |
| `equation` | `PARRAFOS`, centered | Measured |
| `annex_heading` | `XANEXOS` | Measured |
| `dedication` | `Dedicatoria` | Measured (approved doc only) |
| `index_entry` | `TDC1` | Measured |
| `bibliography_entry` | `PARRAFOS` + hanging indent 1.27 cm | Measured |
| `page_number` | `Piedepgina` | Measured |

### `TITU1` has two roles

It formats **numbered chapters** ("Capítulo I. Parte introductoria del trabajo")
and **unnumbered top-level sections** (Resumen, Abstract, Introducción,
Conclusiones, Recomendaciones, Referencias bibliográficas, Anexos).

The profile therefore distinguishes `chapter` — which receives the
`Capítulo {roman}.` prefix — from `top_level_section`, which does not. Both
bind to `TITU1` and both feed the general index.

---

## Indexes — four live style-driven TOC fields

This is the mechanism, measured from the approved document:

```
TOC \h \z \t "TITU1;1;TITU2;1;TITU3;1"     → Tabla de Contenido
TOC \h \z \t "XTABLAS;1"                   → Índice de tablas
TOC \h \z \t "XFIGURAS;1"                  → Índice de figuras
TOC \h \z \t "XANEXOS;1"                   → Índice de anexos
```

Three things follow, and they are the most useful findings in the whole audit:

**The label style is the index source.** Emitting "Tabla 5" with style
`XTABLAS` both formats it bold *and* produces its entry in the Índice de tablas.
No separate index-building step is needed.

**Do not rely on `outlineLvl`.** An earlier plan was to add outline levels to
`TITU1/2/3` so a standard TOC field could see them. Unnecessary — the `\t`
switch works without them — and insufficient, since outline levels could never
produce the table, figure or annex indexes. We reproduce the approved
mechanism. Setting `outlineLvl` anyway, purely so Word's navigation pane works,
is harmless and optional.

**The general index is flat, and we reproduce that.** All three heading styles
map to TOC level 1, so every entry renders as `TDC1` with no depth indentation.
`TDC2` and `TDC3` exist in the template but are unused. Indenting by depth would
look better; it would also differ visibly from the document the faculty
accepted, and we have no rulebook to appeal to. **Decided: reproduce the
approved output.**

---

## Captions — measured, four blocks

**Figures:**

```
Figura 1                                         XFIGURAS   label
Imagen representativa de la sobrerotura.         X1         title  (italic)
[IMAGE]                                          X2         content
Nota: El gráfico resalta la zona roja como…      X3         note
```

**Tables:** identical shape, with the table replacing the image.

```
Tabla 1                                          XTABLAS    label
Valores de factor de fijación y relación (S/B).  X1         title  (italic)
[TABLE]
Nota: fuente Manual de perforación y voladura…   X3         note
```

**Decided:** label and title **above**, note **below**, for both figures and
tables. Note prefix is **`Nota:`** with a colon, as in the approved document.
Label and title are separate paragraphs with no separator character.

Numbering is **global and sequential** — Figura 1…82, Tabla 1…23 — not per
chapter.

The commonly repeated convention "figures captioned below, tables above" is
Chicago/IEEE and would be wrong here.

---

## Equations — measured, and numbered

| Property | Value |
|---|---|
| Count | 141 (26 display) in the approved document; 163 in the proposal |
| Font | Cambria Math |
| **Numbering** | **Global sequential `(1)` … `(47)`** |
| Layout | Centered paragraph, style `PARRAFOS`, tag as parenthesised text after the equation |
| Separator | **None** — no tab, no right alignment |

This is a simpler layout than a right-margin-aligned tag, which is good news: it
needs no invisible-table workaround. A `SEQ` field inside a centered paragraph
is sufficient.

The approved document's manual tags are wrong — 50 tags for 47 numbers, with
duplicates and one out of order.

---

## Bibliography — measured

The reference list is unambiguously **APA 7**:

```
Vidal, M. (2020). Voladura controlada aplicando el modelo matemático de
    Holmberg… [Tesis de pregrado, Universidad Nacional del Centro del Perú].
    Repositorio institucional.
```

| Property | Value |
|---|---|
| Style | **APA 7** |
| Paragraph style | `PARRAFOS` with a direct indent override |
| Indent | **Hanging indent, left 1.27 cm / hanging 1.27 cm** — APA 7's rule |
| Ordering | Alphabetical by author |

IEEE appears **only** inside the front-matter "how to cite" table, which is a
faculty form for citing *this* thesis, not the bibliography style — and that
table is out of scope (see below). The bibliography is APA 7, unambiguously.

**A defect to fix by construction:** each entry's URL sits in a *separate*
paragraph without the hanging indent, so a reference renders as two visually
disconnected blocks. A citation processor emits one paragraph per entry, which
removes this automatically.

## Front matter — measured from the approved document

| # | Slot | Notes |
|---|---|---|
| 1 | `cover` | Institution, faculty, logo image, "TESIS", title, degree statement, "Elaborado por" + author, "Asesor" + advisor, "LIMA – PERÚ", year |
| 2 | `dedication` | Style `Dedicatoria`, italic, right-aligned |
| 3 | `acknowledgements` | Present in the approved document |
| 4 | `abstract_es` | "Resumen" + body + "Palabras clave — …" |
| 5 | `abstract_en` | "Abstract" + body + "Keywords — …" |
| 6 | `toc` | "Tabla de Contenido" + "Pág." + TOC field |
| 7 | `list_of_tables` | Índice de tablas |
| 8 | `list_of_figures` | Índice de figuras |
| 9 | `list_of_annexes` | Índice de anexos |
| 10 | `introduction` | "Introducción", style `TITU1` |

### Deliberately out of scope

Two front-matter elements are present in the approved thesis and **excluded from
v1 on purpose**:

- **ORCID identifiers** with logo images, next to the author and the advisor on
  the cover.
- **Two "Citar / How to cite" tables**, giving the citation for the thesis
  itself in IEEE and in APA 7 format.

Both are highly institution-specific, both are one-time boilerplate that never
changes across a document's revisions, and both are trivially added by hand in
under a minute. They are assigned to the manual 5%. Building them would mean
carrying an ORCID logo asset, a second citation style purely for a front-matter
table, and a bespoke two-table layout — for no saving of repeated work.

Recorded so that their absence reads as a decision rather than an oversight.

---

## Document schemas

**`thesis-final` (approved document A):**

```
chapters:
  I    Parte introductoria del trabajo
  II   Marcos teórico y conceptual
  III  Desarrollo del trabajo de investigación
  IV   Análisis e interpretación de resultados
top_level_sections (unnumbered, after the chapters):
  Conclusiones · Recomendaciones · Referencias bibliográficas · Anexos
```

**`thesis-proposal` (document B):**

```
chapters:
  I    Planteamiento del Problema
  II   Objetivos
  III  Marco Teórico
  IV   Diseño Metodológico
  V    Administración del Plan de Tesis
top_level_sections:
  Referencias bibliográficas · Anexos
```

The approved document's chapter II is **missing its "Capítulo II." prefix** —
see the audit's defect list. We generate the prefix for every chapter, which
fixes that class of error by construction.

---

## Element budget — measured

| Element | Approved (134 pp) | Proposal (73 pp) |
|---|---|---|
| Words | 28,893 | 19,427 |
| **Words per page** | **216** | **266** |
| Paragraphs | 2,074 | 1,157 |
| Equations | 141 | 163 |
| Tables | 37 | 8 |
| Images | 107 (93 media files, 11 MB) | 4 |
| List items | 74 | 119 |
| Sections | 5 | 3 |
| Footnotes / endnotes / code blocks | 0 | 0 |

Use **216–266 words per page** for sizing, at the lower end for figure-heavy
documents.

---

## Conformance rules

| Rule | Limit | Severity |
|---|---|---|
| Table width | ≤ 15.50 cm portrait, ≤ 24.70 cm landscape | warning |
| Figure width | ≤ 15.50 cm portrait | warning |
| Required chapters present and ordered | per schema | error |
| Every chapter carries its `Capítulo {roman}.` prefix | — | error |
| Heading depth | ≤ 3 | warning |
| Direct formatting on generated paragraphs | 0 | error |
| Fonts used | Arial and Cambria Math only | warning |
| Every figure and table has a `title` | — | warning |
| Figure or table with an external source has a `note` | — | warning |
| `SEQ` sequences gap-free and starting at 1 | tables, figures, equations | error |
| All four index fields present | — | warning |
| Raw escape-hatch blocks | reported | info |

The "fonts used" rule exists because the approved document contains 192
`Arial Narrow` runs and 38 `Times New Roman` runs despite the template
specifying Arial.

---

## Decisions taken

All six questions this profile previously carried have been answered.

| # | Question | Decision |
|---|---|---|
| 1 | Body font size — 11pt or 12pt? | **11pt.** Measured, and identical in both documents. Correcting it later is a one-value change — see below |
| 2 | Is 134 pages typical for an undergraduate thesis? | **Yes, representative.** Plan for ~134 pages / ~29,000 words, not 60–70 |
| 3 | Reproduce the flat general index, or indent by depth? | **Reproduce the approved output** — flat, all entries at `TDC1` |
| 4 | Are ORCID iDs and the two how-to-cite tables required? | **Out of scope.** Institution-specific boilerplate, added by hand |
| 5 | The missing `Capítulo II.` prefix — fix or replicate? | **Fix.** Every chapter gets its prefix; a conformance rule asserts it |
| 6 | Does the faculty publish its template? | **No.** The approved thesis is therefore the specification, and extraction from it is how this profile is built |

### On the 11pt decision, precisely

`Normal` sets Arial and double spacing but declares **no size**, so it inherits
Word's document default of 11pt. Both audited documents do this identically.
That is not independent evidence of the faculty's *intent* — two documents from
one template inherit one default — but with no rulebook and no template
available, the approved document is the best authority we have, and it renders
at 11pt.

**The cost of being wrong is small and bounded**, which is why this is not worth
blocking on:

| What changes | Effort |
|---|---|
| `styles.roles.body.size` in `uni-figmm/base` | One value |
| The golden fixture's expected page count | Re-baseline once; 12pt will add roughly 10–15 pages to a 134-page document |
| The `body_size` conformance assertion | One value |

Nothing structural depends on it. No code changes. Recorded in
[D16](../11-decision-log.md#d16--body-text-is-11pt).

### Residual unknowns

Two things remain genuinely unknown, and neither blocks anything:

- **Whether a different approved thesis from this faculty would disagree** on
  any *stable* property. The cheapest insurance is to audit a second approved
  thesis when one becomes available; the extraction tooling makes that nearly
  free once it exists.
- **Whether the faculty would object to the corrections we make** — the chapter
  prefix, gap-free numbering, zero direct formatting. Each is a move toward the
  template's own intent, so the risk is low, and every one is recorded in the
  decision log with its reasoning.

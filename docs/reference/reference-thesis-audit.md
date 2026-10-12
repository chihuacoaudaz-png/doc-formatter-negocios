# Reference Thesis Audit

Every design decision in this folder is grounded in measurements of real thesis
documents, not in assumptions about what theses look like. This document records
those measurements.

## Sources

Three documents have been audited. All three are excluded from version control —
they contain personal data and Word documents version badly (see `.gitignore`).
Author and advisor names, ORCID identifiers and mine site details are
deliberately omitted here.

| # | Document | Institution | Pages | Status |
|---|---|---|---|---|
| **A** | **Final thesis, complete and formatted** | UNI FIGMM | **134** | **Approved** |
| B | Thesis proposal ("plan de tesis"), master's | UNI FIGMM | 73 | Draft |
| C | Final thesis | A different private university | 66 | Submitted |

**Document A is the specification.** The faculty does not publish its template,
and no written rulebook is available to us, so the profile is derived
**~100% from document A** — a complete, formatted thesis the faculty
*accepted*. Where A and B disagree, A wins without discussion.

**Document B's only role is a stability check.** A and B come from the same
university template but were written by different authors. Where they agree on a
property, that property belongs to the **template** rather than to one author's
direct formatting — which is exactly the confidence we need when extracting a
profile from a single document. B is a thesis proposal and contributes nothing
normative to the style layer.

**Document C is contrast only** — it shows how much worse a document gets with
no template at all.

**Method.** Each DOCX was unzipped and its OOXML parsed directly —
`document.xml`, `styles.xml`, `numbering.xml`, `settings.xml`, `footer*.xml`.
Counts are exact, not estimates.

---

## 1. Scale

| Measure | A (approved, 134 pp) | B (proposal, 73 pp) |
|---|---|---|
| Pages | 134 | 73 |
| Words | 28,893 | 19,427 |
| Paragraphs | 2,074 | 1,157 |
| **Words per page** | **216** | **266** |
| `document.xml` | 1,599,208 chars | 722,898 chars |
| Media files | **93 (11 MB)** | 2 |

The difference in words per page is explained by images: A carries 93 media
files, so pages hold less text. **Use 216–266 words per page for sizing, and
expect the figure-heavy end of that range for a final thesis.**

> **Confirmed scale.** Document A is an *undergraduate* thesis ("título
> profesional de Ingeniero de Minas") at **134 pages**, and this is
> **representative** for the faculty — not an unusually long thesis. Plan for
> ~134 pages / ~29,000 words for undergraduate work, not the 60–70 pages
> originally assumed. This affects the content agent, not the formatter.

---

## 2. Element census

| Element | A (approved) | B (proposal) | Design consequence |
|---|---|---|---|
| **Equations (OMML)** | **141** (26 display) | **163** (43 display) | Dominant capability in both |
| **Equation numbers** | **YES — `(1)`…`(47)`** | **none** | **In scope.** See §6 |
| Tables | **37** (200 rows) | 8 | Real volume; width checking matters |
| Images | **107** | 4 | Asset handling is a real subsystem |
| Paragraphs | 2,074 | 1,157 | |
| List items (`numPr`) | 74 | 119 | |
| Sections (`sectPr`) | **5** | 3 | |
| Explicit page breaks | 32 | 6 | All manual; see §6b |
| **Live fields** | **162** | 3 | A is properly built; see §5 |
| Bookmarks | 207 | 38 | |
| Hyperlinks | 190 | 2 | |
| **Footnotes / endnotes** | **0 / 0** | **0 / 0** | Confirmed cut from v1 |
| **Code blocks** | **0** | **0** | Confirmed cut from v1 |
| Comments | 0 | 0 | |

Footnotes, endnotes and code blocks are zero in all three audited documents.
That cut is now well evidenced.

---

## 3. Page setup — stable across both documents

| Property | Value | Stability |
|---|---|---|
| Page size | A4, 21.00 × 29.70 cm | Identical in A and B |
| Margin left | **3.00 cm** | Identical in every portrait section of both |
| Margin top / bottom / right | **2.50 cm** | Identical, with the same drift (below) |
| Annex section | **Landscape**, 29.70 × 21.00, margins 3.00 / 2.50 / 2.50 / 2.50 | Identical in A and B |

**Derived text width, portrait: 15.50 cm.** (21.00 − 3.00 − 2.50)
**Derived text width, landscape: 24.70 cm.**

**The same drift appears in both documents:** one section in each has margins of
2.54 cm instead of 2.50. 2.54 cm is exactly one inch — Word's default — so that
section's margins were never deliberately set. Two independent authors producing
the identical artefact confirms it is drift, not intent. **We normalise to
2.50 cm.**

### Page numbering — three regions

Document A, being complete, shows the full scheme:

| Section | Content | Orientation | Page numbering |
|---|---|---|---|
| 0 | Cover | Portrait | None; no footer |
| 1 | Front matter | Portrait | `lowerRoman` (runs v … xv) |
| 2 | Body, chapters I–IV + closing sections | Portrait | Arabic, restart at 1 (runs 1 … 106) |
| 3 | Annexes 1–6 | Portrait | Arabic, **restart at 1** |
| 4 | Annexes 7–9 | **Landscape** | Arabic, start at 7 |

The annexes carry **their own page sequence restarting at 1** — the table of
contents lists "Anexo 1 … 1", "Anexo 2 … 2". This is a third numbering region,
and B shows the same pattern.

Footers: `PAGE \* MERGEFORMAT`, right-aligned, Arial 10pt, paragraph style
`Piedepgina` ("Pie de página"). Identical in A and B.

---

## 4. Style system — the template, now fully revealed

A and B share one template. B uses part of it; **A uses all of it**, which is
why A is the normative source for the style layer.

```
Normal              Arial, justified, line spacing 2.0 (double), space-after 0
│                   size inherited from document defaults: 11pt
├── PARRAFOS        + first-line indent 1.27 cm      ← default body paragraph
│   └── NORMALES    + first-line indent 0            ← unindented paragraph
│       ├── TITU1   Arial Bold 14pt, bold, centered, space-after 18pt
│       ├── XANEXOS (inherits)                       ← annex heading + index source
│       └── Dedicatoria  + italic, right-aligned     ← dedication page      [A only]
├── TITU2           Arial Bold, bold, no indent      ← level-2 heading
│   └── TITU3       + italic                         ← level-3 heading
├── XTABLAS         Arial Bold, bold                 ← table label + index source [A only]
├── XFIGURAS        Arial Bold, bold                 ← figure label + index source [A only]
├── X1              italic, single-spaced            ← caption title        [A only]
├── X2              9pt, centered, single-spaced     ← image container / table header cell
├── X3              9pt                              ← caption note / table body cell
├── TDC1            (inherits Normal)                ← index entry, level 1
└── Piedepgina      Arial 10pt, right-aligned        ← footer
```

Usage in A: `PARRAFOS` 584 · `X2` 489 · unstyled 410 · `TDC1` 158 · `X1` 107 ·
`X3` 102 · `XFIGURAS` 85 · `NORMALES` 39 · `XTABLAS` 23 · `TITU3` 22 ·
`Dedicatoria` 15 · `TITU1` 12 · `TITU2` 12 · `XANEXOS` 12 · `TtuloTDC` 4.

**Four styles are new in A and they are the ones we were missing:** `XTABLAS`,
`XFIGURAS`, `X1` and `Dedicatoria`. Without document A the caption model would
have been bound to the wrong styles.

### Stable versus drift

| Property | A | B | Verdict |
|---|---|---|---|
| `Normal`: Arial, justified, line 480, after 0 | ✓ | ✓ | **Stable** |
| Document default size: 11pt | ✓ | ✓ | **Stable** (still not declared explicitly — see Q1) |
| `PARRAFOS` first-line indent 1.27 cm | ✓ | ✓ | **Stable** |
| `TITU1` Arial Bold 14pt centered, after 18pt | ✓ | ✓ | **Stable** |
| `TITU2` bold, `TITU3` bold italic | ✓ | ✓ | **Stable** |
| `X2` 9pt centered, `X3` 9pt | ✓ | ✓ | **Stable** |
| Left margin 3.00 cm, landscape annexes, roman front matter | ✓ | ✓ | **Stable** |
| Caption label style | `XTABLAS` / `XFIGURAS` | `NORMALES` | **A wins** — B simply did not use the right styles |
| Caption title style | `X1` (italic) | `NORMALES` | **A wins** |
| Equation numbering | `(1)`…`(47)` | none | **A wins** — in scope |
| Index fields | 4 live TOC fields | 1 | **A wins** |
| Direct formatting | 21–26% of paragraphs | 41% | A is cleaner |

Everything in the "Stable" rows is safe to freeze in the profile. Everything in
the "A wins" rows would have been got wrong from B alone.

---

## 5. How the indexes actually work — the key mechanism

Document A contains **four live `TOC` fields**, every one of them driven by a
paragraph style rather than by outline levels:

```
TOC \h \z \t "TITU1;1;TITU2;1;TITU3;1"     → Tabla de Contenido (general index)
TOC \h \z \t "XTABLAS;1"                   → Índice de tablas
TOC \h \z \t "XFIGURAS;1"                  → Índice de figuras
TOC \h \z \t "XANEXOS;1"                   → Índice de anexos
```

Their combined cached result is 158 `TDC1` entries: ~48 outline entries, 23
table entries, 82 figure entries, 9 annex entries. Each entry carries a
`PAGEREF` field, which is why the document holds 162 fields and 207 bookmarks.

Three consequences, and they are the most useful findings in this audit:

**a) The caption label style does double duty.** `XTABLAS` formats the text
"Tabla 5" *and* is the source for the Índice de tablas. Same for `XFIGURAS` and
`XANEXOS`. This is why those styles exist as separate bold styles rather than
being folded into `NORMALES`. Emitting a label with the right style
automatically produces the index entry.

**b) `outlineLvl` is not the mechanism, and we should not rely on it.** Our
earlier plan was to add `outlineLvl` to `TITU1/2/3` so a standard TOC field
could see them. That is unnecessary: the approved document uses the `\t`
style switch, which works without outline levels. It is also insufficient —
`outlineLvl` could never produce the table, figure and annex indexes, because
those are not outline entries at all. **We follow the approved document's
mechanism.**

**c) The general index is flat.** All three heading styles map to TOC level 1
(`TITU1;1;TITU2;1;TITU3;1`), so every entry renders with `TDC1` formatting and
no indentation by depth. `TDC2` and `TDC3` are defined in the template but
unused. Indenting by depth would look better; it would also differ visibly from
the document the faculty accepted, and there is no rulebook to appeal to.
**Decided: reproduce the approved output.**

---

## 6. Equations are numbered

This corrects a conclusion drawn from document B alone.

| | A (approved) | B (proposal) |
|---|---|---|
| Total equations | 141 | 163 |
| Display | 26 | 43 |
| **Numbered** | **Yes — 50 tags, `(1)` … `(47)`** | No |

Format in A: a **centered** paragraph in style `PARRAFOS`, containing the
equation followed by the tag as plain parenthesised text, with **no tab and no
right alignment**:

```
                    [ centered equation ]  (12)
```

Numbering is **global and sequential** across the whole document — `(1)` through
`(47)` — not per chapter.

This is a simpler layout than the classic right-margin-aligned tag, and it is
good news: it needs no invisible-table trick. A `SEQ` field inside a centered
paragraph is enough.

**The manual numbering is, predictably, wrong.** The tag sequence runs 1…44,
then `6`, then 45, 46, 47, then `45`, `46` again — 50 tags for 47 distinct
numbers, with duplicates and one out-of-order value.

---

## 6b. Page breaks are all manual, and they serve two different purposes

Measured in the approved thesis:

| Mechanism | Count |
|---|---|
| `pageBreakBefore` on the `TITU1` / `TITU2` / `TITU3` styles | **0** |
| `pageBreakBefore` applied directly to a paragraph | **0** |
| Explicit `<w:br w:type="page"/>` runs | **32** |

So every page break in a 134-page document was inserted by hand. What follows
each break separates into two distinct intents:

**a) Structural — a new page before a top-level division.** Resumen, Abstract,
Tabla de Contenido, Lista de Tablas, Lista de Figuras, Introducción, and each
chapter. Consistently applied, and clearly the intended rule.

**b) Ad-hoc — stopping an object from splitting across pages.** Breaks inserted
immediately before `Figura 9`, `Figura 12`, `Figura 18`, `Tabla 3` and a
level-3 heading. These are not a rule; they are manual nudges to fix a local
layout problem, and they are brittle: any content edit above them leaves a
half-empty page behind.

**Both intents are real, and both have a correct declarative mechanism that the
author did not use:**

| Intent | Author's mechanism | Correct mechanism |
|---|---|---|
| New page before a top-level division | 7+ manual page breaks | `w:pageBreakBefore` on the heading style |
| Keep a caption with its figure or table | ~25 manual page breaks | `w:keepNext` on label and title, `w:keepLines` on the block |

Both are **paragraph-style properties** — they change how a paragraph behaves,
not where it sits in the document. Adopting them replaces 32 hand-placed breaks
with two declarative style properties, and removes the brittleness entirely.

This is the [D23](../11-decision-log.md#d23--we-reproduce-the-flat-general-index)
consistency test applied again: the *intent* is consistent and clear, so we
reproduce it; the *mechanism* is a workaround, so we replace it.

## 7. Caption pattern — exact, from the approved document

**Figures** — four blocks, label and title above, note below:

```
Figura 1                                         XFIGURAS  (Arial bold)
Imagen representativa de la sobrerotura.         X1        (italic, single-spaced)
[IMAGE]                                          X2        (9pt, centered)
Nota: El gráfico resalta la zona roja como…      X3        (9pt)
```

**Tables** — the same shape, with the table in place of the image:

```
Tabla 1                                          XTABLAS   (Arial bold)
Valores de factor de fijación y relación (S/B).  X1        (italic, single-spaced)
[TABLE]
Nota: fuente Manual de perforación y voladura…   X3        (9pt)
```

This confirms the four-slot caption model — `label`, `title`, `content`,
`note` — with concrete style bindings. A single `caption` string cannot express
it.

Two details: the note prefix is **`Nota:`** with a colon in the approved
document (document C, from another university, used `Nota.` with a period), and
the label carries **no separator** before the title — they are separate
paragraphs.

---

## 8. Document structure — a complete approved thesis

```
COVER                institution · faculty · logo · "TESIS" · title ·
                     degree statement · "Elaborado por" + author ·
                     "Asesor" + advisor · "LIMA – PERÚ" · year
                     [+ ORCID iDs with logo images — OUT OF SCOPE]
HOW-TO-CITE          two 2×2 tables giving the citation for the thesis itself,
                     one in IEEE style, one in APA 7      [OUT OF SCOPE]
Dedicatoria          style Dedicatoria (italic, right-aligned)
Agradecimientos      heading in NORMALES  ← inconsistent; see §9
Resumen              TITU1, then body, then "Palabras clave — …" in NORMALES
Abstract             TITU1, then body, then "Keywords — …" in NORMALES
Tabla de Contenido   "Tabla de Contenido" + "Pág." in NORMALES, then the TOC field
Índice de tablas     TOC field
Índice de figuras    TOC field
Índice de anexos     TOC field
Introducción         TITU1
Capítulo I.   Parte introductoria del trabajo
Marcos teórico y conceptual          ← missing "Capítulo II." prefix; see §9
Capítulo III. Desarrollo del trabajo de investigación
Capítulo IV.  Análisis e interpretación de resultados
Conclusiones         TITU1
Recomendaciones      TITU1
Referencias bibliográficas   TITU1
Anexos               TITU1
  Anexo 1 … Anexo 9  XANEXOS        ← own page sequence, last three landscape
```

**Two structural facts that change the schema model:**

**a) `TITU1` serves two different roles.** It formats numbered chapters
("Capítulo I. …") *and* unnumbered top-level sections (Resumen, Abstract,
Introducción, Conclusiones, Recomendaciones, Referencias, Anexos). The profile
must therefore distinguish a `chapter` — which receives the
`Capítulo {roman}.` prefix — from a `top_level_section`, which does not, while
both bind to `TITU1`.

**b) Two front-matter elements deliberately excluded from v1:** ORCID
identifiers with logo images on the cover, and the pair of "how to cite" tables.
Both are institution-specific boilerplate that never changes across a document's
revisions and takes under a minute to add by hand. They are assigned to the
manual 5% rather than built — see
[D22](../11-decision-log.md#d22--orcid-ids-and-the-how-to-cite-tables-are-out-of-scope).

---

## 9. Defects in the approved document

These matter for a specific reason: **this document was approved with these
defects in it.** That tells us where the acceptance bar actually sits, and it
tells us exactly which problems automation removes.

**Numbering, all manual:**
- Heading numbers are literal text runs. The separator is inconsistent — some
  headings use a tab (`'1.2.1'`, `<TAB>`, `'Problema general'`), others have
  none at all (`'1.1'`, `'Generalidades'`), which renders as "1.1Generalidades".
- Equation tags: 50 tags for 47 numbers, with duplicates and one out of order.
- Table and figure labels are typed text.

**Structure:**
- **"Marcos teórico y conceptual" is missing its `Capítulo II.` prefix** while
  chapters I, III and IV all have theirs. It appears wrong in the table of
  contents too.
- "Agradecimientos" uses `NORMALES` where the parallel sections Resumen and
  Abstract use `TITU1`.
- "Tabla de Contenido" also uses `NORMALES` rather than a heading style.
- Two annex sub-items under Anexo 6 carry the `XANEXOS` style without an
  "Anexo N:" prefix, so they appear in the annex index as if they were annexes.
- A stray paragraph containing `88` carries the `TITU1` chapter-title style — a
  page number typed into the body. **Document B contains the identical defect**,
  which suggests a shared source file or a shared habit.
- Four stray paragraphs containing `7` and `8` carry the `TtuloTDC` style.

**Consistency:**
- 21–26% of paragraphs carry direct formatting overrides.
- Fonts appearing in runs include `Arial Narrow` (192 runs) and
  `Times New Roman` (38 runs) despite the template specifying Arial throughout.
- One heading ends in a period ("1.4 Justificación.") where the others do not.

For contrast, document C — from a different university, without a template —
had **89%** of paragraphs directly formatted, Arial mixed with Calibri across
the body, line spacing spread across nine distinct values between 0.83 and 1.52,
a table of contents converted to static text, and two different figures both
labelled "Figura 2".

**This is the acceptance bar, and it is well below what automation produces.** A
generated document with automatic numbering, consistent chapter prefixes, four
live indexes and zero direct formatting is not "almost as good as a human" — it
is unambiguously better than an approved thesis. That materially de-risks the
project.

**We correct these defects rather than reproduce them.** The approved document
is the specification for *format*, not for *errors*: every defect above is a
departure from the template's own evident intent, and each correction is
recorded in the decision log. The exception is the flat general index (§5c),
which is a deliberate layout choice rather than a mistake, so we reproduce it.

---

## 10. What this audit changes

| Finding | Consequence |
|---|---|
| Equations **are** numbered — global `(1)`…`(47)`, centered, no tab | Equation numbering is **in scope**. Earlier cut reversed |
| Four live style-driven `TOC` fields | This is the index mechanism. `outlineLvl` is neither necessary nor sufficient — earlier plan reversed |
| Caption label styles double as index sources | Emitting the right label style produces the index entry for free |
| `XTABLAS`, `XFIGURAS`, `X1`, `Dedicatoria` styles | The caption model now has concrete bindings; would have been wrong from B alone |
| `TITU1` used for both chapters and unnumbered sections | Schema must distinguish `chapter` from `top_level_section` |
| ORCID iDs and "how to cite" tables on the front matter | Measured, then **deliberately excluded** — institution-specific boilerplate, added by hand |
| Three page-numbering regions, annexes restarting at 1 | Pagination rules need a third region |
| 37 tables, 107 images, 93 media files, 11 MB | Asset resolution and width checking are real subsystems, not edge cases |
| 32 manual page breaks; **zero** `pageBreakBefore`, **zero** `keepNext` | Both belong in the **style** layer, not as layout rules. Replaces 32 hand-placed breaks with two style properties |
| 2.54 cm margin drift appears in **both** documents | Confirmed as Word's default leaking in; normalise to 2.50 cm |
| 11pt in both documents, inherited rather than declared | **Decided: 11pt.** No rulebook exists to appeal to; correcting it later is a one-value change |
| An *undergraduate* thesis is **134 pages**, and this is representative | Plan for ~29,000 words of undergraduate content, not ~16,000 |
| The faculty publishes neither a template nor a rulebook | **The approved thesis is the specification.** Extraction from it is how the profile gets built |
| Approved document carries visible numbering and structure defects | The acceptance bar is low; automation clears it comfortably |

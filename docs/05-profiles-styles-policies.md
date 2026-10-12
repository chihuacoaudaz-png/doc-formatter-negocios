# 05 — Profiles, Styles and Policies

A **profile** is a named, versioned rulebook: one institution's requirements for
one kind of document. It is the only thing that should need to change when we
onboard a new university.

```
uni-figmm/thesis-proposal@2026
└── schema        which sections are required, and in what order
└── styles        how each semantic role looks
└── layout        deterministic transforms that change document structure
└── conformance   constraints that are checked and reported
└── renderer      which backend and with what options
```

## The three kinds of rule

Most designs collapse styles and policies into one bag of rules. That fails at a
specific, reproducible point, so the boundary needs to be drawn precisely and
enforced by the resolver rather than left to whoever writes the configuration.

Consider *"each chapter starts on a new page."* In Word this is
`w:pageBreakBefore`, a property of a **paragraph style**. But it is also
naturally described as a policy. If both the style layer and the policy layer can
express it, sooner or later both do, and the document gets two page breaks — a
bug that is nearly impossible to trace back, because each layer looks correct in
isolation.

So:

| Kind | Definition | Applied | Examples |
|---|---|---|---|
| **Style** | Anything expressible as a property of a named style or of the page setup. Declarative. Does not change document structure. | Compiled into the backend's style carrier (a reference DOCX, a CSS file, a LaTeX preamble) | Font, size, line spacing, alignment, indent, margins, page size, colour, `pageBreakBefore`, `keepNext`, `keepLines` |
| **Layout** | Anything requiring insertion, movement, reordering, renumbering or referencing of nodes. Deterministic transform. | During lowering, pass 8 | Caption placement, section breaks, page-number format changes, landscape regions, front-matter slot expansion, chapter title prefixes |
| **Conformance** | A predicate over the document or the produced file. Produces a finding; changes nothing. | Passes 4 and 13 | Maximum table width, required sections present, minimum page count, no orphaned headings |

The test to apply when classifying a rule: **does obeying it change the node
tree?** If no, it is a style. If yes, it is layout. If it only needs to be
*checked*, it is conformance.

Under this test, `pageBreakBefore` is unambiguously a **style** — it is a
property, and the paragraph stays where it is. Caption placement is **layout** —
blocks move. Roman-then-arabic page numbering is **both**: a layout rule inserts
the section boundary, and a style declares the numbering format of each section.

> **This document previously got its own test wrong.** An earlier version of the
> profile below classified `pageBreakBefore` as a style in this table and then
> implemented "each chapter starts on a new page" as a `layout` rule named
> `chapter-new-page` — the exact double-application bug described two paragraphs
> above, committed in the same file that warns about it.
>
> That is the strongest available argument for the rule stated next: **the
> resolver applies the classification test, not the person writing the
> configuration.** A human reviewer had both halves in front of them and did not
> notice. Recorded in
> [D9](11-decision-log.md#d9--style-layout-and-conformance-are-three-different-things).

## Layout rules need an execution model

A list of rules is not enough. The profile must also state:

- **Order.** Rules apply in declaration order within a phase. Phases are fixed:
  `structure` → `numbering` → `placement` → `pagination`.
- **Precedence.** A profile's own rules override those from its `extends` chain.
  A rule may be disabled by redeclaring it with `enabled: false`.
- **Idempotency.** Every rule must be safe to apply twice. This is testable and
  should be tested — it is what makes the pipeline debuggable.
- **Conflict is an error, not a coin flip.** Two rules targeting the same node
  with incompatible effects fail the build with both rule ids named. Silent
  last-write-wins is how formatting engines become unpredictable.

## Citation style is delegated, not modelled

APA 7 is not a list of our rules. It is a CSL (Citation Style Language) style
plus a citation processor. The profile declares it:

```yaml
citations:
  style: apa-7        # from the public CSL repository
  locale: es-PE
```

Writing our own citation rules would mean reimplementing CSL, which is a
multi-year project with a free, correct, actively maintained alternative. The
same applies to the bibliography format: standard `.bib` or CSL-JSON.

What *is* ours: the parts of APA 7 that are document layout rather than
citation rendering — the caption structure, double spacing, heading level
formatting. Those are styles and layout rules, expressed in the base profile
`base/apa7` and inherited.

## A real profile

Derived entirely from measurement — see the
[audit](reference/reference-thesis-audit.md) and the fully annotated version in
[UNI-FIGMM Profile](reference/uni-figmm-profile.md).

The two audited documents are different **document kinds** from the same faculty
sharing an **identical style layer**, so the profile splits accordingly:

```
uni-figmm/base                     page setup · styles · captions · numbering · pagination
├── uni-figmm/thesis-final@2024        schema only
└── uni-figmm/thesis-proposal@2026     schema only
```

### `uni-figmm/base`

```yaml
id: uni-figmm/base
extends: base/apa7
renderer: docx-pandoc

# ── STYLES ────────────────────────────────────────────────────────────────
styles:
  page:
    size: A4                     # 21.00 x 29.70 cm
    margins: { top: 2.5cm, bottom: 2.5cm, left: 3.0cm, right: 2.5cm }
    # derived text width: 15.50 cm
  landscape_page:
    size: A4
    orientation: landscape
    margins: { top: 3.0cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm }
    # derived text width: 24.70 cm

  roles:
    body:                  { font: Arial, size: 11pt, line_spacing: 2.0,
                             align: justify, space_after: 0,
                             first_line_indent: 1.27cm, docx_style: PARRAFOS }
    body_standalone:       { inherits: body, first_line_indent: 0, docx_style: NORMALES }

    chapter_title:         { font: Arial, size: 14pt, bold: true, align: center,
                             space_after: 18pt, page_break_before: true,
                             keep_with_next: true, docx_style: TITU1 }
    top_level_section_title: { inherits: chapter_title, docx_style: TITU1 }
    heading_2:             { inherits: body_standalone, font: Arial, bold: true,
                             keep_with_next: true, docx_style: TITU2 }
    heading_3:             { inherits: heading_2, italic: true, docx_style: TITU3 }

    table_label:           { font: Arial, bold: true, keep_with_next: true,
                             docx_style: XTABLAS }
    figure_label:          { font: Arial, bold: true, keep_with_next: true,
                             docx_style: XFIGURAS }
    caption_title:         { italic: true, line_spacing: 1.0, keep_with_next: true,
                             docx_style: X1 }
    caption_note:          { size: 9pt, line_spacing: 1.0, docx_style: X3 }
    image_container:       { size: 9pt, align: center, line_spacing: 1.0, docx_style: X2 }
    table_header_cell:     { size: 9pt, align: center, line_spacing: 1.0, docx_style: X2 }
    table_body_cell:       { size: 9pt, line_spacing: 1.0, docx_style: X3 }

    equation:              { inherits: body, align: center, docx_style: PARRAFOS }
    annex_heading:         { inherits: body_standalone, docx_style: XANEXOS }
    dedication:            { inherits: body_standalone, italic: true,
                             align: right, docx_style: Dedicatoria }
    bibliography_entry:    { inherits: body, first_line_indent: 0,
                             hanging_indent: 1.27cm, docx_style: PARRAFOS }
    index_entry:           { docx_style: TDC1 }
    page_number:           { font: Arial, size: 10pt, align: right,
                             docx_style: Piedepgina }

# ── LAYOUT ────────────────────────────────────────────────────────────────
layout:
  - id: chapter-title-prefix
    phase: structure
    rule: prefix_heading
    target: section[kind=chapter]
    template: "Capítulo {roman}. {title}"
    # top_level_section deliberately excluded - it gets no prefix (D20)

  - id: heading-numbering
    phase: numbering
    rule: number_headings
    levels: [2, 3]
    format: "{n1}.{n2}.{n3}"
    separator: tab

  - id: label-numbering
    phase: numbering
    rule: number_labels
    sequences:
      table:    { prefix: "Tabla ",  scope: global, field: "SEQ Tabla" }
      figure:   { prefix: "Figura ", scope: global, field: "SEQ Figura" }
      equation: { format: "({n})",   scope: global, field: "SEQ Ecuacion" }
      annex:    { prefix: "Anexo ",  scope: global, separator: ": " }

  - id: caption-blocks              # APA 7 - label and title above, note below,
    phase: placement                # for BOTH tables and figures
    rule: caption_position
    target: [table, figure]
    label: above
    title: above
    note: below
    note_prefix: "Nota: "

  # NOTE: "each chapter starts on a new page" is NOT a layout rule. It is
  # page_break_before on the chapter_title style role above - a property, no
  # node-tree change. Likewise "keep a caption with its object" is
  # keep_with_next, not 32 hand-placed page breaks. See the classification
  # test at the top of this document.

  - id: page-numbering              # three regions, measured
    phase: pagination
    rule: page_numbering
    regions:
      - { region: cover,       format: none }
      - { region: frontmatter, format: lower_roman }
      - { region: body,        format: arabic, restart: 1 }
      - { region: annexes,     format: arabic, restart: 1 }

  - id: wide-content-landscape      # Container{kind: wide} -> a landscape section
    phase: pagination                # The IR says "needs more width"; the
    rule: section_orientation        # profile decides that means landscape here
    target: [annex[wide], container[kind=wide]]
    page: landscape_page

  - id: indexes                     # four style-driven TOC fields (D13)
    phase: structure
    rule: build_index
    fields:
      toc:             'TOC \h \z \t "TITU1;1;TITU2;1;TITU3;1"'
      list_of_tables:  'TOC \h \z \t "XTABLAS;1"'
      list_of_figures: 'TOC \h \z \t "XFIGURAS;1"'
      list_of_annexes: 'TOC \h \z \t "XANEXOS;1"'

# ── CONFORMANCE ───────────────────────────────────────────────────────────
conformance:
  - { id: table-fits,     rule: max_width, target: table,  limit: text_width, severity: warning }
  - { id: figure-fits,    rule: max_width, target: figure, limit: text_width, severity: warning }
  - { id: chapter-prefix, rule: all_have_prefix, target: section[kind=chapter], severity: error }
  - { id: seq-gapless,    rule: sequences_gapless, targets: [table, figure, equation], severity: error }
  - { id: no-direct-fmt,  rule: max_direct_formatting, limit: 0, severity: error }
  - { id: fonts-allowed,  rule: fonts_in, allow: [Arial, Cambria Math], severity: warning }
  - { id: has-title,      rule: require_field, target: [table, figure], field: title, severity: warning }
  - { id: indexes-present,rule: require_slots,
        slots: [toc, list_of_tables, list_of_figures, list_of_annexes], severity: warning }
  - { id: no-raw-blocks,  rule: no_node, node: Raw, severity: info }

# ── CITATIONS ─────────────────────────────────────────────────────────────
citations:
  style: apa-7                      # confirmed from the approved thesis
  locale: es-PE
  bibliography_indent: { hanging: 1.27cm }
```

### `uni-figmm/thesis-final@2024` — schema only

```yaml
id: uni-figmm/thesis-final@2024
extends: uni-figmm/base

schema:
  frontmatter:
    required: [cover, abstract_es, abstract_en, toc, introduction]
    optional: [dedication, acknowledgements, list_of_tables,
               list_of_figures, list_of_annexes]
  body:
    ordered: true
    required_chapters:
      - { id: introductoria, title: "Parte introductoria del trabajo" }
      - { id: marcos,        title: "Marcos teórico y conceptual" }
      - { id: desarrollo,    title: "Desarrollo del trabajo de investigación" }
      - { id: analisis,      title: "Análisis e interpretación de resultados" }
  backmatter:
    required: [conclusiones, recomendaciones, references]
    optional: [annexes]
  max_heading_depth: 3
```

The proposal profile is the same file with a different `required_chapters` list
(Planteamiento del Problema, Objetivos, Marco Teórico, Diseño Metodológico,
Administración del Plan de Tesis) and no `conclusiones`/`recomendaciones`.

### Four notes on this profile

**The `chapter-title-prefix` rule earns its place immediately.** The approved
thesis is **missing the `Capítulo II.` prefix** on "Marcos teórico y conceptual"
while chapters I, III and IV have theirs — and it is wrong in the table of
contents too. Generating the prefix eliminates that error class by construction,
and `chapter-prefix` asserts it.

**The index rule looks odd and is correct.** Four raw field instructions in a
profile is not elegant, but it is what the approved document does, and it is
load-bearing: the caption **label style is the index source**, so emitting
"Tabla 5" with style `XTABLAS` produces its index entry for free. See
[D13](11-decision-log.md#d13--indexes-are-style-driven-toc-fields-not-outline-levels).

**Page breaks moved from layout into style, and that removed 32 manual breaks.**
The approved thesis sets `pageBreakBefore` on **no** style and on **no**
paragraph; all 32 of its page breaks are hand-placed `<w:br>` runs serving two
different intents — a new page before top-level divisions, and stopping a figure
or table from splitting. Both have declarative style properties the author did
not use: `page_break_before` and `keep_with_next`. Both are properties, so both
are **styles** under the classification test, and neither needs a layout rule.
See the [audit, §6b](reference/reference-thesis-audit.md#6b-page-breaks-are-all-manual-and-they-serve-two-different-purposes).

**11pt body text is measured, and decided.** `Normal` sets Arial and double
spacing but no size, so it inherits Word's document default of 11pt —
identically in both audited documents. Most thesis rulebooks require 12pt, but
this faculty publishes neither a rulebook nor its template, so the approved
document is the best authority available and it renders at 11pt.

The cost of being wrong is bounded and worth stating, because it is why this was
not worth blocking on: one value in `uni-figmm/base`, one conformance
assertion, and a re-baselined page count in the golden fixture. No code, nothing
structural. See
[D16](11-decision-log.md#d16--body-text-is-11pt).

## Packaging

<a name="packaging"></a>
**One file per profile, with an `extends` chain. Not four cross-referencing
registries.**

```
profiles/
├── base/
│   └── apa7.yaml                    shared: double spacing, caption structure,
│                                    hanging indent, citation style
├── uni-figmm/
│   ├── base.yaml                    extends base/apa7 — page setup, styles,
│   │                                captions, numbering, pagination, indexes
│   ├── thesis-final@2024.yaml       extends uni-figmm/base — schema only
│   └── thesis-proposal@2026.yaml    extends uni-figmm/base — schema only
└── <next-institution>/
    └── …
```

The `uni-figmm/base` layer is not speculative: the two audited documents are
different document kinds whose style layers were **byte-identical** on every
property the audit marks *stable*. The seam was discovered by measurement, not
chosen by taste.

The long-term argument for splitting schemas, styles, policies and profiles into
four independent registries is sound: document variety is combinatorial, and
factoring it turns N×M into N+M+K. But the argument is about a state we are not
in. With one institution and one document kind, four registries buy nothing and
cost real machinery: cross-reference resolution, inheritance semantics,
validation of the configuration itself, and independent versioning of each piece.

`extends` is one inheritance mechanism instead of four. We split when the third
institution arrives — by then we will know where the seams actually are, rather
than guessing. That is the moment the factorisation gets tested, and it is
scheduled deliberately in the [Roadmap](10-roadmap.md).

## How a profile actually gets built

**By extracting it from an approved document.** This faculty publishes neither
its template nor a written rulebook, so there is nothing else to derive from.

An approved thesis is a sound basis, and it carries evidence a rulebook does
not: it shows what the institution **accepted in practice**. It is also far
easier to obtain — every graduate has one.

**It is not strictly better than a rulebook, and the conditions matter.** A
rulebook wins where:

- **It is current and the thesis is not.** An approved 2024 thesis says nothing
  about a 2026 rule change.
- **The rule is a prohibition.** "Tables may not exceed the text width" leaves no
  trace in a compliant document — there is nothing to extract.
- **The reviewer actually checks against it.** Then the rulebook, not past
  practice, is the standard being applied.
- **The approved document contains tolerated deviations.** Our reference thesis
  was accepted with a missing chapter prefix and duplicate equation numbers. It
  proves those were *tolerated once*, not that they are *permitted*.

So the accurate claim is narrower than "approved documents are more
authoritative": **where no rulebook is available, an approved document is a
sufficient and defensible basis; where both exist and conflict, that conflict
needs a human decision, not an automatic winner.**

```
approved-thesis.docx
        ↓  unzip, parse OOXML  (deterministic — no AI)
style definitions · fonts · sizes · spacing · margins · page setup ·
sections · numbering · fields · caption patterns · style usage counts
        ↓  semantic mapping  (LLM — this style appears to be the chapter title)
        ↓  human review
profiles/<institution>/base.yaml
```

Most of the work is deterministic. Style definitions, margins, page size,
numbering, section properties and field instructions are all stored explicitly
in OOXML — asking a model to read them would be strictly worse than parsing
them. An LLM is useful only for the semantic mapping step: deciding that
`XFIGURAS` is the figure label style, or that `TITU1` serves both chapters and
unnumbered top-level sections.

**This makes the product story simple:** *give us one approved thesis from your
university and we derive the profile.* That is the onboarding path for every
institution after the first.

### Three rules the extractor must follow

These come directly from the audits, and each one exists because ignoring it
would have produced a wrong profile.

**1. Extract by statistical mode, never by first value seen.** The audited
document with no template had 89% of its paragraphs directly formatted, mixed
Arial with Calibri across the body, and line spacing spread across 0.83, 0.88,
0.94, 0.96, 1.01, 1.15, 1.49, 1.50 and 1.52. Reading literal values there learns
the noise. Report the spread, and flag low-agreement properties for a human
decision rather than guessing.

**2. Extract from an *approved* document, not a draft.** The thesis proposal
never used `XTABLAS`, `XFIGURAS` or `X1`, so an extractor run on it would bind
the caption model to the wrong styles — and would conclude that equations are
not numbered. Both errors were in this design until the approved thesis was
audited.

**3. Prefer two documents from one template when available.** Where two
documents by different authors agree on a property, that property belongs to the
**template** rather than to one author's direct formatting. That is the whole
value of the second audited document: it turns "one author did this" into "the
template specifies this". The audit's *stable vs. drift* table is the output of
exactly this check.

### Separate the specification from the mistakes

An approved document is the specification for **format**, not for **errors**.
The audited thesis is missing a chapter prefix, has duplicate equation numbers,
mislabels two annexes, and carries a page number typed into the body under the
chapter-title style. We reproduce its format and correct its errors.

The line between the two is not always obvious, so the test is: **is this a
departure from the template's own evident intent?** A chapter missing its prefix
while three others have theirs is an error. A flat table of contents, where the
template defines `TDC2` and `TDC3` but the author used neither, is a layout
choice — so we reproduce it. Every call of this kind is recorded in the
[Decision Log](11-decision-log.md) with its reasoning.

## If a written rulebook is available

For institutions that do publish one, a rulebook is a useful second source —
better than extraction for rules that are *prohibitions* ("tables may not exceed
the text width"), since those leave no trace in a compliant document.

```
rulebook.pdf → LLM (constrained output) → draft rules + evidence
                                             ↓
                                    human review and approval
```

Two non-negotiable constraints, for the same reasons given in
[Architecture](02-architecture.md):

1. **Closed vocabulary.** The model may emit only rule types the engine can
   execute, enforced by a schema with enumerated rule names. Otherwise it
   invents rules that silently do nothing.
2. **Evidence for every rule.** Page number and verbatim quote:

```yaml
- id: frontmatter-roman
  rule: page_numbering
  region: frontmatter
  format: lower_roman
  evidence:
    page: 14
    quote: "Las páginas preliminares se numerarán con romanos minúsculos."
```

This makes the output reviewable and lets the conformance report cite the
rulebook when a document violates a rule. When an institution disputes a
formatting decision, that traceability is the whole argument.

**Not available for UNI-FIGMM.** Our first profile is extraction-only, which
means conformance findings cite the reference audit rather than a rulebook page.

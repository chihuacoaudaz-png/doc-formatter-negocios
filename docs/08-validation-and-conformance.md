# 08 — Validation and Conformance

## The report is a product, not a debug log

We ship documents that are 90–95% correct. The remaining 5% is a person's work.
That person needs to know **what** is left.

So the conformance report is not diagnostics for us. It is the recipient's
to-do list, and it is a first-class output of every build — not a later phase,
and not something enabled with a flag.

There is a second reason it matters more than it looks. The bottleneck in a
thesis is frequently not producing the document but **getting it accepted** by
an advisor or a faculty office. A report that says which rules are satisfied,
each traceable to its source, is an argument. A document alone is a claim.

For our first profile that source is the reference audit rather than a rulebook —
the faculty publishes neither a template nor written rules, so findings cite the
approved thesis we derived the profile from. For an institution that does
publish a rulebook, findings cite it by page; see
[Profiles](05-profiles-styles-policies.md#if-a-written-rulebook-is-available).

## Sample output

```
Conformance report
  document : thesis-sobrerotura
  profile  : uni-figmm/thesis-final@2024
  built    : 2026-09-10T22:41:07Z
  pages    : 134

STRUCTURE
  ok    4 of 4 required chapters present, in order
  ok    all 4 chapters carry their "Capítulo {roman}." prefix
  ok    7 top-level sections (Resumen, Abstract, Introducción,
        Conclusiones, Recomendaciones, Referencias, Anexos)
  ok    48 headings, levels consistent, no skipped levels
  ok    heading numbering automatic (multi-level list on TITU2/TITU3)

STYLE
  ok    A4, margins 2.5 / 2.5 / 3.0 / 2.5 cm
  ok    body Arial 11pt, line spacing 2.0, justified
  ok    fonts used: Arial, Cambria Math
  ok    0 paragraphs with direct formatting overrides
  ok    pagination: cover none / front matter i-xv roman /
        body 1-106 arabic / annexes 1-9 arabic

CONTENT
  ok    37 tables, labels Tabla 1-37 via SEQ, style XTABLAS
  ok    82 figures, labels Figura 1-82 via SEQ, style XFIGURAS
  ok    141 equations rendered (26 display), numbered (1)-(26)
  ok    93 assets resolved, all within 15.50 cm text width
  ok    64 citations resolved against references.bib (APA 7)
  ok    4 index fields generated (contenido, tablas, figuras, anexos)
  ok    2 annexes in landscape sections

FINDINGS
  warn  table-fits      sections/03-desarrollo.md:412
        Tabla 22 is 17.8 cm wide; portrait text width is 15.50 cm.
        Fix: move to a landscape section, or reduce cell font to 8pt.

  warn  has-title       sections/04-analisis-resultados.md:96
        Figura 71 has no `title`. APA 7 requires a title below the label.

  warn  note-on-external  sections/02-marcos-teorico-conceptual.md:233
        Figura 18 has no `note` but its source appears to be external.
        APA 7 requires a source note below the figure.

  info  no-raw-blocks   sections/03-desarrollo.md:58
        1 raw block passed through unprocessed (target=docx).

  4 findings: 0 fatal, 0 errors, 3 warnings, 1 info.
  Estimated manual work: 3 items.
  exit 0
```

For comparison, the human-formatted original of this same thesis — which was
**approved** — would fail four of the `ok` lines above: it is missing a chapter
prefix, its equation tags contain duplicates and one out-of-order value, it uses
`Arial Narrow` and `Times New Roman` against a one-font template, and 21–26% of
its paragraphs carry direct formatting. That gap is the product.

Each finding carries **a file and a line in `DocSource`**, not a position in the
DOCX. The person fixes the source and rebuilds. A finding that says "paragraph
847 of document.xml" is useless.

## Two validation stages, deliberately

| | `validate:structure` (pass 4) | `validate:conformance` (pass 13) |
|---|---|---|
| Runs | Before any rendering | On the produced file |
| Input | `SemanticIR` | The DOCX package |
| Cost | Milliseconds | Seconds to minutes |
| Catches | Missing sections, unresolved references, unknown block types, broken citation keys, skipped heading levels | Actual page count, real rendered widths, style application, field presence |

Splitting them is not redundancy. Pass 4 catches what is cheap and actionable
and fails fast — there is no reason to spend a minute rendering a document whose
methodology chapter is missing. Pass 13 catches what can only be known once the
file exists.

## Severity and build semantics

An earlier version of this document contradicted itself here: the table said an
`error` produced no file, and the prose immediately below said the default was
to produce a file with placeholders. The contradiction came from conflating two
genuinely different things, so the fix is a fourth severity rather than a
reworded sentence.

| Severity | Meaning | File produced? | Exit code |
|---|---|---|---|
| `fatal` | The build **cannot** proceed | **No** | non-zero |
| `error` | A hard requirement is unmet, but a document can still be produced | **Yes**, with a visible placeholder | non-zero |
| `warning` | Produced; a human must decide | Yes | zero |
| `info` | Worth knowing | Yes | zero |

**`fatal` is a capability limit, not a judgement.** It fires only when there is
nothing to produce: an unparseable manifest, a referenced section file that does
not exist, an asset that cannot be read or decoded, a profile that fails its own
schema. No policy decision is involved — the engine physically cannot emit a
document.

**`error` is a conformance judgement,** and it does not stop the build. A missing
required chapter produces a document containing:

```
[MISSING: Capítulo III. Desarrollo del trabajo de investigación]
```

visible in the output, plus an `error` finding and a non-zero exit code.

### Why `error` still produces a file

Because the report is an interface to the **content agent**, and a build that
produces nothing teaches nothing. The agent needs to see which sections are
missing in order to write them; the author needs to see the document taking
shape while it is still incomplete. A placeholder is visible, unambiguous, and
impossible to mistake for finished work.

The non-zero exit code is what keeps this honest: automation that treats exit
code zero as "ready to submit" will not be fooled by a document full of
placeholders.

### `--strict`

For a final submission, `--strict` promotes every `error` to `fatal`: no file,
non-zero exit. Correct when an incomplete document is worthless and shipping one
by accident is the real risk.

The default is deliberately the permissive one because the common case during
development is an incomplete document, and the rare case is submission.

## Visual validation

Some defects are not visible in the file's structure at all — only in its
rendered pages:

- a heading alone at the bottom of a page
- a table running past the margin
- an image cropped or distorted
- a caption separated from its object by a page break
- blank pages
- excessive vertical whitespace

These are checked by rendering to PDF and inspecting the pages.

```
DOCX → LibreOffice → PDF → page images → checks
```

Two classes of check, and they should not be confused:

**Geometric checks are deterministic and belong in v1's later phases.** Text
extraction with coordinates answers "does any element's bounding box exceed the
text area?" and "is this heading the last line on the page?" exactly, with no
model involved.

**Perceptual checks need a vision model, and come later.** "Does this page look
wrong?" is genuinely ambiguous, which is precisely the criterion for using a
model — the same criterion applied everywhere else in this design.

## Page count is a first-class assertion

Many rulebooks specify minimum or maximum page counts. Page count is also the
most sensitive integration signal we have: it changes if a font is substituted,
if line spacing is misapplied, if a margin is wrong, or if an image is scaled
incorrectly.

So every build reports the page count, and every golden fixture asserts it
within a tolerance. See [Testing Strategy](09-testing-strategy.md).

This makes font availability a correctness concern rather than a cosmetic one.
Arial is absent from a stock Linux container; LibreOffice substitutes Liberation
Sans, which is metrically compatible but not identical. Either install the real
fonts or record the substitution as a deliberate decision — but do not discover
it from a page count that drifts in continuous integration.

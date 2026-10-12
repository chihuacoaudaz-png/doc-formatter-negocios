# 09 — Testing Strategy

A formatting engine has an unusual property: its output is large, structured,
and mostly *correct-looking* even when it is wrong. Tests are the only thing
standing between "we changed a pass" and "we silently broke 40 pages."

## The fixture corpus

**Current implementation scope:** the sample in
[`fixtures/uni-figmm-text-math`](../fixtures/uni-figmm-text-math/README.md)
transcribes Resumen, Abstract and Chapter I from the approved thesis, plus
explicitly identified supplemental test equations, with no images. Assertions
cover parsing, authored frontmatter, heading prefixes/numbers, source
diagnostics, editable math, equation numbering and cross-references.
The complete corpus and page-count targets below belong to the later expansion
in Phase 1c; they do not block the first working sample.


Every profile ships with at least one complete document fixture and its expected
output.

```
fixtures/
└── uni-figmm-thesis-final/
    ├── source/                    a complete DocSource
    │   ├── document.yaml
    │   ├── references.bib
    │   ├── assets/                93 files, ~11 MB
    │   └── sections/
    ├── expected/
    │   ├── semantic-ir.json       after pass 4
    │   ├── reference-map.json     after pass 7
    │   ├── layout-plan.json       after pass 9
    │   ├── document.docx          golden output
    │   ├── page-count.txt         134
    │   └── conformance.json       expected findings
    └── pages/                     rendered page images for visual diffing
```

The first fixture is a faithful transcription of the **approved** reference
thesis, and it is the acceptance test for the whole project: **134 pages, 141
equations (26 display, numbered), 37 tables, 107 images across 93 media files,
five sections, three page-numbering regions including a landscape annex block,
and four live style-driven index fields.**

A second, smaller fixture transcribes the 73-page thesis proposal. It costs
little and it exercises the other document kind against the same style layer —
which is the cheapest available test of whether the schema/style split actually
holds.

## Golden files at every stage, not just the end

Because the pipeline is a sequence of pure passes, each boundary is a test
point.

| Boundary | Compared | Catches |
|---|---|---|
| After `parse` | `SemanticIR` JSON | Parser regressions, with a readable diff |
| After `number` | Reference map | Numbering and cross-reference bugs, isolated from rendering |
| After `bind:styles` | `LayoutPlan` JSON | Wrong style bound to a role |
| After `emit` + `postprocess` | DOCX, structurally | Field insertion, sections, pagination |
| After `render:pdf` | Page count, page images | Everything, including font substitution |

The middle rows are the valuable ones. A failing test that says *"the reference
map changed: `tbl:props` moved from `Tabla 2` to `Tabla 3`"* localises a bug in
seconds. A failing test that says *"the DOCX differs"* does not.

## DOCX must be normalised before it can be compared

A DOCX is not reproducible by default. Two builds of identical input differ in:

- creation and modification timestamps in `docProps/`
- `w:rsid` revision-save identifiers throughout `document.xml`
- ZIP entry order and per-entry timestamps
- `w14:paraId` and `w14:textId` paragraph identifiers

The `postprocess:normalize` pass strips all of these. Without it, golden
comparison is comparing noise, the tests get muted, and the suite stops being
worth running.

Comparison itself is done on the **unzipped, canonicalised XML**, not on the ZIP
bytes — so a failure diff is readable.

## Page count as the integration signal

One assertion catches a surprising share of real defects:

```
expected: 134 pages
tolerance: ±3
```

It fails when a font is substituted, line spacing is misapplied, a margin is
wrong, an image is scaled incorrectly, or a section break lands in the wrong
place. It is a single number that is sensitive to most of what can go wrong in
layout.

The tolerance exists because justification and hyphenation are not perfectly
deterministic across renderer versions. A drift beyond tolerance is a real
signal and should be investigated, not widened.

## Visual regression

Rendered pages are hashed and compared perceptually, not byte-for-byte:

```
DOCX → PDF → PNG per page → structural similarity vs. expected
```

A page below the similarity threshold fails, and the diff image is attached to
the failure. This is the only practical way to catch "the caption ended up on
the next page" without writing a bespoke assertion for every possible layout
defect.

Run this on the fixture corpus in continuous integration, not on every local
test run — it is slow and needs a renderer and fonts present.

## Conformance tests per profile

A profile's requirements become a set of assertions, so that we can prove a
profile is implemented rather than assert it. For UNI-FIGMM those requirements
come from the [reference audit](reference/reference-thesis-audit.md), since the
faculty publishes no rulebook.

```yaml
# fixtures/uni-figmm-thesis-final/conformance-assertions.yaml
- { assert: page_size,          equals: A4 }
- { assert: margin_left,        equals: 3.0cm }
- { assert: body_font,          equals: Arial }
- { assert: body_size,          equals: 11pt }
- { assert: body_line_spacing,  equals: 2.0 }
- { assert: frontmatter_page_format, equals: lower_roman }
- { assert: body_page_format,   equals: arabic, restart_at: 1 }
- { assert: annex_page_format,  equals: arabic, restart_at: 1 }
- { assert: annex_orientation,  equals: landscape, for: [anexo-8, anexo-9] }
- { assert: heading_numbering,  is: automatic }
- { assert: chapter_prefixes,   all_present: true }   # the approved doc fails this
- { assert: table_labels,       via: SEQ, style: XTABLAS,  sequence: gapless }
- { assert: figure_labels,      via: SEQ, style: XFIGURAS, sequence: gapless }
- { assert: equation_labels,    via: SEQ, format: "({n})", sequence: gapless }
- { assert: index_fields,       count: 4, style_driven: true }
- { assert: bibliography_indent,hanging: 1.27cm }
- { assert: fonts_used,         subset_of: [Arial, Cambria Math] }
- { assert: direct_formatting_paragraphs, max: 0 }
- { assert: page_break_before,  via: style, on: [chapter_title, top_level_section_title] }
- { assert: manual_page_breaks, max: 0 }   # the approved original has 32
- { assert: keep_with_next,     on: [table_label, figure_label, caption_title] }
```

**Several of these assertions fail against the approved document itself, and
that is the point.** It is missing a chapter prefix, its equation tags contain
duplicates and one out-of-order value, it carries 192 `Arial Narrow` and 38
`Times New Roman` runs against a template specifying Arial, and 21–26% of its
paragraphs carry direct formatting. The fixture's *expected output* is the
corrected document, not a byte-copy of the original — so the golden file is what
the engine *should* produce, and the audit records where it deliberately differs
from the human original.

The direct-formatting assertion deserves particular attention. Our output should
have **zero**, because that is what makes the manual 5% cheap: a person changes
one style instead of hundreds of paragraphs.

## Rule-classification tests

[D9](11-decision-log.md#d9--style-layout-and-conformance-are-three-different-things)
requires that the resolver, not the configuration author, decides whether a rule
is a style, a layout transform or a conformance check. That is testable, and it
needs to be: the design committed exactly this bug once already, classifying
`pageBreakBefore` as a style in one section and implementing it as a layout rule
in another.

Two assertions over every loaded profile:

- **No rule appears in more than one kind.** A rule id declared in both `styles`
  and `layout` fails the load.
- **Every `layout` rule actually changes the node tree.** Run it against a
  fixture and diff the plan; a layout rule that produces an identical tree is
  misfiled and should be a style. This catches the original bug directly.

## Idempotency tests

Every layout rule must be safe to apply twice. This is cheap to test and it
catches a class of bug that is otherwise very hard to find: a rule that inserts a
section break each time it runs produces a document that is subtly wrong only
after a retry or a resumed build.

```
apply(rules, plan) == apply(rules, apply(rules, plan))
```

## Property tests worth having

Beyond fixtures, a few invariants hold for any valid document and are worth
asserting over generated inputs:

- every `CrossRef` resolves to a node that exists
- every `SEQ` sequence is gap-free and starts at 1
- no `Table` or `Figure` exceeds the profile's text width without a
  corresponding finding
- heading levels never skip
- the number of `w:sectPr` elements equals the number of layout regions
- every chapter carries its `Capítulo {roman}.` prefix
- every emitted caption label uses the index-source style for its kind
- no element in the `SemanticIR` carries a font, size, colour, margin,
  alignment, line spacing, indent, style name, or **absolute length** — the
  invariant from [Semantic IR](04-semantic-ir.md#the-exception-boundary),
  asserted mechanically rather than trusted. `Figure.width` is the one permitted
  exception and must be relative (`%`) or `natural`
- no `Container.kind` or `Paragraph.role` value names a medium-specific
  mechanism — `wide` and `standalone` pass, `landscape` and `unindented` do not

Those two are the most valuable tests in the suite. The IR invariant is what
keeps a second backend additive rather than a rewrite, and it is not a
hypothetical risk: **this design violated it in three places before the boundary
was written down as a test** — see
[D25](11-decision-log.md#d25--the-ir-has-one-declared-presentational-exception-and-it-is-relative).
A stated principle does not enforce itself.

## What we do not test

**Pandoc's correctness.** We test that we invoke it correctly and that its
output survives our post-processing. We do not test that it converts a list.

**LibreOffice's rendering.** We pin its version and treat its output as the
reference. When we upgrade it, the golden fixtures are re-baselined
deliberately, as a reviewed change.

**Aesthetics.** No test can tell us a document looks good. That is what the
reference fixture and human review are for.

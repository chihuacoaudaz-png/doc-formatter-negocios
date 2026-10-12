# 02 — Architecture

## The shape of the system

This is a compiler. Content goes in one end, a formatted file comes out the
other, and in between there is a fixed sequence of named, individually testable
passes over three successive representations.

```
                     ┌─────────────────────────────────────┐
  FRONT ENDS         │  content agent · human editor ·     │
                     │  unformatted DOCX · structured data │
                     └──────────────────┬──────────────────┘
                                        ↓
  ┌──────────────────────────────────────────────────────────────────────┐
  │  DocSource        Markdown + YAML on disk. Human-readable.           │
  │                   What the agent writes. The handoff boundary.       │
  └──────────────────────────────────┬───────────────────────────────────┘
                                     ↓  parse · normalize · validate
  ┌──────────────────────────────────────────────────────────────────────┐
  │  SemanticIR       What each element *is*. No fonts, no margins,      │
  │                   no page breaks, no style names. Never mutated      │
  │                   by formatting rules. Persistable and diffable.     │
  └──────────────────────────────────┬───────────────────────────────────┘
                                     ↓  ← PROFILE (schema · styles · layout · conformance)
                                     ↓     resolve assets · citations · numbering
                                     ↓     apply layout transforms · bind styles
  ┌──────────────────────────────────────────────────────────────────────┐
  │  LayoutPlan       Styles bound, labels assigned, sections and        │
  │                   breaks placed, fields declared. Presentational     │
  │                   and disposable. One per output target.             │
  └──────────────────────────────────┬───────────────────────────────────┘
                                     ↓  emit
                 ┌───────────────────┼───────────────────┐
                 ↓                   ↓                   ↓
            DOCX backend        LaTeX backend       HTML backend
          (Pandoc + OOXML        (future)             (future)
           post-processing)
                 ↓
              DOCX  ──→  field refresh (LibreOffice)  ──→  conformance report
                                     ↓
                                    PDF (optional)
```

## Why three representations and not one

The instinct is to have a single document model. That fails at a specific point,
and it is worth being precise about where.

Consider the rule *"each chapter starts on a new page."* If formatting rules are
allowed to mutate a single document model, that rule inserts a page break into
it. The moment it does, the model is no longer format-independent: a page break
is meaningless in HTML, and the model can no longer be used for any other
output. The promise that one model serves many outputs is broken by the first
rule you apply.

So the separation is not aesthetic:

| Representation | Contains | Never contains | Lifetime |
|---|---|---|---|
| **DocSource** | Authored content and its structure | Anything a person should not have to type | Committed to version control |
| **SemanticIR** | What each element *is*; document structure; resolved references | Fonts, sizes, margins, page breaks, style names, anything Word-specific | Persisted per document version; diffable |
| **LayoutPlan** | Bound styles, assigned labels, placed sections and breaks, declared fields | Nothing — it is the last stop before bytes | Rebuilt on every render; cached, never stored |

`SemanticIR` is immutable through the formatting stages. Profiles do not modify
it; they *drive the lowering* from it into a `LayoutPlan`. That single rule is
what keeps a future LaTeX or HTML backend an **additive** piece of work rather
than a re-architecture. It does not make one cheap — see
[Goals and Scope](01-goals-and-scope.md#use-cases-in-priority-order) for what is
still unfinished there.

## The pass pipeline

Each numbered step is a pure function with typed input and output, individually
testable, and dumpable with `--dump-after=<pass>`. That last property matters
more than it sounds: formatting bugs are of the form *"why did this caption end
up above the table?"*, and without the ability to inspect state between passes,
debugging them is guesswork.

| # | Pass | Input → Output | What it does |
|---|---|---|---|
| 1 | `load` | disk → file set | Read the manifest, resolve section file list, locate assets |
| 2 | `parse` | files → SemanticIR | Markdown + YAML + fenced blocks into nodes |
| 3 | `normalize` | IR → IR | Whitespace, locale-correct quotes and dashes, decimal separators, unicode normalisation |
| 4 | `validate:structure` | IR → findings | Required and ordered sections, heading level jumps, closed-vocabulary check. **Runs before rendering** |
| 5 | `resolve:assets` | IR → IR | Resolve paths, probe intrinsic dimensions, convert unsupported formats, compute display size against text width. Not a marginal pass: the approved thesis carries 93 media files, ~11 MB |
| 6 | `resolve:citations` | IR → IR | Citation processor over the bibliography; render in-text citations and the reference list |
| 7 | `number` | IR → IR + xref map | Assign labels to headings, tables, figures, equations, annexes; resolve every cross-reference to a target |
| 8 | `transform:layout` | IR → LayoutPlan | Apply the profile's layout rules: chapter title prefixes, caption placement, section breaks, the three page-number regions, landscape blocks, front-matter slot expansion, index field placement |
| 9 | `bind:styles` | LayoutPlan → LayoutPlan | Map each semantic role to a concrete named style from the profile |
| 10 | `emit` | LayoutPlan → backend artefact | Backend-specific serialisation |
| 11 | `postprocess` | artefact → artefact | For DOCX: section properties, page-numbering formats, `SEQ`/`REF`/`TOC` field insertion, style cleanup, reproducibility normalisation |
| 12 | `refresh:fields` | artefact → artefact | Headless LibreOffice updates TOC, page references and sequence numbers |
| 13 | `validate:conformance` | artefact → report | Check the produced file against the profile's constraints |
| 14 | `render:pdf` | artefact → PDF | Optional |
| 15 | `validate:visual` | PDF → findings | Optional, later phase |

Passes 4 and 13 both validate, and that is intentional: pass 4 catches what is
cheap and actionable before any rendering work happens; pass 13 catches what can
only be known once the file exists.

## Front ends

The engine has exactly one input: `DocSource`. Everything else is a front end
that produces `DocSource`.

**Content agent (primary).** The thesis writer emits `DocSource` directly, one
Markdown file per section. This is the path that matters and it is the reason
the authoring format is Markdown rather than JSON — see
[Authoring Format](03-authoring-format.md#why-not-json) for the argument, which
is quantitative.

**Human editor.** `DocSource` is plain text. A person can open it, fix a
sentence, and re-run. This is not a nice-to-have: it is how content review
happens without round-tripping through Word.

**Unformatted DOCX (use case 2).** Extract text, detect structure with
heuristics plus an LLM, emit `DocSource`.

```
unformatted.docx → extract → detect structure → DocSource
                                    ↓
                       ┌────────────────────────────┐
                       │  HUMAN REVIEWS THE OUTLINE │  ← mandatory
                       └────────────────────────────┘
                                    ↓
                              normal pipeline
```

The review step is not optional. Structure detection will confuse a bold
paragraph with a heading, and it is an order of magnitude cheaper for a person
to correct three lines of an outline than forty pages of wrong output.

**Structured data (future).** Query results or API responses to a data report.
This is a deterministic adapter; see the AI boundary below.

## Where the LLM belongs, and where it does not

| Task | Mechanism | Why |
|---|---|---|
| Write the thesis content | LLM | Genuinely generative |
| Convert human notes into `DocSource` | LLM | Requires judgement about what is a heading |
| Recover structure from an unformatted DOCX | LLM + heuristics + human review | Ambiguous, and the cost of error is high |
| Map extracted styles to semantic roles ("this style is the chapter title") | LLM, constrained | Genuinely ambiguous; the values themselves are parsed, not inferred |
| Read a written rulebook (PDF) into a draft profile | LLM, constrained | Ambiguous input, auditable output — when a rulebook exists at all |
| Convert CSV or query results into a table | Deterministic adapter | Input already has explicit structure |
| Read a font size out of a DOCX | Deterministic | The value is stored explicitly; asking a model is strictly worse |
| Apply a margin, place a caption, number a table | Deterministic | Rules, not judgement |
| Generate formatting code per document | **Never** | This is the failure mode the architecture exists to prevent |

**Deriving a profile from documents** is the highest-leverage LLM use in the
system. Our first institution publishes neither a template nor a rulebook, so
the profile is extracted from an **approved thesis** — mostly deterministic
OOXML parsing, with a model only for the semantic mapping step. See
[Profiles](05-profiles-styles-policies.md#how-a-profile-actually-gets-built).

Where a model does produce rules, two constraints make it trustworthy:

1. **Closed output vocabulary.** The model emits only rule types the engine can
   execute, enforced by a schema with enumerated rule names. Without this it
   invents rules that silently do nothing.
2. **A citation for every rule.** Each emitted rule carries the page and the
   verbatim quote it came from. This turns an unverifiable model output into a
   reviewable artefact, and lets the conformance report say *"rule X, per the
   rulebook, page 14"* — or, for an extracted profile, *"rule X, per the
   reference thesis, §4"*. When negotiating with an institution, that is the
   difference between "trust our script" and a traceable claim.

## What the architecture deliberately does not have

**No Pandoc AST as our data model.** Pandoc is a rendering backend. Its AST is
presentational rather than domain-semantic: it has `Header` and `Table` but no
concept of "this is the methodology section" or "this is an annex in a landscape
section." Encoding those as `Div` attributes is stringly-typed and unvalidatable,
and `pandoc-types` changes across major versions, which would tie persisted
documents to a Pandoc release. Concretely, it cannot express the four-block APA
caption, the three page-numbering regions, or the four style-driven index fields
without degenerating into attribute strings. See
[Decision Log](11-decision-log.md).

**No separate registries for schemas, styles, policies and profiles.** One
profile file with an `extends` chain. With a single institution, four
cross-referencing registries are machinery without return — resolution,
inheritance, config-level validation, and independent versioning of each piece.
We split them when the third institution arrives and we know where the seams
actually are. See [Profiles](05-profiles-styles-policies.md#packaging).

**No template-filling engine.** Filling placeholders in a prepared DOCX is a
legitimate technique for rigid, high-volume documents, and it is a second,
parallel architecture that bypasses this entire pipeline. It is not needed for
theses. If it is ever added it must be a clearly separate path, never the
default for content that can be modelled semantically.

**No PDF renderer of our own.** PDF comes from converting a rendered artefact.

**No footnotes, endnotes, code blocks, or per-chapter numbering in v1.** All
three audited documents contain zero footnotes, zero endnotes and zero code
blocks, and all three number figures, tables and equations globally rather than
per chapter. These are cuts backed by measurement.

**Equation numbering, by contrast, is in scope** — it was cut once, on evidence
from an unapproved draft, and the approved thesis reversed that. See
[D14](11-decision-log.md#d14--v1-omits-footnotes-endnotes-and-code-blocks-equation-numbering-is-in-scope).

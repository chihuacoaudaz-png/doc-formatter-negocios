# 01 — Goals and Scope

## The problem

Producing a formal document is two jobs that normally get tangled together:

1. **Writing the content** — what the document says.
2. **Formatting the document** — margins, fonts, heading hierarchy, caption
   conventions, page numbering, indexes, figure and table numbering, citation
   layout.

Job 2 is mechanical and rule-driven, and it is where most of the human hours go.
It is also where humans reliably fail. The audited **approved** thesis — a
complete, formatted, accepted document — is missing a chapter's `Capítulo II.`
prefix, has 50 equation tags for 47 numbers with duplicates and one out of
order, lists two annex sub-items in the annex index as if they were annexes, and
carries a page number typed into the body under the chapter-title style. The
thesis proposal from the same faculty has three headings numbered `1.1.2.1` and
tables labelled 2, 3, 4, 5, 9A, 9B. See the
[Reference Thesis Audit](reference/reference-thesis-audit.md) for the full
measurement.

This project is job 2, isolated.

## Why isolate it

Our first consumer is a thesis-writing agent. The obvious approach is one agent
that writes the content *and* produces the Word file. We deliberately reject
that, for four reasons:

1. **Different iteration speeds.** Content needs many review cycles with the
   author. Formatting needs to be right once per institution. Coupling them
   means every content revision re-runs the slow, expensive part.
2. **Different failure modes.** Content generation is probabilistic and
   requires human judgement to accept. Formatting is deterministic and can be
   verified automatically against a rulebook — every defect listed above is
   machine-detectable.
3. **Different reuse.** A formatting rulebook amortises across every thesis for
   that institution. Content applies to exactly one thesis.
4. **Testability.** With a standardised handoff format, the formatter has
   fixtures. We can run a 73-page document through the whole pipeline as a
   regression test without spending a single token. If content and formatting
   are coupled, the formatter can never be tested in isolation.

Point 4 is the one most often missed, and it is the most valuable.

## What "done" means

**We are not aiming for perfection.** The target is **90–95% correct on the
first pass**, with the remainder fixable by hand in minutes.

That is a design constraint with teeth. It means the deliverable is not "a
correct DOCX" — it is **"a DOCX that is cheap to finish by hand."** Those are
different optimisation targets, and the second one dictates concrete decisions:

- **Zero direct formatting. Everything through named styles.** If a person needs
  to change the body line spacing, they change one style and the whole document
  follows. A document with hard-coded formatting on every paragraph costs hours
  to adjust.
- **Live Word fields, not baked-in numbers.** If numbering is static text, a
  single manual insertion in the middle invalidates everything after it, and the
  5% of manual work becomes 30%. With real fields, the person edits and presses
  F9. See [Numbering and Fields](07-numbering-and-fields.md).
- **A machine-readable list of what we could not do.** The engine knows when a
  table is too wide or a required section is missing. That list is the person's
  to-do list for the last 5%, and it is a first-class output. See
  [Validation and Conformance](08-validation-and-conformance.md).

> A document that is 98% correct but impossible to touch afterwards is worse
> than one that is 92% correct and easy to finish.

## Use cases, in priority order

**1. Thesis formatting (primary).** Theses against a specific institution's
rulebook, with content produced upstream by an agent. This is the only use case
that drives v1.

Measured scale, confirmed as representative: an undergraduate thesis is
**~134 pages / ~29,000 words**; a master's proposal is ~73 pages / ~19,000
words. Budget **216–266 words per page**, at the lower end for figure-heavy
documents. This is roughly double the 60–70 pages originally assumed for
undergraduate work, which affects the content agent's volume rather than the
formatter.

**2. Formatting documents that are already written (funded, near-term).** The
content exists but arrives unformatted or badly formatted. This reuses the whole
pipeline behind a different front end: recover the document's structure, convert
to our authoring format, then format normally. The structure-recovery step needs
mandatory human review — see [Architecture](02-architecture.md#front-ends).

**3. Generating documents for end users (future).** Producing files from inside
an application, where the output may be PDF or LaTeX rather than Word.

These are one engine rather than three because they share the same shape: take
structured content, apply a rulebook, emit a file. The discipline that keeps
them shareable is cheap and stated in the architecture: **no Word-specific
concept is ever allowed into the authoring format or the semantic IR.**

What that discipline buys is precise, and worth not overstating: if the IR says
`heading` and not `TITU2`, adding a backend is **new work rather than a
re-architecture**. It is not nearly free. We have built no second backend and
have no estimate for one, and there is a known unfinished piece — every style
role in a profile currently carries a `docx_style` field, so a second backend
needs a parallel style-name mapping that does not exist yet. The claim is only
that the cost is contained in one layer.

## Non-goals

**Not a replacement for Word.** We model what our profiles require, not the
whole Word feature surface. Where an existing tool does the job — Pandoc,
LibreOffice, a citation processor — we use it.

**Not pixel-perfect output.** See "What done means".

**Not one formatter per document type.** Adding an institution or a document
kind must mean adding configuration, not code. Code grows when a genuinely new
*capability* appears (the first time we need a signature block), not when a new
format appears.

**Not a content generator.** What the document says is somebody else's job.

**Not a reproducer of human errors.** An approved document is our specification
for *format*, not for *mistakes*. Where the reference thesis departs from its own
template's evident intent — a chapter missing its number prefix, duplicated
equation tags — we correct it. Where it makes a deliberate layout choice we
would have made differently, we reproduce it.

**Not a DOCX round-trip.** Generation is one-way: authoring format → DOCX. We do
not attempt to read an edited DOCX back into the authoring format and preserve
fidelity. That problem is disproportionately hard, and the alternative is
cheaper: keep editing upstream, in the authoring format, and regenerate. Use
case 2 is not a counterexample — it is a one-time structure recovery with a
human in the loop, not a lossless round-trip. This is a stated constraint so
that nobody promises otherwise.

**Not a code generator.** We do not use an LLM to write per-document formatting
code at runtime. A new format is configuration against a fixed engine. Code
generation stays a development-time tool.

## Success metrics

The engine is worth its cost only if these move:

| Metric | Why it matters |
|---|---|
| **Person-hours per delivered document** (before vs. after) | The direct saving |
| **Rounds of formatting-only correction** from the reviewer or advisor | Measures whether the output is actually accepted, not just produced |
| **Findings in the conformance report on first pass** | Measures the size of the manual 5% |
| **Time to onboard a new institution** | Measures whether the factorisation actually works. The onboarding input is one approved thesis from that institution |

The last one is the real test of the architecture. If adding a second university
requires code, the design failed regardless of how clean it looks.

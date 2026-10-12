# Doc-formatter — Design Documentation

This folder holds the **internal design** of the document formatting engine.
It is not the agent brief. Content agents get
[`dialect/docsource.md`](../dialect/docsource.md) plus a playbook under
[`playbooks/`](../playbooks/) (UNI FIGMM:
[`playbooks/uni-figmm-thesis/`](../playbooks/uni-figmm-thesis/)).

The parser and DOCX backend are implemented for profile `uni-figmm/thesis@1`
(Resumen, Abstract, Chapters I–IV in the fixture, plus optional math
regression). The wider design remains the target specification. See
[Implementation Stack](12-implementation-stack.md) for the current supported
subset and how it differs from later milestones.

## Reading order

| # | Document | What it answers |
|---|---|---|
| 01 | [Goals and Scope](01-goals-and-scope.md) | What we are building, what "done" means, what we refuse to build |
| 02 | [Architecture](02-architecture.md) | The layers, the three representations, the compiler pass pipeline |
| 03 | [Authoring Format](03-authoring-format.md) | `DocSource` — what the content agent actually writes |
| 04 | [Semantic IR](04-semantic-ir.md) | The closed node vocabulary the compiler works on |
| 05 | [Profiles, Styles, Policies](05-profiles-styles-policies.md) | How a rulebook is expressed as configuration |
| 06 | [Rendering Backends](06-rendering-backends.md) | Pandoc, OOXML post-processing, and the future LaTeX/HTML paths |
| 07 | [Numbering and Fields](07-numbering-and-fields.md) | Automatic numbering, cross-references, and why Word fields matter |
| 08 | [Validation and Conformance](08-validation-and-conformance.md) | The compliance report as a product surface |
| 09 | [Testing Strategy](09-testing-strategy.md) | Golden files, page-count assertions, visual regression |
| 10 | [Roadmap](10-roadmap.md) | Build order and exit criteria per phase |
| 11 | [Decision Log](11-decision-log.md) | Every significant decision, its rationale, and what we rejected |
| 12 | [Implementation Stack](12-implementation-stack.md) | Selected engine language, external tools, and pending dependency choices |
| 13 | [Agent input (pointer)](13-agent-input.md) | Points to `dialect/` + `playbooks/`; design docs stay here |

## Reference material

| Document | What it holds |
|---|---|
| [Reference Thesis Audit](reference/reference-thesis-audit.md) | Measured facts extracted from the sample thesis we were given |
| [UNI-FIGMM Profile](reference/uni-figmm-profile.md) | The first real profile, derived from that audit |

## Glossary

Acronyms and terms used throughout, defined once here.

| Term | Meaning |
|---|---|
| **APA 7** | American Psychological Association style manual, 7th edition. Citation and caption conventions used by the reference thesis. |
| **CSL** | Citation Style Language. An XML format describing how citations and bibliographies are rendered. Standard, with a public repository of ~10,000 styles including APA 7. |
| **DOCX** | The Microsoft Word file format since Word 2007. A ZIP archive containing XML files. |
| **Dialect** | Shared Markdown/YAML contract the engine accepts (`dialect/docsource.md`). Portable across institutions. |
| **DocSource** | Our authoring format: a folder of Markdown files plus a YAML manifest. What the content agent writes. |
| **Playbook** | Institution / document-kind instructions for an agent (`playbooks/…`). Chapter map, profile id, parking rules. |
| **EMU** | English Metric Unit. The internal length unit of Office documents. 1 cm = 360,000 EMU. |
| **IR** | Intermediate Representation. A structured in-memory form of the document, between input and output. |
| **LayoutPlan** | Our third representation: the document after styles, numbering, and page layout have been resolved, but before a file is written. |
| **OOXML** | Office Open XML. The XML schema family inside a DOCX file (`document.xml`, `styles.xml`, `numbering.xml`, and others). |
| **OMML** | Office Math Markup Language. How Word stores equations. |
| **Pandoc** | An open-source document converter. We use it as a rendering backend, not as our data model. |
| **Profile** | A named, versioned rulebook: one institution's requirements for one document kind. |
| **SemanticIR** | Our second representation: the document's meaning and structure, with no visual or page-layout information. |
| **twip** | Twentieth of a point. The length unit used in most of OOXML. 567 twips = 1 cm. |

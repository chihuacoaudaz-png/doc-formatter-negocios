# DocSource dialect

**What Markdown and YAML the engine accepts today.** This is the shared
authoring contract for any document kind. It is *not* a university playbook:
chapter titles, profile ids, and which files to park live in a playbook under
`playbooks/`.

Give a content agent **this file** plus a **playbook** plus the source
document. The agent returns a `DocSource` folder. Doc-formatter turns that
folder into a formatted document.

The long-term design essay is [docs/03-authoring-format.md](../docs/03-authoring-format.md).
This page wins when they disagree about what a build accepts **now**.

Working shape reference (open the files; copy structure, not topic):
[`fixtures/uni-figmm-text-math/source`](../fixtures/uni-figmm-text-math/source).

---

## 1. The job

You convert an existing document into **semantic source**. You do not format.

| You do | You do not |
|---|---|
| Split the document into one `.md` file per section | Emit `.docx`, PDF, HTML, or JSON IR |
| Strip hand-written numbers, chapter prefixes, TOC, cover | Invent fonts, margins, page breaks, Word style names |
| Put keywords and title in `document.yaml` | Type keyword labels in Markdown (the profile adds them) |
| Keep the author's prose, math, bold, italic | Rewrite unless the operator asked for edits |
| List omitted constructs in `CONVERSION-NOTES.md` | Invent nested lists or `[@cite]` |

A human (or a later pass) runs `doc-formatter build` on the folder you return.

---

## 2. Deliverable tree

Return a **folder**, not a single concatenated Markdown file.

```
<docsource>/
├── document.yaml              required — order and metadata
├── CONVERSION-NOTES.md        required if anything was omitted or parked
├── assets/                    images referenced by :::figure
└── sections/
    ├── 00-….md
    └── …
```

**Encoding.** UTF-8, no BOM, Unix newlines. Filenames ASCII kebab-case.
Paths in the YAML are relative to the folder root and stay inside it
(`sections/01-….md`, never `../` or absolute paths).

**Never return**

- A formatted Word file
- The compiler JSON from `doc-formatter parse`
- One giant `.md` with all chapters
- Files named with chapter prefixes or decimal numbers in the filename
- `references.bib` (not accepted yet)
- Manifest keys the loader rejects (`bibliography`, `citation_style`,
  nonempty `backmatter`, `cover`, `toc`, …)

---

## 3. Manifest (`document.yaml`) — accepted now

```yaml
schema_version: 1
profile: <profile-id-from-playbook>
language: es-PE
meta:
  title: "…"
  keywords_es: [tema, otro]
  keywords_en: [topic, other]
frontmatter:
  - abstract_es: sections/00-resumen.md
  - abstract_en: sections/00-abstract.md
body:
  - sections/01-….md
backmatter: []
```

Optional authored frontmatter slots **before** the abstracts if those files
exist:

```yaml
frontmatter:
  - dedication: sections/00-dedicatoria.md
  - acknowledgements: sections/00-agradecimientos.md
  - abstract_es: sections/00-resumen.md
  - abstract_en: sections/00-abstract.md
  - introduction: sections/00-introduccion.md
```

| Key | Rule |
|---|---|
| `schema_version` | Integer `1` |
| `profile` | Nonempty string. Must equal the profile file `id` when building with `--profile` |
| `language` | Nonempty |
| `meta` | Mapping. Keywords are YAML lists, not a prose line |
| `frontmatter` | List of single-key maps `{slot: path.md}` |
| `body` | Nonempty list of Markdown paths; each file becomes a **numbered chapter** |
| `backmatter` | Only `[]` |

**Authored slots (files you write):** `abstract_es`, `abstract_en`,
`dedication`, `acknowledgements`, `introduction`.

**Do not declare** (the build fails): `cover`, `toc`, `list_of_tables`,
`list_of_figures`, `list_of_annexes`, `bibliography`, `citation_style`,
any nonempty `backmatter`, unknown keys, the same path twice.

Which slots and chapter `#` titles are **required** comes from the playbook /
profile schema — not from this dialect file.

---

## 4. Markdown — accepted now

Each file: **exactly one** `#`. Deeper headings are `##` … `#####` when the
profile allows depth 5. Heading titles are plain text — no bold, math, or
links in the heading line.

| Construct | Write this | Do not write |
|---|---|---|
| Section / chapter title | `# Title without prefix` | `# Capítulo I. …` / `# 1 Title` |
| Subsection | `## Generalidades` | `## 1.1 Generalidades` |
| Sub-subsection | `### Problema general` | Jump from `#` to `###` |
| Level 4 | `#### …` then a paragraph | Hand-typed `#### 2.1.5.2 …`. From level 4 the profile may **run in** the next paragraph |
| Level 5 | `##### …` then a paragraph | Same run-in rule as level 4 |
| Bullet list | `- **Label:** …` | Nested lists or `1. …` ordered lists |
| Paragraph | Blank line between paragraphs | Hard line breaks to fake hanging indents |
| Bold / italic | `**…**` / `*…*` | Word styles, ALL CAPS for emphasis |
| Link | `[texto](https://example.com)` | Bare HTML `<a>` |
| Inline math | `$x_i^2$` on one line | `$` spanning two lines |
| Currency / literal dollar | `\$169` / `328.82 \$/m` | `$169` (starts math) |
| Numbered equation | see below | `(1)` beside the math |
| Unnumbered display | `$$` / LaTeX / `$$` | A numbered `:::equation` for decorative identities |
| Cross-ref | `@eq:…` / `@sec:…` / `@tbl:…` / `@fig:…` | Hand-typed `Figura 1` as the only pointer when you have an id |
| Stable section id | `# Título {#sec:mi-slug}` | Spaces or accents in the id |
| Numbered table | see below | Hand-written `Tabla 1` / bare pipe table |
| Numbered figure | see below | Hand-written `Figura 1` / bare `![…](…)` |

Numbered equation — `{#eq:…}` uses letters, digits, `_`, `-` (must start with
a letter or digit):

```markdown
La media muestral es @eq:promedio.

:::equation {#eq:promedio}
\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i
:::
```

Unnumbered display (does not consume the equation sequence):

```markdown
$$
a^2 + b^2 = c^2
$$
```

Numbered table — metadata, then `---`, then a pipe table. Do not write
`Tabla N` yourself. Put the source note in `note` without a `Nota:` prefix
(the profile adds that label):

```markdown
Como se observa en @tbl:ejemplo.

:::table {#tbl:ejemplo}
title: Título de la tabla.
note: fuente …
---
| Columna A | Columna B |
|-----------|-----------|
| 1 | 2 |
:::
```

Inline math inside cells becomes editable OMML (same as body math).

Numbered figure — put the image under `assets/` inside the DocSource folder.
`width` is relative only (`60%`, `100%`, or `natural`):

```markdown
:::figure {#fig:ejemplo}
src: assets/ejemplo.png
title: Título de la figura.
note: Fuente …
width: 60%
:::
```

Heading ids default to `sec:` + slug of the title (and parent slugs). Accented
titles become ASCII. Set `{#sec:…}` only when another file must link to this
heading.

### Rejected today (build fails — do not emit)

Bare `![alt](file)` images, bare pipe tables (without `:::table`), ordered
lists, nested lists, code fences, raw HTML, `:::wide`, `:::raw`, `[@citekey]`,
bare `@autor2020` that is not `eq|sec|tbl|fig`.

Narrative citations in prose are tolerated: `(Vidal, 2020)`. They are not the
final citation form. Do not invent a `.bib`.

---

## 5. Hard rules (any profile)

1. **Never hand-number** headings, equations, figures or tables.
2. **Never write** fonts, sizes, margins, page breaks, or Word style names.
3. **Never write** a table of contents or an index.
4. One `#` per file. Content cannot appear before that heading.
5. Do not skip heading levels.
6. Do not put keyword label lines in abstract files — put values in `meta`.

The profile adds chapter prefixes, decimal heading numbers, equation labels,
caption labels, and keyword lines.

---

## 6. What to do with constructs the build rejects

Do **not** drop them silently and do **not** fake future syntax from
[docs/03](../docs/03-authoring-format.md).

| In the source | In the `.md` you list | In `CONVERSION-NOTES.md` |
|---|---|---|
| Figure / photo | `:::figure` + file under `assets/` | — |
| Cover, TOC, lists of figures/tables | omit | “Discarded; engine will generate” |
| Table | `:::table` with pipe body | — |
| Bullet / numbered list | bullet `-` OK; ordered/`1.` omit | original ordered items if any |
| Bibliography | omit | “parked; citations stay narrative `(Autor, año)`” |
| Annex | omit from the manifest | filename you would have used |
| Equation already numbered `(17)` | LaTeX in `:::equation {#eq:…}` **without** the `(17)` | old number → new id if remapped |
| Keyword lines after abstracts | omit | values must already be in `meta` |

`CONVERSION-NOTES.md` is operator documentation. Do not put a `#` chapter
heading in it. Do not list it in `document.yaml`.

---

## 7. Dialect self-check

- [ ] Folder contains `document.yaml` and every path it names exists.
- [ ] Every listed `.md` starts with one `#` and has no second `#`.
- [ ] No hand-numbered heading / caption text in titles.
- [ ] No keyword label lines in abstract Markdown.
- [ ] Keyword values are lists in `meta` when present in the source.
- [ ] Every `$` that means money is `\$`.
- [ ] Every numbered display equation uses `:::equation {#eq:id}` and every
      `@eq:` / `@sec:` / `@tbl:` / `@fig:` you wrote resolves.
- [ ] No bare images, bare pipe tables, ordered/nested lists, code fences,
      HTML, or `[@cite]`.
- [ ] Every `:::table` has `{#tbl:…}`, a `title`, and a pipe table after `---`.
- [ ] Every `:::figure` has `{#fig:…}`, `src` under `assets/`, and a `title`.
- [ ] `backmatter: []`. No `cover` / `toc` / `bibliography` keys.
- [ ] You did not change scientific claims, numbers, or author names.

Playbook-specific checks (required chapter titles, parked files) are in the
playbook.

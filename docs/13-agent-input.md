# 13 — Agent input (pointer)

**The agent brief is no longer this file alone.**

Give a content agent:

1. [`dialect/docsource.md`](../dialect/docsource.md) — shared DocSource dialect
   (what Markdown/YAML the engine accepts today)
2. A playbook — for UNI FIGMM theses:
   [`playbooks/uni-figmm-thesis/PLAYBOOK.md`](../playbooks/uni-figmm-thesis/PLAYBOOK.md)
3. The source document (Word, PDF, Markdown, or pasted text)

The agent returns a `DocSource` folder (`document.yaml` + `sections/*.md`).
The operator builds with:

```sh
doc-formatter build PATH/TO/DocSource \
  --profile profiles/uni-figmm/thesis@1.yaml \
  --output out/build-name
```

| Layer | Location | Audience |
|---|---|---|
| Dialect | `dialect/` | Any content agent |
| Playbook | `playbooks/<kind>/` | Agents for one institution / document kind |
| Profile YAML | `profiles/` | Engine formatting only |
| Design docs | `docs/01`–`12` | Maintainers — not the agent brief |

Keep dialect + playbook accurate when the parser, manifest, profile schema,
fixture shape, handoff, or conversion procedure changes. See the
`docsource-sync` skill. Thesis-writer-agent copies are updated in a later
sync pass — do not invent dialect there that dialect/playbook do not list.

Design essay (long-term target): [03 — Authoring Format](03-authoring-format.md).
Working example:
[`fixtures/uni-figmm-text-math/source`](../fixtures/uni-figmm-text-math/source).

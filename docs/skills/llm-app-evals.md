# LLM App Evals

> Evals for prompts, RAG and agents, with honest confidence intervals.

**Category:** AI apps · **Skill folder:** [`skills/llm-app-evals/`](../../skills/llm-app-evals/) · **Instructions:** [`SKILL.md`](../../skills/llm-app-evals/SKILL.md)

## The problem it solves

Without evals, prompt changes are vibes. LLM judges show position, verbosity and self-preference biases (MT-Bench, NeurIPS 2023), and small eval sets carry wide error bars.

## When it activates

- "Is this prompt better?"
- Evaluating a chatbot, RAG pipeline or agent
- Comparing models or prompt versions; LLM-as-a-judge setup

You can also call it directly: `/llm-app-evals` (Claude Code, Antigravity) or `/devforge:llm-app-evals` when installed as a Claude Code plugin.

## How it works

1. Read real outputs first and list failure modes
2. Build a tagged case file covering common paths, failures and edge cases
3. Choose the cheapest reliable binary check per case
4. Calibrate any LLM judge against human labels
5. Run with repeats; compare versions with Wilson intervals
6. Validate the eval with a deliberately broken version

## Bundled tools

| File | Usage | What it does |
|---|---|---|
| [`scripts/eval_harness.py`](../../skills/llm-app-evals/scripts/eval_harness.py) | `python3 scripts/eval_harness.py run --cases cases.jsonl --target app:answer --repeats 3` · `compare a.jsonl b.jsonl` · `demo` | contains / not_contains / equals / regex / json_keys / max_chars / judge checks; per-tag breakdown; flaky-case detection; regression list |

## What you get back

Pass rates with 95% intervals per version, regressions, judge agreement and unstable cases.

## Try it

```text
set up an eval for my support bot so i can tell if prompt changes help
v2 scores higher than v1 on 12 cases, so its better right?
```

More test prompts with graders: [`skills/llm-app-evals/evals/`](../../skills/llm-app-evals/evals/).

## Research basis

- Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* (NeurIPS 2023)

---

[← All skills](../../README.md#whats-inside) · [← writing-commits-and-prs](writing-commits-and-prs.md) · [prompt-injection-defense →](prompt-injection-defense.md)

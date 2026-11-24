# Research basis

DevForge's structure and each skill's procedure are grounded in published work. This page
maps findings to design decisions so you can judge (and challenge) them.

## How skills are built

| Finding | Source | What DevForge does |
|---|---|---|
| Curated skills raised average pass rate by 16.2 points across 84 tasks and 7 agent-model setups; self-generated skills gave no reliable benefit | Li et al., *SkillsBench* (2026), arXiv:2602.12670 | Every skill encodes an established engineering procedure, not "what the model already knows" |
| Focused skills (2-3 modules) beat comprehensive documentation, which was net negative | SkillsBench | One job per skill; core procedure in SKILL.md, detail in `references/` |
| Skills mostly reduce verification failures | SkillsBench | Every workflow ends with an explicit validation step, usually backed by a script |
| Agents often fail to load relevant skills, and gains shrink with distractors and large pools | Liu et al., *How Well Do Agentic Skills Work in the Wild* (2026), arXiv:2604.04323 | Descriptions state what, when and trigger keywords; skills have non-overlapping scopes and "not for" boundaries |
| >99% of 238 real SKILL.md files contain at least one "smell" (no guard against skipped steps 94%, buried gotchas 81%, no plan 78%, never asks human 77%, no progress tracking 71%...) | Hong, Imani, Ahmed, *From Anatomy to Smells* (2026), arXiv:2607.01456 | Shared template (checklist, decision table, ask-the-user points, output template, example, `## Gotchas`) and a linter (`validate_skill.py`) that detects these smells |
| 26.1% of community skills contain a vulnerability; confirmed malicious skills exist in public registries | Liu et al., *Agent Skills in the Wild* (2026), arXiv:2601.10338; Liu et al., *Malicious Agent Skills in the Wild* (2026), arXiv:2602.06547 | CI lints for hidden Unicode, download-to-shell, credential access and env exfiltration; scripts are stdlib-only and offline except one registry lookup |
| Skill files are an effective prompt-injection vector against Claude Code, Gemini CLI and Codex | Schmotz et al., *Skill-Inject* (2026), arXiv:2602.20156 | No instructions that override user intent; README asks users to review skills before installing |
| Agent Skills specification: name/description constraints, progressive disclosure, <500-line SKILL.md | agentskills.io specification | Enforced by `validate_skill.py` |

## Per-skill grounding

| Skill | Key sources |
|---|---|
| codebase-onboarding | Fault localization dominates agent repair success: Yang et al., *SWE-agent* (NeurIPS 2024); Xia et al., *Agentless* (2024) |
| reviewing-code-changes | Bacchelli & Bird, *Expectations, Outcomes, and Challenges of Modern Code Review* (ICSE 2013); Sadowski et al., *Modern Code Review: A Case Study at Google* (ICSE-SEIP 2018) |
| secure-code-review | Ullah et al., *LLMs Cannot Reliably Identify and Reason About Security Vulnerabilities (Yet?)* (IEEE S&P 2024): high false-positive rates, so findings require traced flows; OWASP Top 10 (2021); MITRE CWE |
| test-generation | Alshahwan et al., *Automated Unit Test Improvement using Large Language Models at Meta* (FSE 2024): build / pass / coverage filters (75% built, 57% passed reliably, 25% raised coverage); mutation testing as an adequacy check |
| bug-reproduction | Zeller & Hildebrandt, *Simplifying and Isolating Failure-Inducing Input* (IEEE TSE 2002): ddmin; `git bisect` |
| safe-refactoring | Fowler, *Refactoring* (2nd ed., 2018); Feathers, *Working Effectively with Legacy Code* (2004): characterization tests; Mikado method |
| performance-profiling | Mytkowicz et al., *Producing Wrong Data Without Doing Anything Obviously Wrong!* (ASPLOS 2009): measurement bias; bootstrap confidence intervals for A/B benchmarks |
| dependency-audit | Spracklen et al., *We Have a Package for You!* (USENIX Security 2025): 19.7% of packages in LLM-generated code were hallucinated (5.2% commercial, 21.7% open models), enabling "slopsquatting"; OSV database |
| writing-commits-and-prs | Conventional Commits 1.0.0 specification; Semantic Versioning 2.0.0 |
| llm-app-evals | Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* (NeurIPS 2023): position, verbosity and self-enhancement biases; Wilson score intervals for small-sample pass rates |
| prompt-injection-defense | Greshake et al., *Not What You've Signed Up For* (AISec 2023); Beurer-Kellner et al., *Design Patterns for Securing LLM Agents against Prompt Injections* (2025), arXiv:2506.08837; Debenedetti et al., *Defeating Prompt Injections by Design* (CaMeL, 2025); Hines et al., *Spotlighting* (2024); Willison's dual-LLM pattern and "lethal trifecta" |
| session-handoff | Hong, Troynikov, Huber, *Context Rot* (Chroma technical report, 2025): reliability falls as input length grows in all 18 models tested |
| skill-authoring | All of the "How skills are built" sources above |

## What we measured ourselves
Each skill ships `evals/` cases (realistic prompts + graders). Run them with
`claude plugin eval skills/<name>` or the skill-creator workflow to compare
with-skill and without-skill behavior on your own models. Results depend on the model and
harness; the SkillsBench and in-the-wild papers both show large variance across them.

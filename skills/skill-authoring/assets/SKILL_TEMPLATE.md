---
name: {{name}}
description: {{description}}
license: MIT
metadata:
  version: "0.1.0"
---

# {{title}}

One or two sentences: what this skill produces and why the agent should follow it
instead of improvising. Name the failure it prevents.

## When to use

- The situations that should trigger this skill.
- **Not for:** the near-miss situations another skill or plain prompting handles better.

## Workflow

Copy this checklist into your task list and tick items off as you go:

- [ ] 1. Gather context: what to read or run first.
- [ ] 2. Plan: decide the approach (see the decision table) before changing anything.
- [ ] 3. Do the work: the core procedure, as goals rather than a rigid command list.
- [ ] 4. Validate: run the check that proves the output is right.
- [ ] 5. Report: deliver the output in the template below.

### Choosing an approach

| Situation | Do this |
|---|---|
| Common case | Default approach |
| Edge case | Alternative, and why |

Stop and ask the user before anything destructive, irreversible, or outside the request.

## Output template

```markdown
## Result
...
```

## Example

**Input:** a short, realistic request.
**Output:** what a good answer looks like, abbreviated.

## Gotchas

- The mistake agents most often make here, and how to avoid it.

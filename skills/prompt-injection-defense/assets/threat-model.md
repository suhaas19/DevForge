# Threat model: <system name>

## Components
| Step / agent | Model | Reads (inputs) | Can do (tools, side effects) | Sees (sensitive data) |
|---|---|---|---|---|
| | | | | |

Mark each input as **trusted** (developer-controlled), **user** (the authenticated user), or **untrusted** (third parties: web, email, uploaded files, tickets, other tenants, tool output from external systems).

## Trifecta check
| Step | Untrusted input? | Private data? | Exfiltration channel? | Risk |
|---|---|---|---|---|
| | | | | |

Exfiltration channels include: outbound HTTP, email/messages, writes to shared storage or repos, rendered links or images, tool arguments that reach third parties.

## Abuse scenarios
1. Attacker controls: ... → injects: ... → agent does: ... → impact: ...

## Mitigations
| Scenario | Structural mitigation (pattern) | Layered controls | Owner | Status |
|---|---|---|---|---|
| | | | | |

## Tests
- Injection cases added to the eval suite: `evals/...`
- Attack success rate before / after: ... / ...

## Residual risk and decisions
- Accepted risks, with who accepted them and when to revisit.

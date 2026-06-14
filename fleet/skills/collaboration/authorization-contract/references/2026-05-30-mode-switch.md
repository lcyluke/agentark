# 2026-05-30 Mode Switch Practice

## The Dual-Mode Reality

The authorization-contract (SKILL.md) defines 4 modes, but Hermes Agent has its OWN approval system (`approvals.mode` in `config.yaml`). These are **independent layers**:

- **Contract (SKILL.md)**: defines what the agent SHOULD do for each mode level
- **Hermes approvals (config.yaml)**: defines actual tool-call enforcement behavior

The contract is honored by the agent's reasoning. Hermes approvals are enforced by the runtime.

## Optimal Configuration Found

```
Contract mode: 🟢 open (most operations auto-approved)
Hermes approvals: 🔵 smart (dangerous ops prompt, routine ops auto-pass)
Combined effect: everything auto-passes EXCEPT system commands, deletions, logins
```

## How to Switch

- `/mode open` in WeChat → sets contract mode in SKILL.md
- `hermes config set approvals.mode smart` → changes Hermes runtime enforcement
- To go fully unattended: both `open` + `approvals.mode: off`
- Recommended for production: `open` contract + `smart` approvals (safety net without friction)

## Security Passphrase

密语"阿宝/abao" was set by Luke on 2026-05-30. It is checked manually by the agent — not by the runtime. The agent looks for "阿宝" or "abao" in user's text before executing Level-C operations. This is a reasoning-level check, not a system-level enforcement. Therefore it's advisory — the agent must remember to enforce it.

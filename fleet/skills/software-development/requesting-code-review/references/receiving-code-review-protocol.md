# Receiving Code Review Protocol

Companion to the `requesting-code-review` skill. Covers the *other side* of
every review exchange: how to handle feedback when YOU are the recipient.

**New dedicated skill available:** `receiving-code-review` at
`~/.hermes/skills/dev-superpowers/receiving-code-review/SKILL.md` — 154-line
Hermes skill with full Red Flags table (12 rows), Common Rationalizations
(10 rows), and example dialogs. This reference doc is a quick summary; load
the skill for the complete protocol.

## The Protocol: Understand → Verify → Respond

### Step 1: Understand First

Read the full feedback before responding. Ask yourself:
- What exactly is the reviewer asking for?
- What problem do they think exists?
- Is it a correctness issue, a style preference, or a design concern?

Do NOT start forming a response while still reading. Read all the way through.

### Step 2: Verify Technically

Is the reviewer's claim technically correct? Test it if needed:

- If they say "this input causes an exception" — run it and check
- If they say "this logic is wrong" — trace through the code path
- If they say "there's a better approach" — does the suggested approach solve the problem?

Verification is not optional. Blind implementation of a wrong suggestion produces bad code. Blind dismissal of a correct suggestion misses a real bug.

### Step 3: Choose Your Response

| Situation | Response | What to Say |
|-----------|----------|-------------|
| Review is correct | Accept and implement with full rigor | "Good catch. Fixing with [specific approach]." |
| Review is partially correct | Negotiate with alternative | "The concern about X is valid. Instead of [suggestion], how about [alternative] because [reason]?" |
| Review is incorrect | Push back with evidence | "I considered that. Here's why [evidence] shows this is the right approach: [specific proof]." |

## Red Flags

| Cognitive Trap | Remedy |
|----------------|--------|
| "Reviewer said it, must be right" | Verify every claim independently |
| "I'll just agree and move on" | Don't implement what you don't understand |
| "Don't want to argue" | Evidence-based push back is professional, not confrontational |
| "This is just a style preference" | Style preferences from the code owner matter — but verify first |
| "They're reviewing my code, so I should do what they say" | Review is a conversation, not a directive |
| "If I push back, they'll think I'm difficult" | Competent reviewers want you to push back when you're right |
| "I'll change it now and undo it later" | Later never comes. Push back or fix properly. |
| "The reviewer must know better, they're senior" | Senior people make mistakes too. Verify equals. |
| "I already spent too long on this" | Sunk cost — fix the root issue, not the symptom |
| "Just this one time I'll implement without understanding" | One time = every time. Make understanding non-negotiable. |

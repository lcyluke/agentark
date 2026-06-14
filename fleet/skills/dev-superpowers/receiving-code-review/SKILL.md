---
name: receiving-code-review
description: "Use when receiving code review feedback, before implementing suggestions. Requires technical rigor and verification, not performative agreement or blind implementation."
version: 1.0.0
author: Origin Agent
---

# receiving-code-review

## Overview

Code review feedback is valuable but must be verified, not blindly accepted. Reviewers are fallible — they may misread the code, lack full context, operate on outdated assumptions, or simply be wrong. At the same time, the author (you) is the person most familiar with the code and its surrounding constraints. This skill provides a structured process for engaging with review feedback that maintains technical integrity, preserves learning, and avoids the traps of deference fatigue or ego-driven rejection.

## Core Principle

**Never implement a review suggestion without understanding and verifying it first.**

Implementation without verification is cargo-culting. Agreement without understanding wastes the learning opportunity for both author and reviewer. The goal of code review is to produce better code and shared understanding — not to minimize back-and-forth or to make the reviewer feel heard.

## The Process

### Step 1: Read and understand
Read the feedback as if it were about someone else's code. Ask yourself:
- What exactly is the reviewer asking me to change?
- Why are they asking this? What problem do they see?
- What assumption are they making about the code, the context, or the constraints?
- Do I fully understand their proposed alternative? If not, ask clarifying questions first.

> Do not proceed to Step 2 until you can articulate the reviewer's concern in your own words.

### Step 2: Verify the feedback
Independently verify the technical claim behind the suggestion:
- Is the reviewer's factual assertion correct? (e.g., "this leaks memory", "this creates an N+1 query")
- Reproduce the concern — write a test, check the docs, run a profile, trace the execution path.
- Does the suggestion actually solve the stated problem? (e.g., does it eliminate the leak? does it reduce the query count?)
- What are the trade-offs of the suggestion? (complexity, readability, performance, consistency with the rest of the codebase)

### Step 3: Accept, push back, or negotiate
Three valid responses. Choose based on evidence, not comfort.

| Response | When to use | How to respond |
|---|---|---|
| **Accept** | The reviewer is correct and the suggestion improves the code. | "Good catch. I'll update this and push a fix." |
| **Push back** | The reviewer is incorrect, or the suggestion introduces new problems. | Provide technical evidence. Cite specific lines, benchmarks, docs, or invariants. |
| **Negotiate** | The reviewer has a valid point but the suggestion isn't ideal. Propose something better. | "I see the concern about X. Instead of Y, what if we do Z? It handles the same issue but avoids the regression in W." |

### Step 4: If accepting — implement with rigor
Treat the accepted suggestion like any other code change:
- Write or update tests.
- Check for edge cases the reviewer may not have thought of.
- Ensure consistency with surrounding code patterns.
- Push as a clean commit (squash fixups if appropriate; consider a separate commit for non-trivial review changes).

### Step 5: If pushing back — provide technical evidence, not opinion
- Quote the relevant lines, documentation, or test output.
- Show the trade-off explicitly ("Yes, this adds a conditional, but it avoids a 200ms network call on every page load").
- Be specific about what the reviewer may be missing (constraints, requirements, existing patterns).
- Keep the tone professional: "I considered that approach but chose this one because [evidence]."

## Red Flags

Watch for these warning signs that you are skipping the verification process:

| # | Red Flag | Danger |
|---|---|---|
| 1 | "Reviewer said it, so it must be right" | Surrendering critical thinking to authority. Reviewers are peers, not oracles. |
| 2 | "I'll just agree and move on" | Accumulating technical debt and training the reviewer to stop noticing issues. |
| 3 | "I don't want to argue" | Letting social discomfort override code quality. Healthy pushback is part of engineering culture. |
| 4 | "I've already spent too long on this PR" | Time pressure is not a technical argument. If the feedback is correct, take the time to fix it properly. |
| 5 | "They're a senior engineer, they must know better" | Seniority is not a substitute for evidence. Even the best engineers make mistakes. |
| 6 | "I'll fix it in a follow-up PR" | The standard response when you don't want to do it right now. If it's worth fixing, fix it now. |
| 7 | "This is just a nitpick" | Dismissing feedback as trivial without checking if the reviewer is pointing at a wider pattern or a readability issue. |
| 8 | "The reviewer didn't fully read my code" | Frustration at perceived lack of context. Instead, provide the missing context rather than dismissing the feedback. |
| 9 | "I don't understand the suggestion, but I'll implement it anyway" | You cannot correctly implement something you don't understand. Ask for clarification first. |
| 10 | "I'll just change it and see if the tests pass" | Treating code review suggestions as blind mutations rather than reasoned changes. Test-only validation misses design issues. |
| 11 | "But I tested it and it works" | Past testing does not guarantee the reviewer's concern is invalid. Re-examine through their lens. |
| 12 | "This is how we've always done it" | Not a valid defense against a well-reasoned suggestion. Patterns should evolve. |

## Common Rationalizations

These are the mental shortcuts we use to avoid the hard work of verification:

| # | Rationalization | Reality |
|---|---|---|
| 1 | "It's just a style preference" | Style preferences can affect readability, consistency, and maintainability. Evaluate the substance, not the category. |
| 2 | "The tests pass, so it's fine" | Tests only cover what you wrote, not what you missed. Reviewer concerns often point to untested paths. |
| 3 | "This is production code, I have to be careful" | Being careful means verifying, not avoiding change. Defaulting to "no change" is risk-averse but not always correct. |
| 4 | "The reviewer didn't understand the context" | This may be true, but it's also possible the code didn't communicate the context well enough. Consider improving documentation or naming. |
| 5 | "We don't have time for perfect" | Perfection is not the goal. Correctness and clarity are. A 30-second fix that prevents a production bug is time well spent. |
| 6 | "I'll address it if it comes up again" | It will come up again — in code review, in a bug report, or in production. Fix it now. |
| 7 | "The suggestion introduces other issues" | Then negotiate. Don't let perfect be the enemy of good. Propose the better alternative rather than rejecting outright. |
| 8 | "I wrote this carefully, I know it's right" | Confidence is not correctness. Even carefully written code has blind spots. Use the review as a second set of eyes, not a validation ceremony. |
| 9 | "I'll just explain it in the PR description" | If the explanation belongs in code, put it in code. Comments, variable names, and structure should be self-documenting. |
| 10 | "They always make this type of comment" | Pattern-based fatigue is real, but each comment should still be evaluated on its merits. A repetitive reviewer may be pointing at a real friction point. |

## Example Dialogs

### Good vs Bad: Handling a correctness concern

**Reviewer**: "This reducer mutates state. Line 47: `state.items.push(newItem)`. Redux state must be immutable."

**Bad response** (blind acceptance):
> "Oh sorry, I'll fix that." *Throws `...state` everywhere without checking if the concern actually applies.*

**Bad response** (defensive rejection):
> "It works fine in my tests and pushing to an array is faster. Adding immutability is premature optimization."

**Good response** (verification first, then negotiation):
> "Good catch on the mutation. I verified that Redux's combineReducers does check for mutation in development mode — let me confirm by running in strict mode. ... Confirmed, it throws an error with the current code. Two options: (a) use `[...state.items, newItem]` to be idiomatic, or (b) use Immer's `produce` since we already have it as a dependency. I'll go with (b) since it's consistent with the other reducers in this file. Pushing a fix now."

---

### Good vs Bad: Handling a design suggestion

**Reviewer**: "Instead of an if-else chain, could we use a strategy pattern here? It would be more extensible."

**Bad response** (blind acceptance):
> "Sure, I'll refactor it." *Spends 3 hours building a strategy pattern with an abstract base class, a registry, and dynamic dispatch — for what was a 10-line decision chain with 3 branches.*

**Bad response** (dismissive):
> "A strategy pattern is overkill for this. The if-else is clear enough."

**Good response** (verified evaluation of trade-offs):
> "I see the extensibility concern. Currently we have 3 branches and haven't added a new one in 6 months. I checked git history and the related feature module — the branching conditions are tied to API versions that change predictably. A strategy pattern would add ~60 lines of boilerplate and a new indirection layer. How about we keep the if-else for now but extract the body of each branch into a named function? That makes adding a new case a single `else if` call away without the ceremony. If we hit 5+ branches, we refactor to a registry pattern. Does that work?"

---

### Good vs Bad: Handling a performance concern

**Reviewer**: "This API call inside the render loop will fire on every keystroke. You should debounce it."

**Bad response** (blind implementation):
> "Okay, adding debounce." *Throws a 500ms debounce on the input without considering the user experience or the specific use case.*

**Bad response** (terse pushback):
> "It's a search-as-you-type field, debouncing would make it feel slow."

**Good response** (verify, then negotiate with evidence):
> "I checked — you're right that it fires on every keystroke. I profiled it: each call takes ~80ms and the user types ~5 chars/second, so we're making 5 unnecessary calls for every useful one. However, a fixed debounce makes auto-complete feel sluggish. I tested two alternatives: (a) 150ms debounce — felt responsive in my manual testing, reduces calls by ~60%; (b) `useTransition` with a stale-while-revalidate pattern — more complex but no perceivable delay. I'll go with (a) since it's simpler and the latency profile is acceptable. Let me know if you strongly prefer (b)."

---

### Good vs Bad: Handling a "I don't understand" comment

**Reviewer**: "What does this variable `z` represent? The naming is unclear."

**Bad response** (silent fix without explanation):
> *Renames `z` to `data` without further thought.*

**Bad response** (defensive):
> "It's obvious from the context, it's the z-score normalized value."

**Good response** (verify and improve):
> "Fair point. `z` is the z-score of the confidence interval. I renamed it to `zScore` for clarity and added a comment explaining the formula on line 15 since there's a stat-specific calculation there that isn't obvious. Pushed in commit abc123."

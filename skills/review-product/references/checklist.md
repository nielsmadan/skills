# Product Review Reference

Templates and lenses for reviewing a product from the user's perspective. Load
when building the persona, mapping use cases, or auditing friction and gaps.

---

## Persona template (`docs/product/persona.md`)

Keep it evidence-based: derive every claim from the codebase, the product
description, or explicit user input — never invent demographics. If the product
serves multiple distinct users, write one section per persona and mark the
**primary** one.

```markdown
# User Persona(s)

> Last refined: YYYY-MM-DD · Sources: <code paths / docs / user input>

## <Persona name> (primary)
- **Who they are**: role, context, technical level
- **Why they're here**: the top-level goal that brings them to the product
- **Environment**: device, setting, time pressure, frequency of use
- **What they value**: speed / control / trust / simplicity / depth (rank them)
- **Constraints & frustrations**: what makes their job hard today
- **Success looks like**: how they judge whether the product served them

## <Secondary persona> (if any)
...
```

Refining rule: on later reviews, **edit** the existing file — adjust claims that
new evidence contradicts, add personas that emerged, and bump `Last refined`.
Don't silently discard prior content; note what changed and why.

---

## Use-cases / jobs-to-be-done template (`docs/product/use-cases.md`)

A use case is a *job the persona is trying to get done*, phrased from their point
of view — not a feature list. Order by how central each is to the persona's goal.

```markdown
# Use Cases (Jobs-to-be-done)

> Last refined: YYYY-MM-DD · Persona: see persona.md

## UC1 — <When ___, I want to ___, so I can ___> (primary)
- **Trigger**: what prompts the user to start
- **Path today**: the steps the product currently requires (cite screens/routes)
- **Definition of done**: what state means the job succeeded
- **Frequency / stakes**: how often, how costly to get wrong

## UC2 — ...
```

Each use case becomes a lens for the friction audit below: walk it end-to-end and
ask "could *this* persona actually complete *this* job without confusion, dead
ends, or unmet needs?"

---

## Friction & gap lenses

Walk every primary use case through the product, then evaluate against these
lenses. The first is the most important for a *product* (vs purely visual) review.

### A. Job coverage (does the product do the job at all?)
- Can the persona complete each use case end-to-end? Where does the path break?
- Missing steps, dead ends, or states the product can't represent
- Jobs the persona clearly has that the product simply doesn't support → **gaps to add**
- Steps that exist but the user shouldn't have to do → **friction to remove**

### B. Friction (Nielsen's usability heuristics, applied to flows)
1. **Visibility of status** — is the user told what's happening? loading, progress, confirmation
2. **Match to the real world** — language and concepts match the user's mental model, not the code's
3. **User control & freedom** — undo, cancel, back-out of mistakes, leave without penalty
4. **Consistency & standards** — same action looks/behaves the same everywhere
5. **Error prevention** — the design stops mistakes before they happen
6. **Recognition over recall** — options are visible/discoverable, not memorized
7. **Flexibility & efficiency** — shortcuts and accelerators for repeat/power users
8. **Minimalist** — signal vs noise; what competes for attention with the main job
9. **Error recovery** — messages are plain-language, specific, and tell the user how to fix it
10. **Help & docs** — guidance is available at the point of need

### C. Onboarding & first run
- Time-to-first-value: how long until a new user gets something useful?
- Empty states: do they teach, or just show "nothing here"?
- Setup/permission/config friction before the user can start

### D. Trust & safety
- Are destructive or irreversible actions confirmed and reversible?
- Is it clear what happens to the user's data / what the product will do next?
- Does the product over-promise, surprise, or hide important consequences?

### E. Opportunities (add / change)
- What would most reduce friction on the primary use case?
- What unmet need, if served, would most help this persona?
- What could be removed entirely to simplify?

---

## Severity tiers

Rate every finding by its impact **on the user accomplishing their job**:

- **Critical** — blocks a primary use case; the persona cannot complete a core job
- **High** — significant friction; needs a workaround, risks abandonment
- **Medium** — slows or annoys the user but the job still completes
- **Suggestion** — polish or nice-to-have with marginal impact

For each recommendation, note rough **effort** (S/M/L) so the user can weigh
impact against cost.

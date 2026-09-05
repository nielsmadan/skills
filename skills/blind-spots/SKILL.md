---
name: blind-spots
description: Surface the decisions a plan or design left silently assumed, by interviewing the user in dependency order until nothing is unstated. Use when the user says "blind spots", "grill me", "stress-test this plan", "poke holes in this", "what am I missing", "interrogate this design", "what haven't I decided", or hands over a loose idea to sharpen before building. Do NOT use to explain a previous reply in more detail (use `huh`), to generate ideas when it is unclear what to build (use `ideation`), or to review an already-written plan with agents (use `review-plan`).
argument-hint: '[plan, design, or idea to probe; blank = take it from the conversation]'
effort: high
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Blind Spots

Find the decisions the user does not know they have left open, then get each one made.

A plan feels complete from the inside because the gaps were filled in silently. Make
them visible before they become code. The deliverable is not the answers — it is the
discovery that the questions existed.

## Instructions

### 1. Resolve the target

The argument is what to probe. If blank, take it from the conversation. If no plan,
design, or idea is in play, ask for one sentence on what they want to build.

### 2. Recon before asking anything

An uninformed question wastes a round and spends the user's patience. Before round one,
read what the repo already answers: the relevant source, `AGENTS.md` / `CLAUDE.md`, any
`docs/` covering the area, and how comparable features are already built here.

**Finding facts is your job, never the user's.** Anything discoverable from the
filesystem, the git history, or a tool is yours to look up. Ask the user only for
*decisions*.

### 3. Build the decision tree, then prune it

Map the work as decisions, each branching into the decisions that hang off it. Pruning
is what separates a useful round from an interrogation:

- **Keep** a decision that *forks the design* — different answers lead to different
  structure, different interfaces, or different work.
- **Drop** a decision that is cheap to reverse and constrains nothing downstream.
  Naming, log wording, which of two equivalent helpers to use: decide those yourself
  while building.

An unspecified detail is not automatically a blind spot. A fork the user cannot see is.

### 4. Ask the frontier

The **frontier** is every kept decision whose prerequisites are already settled — the
questions answerable *now* without guessing at answers you have not heard yet.

Ask the whole frontier in one message, ordered by consequence, then **stop and wait**.

```
❓ **Q1 — <short title>**: <the question, with the options if it is a choice>

➡️ <recommended answer, and the reason in a clause>

---

❓ **Q2 — <short title>**: …

➡️ …
```

Rules for a round:

- **Every question carries your recommendation.** "Go with your defaults" must be a
  complete answer — the user may be tired, or may simply trust you on that branch.
- **A question whose answer depends on another open question belongs to a later
  round**, not this one. This is the whole mechanism: question 12 does not exist as a
  question until question 4 is answered.
- **More than about seven questions means the tree is split too fine.** Re-prune per
  step 3 rather than sending a wall.
- Never block on a lookup. A running exploration is an unsettled prerequisite, so only
  the questions downstream of it wait — ask the rest of the frontier now.
- Where the harness offers a structured choice prompt, use it for the discrete
  either/or questions and prose for the rest.

### 5. Recompute and repeat

Each set of answers settles decisions, pushing the frontier outward and unblocking
questions that depended on them. Recompute the frontier and ask the next round. Expect
two to four rounds; a wide design may take more.

### 6. Close

Stop when the frontier is empty: every kept branch visited, nothing left silently
assumed. State the settled understanding back — the decisions and their answers,
compactly, in the user's own terms — and ask the user to confirm it matches what they
meant.

On confirmation, hand off rather than sprawling into implementation: `plan` for a
medium task, `longshot` if they are handing it over and leaving, a heavier planning
workflow for an architectural change. Write the understanding to a file only if asked.

If another workflow invoked this skill, return the settled understanding to that
workflow and stop. Do not hand off yourself.

## Boundaries

- **Do not build during the interrogation.** No edits, no scaffolding, no mutating
  commands, no implementation subagents — not until the user confirms the closing
  summary. Reading and searching are expected.
- Cap parallel lookups at **three read-only subagents**, one question each.
- Do not answer a decision on the user's behalf to shorten the session. Recommend, then
  wait.
- Do not re-ask a decision already settled, in this session or in the docs.

## Examples

### A loose feature idea

`blind-spots add team workspaces` — recon finds single-tenant auth and no authorization
layer. Round 1 asks the four forks that follow: does a user belong to many workspaces,
is existing data migrated or grandfathered, are invites by email or link, does billing
move to the workspace. Round 2 exists only because round 1 answered "many workspaces" —
role model and per-workspace permission checks are now answerable. Round 3 is empty.
The summary lists nine settled decisions, three of which the user had not realized were
open.

### A plan the user already wrote

`blind-spots` after pasting a migration plan — recon reads the current schema, so the
round asks only about forks the plan left implicit (backfill under load, rollback
window, dual-write duration), never about what the plan already states.

## Troubleshooting

### The user answers "you decide" to everything

Take it at face value: record your recommendation as the decision and move on. If it
happens across a whole round, step 3's pruning was too loose — those were not forks.
Tighten it and shorten the next round.

### A question turns out to depend on an answer already given

It belonged to an earlier round and was missed. Drop it, apply the known answer, carry
on. Do not make the user repeat themselves.

### The frontier keeps growing and the session will not end

Each round should narrow. If it widens twice running, the scope is bigger than one
feature — say so, propose splitting it, and probe only the first piece.

### The user says a question is trivia

Believe them and drop it. It failed step 3's fork test.

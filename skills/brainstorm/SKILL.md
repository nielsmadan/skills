---
name: brainstorm
description: Work out how to solve a problem the user can already name — interview them with `blind-spots` to understand it, generate structurally different approaches, validate each with an independent critic, then present the survivors with trade-offs and a recommendation. Use when the user says "brainstorm", "brainstorm approaches", "how should we solve/approach/tackle X", "what are our options", "compare approaches", "think this through with me", or wants solutions weighed before committing. Works on any topic, with codebase recon when a repo is involved; `--debate` adds external advisors for high-stakes calls. Do NOT use when stuck on what to build or what the problem is (use `ideation`), to probe an already-chosen plan (use `blind-spots`), or to pick a library or service (use `evaluate-tech`).
argument-hint: '[problem] [--debate]'
effort: high
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Brainstorm

Find the right way to solve a problem the user can name. Three passes, each putting
judgment somewhere different: **understand** the problem with the user, **diverge** to a
wide set of approaches and cut it to the credible few, then **validate** each survivor
with a critic that never saw the others. You recommend; the user picks.

## Real forks

A choice of approach is a **real fork** when at least two approaches survive the hard
constraints and either differ in something expensive to reverse (data model, external
interface, a new dependency, the overall architecture) or cannot be called with
confidence. It is not one when one approach clearly dominates or the difference is
cheap to change later. Calling workflows use this test to decide whether to invoke
this skill.

## Embedded use

When another workflow invokes this skill on a fork in its own work (`longshot`'s
approach step, or `plan` after the user accepts its offer):

- Skip step 1. The caller's brief and definition of done are the brief; do not
  re-interview.
- Run step 2 with the caller's options among the candidates. If only one credible
  approach survives the cut, there is no fork: say so in one line, with the reason, and
  return it without running critics.
- Run steps 3 and 4 as written; the user picks in step 4.
- Skip step 5. Return the chosen approach, its validation findings and your defaults
  to the caller, which owns planning and every approval gate.

## Instructions

### 1. Understand: run `blind-spots`

Check the request belongs here first:

- Unclear what the problem is, or what to build: say so and switch to `ideation`.
- Choosing a library, tool or service: switch to `evaluate-tech`.
- Everything that matters is in the request and there is one obvious way: say so and
  offer to just do it.

Otherwise invoke `blind-spots` on the problem and run it to completion as an embedded
call, so it returns a brief rather than handing off. Tell it the aim is a settled
problem, not a chosen solution: the alternatives its framing challenge surfaces become
candidates for step 2, and the approach is chosen in step 4. Wait for the user's
answers; never close a round with your own recommendations.

Success: a brief with purpose, who it serves, success criteria, hard and soft
constraints, non-goals, and settled decisions. The critics in step 3 judge against
these criteria, so if success criteria are still vague, get them before moving on.

### 2. Diverge, then cut

Generate 5-8 candidate approaches with judgment off. No two may share a core
mechanism; varying a parameter is not a new approach. Include:

- the alternatives `blind-spots` raised;
- the smallest change or do-nothing option, when it is credible;
- at least one from a breakthrough technique: Crazy 8s, analogical transfer,
  provocation, or TRIZ when a trade-off blocks progress (procedures under
  "Solution-generation methods" in `../ideation/references/frameworks.md`).

In a repo, ground each candidate in what the code does today.

Then cut to the **2-4 credible** ones. Drop any that break a hard constraint, work
against the stated purpose, are ruled out by the existing work, or are dominated by
another candidate. Strip scope the brief does not require from each survivor ("is this
solving the stated problem?"). If only one survives, keep it and validate it anyway;
step 4 explains why the others fell.

Keep the cut list for step 4's "also considered" line. Do not show the raw list yet.

### 3. Validate: independent critics

Dispatch one fresh-context critic subagent per surviving approach, in parallel, using
`references/critic-prompt.md`. Each gets the brief and its own approach only — never the
other approaches, your ranking, or your recommendation, because a critic that can see
your favourite tends to confirm it. Give critics read-only tools and no delegation; in a
repo, name the files the approach touches.

Reconcile what comes back:

- **Fails a hard constraint, no repair:** drop it and move it to "also considered".
- **Fails fixably:** apply the repair. Re-run that critic only if the repair changes
  the mechanism.
- **An unverified fact decides between approaches:** look it up now (`research-tech` or
  `research-general` for anything beyond a quick lookup), or name it as the test.
  Critics disagreeing on a fact is a lookup, not a vote.
- **The riskiest assumption is cheap to test with a throwaway prototype:** offer one.
  Build it only on the user's yes, label it throwaway, and bring what it taught back
  here.

Without a subagent tool, validate each approach in a separate pass yourself, writing its
verdict before reading the next, and say the check was not independent.

**`--debate`:** after the critics, run `second-opinion` with the brief, the surviving
approaches and the critic findings — not your recommendation — and ask each advisor to
pick one and attack the rest. Fold in objections that hold up. Where advisors disagree
with your recommendation, report the disagreement in step 4 rather than smoothing it
over. When the flag is absent but the choice is costly to reverse, suggest it.

### 4. Present the approaches

Put the approaches in a message of their own:

```markdown
**Problem:** <one line from the brief> · **Judged against:** <success criteria, hard constraints>

### A. <name> (recommended)
<how it works in 2-3 lines, grounded in what exists>
- **Trades:** <what it gives up>
- **Validation:** <criteria met / at risk, with the key evidence>
- **Riskiest assumption:** <assumption> → test: <cheapest check>

### B. <name>
...

**Also considered:** <each cut candidate, one clause on why it fell>
**Recommendation:** A, because <reason tied to the brief>.
**Defaults I chose:** <each choice you filled in, so it can be rejected>
```

End by asking which way they want to go. A default they never heard is one they could
not reject, so every choice you made goes in that last line.

### 5. Hand off, for implementation only

Once the user picks:

- **Implementation work:** restate the chosen approach and its settled decisions in a
  few lines, then hand off: `plan` for a medium task, `longshot` if they are handing it
  over. Carry the brief forward so the next skill does not re-interview.
- **Anything else** (a decision, writing, business, personal): the presented approaches
  are the deliverable. Stop there.

Write to a file only when asked.

## Boundaries

- Build nothing before the user picks, apart from a prototype they said yes to.
  Reading, searching and lookups are expected.
- Do not re-ask what `blind-spots` or the docs already settled.
- One critic per approach, four at most. Critics do not delegate.

## Examples

### Example 1: a code problem

User says: "brainstorm how to make search results update live"
Actions: `blind-spots` reads the search code (Postgres full-text, request/response
only) and asks how fresh results must be and at what traffic; the user says "within
30 seconds, low traffic". Diverge to seven candidates (polling, SSE on write, websockets,
`LISTEN/NOTIFY`, a TTL cache, optimistic client updates, a "new results" banner) and cut
to three. The SSE critic finds the nginx config buffers responses (at risk, with
file:line); the polling critic shows 15-second polling with ETags meets the criterion at
current load.
Result: polling recommended with SSE as the upgrade path. The user picks it, and it
goes to `plan` with the brief attached.

### Example 2: a non-code problem

User says: "how should we run the quarterly planning offsite? brainstorm with me"
Actions: `blind-spots` establishes the purpose (agree three priorities), size (12
people) and a hard constraint (one day). Diverge, cut to three formats, critic per
format against "decisions made by end of day".
Result: the approaches message is the deliverable. No handoff.

### Example 3: a high-stakes call

User says: "brainstorm --debate moving auth from server sessions to JWTs"
Actions: as Example 1, then `second-opinion` on the survivors. One advisor argues for
keeping sessions behind a token-exchange edge; the critics had not covered revocation.
Result: the presentation records that disagreement next to the recommendation.

### Example 4: embedded in longshot

`longshot`'s approach step finds that offline sync could use a CRDT library or
last-write-wins with server timestamps, a data-model choice that is expensive to
reverse. It invokes `brainstorm` with the settled brief. Step 2 adds an append-only
operation log, and the critics find that last-write-wins loses edits in the user's
stated two-device case.
Result: the user picks the CRDT approach, and `brainstorm` returns it with the
critic findings. `longshot` drafts its plan around it, with no second interview.

## Troubleshooting

### The approaches are variations of one idea
**Cause:** cut before diverging properly, or skipped the breakthrough technique.
**Solution:** return to step 2 and force the mechanism rule: name each candidate's core
mechanism, and replace any that share one.

### Every critic passes every approach
**Cause:** the brief has no checkable success criteria, or the prompt leaked your
preference.
**Solution:** get concrete criteria from the user, refill the critic prompt from the
template, and re-run.

### `blind-spots` comes back with the solution already chosen
**Cause:** its framing challenge recommended an approach and the user agreed.
**Solution:** if the user explicitly chose it, skip to step 3 and validate that one
approach. Otherwise treat its pick as one candidate in step 2.

### The user says "you pick"
Take it at face value: the recommendation is the decision. Hand off per step 5.

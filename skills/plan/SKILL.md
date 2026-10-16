---
name: plan
description: Lightweight planning workflow — delegate read-only planning to an Opus subagent, then implement in auto mode after a single go-ahead gate, run QA and one `code-review --multi`, fix findings, repeat QA only after substantial code changes, and update docs. The middle tier between "just do it" (tiny tasks) and heavyweight superpowers planning (big features). Never enters plan mode, so it sidesteps the plan-mode permission prompts. Use when the user invokes /plan, or wants a plan for a medium-sized task before implementing.
argument-hint: '[--review] <task, or blank to infer from conversation>'
effort: xhigh
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Plan (middle tier)

Produce a concrete implementation plan for a medium-sized task, then implement it
after one approval gate. Deliberately lighter than `superpowers:brainstorming` /
`writing-plans` (no spec files or per-task implementation checkpoints) and
heavier than just editing — the space where a plan helps but full ceremony is overkill.

**This skill IS the planning workflow for this task.** Do not also invoke
`brainstorming` — that is the heavyweight path this skill exists to avoid.

Two design choices make it work:
- **Never enter plan mode / never call `ExitPlanMode`.** Everything runs in the
  session's normal (auto) mode. This is intentional: it avoids plan mode's read-only
  permission prompts entirely, and a subagent's own tool calls never prompt you.
- **A subagent plans, the main session implements.** A single read-only subagent
  pinned to Opus does the exploring and drafts the plan; the main session implements it.

The argument is the task. If blank, infer the task from the current conversation.

## Usage

```
/plan add a --json flag to the export command    # plan a stated task
/plan                                            # plan the task from context
/plan --review <task>                            # plan, then multi-agent review before the gate
```

## Flags

- `--review` — after the plan is drafted, run `review-plan` (multi-agent) on it and
  fold the findings in before presenting for go-ahead. `review-plan` is already
  multi-agent; there is no separate `--multi`. The final `code-review --multi`
  runs regardless of this flag.

## Instructions

### Step 1: Scope check (early exit)

Judge the task's size first.

- **Trivial** (one-liner, obvious fix, rename, config flip): planning is overhead.
  Say so in one line and offer to just do it directly — do not spend a planning
  round-trip. Respect the user if they still want a plan.
- **Too big** (multi-subsystem, architectural, multi-session): this is above the
  middle tier. Point at `superpowers:brainstorming` and stop.
- **Middle** (a few files, a new endpoint/component, a contained refactor): proceed.

### Step 2: Dispatch the planning agent

Dispatch **one** subagent via the `Agent` tool:
- `subagent_type: Plan` — read-only by construction (no Edit/Write/NotebookEdit).
- `model: opus`.
- `effort: xhigh`.

The `Plan` agent starts **fresh** (it is not a fork),
so brief it fully. Its prompt MUST contain:
- The task statement (from the argument or inferred from the conversation).
- Relevant context from this conversation and pointers to the files/dirs to start from.
- These directives: explore **read-only** — Read/Grep/Glob and read-only shell only,
  run **no** mutating commands; ground every claim in **real file paths / line ranges**
  it actually read; be **concrete — no placeholders** ("TBD", "add error handling").
- The required output skeleton below.

**Required plan skeleton (the agent returns exactly this):**
```
## Approach
2–3 sentences. Name approach A (recommended) vs B in one line, with why.

## Files to touch
- path/to/file — what changes and why

## Ordered steps
1. …

## Risks / edge-cases
- …

## Assumptions & open questions
- Assumption: …
- Open question: … (blocking? y/n)
```

### Step 3: Review (only if `--review`)

Invoke the `review-plan` skill (via the Skill tool) against the plan in current
context. Fold its findings into the plan — apply clear improvements directly, and
surface unresolved disagreements as open questions for the gate.

### Step 4: Present and STOP

Print the plan inline, cleanly formatted, with the **Assumptions & open questions**
called out so the user can resolve them. Include QA, one final multi-agent code review,
fixes, conditional post-review QA, verification, and documentation updates in the plan; the go-ahead covers
these finishing steps too.

**Hard gate:** do NOT begin implementing. Wait for an explicit go-ahead ("go", "yes",
"proceed", or edits). This stop is load-bearing — in auto mode nothing else prevents
you from barreling into implementation.

### Step 5: Implement on go-ahead

Once the user approves, implement the plan directly in the main session (auto mode),
incorporating any answers they gave to the open questions. Do not enter plan mode and
do not re-dispatch implementation to a subagent — the main session does the
implementation and fixes. The QA and review steps below may dispatch their own
workers according to those skills.

### Step 6: QA the implementation

Run `qa --fix` against the completed feature and its affected interfaces. Supply the
approved requirements and acceptance criteria. Fix confirmed defects and retest the
failing paths and affected neighbors before moving on. Follow the QA skill's
coverage and evidence requirements; automated checks alone do not replace runtime
QA when consumer behavior changed.

### Step 7: Review once, fix, and verify

Run `code-review --multi` over the complete task diff, including new files and any
changes already committed during the task. Give it an explicit scope so unrelated
work in the checkout stays outside the review. This is mandatory, even without
`--review`; do not substitute `--quick`. Run exactly one code review: do not pass
`--rereview` or dispatch another review after fixes.

Fix every valid finding, including lower-severity ones, without another approval
round. Record a concrete reason for any finding rejected as incorrect or
inapplicable; do not silently defer valid findings. Run the project's formatter
and relevant checks after fixes. Resolve all valid findings and check failures.
A genuine blocker must be reported explicitly; do not describe blocked work as
complete.

Run a second `qa --fix` only if the changes since the first QA are substantial:
changes to behavior, control flow, state, data handling, interfaces, or integrations
that could invalidate the earlier QA evidence. Judge by impact, not line count.
Scope this pass to affected scenarios and their neighbors, fixing and retesting
confirmed defects. Formatting, comments, naming-only cleanup, and documentation
edits do not trigger another QA pass. State whether repeat QA was needed and why.

### Step 8: Update docs and hand off

Run `doc --update` scoped to the completed task. Update the canonical docs for the
final behavior, interfaces, usage, and constraints; use `doc --generate` where new
behavior needs documentation that does not exist. Carry durable design decisions
from the plan into the appropriate docs. Do not create a separate plan archive.

Check the updated examples and links, and run any required documentation checks.
If documentation work exposes a code defect, return to the fix and verification
steps before finishing, applying the same substantial-change rule for repeat QA
without another code review. Report what changed, QA coverage, review findings
resolved, verification results, docs updated, and any remaining blockers. Do not stop after implementation
with an offer to run review or update docs later.

## Examples

User: "Plan adding a `--json` flag to export."

Actions: one read-only planner drafts the approach → present the plan including
QA, review, and docs → wait for approval → implement in the main session →
`qa --fix` → one `code-review --multi` → fix findings and verify → repeat QA only
if the fixes substantially changed code → update usage docs and examples → report
the completed work.

## Troubleshooting

- **The review skill asks whether to fix findings:** the approved plan already
  authorizes fixes; continue within the task's scope.
- **The task spans committed and uncommitted changes:** supply the full task diff
  to QA, review, and docs instead of relying on their default git scope.
- **QA, checks, or a reviewer are unavailable:** report the missing coverage and exact
  blocker; finish independent work without claiming the completion gate passed.

## Notes

- Read-only precision: the `Plan` agent has no Edit/Write/NotebookEdit tools, so it
  cannot modify files — but it retains Bash, so "no mutating commands" is an
  instruction, not a hard block. Still far safer than plan mode.
- `--review` runs the full `review-plan` fan-out (including a `second-opinion` codex
  agent and a `research-tech` agent); it costs more, which is why it is opt-in.

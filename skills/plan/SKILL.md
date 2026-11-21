---
name: plan
description: Lightweight planning workflow — plan read-only in-session when already on Opus or stronger, otherwise delegate planning to an Opus subagent (or adopt a plan already agreed in the conversation). With --plan-only, save the plan to a Markdown file and stop. With --complete, skip planning for work already done ad hoc and run only the finishing steps (QA, review, docs, commit, squash). Otherwise implement in auto mode after a single go-ahead gate, run QA and one `code-review --multi`, fix findings, repeat QA only after substantial code changes, update docs, and commit the task's work. The middle tier between "just do it" (tiny tasks) and `longshot` (multi-hour features). Never enters plan mode, so it sidesteps the plan-mode permission prompts. Use when the user invokes /plan, or wants a plan for a medium-sized task before implementing.
argument-hint: '[--plan-only] [--review] [--complete] <task, or blank to infer from conversation>'
effort: xhigh
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Plan (middle tier)

Produce a concrete implementation plan for a medium-sized task, then implement it
after one approval gate, or save it to a file and stop with `--plan-only`.
Deliberately lighter than `longshot` (no up-front
interview, per-task implementer subagents or rulings ledger) and
heavier than just editing — the space where a plan helps but full ceremony is overkill.

**This skill IS the planning workflow for this task.** Do not also invoke
`brainstorming` — that is the heavyweight path this skill exists to avoid.

Two design choices make it work:
- **Never enter plan mode / never call `ExitPlanMode`.** Everything runs in the
  session's normal (auto) mode. This is intentional: it avoids plan mode's read-only
  permission prompts entirely, and a subagent's own tool calls never prompt you.
- **The context that explores is the context that implements.** On Opus or a
  stronger model the main session plans read-only itself, so what it learned while
  exploring is still there when it implements. Only a weaker session hands planning
  to a read-only subagent pinned to Opus, at the cost of re-reading the files later.

The argument is the task. If blank, infer the task from the current conversation.

## Usage

```
/plan add a --json flag to the export command    # plan a stated task
/plan                                            # plan the task from context, or adopt a plan agreed above
/plan --review <task>                            # plan, then multi-agent review before the gate
/plan --plan-only <task>                         # save the plan to a file and stop
/plan --plan-only --review <task>                # review the plan, then save it and stop
/plan --complete                                 # finish ad-hoc work already done: QA, review, docs, commit, squash
```

## Flags

- `--plan-only` — draft the plan, write it to a Markdown file, and stop at Step 3a.
  Use a path the user specifies; otherwise use
  `docs/plans/<YYYY-MM-DD>-<task-slug>.md` relative to the project root (or the
  working directory outside a project). Create the parent directory as needed.
  Choose a numbered suffix if the default path already exists; update an existing
  plan only when the user asks to revise it. This flag takes no positional value;
  the remaining text is the task. It combines with `--review` in either order.
- `--review` — after the plan is drafted, run `review-plan` (multi-agent) on it and
  fold the findings in before presenting for go-ahead. `review-plan` is already
  multi-agent; there is no separate `--multi`. The final `code-review --multi`
  runs regardless of this flag when implementing; `--plan-only` stops before it.
- `--complete` — the work was already discussed and implemented in this session
  without the skill. Skip planning, the gate and implementation (Steps 1–5) and run
  the finishing steps (Steps 6–9) over it, as set up in Step 0. Remaining text, if
  any, names the task or narrows its scope; otherwise infer both from the
  conversation. Invoking it is the go-ahead for the finishing steps, including
  committing and squashing the task's work; honor any explicit limit the user gives.
  It does not combine with `--plan-only` or `--review`.

## Instructions

### Step 0: Complete ad-hoc work (only if `--complete`)

Set up what the planning steps would otherwise have produced, then go straight to
Step 6:

1. **Reconstruct the requirements.** From the conversation, collect what the user
   asked for, what was decided along the way (including changes of direction), and
   the acceptance criteria that follow. These stand in for the approved plan in
   Steps 6–8.
2. **Fix the task's scope.** List the files this session changed for the task,
   committed or not. If the session committed any of that work, record the base:
   the `HEAD` before the task's first commit. Work from other sessions in the
   checkout stays out of scope.
3. **Check the work is actually done.** If nothing was implemented, say so and
   offer a normal `/plan` instead. If something agreed in the conversation is
   visibly missing, list it and ask whether to implement it first or finish
   without it. Otherwise do not stop.
4. **State the setup in a few lines** — task, requirements, files, base commit if
   any — and continue to Step 6 without waiting for approval.

### Step 1: Scope check (early exit)

Judge the task's size first.

With `--plan-only`, continue to Step 2 for any task size: the user explicitly
requested a plan artifact. Note scope concerns in the plan rather than exiting
or switching workflows.

- **Trivial** (one-liner, obvious fix, rename, config flip): planning is overhead.
  Say so in one line and offer to just do it directly — do not spend a planning
  round-trip. Respect the user if they still want a plan.
- **Too big** (multi-subsystem, architectural, multi-session): this is above the
  middle tier. Say so in one line, offer `longshot` instead, and stop.
- **Middle** (a few files, a new endpoint/component, a contained refactor): proceed.

### Step 2: Draft the plan

**A plan already in the conversation?** When the argument is blank and the
conversation already holds a concrete plan for the task — files and ordered steps,
not just an idea — ask one line before planning: "There's a plan above. Use it,
or plan from scratch?" Wait for the answer.

- **Use it:** skip planning. Recast that plan into the skeleton below,
  check read-only that the files and claims it relies on hold in the current repo,
  and add any gap or drift as an open question. Continue at Step 3.
- **From scratch:** plan as below, treating the conversation's plan as context.

**Plan in this session when it runs on Opus or a stronger model.** Explore
**read-only** — read, search and read-only shell only, no edits and **no** mutating
commands — then draft the skeleton below yourself, under the same directives the
subagent brief lists. Do not dispatch.

**Otherwise dispatch one subagent** via the `Agent` tool:
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
Add "Close call" if A and B both meet the requirements and either differ in
something expensive to reverse (data model, external interface, new dependency,
architecture) or cannot be called with confidence.

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

### Step 3a: Save and stop (only if `--plan-only`)

Write the final plan to the path selected above. Make it self-contained: include
the task statement, relevant requirements from the conversation, and the full
plan skeleton. Include the QA, review, verification, documentation, and commit
steps described in Step 4 as proposed future work, honoring the user's limits.
Keep unresolved questions in the file and mark which ones block implementation.

Exploration and optional review remain read-only; the plan file and its parent
directory are the only writes authorized by this mode. Verify the saved file,
then return its path with a brief summary and any blocking questions. Do not
print the full plan inline, request implementation approval, or continue to
Steps 4–9. A later request to implement the saved plan is a separate instruction.

### Step 4: Present and STOP

Print the plan inline, cleanly formatted, with the **Assumptions & open questions**
called out so the user can resolve them. If the Approach is marked "Close call", add
one line offering to run `brainstorm` on that fork before going ahead. Run it only on
the user's yes, in its embedded mode, then revise the plan around the chosen approach
and present it again. Include QA, one final multi-agent code review,
fixes, conditional post-review QA, verification, documentation updates, and the final commit in the
plan; the go-ahead covers these finishing steps too, including staging and committing the
task's work on the current branch. Honor any explicit limit the user gives, such as "don't
commit".

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
`--review`; do not substitute `--quick`. Run one full code review only. After the
fixes below, run `code-review --re` once in the same session: it reviews only
what changed since the review, so the fix code does not go unreviewed. Fix what it
finds without a further re-review.

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

### Step 8: Update docs

Run `doc --update` scoped to the completed task. Update the canonical docs for the
final behavior, interfaces, usage, and constraints; use `doc --generate` where new
behavior needs documentation that does not exist. Carry durable design decisions
from the plan into the appropriate docs. Do not create a separate plan archive.

Check the updated examples and links, and run any required documentation checks.
If documentation work exposes a code defect, return to the fix and verification
steps before finishing, applying the same substantial-change rule for repeat QA
without another code review.

### Step 9: Commit and hand off

Invoke the `commit` skill with no argument, limited to the task's changes: code,
tests, and docs land together in the fewest self-contained commits, and other
sessions' work in the checkout stays out. The go-ahead already authorized this; do
not ask again. Do not commit while a check fails or a blocker remains — leave the
work uncommitted and say why in the report.

**With `--complete`, then squash if needed.** When Step 0 recorded a base commit,
the ad-hoc work left commits of its own, so invoke `squash-commits <base>` to fold
them and the new ones into the fewest self-contained commits. Squash only when
every commit in `<base>..HEAD` is the task's and none is on a remote; otherwise
leave history alone and put the proposed before/after commit list under
**Blockers**. Keep the pre-squash tip for the report. Without a base commit there
is nothing to squash.

Then report, in this order:
- **Changed** — the behavior delivered, in a few bullets.
- **QA** — scenarios covered, defects found and fixed, and whether repeat QA ran and why.
- **Review findings** — every valid finding, one line each, with its fix or the reason it
  was rejected; reviewers that failed or timed out.
- **Verification** — the checks run and their results.
- **Docs** — the files updated.
- **Commits** — each hash and subject, or why nothing was committed. After a squash,
  also the pre-squash tip and the undo command `git reset --soft <tip>`.
- **Blockers** — anything still on the user, such as a reinstall.

Do not stop after implementation with an offer to run review, update docs, or
commit later, and do not open the report with a bare "Implemented." that hides the
finishing steps.

## Examples

User: "Plan adding a `--json` flag to export."

Actions: the session (or, below Opus, one read-only subagent) drafts the approach → present the plan including
QA, review, and docs → wait for approval → implement in the main session →
`qa --fix` → one `code-review --multi` → fix findings → `code-review --re` of the fixes → verify → repeat QA only
if the fixes substantially changed code → update usage docs and examples → `commit`
→ report changes, QA, each review finding's resolution, checks, docs, and commits.

User, after discussing and making a change without the skill: "/plan --complete"

Actions: reconstruct requirements and scope from the conversation → state them
→ `qa --fix` → one `code-review --multi` → fix findings → `code-review --re` →
verify → update docs → `commit` → `squash-commits <base>` if the ad-hoc work had
already committed → report.

## Troubleshooting

- **The review skill asks whether to fix findings:** the approved plan already
  authorizes fixes; continue within the task's scope.
- **The task spans committed and uncommitted changes:** supply the full task diff
  to QA, review, and docs instead of relying on their default git scope.
- **QA, checks, or a reviewer are unavailable:** report the missing coverage and exact
  blocker; finish independent work without claiming the completion gate passed.
- **A pre-commit hook fails:** fix what it reports and commit again; follow the
  `commit` skill's troubleshooting rather than bypassing the hook.

## Notes

- Read-only precision: the `Plan` agent has no Edit/Write/NotebookEdit tools, so it
  cannot modify files — but it retains Bash, so "no mutating commands" is an
  instruction, not a hard block. In-session planning has no tool restriction at all,
  so the read-only rule there rests on the instruction alone; the Step 4 gate is what
  stops implementation from starting early.
- `--review` runs the full `review-plan` fan-out (including a `second-opinion` codex
  agent and a `research-tech` agent); it costs more, which is why it is opt-in.

---
name: longshot
description: Run a long autonomous build session from a brief — interrogate every open decision up front with `blind-spots`, then execute for hours without check-ins, deciding ambiguities as recorded rulings instead of stopping to ask. Per task a fresh implementer subagent, an independent spec+quality reviewer, a fix loop, then a whole-branch review and a handoff report with rulings, deferred questions and a squash proposal. Use when the user says "longshot", "work on this independently", "run with this", "ask me everything up front then go", "I'll be away", or hands over a multi-hour feature or package to build end to end. Do NOT use for a single small change — use `plan` for that.
argument-hint: '[--plan FILE] [--no-worktree] [--repos a,b] (brief, or blank to take it from the conversation)'
effort: xhigh
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Longshot

Take a brief, interrogate it until nothing is silently assumed, then build for hours
without the user in the loop.

The bet this skill makes: a session parked on a question costs the user their whole
day and buys nothing, while a wrong ruling costs rework they can see and undo. So
every ambiguity after the interrogation closes gets **decided and recorded**, not asked.

## The contract

Invoking longshot authorizes staging and implementation commits for the run's work
in its writable repos, including on the primary repo's current branch. Honor any
explicit limits the user gives. Do not ask for a separate commit confirmation.
Final squashing requires its own approval under Phase 6.

State it back to the user when the interrogation closes, verbatim in substance:

1. **Every question up front.** The interrogation runs to completion first; after it
   closes, no more questions except the four stops below.
2. **Rulings, not stalls.** Every conflict, gap, plan defect or judgment call gets
   decided and written to the ledger as
   `Ruling: <decision> — <why> — <cost if wrong>`.
3. **Milestone pings only.** One line per completed task. Never a question, never a
   progress summary, never "should I continue?".
4. **Nothing is pushed.** Nothing outside the repos named in the brief is touched.

**Four things stop the run, and only these:** an irreversible or destructive
operation; a security-sensitive action; a side effect outside the work tree that
norms say you ask about first (a merge, a push, a release); or the brief turning out
to be wrong about something load-bearing. Everything else is a ruling.

## Phase 0 — Recon before questions

Uninformed questions waste rounds and spend the user's patience. Before asking
anything, read:

- the project instruction files (`AGENTS.md`, `CLAUDE.md`, `README.md`)
- the workflow file — `workflow.md` / `WORKFLOW.md`, or whatever the brief names.
  **It outranks this skill's defaults.** If none exists, use the default workflow below.
- any plan or spec doc (`docs/plans/*.md`, `docs/specs/*.md`) and note its date
- the reference/neighbour repos the brief names — for the integration surface *and*
  for their tooling: lint, static analysis, git hooks, CI, test layout, release scripts
- git state: branch, whether there are commits at all, what is untracked

Dispatch at most 3 read-only `Explore` agents in parallel for the repo sweeps.

If the brief opens with a technical question of the user's own, **answer it with
analysis and a recommendation** in the first round. Do not hand it back.

## Phase 1 — The interrogation

Invoke `blind-spots` on the brief and run it to completion. Phase 0 already did the
recon its step 2 calls for — do not repeat it.

**This is the one part of a longshot run that needs the user present.** It ends when
the frontier is empty, and that close is the gate for everything after it.

`blind-spots` supplies the mechanics: dependency-ordered rounds, a recommendation on
every question so silence-plus-"go" is a complete answer, and pruning to decisions
that fork the design. Longshot sharpens its fork test — *would a wrong guess here
cost a rewrite, or just a follow-up commit?* Follow-up commit → do not ask it, rule
on it during the run.

These are mandatory wherever they sit in the tree, because the run cannot proceed
correctly without them. Put any still open into the first round:

- **Repo boundary.** Which checkouts may be written to, which are read-only
  reference, and whether new clones/worktrees may be created.
- **Definition of done.** "A complete package I can integrate" means something
  specific — name it: green suite, CI config, docs, a migration branch per consumer.
- The user's own opening question, answered.
- Anything where a wrong guess is architectural.

When the frontier is empty, state the contract above and get the go. From that point
the contract binds: rulings, not questions.

## Phase 2 — Plan (auto-detect)

- **A plan doc exists** → read it, then validate it against the *current* repo state:
  which steps are already done, which paths moved, what the plan asserts that is no
  longer true. Report the drift as part of the run, do not stop for it.
- **No plan doc** → write one now. Invoke `plan` for a moderate scope; for a large one
  run `review-plan` (multi-agent) over the draft and fold the findings in. Save to
  `docs/plans/<YYYY-MM-DD>-<slug>.md` with checkbox tasks.

Either way there is **no approval gate here** — the interrogation was the gate.

Open the ledger at `docs/plans/<YYYY-MM-DD>-<slug>-ledger.md` (see
`references/prompts.md` for its shape) and append to it for the rest of the run. It
lives on disk, not in context, so it survives compaction.

## Phase 3 — Isolation

Follow the workflow file. Default:

- Work on the primary repo's current branch unless the user requests another branch.
- **Every foreign repo gets a worktree**, branched off its main:
  `git worktree add ../<project>-worktrees/<repo> -b <feature> ../all/<repo>`.
  Never commit to a foreign repo's `main`. Never combine two repos in one commit.
- `--no-worktree` skips this and works in place.

## Phase 4 — The execution loop

Per plan task, in order. **Sequential — one subagent at a time.** This fixed fan-out
is the skill's own and needs no further dispatch approval; do not widen it.

1. **Implement.** One fresh write-capable `general-purpose` subagent. Construct its
   prompt from scratch — it inherits nothing. It must carry the literal line
   *"Do not dispatch sub-agents; do this work yourself."* Template in
   `references/prompts.md`.
2. **Review.** One read-only subagent (`Explore`), which has not seen the
   implementer's reasoning, checks the diff against that task's plan section on
   **both** spec compliance and code quality.
3. **Fix loop.** Findings → a fix subagent, then a re-review scoped to the fixes
   only. Repeat until clean, **max 3 rounds**; then rule on what is left, record it,
   and move on.
4. **Verify yourself.** Run the project's own check command (`just check`,
   `npm test`, `cargo test` …) in this session and read the whole output — the
   summary line and exit code, not a grep for the outcome you expect. A subagent
   reporting "all tests pass" is not evidence. Failures get fixed, never labelled
   pre-existing.
5. **Commit** the task's work, per the project's commit convention.
6. **Ping.** One line (see below), then straight into the next task.

**Parallel tasks** only when the plan marks them independent *and* they live in
different worktrees — max 3 at once, still one implementer each.

**Whatever you cannot run** (a GUI test host, a credentialed deploy, a sandbox-blocked
suite) is compile-verified as far as possible, recorded, and carried to the handoff's
"only you can do" list. It is not a reason to stop.

### Milestone pings

After each task's verify, exactly one line. No question, no invitation to respond:

```
Task 3/6 done — consumer registry + bounded sink fan-out, 41 tests, clippy clean. On to install/hooks.
```

## Phase 5 — Whole-branch review

Per the workflow file. Default: `code-review` over the full diff of every touched
repo (`--quick` only if the whole longshot was small), then a fix wave, then a
re-review scoped to those fixes. Cross-repo runs get one reviewer whose job is
**contract coherence** — wire formats, manifest shapes, command strings, identity
semantics agreeing across repo boundaries.

## Phase 6 — Handoff

One report. Template in `references/prompts.md`. It must contain:

- **What exists, where** — a repo / path / branch / commit-count table.
- **Only you can do** — each blocked check with the exact command to run.
- **Rulings** — the ledger, grouped scope vs. design, each as
  decision — why — cost if wrong.
- **Deferred questions** — everything collected but not urgent enough to break the
  contract.
- **Squash proposal** — the concrete before/after commit list, awaiting a yes.
  Never rewrite history without one (delegate to `squash-commits` once approved).
- **Nothing was pushed** — and which checkouts were left untouched.

## Default workflow

Used only when the project has no workflow file:

> Pick the next task → parallelizable? send it to a worktree → plan it → big? review
> the plan multi-agent → implement → QA → code-review (multi; quick for small) → fix
> everything → squash → re-integrate the worktree.

## Examples

### Example: a package to be integrated by two other repos

User: *"Work on this fairly independently. Other repos are under `../all/juggler` and
`../all/ringleader`. Ask whatever you need up front so you can work independently
after. Follow `./workflow.md`. In the end I want a complete package I can integrate.
One question to start: what about sessions that get killed?"*

Actions: read `workflow.md`, the plan doc, both neighbour repos' tooling and the
integration surfaces (3 `Explore` agents) → answer the killed-sessions question with
a recommendation, then `blind-spots`: round 1 asks the questions answerable now
(repo boundary, protocol scope, what "integrate" means, …), round 2 the
two that only became questions once protocol scope was settled, state the contract → validate the plan
against the repo → worktree per consumer repo → 6 tasks through the loop with pings →
whole-branch review + contract-coherence pass + fix wave → handoff.

Result: three branches ready to integrate, a rulings ledger explaining every decision
made in the user's absence, one XCTest run flagged as theirs to do, and a squash plan
waiting on a yes. Zero user turns between the interrogation closing and the report.

### Example: too small for longshot

User: *"Add a `--json` flag to the export command, run it independently."*

Action: say this is a `plan`-sized task, not a longshot, and offer to run `plan`
instead. Longshot's overhead only pays off across many tasks.

## Troubleshooting

### The run stalls waiting for the user anyway

**Cause:** treating an ambiguity as a stop condition. Only the four listed stops
qualify.
**Solution:** re-read the four. If it is not one of them, decide, write the ruling,
continue. A plan defect is a ruling. A conflict between the plan and the spec is a
ruling — the spec wins.

### Reviews keep passing but the code is wrong

**Cause:** the reviewer inherited the implementer's framing, or you accepted a
subagent's word for a green suite.
**Solution:** the reviewer must be a fresh read-only agent given the diff and the
plan section, never the implementer's report. And run the check command yourself in
Phase 4 step 4 — that step is not delegable.

### Context runs out mid-run

**Cause:** a multi-hour run outlives its context window.
**Solution:** this is expected and handled — the plan's checkboxes and the on-disk
ledger are the state. After a compaction, re-read both and resume at the first
unchecked task. Never restate finished work into context to "remember" it.

### The user comes back mid-run and asks something

**Cause:** normal — the contract binds you, not them.
**Solution:** answer, then resume. Do not turn it into a check-in or re-open the
interrogation.

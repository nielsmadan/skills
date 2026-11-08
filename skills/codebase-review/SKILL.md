---
name: codebase-review
description: Review a whole codebase aspect by aspect — overview, docs truth-check, state, API, persistence, caching, startup, auth, errors, UI, layering, dependencies, CI, tests, security, feature deep dives, consistency, architecture roadmap — writing a doc per aspect and a verified findings ledger that doubles as the TODO. Plans first (recon, `blind-spots`, `review-plan`, one start gate), then runs independently. `--fix` hands settled findings to named worker sessions in worktrees or sibling checkouts, integrated locally by fast-forward without pushing; major user-facing changes wait for decision waves at the end. Reports user-facing and other changes. Use for "codebase review", "review the whole codebase", "onboard me to this repo", "deep dive this app", "audit the code base", "review and fix everything". Not for a diff or PR (code-review), a CLI release pass (release-review), or building a feature (longshot).
argument-hint: '[--fix] [--worker LEAD] [--aspects a,b,…] [repo paths or focus] (blank resumes a programme)'
effort: high
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Codebase Review

Review a codebase one aspect at a time. Each aspect produces a doc that explains how it works
and a set of verified findings (bugs, improvements, tidy-ups, doc errors). The findings
accumulate in one ledger that serves as the user's TODO. With `--fix`, worker sessions fix the
settled findings while the review continues, and the lead integrates their branches locally.

**Preparation needs the user; the run is independent.** Until the start gate is approved, stay
read-only and wait for an answer to every question asked. Silence, a question tool returning,
a preselected recommendation and the original invocation are none of them answers.

**`--worker LEAD`** is a different role. Skip everything below and follow "Worker mode" in
`references/workers.md`.

References:
- `references/aspects.md`: the aspect catalog, its order and each aspect's questions
- `references/formats.md`: programme, ledger, prompts, briefs, decision waves, the final report
- `references/workers.md`: worker setup, worker mode, syncing and local integration

## The contract

State it back at the start gate:

1. **Every question up front.** After the start gate there are no questions, except for the
   stops below and the decision waves at the end of a `--fix` run.
2. **Rulings, not stalls.** Every judgment call is decided and logged in `programme.md` as
   `R<n> — <decision> — <why> — <cost if wrong>`.
3. **Held, not asked.** Under `--fix`, a major user-facing change is parked as `held`, along
   with everything that depends on it. The run continues around it, and the user decides held
   items in waves at the end, never one at a time mid-run.
4. **Milestone pings only.** One line per finished aspect or integrated batch.
5. **Local and unpushed.** Writes go only to the docs root, the ledger and, under `--fix`, the
   worker branches. Approval of the start gate authorises creating the planned worktrees and
   branches, the workers' commits on their branches, and fast-forward integration of those
   branches into the integration branch. Nothing is pushed, and no repo outside the plan is
   touched.

**The stops:** an irreversible or destructive operation; a security-sensitive action; a side
effect beyond the contract (a push, a release, a non-fast-forward change to the integration
branch); or the framing turning out to be wrong about something load-bearing. Everything else
is a ruling.

## Phase 0 — Start or resume, then recon

Look for `codebase-review/programme.md` under the repo's `docs/` or under a `docs/` folder in
any parent directory (a workspace above several checkouts).

- **Found:** read `programme.md` and the ledger. Print **Now**, **Next** and the in-flight
  batches. Check each worker branch for commits since the last update and integrate any that
  have reported. Then continue from **Now** without re-asking framing questions. A programme on
  disk is not approval for new scope.
- **Not found:** run the recon.

Recon happens before any question, because an uninformed question wastes a round. Read the
instruction files (`AGENTS.md`, `CLAUDE.md`, `README.md`), the docs tree and ADRs, the stack and
build files, the test setup, the CI and lint config, the git state of every candidate repo, and
any sibling checkouts in the workspace. Use at most 3 read-only `Explore` agents, one per repo.
Draft the **system overview** from this (aspect 1 in `references/aspects.md`). It is the first
thing the user gets, and it makes the interview concrete.

## Phase 1 — The interrogation

Invoke `blind-spots` on the brief, carrying the recon forward, and run it to completion. These
questions are mandatory wherever they fall in its tree:

- **Repos:** which are reviewed, which are read-only reference, and (with `--fix`) which are
  writable.
- **Docs root:** where the aspect docs and the ledger live. The options are the repo's own doc
  set (routed through `doc`, committed with the fixes) or a workspace folder outside the repos
  (private knowledge docs that the team never sees). Ask whether wrong repo docs get corrected,
  or only logged as `D` findings.
- **Aspects:** which ones, how deep, and which feature areas get deep dives. Propose a list
  from the catalog fitted to the recon, and ask about anything the catalog lacks.
- **Baseline:** the branch and commit to review. Uncommitted user edits are reviewed at their
  committed version and are never mentioned.
- **With `--fix`:**
  - The **fix policy** per class, for example: bugs and tidy-ups are fixed; improvements are
    fixed when they cost half a day or less, larger ones go to the TODO; doc errors are fixed.
  - What counts as a **major user-facing change** for this project. Major changes are held.
    Minor ones are fixed and reported.
  - The **integration branch**, and the checkout it lives in. This is normally the lead's own
    checkout.
  - **Workers:** how many, and where each one lives (a new worktree or an existing sibling
    clone). Propose a number from the size of the codebase.
  - The **check command** per repo, and the commit convention.
- **Definition of done:** what the user must have at the end.

Answer the user's own opening questions with analysis in the first round. Do not hand them back.

## Phase 2 — The plan

Draft `programme.md` (format in `references/formats.md`) in the conversation. It contains the
framing table, the fix policy, and the aspect list in catalog tier order. For each aspect it
gives the scope paths, the doc path, the sibling docs it builds on, its boundary with
neighbouring aspects, the model, and which aspects run in parallel (only those with disjoint
scopes, at most 3 at once).

The scope paths matter twice. They keep the reviewers apart, and the readiness analysis uses
them to decide when an area is settled.

**Self-review the draft** for overlapping scopes, aspects without questions, aspects the
definition of done does not need (cut them, and say what you cut) and missing framing. Then run
`review-plan` over it, always, and fold in its findings. Bring any rejected finding to the gate
with the reason.

## Phase 3 — Worker setup (`--fix` only)

Sort out the hand-off before the review starts, following "Setup" in `references/workers.md`:

1. Propose each worker's home and the commands that create it, and create the worktrees on the
   user's yes.
2. Give the user the start command for each named session.
3. Wait for every worker's hello.
4. Test the integration path from the lead's side.

The setup is done only when every worker has reported a green baseline and the path resolves in
both directions.

If the user wants `--fix` without worker sessions, the run still reviews and rules as normal.
The ruled-fix findings then go to `longshot` at the end, with the ledger as its brief.

### Start gate

Present the framing, the aspect plan, the fix policy, the Workers table and the contract. Say
that preparation is complete, then ask: **"Start the review with this plan? After you approve,
you can leave it running."** Wait for an explicit yes. A reply that changes scope gets settled
and a revised gate.

After the yes, announce **"The review is starting. I'll decide details myself, hold major
user-facing changes for the end, and send milestone pings."** Only now write `programme.md` to
`<docs-root>/codebase-review/`, record the base commit and the user's approval message, and
create `RUN=${TMPDIR:-/tmp}/codebase-review-<slug>` for raw findings, verifications and check
logs.

## Phase 4 — The review loop

For each aspect, in plan order, with up to 3 in parallel where the plan allows:

1. **Review.** Dispatch the aspect reviewer (prompt in `references/formats.md`). It writes the
   doc and `$RUN/findings-<aspect>.md`, and returns a 15-line summary.
2. **Verify.** A fresh verifier re-checks each finding at its `path:line`, fixes the line
   numbers, rejects what the code disproves, and marks duplicates of existing ledger entries.
   A finding with no verification mark never gets handed off.
3. **Second opinion, where it pays.** Invoke `second-opinion` for any of the following:
   - a high-severity finding the verifier only rated `✔ (likely)`
   - a security or data-loss finding
   - a recommendation that would restructure a whole area

   Give it the finding and the code, not your conclusion. Use at most one call per aspect.
   Record disagreements on the entry.
4. **Ledger.** Merge the verified findings into `findings.md` under the aspect's section, with
   stable IDs. Under `--fix`, rule each one against the fix policy: `fix`, `todo` or `held`.
   Mark the dependents of held entries as blocked.
5. **Docs.** When the docs root is the repo's doc set, fold the aspect doc in with `doc`:
   `--generate` for a new area, `--update` where a repo doc was wrong. Otherwise the reviewer's
   doc stands as written.
6. **Ping**, for example `Aspect 7/22 done — auth: 19 findings (6 bugs), 2 held. On to analytics.`
   Send it in the same message as the next dispatch. An ended turn is a stopped run.

**Context discipline is what lets this finish.** Raw findings, verifications and logs stay in
`$RUN`. This session reads the counts and the 15-line summaries, and pulls an entry in only to
rule on it. A run that reads reports inline compacts every few aspects.

## Phase 5 — Hand-off while reviewing (`--fix` only)

After each aspect is verified, run the readiness analysis. A finding is **ready** when all of
the following hold:

- it is verified, ruled `fix`, and not held
- everything in its Depends list is fixed or decided
- **its area is settled:** no queued or running aspect has a scope that covers its files
- its Touches do not overlap a batch in flight
- it is not a multi-area refactor; those wait until Phase 6 has named the theme they belong to

Group the ready findings into batches of 3 to 8 that share one area, write `briefs/B-n.md`, and
send its path to an idle worker. On Claude Code, use `SendMessage` to the worker's name. On
other harnesses, print the path for the user to relay. Do not monitor the worker. When its
report arrives, integrate it following "Lead-side integration" in `references/workers.md`. That
includes running the check command yourself. Then go back to the review.

Prioritise batches that remove code, because removed code stops showing up in later aspects.
An area is usually first settled after tier 2, so hand-offs normally begin during tier 3.

## Phase 6 — Synthesis

Run the synthesis aspects from `references/aspects.md` once every planned aspect is verified:

1. **Consistency sweep** with `review-consistency`, over the competing patterns the aspects
   found.
2. **Consolidation:** docs consistency and findings staleness at the current HEAD, as two
   parallel agents. Under `--fix`, integrated batches have moved the code, so this pass also
   retires findings that a fix resolved in passing.
3. **Hotspots:** churn × size × fix commits.
4. **Architecture and roadmap.** Use an `opus` agent with `review-architecture` as the lens. It
   writes `architecture.md` and the Priorities section at the top of the ledger, and names the
   cross-cutting themes. Check the roadmap with `second-opinion`.

Under `--fix`, multi-area refactors now become batches or held items, according to the
themes and the fix policy.

## Phase 7 — Decision waves (`--fix` only)

Start once the review is complete and every ready batch has been handed off. Present the held
items in waves (format in `references/formats.md`):

- Each item is a scenario in the user's terms, with options and a recommendation.
- The decisions that unblock the most dependents come first.
- Each wave holds only the decisions that are independent of each other.

Record each answer on the entry as `decided wave <n>`, along with the ruling. Re-run readiness:
decided-fix items and their now-unblocked dependents become batches. Present the next wave
while those batches run. Stop when nothing is held, or when the user parks the remainder as
TODO.

## Phase 8 — Final checks and report

Under `--fix`:

1. Run the check command on the integration branch yourself.
2. Run `code-review` over `<base>..HEAD` of the integration branch, with `--multi` when more
   than about 30 commits landed. Send the fixes to a worker as a final batch, then re-review
   only those fixes.
3. Run `qa` over the user-facing changes where the app can be run here. Whatever cannot be
   exercised goes to Blocked on you.
4. Run `doc --update` over the integrated range, so the repo docs reflect what the fixes
   changed.

Then write the final report (template in `references/formats.md`) to
`<docs-root>/codebase-review/report.md` and print it. It must contain:

- **Blocked on you**, first
- **User-facing changes**: each one with before → after in the user's terms, its finding and
  its commit
- **Other changes**, summarised by theme
- review coverage, the top of the roadmap, and where everything is, including the worker
  cleanup commands

Do not remove worktrees, delete branches or squash. Workers committed one self-contained commit
per finding, so the history is already clean. Offer `squash-commits` only if the user asks.

## Model per role

Pass `model` on every dispatch. An omitted model silently inherits the session's top tier.

| Role | Model |
|---|---|
| Recon (`Explore`) | `sonnet` |
| Aspect reviewer | `opus` for foundations, security, architecture and feature deep dives; `sonnet` for inventories (docs, dependencies, agent setup, tooling) |
| Verifier, consolidation | `sonnet` |
| Architecture and roadmap | `opus` |

## Examples

### Example: onboarding to an inherited app, review only

User: *"I'm new on this app and middleware. Review it thoroughly: architecture, state, startup,
tests, everything. Docs go in my own folder; keep the repos untouched."*

Actions:
1. Recon with 3 `Explore` agents, then a system overview draft.
2. `blind-spots`: docs root `~/work/<project>/docs`, middleware as reference only, 22 aspects
   including shop and onboarding deep dives.
3. `review-plan` over the programme, then the start gate and the yes.
4. Tiers 1–5 with pings. Each aspect yields a doc plus verified findings in `findings.md`. Two
   security findings go through `second-opinion`.
5. Synthesis: the consistency sweep, consolidation, hotspots, and `architecture.md` with a
   ranked roadmap.

Result: 24 docs, a 1,000-line ledger and TODO with priorities at the top, and a report leading
with coverage and the roadmap. The repos are untouched.

### Example: review and fix with two workers

User: *"codebase-review --fix. Big repo. Hold anything that changes what users see in a major
way. I'll run workers."*

Actions:
1. Interview: bugs and tidy-ups are fixed; improvements are fixed when they cost half a day or
   less; a flow or default change counts as major.
2. Setup: worktree `../app-cr-w1` and the existing clone `../app2`. The user starts `w1` and
   `w2` and runs `codebase-review --worker <lead>` in each. Both hellos report green, and the
   path test resolves.
3. Gate, then the yes.
4. Hand-offs begin during tier 3, once startup and auth are settled. B-1 goes to w1. w1 rebases
   onto `main`, the lead fast-forwards, runs the check itself, and marks the findings fixed.
5. After synthesis, decision waves: wave 1 has 5 items unblocking 12 dependents, and wave 2 has
   3 items.
6. Final `code-review --multi`, then `qa`, `doc --update` and the report.

Result: 64 commits on `main`, all local, with 9 user-facing changes listed before → after. The
remaining TODO is ranked.

### Example: resuming

User: *"codebase-review"* in a repo with a programme.

Action: print Now, Next and the batches. Integrate B-6, which w2 reported while the lead's
session was closed. Continue with the next aspect.

## Troubleshooting

### The run asks the user about a held change mid-run
**Cause:** treating a major user-facing change as a stop.
**Solution:** it is not a stop. Mark it held, block its dependents, and continue. It belongs in a
Phase 7 wave.

### A worker's branch won't fast-forward
**Cause:** another batch landed after the worker rebased, or the worker branched from a stale
tip.
**Solution:** message the worker to rebase onto the integration branch and re-report. Never
merge with a merge commit, and never rebase on the worker's behalf. If git refuses because of
the user's uncommitted edits, record it in Blocked on you and carry on.

### Later aspects keep rediscovering the same issue
**Cause:** the finding is ruled fix but not yet integrated, or reviewers are not given the
ledger.
**Solution:** the verifier marks duplicates against the ledger. Prioritise the removal batch, so
the code stops presenting the issue.

### Docs contradict each other after many aspects
**Cause:** sibling docs were written against older commits.
**Solution:** each reviewer brief lists its sibling docs and says to correct them explicitly.
The consolidation pass in Phase 6 re-checks line references at the current HEAD.

### A worker reports green, but the check fails on the integration branch
**Cause:** tests were deselected, an exit code was swallowed by a pipe, or the worker did not
rebase.
**Solution:** the lead's own check run is the verdict. Send the log path back as a new batch.
Never rewind the integration branch without the user.

### Context runs out mid-run
**Solution:** re-read `programme.md` (Now, Start, Workers, Batches) and the ledger, then resume.
If no start approval is recorded, ask before continuing; never invent one.

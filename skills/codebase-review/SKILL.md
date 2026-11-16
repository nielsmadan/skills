---
name: codebase-review
description: Review a whole codebase aspect by aspect, with aspects fitted to the project type (mobile, desktop, web frontend, static site, CLI, backend, library) — docs truth-check, architecture, tests, security, the type's foundations, feature deep dives, consistency, roadmap — writing a doc per aspect and a verified findings ledger that doubles as the TODO. Plans first (recon, `blind-spots`, `review-plan`, plan approval), then walks the plan with the user aspect by aspect — agents review and verify in the background, the user confirms rulings and decides judgment calls one at a time. `--auto` runs independently after the gate, with decision waves at the end. `--fix` hands settled findings through `crew` to worker sessions, integrated locally, never pushed. Use for "codebase review", "review the whole codebase", "onboard me to this repo", "deep dive this app", "audit the code base", "review and fix everything". Not for a diff or PR (code-review), a CLI release pass (release-review), or building a feature (longshot).
argument-hint: '[--fix] [--auto] [--aspects a,b,…] [repo paths or focus] (blank resumes a programme)'
effort: high
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Codebase Review

Review a codebase one aspect at a time. Each aspect produces a doc that explains how it works
and a set of verified findings (bugs, improvements, tidy-ups, doc errors). The findings
accumulate in one ledger that serves as the user's TODO. With `--fix`, worker sessions fix the
settled findings while the review continues, and the lead integrates their branches locally.

**Two modes.** By default the run is a **walkthrough**: after the plan is approved, the lead
goes through it with the user one aspect at a time, and the user rules on every finding. With
`--auto`, the run is **independent** after one start gate: the lead rules by policy, holds
major changes, and the user decides those in waves at the end.

**Preparation needs the user in both modes.** Until the plan is approved, stay read-only and
wait for an answer to every question asked. Silence, a question tool returning, a preselected
recommendation and the original invocation are none of them answers.

This skill is the lead. Worker sessions run `crew join` and follow the `crew` skill; their
briefs carry this skill's rules.

References:
- `references/aspects.md`: the aspect catalog by project type, how to pick from it, its order
  and each aspect's questions
- `references/formats.md`: programme, ledger, prompts, briefs, decision waves, the final report
- `references/workers.md`: what a codebase review adds on top of `crew` (setup records, brief
  rules, integration checks, cleanup)
- `references/extensions.md`: discover project-local review extensions during recon and
  collect their evidence once for the aspects that consume it

## Review grading

Use only these finding priorities, in descending order:

- **Critical Issues (Must Fix):** a verified path causes data loss, a security failure, a materially
  wrong operation, or makes a core workflow unusable without reasonable recovery.
- **Improvements (Should Fix):** an ordinary supported workflow demonstrably fails or repeatedly
  imposes substantial friction, or a concrete design defect creates meaningful maintenance cost.
- **Suggestions (Nice to Have):** a worthwhile improvement with small practical impact, including
  optional polish, local simplification, and rare recoverable edge cases.

Grade the demonstrated consequence, realistic reachability, and available recovery against project
priorities. A category, missing convention, hypothetical future problem, or confidence that a claim
is true does not set its priority. Do not assign automatic severity floors or ceilings. Keep
unverified claims in validation gaps, outside the graded finding count; distinguish suggestions
from defects. For plans, trace the consequence if implemented and state the assumptions.

Use the short labels **Must Fix**, **Should Fix**, and **Nice to Have** in summaries and ledgers.
Keep effort, verification status, user-facing change size, and tool/vendor diagnostic ratings
separate. When called by `code-review`, return its requested evidence and impact fields; the parent
owns scoring and final triage. Otherwise apply this rubric directly. Omit empty priority sections.

**Reach** goes on every bug: `common`, `plausible`, `rare` or `misuse` (corrupt data, hostile
input, API abuse), with the concrete trigger. It feeds the priority and the fix policy.

## Risk flags

A fix that does any of these is never ruled by policy, whatever its user-facing level: in the
walkthrough it is a judgment item, and under `--auto` it is held for a decision wave:

- removes or narrows something users can do today, or contradicts a promise
- changes a persisted or wire format, or what existing saved data means
- adds public API, or changes what an existing API does
- changes interaction or a default behaviour (focus, keys, clicks, timing)
- adds a dependency, a resource bundle or a packaging change
- adds global or shared mutable state
- adds an abstraction with one user
- is much larger than the failure it removes

Reviewers and verifiers put the flags on the entry. Workers check again while implementing,
where most flags appear, and stop a fix that trips an unlisted one. When the code and a promise
disagree, the user decides which is wrong: calling it a bug does not lift the first flag, and no
fix rewrites a promise to fit.

## The contract

State the one for the mode at the gate.

**Walkthrough (default):**

1. **The plan is the agenda.** Every message opens with the position line, so the user always
   knows which aspect and item is on the table.
2. **The user rules on findings.** The lead proposes a ruling for each and decides only
   mechanics (merging duplicates, batch grouping, wording), logged as
   `R<n> — <decision> — <why> — <cost if wrong>`.
3. **Recording, not implementing.** No code changes in the conversation. Under `--fix`, fixes
   run in worker batches the user approved at a readiness prompt.
4. **One pause per aspect.** Inside an aspect, go straight from one ruling to the next item.
   At the aspect close, wait for the user's go before opening the next one.

**Independent (`--auto`):**

1. **Every question up front.** After the start gate there are no questions, except for the
   stops below and the decision waves at the end of a `--fix` run.
2. **Rulings, not stalls.** Every judgment call is decided and logged as an `R<n>` ruling.
3. **Held, not asked.** Under `--fix`, a major user-facing or risk-flagged change is parked as
   `held` with its dependents. The run continues around it; the user decides held items in
   waves at the end, never mid-run.
4. **Milestone pings only.** One line per finished aspect or integrated batch.

**Both modes — local and unpushed.** Writes go to the work folder and, at the end, the harvest
into the repo's docs. Under `--fix` they also go to the worker branches. Approval of the plan
authorises:
- creating the planned worktrees and branches
- the workers' commits on their branches
- fast-forward integration of those branches into the integration branch
- building the regrouped history on its own branch in Phase 8
- deleting the work folder once Phase 8's conditions hold

Nothing is pushed, and no repo outside the plan is touched.

**The stops** (`--auto`): an irreversible or destructive operation; a security-sensitive
action; a side effect beyond the contract (a push, a release, a non-fast-forward change to the
integration branch); or the framing turning out to be wrong about something load-bearing.
Everything else is a ruling. In the walkthrough these are simply asked when they come up.

## The work folder

Everything the run produces lives in `.codebase-review/` at the root of the lead's checkout. A
multi-repo run uses the primary repo. Its layout:

- `programme.md`
- `findings.md`, the ledger and TODO
- `docs/<aspect>.md`, one per aspect
- `briefs/` and `reports/`
- `run/`, for raw findings, verifications and check logs (`$RUN`)
- `report.md`

The folder is scratch, never committed: at plan approval, append `/.codebase-review/` to
`.git/info/exclude` (local, shared with worktrees; `.gitignore` stays untouched). Do not choose
another location or ask about it. Phase 8 harvests what is durable and deletes the folder.

## Phase 0 — Start or resume, then recon

Look for `.codebase-review/programme.md` at the repo root.

- **Found:** read `programme.md` and the ledger. Print **Now**, **Next** and the in-flight
  batches. Run `crew status`, read any report in `reports/` not yet integrated, and integrate
  it. Then continue from **Now** without re-asking framing questions; in the walkthrough,
  re-present the item **Now** points at. A programme on disk is not approval for new scope.
- **Not found:** run the recon.

Recon comes before any question. Read the instruction files (`AGENTS.md`, `CLAUDE.md`,
`README.md`), the docs tree and ADRs, the stack and build files, the test setup, the CI and
lint config, the git state of every candidate repo, and any sibling checkouts. Use at most 3 read-only `Explore` agents, one per repo.
Draft the **system overview** from this (the first Core aspect in `references/aspects.md`), so
the interview is concrete. In it:

- **Tag the project types** per repo or package, with the signals behind each tag
  (`Types: app/ → mobile app; packages/ui → library: UI component — signals: …`). The tags pick
  the catalog sections, so a wrong tag means a wrong plan.
- **List the promises:** what the README, docs, help text and examples say users can do ("Tab
  can be recorded"), each with its source.
- **Discover extensions:** follow `references/extensions.md` for each reviewed repository.
  Read applicable project-local `codebase-review-*` skills, record their package scopes and
  contributions, and include them in the plan. No installed extension means no extra work.

## Phase 1 — The interrogation

Invoke `blind-spots` on the brief, carrying the recon forward, and run it to completion. These
questions are mandatory wherever they fall in its tree:

- **Repos:** which are reviewed, which are read-only reference, and (with `--fix`) which are
  writable.
- **End state for open findings:** where findings still open at the end will live. The options
  are a roadmap or TODO doc in the repo, the issue tracker, or the work folder until they are
  addressed (which delays its deletion). Without `--fix`, every finding is still open at the
  end, so this question settles where the TODO lives.
- **Types and aspects:** confirm the type tags in the first round. Then propose Core plus every
  section the tags match, deduplicated, and the feature units for deep dives (feature areas,
  pages, commands, endpoint groups or modules). Every aspect of a matched section is planned or
  goes under Skipped with a one-line reason. Add the project-specific aspects the catalog lacks.
- **Baseline:** the branch and commit to review. Uncommitted user edits are reviewed at their
  committed version and are never mentioned.
- **Promises:** confirm the recon's list and ask what else must never break.
- **Smoke list:** about five core workflows, and how this session drives them with real input:
  events through the OS or the shipped binary (an example app with posted clicks and keys, the
  CLI in a shell, a browser), never calls into the code.
- **With `--fix`:**
  - **How settled the project is.** Ask it first: it sets the fix policy's default and the
    change budget (source-line growth over the baseline, tests and docs excluded):

    | Maturity | Default fix policy | Budget |
    |---|---|---|
    | Settled ("done", maintenance only) | bugs with a `common` or `plausible` reach, and doc errors; everything else to the TODO | 5% |
    | Active | the above, plus improvements of half a day or less and tidy-ups in code a fix already touches | 15% |
    | Overhaul | bugs, tidy-ups and doc errors; improvements of half a day or less | none |

    Under Settled and Active, `rare` and `misuse` bugs go to the TODO.
  - The **fix policy** per class, starting from that default. In the walkthrough it sets the
    proposed rulings the user confirms.
  - What counts as a **major user-facing change** for this project. Major and risk-flagged
    changes are judgment items (held, under `--auto`). Minor ones follow the policy and are
    reported.
  - The **integration branch** and its checkout, normally the lead's own.
  - **Workers:** how many (propose from the codebase size), each in a new worktree or an
    existing sibling clone.
  - The **check command** per repo, and the commit convention.
- **Definition of done:** what the user must have at the end.

Answer the user's own opening questions with analysis in the first round. Do not hand them back.

## Phase 2 — The plan

Draft `programme.md` (format in `references/formats.md`) in the conversation: the framing, the
type tags, the aspect list in catalog tier order, and the Skipped list. Each aspect gets scope
paths, doc path, the sibling docs it builds on, its boundary with neighbours, the model, and
which aspects run in parallel (disjoint scopes only, at most 3). Scope paths also tell the
readiness analysis when an area is settled.

**Self-review the draft** for overlapping scopes, aspects without questions, aspects the
definition of done does not need (move them to Skipped) and missing framing. Then always run
`review-plan` and fold in its findings; bring any rejected one to the gate with the reason.

**Run the smoke list on the baseline** with real input. A failing check is the review's first
finding. A check that could not be driven records what was tried; "needs a device" without an
attempt is not a result.

## Phase 3 — Worker setup (`--fix` only)

Load `crew` and follow "Setup" in `references/workers.md`: propose each worker's home, create the worktrees on the user's yes, give the `crew join` line
for each session, and wait until every worker reports a green baseline and `crew status` shows
it joined and level. Without worker sessions, the ruled-fix findings go to `longshot` at the
end, with the ledger as its brief.

## Plan approval

Present the framing (including promises, maturity, fix policy and budget), the type tags, the
baseline smoke results, the aspect plan with Skipped, the Workers table and the contract for
the mode. Then ask:

- Walkthrough: **"Start with this plan? We'll go through it one aspect at a time, and you rule
  on the findings."**
- `--auto`: **"Start the review with this plan? After you approve, you can leave it running."**

Wait for an explicit yes. A reply that changes scope gets settled and a revised gate. Under
`--auto`, announce after the yes: **"The review is starting. I'll decide details myself, hold
major user-facing changes for the end, and send milestone pings."** Only now create the work folder
and add it to `.git/info/exclude`. Confirm with `git check-ignore .codebase-review` that it is
excluded. Then write `programme.md`, recording the base commit, the user's approval message and
the baseline size (source, test and README lines, with the command that counted them).
Set `RUN` to the absolute path of `.codebase-review/run`.

Before dispatching aspect reviewers, collect the approved extensions' evidence as described
in `references/extensions.md`. The lead owns tool setup and collection; reviewers consume the
recorded artifacts. Tool failures become validation gaps, not findings or a clean result.

## Phase 4 — The review loop

For each aspect, in plan order, with up to 3 in parallel where the plan allows. In the
walkthrough, steps 1–5 run in the background: dispatch the next aspects' reviews before
presenting the current one, so the next is verified when its walk begins. Never present an
aspect before its verify step is done.

1. **Review.** Dispatch the aspect reviewer (prompt in `references/formats.md`). It writes the
   doc and `$RUN/findings-<aspect>.md`, and returns a 15-line summary. Include the applicable
   extension guidance and evidence paths; do not create another aspect for the same concern.
2. **Verify.** A fresh verifier re-checks each finding at its `path:line`, fixes the line
   numbers, rejects what the code disproves, and marks duplicates of existing ledger entries.
   A finding with no verification mark never gets handed off.
3. **Second opinion, where it pays.** Invoke `second-opinion` for any of the following:
   - a potentially consequential finding the verifier only rated `✔ (likely)`; keep it ungraded until confirmed
   - a security or data-loss finding
   - a recommendation that would restructure a whole area

   Give it the finding and the code, not your conclusion. Use at most one call per aspect.
   Record disagreements on the entry.
4. **Ledger.** Merge the verified findings into `findings.md` under the aspect's section, with
   stable IDs. Rule each one against the fix policy and its Reach: `fix` or `todo` (without
   `--fix`, everything is `todo`). A risk flag or a major UF makes it a judgment item, `held`
   under `--auto`. In the walkthrough every ruling stays `proposed` until the user confirms it.
   Mark the dependents of held or undecided entries as blocked.
5. **Docs.** A wrong repo doc is a `D` finding; a missing one is an improvement; a promise the
   code breaks is a judgment item (held, under `--auto`), never a `D`. **The docs rule** binds
   every doc change in the run: fix what is wrong, add only what that doc's readers need, and
   keep internals (private names, wire formats nobody writes by hand) out of README and agent
   files.
6. **Walkthrough:** walk the aspect with the user (below). **`--auto`: ping**, for example
   `Aspect 7/22 done — auth: 19 findings (6 bugs), 2 held. On to analytics.` Send it in the
   same message as the next dispatch. Under `--auto`, an ended turn is a stopped run.

**An anomaly is a finding until disproved.** Unexpected behaviour in a probe, test or
reproduction goes in the ledger as `✔ (likely)`, even when it looks like an artefact. Only a
real-input reproduction dismisses it.

**Context discipline is what lets this finish.** Raw findings, verifications and logs stay in
`$RUN`. This session reads the counts and the 15-line summaries, and pulls an entry in only to
rule on it or, in the walkthrough, to present it. A run that reads reports inline compacts every
few aspects.

### Walking an aspect (walkthrough only)

Message formats are in `references/formats.md` (Walkthrough messages).
1. **Open the aspect:** the position line, what the aspect covers in the user's terms (from
   the doc's TL;DR, with the doc path), and the counts per class and priority.
2. **Policy table.** The findings the policy settles go in one table with their proposed
   ruling: verified `✔`, no risk flag, UF none or minor, no conflict. The user confirms the
   table in one reply or names exceptions; an exception becomes a judgment item.
3. **Judgment items, one at a time**, most consequential first: a Must Fix, a risk flag or
   major UF, a consequential `✔ (likely)`, a promise the code breaks (the user decides which
   is wrong), a second-opinion disagreement, a recommendation to restructure an area, and
   anything the policy does not decide. Present each with:
   - the position line
   - a **scenario**: who does what, what happens today, what should happen. Never only
     internal mechanisms; if the scenario cannot be stated, investigate first
   - **prior art** from 3+ comparable tools for anything a user types or a script parses
   - **options** with one recommendation and its deciding trade-off, then "Recording, not
     implementing." Say when an option narrows a promise.
4. **After a ruling,** write the entry, update **Now**, and go straight to the next item. "Later"
   marks the entry `deferred`; deferred items return in Phase 7.
5. **Pushback.** Re-analyse from the scenario and the use cases. An earlier ruling, the current
   code and the status quo are not reasons in themselves. If the push holds, revise the entry
   in place; if not, show the concrete scenario it breaks.
6. **Close the aspect:** what was ruled (fix / todo / rejected / deferred), the readiness
   prompt under `--fix` (Phase 5), and the next aspect. Wait for the user's go.

## Phase 5 — Hand-off while reviewing (`--fix` only)

After each aspect is verified, run the readiness analysis. A finding is **ready** when all of
the following hold:

- it is verified, ruled `fix` (confirmed by the user, in the walkthrough), and not held
- everything in its Depends list is fixed or decided
- **its area is settled:** no queued or running aspect has a scope that covers its files
- its Touches do not overlap a batch in flight
- it is not a multi-area refactor; those wait until Phase 6 has named the theme they belong to

Group ready findings into batches of 3 to 8 in one area. In the walkthrough, propose them at
the aspect close ("ST-B1, ST-B5, ST-T2 are ready and independent of open items. Hand them to
w1?") and continue on the user's answer. Write `briefs/B-n.md` and deliver it to an idle
worker per crew's "Lead: the loop". Do not monitor it. On its report, integrate with
crew plus the additions in `references/workers.md`, running the check yourself, then return to
the review. Prioritise batches that remove code; hand-offs usually begin during tier 3.

**Bigger changes go through `plan` or `longshot`.** A finding or theme that spans areas,
changes a shared interface, or costs more than about half a day goes alone in its brief, marked
`Approach: plan` (or `longshot` for multi-hour work).

**Track the change budget.** After each integration, recount source lines as the baseline was
counted. Past the budget, bugs still go out, but every improvement and tidy-up not yet handed
off waits on one question: fix them anyway, or move them to the TODO? Ask it at the next aspect
close in the walkthrough; under `--auto` it is a wave item.

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

Under `--fix`, multi-area refactors now become batches or judgment items, according to the
themes and the fix policy.

In the walkthrough, synthesis is walked like an aspect: each competing pattern from the sweep
is a judgment item (which one wins), and the roadmap's Priorities are presented for the user
to reorder before they are written into the ledger.

## Phase 7 — Keep audit and the last decisions

Start once the review is complete and every ready batch has been handed off and integrated.
Without `--fix`, only the deferred walkthrough items remain: walk them as judgment items.

**Keep audit first**, because a fix that made the code worse looks just like one that made it
better. Split `<base>..HEAD` by area into at most 4 slices, each for a fresh `opus` agent with
the keep-audit prompt (`references/formats.md`), which never sees the rulings. It rates each
change `real fix`, `worthwhile`, `churn` or `worse` and lists behaviour changes no finding asked
for. Each `churn`, `worse` or unasked-for change becomes a keep-or-drop item; a drop is
reverted by a worker, and the Phase 8 regroup folds the revert away.

**Walkthrough:** walk the keep-audit items and the deferred items one at a time, as judgment
items.

**`--auto`:** present the keep-audit and held items in waves (format in
`references/formats.md`): each a scenario in the user's terms with options and a
recommendation, the most-unblocking first, each wave only mutually independent decisions. Record answers as `decided wave <n>`, re-run readiness, and
present the next wave while the new batches run. Stop when nothing is held or the user parks
the rest as TODO.

## Phase 8 — Final checks, harvest, regroup and report

Under `--fix`:

1. Run the check command on the integration branch yourself.
2. Run `code-review` over `<base>..HEAD` of the integration branch, with `--multi` when more
   than about 30 commits landed. Send the fixes to a worker as a final batch, then re-review
   only those fixes.
3. **Run the smoke list with real input**, after any drops, then `qa` over the user-facing
   changes. A check that did not run, with what was tried, goes first under Blocked on you,
   and the report does not call the run complete.
4. Run `doc --update` over the integrated range, under the docs rule, so the repo docs reflect
   what the fixes changed.

### Harvest

**Harvest with `doc`**, under the docs rule, whatever the repo's next reader needs and lacks:

- how the system works, where the repo lacks it: architecture, data flow, startup, state
  ownership
- the conventions the consistency sweep settled
- decisions from the waves that constrain future work, as ADRs if the repo keeps them
- the promises and the smoke list, in the agent instructions file (`AGENTS.md` or
  `CLAUDE.md`), so the next agent neither narrows a promise nor skips the check
- the roadmap

Leave behind the review mechanics (IDs, marks, batches, run rulings) and anything the code now
says. Under `--fix`, commit the harvest on the integration branch; otherwise leave it
uncommitted. **Move the open findings** to the end state the interview settled. For an issue
tracker, write the issue texts into the report; never create issues yourself.

### Regroup the history (`--fix` only)

Rebuild `<base>..HEAD` as feature commits on `codebase-review/regrouped`, following "Regroup
the history" in `references/workers.md`. Adopting it waits for the user's yes to the report.

### Report

Write the final report from the template in `references/formats.md` to
`.codebase-review/report.md` and print it in full, Blocked on you first. Do not remove worktrees
or delete branches.

### Delete the work folder

**Delete `.codebase-review/`** after checking that the ledger has no open entry, the harvest
commit or doc diff exists, and the report was printed here. If the end state is "the work
folder", or a check fails, keep it and say what holds it under Blocked on you; a later run
resumes and deletes it.

## Model per role

Pass `model` on every dispatch. An omitted model silently inherits the session's top tier.

| Role | Model |
|---|---|
| Recon (`Explore`) | `sonnet` |
| Aspect reviewer | `opus` for foundations, security, architecture and feature deep dives; `sonnet` for inventories (docs, dependencies, agent setup, tooling) |
| Verifier, consolidation | `sonnet` |
| Architecture and roadmap, keep audit | `opus` |

## Examples

### Example: onboarding to an inherited app, walkthrough

User: *"I'm new on this app and middleware. Review it thoroughly: architecture, state, startup,
tests, everything. Don't commit anything."*

Actions: recon and overview; `blind-spots` settles the middleware as reference only, 22
aspects, and open findings staying in the work folder; `review-plan`, plan approval. Then per
aspect: `auth` opens with its TL;DR and counts, the user confirms a 14-row policy table, and
walks 3 judgment items (a token kept after logout, a README promise the code breaks, a
restructure proposal); the next aspect is already verified when the user says go.

Result: every finding ruled by the user, a ranked TODO, docs harvested into `docs/`,
uncommitted, and the work folder kept, because its open findings are the user's TODO.

### Example: a library, review only

User: *"codebase-review this Swift package before I tag 1.0."*

Actions: recon tags it `library: UI component`; the plan takes Core, Library and UI component
library, with modules as feature units, so no client-app aspect is ever proposed. Skipped:
agent setup (no agent files).

Result: findings about accidental public API and an untested platform, and a roadmap toward 1.0.

### Example: independent review and fix with two workers

User: *"codebase-review --fix --auto. Big repo. Hold anything that changes what users see in a
major way. I'll run workers."*

Actions:
1. Interview: Active, so a 15% budget; a flow or default change is major. The smoke list fails
   one check on the baseline, which becomes the first finding.
2. Setup: worktree `../app-cr-w1` and clone `../app2`, each running `crew join <lead>`. Gate, yes.
3. Hand-offs from tier 3. A worker stops one fix that would change the saved format; it is held.
4. The keep audit rates 3 changes as churn. Wave 1 has those 3 and 5 held items; two are dropped.
5. `code-review --multi`, the smoke list and `qa`, `doc --update`, harvest, regroup.

Result: 64 per-finding commits regrouped into 14 feature commits, adopted on the user's yes.
All local, with 9 user-facing changes listed before → after. The remaining TODO is ranked.

## Troubleshooting

### The user is lost ("what are we on?", "are we fixing this now?")
**Cause:** the position line was skipped, or the walk drifted into implementation detail.
**Solution:** print the aspect table with the current aspect marked and the open items in it.
Restate that the conversation records rulings and that fixes run in worker batches.

### A finished project comes back with dozens of changes
**Cause:** the maturity question was skipped or answered Overhaul, or `rare` and `misuse`
findings were ruled fix.
**Solution:** re-ask the maturity question, re-rule the open findings against its default,
and let the keep audit put what already landed to the user as keep or drop.

### A core workflow breaks, but every test passes
**Cause:** recording, clicking or typing was only ever checked through unit tests and
in-process probes.
**Solution:** run the smoke list with real input. Turn the failure into a finding with a test,
and add the check to the smoke list if it was missing.

### A worker's branch won't fast-forward, or its green check fails here
See Troubleshooting in `references/workers.md`.

### Context runs out mid-run
**Solution:** re-read `.codebase-review/programme.md` (Now, Start, Workers, Batches) and the
ledger, then resume. If no plan approval is recorded, ask before continuing; never invent one.

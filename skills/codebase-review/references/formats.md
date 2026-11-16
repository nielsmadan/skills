# Formats and prompts

Fill the `{{...}}` slots. Keep the fixed lines verbatim: each one is there because a run broke
without it.

## programme.md

The resume point, in `.codebase-review/programme.md`. Write it for a reader who has
no conversation history.

```markdown
# <project> codebase review

**Now:** P4 · tier 3 · aspect `analytics` (12/24) · judgment item 2 of 4 · 2 batches in flight
**Next:** caching, then tests

## Framing
| Decision | Ruling | Date |
|---|---|---|
| Mode | walkthrough (default) or `--auto` | … |
| Repos reviewed | app (writable with --fix), middleware (read-only reference) | … |
| Open findings at end | roadmap doc `docs/roadmap.md` in the repo | … |
| Repo docs | wrong ADRs logged as D findings; fixed only in --fix | … |
| Maturity | Active (user: "still adding features") | … |
| Fix policy | bugs (common/plausible) fix; improvements fix if ≤ ½ day; major UF and risk flags held | … |
| Change budget | 15% source growth; past it, improvements and tidy-ups are held | … |
| Major user-facing means | changes a flow, a screen's content or a default a user would notice | … |
| Integration | branch `main` in <path>; ff-only | … |
| Promises | "Tab can be recorded" (README:12); "click a field to record" (user) | … |
| Smoke list | `just example`, real clicks and keys: click a recorder → it stays recording; ⌘K ⌘C records; … Baseline: 4/5 (click fails) | … |

## Start
Base: <repo> <branch> <sha> · Approved: <user's reply, date> · Started: <ISO>
Types: <path → type per repo or package> — <signals>
Size: source <n> · tests <n> · README <n> lines — `<the command that counted them>` · now: source +<n>%

## Aspects
| # | Aspect | Tier | Model | Scope (paths) | Doc | Status | Findings |
|---|---|---|---|---|---|---|---|
| 5 | startup | 2 | opus | src/App.tsx, src/contexts/User*, ios/, android/ | docs/startup.md | verified | 10B 13O 10T |

Aspect statuses: `queued → reviewing → verifying → verified`, then `walked` once the user has
ruled on it (walkthrough).

## Extensions and evidence
| Extension / selected skill path | Repo / package scope | Applies to aspects | Collector / versions / config / exclusions | Revision | Artifacts | Status |
|---|---|---|---|---|---|---|
| codebase-review-typescript / <path> | <repo> / <package> | architecture, feature reviews, hotspots | typescript-structure-v1 / <versions and options> | <sha> | <summary and raw paths> | planned |

Evidence statuses: `planned`, `complete`, `partial`, `unavailable`, `failed`, `stale`.
Record discovery conflicts and collection limits here. A guidance-only extension uses `N/A`
for collector and artifacts. Reuse evidence only when the complete collection identity matches.

## Skipped
- <aspect> (<catalog section>) — <one-line reason, e.g. "no network layer: the library does no I/O">

## Workers
| Name | Harness | Checkout | Branch | Baseline | State |
|---|---|---|---|---|---|
| w1 | claude | <path> (worktree) | crew/w1 | 1432 passed | busy B-3 |

## Batches
| Batch | Findings | Worker | Brief | State |
|---|---|---|---|---|
| B-3 | ST-B2, ST-B5, ST-T2 | w1 | briefs/B-3.md | handed off |

## Rulings
- R4 — <decision> — <why> — <cost if wrong>

## Blocked on you
- <check, merge or command> — <why> — <exact command>
```

Update **Now** and **Next** whenever the position moves.

## findings.md (the ledger and TODO)

One file serves as the record and as the user's TODO list. It has one section per aspect, plus a
Priorities section that the synthesis writes at the top. IDs are stable and never reused:
`<ASPECT-CODE>-<class><n>`. The classes are `B` bug, `O` improvement, `T` tidy-up and `D` doc
error.

```markdown
## startup (from [docs/startup.md](docs/startup.md), main @ 7f11450)

- [ ] **ST-B1** ✔ · Should Fix · Reach: common (every fresh install) · UF: none · Risk: none ·
  ruled: fix · B-3 — The config hook re-evaluates every flag with no user on the first download
  and overwrites the user's flags.
  Fix: pass the last evaluated user; skip the hook for the initial fetch.
  `src/services/FeatureFlags.ts:46-52,407-425` · Depends: — · Touches: FeatureFlags.ts
- [ ] **ST-B6** ✔ · Nice to Have · Reach: misuse (hand-edited prefs file) · UF: none · Risk:
  none · ruled: todo — A negative timeout in prefs crashes startup. Fix: clamp on load.
- [ ] **ST-O4** ✔ (likely) · ungraded · UF: major · Risk: default behaviour · held — Load fonts
  lazily; first paint changes from a branded splash to a plain one for ~200 ms. Scenario: … ·
  Depends: —
- [x] **ST-T2** ✔ · Nice to Have · UF: none · Risk: none · fixed 3b1c0de · audit: worthwhile —
  dead `isLogin` branch.
```

- **Priority:** use Review grading from SKILL.md; keep unconfirmed claims ungraded.
- **Reach** (bugs only): `common`, `plausible`, `rare` or `misuse`, with the trigger in
  brackets. Under Settled and Active, `rare` and `misuse` are ruled `todo`.
- **Risk** lists the risk flags from SKILL.md that the proposed fix trips, or `none`. Any flag
  rules the entry `held` (a judgment item, in the walkthrough). A worker that trips a new flag
  adds it, and the entry goes back to the user the same way.
- **Audit** is the keep-audit verdict on a fixed entry: `real fix`, `worthwhile`, `churn` or
  `worse`. The last two become wave items, and end as `kept wave <n>` or `dropped <revert sha>`.
- **Verification marks:** `✔` means the verifier confirmed it in the code. `✔ (likely)` means
  it was checked but not fully confirmed. No mark means it is the reviewer's reading only and
  must not be handed off.
- **UF** is the user-facing level: `none`, `minor` (visible but no decision needed: a fixed
  label, a removed flicker) or `major` (per the framing's definition). Every `minor` or `major`
  entry carries a **Scenario**: who does what, what they see today, and what they would see
  after the fix.
- **Statuses:** `open → verified → ruled: fix | todo | held → handed off (B-n) → fixed <sha>`.
  The other endings are `stopped (reason)`, `rejected (reason)` and `dup of <ID>`. A held entry
  gets `decided <wave>` once the user rules on it. In the walkthrough a ruling reads
  `proposed: fix | todo` until the user confirms it, then `ruled: … (you, <aspect>)`; `deferred`
  parks it for Phase 7, and `held` is not used.
- **Depends** names the IDs this finding cannot be fixed without. A finding that depends on a
  `held`, `proposed` or `deferred` entry is itself blocked until that entry is decided.
- A finding found again by a later aspect is merged into the existing entry, never duplicated.

## Aspect reviewer prompt

Use a `general-purpose` agent with the model from the plan. It writes two files and nothing else.

```
Review one aspect of a codebase and write it up. You have no prior context.

CODE:      {{repo paths, roles}} at {{branch}} @ {{sha}}. READ-ONLY: no edits, no git state
           changes, no installs. {{If the user has uncommitted edits: review the committed
           version via `git show <sha>:<path>` and do not mention the local edits.}}
DOC:       {{absolute path}}. Write exactly this file.
FINDINGS:  {{$RUN/findings-<aspect>.md}}. Write exactly this file.
SIBLINGS:  {{existing review docs and what each covers}}. Build on them, link to them, do not
           repeat them, and correct them where the code now differs (say so explicitly).
BOUNDARY:  {{out of scope: what other aspects own}}
EXTENSIONS: {{applicable skill paths, evidence paths, revision/scope and coverage limitations;
             none when no extension applies. Read this guidance and evidence; do not rerun
             collectors or start nested review workflows. Verify candidates against CODE.}}
PROMISES:  {{the framing's Promises}}. A fix that narrows one trips the first risk flag. Where
           the code breaks a promise, report the disagreement; never call the promise a doc error.

## Questions
{{Review grading section from SKILL.md}}

{{Risk flags section from SKILL.md}}

{{the aspect's questions from its catalog section in aspects.md, plus project-specific ones}}
Also answer: is it consistent (count each competing pattern with grep)? Do the repo's docs
and ADRs about this area match the code? What is tested?

## Doc
Open with a TL;DR of about 8 bullets. Use tables and mermaid diagrams over prose. Plain
English, no marketing words.

## Findings
Ranked, one per entry: class (bug / improvement / tidy-up / doc error),
priority (Must Fix / Should Fix / Nice to Have; apply the supplied Review grading rubric),
reach for bugs (common / plausible / rare / misuse, with the concrete trigger),
user-facing level (none / minor / major, with a scenario for minor and major),
path:line, the concrete failure or cost, and the smallest fix that removes it, with the risk
flags that fix trips (or none). Where a larger fix is tempting, name it and say why the smaller
one is enough.

## Rules
- Ground every claim in a path:line you actually read. Give the grep behind every count.
  Write "inferred" or "not verified" rather than guess.
- Behaviour a probe or test shows that you did not expect is a finding, even when it looks like
  an artefact of the probe. Report it as unconfirmed rather than explain it away.
- Do not dispatch sub-agents or launch other agent CLIs; do this work yourself.

Reply with at most 15 lines: the main conclusions, the finding counts per class, and what
you could not verify. Do not restate the findings.
```

## Verifier prompt

Use a `general-purpose` agent, `sonnet` by default. It never sees the reviewer's reasoning, only
the findings file.

```
Independently verify review findings against the code. You have no prior context.

CODE:      {{repo}} @ {{sha}}, read-only.
INPUT:     {{$RUN/findings-<aspect>.md}}
LEDGER:    {{findings.md}}, for duplicate detection only.
PROMISES:  {{the framing's Promises}}
OUTPUT:    {{$RUN/verified-<aspect>.md}}

For each finding, open the cited path:line and decide: ✔ confirmed, ✔ (likely) (plausible,
not fully confirmable from code), or ✗ rejected (with the line that disproves it). Fix wrong
line numbers. Mark duplicates of ledger entries with their ID. Check the user-facing level:
anything that changes what a user sees or does is at least minor. Check the reach: trace who
can actually produce the trigger, and downgrade it when only corrupt data, hostile input or API
abuse can. Check the fix against these risk flags and add any it trips:
{{Risk flags section from SKILL.md}}

Write OUTPUT in the findings.md entry format. Return only the counts per verdict.
Do not dispatch sub-agents or launch other agent CLIs. Modify nothing but OUTPUT.
```

## briefs/B-n.md

Use crew's brief envelope (`crew` skill, `references/brief.md`), with the report path
`.codebase-review/reports/B-<n>.md`. Its Items are the findings. Add these Rules after crew's
defaults:

```markdown
- Make the smallest change that removes the failure. A bug fix gets a test that would have
  caught the bug. A fix in an event monitor or handler gets at least one test that drives a
  real event through it.
- If the fix trips a risk flag not already on the entry, or grows well past the failure it
  removes, stop that finding: discard the change and report the flag with the simplest
  alternative. Do not finish it. The flags:
  <Risk flags section from SKILL.md, verbatim>
- These are promises. Never narrow one, and never edit a doc to drop or soften one:
  <the framing's Promises, verbatim>
- Doc changes follow the docs rule: fix what is wrong, add only what the doc's readers need,
  and keep internals out of README and agent files.
- Behaviour you did not expect, in a test, probe or run, goes in the report as a possible
  finding, even when it looks like an artefact.
- Run `code-review` over the batch: `--quick` for one or two small findings, comprehensive
  otherwise.
```

Items: the verbatim entries from findings.md, including Touches and Depends.

## Keep-audit prompt

Use a `general-purpose` agent on `opus`, one per slice. Give it the diffs and the findings'
claims, never the rulings or the reasons a fix was chosen.

```
Judge whether each change in a range made this code better. You have no prior context.

CODE:      {{repo}}; the slice is {{commits, each with its finding ID}} in {{base}}..{{tip}}.
           READ-ONLY.
CLAIMS:    {{per finding: the failure it claimed and the reach, from the ledger}}
CONTEXT:   {{maturity and what the user said about it}}
PROMISES:  {{the framing's Promises}}. A change that narrows one is worse, whatever it fixes.
OUTPUT:    {{$RUN/audit-<slice>.md}}

For each finding, read its commits' diff and the code around it, and classify the change:
- real fix: the claimed failure is reachable as described, and the change removes it simply
- worthwhile: not a bug fix, but the code or docs are clearly better for this project's maturity
- churn: no failure a user or maintainer would meet, or a change for its own sake
- worse: it adds risk, complexity or behaviour changes out of proportion to what it removes
Give the reach as you see it, and for churn or worse the simpler alternative (often: nothing).
Then list every behaviour change in the slice that no finding claimed, with the commit.

Ground each verdict in a path:line. Return only the counts per verdict and the number of
unclaimed behaviour changes. Do not dispatch sub-agents or launch other agent CLIs. Modify
nothing but OUTPUT.
```

## Walkthrough messages

Every message opens with the position line:
`P4 · aspect auth (7/22) · judgment item 2 of 3 · ledger: 140 ruled, 4 deferred · B-3 in flight`

**Opening an aspect**, then the policy table in the same message:

```markdown
## auth — how sign-in, sessions and tokens work
<3–5 lines from the doc's TL;DR, in the user's terms> · Doc: `.codebase-review/docs/auth.md`
17 findings: 3 bugs (1 Must Fix), 8 improvements, 5 tidy-ups, 1 doc error · 3 need your call

### Settled by the policy — confirm, or name the ones to discuss
| ID | Priority | What | Proposed |
|---|---|---|---|
| AU-B2 | Should Fix | Refresh token written to the crash log (plausible: any crash after sign-in) | fix |
| AU-T1 | Nice to Have | Two copies of the expiry check | todo |
```

**A judgment item:**

```markdown
**AU-O3 · Sign-out keeps the session on other tabs** · Should Fix · UF: major
Scenario: <who, what they do, what they see today, what they should see>.
Prior art: <3+ tools, cited, when it is something a user types or a script parses>.
Options: a) <option> (recommended — <the trade-off that decides it>) b) <option> c) TODO.
Recording, not implementing.
```

**Closing an aspect:** what was ruled (fix / todo / rejected / deferred, with IDs), anything a
worker report changed, the readiness prompt under `--fix`, the budget question if it is due,
and `Next: <aspect> — <one line on what it covers>. Ready when you are.`

## Decision wave (`--auto`)

Present one wave as a single message, then use the harness's question tool for the choices,
four at most per call, keeping the wave's order.

```markdown
## Decision wave 1 of ~3 — 7 held changes; 11 findings wait on them

**1. ST-O4 · Lazy font loading** (unblocks ST-O1, ST-O10)
Today: <scenario as the user experiences it>. After: <what changes for users>.
Options: a) fix as proposed (recommended — <decisive trade-off>) b) <variant> c) keep as is → TODO.

**2. RE-O3 · Recording reset counter** (audit: churn · 2 commits, +84 lines)
Changed: <what the change does, in the user's terms>. Audit: <the auditor's reason, one line>.
Options: a) drop it (recommended — <why>) b) keep it.
```

Order a wave so that the decisions unlocking the most dependents come first. The next wave holds
only the decisions that became decidable or changed shape after this wave's answers.

## Final report

```markdown
# <project> codebase review — complete

<One sentence: what state everything is in.>

## Blocked on you
1. **<item>** — <why> — `<exact command>`

## User-facing changes
| Change | What users see now | Finding | Commit |
|---|---|---|---|
| <one line> | <before → after, in the user's terms> | ST-B2 | 3b1c0de |
Held or deferred and still undecided: <IDs, one line each, or "none">.

## Judgment calls and risk flags
| Change | Flag or audit verdict | Simpler alternative | Decided | Commit |
|---|---|---|---|---|
| <one line> | persisted format / churn / … | <what was not done> | wave 1 / aspect auth | 3b1c0de |
Growth against the baseline: source +<n>% (budget <n>%), tests +<n>%, README +<n>%.

## Behaviour changes no finding asked for
<From the keep audit, each with its commit and what was decided, or "none".>

## Other changes
<Grouped by theme, one line per group with commit count and IDs: "Token leaks closed in
logging and crash reports (6 commits: AU-B2, AU-B3, ER-B5 …)".>

## History
<n> per-finding commits regrouped into <m> feature commits on `codebase-review/regrouped`;
the tree is identical to <integration branch> and the check passes. One line per feature
commit with its IDs. To adopt it (rewrites <integration branch>, so it waits for your yes):
`git branch codebase-review/full <branch> && git reset --keep codebase-review/regrouped`

## Review coverage
<aspects done, with the doc path for each; findings per class: found / verified / fixed /
TODO / rejected.>
Smoke list with real input: baseline <n/m> · final <n/m> · not run: <check — what was tried>.

## Top of the TODO
<the roadmap's first five items, each with cost and finding IDs.>

## Where things are
Work folder: `.codebase-review/` (kept: <what still holds it> | deleted). Harvested into: <repo doc paths, committed or not>. Open findings moved to: <end state>. Integration branch: <branch> <base>..<tip>
(<n> commits). Workers: <branch and path each>, with the cleanup commands.
Nothing was pushed.
```

Without `--fix`, drop every section about changes and History, and lead with Review coverage
and Top of the TODO.

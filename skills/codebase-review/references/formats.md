# Formats and prompts

Fill the `{{...}}` slots. Keep the fixed lines verbatim: each one is there because a run broke
without it.

## programme.md

The resume point, in `<docs-root>/codebase-review/programme.md`. Write it for a reader who has
no conversation history.

```markdown
# <project> codebase review

**Now:** P4 · tier 3 · aspect `analytics` (12/24) · 2 batches in flight
**Next:** caching, then tests

## Framing
| Decision | Ruling | Date |
|---|---|---|
| Repos reviewed | app (writable with --fix), middleware (read-only reference) | … |
| Docs root | ~/work/<project>/docs (outside the repos) | … |
| Repo docs | wrong ADRs logged as D findings; fixed only in --fix | … |
| Fix policy | bugs + tidy-ups fix; improvements fix if ≤ ½ day; major UF held | … |
| Major user-facing means | changes a flow, a screen's content or a default a user would notice | … |
| Integration | branch `main` in <path>; ff-only | … |

## Start
Base: <repo> <branch> <sha> · Approved: <user's reply, date> · Started: <ISO>

## Aspects
| # | Aspect | Tier | Model | Scope (paths) | Doc | Status | Findings |
|---|---|---|---|---|---|---|---|
| 5 | startup | 2 | opus | src/App.tsx, src/contexts/User*, ios/, android/ | app/startup.md | verified | 10B 13O 10T |

Aspect statuses: `queued → reviewing → verifying → verified`.

## Workers
| Name | Harness | Checkout | Branch | Baseline | State |
|---|---|---|---|---|---|
| w1 | claude | <path> (worktree) | codebase-review/w1 | 1432 passed | busy B-3 |

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
## startup (from [app/startup.md](app/startup.md), main @ 7f11450)

- [ ] **ST-B1** ✔ · high · UF: none · ruled: fix · B-3 — The config hook re-evaluates every
  flag with no user on the first download and overwrites the user's flags.
  Fix: pass the last evaluated user; skip the hook for the initial fetch.
  `src/services/FeatureFlags.ts:46-52,407-425` · Depends: — · Touches: FeatureFlags.ts
- [ ] **ST-O4** ✔ (likely) · med · UF: major · held — Load fonts lazily; first paint changes
  from a branded splash to a plain one for ~200 ms. Scenario: … · Depends: —
- [x] **ST-T2** ✔ · low · UF: none · fixed 3b1c0de — dead `isLogin` branch.
```

- **Verification marks:** `✔` means the verifier confirmed it in the code. `✔ (likely)` means
  it was checked but not fully confirmed. No mark means it is the reviewer's reading only and
  must not be handed off.
- **UF** is the user-facing level: `none`, `minor` (visible but no decision needed: a fixed
  label, a removed flicker) or `major` (per the framing's definition). Every `minor` or `major`
  entry carries a **Scenario**: who does what, what they see today, and what they would see
  after the fix.
- **Statuses:** `open → verified → ruled: fix | todo | held → handed off (B-n) → fixed <sha>`.
  The other endings are `stopped (reason)`, `rejected (reason)` and `dup of <ID>`. A held entry
  gets `decided <wave>` once the user rules on it.
- **Depends** names the IDs this finding cannot be fixed without. A finding that depends on a
  `held` entry is itself blocked until that entry is decided.
- A finding found again by a later aspect is merged into the existing entry, never duplicated.

## Aspect reviewer prompt

Use a `general-purpose` agent with the model from the plan. It writes two files and nothing else.

```
Review one aspect of a codebase and write it up. You have no prior context.

CODE:      {{repo paths, roles}} at {{branch}} @ {{sha}}. READ-ONLY: no edits, no git state
           changes, no installs. {{If the user has uncommitted edits: review the committed
           version via `git show HEAD:<path>` and do not mention the local edits.}}
DOC:       {{absolute path}}. Write exactly this file.
FINDINGS:  {{$RUN/findings-<aspect>.md}}. Write exactly this file.
SIBLINGS:  {{existing review docs and what each covers}}. Build on them, link to them, do not
           repeat them, and correct them where the code now differs (say so explicitly).
BOUNDARY:  {{out of scope: what other aspects own}}

## Questions
{{aspect questions from aspects.md, plus project-specific ones}}
Also answer: is it consistent (count each competing pattern with grep)? Do the repo's docs
and ADRs about this area match the code? What is tested?

## Doc
Open with a TL;DR of about 8 bullets. Use tables and mermaid diagrams over prose. Plain
English, no marketing words.

## Findings
Ranked, one per entry: class (bug / improvement / tidy-up / doc error), severity,
user-facing level (none / minor / major, with a scenario for minor and major),
path:line, the concrete failure or cost, and a concrete fix.

## Rules
- Ground every claim in a path:line you actually read. Give the grep behind every count.
  Write "inferred" or "not verified" rather than guess.
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
OUTPUT:    {{$RUN/verified-<aspect>.md}}

For each finding, open the cited path:line and decide: ✔ confirmed, ✔ (likely) (plausible,
not fully confirmable from code), or ✗ rejected (with the line that disproves it). Fix wrong
line numbers. Mark duplicates of ledger entries with their ID. Check the user-facing level:
anything that changes what a user sees or does is at least minor.

Write OUTPUT in the findings.md entry format. Return only the counts per verdict.
Do not dispatch sub-agents or launch other agent CLIs. Modify nothing but OUTPUT.
```

## briefs/B-n.md

A worker executes it without ever having seen this conversation.

```markdown
# Batch B-<n>: <theme>

Worker: <name> · Checkout: <path> · Branch: codebase-review/<name>
Base: integration branch <I> must contain <sha>. Catch up first (workers.md, Syncing).
Check command: <cmd> · Commit convention: <feat/fix/chore, no scopes, no body | repo's own>

## Rules
- If a finding's premise does not match the code, stop that finding and report it. Do not
  adapt the fix to fit.
- Confirm the new tests actually ran: the count moved, or the names appear in the output.
- Read exit codes directly, never through a pipe.
- One commit per finding; fold the code-review fixes into the commit they belong to.
- Before reporting, rebase onto the lead's current tip and re-run the check command.
- Do not push. Do not touch <I> or any repo not named here.
- Report to <lead-name>: commits mapped to IDs, the check summary after the rebase, and the
  stopped findings with reasons.

## Findings
<verbatim entries from findings.md, including Touches and Depends>
```

## Decision wave

Present one wave as a single message, then use the harness's question tool for the choices,
four at most per call, keeping the wave's order.

```markdown
## Decision wave 1 of ~3 — 7 held changes; 11 findings wait on them

**1. ST-O4 · Lazy font loading** (unblocks ST-O1, ST-O10)
Today: <scenario as the user experiences it>. After: <what changes for users>.
Options: a) fix as proposed (recommended — <decisive trade-off>) b) <variant> c) keep as is → TODO.
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
Held and still undecided: <IDs, one line each, or "none">.

## Other changes
<Grouped by theme, one line per group with commit count and IDs: "Token leaks closed in
logging and crash reports (6 commits: AU-B2, AU-B3, ER-B5 …)".>

## Review coverage
<aspects done, with the doc path for each; findings per class: found / verified / fixed /
TODO / rejected.>

## Top of the TODO
<the roadmap's first five items, each with cost and finding IDs.>

## Where things are
Docs: <root>. Ledger/TODO: <path>. Integration branch: <branch> <base>..<tip>
(<n> commits). Workers: <branch and path each>, with the cleanup commands.
Nothing was pushed.
```

Without `--fix`, drop User-facing changes and Other changes, and lead with Review coverage and
Top of the TODO.

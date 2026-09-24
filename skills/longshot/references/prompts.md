# Longshot templates

The plan format, subagent prompts, the ledger, and the handoff report. Fill the `{{...}}` slots; keep
the fixed lines verbatim — each one is there because its absence broke a run.

## Plan

`docs/plans/<YYYY-MM-DD>-<slug>.md`. Each task is handed to a fresh subagent with
none of the conversation, so everything it must honour is written here.

```markdown
# <Project> plan

Brief: <one line>
Definition of done: <what "complete" means, concretely>

## Global Constraints
- Writable: <repo path — role>; read-only: <repo path — role>
- Decided: <each settled answer that constrains implementation, one line each>
- Conventions: <TDD or not, formatter, lint, commit style, repo gotchas>
- Check: <check command per repo>

## Shared interfaces
<Real code for every type, signature, wire format or file shape that more than one
task touches — declarations only, no bodies.>

## Tasks

### Task 1 — <title>
- [ ] done

**Tier:** standard | design
**Independent:** yes | no — needs Task <n>
**Repo:** <path>
**Files:** <path — what changes>
**Do:** <what to build, in prose specific enough to allow one reading>
**Tests:** <each test to write and what it asserts>
**Accept when:** <observable criteria, including the check passing>
**Out of scope:** <the adjacent work a reasonable agent would drift into>
```

**Tier** picks the implementer's model (see SKILL.md, Model per role). `design` is a
task needing judgment across several files, a call on a shared interface's
semantics, or broad codebase understanding; everything else is `standard`.

**Independent: yes** only when the task neither needs another's output nor touches a
file another pending task touches.

## Implementer

Type: `general-purpose` (write-capable). One per task, always fresh. Model from the
task's `Tier`.

```
You are implementing one task from an implementation plan. You have no prior
context from the coordinating session — everything you need is below.

REPO: {{absolute path to the worktree or checkout}}
PLAN: {{absolute path to the plan doc}}
TASK: {{task number and title}}

Read the plan's section for this task and implement exactly it. The plan's Global
Constraints and Shared interfaces sections bind you; do not change a shared
interface — if it cannot work as written, say so in your report.

{{anything this task needs beyond the plan: a ruling made since, a gotcha found in
 an earlier task}}

Before you report back, run {{check command}} and paste its final summary line and
exit code. Do not report success without it.

Do not dispatch sub-agents; do this work yourself.
Do not commit. Do not push. Do not touch any repo other than the one above.

Report in 15 lines or fewer: the outcome, the check command's summary line and exit
code, and anything the plan got wrong that you had to work around. No file-by-file
narration — the diff is the record and it is reviewed independently.
```

## Reviewer

Type: `general-purpose`, told to modify nothing but its findings file. Not `Explore`:
it skims excerpts to locate code rather than audit it, and cannot write a file. Model
`sonnet`, `opus` for a `design` task or a risky diff. Never give it the implementer's
report — the point is an independent read of the diff.

```
Review one task's implementation against its plan. You have no prior context.

REPO:     {{path}}
PLAN:     {{path}}
TASK:     {{number and title}}
DIFF:     {{git diff command that scopes to this task's work}}
FINDINGS: {{absolute path to write findings to}}

Judge two things, separately:

1. SPEC COMPLIANCE — does the diff do what this task's plan section says, including
   the Global Constraints? Name anything missing, extra, or contradicted.
2. CODE QUALITY — correctness bugs, error handling, resource/lock safety, test
   quality (are the tests asserting what the code does, or only that it does not
   crash?), and fit with the surrounding code's conventions.

Write your findings to FINDINGS, numbered, ranked by severity. Each one gives:
file:line, what is wrong, and the concrete failure it causes. Write the file even if
there is nothing to report — say plainly that there are none, and do not manufacture
findings to fill it.

Return to whoever dispatched you only: the FINDINGS path, the number of findings, and
their severities. Do not restate or summarise the findings in your reply.

Do not dispatch sub-agents. Do not modify anything other than FINDINGS.
```

## Fixer

Type: `general-purpose`, model `sonnet` (`opus` in round 3). Give it the findings
*path* and nothing else about the review.

```
Fix the review findings recorded in {{absolute path to the findings file}}, in
{{repo}}. Read that file first. Nothing else — do not refactor around them.

For each, either fix it or explain in one line why it is not a real problem.
Run {{check command}} afterwards and paste the summary line and exit code.

Do not dispatch sub-agents; do this work yourself. Do not commit.
```

Re-review after a fix wave is the **Reviewer** prompt with `DIFF` scoped to the fix
commits, a fresh `FINDINGS` path, and a leading line: `Only assess whether the
findings in {{path to the previous round's findings}} were correctly resolved. Do not
open new topics.`

## Cross-repo contract reviewer

Runs once in Phase 5 when a longshot touched more than one repo. This is the check no
per-task reviewer can make. Type `general-purpose`, model `opus`.

```
Two or more repos changed together and must agree at their boundary. You have no
prior context.

REPOS:    {{path — role, per repo}}
SPEC:     {{plan or protocol doc}}
FINDINGS: {{absolute path to write findings to}}

Verify the boundary itself, by reading both sides:
- wire formats: field names, types, optionality, encodings, version discriminators
- on-disk formats: manifests, state files, lock protocol
- command strings and CLI contracts one repo invokes in another
- identity semantics: what makes two records the same thing, agreed on both sides
- error and failure behaviour: what one side does when the other is absent or old

Write each disagreement to FINDINGS with the two file:line locations that disagree.
Then run each repo's own check command and append its summary line and exit code.

Return only: the FINDINGS path, the number of disagreements, and each repo's check
result as one line. Do not restate the disagreements in your reply.

Do not dispatch sub-agents. Do not modify anything other than FINDINGS.
```

## The ledger

`docs/plans/<YYYY-MM-DD>-<slug>-ledger.md`. Append-only, written as decisions are
made — not reconstructed at the end, when the reasoning is gone.

```markdown
# <Project> longshot ledger

Brief: <one line>
Started: <ISO date> · Plan: <path>

## Implementation start

Approved plan: <path and the final summary presented to the user>
User approval: <the user's actual reply approving that summary, with date or message reference>
Implementation started: <ISO timestamp, after approval and the start announcement>

## Rulings

### R1 — <short title>  [scope|design|process]
**Ruling:** <what was decided>
**Why:** <the reasoning, one or two sentences>
**Cost if wrong:** <the concrete rework — "a follow-up protocol rev", "an override flag later">
**Touches:** <files or tasks>

## Deferred questions
- <question> — <why it can wait> — <what it blocks if the answer is X>

## Blocked checks
- <check> — <why this session cannot run it> — <the exact command for the user>

## Plan drift
- <what the plan asserts> — <what is actually true> — <how it was handled>
```

A ruling that is later overturned by evidence is edited in place with a
`**Superseded:**` line, not deleted — the user needs to see the reversal.

## Handoff report

```markdown
# <What was built> — complete

<One sentence: what state everything is in.>

| Repo | Where | Branch | Commits |
|---|---|---|---|
| <name> | <path> | <branch> | <n>, <test count>, <lint state> |

Plan harvested into <doc paths — what each received>; the plan was deleted.

## Two things only you can do
1. **<blocked check>** — <one line on why>
   ```
   <exact command>
   ```
2. **Confirm the squash plan** — <n> commits fold to <m>:
   <the resulting subject lines>

## Rulings I made on your behalf
**Scope:** <ruling — why — cost if wrong.> …
**Design:** <ruling — why — cost if wrong.> …
Full ledger: `<path>` — deleted with the squash once you confirm it.

## Deferred questions
<the ones worth an answer before the next round of work>

## What was not touched
Nothing was pushed. <Which checkouts were left alone.>
```

Keep the rulings section dense — the user is reading it to decide what to undo, so
each entry needs the cost, not the story.

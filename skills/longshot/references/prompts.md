# Longshot templates

Subagent prompts, the ledger, and the handoff report. Fill the `{{...}}` slots; keep
the fixed lines verbatim — each one is there because its absence broke a run.

## Implementer

Type: `general-purpose` (write-capable). One per task, always fresh.

```
You are implementing one task from an implementation plan. You have no prior
context from the coordinating session — everything you need is below.

REPO: {{absolute path to the worktree or checkout}}
PLAN: {{absolute path to the plan doc}}
TASK: {{task number and title}}

Read the plan's section for this task and implement exactly it. The plan's Global
Constraints section binds you.

{{project conventions that matter here: TDD or not, commit style, formatter,
 lint command, test command, any repo-specific gotcha from AGENTS.md}}

Out of scope: {{adjacent things a reasonable agent would drift into}}

Before you report back, run {{check command}} and paste its final summary line and
exit code. Do not report success without it.

Do not dispatch sub-agents; do this work yourself.
Do not commit. Do not push. Do not touch any repo other than the one above.

Report: what you changed (file by file), the check output, and anything the plan
got wrong that you had to work around.
```

## Reviewer

Type: `Explore` (read-only). Never give it the implementer's report — the point is an
independent read of the diff.

```
Review one task's implementation against its plan. You have no prior context.

REPO: {{path}}
PLAN: {{path}}
TASK: {{number and title}}
DIFF: {{git diff command that scopes to this task's work}}

Judge two things, separately:

1. SPEC COMPLIANCE — does the diff do what this task's plan section says, including
   the Global Constraints? Name anything missing, extra, or contradicted.
2. CODE QUALITY — correctness bugs, error handling, resource/lock safety, test
   quality (are the tests asserting what the code does, or only that it does not
   crash?), and fit with the surrounding code's conventions.

For each finding give: file:line, what is wrong, and the concrete failure it causes.
Rank by severity. Say plainly if there are none — do not manufacture findings.

Do not dispatch sub-agents. Do not modify anything.
```

## Fixer

Type: `general-purpose`. Give it the findings and nothing else about the review.

```
Fix these review findings in {{repo}}. Nothing else — do not refactor around them.

{{findings, verbatim, numbered}}

For each, either fix it or explain in one line why it is not a real problem.
Run {{check command}} afterwards and paste the summary line and exit code.

Do not dispatch sub-agents; do this work yourself. Do not commit.
```

Re-review after a fix wave is the **Reviewer** prompt with `DIFF` scoped to the fix
commits and a leading line: `Only assess whether these findings were correctly
resolved: {{findings}}. Do not open new topics.`

## Cross-repo contract reviewer

Runs once in Phase 5 when a longshot touched more than one repo. This is the check no
per-task reviewer can make.

```
Two or more repos changed together and must agree at their boundary. You have no
prior context.

REPOS: {{path — role, per repo}}
SPEC:  {{plan or protocol doc}}

Verify the boundary itself, by reading both sides:
- wire formats: field names, types, optionality, encodings, version discriminators
- on-disk formats: manifests, state files, lock protocol
- command strings and CLI contracts one repo invokes in another
- identity semantics: what makes two records the same thing, agreed on both sides
- error and failure behaviour: what one side does when the other is absent or old

Report each disagreement with the two file:line locations that disagree. Then run
each repo's own check command and report the results.

Do not dispatch sub-agents. Do not modify anything.
```

## The ledger

`docs/plans/<YYYY-MM-DD>-<slug>-ledger.md`. Append-only, written as decisions are
made — not reconstructed at the end, when the reasoning is gone.

```markdown
# <Project> longshot ledger

Brief: <one line>
Started: <ISO date> · Plan: <path>

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
Full ledger: `<path>`

## Deferred questions
<the ones worth an answer before the next round of work>

## What was not touched
Nothing was pushed. <Which checkouts were left alone.>
```

Keep the rulings section dense — the user is reading it to decide what to undo, so
each entry needs the cost, not the story.

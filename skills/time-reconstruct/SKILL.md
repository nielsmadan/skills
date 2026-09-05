---
name: time-reconstruct
description: Reconstruct what you worked on from git history for time tracking — list each task with its commit (end) time and a real assessment of how complex the work was, based on what the diff actually does, not its size. Use when you forgot to track time and need to reconstruct it, or say "reconstruct my time", "what did I work on", "timesheet from git", "time tracking from commits", "how complex were my commits".
model: sonnet
effort: low
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Time Reconstruct

Reconstruct a work log from git history for client time tracking. The output is a list of tasks, each with the commit time (when you finished it) and an honest complexity read of what the work actually involved — so you can decide for yourself how many hours each was worth.

This skill does **not** estimate durations or hours. It gives end times and complexity; the user converts that to time.

## Instructions

### Step 1: Determine scope

Ask the user for the range if not given. Accept natural language ("since Monday", "last week", "today", "since my last commit yesterday afternoon"). Translate to a git revision range or `--since`/`--until`.

Default to the user's own commits. Get their email with `git config user.email` and filter with `--author`. Only drop the author filter if the user says so (e.g. solo repo, or they want everyone's work).

Examples:
- `git log --author="$(git config user.email)" --since="last monday" --pretty=...`
- `git log --author="$(git config user.email)" main..feature-branch --pretty=...`

### Step 2: Get the commit list

List commits in the range, oldest first, with full author date:

```bash
git log --author="$(git config user.email)" --since="<range>" --reverse \
  --pretty=format:'%h%x09%ad%x09%s' --date=format:'%Y-%m-%d %H:%M'
```

This gives `hash <tab> date time <tab> subject` per line. Each commit's time is the **end time** for that piece of work.

### Step 3: Read what each commit actually did

For each commit, inspect the real content — do NOT judge complexity by line count:

```bash
git show --stat <hash>     # files touched, scope
git show <hash>            # the actual diff
```

For large diffs, use `git show <hash> -- <path>` or `git show <hash> --stat` first to triage, then read the substantive files. Skip lockfiles, generated code, vendored deps, and bulk formatting when judging complexity (but note them, since they still took time to generate/verify).

Assess **what was done**, not how many lines changed. The same line count can be trivial or hard:
- A 500-line generated migration or a dependency bump = trivial.
- A 30-line concurrency fix, a tricky algorithm, or a cross-cutting refactor = high.

Judge complexity on signals like:
- **Conceptual difficulty** — novel logic, algorithms, concurrency, edge-case handling vs. boilerplate/CRUD/config.
- **Novelty & uncertainty** — new ground (likely lots of trial-and-error) vs. repeating an established pattern.
- **Integration surface** — how many modules/systems it touches and coordinates.
- **Likely debugging effort** — does the change smell like it needed investigation (bug fixes, "fix", reverts, follow-up commits to the same area)?
- **Mechanical vs. thinking** — renames, moves, generated output, and reformatting are low even when huge.

Assign a level: **Trivial / Low / Medium / High / Very High**, with a one-line justification grounded in what the diff does.

### Step 4: Produce the table and summary

Output a markdown table, oldest to newest:

```markdown
| Date | End | Task | Complexity | What it involved |
|------|-----|------|-----------|------------------|
| 2026-06-05 | 11:20 | Auth token refresh | High | New refresh-rotation logic with concurrency guard; touches auth + http client |
| 2026-06-05 | 14:30 | Settings page copy | Trivial | Text/label tweaks, no logic |
```

- **Task**: a clear human description of the work — synthesize it from the diff, don't just copy the commit subject (especially for terse subjects).
- Group trivially-related back-to-back commits into one row if they're clearly one task (e.g. a feature + its immediate fixup), but keep distinct tasks separate.

Then write a short **summary** below the table:
- One or two sentences on the overall shape of the work (what was built/fixed across the range).
- A complexity tally (e.g. "1 high, 2 medium, 3 trivial").
- Flag anything ambiguous — gaps where you can't tell what happened, or commits whose complexity is genuinely uncertain — so the user can fill in.

Print everything in chat. Do not write it to a file unless asked.

## Examples

### Example 1: Reconstruct last week

User says: "I forgot to track time — reconstruct what I did last week"

Actions:
1. `git config user.email` → filter author. Range = `--since="last monday" --until="last friday"`.
2. `git log` with that filter, `--reverse`, formatted with hash/date/subject.
3. For each commit: `git show --stat` then `git show` to read the diff; assess complexity from what it does.
4. Emit the table (date, end time, task, complexity, what-it-involved) + summary with a complexity tally.

Result: a per-task log the user maps to hours themselves.

### Example 2: One branch's work

User says: "Give me a complexity breakdown of my commits on the billing branch"

Actions:
1. Range = `main..billing` (confirm the base with the user if unclear), author = user.
2. Same read-and-assess loop, then table + summary.

## Troubleshooting

### Too many commits / huge diffs to read fully
**Cause:** Wide range or large generated changes.
**Solution:** Triage with `git show --stat` first; read only substantive files. Note generated/vendored bulk as low complexity rather than reading it line by line. If the range is very large, confirm the scope with the user before grinding through everything.

### Commit messages are terse or misleading
**Cause:** Subjects like "wip" or "fix" don't describe the work.
**Solution:** Derive the task description from the diff itself, not the subject. The whole point is to judge actual content.

### Can't tell how complex something was
**Cause:** A diff is ambiguous, or work spanned commits/uncommitted exploration.
**Solution:** Mark it uncertain in the "What it involved" column and call it out in the summary so the user can correct it — don't fabricate confidence.

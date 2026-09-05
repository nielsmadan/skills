---
name: squash-commits
description: Squash unpushed commits into clean, higher-level feat/fix/chore commits that follow the project commit policy. Use when local history has too many small/WIP/fixup commits (common after superhuman or gsd runs), or the user says "squash commits", "squash my commits", "tidy history", "clean up commits", "combine commits before pushing".
argument-hint: '[--conservative] [base-ref]'
effort: medium
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Squash Commits

Combine the unpushed commits on the current branch into the smallest set of clean,
self-contained commits, each adhering to the commit policy (`feat`/`fix`/`chore`,
**no scopes**, subject only). Superhuman/gsd-style runs leave many superfluous
commits — initial work, follow-up fixes, tests, docs — that belong together as one
higher-level feature commit.

This skill rewrites history, so it **proposes a plan and only proceeds after the user
confirms**. It never touches the branch ref until the very last step, and only ever
operates on **unpushed** commits. It creates no backup tags or stashes; the original tip
is recoverable from the branch reflog after the verified ref move.

## Usage

```
/squash-commits                  # aggressive feature-level grouping of unpushed commits
/squash-commits --conservative   # only fold obvious WIP/fixup commits into their parent
/squash-commits origin/main      # use an explicit base instead of auto-detecting unpushed range
```

## Hard rules

- **Never rewrite pushed commits.** Only squash commits not present on any remote.
- **Never reorder commits.** Groups are contiguous runs in original order. Reordering
  risks conflicts and changes intent.
- **The final tree must be byte-identical** to the original tip before the branch is
  moved. Squashing changes *history*, never *content*. Verify this and abort if it differs.
- **Require a clean working tree.** If there are uncommitted changes, stop without
  creating a stash. Let the user decide how to preserve their work before re-running.
- **No interactive rebase.** `git rebase -i` is unsupported in this harness. Use the
  rebuild method below.
- **Leave no persistent helper state.** Do not create backup tags, branches, or stashes.
- **Leave no temporary files.** Use subject-only commit messages, so no message files are
  needed. Git's normal reflog and unreachable-object retention are not helper state and
  can be left to normal expiry/GC.

## Workflow

### Step 1: Preconditions

```bash
git status --porcelain      # MUST be empty — else stop without changing Git state
git rev-parse --abbrev-ref HEAD   # current branch (save as BRANCH)
```

If the working tree is dirty, stop: "Working tree has uncommitted changes. Preserve or
commit them as you prefer, then re-run `/squash-commits`. This skill did not create a
stash or change the working tree."

### Step 2: Determine the unpushed range

Find the commits to squash and the base (the commit they sit on top of).

- **If a base ref is passed as an argument** (e.g. `origin/main`, a SHA): `BASE` = that ref.
  Range = `BASE..HEAD`.
- **Otherwise auto-detect unpushed commits:**
  ```bash
  git rev-list HEAD --not --remotes --oneline
  ```
  This lists commits reachable from HEAD that are on no remote-tracking branch (newest
  first). The oldest of these is the last line; `BASE` = its parent (`<oldest>^`).
  - If the list is **empty** → nothing to squash. Tell the user and stop.
  - If it includes the **root commit** (no parent), or there are **no remotes at all**,
    auto-detection is unreliable — ask the user for an explicit base ref (e.g.
    `origin/main`) and re-run, or confirm a base before continuing.

Save `ORIG_TIP = git rev-parse HEAD`.

**Check for merge commits** in the range:
```bash
git rev-list --merges BASE..HEAD
```
If non-empty, stop: this skill only handles linear history. Tell the user the range
contains merge commits and squashing them is out of scope.

If the range has **0 or 1 commit**, there is nothing to combine — say so and stop.

### Step 3: Read and analyze the commits

List the range oldest→newest and read what each commit does:
```bash
git log --reverse --format='%h %s' BASE..HEAD
git log --reverse --stat BASE..HEAD     # add -p for full diffs if grouping is unclear
```

For each commit note: its subject, the files it touches, and whether it's substantive
work, a fixup of an earlier commit, tests, or docs.

### Step 4: Propose a grouping plan

Partition the commits into **contiguous groups**, each becoming one new commit.

**Default (aggressive, feature-level):** collapse adjacent commits that serve one logical
feature into a single commit — initial implementation + its follow-up fixes + its tests +
its docs become one. The goal is the smallest set of commits that each stand on their own.

**`--conservative`:** only fold obvious checkpoint/WIP/fixup commits (e.g. "wip", "fix
typo", "address review", "oops") into the substantive commit they belong to. Leave
genuinely distinct logical commits as separate groups.

For each group, write a new message per the commit policy:
- Type is exactly one of `feat` / `fix` / `chore`. **No scopes, no parentheses** — write
  `feat: add login button`, not `feat(ui): ...`.
  - `feat` — a user-noticeable addition. `fix` — a user-noticeable bug fix.
    `chore` — everything else (refactor, tests, docs, internal).
  - If a group mixes a feature and an unrelated fix, that's a sign they shouldn't be one
    group — split them.
- Omit the body. Use a single subject line so this workflow needs no temporary message
  files.

Present the plan as a before→after table and stop for confirmation:

```markdown
## Squash plan (BASE = <short-sha or ref>, <N> commits → <M> commits)

### Group 1 → `feat: <new subject>`
- `abc123` wip feat1
- `def456` fix feat1 typo
- `ghi789` add tests for feat1

### Group 2 → `feat: <new subject>`
- `jkl012` start feat2
- `mno345` fix feat2

Proceed? This rewrites unpushed history. The original tip will remain recoverable from
the branch reflog; no backup tag or stash will be left behind.
```

**Wait for explicit user confirmation.** Do not proceed otherwise. If the user wants
edits to the grouping or messages, revise and re-present.

### Step 5: Preserve the recovery point without helper refs

Do not create anything. Keep the recorded `ORIG_TIP`: the original branch still points
there until Step 7, and the branch reflog records that tip when the ref moves. This gives
the user an undo point without a backup tag, branch, stash, or temporary file.

### Step 6: Rebuild the history (detached HEAD + merge --squash)

Determine each group's **tip** = the newest (last) original commit in that group, in order.
Then rebuild on a detached HEAD starting from `BASE`:

```bash
git checkout --detach <BASE>
# For each group, in original order, with its tip SHA and subject:
git merge --squash <group1_tip>
git commit -m '<group1-subject>'
git merge --squash <group2_tip>
git commit -m '<group2-subject>'
# ...one merge --squash + commit pair per group
```

`git merge --squash <tip>` stages the cumulative diff from the current HEAD up to `<tip>`
— i.e. exactly that group's changes — without committing. Then commit it with the new
message. Because the history is linear and groups are contiguous and in order, this never
conflicts.

Pass each approved subject as a single `git commit -m` argument. Do not create commit
message files.

Save `NEWTIP = git rev-parse HEAD`.

If any merge or commit fails, abort the rebuild, return to `BRANCH`, and report the
failure. Since the precondition required a clean tree, remove only the rebuild's pending
index/worktree changes before returning:
```bash
git reset --merge HEAD
git checkout <BRANCH>
git status --short         # should be clean
```
The original branch is still untouched. Do not use a stash or leave the user detached.

### Step 7: Verify, then move the branch

**Verify the content is identical** before touching the branch:
```bash
git diff <ORIG_TIP> <NEWTIP> --stat
```
This **must be empty**. If it shows anything, the rebuild changed content — abort without
moving the branch:
```bash
git checkout <BRANCH>      # discards the detached rebuild; original branch untouched
```
Report what diverged. Do **not** proceed.

If the diff is empty, point the branch at the rebuilt history:
```bash
git checkout <BRANCH>
git reset --soft <NEWTIP>
git status --short         # should be clean
```
`reset --soft` moves the branch ref to `NEWTIP` while leaving the working tree (already
identical) untouched — so status is clean.

### Step 8: Report

Show the result and how to undo:
```bash
git log --oneline <BASE>..HEAD
```

```markdown
## Done — squashed <N> commits into <M>

<new oneline log>

Original tip: `<ORIG_TIP>` (retained in `<BRANCH>`'s reflog).
- Undo: `git reset --hard <ORIG_TIP>` (run it yourself — the agent does not run
  `reset --hard`).
- Cleanup: complete — no backup tag, branch, stash, or temporary message files remain.
```

Git will normally retain the replaced commits through the branch reflog until reflog
expiry and garbage collection. That is standard Git recovery history, not a leaked ref;
do not expire reflogs or run GC as part of this skill.

## Examples

### Example 1: superhuman run left 6 WIP commits

> /squash-commits

Auto-detects 6 unpushed commits via `git rev-list HEAD --not --remotes`. Reading them
shows two features: an export button (impl + 2 fixups + a test) and an unrelated config
tweak. Proposes Group 1 → `feat: add CSV export button` (5 commits) and Group 2 →
`chore: bump lint config` (1 commit, kept as-is). After confirmation, rebuilds on a
detached HEAD with two `merge --squash` + commit steps, verifies the tree is identical,
and `reset --soft`s `main` onto the result — 6 commits become 2 with the original tip
retained only in the reflog.

### Example 2: conservative, only fold fixups

> /squash-commits --conservative

Range has `feat: add auth`, `fix typo`, `address review`, `refactor session store`,
`feat: add logout`. Folds `fix typo` and `address review` into `feat: add auth`; leaves
the refactor and the logout feature as their own commits. 5 commits → 3.

### Example 3: explicit base

> /squash-commits origin/develop

Skips auto-detection and squashes everything in `origin/develop..HEAD`, useful when the
branch has no upstream set or you want to bound the range to a specific integration point.

## Troubleshooting

### "Nothing to squash"

**Cause:** `git rev-list HEAD --not --remotes` is empty — all commits are already pushed,
or HEAD is at a remote-tracking branch.
**Solution:** Confirm there are local-only commits. If the branch has no upstream and no
remote contains the work, pass an explicit base: `/squash-commits origin/main`.

### Auto-detection picks up too many commits (no remotes / new repo)

**Cause:** With no remote-tracking branches, `--not --remotes` excludes nothing, so the
range walks back to the root commit.
**Solution:** Pass an explicit base ref (e.g. `/squash-commits main` or a SHA) bounding
the commits you want to squash.

### Verify step shows a non-empty diff

**Cause:** Something in the rebuild changed final content (very unusual on linear history —
possibly a merge commit slipped into the range, or a group tip was misidentified).
**Solution:** Abort immediately — `git checkout <BRANCH>` (the branch ref was never moved,
so history is intact). Re-examine the range with `git log --stat BASE..HEAD`, exclude any
merge commits, and re-run. Never move the branch when the diff is non-empty.

### Range contains merge commits

**Cause:** The unpushed history isn't linear.
**Solution:** This skill is out of scope for merges. Tell the user; suggest they handle
the merges manually or rebase to a linear history first.

### User wants to undo after the squash

**Cause:** The new grouping/messages aren't what they wanted.
**Solution:** Use the `ORIG_TIP` printed in the completion report:
`git reset --hard <ORIG_TIP>` (the user runs this — the agent does not run
`reset --hard`). If the report is unavailable, inspect `git reflog <BRANCH>` and identify the tip
immediately before the squash. Then adjust the plan and re-run.

### Legacy `squash-backup-*` tags exist

**Cause:** Older versions of this skill intentionally left a backup tag after every run.
They did not create stashes.
**Solution:** Inspect them with `git tag --list 'squash-backup-*'`. Delete only tags whose
target you no longer need with `git tag -d <exact-tag-name>`. Current runs do not create
these tags.

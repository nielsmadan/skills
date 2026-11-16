# Workers and local integration (`--fix`)

The sessions, branches, delivery, worker loop and integration all come from the `crew` skill.
Load it at Phase 3. This file adds only what a codebase review layers on top.

## Setup (Phase 3, before plan approval)

Run crew's "Lead: setup" from the lead's checkout, on the integration branch the interview
settled. Worker homes are a new worktree (`crew add w1 --new-worktree`, the default) or an
existing sibling clone (`crew add <name> <path>`). The user's yes to the setup proposal
authorises creating the worktrees and branches.

When `crew status` shows every worker joined and level, record each hello in `programme.md`
under Workers: name, harness, checkout, branch, baseline check result. Plan approval presents
that table.

## Briefs

Briefs go to `.codebase-review/briefs/B-<n>.md` and reports come back to
`.codebase-review/reports/B-<n>.md`. Use crew's envelope with this skill's Rules and the
findings as Items (`references/formats.md`, briefs). The risk-flag tripwire rides in the Rules:
a worker whose diff trips a flag the entry does not carry, or that has grown well past the
failure it removes, discards that change and reports the flag with the simplest alternative.

## Lead-side integration additions

On top of crew's "Lead: the loop", step 4:

- **Touches and proportion.** In the `--dry-run` listing, each commit must stay inside its
  finding's Touches (plus its tests and docs) and be in proportion to the failure. Read the
  diff of any that is not, and of any that touches a flagged area. A commit that refactors,
  renames or redesigns beyond its finding, or trips an unreported risk flag, goes back to the
  worker to be split or stopped, and the finding goes back to the user: a judgment item at the
  next aspect close in the walkthrough, `held` under `--auto`.
- **Check log** goes to `$RUN/check-B-<n>.log`.
- **Ledger.** Mark the findings `fixed` with their shas and the batch done. A finding stopped
  on a risk flag gets the flag and goes back to the user the same way. Recount the size for
  the change budget.
- **Refused by the user's edits** (exit 4): record the branch in Blocked on you with the
  command crew printed, and keep handing out work in other areas.

## Regroup the history (Phase 8)

Per-finding commits suit integration, not history: batch order, repairs apart from what they
repair, messages covering one finding. Rebuild `<base>..HEAD` as feature commits:

1. **Group** the commits by feature or user-visible change, reordering freely. Fold every
   repair, revert and review fix into the commit it changes; a change and its revert vanish
   together. Tests and docs go with their change, and each message covers its whole diff in
   the repo's convention.
2. **Build** it on `codebase-review/regrouped`, from the base, in a worktree: cherry-pick each
   group's commits with `-n` in order, resolving conflicts to the integration tip's version,
   then commit once per group.
3. **Verify** that `git diff <integration branch> codebase-review/regrouped` is empty and that
   the check command passes on the regrouped tip. A non-empty diff is a regroup bug: fix the
   regroup, never the code.

(`squash-commits` only merges neighbours, so it cannot.) Adopting it rewrites the integration
branch, so it waits for the user's yes to the report; then keep the old tip as
`codebase-review/full` and run `git reset --keep codebase-review/regrouped`.

## Cleanup (Phase 8)

Remove nothing. List crew's teardown commands in the report for the user to run once they are
satisfied. Once the regroup is adopted, the worker branches are contained in
`codebase-review/full`, not in the integration branch, so `branch -d` refuses. Give the check
and the forced delete instead:
`git merge-base --is-ancestor crew/w1 codebase-review/full && git branch -D crew/w1`.

## Troubleshooting

### A worker's branch won't fast-forward
**Cause:** another batch landed after the worker rebased, or the worker branched from a stale
tip.
**Solution:** `crew integrate` exits 3; message the worker to run `crew sync --rebase` and
re-report. Never merge with a merge commit, and never rebase on the worker's behalf. If it exits
4 (the user's uncommitted edits), record it in Blocked on you and carry on.

### A worker reports green, but the check fails on the integration branch
**Cause:** tests were deselected, an exit code was swallowed by a pipe, or the worker did not
rebase.
**Solution:** the lead's own check run is the verdict. Send the log path back as a new batch.
Never rewind the integration branch without the user.

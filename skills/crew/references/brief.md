# Brief, report and hello formats

## Brief: `<work folder>/briefs/B-<n>.md`

A worker executes it without ever having seen the lead's conversation. A calling skill fills
the Rules and Items sections from its own ledger; the envelope stays as is.

```markdown
# Batch B-<n>: <one-line theme>

From: <lead session name> · Lead checkout: <absolute path> · Integration branch: <I>
Worker: <name> · Checkout: <absolute path> · Branch: <branch>
Base: <I> must contain <sha>. Run `crew sync` first.
Check command: <cmd> · Commit convention: <the repo's, e.g. feat/fix/chore, no scopes, no body>
Approach: <per-item loop | plan | longshot>
Report: <work folder>/reports/B-<n>.md, then message <lead session name> `report <that path>`

## Rules
- If an item's premise does not match the code, stop that item and report it. Do not adapt it.
- Make the smallest change that does what the item asks. No renames, refactors, comment
  rewording, test moves or reformatting beyond it; report those as new items instead. Stay
  inside the item's Touches.
- Test through public behaviour. Confirm new tests actually ran: the count moved, or their
  names appear in the output.
- Read exit codes directly, never through a pipe.
- One commit per item; fold review fixes into the commit they belong to.
- Before reporting, `crew sync --rebase` and re-run the check command.
- Do not push. Do not touch <I> in the lead's checkout or any repo not named here.
<caller's own rules, e.g. risk flags with the instruction to stop on an unlisted one>

## Items
<each item verbatim from the caller's ledger: ID, what to do, where (path:line), Touches,
Depends, and how to verify it>
```

## Report: `<work folder>/reports/B-<n>.md`

```markdown
# Report B-<n> from <worker name>

Branch <branch> @ <sha>, rebased onto <I> @ <sha>.
Check after rebase: <command> → <summary line>, exit <code>

## Commits
| Commit | Subject | +/− | Item | Simpler alternative considered |
|---|---|---|---|---|
| a1b2c3d | fix: keep draft when sync fails | +24 −3 | ST-B2 | retry only, rejected: loses the draft offline |

## Stopped
- <ID> — <why: premise mismatch, rule tripped (which), blocking question> — <simplest alternative, if any>

## For the lead
<anything needed to verify: a manual step, a test that needs a device, a conflict resolved>
```

## Hello (message, not a file)

```
crew hello from <name> (<harness>)
checkout <absolute path> · branch <branch> @ <sha>
check: <command> → <summary line>, exit <code>
```

# Programme file formats

Four working files live in the programme directory. They are the memory of a review that runs
for weeks across compactions, sessions and harnesses, so write them for a reader with no
conversation history.

## programme.md

```markdown
# <product> <version> release review

**Now:** P3 · unit `init` (4/10) · item P-17 of 7 open in this unit
**Next:** finish `init`, then `template`

## Framing
| Decision | Ruling | Date |
|---|---|---|
| Release path | ship 0.9.0, then run the programme, then 1.0.0 | 2026-09-14 |
| Breaking changes | wide open until the freeze | 2026-09-14 |
| Out of scope | Antigravity harness | 2026-09-14 |

## Phases
| | Phase | Status |
|---|---|---|
| P1 | Map and target flows | done |
| P2 | Cross-cutting conventions | done |
| P3 | Unit-by-unit surface review | in progress |
...

## Units
| Unit | Status | Open | Ruled | Notes |
|---|---|---|---|---|
| `sync` | ruled | 0 | 6 | |
| `init` | in review | 7 | 3 | target flow in target-flows.md#init |

## In flight
| Batch | Entries | Where | Brief | Status |
|---|---|---|---|---|
| B-1 | S-01..S-04 | session `lo2`, checkout dev2 | briefs/B-1.md | reported done, not yet verified here |
```

Unit statuses: `unreviewed → in review → ruled → handed off → implemented → verified`. A unit is
`verified` only when every flag, config key and output it owns is accounted for and each of its
entries is `verified`.

Update the **Now** and **Next** lines every time the position moves. They are the first thing read
on resume.

## changes.md

The ledger. One entry per finding. IDs are stable and never reused: `S-` surface, `Q-` quality,
`D-` docs, `A-` QA.

```markdown
### S-07 · unit: sync · breaking: yes · status: ruled

Scenario   A user who edited ~/.claude/settings.json by hand runs `tool sync` to pick up a new
           skill. `--force` would discard the edit; on `init`, `--force` means "replace the
           registration". Same word, unrelated effects.
Finding    `--force` names two unrelated behaviours.
Prior art  git, cargo, npm: `--force` = override a safety check. None use it for "replace".
Ruling     `sync --overwrite-modified`; `init` uses `--replace`. No alias (nothing is released).
Rationale  Each flag says what it destroys. Pre-1.0, so no compatibility cost.
Spec       cli.py:66 and cli.py:140; help text names the files at risk.
Touches    src/tool/cli.py · README.md:739 · docs/user/reference/cli.md:12
Verify     tests/test_cli.py covers both spellings; `--help` shows the new names.
Depends    none
Triggers   none
```

- **Scenario** is mandatory. Anyone should be able to reproduce it from the text alone.
- **Rationale** records the *use-case* reason for the ruling. If it is ever challenged, it is
  re-analysed on that basis, and "we decided it" is not a rationale.
- **Depends** names entries or open questions this one cannot be implemented without. Readiness
  analysis reads it.
- **Triggers** is mandatory, either non-empty or `none`. It lists the repo-specific constraints an
  implementer would otherwise miss: expected-output regeneration, extraction round-trips,
  migration test tiers, generated files. Harvest them from the repo's `AGENTS.md` and ADRs.
- **Touches** is a starting list, not a guarantee. The implementer re-greps.
- Statuses: `open → ruled → handed off → implemented → verified`, or `deferred` / `rejected` with
  the reason on the Ruling line. A deferred entry names where it went (roadmap, issue).

A ruling that reverses an earlier one edits that entry in place, updating the Ruling and Rationale
and adding a `Revised <date>:` line. Never create a second entry for the same finding.

## target-flows.md

The target journeys, written as what **should** happen, never as a description of current
behaviour.

```markdown
## Adopting the tool with existing config (global)

Starting state: 18 skills in ~/.claude/skills, an AGENTS.md, two MCP servers, no version control.

1. `tool init global` asks where to keep the source. Answer: ~/dotfiles/agents (empty).
2. Detects claude and codex installed; proposes both; user confirms.
3. Extracts the existing skills and instructions into the source tree.
4. Renders, compares with what is on disk, shows any differences, asks before overwriting.
...
```

Each ruled entry that changes a flow updates the flow in the same edit.

## briefs/B-n.md

A brief for an implementer session. It must be executable by a session that never saw this
conversation.

```markdown
# Batch B-2: <one-line theme>

Checkout: <absolute path>. Base: <commit>, which must contain <commits it depends on>.
Entries: S-06, S-07 (copied verbatim below; changes.md is the source of truth).

## Rules
- If an entry's premise does not match the code you find, stop and report. Do not adapt the
  ruling to fit.
- Verify each entry with the command in its Verify line. Confirm the new tests actually ran
  (the count moved, the test names appear in the output). A pass count that did not change
  means the tests were deselected, not that they passed.
- Read exit codes directly, never through a pipe (`cmd | tail` reports tail's status).
- Probe in an isolated scratch HOME, and unset tool-specific config-dir variables that would
  otherwise point back at the real one.
- Commit per entry as `<type>: <subject>` following the repo's commit policy. Do not push.
- Report: commits, verification output summary, anything stopped on.

## Entries
<verbatim entries>
```

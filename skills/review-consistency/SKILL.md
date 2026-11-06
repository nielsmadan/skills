---
name: review-consistency
description: >-
  Review whether changes follow the patterns the codebase already uses — compare each added or changed construct with its existing siblings for naming, placement, mechanisms (error handling, logging, config, helpers), shape, and registration, and cite the precedent for every divergence. Triggers "review consistency", "consistency review", "does this follow existing patterns", "is this consistent with the codebase", "match the conventions", "pattern drift", "check conventions". Not for style a formatter or linter decides, or for judging whether the existing pattern is any good (use review-cleancode).
argument-hint: '[--staged | --unpushed | --changed | --all]'
effort: high
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Review Consistency

Language-agnostic review of one question: **does the change do things the way this codebase already does them?** Every finding names the precedent it diverges from. A divergence without a cited precedent is an opinion, not a finding.

## Usage

```
/review-consistency                  # Review context-related code
/review-consistency --staged         # Review staged changes
/review-consistency --unpushed       # Review files changed across all unpushed commits
/review-consistency --changed        # Review unstaged changes
/review-consistency --all            # Whole-repo audit for competing patterns
```

## Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related code | Files from the current conversation context. If no context, ask the user to specify files or use `--staged`/`--changed`/`--all`. |
| `--staged` | Staged changes | `git diff --cached` |
| `--unpushed` | Changes across unpushed commits | `git diff $(git rev-list HEAD --not --remotes \| tail -1)^..HEAD` |
| `--changed` | Unstaged changes | `git diff` |
| `--all` | Full codebase | `git ls-files`, grouped by directory and construct kind |

`--unpushed` derives its range from `git rev-list HEAD --not --remotes` (oldest unpushed commit's parent → HEAD). If nothing is unpushed, or there is no remote/upstream (or the range walks back to the root commit) so it can't be determined reliably, stop and ask the user to pick another scope.

The diff scopes review the **diff** against the rest of the repo: the precedents are almost always outside the scoped files, so search the whole checkout for them.

## Gotchas
- **Written rules beat precedent.** If `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md` or a doc says "new code uses X", code that uses X is correct even when most existing code does Y. Never flag a change for following a documented migration.
- **Newer beats older.** When the codebase holds two patterns, check `git log -S '<construct>' --format='%h %ad %s' --date=short` for which one recent commits add. The one being adopted is the convention; the other is legacy.
- **No majority, no finding.** A convention needs at least two agreeing precedents or one written rule. If siblings disagree among themselves, the change cannot be inconsistent with them — at most report that the codebase has competing patterns (with `--all`).
- **Generated, vendored and fixture code is not precedent.** Skip files with a generated banner, `vendor/`, `third_party/`, `node_modules/`, snapshots and test fixtures when collecting precedents.
- **A rendered or generated output is not the place to fix drift.** Point the finding at the source the output is generated from.

## Workflow

1. **Determine scope** based on flags (see Scope table above).
2. **Read the written conventions**: `AGENTS.md` / `CLAUDE.md` in the root and the touched directories, `CONTRIBUTING.md`, and any docs they point to for conventions. Note each stated rule; these override precedent.
3. **Inventory the change.** List every unit the diff adds or materially changes, each with its *kind*: "a new CLI subcommand", "an HTTP handler", "a skill", "a config key", "an error raised to callers", "a log call", "a test file", "an env var read", "a README table row". Kind is what you will search for precedents of.
4. **Collect precedents per unit.** For each unit, find two to five existing instances of the same kind:
   - Siblings first: other files in the same directory, other entries in the same table, registry, enum, or switch.
   - Then same-kind constructs elsewhere: grep for the call, decorator, base class, or keyword that marks the kind (other `add_argument` calls, other `raise AppError`, other `logger.` calls, other `os.environ` reads).
   - Record each precedent as `file:line`. If you find fewer than two agreeing precedents and no written rule, drop the unit.
5. **Compare against the checklist below**, one category at a time, and draft a finding for each divergence with its precedents.
6. **Filter** — drop every draft that:
   - appears in Out of Scope below;
   - follows a written rule or the newer of two patterns (Gotchas);
   - cites precedents that do not actually agree with each other. Re-open each cited `file:line` to confirm before keeping the finding.
7. **Classify severity**:
   - **High**: missed wiring (siblings are all registered somewhere and this one is not, so it is unreachable, undocumented, or untested), or a divergence that changes behaviour callers rely on (a different error type, exit code, return shape, or log level that downstream code or alerts key on).
   - **Medium**: a second way to do a job the codebase already does one way — a hand-rolled helper, a different config or logging mechanism, a new dependency for something an existing one covers, a structure that differs from every sibling.
   - **Suggestion**: naming, file placement, or ordering drift with no behavioural effect.
8. **Report** using the Output Format below.

For more than five files or with `--all`, split the units into groups of related kinds and give each group to one sub-agent; merge and deduplicate their findings.

Dispatch workers that return findings without editing files. Disable delegation tools where supported; read-only access alone does not prevent delegation. Any coordinating role needs explicit subtasks, a descendant limit, and a stopping condition in its brief.

## Checklist

### 1. Naming & Vocabulary
- Identifiers, files, flags, env vars, config keys and CLI commands follow the siblings' casing, prefixes, suffixes and word order (`get_x` vs `fetch_x`, `--dry-run` vs `--dryrun`, `FOO_ENABLED` vs `ENABLE_FOO`).
- The same concept uses the same word the rest of the codebase uses for it — not a synonym (`account` vs `user`, `remove` vs `delete`).

### 2. Placement & Structure
- The file lives where siblings of its kind live, and is split the way they are (one class per file, `index` barrel, `tests/` mirror of `src/`).
- Internal layout matches the siblings: section order, where constants and helpers sit, the order of a skill's or doc's headings.
- Test data, builders and helpers live where sibling tests keep theirs (a `factories/` or `fixtures/` folder, a shared `helpers` module), not inline in one test file.

### 3. Mechanisms
- Errors raised, wrapped, returned and reported the way siblings do (project error class, `Result`, exit codes, error message format).
- Logging, config and env reading, HTTP/DB/file access, retries, time and randomness go through the same wrappers and helpers siblings use.
- An existing helper or utility already does what the change hand-rolls — name it with its `file:line`.
- Tests mock, stub, set up and build data the way sibling tests do — through the established fixtures, factories and helpers, not an ad-hoc `patch` or inline builder where one already exists.
- A new dependency for a job an already-installed one does elsewhere in the repo.

### 4. Shape of Siblings
- A new member of a family (command, endpoint, handler, migration, skill, plugin, component) has the same signature, arguments, options, defaults, output format and documentation sections as the other members.
- Public interfaces return and accept the same shapes their neighbours do (pagination, IDs, timestamps, null vs missing).

### 5. Wiring & Registration
- Every place the siblings are registered also lists the new one: routers, CLI registries, exports and barrels, dependency injection, feature lists, README or catalog tables, changelogs, config schemas, permission lists, CI matrices.
- Tests exist where siblings have tests, named and located the way theirs are, using the same fixtures and helpers.

## Out of Scope

These are **never findings** here. Do not report them, and do not mention them as "worth considering".

| Not a finding | Why |
|---|---|
| Whitespace, quotes, import order, line length, anything a configured formatter or linter decides | `review-tidy` runs the formatter and lint autofixes |
| Whether the existing pattern is a good one | `review-cleancode` / `review-architecture`. A change that faithfully copies a weak pattern is consistent |
| Layering and module boundaries across the system | `review-architecture` |
| Docs and references the change left stale by renaming or removing something | `review-tidy` |
| Version-specific library API usage | `review-library-use` |
| Test assertion quality and coverage gaps | `test --review`; this skill checks only that tests exist where siblings have them, in their style |
| Inconsistencies between existing files the change did not touch | Report only what the scoped diff introduces, except with `--all` |
| A deliberate improvement that replaces the old pattern everywhere in the change's reach | That is a migration, not drift. It becomes a finding only if it leaves two ways to do the same job — then report it as Medium, cite both, and recommend which to keep |

## Autofix

Some fixes are safe to apply without a separate decision: they cannot change production behaviour, any change in what a test executes is proven by running tests, and a wrong call shows in the diff and is cheap to revert. Spotting the pattern is still a judgment; that is fine, as it is for comment cleanup. Tag exactly these:

| Fix | Tag |
|---|---|
| Rename an unexported identifier to the pattern its same-kind identifiers use, updating every reference grep finds, string literals included | `autofix` |
| Add a missing entry to a documentation list that holds only names (usage synopsis, `argument-hint`, flag list) | `autofix` |
| Move test code (builders, test data, helpers) unchanged to where its siblings keep it, and import it | `autofix, verify: suite` |
| Replace a test's ad-hoc mock or setup with the established fixture or helper | `autofix, verify: mutation` |

`verify: suite` means the full test suite must pass with the fix applied: a moved builder can collide with or shadow a name in the shared module. `verify: mutation` means the affected tests must pass, and must still fail once the behaviour they assert is deliberately broken: a substituted fixture can leave a test passing for the wrong reason, which a green run alone does not reveal.

Never tag public names, flags, env vars or config keys; registrations; production code moves or mechanism swaps; anything that needs new prose; a move into a `conftest.py` or any other change that widens fixture scope; or a move of code that resolves paths relative to its own file.

Under `code-review`, the main thread runs the checks and applies the items that pass. Standalone, this skill only reports; the tag marks a fix that can be applied without further discussion.

## Output Format

```markdown
## Consistency Review: {scope}

### High Priority (missed wiring / behaviour callers rely on)
- {file}:{line} - {category}: {what the change does}
  **Precedent:** {file:line}, {file:line} — {what they do}
  **Fix:** {the change that brings it in line}

### Medium Priority (second way to do the same job)
- {file}:{line} - {category}: {what the change does}
  **Precedent:** {file:line}, {file:line} — {what they do}
  **Fix:** {the change that brings it in line}

### Suggestions (naming / placement drift)
- {file}:{line} - {category}: {divergence} (precedent: {file:line})
```

Append the tag from Autofix to every finding that qualifies, e.g. `[autofix, verify: suite]`.

With `--all`, add a section for clusters where the codebase itself disagrees:

```markdown
### Competing Patterns
- {kind}: {pattern A} in {N} places ({file:line}, …) vs {pattern B} in {M} places ({file:line}, …). Newer: {A or B, from git log}.
```

If nothing survives the filter, say so plainly and stop. An empty result is normal for a change that was written by copying its siblings.

## Examples

**A new CLI subcommand that skipped the registry:**
> /review-consistency --staged

The diff adds `cmd_export` in `cli/export.py`. Every sibling in `cli/` is listed in `cli/__init__.py:COMMANDS` and has a `tests/cli/test_<name>.py`; `export` has neither. Reports High (unreachable from the CLI) with both siblings cited. Also finds `export` reading `os.environ["EXPORT_DIR"]` where the other commands call `config.get()` (`cli/sync.py:14`, `cli/import_.py:22`) — Medium. And `tests/cli/test_export.py` builds its records with an inline `make_record()` where every other CLI test imports builders from `tests/factories/` — Medium, tagged `[autofix, verify: suite]`.

**Following a documented migration:**
> /review-consistency --changed

The change logs through `structlog` while 40 files still use `logging.getLogger`. `AGENTS.md` says "new code uses structlog", and `git log -S structlog` shows it being adopted over the last month. No finding.

**Whole-repo audit:**
> /review-consistency --all

Groups the repo by construct kind and reports Competing Patterns: HTTP handlers return errors as `{"error": msg}` in 12 places and `{"detail": msg}` in 5, with `detail` the newer. No High or Medium findings, since `--all` reports existing drift as clusters rather than blaming individual files.

## Troubleshooting

### Every unit gets a finding
**Cause:** The precedents are drawn from too wide a net — a different subsystem, an older layer, or test code standing in for production code.
**Solution:** Restrict precedents to siblings of the same kind in the same subsystem, and re-check each cited `file:line` agrees with the others.

### Findings contradict the project's own instructions
**Cause:** Step 2 was skipped or the rule lives in a nested `AGENTS.md`/`CLAUDE.md`.
**Solution:** Read the instruction files in every touched directory, not only the root. A written rule always wins.

### No precedents found for a unit
**Cause:** The unit is the first of its kind, or the search term was wrong.
**Solution:** Try the construct's marker (decorator, base class, registry name) rather than the new unit's own name. If it really is the first of its kind, it cannot be inconsistent — drop it.

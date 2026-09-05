# Review Mode (`--review`)

The `--review` action (assess is the default; this is the explicit override). Assesses docs
against the principles in `references/principles.md`, then offers to apply fixes.

## Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related docs | Find docs related to recent conversation |
| `<target>` | A feature/area as a whole | Find all docs covering that feature |
| `--staged` | Staged .md files | `git diff --cached --name-only -- '*.md'` |
| `--unpushed` | .md files changed across unpushed commits | `git diff --name-only $(git rev-list HEAD --not --remotes \| tail -1)^..HEAD -- '*.md'` |
| `--all` | All documentation | Glob `docs/**/*.md` (excluding `docs/explain/`, `docs/product/`, `docs/superpowers/`) + `README.md` + `CLAUDE.md`. Include `docs/user/` (check for accuracy vs behavior, but it's human-format — don't flag verbosity). Include `docs/decisions/` + `docs/log/` for link/quality checks but never sync their bodies to code (append-only). Include `docs/reference/`, but judge it against the external subject and the version the repo now resolves — never against our code. |

`--unpushed` derives its range from `git rev-list HEAD --not --remotes` (oldest unpushed commit's parent → HEAD). If nothing is unpushed, or there is no remote/upstream (or the range walks back to the root commit) so it can't be determined reliably, stop and ask the user to pick another scope.

## Workflow

1. **Get file list** based on scope.
2. **Review** (directly if ≤5 files, parallel sub-agents if more), checking each doc
   against its lifecycle — prioritize accuracy/completeness/staleness over prose. Check
   living docs against current code. For `docs/tests/`, use [manual-tests.md](manual-tests.md):
   review procedures for repeatability and runs against their recorded revision and evidence.
3. **Report findings** by priority (see Output Format). For `docs/features/` docs, report
   divergences between the documented behavior and the implementation in **both directions**
   (doc describes behavior the code lacks; code has behavior the doc omits) without assuming
   either side is correct — the user reconciles. This is the implementation side of the
   three-layer check; `review-product` checks `docs/product/` ↔ `docs/features/`.
4. **Offer to apply.** Present the findings as a numbered list and ask the user which
   to apply — accept multiple selections. Where the tool supports an interactive
   multi-select prompt, use it; otherwise ask the user to reply with the numbers
   (e.g. `1,3,4`), `all`, or `none`.
5. **Apply** the chosen findings using the `--update` apply logic (in-place edits),
   then report what changed. `none` → stop without writing. Review never rewrites
   silently — the user always chooses.

## Checklist

**Accuracy:**
- [ ] No local paths (`/Users/`, `/home/`, `C:\`)
- [ ] File paths / `file:line` references exist and are correct
- [ ] Class/function names are current; described behavior matches the code
- [ ] No signatures restated in prose (should reference code instead)
- [ ] Links to related docs work
- [ ] `docs/tests/`: only occasional manual operations; procedures have usable commands,
      prerequisites, inputs, and evaluation criteria
- [ ] `docs/tests/*/runs/`: observed results and original setup are preserved; missing
      historical details are reported as gaps, not filled from current code or measurements
- [ ] `docs/reference/`: every verified claim carries a date **and** the version probed;
      upstream links resolve; no claim is stamped against a version older than the one the
      repo now resolves (report it as needing re-verification — do not rewrite the claim)
- [ ] `docs/decisions/`: an ADR marked `superseded` carries a working forward link to the ADR
      that replaced it (one without a pointer reads as current to anyone arriving by search)
- [ ] `docs/decisions/`: no two `accepted` ADRs answer the same question differently — report
      the contradiction and which one is current; never settle it by editing either body

**Quality:**
- [ ] No verbatim duplication across files
- [ ] Current-state and why are separated; gotchas documented
- [ ] Examples are concrete (not generic placeholders)

**Completeness:**
- [ ] No incomplete sections, placeholders, or TODOs
- [ ] Key interfaces covered (APIs, components, hooks, services, utilities)
- [ ] Root `overview.md` present *if* ~3+ docs warrant an index (Principle 5); do not
      flag a missing per-directory `overview.md` unless that subdir clearly needs one
- [ ] Instruction file (`AGENTS.md`/`CLAUDE.md`) is lean: no derivable/enforceable
      content, roughly <200 lines (Principle 8)
- [ ] Required sections match the doc type (Purpose, How it works, Gotchas for code docs;
      procedure/run fields from `manual-tests.md` for `docs/tests/`)

## Output Format

```markdown
## Documentation Review: {scope}

### Critical (fix now)
1. {file}:{line} - {issue}

### High Priority (fix soon)
2. {file} - {issue}

### Suggestions
3. {file} - {improvement}
```

Number findings sequentially across all tiers so the user can select by number.

## Troubleshooting

### Review finds no issues but coverage is incomplete
**Solution:** Use `--all` to scan the full `docs/` tree against source modules; missing
docs for key modules surface as completeness gaps.

### Review "fixed" a stale ADR by updating its body
**Cause:** Treating `docs/decisions/` like a live code-derived doc. An ADR describes the past
on purpose, so it goes out of date by design and that is not a defect. **Solution:** The only
edit review may propose is the `**Status:**` line plus a forward link to the ADR that replaced
it — the fix for a decision that no longer holds is a *new* ADR. Revert the rewrite and report
it as needing supersession.

### Review "fixed" a reference doc by rewriting a verified claim
**Cause:** Treating `docs/reference/` like a live code-derived doc. **Solution:** Review may
flag a claim as stale against the current version and may fix links and prose, but the claim
itself changes only by re-running the probe (that is `--update`'s job). Revert the rewrite and
report it as needing re-verification instead.

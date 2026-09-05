# Update Mode (`--update`)

Sync existing docs to the current code — the end-of-feature "make sure what changed
is reflected" pass. Edits in place; never appends a changelog. Applies the principles
in `references/principles.md`.

## Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Staged code changes | `git diff --cached --name-only`; if empty, fall back to unstaged (`git diff --name-only`) and open with a one-line note: "Nothing staged — syncing docs for unstaged changes instead." |
| `<target>` | A feature/area as a whole | All docs + code for that feature |
| `--all` | Whole project | Cross-check `docs/**` against source |

## Workflow

1. **Determine the changed scope** (above).
2. **Map** changed files/symbols → affected docs: grep `docs/**`, `README.md`,
   `CLAUDE.md` for the changed symbols/topics to find the docs describing them.
3. **Apply in place**: edit each affected doc to match the current code — **replace**
   the stale parts, preserve formatting/style, stay concise (current state, not
   history). Update the "how it works now" sections; leave "why" alone unless the
   decision itself changed. **Skip append-only records** (`docs/decisions/`,
   `docs/log/`, `docs/tests/*/runs/`): never rewrite their bodies to match code — they
   describe the past on purpose. At most add a new entry or fix a broken link (see Doc lifecycles in
   `references/principles.md`). A decision the diff invalidates is **superseded, not
   edited**: write a new ADR, and on the old one change only the `**Status:**` line and its
   forward link. **Skip `docs/reference/` on a source-scoped run** — it is
   anchored to external things, so our refactor cannot make it stale (see step 5).
   For `docs/tests/`, update only the live procedure when its commands or prerequisites
   change; follow [manual-tests.md](manual-tests.md). Updating docs does not itself run the
   operation or produce new measurements.
4. **New behavior with no doc**: if there's a clear home pattern (e.g.
   `docs/features/<name>.md`), create that doc from the template; otherwise list it
   as an undocumented gap and suggest `--generate`. Don't create docs with no obvious
   home.
5. **Reference docs go stale on a *dependency* bump, not a code change.** Include
   `docs/reference/` only when the diff touches a manifest/lockfile, on `--all`, or when the
   target names the subject. Then, per affected doc: re-run the probe each verified claim
   records, and either refresh its date + version stamp or mark it unverified against the new
   version. **Never bump a stamp you did not re-check** — a false stamp is worse than an old
   one. If verification requires an occasional operation recorded under `docs/tests/`, report
   it as needing re-verification unless running that operation is already authorized.
   Drop claims that stopped being true rather than archiving them; if the change forces
   one on us, propose an ADR.
6. **Fan out**: if >5 affected files/docs, spawn one sub-agent per doc/area, merge.
7. **Report**: which docs were edited and what was synced; any gaps left for
   `--generate`.

## Troubleshooting

### `--update` reports "nothing staged"
**Cause:** No staged changes. **Solution:** It falls back to unstaged changes
automatically (with a note). To target something specific, run `doc --update <feature>`
or `git add` the files first.

### `--update` found new behavior but didn't document it
**Cause:** No existing doc and no clear home directory for it. **Solution:** It's
listed as a gap — run `doc --generate <target>` to create the doc, which also wires
the home into the docs tree.

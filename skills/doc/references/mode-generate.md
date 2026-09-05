# Generate Mode (`--generate`)

Create documentation for code that isn't documented yet, following
`references/principles.md` and `references/generate-templates.md`.

## Scope

| Flag | Scope | Method |
|------|-------|--------|
| `<target>` | Specific file/module/feature | Read the code, generate docs |
| `--staged` | Staged code changes | Generate docs for what changed |
| `--unpushed` | Unpushed code changes | Generate docs for what changed across unpushed commits (`git diff --name-only $(git rev-list HEAD --not --remotes \| tail -1)^..HEAD`). If nothing is unpushed or detection is unreliable (no remote/upstream, root-commit walk-back), stop and ask. |

## Workflow

1. **Read the code** - understand what it does and how it works.
2. **Check for existing docs** - if they exist, prefer `--update` instead.
3. **Generate** following the templates (current-state + why; `file:line` refs, not
   restated signatures).
4. **Place appropriately**, per the repo's **Doc Profile** (see `references/principles.md`
   for the selection test; default to Lean when ambiguous). Where each kind of doc goes:
   - `docs/<flow>.md` — cross-cutting flows (Lean, the common case).
   - `docs/features/` — **what** each feature does (Structured; mirrors `docs/product/`
     use cases, tracks the implementation).
   - `docs/tech/` — **how** it's built (Structured; non-derivable only, never restate code).
   - `docs/reference/` — how **external** things behave (dependency / platform / API quirks).
     Orthogonal to the profile: warranted by the three-part test in `references/principles.md`,
     not by repo size — even a Minimal repo can earn one.
   - `docs/decisions/` — ADRs (why-this-way).
   - `docs/tests/<name>/` — occasional manual test procedures and dated results, including
     performance measurements. Use [manual-tests.md](manual-tests.md), not the code-doc templates.
   - Root `docs/overview.md` index once ~3+ docs exist; a subdirectory `overview.md` only
     where a subdir warrants one (Principle 5), not by default.
5. **Install the per-repo update trigger.** After writing docs, add the trigger to the
   canonical instruction file (`AGENTS.md`, via the Bridge note pattern) — **idempotent**,
   skip if already present:
   > ## Documentation
   > Project docs live in `docs/` (start at `docs/overview.md`, or the file map in this
   > file for a Lean repo). After completing a feature, run `doc --update` to keep them
   > current.
   This is the moment a project opts into maintaining docs, so the trigger is
   installed exactly here — not globally.

## Generating an occasional manual test record

Read [manual-tests.md](manual-tests.md) and use the available session evidence, saved output,
and actual scripts. A qualifying operation warrants `docs/tests/` even in a Minimal repo.
Create or update its procedure and capture each evidenced run separately. Mark missing
historical details as not recorded; creating documentation does not rerun the operation.

## Generating a reference doc

When the target is an external subject rather than our code, generate into `docs/reference/`
using the Reference Template. Four things differ:

- **The source is not our code.** Gather from upstream docs, changelogs and issues, from what
  this session already established, and from git history / prior notes.
- **Separate verified from documented**, and stamp every verified claim with the date and the
  version probed. A claim nobody ran is a documented claim with a link.
- **Don't invent verification.** If an unverified claim matters and the probe is cheap, run it;
  otherwise mark it as upstream's word.
- **Record the delta only.** Upstream is one link away — the doc earns its keep on what
  upstream doesn't say, gets wrong, or leaves ambiguous, plus what it means for us.

Add `docs/reference/overview.md` once ~3+ subjects exist; when they are peers, that index
carries the cross-cutting comparison table.

## Troubleshooting

### Generated docs restate function signatures
**Cause:** The generator should reference code, not copy it. **Solution:** Re-run
`--update` on the doc; signatures belong as `file:line` references (principle 3), with
prose describing the contract and why.

### A reference doc came out as a copy of the upstream docs
**Cause:** Same failure aimed outward — mirroring the canonical source instead of linking it.
**Solution:** Cut everything the linked page already says. What remains is the doc: what we
verified, where reality diverged from the docs, and the consequence for this repo. If nothing
remains, the doc wasn't warranted — a link in the relevant `tech/` doc is enough.

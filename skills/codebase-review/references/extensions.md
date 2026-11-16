# Project-local extensions

## Discovery

During recon, for each reviewed Git root, run the bundled helper:

```sh
python3 <codebase-review-skill>/scripts/discover.py --root <repo> --harness codex
```

Use the current harness (`claude`, `codex`, `cursor`, `droid`, `opencode`, or `pi`). It looks only in
project-local skill directories for `codebase-review-*/SKILL.md`. The current harness's
directory wins, followed by the other supported directories and legacy `.codex/skills`.
Multiple rendered copies count as one logical extension per repository. The output lists
every copy and fingerprints its support files too; a disagreement is a configuration gap.
Record the selected copy and the conflict; use the current harness's copy when present.
Without a current-harness copy, settle conflicting fallback copies before running that
extension. Do not merge their instructions or run each copy separately.

Read each selected skill and assess its applicability per package. Presence is opt-in, not
proof that every package uses that language. A project can add `codebase-review-project`
alongside kit extensions. The base `codebase-review` skill is not an extension. Do not scan
global skills or Loadout source catalogs: review the project's installed result.

## Extension contract

An extension's `SKILL.md` states:

- **Applies to:** project signals, scope boundaries, and exclusions.
- **Contributes to:** existing catalog aspects it enriches, and any genuinely new concern.
- **Evidence:** collector identity, command, prerequisites, artifacts, and limitations.
- **Interpretation:** what to verify before turning candidates into findings.

This is a prose convention, not a new manifest format. Extensions are supporting guidance,
not nested runs of `codebase-review`, and may contribute guidance without a collector. The
lead owns the plan, verification, grading, ledger, and fixes. Do not use `review-project`
automatically here; it belongs to diff review and has a different scope contract.

## Collection and reuse

Record extensions in the programme before approval. After approval, the lead provisions tools
outside the reviewed project and collects into `$RUN/extensions/<extension>/<scope>/<revision>/`.
Reviewers' existing "no installs" boundary remains intact. Run one collector per distinct
repository, approved SHA, package scope, resolver configuration, exclusions, and tool version;
extensions requesting the same collector share the result. Record all of these with artifact
paths and status in the programme's evidence table. On resume, reuse only an exact match.

Analyze a materialized approved commit, not the mutable working tree. Bound Git history at
that SHA. Keep baseline source/configuration separate from borrowed installed dependencies;
record dependency-resolution limitations. A tool that cannot resolve aliases, parse inputs,
or cover the planned scope has partial, unavailable, or failed coverage. An empty report is
not evidence of absence until coverage is complete for that check.

Pass each aspect only its relevant skill guidance and evidence paths, including coverage
status. Keep raw data in `$RUN`; reviewers inspect candidates against the named revision and
return findings through the existing verifier and ledger. Group shared causes before grading.
An extension may enrich Architecture or Hotspots without adding a duplicate aspect.

After integrated fixes, mark affected artifacts stale. Recollect at the new approved review
revision before using them to claim the current code is clean; retain baseline evidence for
comparison. No tool rating, complexity threshold, or cycle count assigns a finding priority.

---
name: codebase-review-typescript
description: Supply TypeScript and JavaScript structural evidence to codebase-review using dependency-cruiser, ESLint complexity, and Git churn. Use for whole-codebase import-cycle and complexity-hotspot investigation, or when discovered as a project-local codebase-review extension. Does not replace review-typescript's type-design checks or review a diff.
argument-hint: '[repository and package scope]'
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# TypeScript codebase review

## Applies to

Projects or packages containing handwritten JavaScript/TypeScript, including JSX/TSX. Resolve
the source scope and its tsconfig from the approved baseline. In a monorepo, select each
distinct package/resolver scope explicitly; do not assume the root tsconfig covers everything.
The `typescript` kit opts in. Other kits need not change, and `review-typescript` retains its
type-design scope.

## Contributes to

- **Architecture and layering:** runtime import cycles, grouped by overlapping files; barrel
  imports that pull higher-level code into lower-level modules.
- **Feature reviews and Hotspots:** functions with many control-flow paths in frequently
  changed files. File-level churn is an investigation aid, not function history or severity.

Enrich these existing aspects. Do not create a second architecture review, duplicate the
ledger, or run the full `codebase-review` workflow from this skill. Standalone use is read-only
analysis of the user-specified revision and scope; return verified concerns and coverage gaps.

## Evidence

The lead runs `scripts/collect.py` once per collection identity after plan approval. Requires
Python 3.12+, Git, Node supported by dependency-cruiser (22, 24, or 26+), and npm. The runner
installs pinned analysis packages with lifecycle scripts disabled into a separate tool cache;
it does not modify project manifests, lockfiles, hooks, or source. Install and analysis
subprocesses each have a three-minute hard deadline.

```sh
python3 <this-skill>/scripts/collect.py \
  --root <git-root> --ref <approved-sha> --scope src --tsconfig tsconfig.json \
  --output <RUN>/extensions/typescript/src/<revision>
```

Use `--scope .` when the package includes root-level entry files such as `App.tsx`. Paths are
repository-relative; omit `--tsconfig` for JavaScript without one. Add repeatable `--exclude`
regexes for generated sources not covered by the defaults, such as an API declaration folder
or generated icon components. Defaults exclude tests, declarations, build output, and common
generated paths. Inspect `inputs` in the summary to validate the actual source population.
`--days` sets the history window (180 by default, ending at the approved commit).

The collector materializes that revision in temporary storage and removes it afterwards.
It may borrow installed dependencies for module resolution, rebinding local workspace links
to the snapshot and flagging source that escapes it. This does not verify installed
versions against the baseline lockfile. Report dependency-context limits where they affect
conclusions. Missing packages and unresolved aliases require investigation, not suppression.
If a monorepo's packages have different installed dependency trees or resolver configurations,
collect separately. Keep cross-package cycle investigation at a scope that includes both sides.

Output: `summary.json`, the raw graph in `dependencies.json`, filtered ESLint diagnostics in
`complexity.json`, configuration and stderr logs. The summary carries baseline, scope, tools,
exclusions, input paths and per-check status. Exit 0 means collection completed, **not** that
there are no candidates; exit 2 means incomplete/failed collection. Preserve the report and
surface its limitation. An existing output directory must be empty; reuse recorded matching
evidence or select a new one. Do not overwrite a baseline report on resume.

No graph or complexity algorithm is implemented here. The wrapper groups dependency-cruiser
cycle reports and combines ESLint's cyclomatic complexity with Git file-commit counts. The
rank is complexity × file commits; it is not a risk score. jscpd remains an optional separate
investigation when a specific duplication concern warrants it. Existing Knip checks remain
responsible for unused-code analysis.

## Interpretation

1. Check coverage before candidates: the resolver loaded TypeScript, imports resolved, expected
   source files were included, and ESLint parsed them. Partial data may support an individual
   verified concern, but cannot establish that a scope is clean.
2. For each relevant cycle cluster, inspect representative runtime edges. Find the underlying
   dependency-direction or barrel problem and its practical maintenance cost. Many cycle paths
   through one barrel are one concern, not dozens of defects. A cycle alone proves no crash.
3. For complexity candidates, inspect responsibilities and ordinary change scenarios. Validation
   guards, optional data, and JSX may legitimately contribute branches. Do not split functions
   merely to meet a threshold. Prioritize repeated change friction with concrete evidence.
4. Return source locations at the analyzed revision, evidence, consequence, suggested direction,
   and rejected candidates with reasons. The parent owns grading and deduplication. Standalone,
   use Must Fix for verified serious failures, Should Fix for demonstrated workflow failures or
   meaningful maintenance cost, and Nice to Have for small improvements. Unverified claims stay
   outside the graded findings.

Read [tool choices and limitations](references/tools.md) when adjusting collection behavior.

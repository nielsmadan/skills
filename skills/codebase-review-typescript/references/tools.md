# Tool choices and limitations

- [dependency-cruiser](https://github.com/sverweij/dependency-cruiser): resolves the module graph
  and detects runtime cycles. Its TypeScript peer must be installed alongside it; an isolated
  CLI without that peer can silently omit most of a TS project. The runner checks availability
  and unresolved imports. It passes the baseline tsconfig, excludes pre-compilation-only edges,
  and does not follow external dependencies into node_modules. Native platform-specific
  resolution and unusual bundler conditions still need project-specific verification.
- [ESLint complexity](https://eslint.org/docs/latest/rules/complexity): cyclomatic complexity
  greater than 20 supplies candidates. The isolated config disables project and inline rules
  so this is not a rerun of application lint. No length or hook-count penalty is used.
- Git: commit counts per file within the chosen history window ending at the baseline.
  Bulk changes, renames, and young files can distort that proxy. Zero churn is not zero risk.
- [jscpd](https://github.com/kucherenko/jscpd): optional duplication evidence. Start by excluding
  generated files and tests and enable cross-format matching for TS/TSX. Repeated styles,
  component props, and short query setup often merit no abstraction; do not gate on a percentage.

These tools produce evidence, not review priorities. Pins live in `scripts/collect.py`; update
them together with resolver, grouping, baseline-isolation, and partial-result tests. A new
tool set receives a different cache directory. Avoid invoking Fallow or copying its algorithms.

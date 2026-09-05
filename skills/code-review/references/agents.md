# Review Agent Briefs

Load at Step 3c, once the aspect selection and scope are resolved. Each agent
outputs a list of issues — what the problem is, where it is (`file:line`), and why
it matters. Agents do **NOT** assign confidence scores; scoring is a separate pass.

Delegating agents pass the resolved scope through per the translation table in
Step 3c. Inline agents work directly against the file list computed in Step 3b.

## Agent 1: Bug & Logic Review (`--logic`) — inline
Operate on the file list from step 3b.
- Look for potential bugs, edge cases, race conditions
- Check null/undefined handling
- Verify error handling completeness
- Look for off-by-one errors

## Agent 2: Architecture Review (`--architecture`)
Invoke `review-architecture` with the scope-translated arguments.
- Check layering and module boundary respect
- Flag coupling/cohesion smells (god modules, circular deps, modular mirage, manager centralization)
- Verify pattern consistency with the rest of the system
- Check structural support for stated quality attributes (scalability, resilience, evolvability)
- Flag deviations from `CLAUDE.md`, `docs/`, and ADRs

## Agent 3a: Security Review (`--security`)
Operate on the file list from step 3b. Optionally also invoke `review-security` with the scope-translated arguments.
- Check for injection vulnerabilities (SQL, command, XSS, etc.)
- Verify input validation at trust boundaries
- Look for sensitive data exposure (secrets, PII, tokens in logs)
- Check auth/authz gaps

## Agent 3b: Performance Review (`--performance`)
Operate on the file list from step 3b. Optionally also invoke `review-perf` with the scope-translated arguments.
- Identify performance bottlenecks (N+1 queries, unnecessary loops)
- Check algorithmic complexity
- Check for memory leaks
- Look for expensive work in hot paths

## Agent 4: Historical Context Review (`--history`) — inline
Operate on the file list from step 3b.
- Use git blame to understand code evolution
- Check for TODO/FIXME comments that need addressing
- Identify code that may be stale or unused

## Agent 5: Test Quality Review (`--test`)
Invoke `test --review` with the scope-translated arguments.
- Check for missing edge cases and coverage gaps
- Identify brittle or flaky test patterns
- Flag over-mocking and testing implementation instead of behavior
- Ensure tests have meaningful assertions

## Agent 6: Interface Design Review (`--interface`)
Invoke `review-interfaces` with the scope-translated arguments.
- Check for pit-of-success violations (multiple ways to do the same thing, easy to misuse)
- Flag poor naming, inconsistent vocabulary, weak types
- Identify over-engineered or YAGNI interfaces
- Check encapsulation and public surface area

## Agent 7: Clean Code Review (`--clean-code`)
Invoke `review-cleancode` with the scope-translated arguments.
- Check SOLID principles (SRP, OCP, LSP, ISP, DIP)
- Flag DRY violations, YAGNI, unnecessary complexity (KISS)
- Identify code smells (god classes, long methods, feature envy, primitive obsession, shotgun surgery)
- Check design principles (Law of Demeter, separation of concerns, composition over inheritance)

## Agent 8: Language Review (`--typescript` / other `--<language>`) — conditional
Only if Step 3b.5 detected a language (or the flag was passed explicitly). For each applicable language, invoke its `review-<language>` skill with the scope-translated arguments.
- TypeScript → `review-typescript`: judgment-level type design a linter can't decide — type modeling (make invalid states unrepresentable, unions of interfaces, outputs no wider than needed), inference-vs-annotation calls, and casts/`any` that compile but hide a wrong upstream type or unvalidated boundary data. Deliberately non-overlapping with typescript-eslint.
- Swift → `review-swift`: judgment-level design a linter and the compiler can't decide — state modeling with enums and value types (make invalid states unrepresentable), optional/error/Codable modeling, concurrency isolation intent (actors, `Sendable`, state assumptions across `await`, `Task` lifetime), SwiftUI identity/lifetime/dependencies, ARC ownership, and escape hatches (`!`, `as!`, `try!`, `@unchecked Sendable`) that hide a modeling problem. Deliberately non-overlapping with SwiftLint, swift-format, and Swift 6 strict-concurrency diagnostics. Note it establishes a build-settings baseline first (language mode, default actor isolation, enabled SwiftLint rules) — isolation findings are unreviewable without it.

## Agent 9: Project-Specific Review (`--project`) — conditional
Only if Step 3b.5 found a `review-project` skill in the repo (or the flag was passed explicitly). Invoke the project's `review-project` skill with the scope-translated arguments. This agent checks issues unique to this codebase that the language-agnostic and language-specific agents don't know about.

## Agent 10: Library-Use Review (`--library-use`) — conditional
Only if Step 3b.5 found a `library-use` reference in the repo (or the flag was passed explicitly). Invoke `review-library-use` with the scope-translated arguments. This agent checks the scoped code against the repo's documented, version-specific library conventions (stale/renamed APIs, deprecated patterns, missing required setup) — non-overlapping with the language-agnostic and language-specific agents.

---

## The extensible layer (how 8, 9 and 10 plug in)

Language reviews and the project review sit on top of the 8 language-agnostic aspects:

- **Language reviews** live globally in `claude/skills/review-<language>/`. They hold checks that apply to *every* project in that language. To add a new language, create a `review-<language>` skill and add a row to the detection registry in Step 3b.5 — `code-review` will auto-route to it. Nothing else to wire.
- **The project review** is a skill the *project* defines at `.claude/skills/review-project/` for issues unique to that one codebase (conventions, gotchas, house rules that don't generalize). `code-review` calls it only when it exists — projects without one are unaffected. Minimal shape:

  ```markdown
  ---
  name: review-project
  description: Project-specific review checks for <this project>.
  argument-hint: [--staged | --unpushed | --changed | --all]
  ---
  # Review Project
  Review the scoped files (accept --staged/--unpushed/--changed/--all or a target)
  against this project's specific rules: <list the project-specific things reviewers
  keep missing>. Output findings as {file}:{line} — {issue} + fix, grouped by severity.
  ```
- **The library-use review** (`review-library-use`, global) checks the scoped code against the repo's `library-use` reference — the version-specific correct-usage conventions for its third-party libraries (generated by the `library-docs` skill). `code-review` auto-includes it when `.claude/skills/library-use/SKILL.md` (or `.agents/skills/library-use/SKILL.md`) exists; repos without one are unaffected. It flags only doc/version-specific library misuse.

# Review Agent Briefs

Load at Step 3c, once the aspect selection and scope are resolved. Each agent
outputs a list of issues — what the problem is, where it is (`file:line`), and why
it matters. Agents do **NOT** assign confidence scores; scoring is a separate pass.

Delegating agents pass the resolved scope through per the translation table in
Step 3c. Inline agents work directly against the file list computed in Step 3b.

## Rules for every agent

Include these in every brief, delegated or inline.

**Read-only, including temporarily.** Do not edit, create, delete, revert, stage or format any file in the checkout, not even to mutation-test and restore it. The other reviewers read the same files at the same time, and in past runs they reported a test agent's mutation as a real bug. To run an experiment, make a disposable copy in a scratch directory (`$SCRATCH` below) and work there:

```bash
git worktree add --detach "$SCRATCH/cr-<aspect>" HEAD
git diff HEAD --binary | git -C "$SCRATCH/cr-<aspect>" apply
# copy any untracked files in scope, run the experiment, then:
git worktree remove --force "$SCRATCH/cr-<aspect>"
```

If you cannot make a copy, describe the experiment in the finding instead of running it.

**Tag mechanical findings `autofix`.** A finding is `autofix` only when its fix has one right answer, changes no behaviour, and stays local. Examples: a doc or help line naming a symbol, flag or path the diff renamed or removed; an unexported import or helper whose last use the diff removed, with grep (string literals included) finding no other reference; a test name that names a renamed symbol. Anything that needs a design choice, touches exported or public code, or could change behaviour is a normal finding. `autofix` items skip scoring and are applied by the main thread.

## Agent 1: Correctness Review (`--correctness`, aliases `--logic` / `--defensive`)
Read `review-correctness` and apply both passes to the resolved scope and file list. Do this work yourself; do not dispatch sub-agents or launch other agent CLIs.
- Trace normal behavior, edge cases, state transitions, races, null handling, and off-by-one errors.
- Trace failure paths and changing assumptions: exhaustiveness, external unknowns, swallowed errors, masking defaults, invariants, deadlines, cancellation, and retry safety.
- When a diff extends a type or status set, search all consumers, including branches outside the initial file list.
- Verify concrete triggers and existing guarantees. Apply the skill's ownership boundaries; structural advice and capacity checks go to their specialist reviewers.

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
- Check attacker-controlled resource exhaustion and missing security bounds, including payload/read size and queue admission

## Agent 3b: Performance Review (`--performance`)
Operate on the file list from step 3b. Optionally also invoke `review-perf` with the scope-translated arguments.
- Identify performance bottlenecks (N+1 queries, unnecessary loops)
- Check algorithmic complexity
- Check for memory leaks and accumulated handles/listeners; inspect unbounded caches, buffers, queues, pagination, and file/payload reads against expected workloads
- Leave operation termination, cancellation, rollback, and lock release failures to correctness; check capacity and growth here
- Look for expensive work in hot paths

## Agent 4: Historical Context Review (`--history`) — inline
Operate on the file list from step 3b.
- Use git blame to understand code evolution
- Check for TODO/FIXME comments that need addressing
- Identify code that may be stale or unused

## Agent 5: Test Quality Review (`--test`)
Invoke `test --review` with the scope-translated arguments.
- Mutation-test only in a disposable copy (see Rules for every agent), never in the shared checkout
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

## Agent 7b: Functional Review (`--functional`)
Read `review-functional` and apply its checklist to the resolved scope or file list. Do this work yourself; do not dispatch sub-agents or launch other agent CLIs.
- Check effect placement, hidden shared state, mutation of caller-owned data, and determinism
- Check whether transformations are expressed directly and queries hide side effects
- Apply the skill's exclusions for local mutation, I/O entry points, language idioms, and justified hot-path mutation
- Exclude currying, point-free style, recursion, and monads

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

Language reviews and the project review sit on top of the 9 language-agnostic aspects:

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

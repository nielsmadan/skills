---
name: review-functional
description: Review code against pragmatic functional principles — effects pushed to the edges, no hidden shared state, no mutation of a caller's data, deterministic functions, declarative transforms. Deliberately non-dogmatic: currying, point-free style, recursion and monads are out of scope and are never findings. Triggers "review functional", "functional review", "check for side effects", "is this pure", "too much mutable state", "check global state".
argument-hint: '[--staged | --unpushed | --changed | --all]'
effort: high
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Review Functional

Language-agnostic review for the functional-programming lessons that pay off in ordinary imperative languages: testable logic, contained effects, and state you can reason about locally.

This skill is explicitly **not** a push toward functional *style*: currying, point-free code, recursion and monads are out of scope and are never findings. What it does check is whether a reader can predict what a function does from its signature and its inputs, and whether the code states what it produces rather than how it accumulated it.

## Usage

```
/review-functional                  # Review context-related code
/review-functional --staged         # Review staged changes
/review-functional --unpushed       # Review files changed across all unpushed commits
/review-functional --changed        # Review unstaged changes
/review-functional --all            # Full codebase audit (parallel agents)
```

## Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related code | Files from the current conversation context: any files the user has discussed, opened, or that you have read/edited in this session. If no conversation context exists, ask the user to specify files or use `--staged`/`--changed`/`--all`. |
| `--staged` | Staged changes | `git diff --cached --name-only` |
| `--unpushed` | Files changed across unpushed commits | `git diff --name-only $(git rev-list HEAD --not --remotes \| tail -1)^..HEAD` |
| `--changed` | Unstaged changes | `git diff --name-only` |
| `--all` | Full codebase | Glob source files, parallel agents |

`--unpushed` derives its range from `git rev-list HEAD --not --remotes` (oldest unpushed commit's parent → HEAD). If nothing is unpushed, or there is no remote/upstream (or the range walks back to the root commit) so it can't be determined reliably, stop and ask the user to pick another scope.

## Gotchas
- Default scope (no flag) uses conversation context, which may be stale from an earlier part of the session.
- **The shell is supposed to be impure.** An entry point, handler, `main`, CLI command or migration whose whole job is I/O is doing its job. Only flag an effect when it is buried inside something that reads as a calculation.
- **Local mutation is not a finding.** A loop accumulator, a builder, a swap — anything mutating a value the function created itself — is fine and idiomatic. The line is whether the mutation escapes the function.
- Language idioms differ. Go returns errors and mutates through pointers by convention; Rust's borrow checker already enforces most of this; a React component is a function by construction. Judge against the language's own idiom, not a transplanted one.
- Hot paths and large data structures are a legitimate reason to mutate in place. Check for a comment or a benchmark before flagging.

## Workflow

1. **Determine scope** based on flags (see Scope table above)
2. **Read CLAUDE.md / AGENTS.md** in the repository root for project conventions that override the defaults here
3. **Review each file** against all 5 categories in the Checklist below
4. **Parallelize** if scope has >5 files: spawn one sub-agent per category, each scanning all files for that category. Merge results and deduplicate.

   Dispatch workers that return findings without editing files. Disable delegation tools where supported; read-only access alone does not prevent delegation. Any coordinating role needs explicit subtasks, a descendant limit, and a stopping condition in its brief.
5. **Drop every finding that appears in Out of Scope below** before classifying. Do this as an explicit pass, not as a background judgement.
6. **Classify severity** for each finding:
   - **Critical**: Hidden shared mutable state, or a function that mutates data its caller still holds — bugs that reproduce only under specific call ordering
   - **High**: Business logic welded to I/O so it cannot be tested without mocks; a decision function reaching for the clock, environment, or a global
   - **Medium**: Command/query violation, manual accumulation where the language has a direct expression, a value declared then mutated across branches
   - **Suggestion**: Improvement with marginal current impact
7. **Report findings** grouped by severity using the Output Format below

## Checklist

### 1. Effect Placement

Are decisions separable from the effects that carry them out?

- Business logic interleaved with the reads that fetch its inputs and the writes that persist its results — can the decision be called with plain data and asserted on?
- A function whose name promises a calculation (`calculate`, `format`, `validate`, `resolve`, `is*`, `should*`) that also logs, writes, enqueues, or fires a request
- Effects scattered across many layers rather than concentrated at the entry points
- A test for this logic that needs three mocks to run — usually a symptom, not a testing problem

### 2. Shared & Hidden State

Does the function's result depend on anything it wasn't given?

- Module-level or class-level mutable variables read or written by functions that otherwise look self-contained
- Singletons, module caches, registries and ambient config mutated after startup (constants and immutable config are fine — they're equivalent to inlining the value)
- Order-dependent functions: a second call behaves differently because the first one left something behind
- State a caller must set up before the call for it to work, with nothing in the signature saying so

### 3. Mutation Escaping the Function

Does a caller's data change under them?

- A parameter mutated in place — array `push`/`sort`/`splice`, dict assignment, object field writes on an argument
- A getter or constructor handing back a live internal reference the caller can then mutate
- Many callers mutating one structure directly rather than going through a single owner with an explicit interface
- Mutation crossing a module boundary: if state must be mutable, it should be fenced behind one owner, not passed around for anyone to change

### 4. Determinism

Same input, same output?

- `now()`, `random()`, `uuid()`, `getenv`, locale or timezone read inside decision logic rather than passed in
- Results that vary by machine, run order, or wall-clock time
- Any place where a test had to freeze time or patch a module-level symbol to be written at all

### 5. Expression & Data Shape

Is the code saying what it means?

- A hand-written `for` loop that maps, filters, sums, flattens, or checks any/all, where the language has `map`/`filter`/`sum`/`any`/`all` or a comprehension — the direct form names the result, the loop makes the reader derive it from an accumulator and a body. Flag the small ones too; this is the default, not a last resort
- A value declared uninitialised then assigned across several branches, where one assigned-once expression would do
- Validation repeated at every layer because the data's shape never captured the guarantee — parse once at the boundary instead
- Objects constructed half-valid and completed later, so every consumer has to defend against the intermediate state

## Out of Scope

These are **never findings**, no matter how the code is written. Do not report them, do not mention them as "worth considering", and do not use them as a tiebreaker on severity.

| Not a finding | Why |
|---|---|
| A `for` loop that needs an early exit or `break`, one whose rewrite would run to four or more chained stages, or a `reduce` building a dict/object | These rewrites are regressions. Every *other* loop that is really a transformation is fair game — see category 5. |
| Absence of currying, partial application, point-free style, compose/pipe | Out of scope entirely. |
| Iteration instead of recursion | Recursion is the wrong default in any language without tail calls. Never suggest it. |
| No `Option`/`Either`/`Result`/monad where the language has exceptions or error returns | Use the language's own idiom. |
| No FP utility library (lodash/fp, Ramda, funcy, …) | Never propose adding one. |
| Mutable locals inside a function | Idiomatic everywhere. |
| In-place mutation of a large structure in a measured hot path | Performance is a real constraint. |
| Classes, methods or inheritance as such | This is not an OO review. Use `/review-cleancode` for that. |
| Existing imperative code that works and wasn't touched by this change | Report only what the scoped diff introduces or makes worse. |

## Output Format

```markdown
## Functional Review: {scope}

### Critical (hidden shared state / caller's data mutated)
- {file}:{line} - {category}: {description}
  **Impact:** {the call ordering or sequence that produces the bug}
  **Fix:** {solution with code example}

### High Priority (untestable logic / non-determinism)
- {file}:{line} - {category}: {description}
  **Fix:** {solution}

### Medium Priority
- {file} - {category}: {description}

### Suggestions
- {improvement opportunity}
```

If nothing survives the Out of Scope pass, say so plainly and stop. An empty result is a normal outcome for code that was already written this way.

## Examples

**A handler with the decision buried in it:**
> /review-functional --staged

Finds an `updateSubscription` handler that loads the account, computes the proration against `datetime.now()`, writes the new row, and sends the email — all in one function. Reports as High: the proration rule cannot be tested without a database and a frozen clock. Fix extracts `compute_proration(account, plan, at)` taking the timestamp as a parameter, leaving the handler to fetch, call, and persist.

**Caller's list mutated:**
> /review-functional --changed

Finds `normalize_tags(tags)` calling `tags.sort()` before returning a new list. The caller's list is reordered as a side effect nobody declared. Reports as Critical with the fix `sorted(tags)`.

**Nothing to report:**
> /review-functional --staged

The diff adds two pure helpers and a thin handler that calls them. Reports no findings rather than manufacturing one.

## Troubleshooting

### A suggested `map` rewrite reads worse than the loop
**Solution:** Check it against the three exclusions before reporting: an early exit, a chain of four or more stages, or a `reduce` building a dict/object. If it hits none of those, the rewrite stands — a two-stage `filter`/`map` chain is a normal finding, not an over-reach. Write the replacement out in the finding so the comparison is on the page rather than asserted.

### Everything in the file is flagged as impure
**Solution:** Check whether the file *is* the shell — a route handler module, a CLI entry point, a migration, a job runner. Those are supposed to be impure. Point the review at the modules they call instead, and report at most one finding saying the logic hasn't been separated out.

### Findings conflict with a framework's conventions
**Solution:** Frameworks that own object lifecycle (ORM models with dirty tracking, Vue/MobX reactive stores, Android/SwiftUI view state) mutate by design. Working against the framework is worse than the mutation. Note the convention and move on.

## Notes

- Effect placement and shared state carry the highest severity, because they produce bugs. Expression shape is a readability finding and caps at Medium — but report it, don't skip it.
- Purity in imperative languages works at module scale, not at every helper. Don't split a coherent 15-line function to chase it.
- A finding needs a concrete failure or a concrete test that can't be written. "This isn't pure" on its own is not a finding.
- For `--all`, use parallel agents per category (5 agents)

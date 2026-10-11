---
name: review-defensive
description: Review code for defensive-programming gaps — code that is correct today but breaks silently or crashes when an assumption changes. Headline check is closed-world branching, where a catch-all else/default handles "the last remaining case" and silently absorbs the next value an API or enum adds. Also covers unknown values from external data, swallowed errors and masking defaults, missing assertions on impossible states, missing timeouts and bounds, and the opposite failure, defensive checks that hide bugs. Triggers "review defensive", "defensive programming review", "check exhaustiveness", "missing default case", "what breaks if the API adds a value", "fail fast review", "robustness review".
argument-hint: '[--staged | --unpushed | --changed | --all]'
effort: high
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Review Defensive

Language-agnostic review for assumptions that hold today and fail silently tomorrow. The question behind every finding is: **when the world this code assumes changes — a new enum value, a new API field, a slow dependency, an error nobody expected — does the code fail loudly at the right place, or does it do the wrong thing quietly?**

Defensive programming here means *fail fast, at the boundary, on purpose* — not "check everything everywhere". Over-defense that hides bugs is itself a finding (category 6).

Code examples and the cited sources live in `references/defensive-checklist.md`. Load it when writing a fix or when a finding needs its rationale backed by a source.

## Usage

```
/review-defensive                  # Review context-related code
/review-defensive --staged         # Review staged changes
/review-defensive --unpushed       # Review files changed across all unpushed commits
/review-defensive --changed        # Review unstaged changes
/review-defensive --all            # Full codebase audit (parallel agents)
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
- **"Correct today" is not a defense.** The headline bug class produces no failing test and no wrong output until someone adds a value elsewhere. Flag a catch-all that absorbs a specific known case even when every current input is handled correctly — that is exactly when it is cheapest to fix.
- **The branch that matters may be far from the change.** When the diff adds a value to an enum, union, status set, or API response type, grep the whole repo for every branch over that type — `switch`, `match`, `if/elif` chains, lookup maps, `in (...)` sets — not just the scoped files. A new value that lands in someone else's `else` is the bug.
- **Not every final `else` is a phony default.** Apply the test: *if a new value were added tomorrow, is this branch the right behaviour for it?* `else` over an open domain (integers, free text, "any other status shows a generic badge" when that is the intended product behaviour) is fine. `else` that means "this must be `CANCELLED`" is not.
- **A compile-time check and a runtime catch-all do different jobs.** Values the compiler sees should be matched exhaustively with no `default`, so adding a case breaks the build. Values decoded from outside at runtime still need a branch for "unknown" — but that branch reports or rejects, it never reuses a known case's handler.
- Judge against the language's own mechanism (see the table in the reference file). Do not demand `assertNever` in a language that has native exhaustive `match`.

## Workflow

1. **Determine scope** based on flags (see Scope table above)
2. **Read CLAUDE.md / AGENTS.md** in the repository root for project conventions that override the defaults here
3. **Find every type the scope branches on or extends.** For each enum, union, status string set, or external response type touched by the diff, grep the repo for consumers (step one of category 1).
4. **Review each file** against all 6 categories in the Checklist below
5. **Parallelize** if scope has >5 files: spawn one sub-agent per category, each scanning all files for that category. Merge results and deduplicate.

   Dispatch workers that return findings without editing files. Disable delegation tools where supported; read-only access alone does not prevent delegation. Any coordinating role needs explicit subtasks, a descendant limit, and a stopping condition in its brief.
6. **Drop every finding that appears in Out of Scope below** before classifying. Do this as an explicit pass.
7. **Classify severity** for each finding:
   - **Critical**: A value is (or will be, once the diff lands) silently routed into another case's handler with wrong data, a crash, or a security effect; an error swallowed where it loses or corrupts data
   - **High**: A catch-all that defeats the language's exhaustiveness check even though today's inputs are handled; branching on externally sourced values with no explicit unknown-value path; a remote call with no timeout; unbounded retries
   - **Medium**: Masking defaults, a missing assertion on a state the code assumes impossible, unchecked return values, over-defense that hides bugs
   - **Suggestion**: Enabling a compiler/linter exhaustiveness flag project-wide, and other improvements with marginal current impact
8. **Report findings** grouped by severity using the Output Format below

## Checklist

### 1. Closed-World Branching (exhaustiveness)

Does adding a value to a type break the build, or silently take somebody's `else`?

- **Phony default**: an `if/elif/else` chain or `switch/default` where the last branch handles one specific known value by elimination. Fix: name every case explicitly, then make the remaining branch unreachable — `assertNever` / `assert_never` / no wildcard arm — so a new value is a compile error.
- A `default:` / `_ =>` / `else` that **silences the language's exhaustiveness check** over an enum or union the compiler already knows (`-Wswitch` stops warning; typescript-eslint's check stops reporting; JEP 441 calls a manual `default` "pernicious").
- **Negated predicates** standing in for a positive case: `if (status !== 'active') showArchived()` treats every future status as archived. Same for `not in {...}` sets and booleans derived from "is not X".
- **Lookup maps with a fallback** — `handlers[kind] ?? defaultHandler`, `dict.get(kind, fallback)` — where a missing key is a bug. Prefer a map typed over the whole key set (`Record<Kind, Handler>`, an exhaustive `match`) so a missing entry fails to compile.
- **Parallel case lists** that must stay in sync (a switch in the serializer, another in the UI, a third in the permissions check) with nothing tying them together.
- **Broad `catch`** that will also absorb exception types added later (CWE-396) — the exception-handling version of the same bug.

### 2. Unknown Values From Outside

Branches over data the compiler cannot see — API responses, DB rows, config, messages, user input.

- An external enum/status decoded straight into a closed type, so an unknown value either crashes in the decoder or is coerced into a known case. GitHub's REST API lists "adding enum values" as a non-breaking change: the client is expected to cope.
- No explicit unknown path. The decoder should produce a known value *or* an explicit unknown (protobuf `UNRECOGNIZED`, Swift `@unknown default`, a `{ kind: 'unknown', raw }` variant), and each consumer decides deliberately: skip and log, show "unsupported", or reject the request.
- Validation smeared through processing code instead of parsed once at the boundary into a type the interior can trust ("shotgun parsing"). Tolerant of fields the code does not use; strict about values it branches on.
- Crashing an entire batch, page, or sync on one unrecognized element when the element could be skipped and reported — and the reverse: silently dropping it with no log or metric.

### 3. Silent Failure and Masking Defaults

Does an error surface where it happened, or show up later as strange behaviour?

- Empty `catch`, `except: pass`, `.catch(() => {})`, `_ = err`; log-and-continue that leaves half-written state behind.
- Defaults that turn "missing" into a plausible value: `?? 0`, `|| ''`, `.get(k, [])`, `getOrDefault`, `unwrap_or_default()` — when absence means a bug or an upstream contract break rather than a legitimate empty.
- Return values and error results ignored (CWE-252): unchecked `write`/`close`, ignored `Result`, unawaited promises, `rows_affected` never compared.
- Retry or fallback paths that hide a persistent failure forever with no alert.

### 4. Invariants and Assertions

Are the states the code assumes impossible actually checked, or made unrepresentable?

- A branch or calculation that is only correct if some condition holds (non-empty list, sorted input, balance ≥ 0, exactly one match), with no assertion and no type that guarantees it.
- State modelled as a bag of optional fields whose valid combinations live only in the author's head — prefer one variant per state ("make illegal states unrepresentable"). Report the defensive consequence here; leave type-design depth to the language review.
- Assertions used for **input validation** — they are stripped under `python -O`, `NDEBUG`, and release builds in several languages. Input checks must be real errors; assertions guard programmer mistakes.

### 5. Bounds and Resources

Can a slow or misbehaving dependency, or a large input, hang or exhaust this code?

- A network, IPC, DB, or subprocess call with no timeout (both connect and request), or a timeout longer than the caller's own deadline.
- Retries with no limit, no backoff, or no jitter; retry loops nested across layers that multiply.
- Loops, recursion, queues, buffers, pagination, and file/payload reads with no upper bound on attacker- or upstream-controlled size.
- Resources (files, locks, connections, temp dirs, subscriptions) not released on every path, including the error path — use the language's scoped construct (`with`, `try`-with-resources, `defer`, `using`, RAII).

### 6. Defense That Hides Bugs

Checks that make failure quieter rather than earlier. Caps at Medium.

- Null/undefined checks on values the type system or an upstream parse already guarantees, which return early and silently skip the work.
- `try/catch` wrapped around code that cannot meaningfully fail, or around a whole function "to be safe".
- The same validation repeated at every layer of the trusted interior instead of once at the boundary.
- A "safe" fallback that keeps going on corrupt state where crashing would have surfaced the bug.

## Out of Scope

These are **never findings** here — they belong to another reviewer, or are not defects.

| Not a finding | Why |
|---|---|
| Injection, authn/authz, input validation as a security control | `review-security` owns trust-boundary security. Report only the correctness side here. |
| Mutating a caller's argument, returning a live internal reference | `review-functional` category 3 owns aliasing. |
| Validation ordering inside one function (check before expensive work) | `review-cleancode` Fail Fast. |
| Deep type design — discriminated unions, `Codable` modelling, newtypes | Language reviews (`review-typescript`, `review-swift`, …). Flag only where a branch silently depends on the missing guarantee. |
| A plain null dereference or off-by-one with no changing-assumption angle | Bug & logic review. |
| A final `else` over a genuinely open domain where it is the intended behaviour for future values | Passes the "new value tomorrow" test in Gotchas. |
| Missing defensive checks inside a private function whose only callers sit behind a boundary that already parsed the data | That is the barricade working. |
| Existing code untouched by this change — **except** branches over a type the change extended | Report only what the scoped diff introduces or exposes. |

## Output Format

```markdown
## Defensive Review: {scope}

### Critical (value silently misrouted / error loses data)
- {file}:{line} - {category}: {description}
  **Trigger:** {the concrete change or input that produces the failure, e.g. "API adds status `PAUSED`"}
  **Fix:** {solution with code example}

### High Priority (exhaustiveness defeated / unknown values / no timeout or bound)
- {file}:{line} - {category}: {description}
  **Trigger:** {…}
  **Fix:** {solution}

### Medium Priority
- {file}:{line} - {category}: {description}

### Suggestions
- {improvement opportunity, e.g. enable `-Wswitch-enum` / clippy `wildcard_enum_match_arm` / mypy `exhaustive-match`}
```

Every Critical and High finding names its **Trigger** — the specific future value, input, or failure that turns the latent assumption into a bug. A finding with no nameable trigger is not a finding.

If nothing survives the Out of Scope pass, say so plainly and stop.

## Examples

**The phony default:**
> /review-defensive --staged

Finds `if (kind === 'card') … else if (kind === 'sepa') … else { refundViaPaypal(payment) }` over a `PaymentKind` union of three values. Correct today. Reports High: the `else` means "this must be PayPal", so the next payment kind is refunded through PayPal. Fix names `'paypal'` explicitly and ends with `assertNever(kind)`.

**A new value meets an old branch:**
> /review-defensive --changed

The diff adds `PAUSED` to `SubscriptionStatus`. A grep finds `billing/charge.py` doing `if status != Status.CANCELLED: charge(sub)`. Reports Critical with Trigger "every `PAUSED` subscription is charged": the negated predicate was written when only `ACTIVE` and `CANCELLED` existed.

**Unknown value from an API:**
> /review-defensive src/integrations/

A webhook handler decodes `event.type` into a closed enum and throws on anything else, failing the whole batch. Reports High: the provider documents new event types as additive. Fix decodes to a known type or `Unknown(raw)`, logs and acknowledges unknowns, and keeps processing.

**Nothing to report:**
> /review-defensive --staged

The diff adds a field to a form with a parse step at the edge and an exhaustive `match`. Reports no findings rather than manufacturing one.

## Troubleshooting

### Every `if/else` in the file looks like a candidate
**Solution:** Only branches over a *closed set of named values* (enum, union, status strings, event types, a known list of providers) qualify for category 1. Range checks, presence checks, and free-text comparisons do not. Apply the "new value tomorrow" test to each before reporting.

### The language has no exhaustiveness check
**Solution:** Go has none built in; recommend the `exhaustive` linter. In plain JavaScript or untyped Python, recommend the explicit-cases-plus-throwing-default shape (`default: throw new Error(\`unhandled kind ${kind}\`)`), which at least fails loudly at runtime. The reference file lists each language's mechanism.

### Findings conflict with "let it crash" / fail-fast advice
**Solution:** They agree. A throwing default is fail-fast; what this review flags is a default that *does work* for a value it never anticipated. Crash loudly inside the trusted interior; at a boundary that processes many independent items, isolate per item and report.

## Notes

- Category 1 carries the highest severity because its bugs are invisible until an unrelated change lands, and nobody re-reviews the old branch when they add the value.
- Category 6 is the counterweight: defensive programming is about failing early and loudly, not about adding checks. A finding that would make the code quieter on failure is wrong.
- For `--all`, use parallel agents per category (6 agents)

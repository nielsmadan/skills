---
name: review-python
description: Python-specific code review focused on JUDGMENT-level design a linter and type checker can't decide — modeling state so invalid combinations are unrepresentable, keeping parsed data parsed instead of re-widening it to dicts, exception hierarchies that callers can act on, async task lifetime and cancellation, and boundary discipline for subprocess, filesystem and untrusted input. Deliberately does NOT duplicate ruff or mypy. Auto-invoked by `code-review` on Python projects. Triggers "review python", "python review", "asyncio review", "type modeling review".
argument-hint: '[--staged | --unpushed | --changed | --all | --multi]'
effort: high
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Review Python

Python review that covers what **ruff and a type checker cannot decide for you** — how state is
*modeled*, whether parsed data stays parsed, whether an exception hierarchy tells callers
anything, whether async work has an owner, and whether a good primitive is being bypassed.

Run on `.py` / `.pyi` files. Complements `review-cleancode` (SOLID/DRY/smells) — don't repeat it.

## Relationship to the toolchain (read first)

**Ruff's defaults changed radically in 0.16.0** and most "what ruff covers" intuition predates it:

> "Ruff now enables a much larger set of rules by default (413, up from 59)."
> — <https://astral.sh/blog/ruff-v0.16.0>

The trap: **`select` replaces the default set; `extend-select` adds to it.** A project with a
hand-written `select = [...]` is usually running *fewer* rules than an unconfigured `ruff check`.
So you cannot infer coverage from "they configured ruff" in either direction — read the config.

### Step 0 is a baseline read, not a code read

Open `pyproject.toml` (or `ruff.toml` / `setup.cfg` / `mypy.ini`) and record:

| Check | Why it changes your review |
|---|---|
| `select` vs `extend-select` | With `select`, diff their prefixes against the 413 defaults. Commonly lost: all 10 `DTZ` (naive datetime), all 10 `ASYNC`, `TRY`, `LOG`, `G`, `TC`, `PIE`, `PERF`. |
| Is the whole `B` prefix selected? | `B904` (raise-without-from) is **off by default** and its tryceratops twin `TRY200` was *removed* from ruff in v0.2.0. If `B` is absent, **nothing** checks exception chaining — then chaining is yours to review. |
| `S` / `BLE` / `SLF` / `ANN` | Only 3 of 73 `S` rules are on by default; `SLF`, `ARG`, `ANN`, `ERA`, `FBT`, `EM`, `TID` are entirely off. |
| mypy `strict`, or `check_untyped_defs` | *"By default the bodies of functions without annotations are not type checked."* Under plain mypy, an unannotated `def` is a **hole in the checker's coverage**, not a style nit — treat missing annotations as a visibility finding. |
| pytest `--strict-markers`, `filterwarnings`, `asyncio_mode` | In pytest-asyncio's default **strict** mode an `async def` test with no marker is collected and silently never awaited. It passes without running. |

**Read this to know what to stay quiet about, not to report it.** Recommending a lint or type
configuration is a *project-level* action — see §P — and belongs in an `--all` audit. On a diff
review the baseline has one job: stop you raising something a rule already covers.

## What this skill checks

**Python codebases go wrong the same handful of ways, over and over.** So the default review looks
only at what the diff introduces — a new `dict` where a dataclass belongs, a new bare `except`, a
new subprocess without a timeout, a new write that bypasses the repo's atomic writer. Repo-wide
properties (is ruff configured with `select` or `extend-select`, is mypy strict, does pytest run
with `--strict-markers`) belong to **§P**, which runs at `--all` and nowhere else.

## Usage

```
/review-python                  # Review context-related code
/review-python --staged         # Review staged changes
/review-python --unpushed       # Review files changed across all unpushed commits
/review-python --changed        # Review unstaged changes
/review-python --all            # Full codebase audit (parallel agents)
/review-python --multi          # Also get external advisor opinions
```

## Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related code | Files from the current conversation context. If no context, ask the user to specify files or use `--staged`/`--changed`/`--all`. |
| `--staged` | Staged changes | `git diff --cached --name-only` |
| `--unpushed` | Files changed across unpushed commits | `git diff --name-only $(git rev-list HEAD --not --remotes \| tail -1)^..HEAD` |
| `--changed` | Unstaged changes | `git diff --name-only` |
| `--all` | Full codebase + **§P project-level checks** | Glob `*.py`/`*.pyi`, parallel agents |
| `--multi` | Add external opinions | Combines with any scope above; invokes `second-opinion --quick` |

`--unpushed` derives its range from `git rev-list HEAD --not --remotes` (oldest unpushed commit's
parent → HEAD). If nothing is unpushed, or there is no remote/upstream (or the range walks back to
the root commit) so it can't be determined reliably, stop and ask the user to pick another scope.
Restrict the resolved file list to Python extensions before reviewing.

## Workflow

1. **Determine scope** (see table) and filter to Python files only.
2. **Read the baseline** (Step 0 above) — before reading any code.
3. **Identify the project shape** — CLI, library, backend, or data/script. §5 changes by shape,
   and a finding that is right for a library is often wrong for a CLI.
4. **Read AGENTS.md / CLAUDE.md** in the repo root for project conventions.
5. **Review each file** against §1–§6 — against what the diff introduces. Add **§P only at
   `--all`**. Load `references/async.md` when the code touches asyncio, threads or a TUI event loop;
   load `references/boundaries.md` when it touches subprocess, the filesystem, or parsing external
   input.
6. **Parallelize** if scope has >5 files: one sub-agent per category, merge and dedupe.
7. **External opinions** (if `--multi`): invoke `second-opinion --quick` with this prompt:

   ```
   Read-only Python review. Assume ruff and mypy already handle mechanical rules — do NOT repeat
   lint-level findings (mutable defaults, naive datetimes, late-binding closures, bare excepts,
   unsorted imports). Focus on DESIGN judgment: is data that was validated at the perimeter
   re-widened to dict[str, Any] so every consumer re-validates or forgets to? Are correlated
   fields modeled as a bag of optionals where a Literal-discriminated union plus match plus
   assert_never belongs? Does the exception hierarchy correspond to distinct caller responses, or
   is it bypassed by raw ValueError? Does every async task have an owner that awaits it, and does
   cancellation propagate? Is a good existing primitive (atomic write, lock, coercion helper)
   bypassed by some call sites? 300 words or less.
   ```

   Wait for all external results before proceeding.
8. **Classify severity** and **report**, grouped by severity.

## 1. Data & state modeling

The core value, and usually the root of findings in §2 and §3. A type checker checks that types
are *consistent*; only a human checks that they are *right*.

- **A `dict` standing in for a domain record.** The tell is the same field read as `t["x"]` in
  some places and `t.get("x")` in others — each call site independently guessing at optionality.
  Second tell: the schema exists only inside one constructor, and other code paths add keys that
  constructor never mentions, so the shape is genuinely open. Recommend a `TypedDict` (for a dict
  you were *handed*) or a dataclass (for a thing you *constructed*).
- **Validated at the perimeter, then re-widened.** A schema validator proves exact shapes and
  hands back `dict[str, Any]`; the type system learns nothing, so interior code either re-checks
  the same invariants in branches that can never execute, or forgets to and trusts a value nobody
  proved. Both are the same defect. *"Push the burden of proof upward as far as possible, but no
  further… Get your data into the most precise representation you need as quickly as you can."*
  (Parse, don't validate — <https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/>)
- **A declared enum that isn't enforced.** A JSON schema with `"enum": [...]` sent to an external
  service (an LLM, an API) is a *request*, not a guarantee. If the response string is written into
  the domain unchecked, an unexpected value silently matches no branch anywhere and the record
  vanishes from every rollup with no error. Recommend a `Literal` on the setter plus one perimeter
  check.
- **Bag-of-optionals where a tagged union belongs.** Fields correlated by convention —
  "`claim` is non-None exactly when `status != "busy"`" — force a guard at every use, and the
  guard usually raises an internal error for a state the code constructs itself. A string like
  `"internal: ..."` in a raise message is the author flagging an unrepresentable state. Recommend
  a `Literal` discriminator + `match` + `assert_never`, which converts the impossible branch from
  a runtime raise into a type error. *"The type checker will allow this call only if it can prove
  that the code is not reachable."* (<https://typing.python.org/en/latest/guides/unreachable.html>)
- **An enum decomposed back into mutually-exclusive booleans.** Four independent bools for five
  legal states is 16 representable states, and the exclusivity gets reassembled by an `elif` chain
  in the renderer. Keep the enum and switch on it.
- **In-band sentinels** — `""`, `-1`, or `0` overloaded to mean "none"/"not applicable", so a
  typo in a magic string is a silent no-op. Especially where a `str` field carries three values
  and one of them is emptiness.
- **Positional construction from parsed data** — `Record(*fields)` splatting a row of same-typed
  strings. Reordering the dataclass silently mis-assigns every persisted record and nothing
  type-checks it. Also flag the asymmetry where the encoder spells all fields out and the decoder
  splats, since the two halves can drift.
- **Tuples with a comment instead of a `NamedTuple`** — `list` fields whose element shape lives in
  a trailing comment and is then indexed positionally.
- **`frozen=` as a decision, not a habit.** Ask whether the object is ever a dict key or set
  member: *"If eq is true and frozen is false, `__hash__()` will be set to `None`, marking it
  unhashable."* And `__eq__` without `__hash__` (`PLW1641`, off by default) breaks the invariant
  that equal objects hash equally.
- **Structural conformance faked with alias properties** — a class growing a field that is always
  `None`, or aliasing another field, so two types can be indexed uniformly. That is a union
  wanting to be written down.

## 2. Typing judgment

- **Unannotated defs and `args: Any` are coverage holes.** Under non-strict mypy the body of an
  unannotated function is unchecked entirely. `args: Any` on a CLI command function switches
  strict mode off at the busiest boundary in the program — and the cost shows up in the tests,
  which must fabricate the contract by hand (`Namespace(...)` objects that nothing verifies).
  Report the *hole*, not the missing annotation.
- **`Any` laundering into a `Literal`.** A value from `json.loads` or a `dict[str, Any]` satisfies
  a `Literal[...]` parameter with no check. Related: a `cast(Literal[...], x)` that is correct only
  because an argparse `choices=` tuple elsewhere happens to match — two unlinked copies of one
  enumeration.
- **`@runtime_checkable` Protocol `isinstance` is not validation.** *"act as simple-minded runtime
  protocols that check only the presence of given attributes, ignoring their type signatures."*
  Flag code that treats it as a guarantee about the signature.
- **Variance: accept wide, return narrow.** `list[Shape]` as a parameter rejects a `list[Triangle]`
  because `list` is invariant; `Sequence[Shape]` accepts it. Take `Iterable`/`Sequence`/`Mapping`
  in, return the concrete type. Flag `list[X]` demanded for read-only iteration.
- **`Any` vs `object` vs `Never`** — `object` keeps checking and forces narrowing; `Any` disables
  it. `Never` is the bottom type and is what makes `assert_never` work.
- **`Self`** for fluent APIs, alternative constructors and `__enter__`; **`@override`** (PEP 698)
  to catch a base-class rename that leaves the subclass orphaned — no ruff rule covers it.
- **`@final` has no runtime effect** — flag code relying on it for safety rather than for the
  checker.

## 3. Error modeling

- **A hierarchy that exists and is bypassed.** The highest-value finding in this section. A
  project defines `AppError(exit_code, is_error)` with meaningful subclasses, then raises raw
  `ValueError` from dozens of sites — sometimes in the same function as a correct raise. Every
  distinction the hierarchy exists to carry is discarded at the top-level handler.
- **An exception that escapes the top-level handler.** Check what the entry point actually
  catches against what the code actually raises. A bare `RuntimeError` matches neither
  `except AppError` nor `except (DomainError, ValueError)` even when `AppError` subclasses
  `RuntimeError` — subclass relationships run the wrong way for this.
- **A catch so broad it flattens the hierarchy.** `except (FileNotFoundError, OSError, ValueError,
  RuntimeError)` catches the entire domain when the domain's base *is* `RuntimeError`, collapses
  every exit code to 1, and drops a deliberate exit 0.
- **Cross-function exception flow.** A module's `discover()` guards `json.JSONDecodeError` and its
  `parse()` doesn't, while the caller catches only `OSError`. `JSONDecodeError` and
  `UnicodeDecodeError` are both `ValueError`, not `OSError` — one corrupt input file kills the
  whole scan. This needs reading two functions and the caller; no rule reaches it.
- **A builtin IO exception used as a domain signal**, then caught too broadly — `raise
  FileNotFoundError("no config here")` caught by an `except FileNotFoundError` that also swallows
  a genuinely missing binary and reports success.
- **Result-or-error smuggled in-band** — `-> RunResult | str` where `str` means failure, or
  `-> tuple[str | None, int | None]`. Nothing forces a new caller to check. Recommend a failure
  dataclass or an exception.
- **Computed diagnostics discarded** — a `skipped` counter incremented and never returned, so the
  user is told "deleting 4" with no sign the 5th was silently retained. `F841` stays quiet because
  `+=` counts as a read.
- **A handler that catches but does nothing.** Detection of a blind `except` is `BLE001`/`E722`;
  whether the handler *is* the bug is yours. Distinguish "genuinely don't care" from "lost the
  diagnostic". `contextlib.suppress` spanning ten statements suppresses far more than the one
  call it was written for — *"should be used only to cover very specific errors where silently
  continuing with program execution is known to be the right thing to do."*
- **Chaining**, only if `B904` is not reachable per Step 0.

## 4. Async, concurrency & boundaries

**Load `references/async.md`** when the code touches asyncio, threads or a TUI event loop, and
**`references/boundaries.md`** for subprocess, filesystem and untrusted input. The two headline
items, because they recur everywhere:

- **Blocking work reachable from the event loop *indirectly*.** Ruff's `ASYNC22x` rules are
  call-site-local: they flag a literal `subprocess.run` inside an `async def`, not a named function
  three frames above one. An `async` handler that calls something which scans a filesystem, sleeps,
  and shells out is invisible to them and freezes the UI completely.
- **A good primitive that call sites bypass.** Find the repo's best existing atomic-write, lock,
  or coercion helper, then check who doesn't use it. Divergent copies of the same primitive with
  different safety guarantees — only one of which `fsync`s — are a real and common defect.

## 5. Project shape

A finding that is right for a library is often wrong for a CLI. Establish the shape first.

| Shape | What changes |
|---|---|
| **CLI** | Exit codes: `subprocess.call` returns a **negative** value for a signal-terminated child, so passing it to `sys.exit` turns Ctrl-C into shell status 254. Results to stdout, diagnostics to stderr, so pipelines work. `input()` without an `EOFError` guard crashes under `< /dev/null` and in CI. Interactive prompts belong at the CLI edge, not in the library layer where every caller must arrange a TTY. **`print` is correct here — never flag `T201`.** |
| **Library** | `__all__` is the typed-API contract, not decoration: *"Imported symbols are considered private by default"*, and `import X as X` / `from Y import X as X` are what re-export. Flag a `py.typed` package with neither. Add `NullHandler` and never configure logging — *"the configuration of handlers is the prerogative of the application developer who uses your library."* Never call `sys.exit`; raise. No import-time side effects. Variance is caller compatibility, so §2's accept-wide/return-narrow is a compatibility rule, not a style one. |
| **Backend** | The bug is the *third* combination: an `async def` handler containing blocking I/O — worse than either pure option, since FastAPI runs a plain `def` handler in a threadpool. Django: `SynchronousOnlyOperation` from ORM calls under a running loop, the `a`-prefixed queryset variants, and N+1 via missing `select_related`/`prefetch_related`. Plus request-scoped state parked in module globals, and missing timeouts on outbound calls. |
| **Data / scripts** | Reproducible seeds; float and NaN handling (`math.isclose` needs a positive `abs_tol` to compare against zero at all, and NaN is never close to anything including itself); chunked reads over `read()`. Where a hand-written table of examples guards a real invariant, recommend hypothesis. |

## 6. Test quality

Module-level state and import-time side effects are in `references/boundaries.md` §8 — they
belong to the same review pass as the other boundary items. What follows is tests.

- **Asserting private state instead of rendered behaviour** — `app._inbox`, `app._active_tab`.
  A change that correctly updates the list but fails to render it still passes.
- **Fixed-iteration event-loop pumps as a worker wait** — `for _ in range(5): await pilot.pause()`,
  with the number varying across tests. Every such test is timing-dependent by construction;
  recommend the framework's real wait (`workers.wait_for_complete`).
- **Monkeypatching private internals, and the double-patch tell** — the same name patched in two
  modules because `from X import y` creates a second binding. A third importer silently gets the
  real function and the stub quietly stops covering it, with no failure.
- **Tests fabricating an untyped contract** — hand-built `Namespace(...)` objects standing in for
  a real parser; a downstream cost of §2's `args: Any`.
- **Negative assertions that pin nothing** — `assert "Metro" not in text` passes for every wrong
  renderer that happens not to print that word. Keep the ones naming a specific thing that would
  otherwise have happened (`assert not path.exists()` after a delete, `assert secret not in err`).

## P. Project-level checks — `--all` only

Repo-wide configuration. It changes rarely, so raising it on a diff review is noise.

- **ruff `select` vs `extend-select`.** `select` *replaces* the 413-rule default set, so a project
  with a hand-written `select` is usually running fewer rules than an unconfigured `ruff check`.
  Diff the prefixes against the defaults and report what's lost — commonly all 10 `DTZ` (naive
  datetime), all 10 `ASYNC`, plus `TRY`, `LOG`, `G`, `TC`, `PIE`, `PERF`. Recommending
  `extend-select` fixes the whole category at once. Note that 18 opinionated `E`/`F` rules were
  *removed* from the 0.16 default set (`E401`, `E402`, `E701`–`E703`, `E711`–`E714`, `E721`,
  `E731`, `E741`–`E743`, `F403`, `F405`, `F406`, `F722`), so a repo selecting bare `E`/`F` must
  keep those listed explicitly to retain them.
- **mypy strictness.** Plain mypy does not check the bodies of unannotated functions at all. Where
  a codebase has many partially-annotated defs, stage it: `check_untyped_defs`, then
  `disallow_incomplete_defs`, then `strict`.
- **pytest configuration** — `--strict-markers`, `--strict-config`, `filterwarnings = ["error"]`,
  a coverage threshold, and whether `asyncio_mode` matches how the tests are actually marked.
- **Whether the repo has a good primitive that call sites bypass** — atomic write, lock, coercion
  helper. Finding the divergent copies is a whole-repo sweep; a diff review only checks whether
  *this* change bypassed it.
- **Encoding discipline across all readers**, which is only visible in aggregate.

## Do NOT flag these

- **Anything in §P, on a diff review.** Lint and type configuration are project properties; this
  diff did not change them.

Already mechanical, or wrong. Check Step 0 before suppressing — if the project's config doesn't
reach the rule, fold it into the one-time recommendation instead of reporting each occurrence.

- **Mutable default arguments** (`B006`), function calls in defaults (`B008`), mutable class
  defaults (`RUF012`) — and the dataclass decorator raises on them anyway.
- **Late-binding closures in loops** (`B023`), `lru_cache` on methods (`B019`).
- **Naive datetimes** — all ten `DTZ` rules are on by default. The best-covered category ruff has.
- **Blind `except` *detection*** (`BLE001`, `E722`) — the judgment of whether the handler does
  anything useful stays yours.
- **PEP 695 generic syntax** (`UP046`, `UP047`), import sorting (`I001`), modern-syntax rewrites
  (`UP`).
- **`print` in a CLI** — see §5.
- **Demanding Pydantic.** A stdlib dataclass plus a perimeter validator is a complete answer; a
  validation library is a dependency decision, not a review finding.
- **Demanding `ty`.** It is 0.0.x with no API stability commitment. `pyrefly` is production-ready
  if mypy's speed is a real problem — but mypy `--strict` is not a finding to begin with.
- **Docstring coverage** (`D`) unless the project already enforces it.

## Severity

- **Critical**: crashes, corrupts, or silently loses data at runtime — an unvalidated external
  value entering the domain where no branch matches, a truncate-in-place write to a file another
  program depends on, malformed-row skipping combined with a rewrite, an exception that escapes
  the top-level handler on a reachable path.
- **High**: will cause bugs as the code evolves — invalid states representable in a load-bearing
  model, a hierarchy bypassed so exit codes are lost, blocking work on the event loop, a task with
  no owner, shared mutable state mutated across an `await`, a missing timeout on the slowest call.
- **Medium**: `dict` where a dataclass belongs, in-band result/error unions, coverage holes from
  unannotated defs, variance, encoding and atomicity inconsistencies, discarded diagnostics.
- **Suggestion**: `NamedTuple` over commented tuples, `@override`, `__all__` on a library,
  naming and ergonomics where the code is awkward rather than buggy.

## Output Format

```markdown
## Python Review: {scope}

### Baseline
{Project shape, and whether `B904` is reachable (it decides whether exception chaining is yours to
review). **At `--all` only:** the §P results. On a diff review, omit this block unless something in
it changes what you reported.}

### Critical (crash / data loss / corruption reachable)
- {file}:{line} — {category}: {description}
  **Why it's not a ruff or mypy finding:** {what judgment this needed}
  **Impact:** {what breaks}
  **Fix:** {model change / boundary validation / real failure path — with code}

### High (design problems that will cause bugs)
- {file}:{line} — {category}: {description}
  **Fix:** {solution}

### Medium (modeling, typing, boundaries)
- {file}:{line} — {category}: {description} — {suggested change}

### Suggestions
- {opportunities}
```

If `--multi` was used, append one subsection per advisor that responded (titled with the advisor's
name as reported by `second-opinion`), then a **Cross-Model Agreement** subsection.

## Examples

**Validated data re-widened:**
> /review-python --staged

A 400-line schema validator proves the exact shape of each resource spec, then stores the result
as `dict[str, Any]`. Downstream, `provision()` re-checks `isinstance(spec.get("range"), list)` and
raises on an unknown `type` — branches that cannot execute, and which permanently depress the
coverage number. Reports High: a `TypedDict` union keyed on a `Literal` `type` field turns the
final `else` into an `assert_never` type error and deletes five defensive raises. Not a mypy
finding: `Any` conforms to every consumer, so mypy has no discriminator to narrow on and cannot
see the branches as unreachable.

**Blocking the event loop indirectly:**
> /review-python --changed

An `async` worker pushes a progress modal, then calls `cmd_roundup(...)`, which three frames down
scans every session directory, calls `time.sleep`, runs `shutil.rmtree`, and issues N sequential
LLM subprocesses with no `timeout=`. Reports High — the modal cannot paint and keystrokes are dead
until it returns; fix with `asyncio.to_thread` or `thread=True`, and add a timeout. `ASYNC221` is
silent because the subprocess call is not lexically inside the `async def`.

**Hierarchy bypassed:**
> /review-python

`errors.py` defines `ApplicationError(exit_code, is_error)` with `UsageError` (exit 2) and
`MissingRecipeError` (exit 0). The code raises 61 raw `ValueError`s, four of them in a function
that raises `UsageError` correctly on the line above. Reports High — every one renders identically
through the generic handler and exits 1, discarding the distinctions the hierarchy exists to carry.
`TRY002` only catches `raise Exception`; `ValueError` is a perfectly ordinary raise.

## Troubleshooting

### Findings overlap with ruff or mypy
**Solution:** Check Step 0 — whether the project's config actually *reaches* that rule. Ruff's
defaults are large but `select` replaces them, so coverage is not inferable from the presence of a
config. If the rule runs, drop the finding. If it doesn't, fold it into the one-time baseline
recommendation rather than reporting each occurrence.

### Can't tell whether a `dict` should be a dataclass
**Solution:** Ask where it was born. Handed to you by `json.loads`, a subprocess, or a wire format
and passed straight through → `TypedDict` describes it honestly. Constructed by your own code, or
carrying invariants across function boundaries → a dataclass, validated once at construction. The
deciding tell is whether any consumer has to ask "is this key present?" about a field the
producer always sets.

### Can't tell whether a broad `except` is wrong
**Solution:** Read what the handler does, not what it catches. Re-raising as a domain error, or
logging with the traceback and continuing a loop that must not die, is fine. Returning `None` to a
caller that cannot distinguish "absent" from "failed" is not. And check the *callers* — a handler
can be correct while the caller's own `except` clause fails to match what actually propagates.

## Notes

- Model first, parse second, annotate third. Most `Any` and most defensive re-validation dissolve
  once the underlying data is modeled correctly.
- Respect project conventions in AGENTS.md / CLAUDE.md — a codebase may deliberately use plain
  dicts at a boundary, or standardize on returning `Result`-shaped tuples.
- Don't be dogmatic: `TypedDict` migrations, wrapper types, and exhaustive `match` all have costs.
  Recommend them where they prevent real bugs, not everywhere they are possible.
- **Test code:** patching *your own* module's private helper in a focused unit test is defensible;
  patching a name in two places because of import bindings, or asserting on private attributes
  instead of rendered output, is not. Also flag `sleep`-based synchronization and real clock,
  network, or home-directory access in unit tests.
- Sources: the ruff 0.16 release notes and rule documentation (astral.sh); the CPython
  `asyncio`, `dataclasses`, `enum`, `contextlib`, `subprocess` and `logging` docs; the typing spec
  and guides at typing.python.org (exhaustiveness, distributing, re-export); PEP 654 and PEP 698;
  Alexis King, "Parse, don't validate"; Hynek Schlawack on hashes and equality; mypy's command-line
  reference. ruff and the type checker own the mechanical rules referenced above.

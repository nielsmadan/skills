---
name: review-rust
description: Rust-specific code review focused on JUDGMENT-level design that clippy and the compiler cannot decide — modeling state so invalid combinations are unrepresentable, sum types that get flattened into correlated primitives, closed vocabularies carried as strings, units that live only in comments, error types that lose the cause at a boundary, ownership and trait choices, unsafe justifications, async task ownership and cancellation, and semver commitments. Deliberately does NOT duplicate clippy, and opens by checking which of its 839 lints the project actually runs. Auto-invoked by `code-review` on Rust projects. Triggers "review rust", "rust review", "clippy review", "type modeling review".
argument-hint: '[--staged | --unpushed | --changed | --all | --multi]'
effort: high
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Review Rust

Rust review that covers what **clippy and the compiler cannot decide for you** — how state is
*modeled*, whether errors carry what callers need, whether ownership and trait choices reflect a
decision, whether an `unsafe` justification is true, and what the public surface commits you to.

Run on `.rs` files. Complements `review-cleancode` (SOLID/DRY/smells) and `review-cli` (the
interface a binary presents) — don't repeat either.

## Relationship to clippy (read first)

Clippy ships **839 lints**. 489 are enabled by default — 67 at **deny** (`correctness`) and 422 at
**warn** (`suspicious`, `style`, `complexity`, `perf`). The remaining 333 are allow-by-default:
`pedantic` (143), `restriction` (132), `nursery` (53), `cargo` (5).

**So "clippy is clean" means much more than people assume, and the judgment layer is narrower than
it looks.** These are all **warn-by-default** — never report them:

| You might think it's judgment | It's already a lint | Group |
|---|---|---|
| `&String`/`&Vec<T>`/`&Path`-vs-`&str` parameters | `ptr_arg` | style |
| `as_`/`to_`/`into_` self-convention | `wrong_self_convention` | style |
| Holding a `std`/`parking_lot` lock across `.await` | `await_holding_lock`, `await_holding_refcell_ref` | suspicious |
| Getter naming | `misnamed_getters` | suspicious |
| `Result<_, ()>` | `result_unit_err` | style |
| `Box<dyn T>` in a field, `Vec<Box<T>>`, `&Box<T>` | `borrowed_box`, `vec_box`, `box_collection` | complexity/perf |
| Missing `# Safety` on a public `unsafe fn` | `missing_safety_doc` | style |
| `new()` conventions, `From` over `Into` | `new_ret_no_self`, `new_without_default`, `from_over_into` | style |
| Over-complex types, too many arguments | `type_complexity`, `too_many_arguments` | complexity |
| Fat `Err` variants, fat enum variants | `result_large_err`, `large_enum_variant` | perf |

What survives is narrower and more interesting. `ptr_arg` fires on `&String` but says nothing about
whether the function should take `String`, `&str`, `impl Into<String>`, or `Cow<'_, str>` — that's
the design question. `await_holding_lock` catches `std` guards but not `tokio::sync::Mutex` guards,
because holding those across `.await` is legal; whether it's *wise* is judgment.

### The lint baseline is a silencer, not a finding

Read the `[lints]` tables, `#![deny]`/`#![warn]`, `clippy.toml` and the edition **so you don't
report what a lint already covers**. Recommending a lint configuration is a *project-level* action
— see §P — and belongs in an `--all` audit, not in a diff review.

At `--all`, if the project runs default clippy only, recommend a `[lints]` table (package or
workspace; respected since Cargo 1.74) **once**, then move on — never hand-flag what a lint group
would catch. At a narrower scope, the baseline only tells you what to stay quiet about.

```toml
[workspace.lints.clippy]
nursery = { level = "warn", priority = -1 }
pedantic = { level = "warn", priority = -1 }
missing_errors_doc = "allow"   # enable only with intent to write them
must_use_candidate = "allow"   # low value outside a published library
```

**The `priority` field is not optional here.** Entries are otherwise unordered, so a group plus an
exemption silently doesn't work without the negative priority on the group. Member crates then opt
in with `[lints] workspace = true`.

Expect `nursery` to carry most of the value and `pedantic` to be dominated by two doc lints. Note
that several lints people assume are pedantic are actually **nursery** — `use_self`,
`redundant_clone`, `needless_collect`, `option_if_let_else`, `missing_const_for_fn` — which means
they carry a real false-positive rate; say so when recommending them. `module_name_repetitions` is
**restriction**, not pedantic.

Worth recommending individually, by situation: `undocumented_unsafe_blocks` +
`multiple_unsafe_ops_per_block` (any crate with `unsafe`), `future_not_send` (a library exposing
futures), `unwrap_used`/`expect_used`/`indexing_slicing` (only where panic-freedom is an actual
policy — otherwise pure noise), and rustc's `unreachable_pub` and `missing_debug_implementations`.

**Load `references/clippy-scope.md`** when you are unsure whether something is already mechanical.

## What this skill checks

**Rust design decisions are made once; the ways they get violated recur with every change.** So the
default review looks only at what the diff introduces — a new enum flattened into bools, a new
`pub` item, a new `unsafe` block, a new error variant that drops its cause. Whole-crate properties
(is there a `[lints]` table, is the `pub`/`pub(crate)` discipline coherent, are the crate layers
respected) belong to **§P**, which runs at `--all` and nowhere else.

## Usage

```
/review-rust                  # Review context-related code
/review-rust --staged         # Review staged changes
/review-rust --unpushed       # Review files changed across all unpushed commits
/review-rust --changed        # Review unstaged changes
/review-rust --all            # Full codebase audit (parallel agents)
/review-rust --multi          # Also get external advisor opinions
```

## Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related code | Files from the current conversation context. If no context, ask the user to specify files or use `--staged`/`--changed`/`--all`. |
| `--staged` | Staged changes | `git diff --cached --name-only` |
| `--unpushed` | Files changed across unpushed commits | `git diff --name-only $(git rev-list HEAD --not --remotes \| tail -1)^..HEAD` |
| `--changed` | Unstaged changes | `git diff --name-only` |
| `--all` | Full codebase + **§P project-level checks** | Glob `*.rs`, parallel agents |
| `--multi` | Add external opinions | Combines with any scope above; invokes `second-opinion --quick` |

## Workflow

1. **Determine scope** and filter to Rust files.
2. **Read the lint baseline** — every `[lints]` table, `#![deny]`/`#![warn]`, `clippy.toml`, and the
   edition. Run `cargo clippy --workspace --all-targets -- -D warnings` to confirm the stated
   baseline is actually clean, then `-W clippy::nursery -W clippy::pedantic` and record the top
   lints by count. That tells you what to *recommend* rather than what to *report*.
3. **Read AGENTS.md / CLAUDE.md** for project conventions.
4. **Identify the shape** — published library, internal library, binary, or workspace. §5 and the
   semver material only bind on a published public API.
5. **Review against §1–§8** — against what the diff introduces. Add **§P only at `--all`**. Load
   `references/api-and-semver.md` for public-surface and edition questions;
   `references/async-and-unsafe.md` when the code has either.
6. **Parallelize** if scope has >5 files: one sub-agent per category, merge and dedupe.
7. **External opinions** (if `--multi`): invoke `second-opinion --quick` with this prompt:

   ```
   Read-only Rust review. Assume clippy's 489 default lints already ran clean — do NOT repeat
   anything lint-level (&String params, wrong_self_convention, await_holding_lock, missing safety
   docs, too_many_arguments). Focus on DESIGN judgment: where does the code compute an answer as an
   enum and then flatten it into correlated bools or Options for storage? Is a closed vocabulary
   carried as &str with a catch-all arm that returns a valid value instead of an error? Do raw
   integers and floats carry units that live only in comments? Does an error type lose the cause or
   the ErrorKind at a crate boundary? Is a newtype dropped at one boundary and re-parsed with a
   fallback? Does each unsafe SAFETY comment actually discharge the precondition? Does every spawned
   task have an owner? 300 words or less.
   ```

   Wait for all external results before proceeding.
8. **Classify severity** and **report**, grouped by severity.

## 1. Type modeling — the core

Rust's type system is unusually able to encode invariants, so the gap between *what the code knows*
and *what the types say* is the highest-value thing to review.

- **A sum type computed correctly, then flattened into correlated primitives for storage.** The
  single most common judgment defect. The code matches on a proper enum, destructures it into a
  `(bool, bool)` or `(Phase, bool)` tuple, and stores that — at which point the illegal combination
  is representable, constructible and serializable. The tell is a `match` whose arms all produce a
  tuple of primitives. Ask: *where does this code already know the answer as an enum, and where
  does it stop knowing?*
- **Correlated `Option` fields.** Two `Option`s that are always both-`Some` or both-`None`, with
  the pairing enforced by convention. Watch for a `let ... else` at the consumer that silently
  reclassifies the mixed state rather than erroring. `option_option` (pedantic) catches only the
  nested case; correlated *separate* fields are invisible to every lint.
- **A return type one variant too wide, evidenced by `unreachable!`.** When one variant is
  documented as "always the sole element" or "handled above", the function should return a narrower
  type. An `unreachable!("handled above")` is not a code smell in itself — it is *evidence* about
  the signature.
- **A closed vocabulary carried as `&str`/`String`/`u8`, with a catch-all that returns a valid
  value.** Parallel tables in unrelated modules (or in another language's source) that must agree,
  reconciled by `_ => Ignore` or `other => { warn; default }`. The catch-all makes every drift
  well-formed. An enum makes the tables one closed set and turns extension into a compile error.
- **A raw integer or float whose unit lives only in a comment.** The same field carrying seconds in
  some entries and milliseconds in others; per-tick rates sitting beside per-second rates; a
  `0..20` attribute scale documented once in a doc comment. In numeric code this is the
  highest-density finding class and the compiler is structurally blind to all of it.
- **A newtype dropped at one boundary.** A domain type kept everywhere except one struct, where it
  becomes `String` — then re-parsed downstream with `unwrap_or_else(Generate::new)`, which mints a
  fresh identity rather than failing. Also forces stringly comparisons at every join.
- **Two integers that name different things.** An index into a `Vec` and a domain id, both small
  unsigned ints, freely substitutable by the compiler and passed to the same functions. Newtypes
  plus `Index<MyIdx>` keep the ergonomics.
- **Invariants documented in prose instead of encoded.** A doc comment saying "the caller MUST clear
  X before calling" is a design finding, not documentation: any new caller compiles and gets the
  bug the comment describes. Private fields with a mutator, or returning the obligation as part of
  the result, encode it once.
- **Silent-fallback parsing that invents a sentinel.** `unwrap_or(Key::new("?", 0))` fabricates a
  value that then flows through the system and grows its own special handling. `Option<T>` makes the
  absence real. Distinguish this from a *documented* fallback that preserves data for a later
  validation pass — that one can be right, but note that the fallback type now means two things.
- **Nested `Option` for tri-state** — `Option<Option<T>>` as leave/clear/set. It works and is
  usually documented, which is the tell that the type isn't saying it.
- **`#[non_exhaustive]` on public enums and structs.** *Adding it later is a major breaking change;
  adding it at birth is free.* Its absence on a public error enum or a trait's associated types is a
  decision that usually wasn't taken. Note there is **no API-guideline item** for this — the source
  is the Cargo semver chapter and the Reference.

## 2. Error modeling

- **`thiserror` for libraries, `anyhow` for applications** remains the 2026 consensus, with
  `color-eyre`/`miette` where errors are *shown to humans*. Verify the split is respected across a
  workspace rather than assuming — two crates in one workspace doing opposite things is the tell
  that it was two sittings, not a position.
- **An error stringified at a crate boundary.** `Error::Io(String)` built by a
  `fn io<E: Display>(e: E)` helper discards the path, the operation *and* the `ErrorKind`, so no
  caller can branch on not-found versus permission-denied. Especially worth flagging when the same
  workspace does it correctly elsewhere with `#[from]`. Check `#[source]` usage — zero occurrences
  in a crate with a custom error type means nothing renders a cause chain.
- **`map_err(|_| ...)` discarding the cause.** The `|_|` is the tell. A spawn failure reported as
  "not installed or not on PATH" hides `EACCES`, `ENOMEM`, and a bad working directory.
- **One variant carrying many distinct causes.** The inverse of the usual smell: when empty input,
  an unknown keyword, an out-of-range offset and an arithmetic overflow all produce a byte-identical
  error, callers cannot respond differently even if they want to.
- **`{:?}` in a user-facing message.** Reaching for `Debug` because the type has no `Display` is the
  path of least resistance and renders internals to users.
- **`unwrap`/`expect`/`panic!` quality is bimodal and clippy can't tell the halves apart.**
  `unwrap_used` is restriction-level and flags every occurrence equally. The judgment is whether
  each `expect` message names a real invariant a reader can check against the lines above it. Same
  for `unreachable!` — one naming an invariant enforced elsewhere is good; a bare `unreachable!()`
  guarding a case the enclosing match arm already bound is a sign the match should have bound it.
  Panics in a *library* are a different question from panics in a binary.
- **Fallible work whose failure is unobservable** — a `pub fn` returning `()` that routes failures
  to a warnings buffer the caller must remember to drain.

## 3. Ownership & borrowing

After clippy's `ptr_arg` territory, what's left:

- **`Cow<'_, str>` in a return type or field.** It earns its place when the borrowed case is common
  and the owned case rare — a normalizer that usually returns its input unchanged, called per item
  per pass. It does not earn its place as a hedge, because it infects callers with a lifetime.
  (`ptr_arg` already covers `Cow` *parameters*, so the judgment is confined to returns and fields.)
- **`Rc<RefCell<T>>`: smell or legitimate.** The test is whether the aliasing genuinely can't be
  known statically — observer graphs, trees with parent pointers, interpreter environments. It's a
  smell when it works around a borrow that restructuring would fix.
- **A `Mutex` in a codebase with no concurrency.** Grep for `async`, `thread::`, `Arc`, channels
  first. A `Mutex` reached for purely to get interior mutability behind `&self` is `RefCell`'s job,
  or `&mut self`'s. The tell is poison recovery (`unwrap_or_else(|e| e.into_inner())`) on a lock
  that can never be contended.
- **Clone-to-satisfy-the-borrow-checker.** `redundant_clone` (nursery) catches the provable subset.
  The residue is a clone that is load-bearing but signals the ownership model is wrong — count them,
  then say which are forced by a trait signature and which are capitulation. A by-value trait
  adopted for a *foreign-language* boundary that has no foreign implementors yet imposes the cost on
  every caller today; that's a decision worth naming, not the individual clones.
- **Take-owned vs borrow-and-clone** — the API guidelines' C-CALLER-CONTROL: if a function requires
  ownership, take it rather than borrowing and cloning internally.

## 4. Trait & API design

- **`impl Trait` in argument position is a semver commitment, not shorthand.** It removes turbofish
  from your API, and switching between it and `<T: Trait>` breaks callers in both directions,
  because it changes the number of generic arguments.
- **Static vs dynamic dispatch should be decided, not defaulted.** The guideline is to decide early
  whether a trait is used as an object or as a bound. `Box<dyn Trait>` is right when the
  implementation is chosen at runtime from config; generics are right when it's chosen at the call
  site.
- **`async fn` in a trait makes it not dyn-compatible** — a hidden `Future` type is an opaque return
  type. A trait with `async fn` cannot be `Box<dyn Trait>` without a workaround. (The term is
  **dyn compatibility**; "object safety" is the former name, still used by the API guidelines and
  the Cargo book.)
- **Conspicuously missing derives.** Not the mechanical ones — `derive_partial_eq_without_eq` is
  nursery and will find those. The judgment is whether `Ord`/`Hash`/`Default` are *semantically*
  meaningful, and the orphan-rule consequence: a missing impl on a public type is a downstream dead
  end nobody else can fix.
- **Traits with one implementor** — raise as a question ("is this earning its indirection?"), not as
  a rule. There is no citable authority for it.
- **Sealed traits** for a trait you want to extend without breaking implementors, documented as
  sealed in rustdoc.
- **Inconsistent spellings of one method across a workspace** — `as_str(&self)` on a `Copy` enum in
  one crate and `const fn as_str(self)` in another.

## 5. Public surface & semver — what the diff adds

- **A new `pub` item that should be `pub(crate)`.** Ask whether anything outside the crate calls it,
  or whether it is `pub` only so a sibling module can reach it. A new `pub` **field** is worse: it
  pins the representation and means no invariant on it can hold.
- **A new `pub` field or enum variant on a published type** — adding a field when all fields are
  public, or a variant to an enum without `#[non_exhaustive]`, is a **major** breaking change. And
  `#[non_exhaustive]` cannot be retrofitted cheaply: adding it later is itself major, adding it at
  birth is free.
- **A new non-defaulted trait item** breaks every implementor.
- **A new inherent method that shares a name with a trait method the type implements.** The only
  entry in the Cargo semver chapter whose failure mode is a *silent runtime behaviour change* rather
  than a compile error — and exactly the class `cargo-semver-checks` documents itself as unable to
  catch. Worth a specific look whenever a diff adds an inherent method.
- **A parameter switched between `impl Trait` and `<T: Trait>`** — that changes the number of
  generic arguments and breaks callers in both directions.
- **Tightened generic bounds** on an existing public signature.

Whole-crate surface questions — the `pub`/`pub(crate)` ratio, glob re-exports, crate layering, a
dependency used only from tests — are §P.

## 6. `unsafe`

**Load `references/async-and-unsafe.md`** if the crate has any. Most of the mechanical layer is
already on (`missing_safety_doc` is style/warn; `not_unsafe_ptr_arg_deref` is correctness/**deny**).
The judgment residue is small and high-value:

- **Whether the `SAFETY:` comment is true**, and whether it discharges the actual precondition or
  merely restates the code. 100% human.
- **The soundness test, from the std dev guide:** inside a *safe* function, a `SAFETY:` comment
  "must not depend on anything from the caller beside properly constructed types and values." If the
  justification appeals to caller behaviour, the function should be `unsafe`.
- A crate with **no `unsafe` at all** — say so and move on. `unsafe_code = "forbid"` in a `[lints]`
  table is worth crediting.

## 7. Async & concurrency

**Load `references/async-and-unsafe.md`.** Headlines:

- **Do not tell people to use `tokio::sync::Mutex` to avoid holding a lock across `.await`.** Tokio's
  own docs say the opposite: the std mutex is preferred in async code, and the async mutex is *more
  expensive*. The right advice is the std mutex plus not holding it across `.await` — which clippy
  already enforces.
- **Cancellation safety** — `select!` in a loop over a non-cancel-safe future (`read_exact`,
  `write_all`, `Mutex::lock`, `Semaphore::acquire`) loses data or queue position. Tokio documents
  which is which. Note cancelling something non-cancel-safe is not automatically wrong.
- **A spawned task with no owner.** A bare `tokio::spawn` whose `JoinHandle` is dropped outlives its
  logical parent and its errors go nowhere; a `JoinSet` aborts its tasks on drop.
- **`spawn_blocking` tasks cannot be aborted**, so a shutdown path that waits on them can hang
  indefinitely.

## 8. Performance & tests

**Performance — flag only what's evident from the code's role**, never anything needing a claim
about relative cost without a measurement. Say "worth measuring", not "this is slow".

- **An operation whose cost is structurally wrong for its role** — a single-item lookup that walks
  and parses an entire directory, called inside a loop, when an index holding exactly that mapping
  already exists. This is the one performance finding that's usually unambiguous.
- **Nested linear scans over collections sized by the domain**, where a map built once before the
  loop fixes several at a time. Distinguish honestly from scans bounded by a single-digit count.
- **Allocation in a hot loop** — a fresh `Vec` per tick, or a `.clone()` of a `Copy`-eligible type
  per entity per tick. Note when the file already knows the fix (a reused, `clear()`ed buffer
  elsewhere).
- **Do not repeat the folklore.** Clippy disowns it: `inline_always` is "meant to be deactivated by
  everyone doing serious performance work"; `large_enum_variant` says "Always measure the change
  this lint suggests". Struct-of-arrays is not automatically right at small entity counts.

**Tests:**

- **A determinism test that compares two integers and a length** for a system whose premise is
  reproducibility. `assert_eq!(r1.events, r2.events)` is usually available for free; a hashed golden
  value is better.
- **Tolerance assertions wide enough that no plausible bug fails them** — a crash test wearing
  behavioural clothing.
- **A test that recomputes the expected value the way the code computes it**, so it passes for any
  implementation of that shape — and can lock in a model the constants say is wrong.
- **`#[should_panic]` without `expected`**, tests mutating process env (`unsafe` in edition 2024),
  and a hand-rolled multi-seed sweep that is a property test missing only the library.
- Credit real property tests, conformance suites run against every implementor, and architecture
  fitness tests where they exist.

## P. Project-level checks — `--all` only

Whole-crate properties. They change rarely, so reporting them on a diff review buries the findings
that matter. **Never raise these outside an `--all` audit.**

- **Lint configuration.** No `[lints]` table, or one that leaves `nursery` off. Run
  `-W clippy::nursery -W clippy::pedantic` and report the top lints by count, then recommend a
  configuration — including any lint whose advice conflicts with a stated property of the system,
  which needs an explicit `allow` with a reason rather than being left off by accident.
- **`pub` discipline as a whole.** Count `pub(crate)` against `pub fn`; a ratio near zero means
  `pub` was the default rather than a decision. Grep each `pub` item from the crate's own binary and
  `tests/` — items reachable from neither are internal. Recommend rustc's `unreachable_pub` rather
  than listing instances.
- **Dead `pub` fields.** In a lib crate `pub` suppresses `dead_code`, so a field written and never
  read produces no diagnostic at all. This sweep is only worth doing whole-crate.
- **Glob re-exports** (`pub use module::*` at the crate root), which silently admit every new `pub`
  item to the public API.
- **Crate layering** in a workspace — a lower crate knowing about a higher one, a dependency used
  only from `#[cfg(test)]` code that belongs in `[dev-dependencies]`. Credit an architecture fitness
  test where one exists.
- **Edition migration hazards.** In a crate recently moved to 2024, check the two *silent* changes:
  `if let` temporary scope and tail-expression drop order both change when destructors run, with no
  diagnostic at the use site. A lock guard or RAII type in a scrutinee or tail position behaves
  differently.
- **Tooling.** `cargo-nextest` and `cargo-deny` in CI; `cargo-semver-checks` for a published
  library; `miri` for any crate with `unsafe`; `proptest` where an invariant is stated. State the
  ceilings honestly — see `references/clippy-scope.md`.

## Do NOT flag these

- **Anything in §P, on a diff review.** Lint configuration, `pub` ratios, layering and tooling are
  project properties; this diff did not change them.
- **Everything in the toolchain table above** — all warn-by-default.
- **Anything an enabled `[lints]` group already gates.** Check the config first.
- **`&String`/`&Vec<T>` parameters** — `ptr_arg`, style/warn. This is the most common false
  judgment finding.
- **Naming conventions, `new_without_default`, `from_over_into`** — all lint-level.
- **`#[inline(always)]` absence, boxing large variants unconditionally, struct-of-arrays** — see §8.
- **`C-NONEXHAUSTIVE-ENUM`** — it does not exist. The API guidelines have no `#[non_exhaustive]`
  content at all.
- **`error-chain`-era error advice** — C-GOOD-ERR's examples predate `thiserror`; its rules
  (`impl Error`, `Send + Sync + 'static`, never `()`) still hold, its exemplar does not.
- **Demanding `#![deny(warnings)]`** — the Cargo semver chapter warns it can break builds when new
  lints land.
- **Claiming `cargo-semver-checks` or Miri prove anything.** The former documents real false
  negatives (type changes, generics, feature subsets); Miri detects UB only in executions your tests
  actually drive and "cannot ensure code soundness".

## Severity

- **Critical**: an illegal state reachable in a load-bearing model; a fabricated sentinel identity
  entering persistent storage; unsound `unsafe`; a data race.
- **High**: a sum type flattened so the invalid combination is emitted; a closed vocabulary with a
  silent catch-all; a unit mismatch in the same field; an error losing the cause at a boundary; a
  spawned task with no owner; structurally wrong cost in a hot path; a `pub` field carrying an
  invariant.
- **Medium**: correlated `Option`s; missing `#[non_exhaustive]` on a published enum; `Mutex` in
  single-threaded code; missing semantically-meaningful derives; glob re-exports; a return type one
  variant too wide; dead `pub` fields.
- **Suggestion**: `Cow` opportunities, newtypes where mix-ups are possible but not evidenced, sealing
  a trait, naming consistency, lint-group adoption.

## Output Format

```markdown
## Rust Review: {scope}

### Baseline
{Edition, and whether `clippy -D warnings` is clean. **At `--all` only:** the §P results, including
what `-W nursery -W pedantic` would add by count and the lint-configuration recommendation. On a
diff review, omit this block entirely unless the baseline is broken.}

### Critical (illegal state reachable / unsound / data loss)
- {file}:{line} — {category}: {description}
  **Why it's not a clippy finding:** {what judgment this needed}
  **Impact:** {what breaks}
  **Fix:** {model change — with code}

### High (design problems that will cause bugs)
- {file}:{line} — {category}: {description}
  **Fix:** {solution}

### Medium (modeling, errors, ownership, public surface)
- {file}:{line} — {category}: {description} — {suggested change}

### Suggestions
- {opportunities}
```

If `--multi` was used, append one subsection per advisor that responded (titled with the advisor's
name as reported by `second-opinion`), then a **Cross-Model Agreement** subsection.

## Examples

**A sum type flattened at birth:**
> /review-rust --staged

`map_event` returns a proper `MappedAction` enum, and two lines later it becomes
`let (phase, running) = match ... { Update(p) => (p, true), Remove => (Phase::Idle, false) }`, stored
as `StatusEvent { phase, running }`. Reports High: `(Phase::Working, running: false)` is
representable, serializable and meaningless — and a synthetic-event helper elsewhere emits exactly
that combination today. Clippy sees a well-typed tuple.

**A unit living in a comment:**
> /review-rust --all

`EventSpec.timeout: u64` holds seconds in 44 entries and milliseconds in 13, distinguished only by
a comment above one table. Reports High — a `Duration` converted per agent at render time, or a
`Timeout::Secs/Millis` enum, removes the class. No lint can see that one `u64` means two things.

**A return type one variant too wide:**
> /review-rust

`resolve_identity` returns `Vec<Outcome>`, and one variant is documented as "always the sole element
of the vec". The caller scans for it, handles it, then matches it again with
`Outcome::ScanRejected { .. } => unreachable!("handled above")`. Reports Medium: return
`Result<Vec<Outcome>, RejectReason>`. The `unreachable!` is not the defect — it's the evidence.

## Troubleshooting

### Findings overlap with clippy
**Solution:** Check the toolchain table and `references/clippy-scope.md`. Clippy's default set is
489 lints, and `correctness` is **deny**, not warn — "clippy is clean" rules out more than people
assume. If the rule exists but the project doesn't run its group, fold it into the one-time baseline
recommendation rather than reporting occurrences.

### Can't tell whether a clone is load-bearing
**Solution:** Check what forces it. A trait taking parameters by value forces every caller to clone
— then the finding is about the trait's signature, not the call sites. Run `-W clippy::redundant_clone`
to remove the provably-removable ones first, then review what's left.

### Not sure whether a `pub` item is really public API
**Solution:** Grep for it from the crate's own binary and `tests/`. An item reachable from neither is
`pub` only so a sibling module can call it — `pub(crate)` is the honest spelling. `unreachable_pub`
(rustc, allow-by-default) mechanizes this; recommend it rather than listing instances.

## Notes

- Model first, then errors, then ownership. Most `String`-typed errors and most defensive fallbacks
  dissolve once the data is modeled correctly.
- Respect project conventions in AGENTS.md / CLAUDE.md.
- Don't be dogmatic: newtypes, typestate, sealing and `Cow` all have costs. Recommend them where
  they prevent real bugs, not everywhere they're possible.
- **A lint can be wrong for a codebase, and that's worth saying.** `suboptimal_flops` suggests
  `mul_add`, which is a *fused* operation — different rounding, with a software fallback on targets
  without FMA. In a simulation whose premise is "same seed, same result", taking that advice breaks
  reproducibility. The right outcome is an explicit `allow` with a comment saying why, not a group
  left off by accident.
- Sources: the clippy lint list (839 lints, group and level verified per-lint); the Cargo book's
  `[lints]` and SemVer Compatibility chapters; the Rust Reference (`#[non_exhaustive]`, dyn
  compatibility, `impl Trait`); the Rust Edition Guide for 2024; the std dev guide's safety-comment
  policy; tokio's docs on `select!` cancellation safety, `Mutex` and `spawn_blocking`; the Rust API
  Guidelines (last substantive change 2024-03 — a stable classic, not a maintained standard).

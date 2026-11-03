# Clippy scope: what is already mechanical

Load when unsure whether a finding duplicates a lint. Verified 2026-09-14 against the stable
(1.98) lint list — 839 lints total, counted from the rendered index rather than recalled.

## Group sizes and default levels

| Group | Default level | Count |
|---|---|---|
| `correctness` | **deny** | 67 |
| `suspicious` | warn | 83 |
| `style` | warn | 158 |
| `complexity` | warn | 143 |
| `perf` | warn | 38 |
| `pedantic` | allow | 143 |
| `restriction` | allow | 132 |
| `nursery` | allow | 53 |
| `cargo` | allow | 5 |
| *(deprecated)* | — | 17 |

**489 lints are on by default** (422 warn + 67 deny). `correctness` being **deny** rather than warn
is the detail people get wrong, and it changes what "clippy is clean" means.

## Already warn-by-default — never report these

| Concern | Lint | Group |
|---|---|---|
| `&String` / `&Vec<T>` / `&Cow<_>` parameters | `ptr_arg` | style |
| `as_`/`to_`/`into_` self conventions | `wrong_self_convention` | style |
| Getter naming | `misnamed_getters` | suspicious |
| `Result<_, ()>` | `result_unit_err` | style |
| Lock held across `.await` (std / parking_lot / RefCell) | `await_holding_lock`, `await_holding_refcell_ref`, `await_holding_invalid_type` | suspicious |
| `&Box<T>`, `Vec<Box<T>>`, `Box<String>`/`Box<Vec<_>>` in a field | `borrowed_box`, `vec_box`, `box_collection` | complexity / perf |
| Missing `# Safety` on a public `unsafe fn` | `missing_safety_doc` | style |
| Dereferencing a raw pointer in a safe public fn | `not_unsafe_ptr_arg_deref` | **correctness (deny)** |
| `new()` not returning `Self`; `new()` without `Default`; `Into` where `From` fits; inherent method shadowing a std trait | `new_ret_no_self`, `new_without_default`, `from_over_into`, `should_implement_trait` | style |
| Over-complex types; too many arguments | `type_complexity`, `too_many_arguments` | complexity |
| Fat `Err` variant; fat enum variant | `result_large_err`, `large_enum_variant` | perf |
| Async block yielding an async block | `async_yields_async` | **correctness (deny)** |
| Unused `unsafe`; dead code; refs to `static mut` | `unused_unsafe`, `dead_code`, `static_mut_refs` | rustc, warn/deny |
| Redundant allocation, unnecessary `to_owned`, manual memcpy, slow vec init | `redundant_allocation`, `unnecessary_to_owned`, `manual_memcpy`, `slow_vector_initialization` | perf |

`ptr_arg`'s own rationale is the argument a reviewer would otherwise make by hand: *"Requiring the
argument to be of the specific type makes the function less useful for no benefit; slices in the
form of `&[T]` or `&str` usually suffice."*

**What survives as judgment in those areas** is narrower: `ptr_arg` says nothing about whether a
function should take `String`, `&str`, `impl Into<String>` or `Cow<'_, str>`; `await_holding_lock`
does not cover `tokio::sync::Mutex` guards, because holding those across `.await` is legal.

## Lints whose group people misremember

Recommending a nursery lint as though it were pedantic misrepresents its false-positive rate.

| Lint | Actually | Often assumed |
|---|---|---|
| `use_self` | nursery | pedantic |
| `redundant_clone` | nursery | perf |
| `needless_collect` | nursery | perf |
| `option_if_let_else` | nursery | pedantic |
| `missing_const_for_fn` | nursery | pedantic |
| `or_fun_call` | nursery | perf |
| `module_name_repetitions` | restriction | pedantic |
| `format_push_string` | pedantic | restriction |
| `string_to_string` | **deprecated — does nothing** | restriction |

## Worth recommending, by situation

Each of these converts a recurring manual review comment into a compiler check — which is the most
useful thing a review can do, because it *removes* work from the judgment layer permanently.

| Lint(s) | Group | When |
|---|---|---|
| `undocumented_unsafe_blocks` + `multiple_unsafe_ops_per_block` | restriction | Any crate with `unsafe`. The second exists so "each unsafe operation must be independently justified". |
| `missing_errors_doc`, `missing_panics_doc` | pedantic | A published library. Mechanizes API-guideline C-FAILURE. Expect a large one-time cost — enable with intent or `allow` with intent, not by accident. |
| `redundant_clone` | nursery | Any codebase where clone count is a question. |
| `derive_partial_eq_without_eq` | nursery | Finds the missing-`Eq` derives directly. |
| `needless_pass_by_value`, `trivially_copy_pass_by_ref` | pedantic | Ownership-signature review. |
| `future_not_send` | nursery | A library exposing futures; keeps them usable on multi-threaded runtimes. |
| `unwrap_used`, `expect_used`, `indexing_slicing`, `panic_in_result_fn` | restriction | **Only** where panic-freedom is an actual policy. Otherwise pure noise — they flag every occurrence equally, including the correct ones. |
| `allow_attributes` + `allow_attributes_without_reason` | restriction | Forces `#[expect(..., reason = "...")]`, which self-removes when stale. |
| `cast_possible_truncation`, `cast_precision_loss`, `cast_sign_loss` | pedantic | Numeric code. Note the docs say these are allow-by-default *because* the behaviour is usually intended — so they need auditing individually, not blanket adoption. |

Useful rustc lints, all allow-by-default: `unreachable_pub` ("`pub` items not reachable from crate
root"), `missing_debug_implementations`, `missing_docs`, `missing_copy_implementations`,
`elided_lifetimes_in_paths`, `let_underscore_drop`, `unused_qualifications`, `variant_size_differences`,
`must_not_suspend`.

`rust_2018_idioms` is a **group**, not a lint — it expands to `bare-trait-objects`,
`unused-extern-crates`, `ellipsis-inclusive-range-patterns`, `elided-lifetimes-in-paths`,
`explicit-outlives-requirements`. The last is the noisy one. `rust_2024_compatibility` is the
migration group for a pre-2024 crate.

## The `[lints]` table

Respected since Cargo 1.74, in both package and workspace form. The tool is the part before `::`;
no `::` means `rust`.

```toml
[workspace.lints.rust]
unsafe_code = "forbid"

[workspace.lints.clippy]
nursery = { level = "warn", priority = -1 }
pedantic = { level = "warn", priority = -1 }
missing_errors_doc = "allow"
must_use_candidate = "allow"
```

```toml
# member crate
[lints]
workspace = true
```

**`priority` is required whenever a group is combined with an exemption.** It is "a signed integer
that controls which lints or lint groups override other lint groups: lower (particularly negative)
numbers have lower priority, being overridden by higher numbers." Without the negative priority on
the group, the entries are unordered and the exemption silently may not win. This is the single most
common mistake in a `[lints]` table.

Cargo applies these only to the current package, not to dependencies.

## A lint can be wrong for a codebase

`suboptimal_flops` (nursery) suggests `a.mul_add(b, c)` for multiply-then-add — one rounding instead
of two, genuinely more accurate. It is also a *different number*, and `f64::mul_add` falls back to a
software implementation on targets without an FMA instruction, so results can differ between
machines. In a simulation whose premise is reproducibility, taking that advice is actively harmful.

The right outcome is an explicit `allow` with a comment saying why — not a group left off by
accident, which produces the right behaviour for the wrong reason and will silently reverse the
moment someone enables `nursery`.

Generalize the check: when recommending a group, scan what it would actually fire on, and name any
lint whose advice conflicts with a stated property of the system (determinism, bit-exactness, a
documented output format).

## Adjacent tooling — the one-time recommendation set

Versions verified 2026-09-14.

| Tool | Version | Worth it for |
|---|---|---|
| `cargo-nextest` | 0.9.144 | Everything. Process-per-test isolation. |
| `cargo-deny` | 0.20.2 | Everything in CI. Licenses, advisories, banned/duplicate deps. |
| `cargo-semver-checks` | 0.50.0 | Any published library — with the caveat below. |
| `proptest` | 1.11.0 | Any round-trip or stated invariant. Dominant by a wide margin (47M recent downloads vs quickcheck's 10.7M). |
| `cargo-fuzz` | 0.13.2 | Parsers, anything reading untrusted bytes. |
| `miri` | — | Any crate with `unsafe`. |
| `cargo-udeps` | 0.1.61 | Nightly-only, lowest traffic of the set. |

Two honesty caveats to carry into any recommendation:

- **`cargo-semver-checks` documents its own ceiling**: "Will `cargo-semver-checks` catch every semver
  violation? No, it will not — not yet!" It explicitly misses breaking *type* changes, generics and
  lifetime changes, and breakage that only appears under a subset of features. It is
  low-false-positive by design ("If they do occur, they are considered bugs") but has real false
  negatives — so a clean run is not proof.
- **Miri cannot establish soundness.** It detects UB in the executions your tests actually perform.
  "Miri is green" is evidence about the test suite, not about the `unsafe`.

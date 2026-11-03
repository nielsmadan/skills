# Public surface, semver & edition 2024

Load when reviewing a public API, a workspace's crate boundaries, or a crate that recently moved
editions. Verified 2026-09-14 against Rust stable 1.98.1.

---

## Rust API Guidelines — use with a currency warning

<https://rust-lang.github.io/api-guidelines/checklist.html> is still the canonical checklist, but it
is **effectively dormant**: the last substantive content change was 2024-03, and the two most recent
commits are a broken-link fix and an autolink cleanup. Treat it as a stable classic, not a
maintained standard. Three concrete staleness markers:

- **C-GOOD-ERR cites `error-chain` twice** as the exemplar error library. `error-chain`'s last
  release is 0.12.4, **2020-08-02**. Its *rules* still hold; its examples predate `thiserror`.
- **C-OBJECT says "object safe"**. The Reference now notes: *"This concept was formerly known as
  object safety."* Current term: **dyn compatibility**.
- **There is no `#[non_exhaustive]` guidance at all** — the attribute landed after the guidelines
  went quiet. In particular `C-NONEXHAUSTIVE-ENUM` **does not exist**; do not cite it. Use the Cargo
  semver chapter and the Reference.

### The items that are genuine judgment

| Item | The core, quoted | Why it's judgment |
|---|---|---|
| **C-CUSTOM-TYPE** | "Core types like `bool`, `u8` and `Option` have many possible interpretations. Use a deliberate type (whether enum, struct, or tuple) to convey interpretation and invariants." | The highest-value item. `fn_params_excessive_bools` only counts bools past a threshold — it can't see that *one* bool is a domain distinction. |
| **C-COMMON-TRAITS** | "crates that define new types should eagerly implement all applicable, common traits" … "There is no way for `webapp` to add `Display` to `Url`, since it defines neither." | The orphan-rule argument is the point: a missing impl is a downstream dead end nobody else can fix. |
| **C-NEWTYPE** | "cannot accidentally be called with a `Kilometers` value. The compiler will remind us to perform the conversion, thus averting certain catastrophic bugs." | Pure design. |
| **C-STRUCT-PRIVATE** | "Making a field public is a strong commitment: it pins down a representation choice, and prevents the type from providing any validation or maintaining any invariants on the contents of the field, since clients can mutate it arbitrarily." | Ties directly to semver and to invariants. |
| **C-VALIDATE** | "Rust APIs do not generally follow the robustness principle… Instead, Rust code should enforce the validity of input whenever practical." | This is "parse, don't validate" in the official checklist. |
| **C-SEALED** | "The empty private `Sealed` supertrait cannot be named by downstream crates… We are free to add methods to `TheTrait` in a non-breaking release" | A permanent API commitment either way. |
| **C-GENERIC vs C-OBJECT** | C-GENERIC: "The fewer assumptions a function makes about its inputs, the more widely usable it becomes." C-OBJECT: "**decide early on** whether the trait will be used as an object or as a bound on generics." | These pull against each other; the guideline's own answer is to decide, not to default. |
| **C-CALLER-CONTROL** | "If a function requires ownership of an argument, it should take ownership… rather than borrowing and cloning" | |
| **C-STRUCT-BOUNDS** | "Generic data structures should not use trait bounds that can be derived or do not otherwise add semantic value." Never bound on `Clone, PartialEq, PartialOrd, Debug, Display, Default, Error, Serialize, Deserialize, DeserializeOwned`. | A backward-compatibility hazard nothing lints. |
| **C-FAILURE** | "It is not necessary to document all conceivable panic cases… But when in doubt, err on the side of documenting more panic cases." | The guideline explicitly calls it a judgment call. |
| **C-GOOD-ERR** | "Error types should always implement the `std::error::Error` trait" … "should implement the `Send` and `Sync` traits" … "Never use `()` as an error type" | The `Error + Send + Sync + 'static` bound is durable. `'static` is what "allows the trait object to be used with `Error::downcast_ref`". |

---

## `#[non_exhaustive]`

From the Reference: *"The `non_exhaustive` attribute indicates that a type or variant may have more
fields or variants added in the future."* And crucially: **"Within the defining crate,
`non_exhaustive` has no effect."**

Downstream consequences, quoted: non-exhaustive variants "cannot be constructed with a
StructExpression (including with functional update syntax)"; "When pattern matching on a
non-exhaustive enum, matching on a variant does not contribute towards the exhaustiveness of the
arms"; "It's also not allowed to use numeric casts (`as`) on enums that contain any non-exhaustive
variants."

**The decisive asymmetry:** adding it later is a **major** breaking change; adding it at birth is
free. The Cargo book says so directly — *"Mark structs, enums, and enum variants as
`#[non_exhaustive]` when first introducing them, rather than adding `#[non_exhaustive]` later on."*

The textbook case is a public error enum. A trait designed for out-of-crate implementors has the
same problem in reverse: one new error variant breaks every downstream implementation.

---

## Semver — the non-obvious breakages

From the Cargo book's SemVer Compatibility chapter, which is unusually concrete and anchors each
rule.

| Change | Category | Quote |
|---|---|---|
| Adding a public field when all fields are public | **Major** | "this will break any code that attempts to construct it with a struct literal" |
| Adding a private field when all fields are public | **Major** | — |
| Adding an enum variant (no `#[non_exhaustive]`) | **Major** | "It is a breaking change to add a new enum variant if the enum does not use the `#[non_exhaustive]` attribute." |
| Adding a non-defaulted trait item | **Major** | "This will break any implementors of the trait." |
| Adding a *defaulted* trait item | **Possibly-breaking** | "this can introduce an ambiguity if a method of the same name exists in another trait." |
| **Adding an inherent method** | **Possibly-breaking** | "in some cases the collision can cause problems if the name is the same as an implemented trait item with a different signature." **"Note that if the signatures match, there would not be a compile-time error, but possibly a silent change in runtime behavior (because it is now executing a different function)."** |
| Adding a trait item that breaks dyn compatibility | **Major** | "It is safe to do the converse (making a non-object safe trait into a safe one)." |
| Tightening generic bounds | **Major** | (loosening is minor) |
| Capturing more generics in RPIT | **Major** | "Starting in Rust 2024, all lifetime parameters are unconditionally captured… the default is maximally compatible, requiring you to be explicit when you want to capture less, **which is a SemVer commitment.**" |
| Adding `#[non_exhaustive]` later | **Major** | see above |

**The inherent-method row deserves emphasis.** It is the only entry in the chapter whose failure
mode is a *silent runtime behaviour change* rather than a compile error — and it is precisely the
class `cargo-semver-checks` documents itself as unable to catch. Worth flagging in review when a new
inherent method shares a name with a trait method the type implements.

One more, which constrains how hard a reviewer should push for strict lints:

> "Beware that it may be possible for this to technically cause a project to fail if they have
> explicitly denied the warning… **Denying warnings should be done with care** and the understanding
> that new lints may be introduced over time."

So don't demand `#![deny(warnings)]`.

---

## `impl Trait` in argument position is a semver commitment

From the Reference:

> "`impl Trait` in argument position is syntactic sugar for a generic type parameter like
> `<T: Trait>`, except that the type is anonymous and doesn't appear in the GenericParams list."

> "**Note** For function parameters, generic type parameters and `impl Trait` are not exactly
> equivalent. With a generic parameter such as `<T: Trait>`, the caller has the option to explicitly
> specify the generic argument for `T` at the call site using GenericArgs, for example,
> `foo::<usize>(1)`. **Changing a parameter from either one to the other can constitute a breaking
> change for the callers of a function, since this changes the number of generic arguments.**"

So APIT is not merely shorter — it removes turbofish from the API, and switching later breaks
callers in both directions.

## Dyn compatibility

The review-relevant rules from the Reference: a dyn-compatible trait's dispatchable functions must
not have type parameters, and must "Not have an opaque return type; that is, **Not be an `async
fn`**… Not have a return position `impl Trait` type." Associated constants and generic associated
types also disqualify. `AsyncFn`, `AsyncFnMut` and `AsyncFnOnce` are not dyn-compatible.

Live 2026 tension worth raising rather than prescribing: **`async fn` in traits is stable but makes
the trait not dyn-compatible.** Such a trait cannot be `Box<dyn Trait>` without a workaround
(`async-trait`, or a manual `-> impl Future` / `Pin<Box<dyn Future>>`). Raise it as a design
question; the recommended workaround's current status is not settled enough to prescribe.

---

## Edition 2024

Shipped in Rust 1.85.0. The review-relevant changes:

| Change | Effect |
|---|---|
| `unsafe_op_in_unsafe_fn` | Now **warns by default** — "detects calls to unsafe operations in unsafe functions without an explicit unsafe block". |
| Unsafe functions | `std::env::set_var`, `std::env::remove_var` and `CommandExt::before_exec` are now `unsafe` — a **hard error** without a block, not a warning. |
| `static_mut_refs` | Now **deny** by default. "Merely taking such a reference in violation of Rust's mutability XOR aliasing requirement has always been instantaneous undefined behavior, **even if the reference is never read from or written to**." |
| RPIT capture | "all in-scope generic parameters, including lifetime parameters, are implicitly captured when the `use<..>` bound is not present." |
| `if let` temporary scope | Temporaries from the scrutinee "will be dropped before the program enters the `else` branch instead of after." |
| Tail expression temporary scope | Temporaries in a tail expression "may now be dropped before local variables". |
| `gen` | Reserved keyword. |
| Prelude | `Future` and `IntoFuture` added. |
| Cargo | `edition = "2024"` implies `resolver = "3"`. |

**The two that matter most in review are the silent ones.** `if let` temporary scope and
tail-expression drop order change *when destructors run*, with no diagnostic at the use site. For a
lock guard or any RAII type in a scrutinee or tail position, behaviour differs between editions
silently. Check these specifically in a crate that recently migrated.

**A trap when reading lint defaults:** `rustc -W help` reports `unsafe_op_in_unsafe_fn` as `allow` —
that is the *pre-2024* default. The level is edition-dependent. The same applies to
`static_mut_refs`. Never conclude a lint is off from the flat list alone.

The `set_var` change has a useful review consequence: **precedence and config logic that reads the
environment must be factored into a pure function taking its inputs as parameters**, because a test
that mutates process env now needs an `unsafe` block and is racy under a parallel test runner.
Crediting a codebase that did this is worthwhile; flagging one that mutates env in tests is a real
finding.

---

## `pub`, dead code, and the detection hole

In a library crate, `pub` suppresses `dead_code`. A `pub` field that is written and never read
produces **no diagnostic at all**, even under `cargo clippy --all-targets`. A write counts as a use.

So in a lib crate, *"is this field ever read?"* is a question only a reviewer can answer. Practical
checks:

- Grep each suspicious `pub` field for reads specifically, not mentions.
- Count `pub(crate)` against `pub fn`. A ratio near zero means `pub` was the default rather than a
  decision — and then some `pub` items exist only so a sibling module can reach them.
- Grep each `pub` item from the crate's own binary and `tests/`. Items reachable from neither are
  internal. `unreachable_pub` (rustc, allow-by-default) mechanizes exactly this — recommend it
  rather than listing instances.
- Glob re-exports (`pub use module::*` at the crate root) mean any new `pub` item silently joins
  the public API, and give names multiple valid paths. `clippy::wildcard_imports` (pedantic) finds
  the import side.
- An `#[allow(dead_code)]` on a `pub` field is doubly redundant and usually a confession.

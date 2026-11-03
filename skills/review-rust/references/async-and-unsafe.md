# Async, concurrency & unsafe

Load when the crate has either. Both are conditional sections — a crate with no `async` and no
`unsafe` should have this said plainly and skipped, not padded.

---

# Async

## Which mutex — the folklore runs backwards

The most repeated piece of async-Rust advice is "never hold a lock across `.await`, use
`tokio::sync::Mutex`". Tokio's own documentation says the opposite:

> "**Contrary to popular belief, it is ok and often preferred to use the ordinary `Mutex` from the
> standard library in asynchronous code.**"

> "The feature that the async mutex offers over the blocking mutex is the ability to keep it locked
> across an `.await` point. This makes the async mutex more expensive than the blocking mutex, so
> the blocking mutex should be preferred in the cases where it can be used."

> "A common pattern is to wrap the `Arc<Mutex<...>>` in a struct that provides non-async methods for
> performing operations on the data within, and only lock the mutex inside these methods."

So the correct guidance is: **std mutex, not held across `.await`** — which `clippy::await_holding_lock`
(suspicious, warn-by-default) already enforces. Reach for `tokio::sync::Mutex` only when the guard
genuinely must span an await, typically for an IO resource.

The judgment residue is *which* mutex, and whether a `tokio::sync::Mutex` held across an await is
there because it must be or because someone was avoiding a lint.

## Cancellation safety

Tokio's `select!` docs define this precisely, and the definition is the review test:

> "Cancellation safety describes what happens when a future is dropped before it completes."

> "If you have a future that has not yet completed, then it must be a no-op to drop that future and
> recreate it."

> "To determine whether your own methods are cancellation safe, look for the location of uses of
> `.await`. This is because when an asynchronous method is cancelled, that always happens at an
> `.await`. If your function behaves correctly even if it is restarted while waiting at an `.await`,
> then it is cancellation safe."

Tokio ships the lists, which makes this checkable rather than vibes:

- **Cancel-safe:** `mpsc::Receiver::recv`, `broadcast::Receiver::recv`, `watch::Receiver::changed`,
  `TcpListener::accept`, `AsyncReadExt::read`, `AsyncWriteExt::write`, `StreamExt::next`.
- **Not cancel-safe — data loss:** `read_exact`, `read_to_end`, `read_to_string`, `write_all`.
- **Not cancel-safe — queue position lost:** `Mutex::lock`, `RwLock::read`, `RwLock::write`,
  `Semaphore::acquire`, `Notify::notified`.

**The review check is `select!` in a loop over something from the second or third list.** But this
is a judgment call, not a ban — tokio says so:

> "Be aware that cancelling something that is not cancellation safe is not necessarily wrong. For
> example, if you are cancelling a task because the application is shutting down, then you probably
> don't care that partially read data is lost."

Also flag a custom `async fn` used in a `select!` branch whose own cancellation safety was never
considered — the method above (look at every `.await` and ask whether restarting there is a no-op)
is the thing to apply.

## Task ownership

A bare `tokio::spawn` whose `JoinHandle` is dropped outlives its logical parent, and any error
inside it goes nowhere. The citable contrast is `JoinSet`:

> "When the `JoinSet` is dropped, all tasks in the `JoinSet` are immediately aborted."

So the review question is: **is this spawn owned by something?** Something that can await it, cancel
it, and observe its failure. "Fire and forget" in a comment with nothing collecting the result is
the tell.

## Blocking

> "In general, issuing a blocking call or performing a lot of compute in a future without yielding is
> problematic, as it may prevent the executor from driving other futures forward."

> "When you run CPU-bound code using `spawn_blocking`, you should keep this large upper limit in
> mind. When running many CPU-bound computations, a semaphore or some other synchronization
> primitive should be used to limit the number of computations executed in parallel. Specialized
> CPU-bound executors, such as `rayon`, may also be a good fit."

And the one that bites on shutdown:

> "**Be aware that tasks spawned using `spawn_blocking` cannot be aborted** because they are not
> async."

with the consequence that "runtime shutdown will wait indefinitely for all started `spawn_blocking`
to finish running". A `spawn_blocking` doing unbounded work plus a graceful-shutdown path is a hang.

Note the limitation clippy's async lints share with every static analysis: they are call-site-local.
A blocking call three frames below an `async fn`, behind a named helper, is invisible to them.

## `Send` bounds

`clippy::future_not_send` (nursery, allow) mechanizes this for libraries — its own rationale:
*"This can be used by library authors (public and internal) to ensure their functions are compatible
with both multi-threaded runtimes that require `Send` futures, as well as single-threaded
runtimes."* Recommend it for a library exposing futures rather than hand-checking.

Already on: `async_yields_async` (correctness, **deny**). Allow-by-default and worth knowing:
`unused_async`, `large_futures` (both pedantic).

## Concurrency without async

- **A `Mutex` in a codebase with no concurrency.** Grep for `async`, `thread::`, `Arc`, channels
  first. A `Mutex` used purely for interior mutability behind `&self` is `RefCell`'s job — or
  `&mut self`'s. The tell is poison recovery on a lock that can never be contended.
- **Unbounded parallelism** — a `JoinSet` or `spawn` per item over an unbounded input with no
  semaphore.
- **A cache with no invalidation** that is currently unreachable because the mutating path returns
  `Unsupported`. Worth one line noting the coupling before someone implements that path.

---

# `unsafe`

## The mechanical layer is mostly on already

- `missing_safety_doc` — style, **warn**. Public `unsafe fn` without a `# Safety` section.
- `not_unsafe_ptr_arg_deref` — correctness, **deny**. Its doc is worth quoting for the principle:
  *"In general, this lint should never be disabled unless it is definitely a false positive… since
  it breaks Rust's soundness guarantees… This is also true for internal APIs, as it is easy to leak
  unsoundness."*
- `unused_unsafe` — rustc, warn.
- `static_mut_refs` — **deny under edition 2024**.
- `unsafe_op_in_unsafe_fn` — **warns under edition 2024** (reported as `allow` by `rustc -W help`,
  which shows the pre-2024 default).

Worth recommending: `clippy::undocumented_unsafe_blocks` and `clippy::multiple_unsafe_ops_per_block`
(both restriction). The second exists specifically so that, combined with the first, "each unsafe
operation must be independently justified".

## The judgment residue

The operative policy is the **std dev guide's safety-comment policy**, not the Rustonomicon (which
is explicitly non-normative):

- Each `unsafe` block gets a `SAFETY:` comment "explaining why the block is safe, which invariants
  are used and must be respected."
- Each `unsafe fn` gets a `# Safety` doc section explaining what the caller must ensure.
- **The soundness test, and the highest-value thing in this section:** *"Inside safe elements, a
  `SAFETY:` comment must not depend on anything from the caller beside properly constructed types
  and values."* If the justification appeals to caller behaviour, the function should be `unsafe`.
- std itself enables `unsafe_op_in_unsafe_fn`, "requiring each unsafe operation to be enclosed in
  its own `unsafe` block for easier review".

So the review questions, in order:

1. Is there a `SAFETY:` comment at all? (Mechanizable — recommend the lint.)
2. **Is it true?** Does it discharge the actual precondition, or restate what the code does?
3. Does it appeal to caller behaviour from inside a safe function? If so, the safe wrapper is
   unsound and the function should be `unsafe`.
4. Could safe code do this? An `unsafe` block that exists to avoid a bounds check is a performance
   claim and needs a measurement.

## Miri

Miri detects out-of-bounds access and use-after-free, invalid use of uninitialized data, violation
of intrinsic preconditions, insufficiently aligned accesses, violation of basic type invariants,
data races and some weak-memory effects, Stacked/Tree Borrows aliasing violations, and leaks.

Its documented limits matter for how a review should cite it: Miri "does **not catch every violation
of the Rust specification**", and it detects UB only in the executions your tests actually perform —
it cannot establish soundness. **"Miri is green" is evidence about the test suite, not about the
`unsafe`.** Recommend it for any crate with `unsafe`; never present a clean run as proof.

## The common case

Most crates have no `unsafe` at all. Say so in one line and move on — and credit
`unsafe_code = "forbid"` in a `[lints]` table where it exists, since that turns the whole section
into a compiler guarantee.

# Language-specific fixes

Load before writing a fix. The *checks* in the skill are language-agnostic; these are the
mechanics. Verified 2026-09-14 against Python 3.13/3.14 and Rust 1.93.1 stable.

---

## Broken pipe

The check is the same everywhere: pipe the tool into `head` and look at stderr. The fix is not.

### Python

The Python `signal` docs carry a "Note on SIGPIPE" with the sanctioned fix:

> "Piping output of your program to tools like _head(1)_ will cause a `SIGPIPE` signal to be sent to
> your process when the receiver of its standard output closes early. This results in an exception
> like `BrokenPipeError: [Errno 32] Broken pipe`. To handle this case, wrap your entry point to
> catch this exception as follows:"

```python
def main():
    try:
        for x in range(10000):
            print("y")
        # flush output here to force SIGPIPE to be triggered
        # while inside this try block.
        sys.stdout.flush()
    except BrokenPipeError:
        # Python flushes standard streams on exit; redirect remaining output
        # to devnull to avoid another BrokenPipeError at shutdown
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)  # Python exits with error code 1 on EPIPE
```

Two details worth checking in a review, because a partial version of this fix still misbehaves:

- the explicit `sys.stdout.flush()` **inside** the `try`, so the failure surfaces where it can be
  caught rather than during interpreter shutdown;
- the `dup2` to devnull, so the shutdown flush doesn't raise a second one.

And the trap, stated by the docs directly:

> "**Do not set `SIGPIPE`'s disposition to `SIG_DFL` in order to avoid `BrokenPipeError`.** Doing
> that would cause your program to exit unexpectedly whenever any socket connection is interrupted
> while your program is still writing to it."

Note the sanctioned fix exits **1**, not 141 — so even CPython's own recipe does not reproduce the
shell-visible SIGPIPE status. No source found recommends going further; don't ask for 141 in Python.

### Rust

Rust's std sets SIGPIPE to `SIG_IGN` before `main`, so the write returns `EPIPE` and `println!`
unwraps it into a **panic**: "failed printing to stdout: Broken pipe (os error 32)", exit **101**.
That is worse than Python's behaviour, because 101 is the ordinary panic exit and a bug report
carrying it reads as a genuine crash.

**There is no stable language-level fix.** On 1.93.1, `#[unix_sigpipe = "..."]` and
`#[unsafe(unix_sigpipe = "...")]` both fail with "cannot find attribute", and
`#![feature(unix_sigpipe)]` fails with `error[E0635]: unknown feature 'unix_sigpipe'` — the feature
name is gone from the compiler, not merely unstable. Its replacement, `-Zon-broken-pipe=kill`, is a
nightly `-Z` flag and is rejected on stable. The tracking issue is open and the plan has moved again,
toward an externally implementable item.

Two workarounds, both verified:

**A — restore the Unix default, first statement in `main`.** Needs `libc`.

```rust
unsafe { libc::signal(libc::SIGPIPE, libc::SIG_DFL); }
```

Result: exit 141 (128+13), empty stderr — exactly what `ls`, `grep` and every other Unix tool do.
One line, covers every write site. Caveat: the disposition is inherited across `fork`/`exec`, which
matters if the tool spawns `$EDITOR`, `git`, or a pager.

**B — handle `EPIPE` on a locked, buffered writer.** The only option for a crate that forbids
unsafe.

```rust
if let Err(e) = writeln!(w, "{row}") {
    if e.kind() == io::ErrorKind::BrokenPipe {
        return ExitCode::SUCCESS;
    }
    return Err(e.into());
}
```

Result: exit 0, empty stderr. More invasive, since every write site must go through it.

Recommend A for a tool that produces textual output, unless the crate forbids unsafe or spawns
children whose SIGPIPE disposition matters.

---

## Exit mechanism

### Python

`sys.exit(n)` / `raise SystemExit(n)`. Argument parsers conventionally use 2 for usage errors.
Concentrate exits at the entry point: library-layer code should return or raise, so the exit code
is decided in one place.

The subtle one: a signal-terminated child does not yield an exit code. `subprocess.call` returns a
**negative** number for a child killed by a signal, so passing it to `sys.exit` turns Ctrl-C into a
nonsense shell status (`-2` → 254). Normalize it — map a negative status to `128 + (-status)`, or to
a fixed failure code.

### Rust

Three mechanisms with materially different behaviour:

| Mechanism | Behaviour |
|---|---|
| `fn main() -> Result<...>` | Prints the **`Debug`** form of the error and exits 1. A real UX defect: the user sees a struct dump rather than a message. |
| `std::process::exit(n)` | **Skips all destructors.** Matters when the program holds lock guards, temp files, or anything whose `Drop` does cleanup. |
| `fn main() -> ExitCode` | Runs destructors, allows `ExitCode::from(n)`. The right default. |

So for Rust, "which mechanism" is itself a review question with no Python analogue. A tool that
does careful atomic writes and holds `flock` guards but exits via `process::exit` has made those
guarantees weaker than they look.

---

## Error chaining

**Python** — `raise X from e`, and the interpreter prints the full chain for free. The failure mode
is stringifying at a boundary, which throws away the exception object.

**Rust** — nothing prints `.source()` automatically. `eprintln!("error: {e}")` shows exactly one
level, so any wrapper with its own message silently discards its cause. Fixes: a context-carrying
error library rendered with its debug formatter, or a hand-written chain walk.

A stringly-typed error costs far more in Rust than in Python. Collapsing `std::io::Error` into a
`String` at a boundary loses the path, the operation *and* the `ErrorKind`, so no caller can branch
on not-found versus permission-denied and the user sees "No such file or directory" with no
indication which file. The shape to recommend:

```rust
#[error("{op} {path}")]
Io { op: &'static str, path: PathBuf, #[source] source: std::io::Error },
```

---

## Stream discipline

**Python** has no default lint for this; review it by reading.

**Rust can mechanize it.** `clippy::print_stdout` and `clippy::print_stderr` are restriction lints —
off by default, enabled crate-wide, with `#[allow]` on the genuine output sites. When reviewing a
Rust CLI, recommend enabling them once rather than listing instances; that converts the whole
category from judgment into a compile gate.

---

## Dry-run enforcement

**Python** — threaded through by discipline only. The best available structural move is to funnel
every write through one module whose functions take the flag, so there is a single place to audit.

**Rust** — can be made a type-level guarantee: pass an effect enum (`Effect::Apply | Effect::Preview`)
or a writer trait object into the backend, so a code path that writes without consulting it fails to
compile. Ask for the stronger form; an `if !dry_run` at each call site is a promise the next caller
will forget.

---

## Atomic writes

**Python** — `tempfile.NamedTemporaryFile(dir=...)` or `mkstemp` in the target's directory, write,
`os.fsync(fd)`, then `os.replace`. Fsyncing the parent directory afterwards is what makes the rename
itself durable.

**Rust** — the same sequence, with `File::sync_all()` before the rename and `OpenOptionsExt::mode`
for the temp file's permissions. One language-specific trap: `Path::with_extension("tmp")`
**replaces** the existing extension rather than appending, so `foo.json` becomes `foo.tmp` — which
also means two files differing only by extension collide on the same temp path.

Whether destructors run at all is the `process::exit` vs `ExitCode` question above.

---

## Environment variables and precedence

**Python** — `os.environ.get`, uniform. Remember that `VAR=` yields `""`, not `None`, so
blank-is-unset needs an explicit filter.

**Rust** — a genuine choice:

- the argument parser's env support gives a free `[env: VAR=]` annotation in `--help`, but treats
  `VAR=` as *set to empty*;
- hand-rolling `std::env::var` gets blank-is-unset right but loses the help annotation.

Hand-rolling is defensible; the reviewable defect is the resulting **undiscoverability** — the env
override no longer appears in `--help` anywhere.

Edition-2024 constraint with no Python analogue: mutating process environment is `unsafe` and racy
under a parallel test runner. Precedence logic must therefore be factored into a pure function
taking its inputs as parameters, or it cannot be tested.

---

## File locking

**Python** — `fcntl.flock`, stdlib, no dependency decision.

**Rust** — historically needs a crate; `File::lock()` only stabilised recently. Its absence is
therefore somewhat more forgivable in a Rust CLI, and recommending it carries a dependency
decision — say so in the finding rather than treating it as free.

---

## Dead dependencies as a UX signal

Rust-specific surfacing: an unused crate or an unused parser feature flag promises a capability the
binary does not have. `clippy::cargo` and `cargo-udeps` catch these; both are off by default.
Python's equivalents are weaker and this rarely gets flagged. Worth a Suggestion when the unused
feature is one a user would reasonably expect to work — a declared-but-unused env-var feature, for
instance, next to hand-rolled env reading.

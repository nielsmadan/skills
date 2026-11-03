# Boundaries: parsing, subprocess, filesystem (full catalogue)

Load when the code reads untrusted input, shells out, or writes files. The governing idea is one
sentence from Alexis King:

> "Push the burden of proof upward as far as possible, but no further. Get your data into the most
> precise representation you need as quickly as you can. Ideally, this should happen at the
> boundary of your system, before *any* of the data is acted upon."
> — <https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/>

The failure mode it names is the one to look for:

> "Shotgun parsing is a programming antipattern whereby parsing and input-validating code is mixed
> with and spread across processing code—throwing a cloud of checks at the input, and hoping,
> without any systematic justification, that one or another would catch all the 'bad' cases."

And the reason it matters beyond tidiness:

> "a program that does not parse all of its input up front runs the risk of acting upon a valid
> portion of the input, discovering a different portion is invalid, and suddenly needing to roll
> back whatever modifications it already executed in order to maintain consistency."

## 1. Where is the perimeter?

For each external input — subprocess stdout, JSON/JSONL/TOML files, env vars, CLI args, network
responses, model output — find the single place it becomes typed. Then ask:

- **Is there one?** If parsing is spread across the consumers, that is shotgun parsing.
- **Does the parsed form survive?** A validator that proves an exact shape and returns
  `dict[str, Any]` has thrown the proof away. See §1 of the main skill.
- **Does interior code still use `.get()` chains?** `.get("a", {}).get("b", "")` three layers deep
  in business logic means the boundary never happened. Each `or ""` installs an in-band sentinel
  that some later comparison will silently fail to match.
- **Is a `-> Any` function the de facto boundary?** `def _run_json(args) -> Any: return
  json.loads(out)` propagates `Any` into every caller, so `str(x.get(k, ""))` type-checks no matter
  what `x` is. Give it a `TypedDict`, or a `_parse_x(raw) -> X | None` that fails loudly once.

**Coercion helpers are the cheap fix worth praising when present** — a module of `as_dict`,
`as_int`, `as_float_or_none` applied uniformly at every reader, each correctly excluding `bool`
from the numeric check.

## 2. Trusting a declared schema

A JSON schema sent to an external service — an LLM, a third-party API — is a *request*. If the
client validates only `isinstance(result, dict)`, the enum in that schema guarantees nothing. An
unexpected value written into the domain then matches no branch in any consumer, so the record
silently disappears from every filter and rollup with no error anywhere. Validate the response
against the declared enum at the boundary, and type the setter `Literal[...]`.

## 3. Subprocess

> "Unlike some other popen functions, this library will not implicitly choose to call a system
> shell. … If the shell is invoked explicitly, via `shell=True`, it is the application's
> responsibility to ensure that all whitespace and metacharacters are quoted appropriately to avoid
> shell injection vulnerabilities. On some platforms, it is possible to use `shlex.quote()`."
> — <https://docs.python.org/3/library/subprocess.html#security-considerations>

Most of this is `S602`–`S607`, which are **off by default** (only 3 of 73 `S` rules are on), so
check Step 0 before assuming coverage.

The judgment items no rule reaches:

- **Missing `timeout=` on the slowest call**, especially when sibling calls in the same package
  have one. A wedged child hangs a CLI forever.
- **`check=False` and then ignoring `returncode`** — the result is discarded and failure looks like
  success.
- **Injection into a non-shell interpreter.** `shell=True` gets the attention; an f-string
  interpolated into `osascript -e`, `sqlite3`, `awk`, `jq`, or a generated config is the same class
  of bug with no rule watching. Safe today because every caller passes a constant is not safe — it
  is one refactor away.
- **`.decode()` with no encoding and no `errors=`** on subprocess bytes.
- Negative return values: `subprocess.call` returns a negative number for a signal-terminated
  child, so passing it to `sys.exit` produces a nonsense shell status (`-2` → 254).

## 4. Filesystem atomicity

> "If successful, the renaming will be an atomic operation (this is a POSIX requirement)."
> — `os.replace`, <https://docs.python.org/3/library/os.html>

The full-strength pattern: `mkstemp` **in the same directory** as the target → `fchmod` → write →
`flush` → `fsync(fd)` → `os.replace` → `fsync` the **parent directory** → clean up the temp in
`finally`. Most implementations stop at `os.replace` and lose durability across a power cut.

What to actually review:

- **Truncate-in-place on a file another process reads.** `read_text()` → transform →
  `write_text()` leaves a truncated file if the process dies mid-write. Worst when the target
  belongs to another program — an editable-install `.pth`, another tool's `settings.json`, a
  user's index file.
- **Divergent copies of the same primitive.** Count the atomic writers in the package and compare
  their guarantees: which ones `fsync`, which open `O_NOFOLLOW`, which re-`stat` after opening,
  which preserve mode. Two functions both named `_atomic_write` in different modules, with
  different safety properties, is a real finding. **Then check who bypasses the good one** — an
  exemplary primitive with four call sites that don't use it is the common shape.
- **Symlink handling** — `lstat` → reject symlink → `O_NOFOLLOW` open → `fstat` re-check is the
  hardened read; `resolve(strict=True)` followed by a containment re-check is the hardened path
  validation. Flag destructive operations that skip this while less destructive ones in the same
  repo do it.

## 5. TOCTOU

`if path.exists(): path.unlink()` is a race; `with suppress(FileNotFoundError): path.unlink()` is
not. The glossary makes the argument directly:

> "In a multi-threaded environment, the LBYL approach can risk introducing a race condition between
> 'the looking' and 'the leaping'. For example, the code, `if key in mapping: return mapping[key]`
> can fail if another thread removes *key* from *mapping* after the test, but before the lookup."
> — <https://docs.python.org/3/glossary.html>

This is the one place where EAFP is a correctness argument rather than a style preference. Weight
findings by what sits inside the window: an `exists()` guarding a read is usually fine; one
guarding an `unlink`, a `move`, or a rewrite is not.

Two specific shapes:

- **A whole-file equality comparison as a deletion gate** — `if path.read_text() == TEMPLATE:
  path.unlink()`. A trailing newline or line-ending difference flips "clean up" into "leave in
  place", and the exists→read→unlink window is unguarded.
- **Re-checking after a prompt.** A confirmation blocks for an unbounded time; the destination may
  exist by the time the user answers. Note that `shutil.move` does *not* raise on an existing
  directory — it moves the source *inside* it and reports success.

## 6. Reading

- **Encoding asymmetry.** Writes usually declare `encoding="utf-8"`; reads often don't. A package
  with 55 `read_text()` calls and one `encoding=` has an unintentional gap, not a convention.
  Same for `errors=` — if every other reader in the package passes `errors="replace"` and one
  doesn't, that one aborts on a malformed byte.
- **Whole-file reads of the format the repo itself documents as largest.** If every other JSONL
  reader streams line by line and one calls `read_text().splitlines()`, that is a regression
  against the package's own stated reason for streaming.
- **Silently dropped malformed rows combined with a rewrite.** Skipping unparseable lines on read
  may be the right call for a cache. Rewriting the file from the *filtered* list turns one
  corrupted byte into permanent, silent data loss on the next write. Flag the combination, not the
  skipping, and ask for a diagnostic either way.
- **Append with no lock where a concurrent writer is known.** A read-the-tail-then-append sequence
  against a file another process is actively writing produces either a spurious blank line or two
  joined records. If the package has a lock used everywhere else, this is the one place it was
  forgotten.

## 7. Exception flow at the boundary

`json.JSONDecodeError` and `UnicodeDecodeError` are both `ValueError`, **not `OSError`**. A caller
catching only `OSError` around a parse will not survive one corrupt file. This recurs because the
`open()` and the `json.loads()` look like the same kind of operation.

Check each boundary reader against its caller's `except` clause specifically:

- Does the discovery/scan path guard decode errors while the parse path doesn't?
- Does one bad input abort a whole batch that should have skipped it?
- Conversely, does a broad guard swallow errors that should abort the batch?

## 8. Module-level state and import time

- Network calls, config file reads, `os.environ` reads, or logging configuration at module scope.
- One module mutating another's global at import, with the ordering load-bearing — usually
  documented in a comment, which is the tell that it is fragile.
- `@cache`/`@lru_cache` on a function whose answer changes: a filesystem or git query cached for
  the process lifetime, inside a command whose purpose is to change the filesystem.
- A module global cleared at the top of a function, making that function non-reentrant.
- A package root re-exporting private names so tests can patch them.

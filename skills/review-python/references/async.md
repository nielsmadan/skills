# Async, threads & concurrency (full catalogue)

Load when the code touches `asyncio`, threads, or a TUI/GUI event loop. Everything here assumes
ruff's `ASYNC` rules own the mechanical layer — check Step 0, because all ten are lost whenever a
project uses `select` without listing `ASYNC`.

## What ASYNC already covers (don't repeat it)

Default-on: `ASYNC100` cancel-scope-no-checkpoint, `ASYNC105`, `ASYNC115` zero-sleep, `ASYNC116`
long-sleep-not-forever, `ASYNC210` blocking-http, `ASYNC220`/`221`/`222` subprocess,
`ASYNC230` blocking `open()`, `ASYNC251` `time.sleep`.

Off by default even when `ASYNC` is selected: `ASYNC109` (hand-rolled `timeout=` parameter),
`ASYNC110` (busy-wait loop), `ASYNC212` (sync httpx), `ASYNC240` (blocking pathlib), `ASYNC250`
(blocking `input`).

**The structural limit:** every one of these is call-site-local. They match a blocking call
lexically inside an `async def`. They cannot follow a call graph, so none of the judgment items
below is reachable by any of them.

## 1. Blocking the loop indirectly — the highest-value finding

An `async` handler calls a named function; three frames down, that function scans a filesystem,
calls `time.sleep`, runs `shutil.rmtree`, or shells out. Nothing yields back to the loop until the
whole call returns, so a progress indicator pushed on the line above cannot paint and keystrokes
are dead.

How to find it: for each `async def` and each framework worker/handler, list the non-trivial calls
it makes and ask whether *that* function does I/O. A useful proxy — if the package contains **no**
`to_thread`, `run_in_executor`, or `thread=True` anywhere, yet its handlers reach the filesystem or
subprocess, the offloading was never considered.

Fix: `await asyncio.to_thread(fn, ...)` — *"primarily intended to be used for executing IO-bound
functions/methods that would otherwise block the event loop if they were run in the main thread"* —
or the framework's threaded-worker flag.

Framework-specific: in Textual, `@work` without `thread=True` schedules an asyncio task on the UI
loop; work done in `compose()` or a message handler runs inline during mount. In FastAPI, a plain
`def` handler is already run in a threadpool, so the dangerous shape is `async def` + blocking I/O.
In Django, ORM access under a running loop raises `SynchronousOnlyOperation` — *"you don't have to
be inside an async function directly to have this error occur"* — and the fix is `sync_to_async`
or the `a`-prefixed queryset methods.

## 2. Task lifetime — `create_task` and the GC hazard

The official wording, which is worth quoting verbatim in a finding:

> "Save a reference to the result of this function, to avoid a task disappearing mid-execution.
> The event loop only keeps weak references to tasks. A task that isn't referenced elsewhere may
> get garbage collected at any time, even before it's done."
> — <https://docs.python.org/3/library/asyncio-task.html>

The documented fire-and-forget pattern holds the set and discards on completion:

```python
background_tasks = set()
task = asyncio.create_task(coro())
background_tasks.add(task)
task.add_done_callback(background_tasks.discard)
```

with the caveat that this never awaits, so a failure surfaces only as a logged "Task exception was
never retrieved". Prefer `TaskGroup`, which *"keeps a strong reference to each task, awaits them
and propagates their exceptions"*.

Flag: a bare `asyncio.create_task(...)` whose result is discarded; a task stored on an object that
is itself short-lived; "fire and forget" in a comment with nothing collecting the exception.

## 3. `TaskGroup` vs `gather`, and the `ExceptionGroup` consequence

> "TaskGroup provides stronger safety guarantees than gather for scheduling a nesting of subtasks:
> if a task (or a subtask, a task scheduled by a task) raises an exception, TaskGroup will, while
> gather will not, cancel the remaining scheduled tasks."

> "Once all tasks have finished, if any tasks have failed with an exception other than
> `asyncio.CancelledError`, those exceptions are combined in an `ExceptionGroup` or
> `BaseExceptionGroup` … which is then raised."

**The review trigger that catches real bugs:** code using `TaskGroup` and catching a plain
`except SomeError:` around it. The group raises an `ExceptionGroup`, which `except SomeError` does
not match — the handler never runs. It needs `except*` (PEP 654), where *"each exception is either
handled by exactly one clause (the first one that matches its type) or is reraised at the end"*.

Also flag `gather(...)` without `return_exceptions=` where a partial failure silently leaves the
other tasks running.

## 4. Cancellation

> "In case `asyncio.CancelledError` is explicitly caught, it should generally be propagated when
> clean-up is complete. `asyncio.CancelledError` directly subclasses `BaseException`… The asyncio
> components that enable structured concurrency, like `asyncio.TaskGroup` and `asyncio.timeout()`,
> are implemented using cancellation internally and **might misbehave if a coroutine swallows
> `asyncio.CancelledError`**."

Practical consequences:

- `except Exception:` in an async function is *usually fine* — `CancelledError` is a
  `BaseException` and passes through. `except BaseException:` and bare `except:` are not.
- A `finally:` block that itself awaits something slow delays cancellation for everyone waiting.
- `asyncio.shield` around work that must not be cancelled is correct; around work that *should* be
  is a hang.
- User code calling `uncancel()` is almost always wrong.

## 5. Timeouts

`asyncio.timeout` over a hand-rolled deadline, with one trap worth a finding of its own:

> "The `asyncio.timeout()` context manager is what transforms the `asyncio.CancelledError` into a
> `TimeoutError`, which means **the `TimeoutError` can only be caught *outside* of the context
> manager**."

For subprocesses and network calls, the judgment is **asymmetry**: if the fast calls in a module
pass `timeout=` and the slowest, most hang-prone one does not, that is a defect and not a style
note — the authors demonstrably know the argument exists. An LLM call, a network fetch, or a
user-facing shell-out with no timeout can wedge a CLI forever and freeze a TUI including its
keystrokes.

`ASYNC109` flags the hand-written `timeout=` *parameter* pattern and is off by default:
> "highly opinionated to enforce a design pattern called 'structured concurrency' that allows for
> `async` functions to be oblivious to timeouts, instead letting callers handle the logic with a
> context manager."

## 6. State across a suspension point

The async analogue of a data race, and entirely outside any checker's scope. Three shapes:

- **Check-then-act** — read a cache, `await` a fetch, write back. Concurrent callers each see the
  empty cache and issue duplicate requests. Fix: store the in-flight task so later callers await
  the same one.
- **Read-modify-write** — load a structure, `await`, save it. A handler that ran during the await
  has its write silently discarded.
- **Reassigning shared state from inside a worker.** The nastiest variant: an instance attribute
  holding a whole document is replaced mid-flight while other handlers mutate and persist the old
  object. Worse, any list holding references *into* the old value now renders stale data and hands
  stale objects to the next action. Ask: who else can touch this attribute between the `await` and
  the write?

## 7. Threads and executors

- **`ThreadPoolExecutor` not used as a context manager**, with a hand-rolled `finally` that
  reimplements what `with` provides.
- **`shutdown(wait=False, cancel_futures=True)`** returns while already-started futures are still
  running — `cancel_futures` cannot cancel one that has begun. On a timeout path this leaves
  orphaned subprocesses running after the process reports completion.
- **Mutable containers passed in to be mutated by the callee** — a set or list used as a
  side-channel second return value. Return a value instead.
- **Unbounded concurrency** — a `TaskGroup` or `gather` over an unbounded input list with no
  `Semaphore` and no batching. Nothing mechanical covers this.
- **`asyncio.run` nesting**, and blocking primitives (`threading.Lock`, `queue.Queue.get`) used
  from async code where the async variant exists.
- **Mutating UI state from a thread** without the framework's marshalling call
  (`call_from_thread` in Textual); the inverse — using it when already on the event loop — is also
  wrong.

## 8. Busy-waiting

`while not done: await asyncio.sleep(0.1)` forces a tradeoff between latency and waste. An
`asyncio.Event` removes it: *"Waiting on an `Event` object like `asyncio.Event` … eliminates this
tradeoff."* (`ASYNC110`, off by default.)

## Async test correctness

- In pytest-asyncio's default **strict** mode, an `async def` test with no `asyncio` marker is
  collected and never awaited — it passes without running anything. In `auto` mode the marker is
  added automatically, so a module also setting `pytestmark = pytest.mark.asyncio` is redundant.
  Either way, `filterwarnings = ["error"]` and `--strict-markers` surface the mismatch.
- **Fixed-iteration loop pumps as a worker wait** — `for _ in range(5): await pilot.pause()`. The
  number is a guess about how many loop turns the worker needs, and it varies across tests in the
  same file. Recommend the framework's real wait (`app.workers.wait_for_complete()`).
- `sleep`-based synchronization anywhere in a test suite.

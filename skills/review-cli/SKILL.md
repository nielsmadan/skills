---
name: review-cli
description: Language-agnostic review of a command-line tool's interface and behaviour — exit codes and signals, broken-pipe handling, stdout/stderr discipline, TTY detection and destructive-action gating, dry-run integrity, partial failure and idempotency, config precedence, flag and help design, and error messages that name the next action. Starts by RUNNING the binary, because most of this is invisible in the source. Applies equally to Python, Rust, Go, Node and shell-invoked tools. Auto-invoked by `code-review` on projects that ship a console entry point. Triggers "review cli", "cli review", "command line interface review", "review the CLI UX".
argument-hint: '[--staged | --unpushed | --changed | --all | --multi]'
effort: high
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Review CLI

Review of the interface a command-line tool *presents*, not the language it is written in. The
checks below are the same for a Python CLI and a Rust one; only the fixes differ, and §8 carries
those.

Complements `review-<language>` skills (which review the code) and `review-interfaces` (which
reviews function and module signatures, not the CLI surface). Don't repeat either.

## Review grading

Use only these finding priorities, in descending order:

- **Critical Issues (Must Fix):** a verified path causes data loss, a security failure, a materially
  wrong operation, or makes a core workflow unusable without reasonable recovery.
- **Improvements (Should Fix):** an ordinary supported workflow demonstrably fails or repeatedly
  imposes substantial friction, or a concrete design defect creates meaningful maintenance cost.
- **Suggestions (Nice to Have):** a worthwhile improvement with small practical impact, including
  optional polish, local simplification, and rare recoverable edge cases.

Grade the demonstrated consequence, realistic reachability, and available recovery against project
priorities. A category, missing convention, hypothetical future problem, or confidence that a claim
is true does not set its priority. Do not assign automatic severity floors or ceilings. Keep
unverified claims in validation gaps, outside the graded finding count; distinguish suggestions
from defects. For plans, trace the consequence if implemented and state the assumptions.

Use the short labels **Must Fix**, **Should Fix**, and **Nice to Have** in summaries and ledgers.
Keep effort, verification status, user-facing change size, and tool/vendor diagnostic ratings
separate. When called by `code-review`, return its requested evidence and impact fields; the parent
owns scoring and final triage. Otherwise apply this rubric directly. Omit empty priority sections.

## Relationship to the toolchain (read first)

**There is essentially no tooling for this layer.** That is not an assumption — a search across
four phrasings for a CLI-design linter turned up clig.dev itself, generic static-analysis
round-ups, and no tool. ShellCheck analyses *shell scripts*, i.e. programs written in bash; it says
nothing about the interface a compiled or Python program presents. Neither ruff nor clippy ships a
CLI-conventions rule set.

Two narrow exceptions worth knowing:

- **Rust can mechanize the stream discipline** in §2. `clippy::print_stdout` and
  `clippy::print_stderr` are restriction lints — off by default, but a crate can turn them on and
  `#[allow]` the handful of genuine output sites. When reviewing a Rust CLI, *recommend enabling
  the lint* rather than listing instances one by one.
- **`clap::Command::debug_assert()`** catches duplicate short flags and conflicting requirements —
  definition consistency, not design.

So this skill carries more weight than a language review does, and **its findings must be earned
by evidence**, since nothing else will catch a mistake here and nothing else will catch a false
positive either.

## What this skill checks

**A CLI's design is decided once; its behaviour regresses continuously.** So the default review
looks only at what the diff introduces — a new subcommand, a new output path, a new destructive
operation, a new prompt. One-time properties (does `--version` exist, does `--help` carry
descriptions, are config roots XDG-correct) belong to the **project-level set in §P**, which runs
at `--all` and nowhere else. Re-checking those on every diff is noise, and it buries the findings
that matter.

## Step 0: probe what the diff touches

Most CLI behaviour is invisible in the source, so run the thing rather than reading it — but scope
the probing to the change:

- **Any scope:** if the diff adds or changes an output path, pipe it into `head` and check stderr
  is empty. If it adds a destructive operation, run it with `< /dev/null`. If it adds `--json`
  output, pipe it through `jq`.
- **`--all` only:** the full probe table in §P.

**The pipe probe needs output larger than the pipe buffer (~64 KB)** or it silently passes. Use the
largest output the changed command can produce.

A probe you could not run (no build, no fixture data) is reported as *not run*, never as passing.

## Usage

```
/review-cli                  # Review context-related code
/review-cli --staged         # Review staged changes
/review-cli --unpushed       # Review files changed across all unpushed commits
/review-cli --changed        # Review unstaged changes
/review-cli --all            # Full CLI surface audit (the natural scope for this skill)
/review-cli --multi          # Also get external advisor opinions
```

## Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related code | Files from the current conversation context, plus the CLI entry point and argument definitions regardless of scope — a diff to one subcommand is reviewed against the whole interface it joins. |
| `--staged` | Staged changes | `git diff --cached --name-only` |
| `--unpushed` | Files changed across unpushed commits | `git diff --name-only $(git rev-list HEAD --not --remotes \| tail -1)^..HEAD` |
| `--changed` | Unstaged changes | `git diff --name-only` |
| `--all` | Whole CLI surface + **§P project-level checks** | Entry point, argument definitions, every subcommand handler, output and prompt helpers |
| `--multi` | Add external opinions | Combines with any scope above; invokes `second-opinion --quick` |

**Only `--all` runs §P.** At every other scope the review covers §1–§8 against what the diff
introduces, and a §P finding is out of scope even if you notice it — note it in one line at the end
if it is severe, but never as a review finding.

## Workflow

1. **Determine scope** and locate the entry point and argument definitions.
2. **Run the Step 0 probes.** Record results.
3. **Read AGENTS.md / CLAUDE.md / README** — the README matters unusually much here, because a
   gap between what it documents and what `--help` says is itself a finding (§6).
4. **Review against §1–§7.** Load `references/conventions.md` for the normative sources and the
   contested list; load `references/language-notes.md` when writing a fix.
5. **Parallelize** if the CLI has many subcommands: one sub-agent per category, merge and dedupe.
6. **External opinions** (if `--multi`): invoke `second-opinion --quick` with this prompt:

   ```
   Read-only review of a command-line tool's interface, not its implementation language. No
   linter covers this layer, so nothing is out of scope for being mechanical. Focus on: does a
   destructive command have a gate, and is whatever justifies skipping it available on every code
   path that reaches it? Does the tool refuse rather than assume when stdin is not a terminal?
   Does it ever report an action that did not happen? Do exit codes distinguish failure classes
   without colliding? Is primary output on stdout and every diagnostic on stderr? Does a dry-run
   flag reach the lowest write primitive or just the command handler? If it dies halfway, what is
   left behind and is a re-run safe? Do errors say what to do next? 300 words or less.
   ```

   Wait for all external results before proceeding.
7. **Classify severity** and **report**, grouped by severity.

## 1. Exit codes & signals

- **Broken pipe is the single most commonly missed defect.** A tool piped into `head` keeps
  writing after the reader exits. If SIGPIPE is ignored (which both Python and Rust do by default),
  the write fails and surfaces as a traceback or panic on stderr plus a wrong exit code. **Check
  every CLI for this**; the fix is language-specific (§8). The symptom differs: Python prints a
  `BrokenPipeError` traceback and exits 1; Rust prints a *panic* and exits **101**, which is
  indistinguishable from a genuine bug — a Rust CLI reporting 101 in a bug report should make you
  suspect this first.
- **Exit codes must distinguish failure classes, and no two classes may collide.** The reviewable
  property is consistency and documentation, not which scheme. A CLI that returns 2 for both
  "you typed it wrong" (the parser's convention) and "this build doesn't do that" has made those
  indistinguishable to a caller. Do **not** prescribe `sysexits.h` — see the contested list.
- **Zero on failure is a defect unless it is a documented inversion.** A hook or shim that must
  never break its host can legitimately always exit 0, provided failures are routed to a channel
  the user can actually see (a health log with a `doctor` command, say). Check that the
  compensating channel exists before calling it a bug — and check it exists before calling it fine.
- **Signal handling.** If the tool catches SIGINT for cleanup, it should still terminate promptly
  and bound the cleanup; a second Ctrl-C must escape. Exiting 130 imitates what the shell reports
  for an uncaught SIGINT (128+2) and is the usual convention, though no primary source states it
  directly.
- **A signal-terminated child's status is not an exit code.** Passing a negative or raw wait status
  straight to the process exit turns Ctrl-C in a child into a nonsense shell status.

## 2. Streams & machine-readable output

- **Primary output and anything machine-readable on stdout; every log, error and progress message
  on stderr.** The tell is a *diagnostic on stdout right next to a mechanism that gets it right* —
  a prompt preamble printed to stdout while the prompt itself goes to stderr, or a line saying
  "see the warning above" when the warning went to stderr and the user redirected stdout to a file.
- **Help is not an error.** Requested help → stdout, exit 0. Usage error → stderr, non-zero. A tool
  that prints `--help` to stderr is wrong, and so is one that prints a usage error to stdout. This
  one has a definite answer; see the contested list for why the folklore says otherwise.
- **A machine-readable format is what earns the freedom to change human output.** A tool with no
  `--json`/`--plain` has implicitly made its pretty output an API. Check that machine output
  carries a **schema version** the consumer can branch on, and that nothing else is interleaved on
  stdout when it is active.
- **Column widths computed from the result set** are fine for humans and a trap for scripts — a
  note rather than a defect when a stable format is offered alongside.
- **Colour off when not a TTY, and when `NO_COLOR` is set and non-empty** regardless of its value.
  Check stdout and stderr independently: piping stdout does not mean stderr colour is unwanted.
  If the tool emits no colour at all, this whole item is moot — don't invent it.

## 3. Interactivity, TTY & destructive actions

- **The gate must exist on every path that reaches the command.** The highest-value check in this
  skill. When a destructive command has no confirmation because something else makes it
  recoverable — an undo, a trash, a backup — verify that thing is available on *every* backend,
  platform and configuration the command runs under. A safety net that exists for one of two
  storage backends does not gate the command; it gates half of it.
- **Non-TTY must refuse, not assume.** Silence is not consent and EOF is not yes. The correct
  shape is: explicit `--yes`/`--force` → proceed; interactive terminal → prompt; otherwise →
  refuse with a message naming the flag that would have worked. Checking that *both* stdin and
  stderr are terminals is stricter than the common stdin-only check and is right.
- **Never require a prompt.** Every prompted value needs a flag or argument equivalent, or the
  command is unscriptable. Prompts also belong at the CLI edge, not in the library layer where
  every caller — tests included — has to arrange a TTY.
- **Unguarded `input()`/read crashes under `< /dev/null` and in CI.** Check every prompt, not the
  first one; these are usually copy-pasted, and the guard is usually on some of the copies.
- **Match the gate to the blast radius.** Deleting one named thing the user just named may need no
  prompt. A bulk or remote deletion needs one. Something irreversible and large should be hard to
  confirm *by accident* — requiring the name to be typed, with a flag form like
  `--confirm=<name>` so it stays scriptable, is the design that satisfies both.
- **Watch for non-obvious destruction** — a config value changed from 10 to 1 that implicitly
  deletes nine things is a severe action wearing an edit's clothing.

## 4. Dry-run, partial failure & idempotency

- **A dry-run flag must be threaded to the lowest write primitive, not checked at the command
  handler.** An `if not dry_run:` at each call site is a promise a future caller will forget.
  In a typed language, ask for the stronger form: pass an effect enum or a writer into the
  backend so a path that writes without consulting it fails to compile.
- **If it dies halfway, what is on disk, and is a re-run safe?** Trace a mid-loop failure
  explicitly. Idempotent-by-accident (the re-run happens to work) is worth crediting and worth
  naming as accidental — the reviewer's question is whether the recovery path was designed or
  merely available today.
- **Batch commands: validate everything, then apply everything.** Resolving all inputs before the
  first mutation is the pattern; the alternative needs a documented partial-result contract and
  an exit code that expresses it. There is no established convention for what a bulk command
  should exit when 7 of 10 items succeed — so the finding is that the tool must *decide and
  document* it, not that it picked wrong.
- **Never report an action that did not happen.** Idempotency at the library layer is correct;
  narrating it as though it occurred is the bug. "removed X" with exit 0 when X was never present
  is a defect in any language — and it is worse when a typo'd argument triggers a teardown path
  that then reports success.
- **Atomic writes and durability** — temp file in the same directory, then rename. Whether the
  contents are `fsync`ed before the rename decides whether a power cut yields a truncated file.
  Check especially where the tool rewrites files it does not own.
- **Cap unbounded stdin** if the tool reads it.
- **Parse arguments before loading config**, so `--help` still works on a machine with a broken
  config file. Easy to get backwards, trivial to check.

## 5. Config precedence

Per-change: **a new setting must join the existing precedence chain, not start a second one.** If
the diff reads an environment variable or a config key directly instead of going through the
project's one resolution function, that is the finding — a second copy of the order is how
precedence drifts. Whether the order itself is right, and whether config lands in the correct XDG
root, is §P.

Also per-change: a new secret read from a flag (it leaks into `ps` and shell history) or from an
environment variable. A `--password-file` or stdin is the shape.

## 6. Flags & subcommands

Per-change, all of these are about the **new** surface agreeing with the surface it joins:

- **A new flag or subcommand inconsistent with its siblings** — the same concept spelled
  differently, a short alias where siblings have none, `--json` on three subcommands and not the
  fourth. A consistency promise already made is a defect to break; one never made is a scope
  decision.
- **A new flag whose help text is missing** while its siblings have one.
- **A required thing modeled as optional** — a flag declared optional but handled only in its
  present form, producing a confusing fallthrough instead of the parser's "required argument not
  provided". Let the parser express the constraint.
- **A new conflict hand-checked** instead of declared to the parser, so it neither appears in help
  nor fails uniformly.
- **Validation for the new flag living in a second layer** — the same mistake reachable two ways
  should produce the same message *and* the same exit code and envelope. A shared validator reached
  through two layers often doesn't.
- **A changed flag, output shape, or subcommand name.** These are interfaces you have committed to;
  a rename breaks scripts in the wild. Watch for a new catch-all subcommand or newly-allowed
  abbreviation, both of which make it impossible to add names later.

## 7. Errors & messages

- **An error should name the next action.** "unknown project `nope` — configured project(s): demo"
  is a finding-free error. A bare string with no remedy is the defect. The fuller shape worth
  aiming at: what failed, why, and how to fix it, plus a code or URL when there is one.
- **Don't lose the cause at a boundary.** Stringifying an I/O error into a message discards the
  path, the operation and the error kind, so no caller can branch on not-found versus
  permission-denied and the user sees "No such file or directory" with no indication which file.
  This costs more in languages where the chain is not printed for free (§8).
- **A pointer to a message on another stream is not a message.** See §2.
- **The worst message is a success message for something that did not happen.** See §4.

## P. Project-level checks — `--all` only

These are decided once and almost never regress. Run them on a full audit; **never report them on a
diff review**, where they are noise that buries the real findings.

**The full probe table:**

| Probe | Expected |
|---|---|
| `cmd --help; echo $?` | Help on **stdout**, exit **0**. GNU: "output brief documentation for how to invoke the program, on standard output, then exit successfully." |
| `cmd --bogus >/dev/null; echo $?` | Usage error on **stderr**, non-zero (2 by convention) |
| `cmd --version; echo $?` | Prints a version, exit 0 — a `version` *subcommand* alone fails every script and packaging tool that probes for the flag |
| `cmd <long output> \| head -1` | No traceback, no panic, empty stderr |
| `cmd \| cat -v \| grep -c $'\e\['` | 0 — colour off when not a TTY |
| `NO_COLOR=1 cmd \| cat -v \| grep -c $'\e\['` | 0 |
| `cmd --json \| jq .` | Valid JSON, nothing else on stdout |
| `cmd -- -weirdname` | `--` terminates option parsing (POSIX Guideline 10) |
| `echo x \| cmd -` | `-` means stdin (POSIX Guideline 13) |
| Ctrl-C during a long run | Exits promptly; a second Ctrl-C escapes cleanup |

**Plus, read once:**

- **Does `--help` carry what the README carries?** A CLI whose subcommands have no descriptions
  while the README documents all of them has put its documentation where the user isn't.
- **Is SIGPIPE handled at all**, anywhere — one fix in `main` covers every write site (§8).
- **Is precedence implemented exactly once**, in one function every consumer calls, including any
  `which`/`debug` command that reports the resolution?
- **Are config, data, state and cache in the right XDG roots?** The one people get wrong is state:
  per the spec, `$XDG_STATE_HOME` holds data that persists between restarts but is "not important or
  portable enough to the user that it should be stored in `$XDG_DATA_HOME`" — history, logs,
  last-used selections. Credentials and user-authored content are data. The test: *would the user
  want this back on a new machine?*
- **Does a machine-readable format exist, and does it declare a schema version** a consumer can
  branch on? A tool with none has implicitly made its pretty output an API.
- **Is there a `--dry-run` where the destructive surface warrants one?**

## 8. What differs by language

The checks above are identical everywhere. These fixes are not — **load
`references/language-notes.md` before writing one.** The three that most often change the finding
itself:

| Concern | Python | Rust |
|---|---|---|
| **Broken pipe** | Catch `BrokenPipeError`, `dup2` stdout to devnull, exit 1. The Python docs explicitly advise **against** `signal.signal(SIGPIPE, SIG_DFL)` | **No stable language-level fix.** `#[unix_sigpipe]` no longer exists as a feature name; `-Zon-broken-pipe` is nightly-only. Either `libc::signal(SIGPIPE, SIG_DFL)` in an `unsafe` block first thing in `main`, or match `ErrorKind::BrokenPipe` on a locked buffered writer |
| **Exit mechanism** | `sys.exit(n)`; a signal-killed child's negative status must be normalized before it becomes the exit code | Three mechanisms with different semantics. Returning `Result` from `main` prints the **Debug** form and exits 1 — a real UX defect. `process::exit` skips destructors, weakening any lock guard or temp-file cleanup. `ExitCode` is the right default |
| **Error chaining** | `raise X from e`; the interpreter prints the chain | Nothing prints the source chain automatically, so one-level `Display` drops it. Stringifying an I/O error also discards the path and `ErrorKind` — a much more expensive mistake than in Python |

The reference also covers stream discipline (Rust can turn this into a compile gate; Python can't),
dry-run enforcement, atomic writes, env precedence, and file locking.

## Do NOT flag these

- **Anything in §P, on a diff review.** Missing `--version`, thin `--help`, XDG placement and
  precedence structure are project properties; they have not changed because this diff didn't touch
  them, and reporting them every time trains the reader to skim.
- **Missing `--json` on a tool with no machine consumers**, or `NO_COLOR` handling on a tool that
  emits no colour. Both are real rules with a precondition; check the precondition.
- **Deviations from POSIX Utility Syntax Guidelines 3, 7 and 9.** Guideline 3 permits only
  single-character options, so `--long` has no POSIX basis at all; 7 forbids optional
  option-arguments; 9 requires options before operands. Git, docker and cargo all violate these
  deliberately. Guidelines 4, 10 and 13 are the durable ones.
- **Not adopting `sysexits.h`** — deprecated by the BSD that originated it, documented neutrally
  by Linux, still recommended by the Rust CLI Book. No consensus; don't manufacture one.
- **Prescribing a specific exit number** beyond 0/non-zero and the 2-for-usage convention.
- **A deliberate always-exit-0 inversion** with a working diagnostic channel (§1).
- **Idempotent library behaviour** — the bug is narrating it as an action, not the idempotency.
- **Anything the project's own enabled lints already gate**, including a Rust crate that has
  turned on the print lints.


## Output Format

```markdown
## CLI Review: {scope}

### Baseline
{Probes you ran and what happened, including any you could not run and why. Language and argument
library. **At `--all` only:** the §P results. On a diff review, omit this block unless a probe you
ran actually failed.}

### Critical Issues (Must Fix)
- {file}:{line} — {category}: {description}
  **Probe:** {the command and its actual output, where a probe found it}
  **Impact:** {what breaks, for whom}
  **Fix:** {concrete change — with code, in this project's language}

### Improvements (Should Fix)
- {file}:{line} — {category}: {description}
  **Fix:** {solution}

### Suggestions (Nice to Have)
- {file}:{line} — {category}: {description} — {suggested change}

```

If `--multi` was used, append one subsection per advisor that responded (titled with the advisor's
name as reported by `second-opinion`), then a **Cross-Model Agreement** subsection.

## Examples

**A gate that only covers half the paths:**
> /review-cli --all

`rm` has no confirmation, no `--yes` and no `--force`. The justification is an `undo` command — but
`undo` is only wired for one of two storage backends, and on the other it returns "this backend
does not support undo". Reports Must Fix: on that backend `rm` is unprompted and unrecoverable.
The finding needs reading the gate, the thing that justifies its absence, and every construction
path of that thing — three places, none of which look wrong alone.

**Broken pipe, found by probe not by reading:**
> /review-cli

`cmd ls | head -3` prints three rows and then panics — `failed printing to stdout: Broken pipe`,
exit 101. Nothing in the source mentions SIGPIPE, and nothing looks wrong: it is a plain print in
a loop. Reports Should Fix with the one-line fix for the language, and notes that exit 101 will be
misread as a genuine bug in any report.

**Success message for a no-op:**
> /review-cli --changed

`uninstall --consumer <typo>` removes nothing, then reports "removed consumer <typo> (last
consumer; hooks and active binary removed)" and exits 0 — having actually torn down the shared
hooks, because zero registered consumers remain. The idempotent remove is correct; the message is
the defect. Reports Must Fix: a misspelled argument performs a full teardown and reports success.

## Troubleshooting

### Can't build or install the tool, so Step 0 is impossible
**Solution:** Review §2–§7 from the source and say in the Baseline that probes were not run. Do
not infer probe results from reading — the whole point of Step 0 is that these behaviours don't
appear in the source. Ask the user for a build command or a fixture project rather than guessing.

### The pipe probe passes but the tool looks unprotected
**Solution:** The output fit in the pipe buffer (~64 KB), so the writer never saw the closed pipe.
Re-run against the largest output the tool can produce, or a project with real data in it. A tool
can be exposed by construction and shielded only by volume — that is still a finding, because the
volume is the user's data, not a property of the tool.

### Unsure whether a missing affordance is a defect or a scope decision
**Solution:** Check whether the tool's own conventions imply it. A CLI that offers `--json` on
three subcommands and not the fourth has made a consistency promise; one that offers it nowhere
has made a scope decision. Same for `--dry-run`, short flags, and confirmation prompts. Report the
first as a defect and the second as a suggestion, if at all.

## Notes

- Probe first, read second. The probes cost a minute and find the defects that reading misses.
- Respect project conventions in AGENTS.md / CLAUDE.md, and read the README — a gap between it and
  `--help` is a finding in its own right.
- Don't be dogmatic. The most-cited source in this area says of itself: "When following convention
  would compromise a program's usability, it might be time to break with it—but such a decision
  should be made with care." Look for the decision, not just the deviation.
- Credit what's right. A CLI that refuses on a non-TTY with a message naming both escapes, or that
  re-parses its own rendering before writing a file it doesn't own, is doing something most don't —
  and saying so keeps the review honest about what the remaining findings cost.
- Sources: Command Line Interface Guidelines (clig.dev); POSIX Utility Syntax Guidelines and
  `<signal.h>`; the GNU Coding Standards on `--help` and `--version`; the XDG Base Directory
  Specification; no-color.org; the GNU Bash manual on exit status; the Python `signal` docs' note
  on SIGPIPE; the Rust CLI Book and the `-Zon-broken-pipe` documentation; 12 Factor CLI Apps; git's
  `--porcelain` stability wording. Quoted lines and the contested list are in
  `references/conventions.md`.

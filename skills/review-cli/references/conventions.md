# CLI conventions: the normative sources, quoted

Load when writing a finding that needs a citation, or when you are unsure whether something is a
rule or folklore. Verified 2026-09-14.

The second half of this file — **Contested or outdated** — matters as much as the first. Several
widely-repeated pieces of CLI advice are wrong, stale, or have no consensus behind them.

---

## Streams

clig.dev:

> "**Send output to `stdout`.** The primary output for your command should go to `stdout`. Anything
> that is machine readable should also go to `stdout`—this is where piping sends things by default."

> "**Send messaging to `stderr`.** Log messages, errors, and so on should all be sent to `stderr`.
> This means that when commands are piped together, these messages are displayed to the user and
> not fed into the next command."

## `--help` and `--version`

GNU Coding Standards, which is unambiguous and settles the stdout-vs-stderr question:

> "The standard `--help` option should output brief documentation for how to invoke the program,
> **on standard output**, then **exit successfully**. Other options and arguments should be ignored
> once this is seen, and the program should not perform its normal function."

> "All programs should support two standard options: `--version` and `--help`."

`--version` must likewise print "all on standard output" and exit successfully, ignoring other
arguments.

clig.dev on content:

> "**Display concise help text by default.** When `myapp` or `myapp subcommand` requires arguments
> to function, and is run with no arguments, display concise help text."

> "Ignore any other flags and arguments that are passed—you should be able to add `-h` to the end of
> anything and it should show help. Don't overload `-h`."

The concise text should contain: a description of what the program does, one or two example
invocations, descriptions of flags unless there are many, and a pointer to `--help`.

## Exit codes

POSIX standardises only success vs failure:

> "Usually, utilities return zero for successful completion and values greater than zero for
> various error conditions. … A strictly conforming application shall not rely on any specific
> value in the range shown and shall be prepared to receive any value in the range."

GNU Bash manual, for the shell-side mapping:

> "When a command terminates on a fatal signal whose number is N, Bash uses the value 128+N as the
> exit status."

> "If a command is not found, the child process created to execute it returns a status of 127. If a
> command is found but is not executable, the return status is 126."

> "All builtins return an exit status of 2 to indicate incorrect usage, generally invalid options or
> missing arguments."

So 128+N is the *shell's* reporting of a signal death, not something a program sets. Python's
argparse is a second source for the usage convention: an invalid argument list "will print a
message to `sys.stderr` and exit with a status code of 2."

clig.dev adds only:

> "**Return zero exit code on success, non-zero on failure.** … Map the non-zero exit codes to the
> most important failure modes."

## Signals

POSIX `<signal.h>` default actions — SIGINT, SIGPIPE and SIGTERM all have default action "T",
defined as "Abnormal termination of the process."

clig.dev:

> "**If a user hits Ctrl-C (the INT signal), exit as soon as possible.** Say something immediately,
> before you start clean-up. Add a timeout to any clean-up code so it can't hang forever."

> "**If a user hits Ctrl-C during clean-up operations that might take a long time, skip them.** Tell
> the user what will happen when they hit Ctrl-C again, in case it is a destructive action."

clig.dev says nothing at all about SIGPIPE or SIGTERM — that gap is why §1 of the skill spells
broken-pipe handling out.

## Prompts and TTY

clig.dev:

> "**Only use prompts or interactive elements if `stdin` is an interactive terminal (a TTY).** This
> is a pretty reliable way to tell whether you're piping data into a command or whether it's being
> run in a script, in which case a prompt won't work and you should throw an error telling the user
> what flag to pass."

> "**Never _require_ a prompt.** Always provide a way of passing input with flags or arguments. If
> `stdin` is not an interactive terminal, skip prompting and just require those flags/args."

> "**If `--no-input` is passed, don't prompt or do anything interactive.**"

> "**Let the user escape.** Make it clear how to get out. … If your program hangs on network I/O
> etc, always make Ctrl-C still work."

## Destructive actions

clig.dev's graduated model, which is the most useful thing in this whole area:

> "**Confirm before doing anything dangerous.** A common convention is to prompt for the user to
> type `y` or `yes` if running interactively, or requiring them to pass `-f` or `--force`
> otherwise."

> "'Dangerous' is a subjective term, and there are differing levels of danger:
> * **Mild:** A small, local change such as deleting a file. You might want to prompt for
>   confirmation, you might not. …
> * **Moderate:** A bigger local change like deleting a directory, a remote change … Consider
>   giving the user a way to 'dry run' the operation …
> * **Severe:** Deleting something complex, like an entire remote application or server. You don't
>   just want to prompt for confirmation here—you want to **make it hard to confirm by accident**.
>   Consider asking them to type something non-trivial such as the name of the thing they're
>   deleting. Let them alternatively pass a flag such as `--confirm="name-of-thing"`, so it's still
>   scriptable."

> "Consider whether there are non-obvious ways to accidentally destroy things. For example, imagine
> a situation where changing a number in a configuration file from 10 to 1 means that 9 things will
> be implicitly deleted—this should be considered a severe risk, and should be difficult to do by
> accident."

The `--confirm="name-of-thing"` detail is the one that resolves the real tension: it is
simultaneously hard to do by accident and scriptable.

## Robustness

clig.dev:

> "**Make things time out.** Allow network timeouts to be configured, and have a reasonable default
> so it doesn't hang forever."

> "**Make it recoverable.** If the program fails for some transient reason (e.g. the internet
> connection went down), you should be able to hit `<up>` and `<enter>` and it should pick up from
> where it left off."

> "**Make it crash-only.** This is the next step up from idempotence. If you can avoid needing to do
> any cleanup after operations, or you can defer that cleanup to the next run, your program can exit
> immediately on failure or interruption."

> "**People are going to misuse your program.** Be prepared for that. They will wrap it in scripts,
> use it on bad internet connections, run many instances of it at once…"

## Config precedence and locations

clig.dev's tiers, highest to lowest: flags, the shell's environment variables, project-level
configuration, user-level configuration, system-wide configuration. Note it does **not** list
built-in defaults as a tier — the commonly-quoted six-tier version is a synthesis.

Its three-way framework is the better judgment aid:

> "1. Likely to vary from one invocation of the command to the next. … Recommendation: **Use
> flags.**"
> "2. Generally stable from one invocation to the next, but not always. Might vary between projects.
> … Recommendation: **Use flags and probably environment variables too.**"
> "3. Stable within a project, for all users. … Recommendation: **Use a command-specific,
> version-controlled file.**"

> "**Do not read secrets from environment variables.** While environment variables may be convenient
> for storing secrets, they have proven too prone to leakage"

> "**Do not read secrets directly from flags.** When a command accepts a secret, e.g. via a
> `--password` flag, the flag value will leak the secret into `ps` output and potentially shell
> history." … "Consider accepting sensitive data only via files, e.g. with a `--password-file` flag,
> or via `stdin`."

> "**If you automatically modify configuration that is not your program's, ask the user for consent
> and tell them exactly what you're doing.** Prefer creating a new config file … rather than
> appending to an existing config file."

XDG Base Directory Specification — the state-vs-data sentence people get wrong:

> "The `$XDG_STATE_HOME` contains state data that should persist between (application) restarts, but
> that is **not important or portable enough to the user that it should be stored in
> `$XDG_DATA_HOME`**. It may contain:
> * actions history (logs, history, recently used files, …)
> * current state of the application that can be reused on a restart (view, layout, open files, undo
>   history, …)"

Defaults: `$XDG_CONFIG_HOME` → `$HOME/.config`, `$XDG_DATA_HOME` → `$HOME/.local/share`,
`$XDG_STATE_HOME` → `$HOME/.local/state`, `$XDG_CACHE_HOME` → `$HOME/.cache` ("non-essential").
`$XDG_RUNTIME_DIR` carries the spec's only MUSTs: owned by the user, sole read/write access, mode
0700 — so a socket path is mechanically checkable.

## Flags and arguments

POSIX Utility Syntax Guidelines — the three durable ones:

> **Guideline 4:** All options should be preceded by the '-' delimiter character.
> **Guideline 10:** The first **--** argument that is not an option-argument should be accepted as a
> delimiter indicating the end of options. Any following arguments should be treated as operands,
> even if they begin with the '-' character.
> **Guideline 13:** For utilities that use operands to represent files to be opened for either
> reading or writing, the '-' operand should be used to mean only standard input (or standard output
> when it is clear from context that an output file is being specified) or a file named **-**.

clig.dev:

> "**Prefer flags to args.** It's a bit more typing, but it makes it much clearer what is going on."

> "**Have full-length versions of all flags.** For example, have both `-h` and `--help`."

> "**Only use one-letter flags for commonly used flags,** particularly at the top-level when using
> subcommands."

> "**If input or output is a file, support `-` to read from `stdin` or write to `stdout`.**"

> "**If possible, make arguments, flags and subcommands order-independent.**"

Standard flag names it lists: `-a/--all`, `-d/--debug`, `-f/--force`, `--json`, `-h/--help` ("This
should only mean help"), `-n/--dry-run`, `--no-input`, `-o/--output`, `-p/--port`, `-q/--quiet`,
`-u/--user`, `--version`, and `-v` (ambiguous — verbose or version, or avoid).

## Future-proofing

clig.dev's framing sentence:

> "Subcommands, arguments, flags, configuration files, environment variables: these are all
> interfaces, and you're committing to keeping them working."

> "**Don't create a 'time bomb.'** Imagine it's 20 years from now. Will your command still run the
> same as it does today, or will it stop working because some external dependency on the internet
> has changed or is no longer maintained?"

> "**Changing output for humans is usually OK.** The only way to make an interface easy to use is to
> iterate on it, and if the output is considered an interface, then you can't iterate on it.
> Encourage your users to use `--plain` or `--json` in scripts to keep output stable"

> "**Don't have a catch-all subcommand.**" … "now you can never add a subcommand named `echo`—or
> _anything at all_—without risking breaking existing usages."

> "**Don't allow arbitrary abbreviations of subcommands.**" … "you can't add any more commands
> beginning with `i`, because there are scripts out there that assume `i` means `install`."

## Machine-readable output

Git's `--porcelain` is the citable example of a stability promise:

> "Version 1 porcelain format is similar to the short format, but is **guaranteed not to change in a
> backwards-incompatible way between Git versions or based on user configuration**. This makes it
> ideal for parsing by scripts."

Git also versioned the format (`--porcelain=v2`) so it could evolve while keeping the promise —
that is the answer to "how do you ever change a stable output format".

12 Factor CLI Apps, on tables:

> "It's important that each row of your output is a single 'entry' of data. **Never output table
> borders.** It's noisy and a huge pain for parsing."

Its factor 5 gives the most concrete error structure anywhere, with no clig.dev equivalent — an
error message should carry an error code, a title, an optional description, how to fix the error,
and a URL for more information.

## Colour

no-color.org, the requirement verbatim:

> "**Command-line software which adds ANSI color to its output by default should check for a
> `NO_COLOR` environment variable that, when present and not an empty string (regardless of its
> value), prevents the addition of ANSI color.**"

Two scoping sentences that are routinely missed:

> "If your software outputs color by default, please consider not doing so."
> "If your software does not output color by default, you do not need to bother with this standard."

Its reference implementation ends with the comment "do getopt(3) and/or config-file parsing to
possibly turn color back on" — so an explicit `--color` flag *may* override `NO_COLOR`.

clig.dev's fuller disable list: not a TTY (checked per-stream, since piping stdout doesn't make
stderr colour unwanted), `NO_COLOR` set and non-empty, `TERM=dumb`, `--no-color`, and optionally a
tool-specific `MYAPP_NO_COLOR`. Plus:

> "**If `stdout` is not an interactive terminal, don't display any animations.** This will stop
> progress bars turning into Christmas trees in CI log output."

## On breaking the rules

clig.dev about itself:

> "When following convention would compromise a program's usability, it might be time to break with
> it—but such a decision should be made with care."

> "It's ironic that this document implores you to follow existing patterns, right alongside advice
> that contradicts decades of command-line tradition. We're just as guilty of breaking the rules as
> anyone."

> "'Abandon a standard when it is demonstrably harmful to productivity or user satisfaction.' — Jef
> Raskin, The Humane Interface"

---

# Contested or outdated — do not repeat as fact

**1. `sysexits.h` has three positions and no consensus.** FreeBSD's own `sysexits(3)`: "This
interface has been deprecated and is retained only for compatibility. Its use is discouraged." The
Linux man-pages version carries no deprecation language, only "The choice of an appropriate exit
value is often ambiguous." The Rust CLI Book actively recommends it via the `exitcode` crate.
clig.dev doesn't mention it. **Don't recommend adopting it and don't call it dead** — review for
documented, internally consistent codes instead.

**2. `--help` to stderr is wrong, and this one does have an answer.** GNU standards, argparse and
clap all put requested help on stdout with exit 0. The folklore comes from conflating two events:
requested help → stdout, exit 0; *usage error* → stderr, non-zero. A tool doing either backwards is
wrong. There is real debate in the wild but no standards body on the stderr side.

**3. The rule is "don't create a time bomb", not "time machine".** It's about a program silently
breaking in 20 years because an external dependency vanished — not about replaying history. Getting
the name wrong makes it unsearchable.

**4. `#[unix_sigpipe = "sig_dfl"]` is stale syntax and was never stable.** It became the nightly
`-Zon-broken-pipe={kill,error,inherit}` flag; on current toolchains even
`#![feature(unix_sigpipe)]` fails with "unknown feature", so the name is gone from the compiler
entirely. The tracking issue is open and the plan has moved again, to an externally implementable
item. Any advice saying "just use `#[unix_sigpipe]`" is unusable.

**5. `signal.signal(SIGPIPE, SIG_DFL)` in Python is explicitly advised against by the Python
docs** — "Doing that would cause your program to exit unexpectedly whenever any socket connection is
interrupted while your program is still writing to it." This is the most repeated piece of CLI
folklore in this area. See `language-notes.md` for the sanctioned fix.

**6. POSIX Guidelines 3, 7 and 9 are widely and deliberately violated.** Guideline 3 permits only
single-character options — so `--long` has no POSIX basis at all and is a GNU extension. Guideline 7
forbids optional option-arguments (`--color[=when]`). Guideline 9 requires all options before
operands (git, docker and cargo all break this). Citing POSIX as though modern tools conform to all
14 misrepresents it.

**7. "Flags > env > project > user > system > defaults" is a synthesis.** clig.dev lists five tiers
and stops at system-wide. State the ordering as convention, not as a quote.

**8. `CLICOLOR`/`CLICOLOR_FORCE` are not a standards-body spec** — one person's write-up of a BSD
`ls` convention. `NO_COLOR` is the one with broad adoption and the one to require. Heroku's own
style guide uses `COLOR=false`, matching neither; this corner is unsettled.

**9. `XDG_STATE_HOME` post-dates most advice you'll find.** Anything written before ~2021, including
12 Factor CLI Apps (2018), will tell you to put logs and history in the data directory. The spec now
says state. Quote the spec, not a secondary source.

**10. Julia Evans' terminal "rules" are explicitly descriptive.** She says so twice — "descriptive,
not prescriptive" and "My goal here isn't to convince authors of terminal programs that they
_should_ follow any of these rules." Cite her as evidence of what users *expect*, which is often the
stronger argument, not as a normative source.

**11. No citable source exists on partial-failure exit semantics.** What a bulk command should exit
when 7 of 10 items succeed is undecided in the literature. Report that the tool must decide and
document it; don't claim it picked wrong.

**12. No normative source for `--no-<flag>` negation.** Widespread practice; absent from both the
GNU standards and clig.dev as a pattern. Don't cite it as a standard.

**13. No source states "exit 130 on SIGINT" directly.** It follows from bash's 128+N rule plus
SIGINT=2, and is the usual convention — present it that way.

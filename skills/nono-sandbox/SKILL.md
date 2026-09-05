---
name: nono-sandbox
description: 'Decide whether a failure is actually a nono sandbox denial before treating it as one. Use when a command fails with "Operation not permitted", "sandbox-exec: sandbox_apply", EACCES, EPERM, or a "Sandbox denial" footer. Most such failures on this machine are NOT missing grants — verify first, then either disable a nested sandbox or report a real denial to the user.'
compatibility: Requires the nono sandbox (https://github.com/nolabs-ai/nono).
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Working inside a nono sandbox

Your granted workspace directory is read+write. Package caches, agent config and a few named files are granted.
Most of the rest of `$HOME` is not.

**Most failures that look like sandbox denials are not.** Of the sandbox reports raised on this
machine, two thirds turned out to be something else — a tool sandboxing itself, a misread
diagnostic, or an unrelated failure with a plausible-looking error string. Treat "the sandbox
blocked me" as a hypothesis to test, never a conclusion to report.

## Before you conclude anything

**1. Did the command actually fail?** nono prints `Sandbox denial: N paths blocked` at exit
**even on successful runs**, listing harmless probes — tools walking up from the workdir looking
for config. Check the exit code and the real output first. A denial footer next to a failure
does not mean it caused the failure.

**2. Quote the path from the error.** If you cannot point at a line of output naming a specific
path, you do not have a sandbox problem — you have a guess. Never report a denial with a
placeholder path.

**3. Verify that exact path:**

```
nono why --self --path /the/path/from/the/error --op read|write|readwrite
```

`--self` is **not optional**. Without it, `nono why` evaluates nono's *default* profile rather
than the running session and reports `DENIED / path_not_granted` for almost anything — including
from a shell that is not sandboxed at all. A bare `nono why` is never evidence.

Two ways `nono why` still misleads you:

- **It misreports grants inside the built-in keychain protection.** A `read_file` grant on a
  path under `~/Library/Keychains` is honored by the sandbox while `nono why` reports
  `DENIED / filesystem_deny`. If it says denied but the command works, believe the command.
- **It resolves real paths.** A path that does not exist yet reports `path_not_granted` even
  when its parent directory is granted.

When the verdict contradicts the error, trust an actual read or write inside `nono run` over
either.

**4. A denial can arrive as a non-permission errno.** A hidden path reports *absent* to `stat`
and *present* to an operation on it:

```
DENIED   exists(): False   mkdir: EEXIST   open(…,'x'): EEXIST   link: EPERM
GRANTED  exists(): True    mkdir: EEXIST   open(…,'x'): EEXIST   link: CREATED
```

`EEXIST` alone means nothing — it fires on every path that exists. The **disagreement** is the
signal. Calls that check permission before existence stay honest, so this only shows up where
the existence check runs first.

The general form: **the most legible output can point away from the actual cause.** An errno
lying about existence, and a `forbidden-sandbox-reinit` denial suggesting `--allow <path>` when
it carries no path, are the same trap.

## The most common cause: something under nono starting its own sandbox

Nono blocks sandbox re-initialization for **anything** running under the profile — usually not
the agent itself but a process it spawned (SwiftPM evaluating `Package.swift`, xcodebuild's
plugin execution, Chrome's zygote). The giveaway is `sandbox-exec: sandbox_apply: Operation not
permitted`, `forbidden-sandbox-reinit` in the footer, or an error naming a path that
`nono why --self` says is **allowed**.

The denial carries **no path**, so no grant can address it — ignore nono's own
`--allow <path>` suggestion here. Disable the inner sandbox instead:

| tool | flag |
|---|---|
| `swift build` / `swift test` / `swift run` | `--disable-sandbox` |
| `xcodebuild` | `-IDEPackageSupportDisableManifestSandbox=1 -IDEPackageSupportDisablePluginExecutionSandbox=1` |
| Chrome / Chromium | `--no-sandbox` |
| Codex | `-c sandbox_mode="danger-full-access"` |

Most of this is already handled: the wrappers set `OTHER_SWIFT_FLAGS` and
`AGENT_BROWSER_ARGS`, and `bin/sandbox-shims/xcodebuild` appends the two
`-IDEPackageSupport…` flags, which are NSUserDefaults and so reachable only through
argv. A tool that spawns `xcodebuild` itself therefore works without doing anything.
`swift build` and `swift test` still take `--disable-sandbox` on their own command line.

## Known limits — report these, do not try to fix them

- **Xcode test targets with a host application** (`TEST_HOST` set) cannot run sandboxed: the app
  launches via LaunchServices, lands outside the sandbox, and its connection back never
  establishes. `swift test` on a `Package.swift` target is unaffected.
- **A profile change does not reach a running session.** Seatbelt applies the policy at process
  start. If a grant was added after this session began, it is invisible until restart — say so
  rather than asking for it again.

## Denied on purpose — these will not be granted

Each was decided deliberately and measured; the reasoning is in
[`docs/security-model.md`](https://github.com/nielsmadan/agentic-coding/blob/main/docs/security-model.md). Name the blocker once, hand over the
command, and continue with what is still possible. Do not propose a grant, do not work around it,
and do not raise it again in a later session.

| Blocked | Why it stays blocked | Give the user this |
|---|---|---|
| `~/Library/Keychains/login.keychain-db` | Holds the login credentials and codesigning identities. A read grant returns them as **plaintext** through securityd with no prompt, and outbound network is unrestricted, so readable means exfiltratable. Distribution and Developer ID signing is attributable beyond this machine. | For codesigning, use `agent-signing.keychain-db` — already granted, and it holds one Apple Development identity. Anything needing the login keychain runs in a plain terminal. |
| `~/.ssh` | Private keys. Would let an agent `git push` and ssh to any host. `git push` is separately denied for the same reason. | `git push` — or the ssh command — themselves. |
| `~/.local/state/mise/trusted-configs` | `mise trust` applies a repo's `[env]`, including `_.path`, to the user's own interactive shell in that directory. That is a route out of the sandbox. | `mise trust`, once, in that repo. |
| `~/.gradle/init.d`, `~/.gradle/gradle.properties` | Gradle executes init scripts and applies `jvmargs` on **every** build, including the user's unsandboxed ones. | Nothing to run — these stay denied whether or not the rest of `~/.gradle` is granted. |

The shape they share: an agent writes or reads something that the *user's own* unsandboxed tools
later trust. A grant that only fails safe inside the granted workspace is a different question and
may well be reasonable — these are not that.

## When it is a real denial

Say so plainly, quote the path and the `nono why --self` verdict, and **stop**. Adding a grant is
the user's decision: it widens the boundary for every agent on the machine, and some paths that
look like config hold credentials.

Do **not**:

- offer `nono run --allow …` or `nono profile promote` as remedies — profiles are
  version-controlled and edited at their source, not drafted ad hoc
- relocate files, weaken a test, or call a binary by another path to get around it
- ask a peer session to read the path for you

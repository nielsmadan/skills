# CLI, Plugin, and Library QA

## CLI and TUI

Locate the documented build/run entry point. Establish whether it executes the
current checkout or an older installed binary; record the executable/build identity.
Use disposable fixtures and documented config/state overrides. Never repoint `HOME`
or replace the user's real config to manufacture isolation. If an operation targets
real machine state, use the tool's supported fixture mode or mark that case blocked.

Select applicable cases for the changed command:

- Root/subcommand help, the advertised example, missing/invalid/conflicting options.
- Empty, malformed, boundary, Unicode, and space-containing inputs or paths.
- Stdin as a pipe and at EOF; separate stdout, stderr, and exit status. Parse promised
  JSON as JSON and verify its contents; an exit code alone is insufficient.
- TTY versus noninteractive invocation, prompts/defaults, cancellation with Ctrl-C,
  progress while work is pending, and a slow or failed dependency.
- First run and existing config, documented precedence, rerun/idempotence, partial
  failure and recovery. Inspect files/state produced through the normal command.

For a TUI, use a PTY and real key sequences, then verify the resulting screen and
state. Noninteractive output does not establish interactive behavior. Bound waits
and terminate only the process started for the case.

## Agent plugins and skills

Read the project's host-specific development instructions. Validate the actual
packaged artifact, then load it through the real host's documented local-development
mechanism in a disposable test session. Record host version and loaded package
path/version; stale caches can make a source change invisible.

Keep these checks distinct:

1. **Packaging and discovery:** manifests, resource paths, executable hooks, and host
   registration of the changed skill/command/tool.
2. **Explicit invocation:** perform the affected action and observe its output/state
   or side effect, including malformed input and unavailable dependencies.
3. **Behavior:** test a positive natural-language trigger and a nearby negative case
   where relevant; exercise deactivate/reset, persistence/resume, session isolation,
   and precedence only when the feature promises them.

Use host diagnostics and observed behavior as evidence. Reading `SKILL.md`, parsing
a manifest, or an agent saying it loaded the plugin proves less than a real
invocation. A trigger walkthrough is a hypothesis until tested in the host. Record
prompt, observable acceptance criteria, model/host, and attempts for variable agent
behavior. Keep host runs bounded; do not launch an unbounded agent test matrix or
recursive agent workflow. Mark unsupported hosts untested instead of extrapolating.

For plugins that affect prose, check an ordinary reply and a code/file-writing
task: assess the promised scope of the behavior in both. For hooks, actually trigger
the event. For MCP integrations, establish discovery and perform the relevant
protocol/tool interaction; a running process alone is insufficient.

## Libraries and internal changes

Use an existing example, sample app, or minimal consumer through the public API.
Check changed integration behavior, packaging, and errors. If the change is purely
internal and existing tests cover the observable contract, explain why exploratory
runtime QA adds little and report the relevant checks. Do not invent a UI or build
a new test framework just to make the skill applicable.

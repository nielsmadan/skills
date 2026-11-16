---
name: code-tour
description: Give an interactive tour of code, starting with an overview of the changes and tracing concrete inputs through entry points, calls, state changes, and branches, pausing for questions at each step. Use for "code-tour", "give me a tour of the code", or "walk me through this code step by step". Defaults to staged changes; accepts --staged, --changed, --unstaged, --unpushed, --all, or a target. Reuses relevant QA screenshots and logs. Use qa-tour for a walkthrough the user operates in the running app, and explain for a one-shot explanation or generated documentation.
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Code Tour

Teach the selected code in the main conversation, following execution from a concrete
input through its observable result. Keep the tour read-only unless the user explicitly
requests an edit. Preparation is source inspection and reuse of existing evidence;
it does not require starting the app or running QA.

## Resolve scope

Read project instructions and `git status --short`. Accept one scope flag; with no
flag or target, use `--staged`. Announce the resolved scope.

| Scope | Selection |
|---|---|
| `--staged` (default) | Staged changes: `git diff --cached`. |
| `--changed` / `--unstaged` | Unstaged changes: `git diff`, plus relevant untracked files from `git ls-files --others --exclude-standard`. |
| `--unpushed` | Changes across unpushed commits, identified with `git rev-list HEAD --not --remotes`; establish the range's base before reading its aggregate diff. Exclude working-tree changes. |
| `--all` | The current project, organized into input-driven flows. |
| Target alone | The named feature, path, symbol, command, or request in the current code. With a scope flag, the target narrows that scope. |

An empty scope stays empty: report it and ask for another scope or target. Do not
substitute recent commits. For `--unpushed`, ask for an explicit range or another
scope if there is no remote/upstream or no reliable base. An explicit revision or
range selects that historical code. Outside Git, a target or `--all` can still be
toured; ask for one when none was supplied.

Scope selects the changes to explain, not just filenames. Follow unchanged callers,
dependencies, and contracts when needed to connect those changes, identifying them
as existing context. Read the selected version: `git show :path` for staged files,
`git show <revision>:path` for committed code, and working-tree files for current
code. Do not mix unstaged edits into a staged explanation or switch checkouts.
For mixed working-tree changes, read both diffs to distinguish the selected delta.

## Prepare the route and supporting evidence

Inspect the selected changes, relevant project docs, callers, implementations, and
tests. Build an itinerary around behavior rather than diff order or file order.
Group distinct features into separate flows; include supporting schemas, config,
tests, and non-runtime changes where they explain a flow. If the selection is only
configuration, docs, or tests, trace the consuming tool or test invocation instead
of inventing an application entry point.

Choose a concrete input for each flow:

- UI: app startup and route/navigation needed to reach the feature, the screen or
  control the user encounters, then the action that enters the changed behavior.
- CLI: the actual command, representative arguments/input, and command dispatch.
- Backend: the method and route, representative request, and relevant middleware.
- Other consumers: the triggering event, callback, job, or public library call.

Before presenting a flow, establish its participating symbols/files and the main
call and data relationships. Trace across callbacks, async boundaries, client/server
handoffs, storage, and return/render paths. Keep hypothetical example values clearly
separate from observed output; mark unresolved dynamic dispatch as uncertain.

Look for QA evidence paths already given in the conversation or project test docs.
Otherwise inspect indexes under `${TMPDIR:-/tmp}/qa/` for the current checkout.
The QA convention is `<project-key>/<UTC-timestamp>-<feature>-<unique-suffix>/index.md`;
the project key combines the repo name and a short hash of its absolute root. Match
the index's checkout/build identity, scope, and scenarios rather than guessing the
hash or choosing the newest directory indiscriminately. Durable runs may instead
be linked from `docs/tests/`.

Read the matching index and only relevant artifacts. Check that each file exists
and inspect its content before describing it; view screenshots rather than inferring
their contents from filenames. Match UI evidence to the component, scenario, state,
and viewport/device; match logs or request/response captures to the invocation and
branch being explained. The index distinguishes original failures and retests:
preserve that distinction. Label older or mismatched captures as historical context,
not proof of the selected code's current behavior. If evidence is absent, expired,
or unidentifiable, say so briefly and continue from source without running QA.

## Open with the overview, then pause

The first tour response contains:

1. The scope and high-level aspects added or changed, such as a request, route,
   UI components, state handling, persistence, or tests, with their purpose.
2. A short itinerary of input-driven flows. For the first flow, show its concrete
   input and a compact map of the participating code, with file/symbol references
   and each piece's role, before diving into implementation.
3. The proposed first stop and an invitation to continue or adjust the route.

Stop here and wait for the user. Do not append the full walkthrough to the overview.
For later flows, introduce their code map before their first implementation stop.

## Walk one meaningful step at a time

Each stop covers one cohesive execution step, not an arbitrary whole file:

- Locate the current function/component and show a small, exact code excerpt with
  a clickable absolute file path and line number. Explain the relevant lines,
  including non-obvious syntax, in terms of this input and the feature's behavior.
- State what enters the step, what it does, and what leaves it: values, state,
  effects, result, or the next call. Connect it to the preceding and next steps.
- At a decision, name the condition and meaningful outcomes. Trace the chosen path
  and queue alternate paths, returning to the decision or join point afterward.
  Cover changed error/loading/empty/permission/data variants as well as success;
  keep unchanged peripheral branches brief unless needed or requested.
- When useful, attach the verified QA artifact beside the code it illustrates:
  `[Rendered empty state](/absolute/path/Q2-empty.png)` or a log/capture link.
  Name the scenario/state and any material mismatch. Include a short relevant log
  excerpt when it helps connect the source to the output.

For staged or historical code that differs from the working file, label the excerpt's
version and its line numbers explicitly; warn that opening the working-file link
may show different code. Never present those coordinates as current-file lines.

End each stop with a compact position marker: current flow/step, pending branches,
and next stop. Invite questions or feedback, then end the turn and wait. Do not
advance on silence. “Next”, “continue”, or equivalent advances one stop; a question
keeps the current stop open. Answer follow-ups at the requested depth, then return
to the same place. Honor requests to skip, reorder, or cover several steps together.

Feedback is not automatic permission to edit. If the user explicitly requests a
change, complete it and re-read affected code before resuming. Likewise, incorporate
user edits, rechecking affected references and evidence compatibility without
silently widening the original scope. Keep the remaining itinerary current.

Finish once the selected flows and queued branches have been covered or explicitly
skipped. Recap how inputs become outcomes, link the key code and evidence, and name
any skipped or unresolved pieces. Do not turn the tour into an unsolicited review,
documentation-writing task, or QA run.

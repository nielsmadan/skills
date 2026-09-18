# Research Behind the QA Workflow

Reviewed 2026-09-05. These are sources of workflow ideas; the skill is an original
synthesis. Read this file when revising the workflow, not on every QA run.

| Primary source | Ideas adopted |
|---|---|
| [gstack QA patterns](https://github.com/garrytan/gstack/blob/main/qa/sections/qa-patterns.md) | Infer affected workflows from changes and intent; cover loading, empty/error states, navigation, and adjacent regressions. |
| [Vercel dogfood](https://github.com/vercel-labs/agent-browser/blob/main/skill-data/dogfood/SKILL.md) | Reproduce findings, record them as discovered, and match screenshots/recordings to the defect. |
| [Anthropic webapp-testing](https://github.com/anthropics/skills/blob/main/skills/webapp-testing/SKILL.md) | Inspect the rendered app, reuse tooling, and manage the application-server lifecycle separately. |
| [Callstack dogfood](https://github.com/callstack/agent-device/blob/main/skills/dogfood/SKILL.md) and [commands](https://github.com/callstack/agent-device/blob/main/website/docs/docs/commands.md) | Use version-matched CLI help, native runtime evidence, explicit target selection, and platform-specific capabilities. |
| [CLI Guidelines](https://clig.dev/) | Check streams, exit status, pipes, interactive behavior, configuration, and cancellation through the executable. |
| [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference#debugging-and-development-tools) | Distinguish structural validation, host registration, and actual invocation. |
| [Schemathesis checks](https://schemathesis.readthedocs.io/en/stable/reference/checks) | Test API contracts, authorization, and stateful operation sequences. |

The adapters were checked against installed agent-browser 0.27.0 and agent-device
0.19.3 help. For the iOS offline caveat, see Callstack's
[settings implementation](https://github.com/callstack/agent-device/blob/main/packages/platform-apple/src/core/app-settings.ts).

The synthesis uses feature-scoped coverage and evidence. Upstream bug quotas,
arbitrary health scores, automatic git operations, mandatory browser use for
backends, and blanket video requirements do not fit this workflow.

Efficiency guidance reviewed 2026-09-17 against agent-device 0.21.0 help and its
[batching docs](https://github.com/callstack/agent-device/blob/v0.21.0/website/docs/docs/batching.md),
[snapshot docs](https://github.com/callstack/agent-device/blob/v0.21.0/website/docs/docs/snapshots.md),
and [response views](https://github.com/callstack/agent-device/blob/v0.21.0/src/daemon/response-views.ts).
Fresh-worker handoffs and phase-boundary compaction draw on
[Claude subagents](https://code.claude.com/docs/en/sub-agents#how-forks-differ-from-other-subagents)
and [OpenAI subagents](https://developers.openai.com/codex/subagents#why-subagent-workflows-help).
These are workflow recommendations, not measured token-savings guarantees.

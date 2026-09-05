# nlsmdn skills

Opinionated agent skills for code review, research, and daily workflow. 45 skills, generated from
[nielsmadan/agentic-coding](https://github.com/nielsmadan/agentic-coding) — do not edit this repo
directly, changes are overwritten.

## Install

Claude Code, as a plugin:

```
claude plugin marketplace add nielsmadan/skills
claude plugin install nlsmdn@nlsmdn
```

Skills then appear as `/nlsmdn:code-review` and so on.

Any other agent (Codex, Cursor, OpenCode, Zed, Copilot CLI, Gemini CLI, Amp):

```
npx skills add nielsmadan/skills
```

Add `--skill <name>` to install one, or `--all` to cover every detected agent.

## Notes

- Third-party marketplaces default to **auto-update off**. Enable it per
  marketplace in `/plugin`, or run `claude plugin update nlsmdn` when you want
  changes.
- There is no `version` field: the version resolves to the source commit SHA, so
  every push is available immediately to anyone who updates.
- Codex budgets its initial skill list at 2% of the model's context window
  (8,000 characters only when the window is unknown) and shortens descriptions
  first when over it; only very large sets see skills omitted. `--skill <name>`
  installs a subset if you want to keep the catalog lean.
- Some skills declare a `compatibility` requirement (an external CLI). Those
  degrade gracefully when the tool is absent.

## Skills

### Code review

| Skill | Description |
|---|---|
| `code-review` | Clean up code comments, then review code with comprehensive and quick modes. Use when reviewing code changes, PRs, or specific files for quality, bugs, and best practices. |
| `review-architecture` | Review system architecture — layering, module boundaries, coupling/cohesion, pattern fit, quality attributes (scalability, resilience, evolvability), and architectural smells. Triggers "review architecture", "architecture review", "system design review", "check architecture". |
| `review-cleancode` | Review code for clean-code principles — SOLID, DRY, YAGNI, KISS, code smells. Triggers "review clean code", "check DRY/SOLID", "code smells". |
| `review-comments` | Review and clean up code comments for necessity, accuracy, non-duplication, clarity, and concise explanation of rationale. Use when comments may restate code, repeat a "why" already explained in the file, contain stale or vague claims, or need tightening before a PR. |
| `review-history` | Analyze how code changed over time. Use when investigating regressions, understanding why code was written a certain way, or finding when a behavior changed. |
| `review-interfaces` | Review interface design for functions, classes, modules, components — naming, params, encapsulation, YAGNI, usability. Triggers "review interfaces". |
| `review-library-use` | Review code for correct use of the repo's third-party libraries — checks the scoped files against the version-specific conventions recorded in the repo's `library-use` reference (docs-derived correct-usage rules, API contracts, footguns). Catches stale-API usage, deprecated patterns, and doc-violating misuse a general reviewer misses. Auto-invoked by `code-review` when a `library-use` reference exists. Triggers "review library use", "check library usage", "are we using this library correctly", "library convention review". |
| `review-perf` | Performance analysis for algorithmic complexity, memory leaks, N+1 queries, and render issues. Use when code feels slow, after adding loops/queries, or before scaling up. |
| `review-security` | Security audit for vulnerabilities, secrets, and unsafe patterns. Use before releases, after adding auth code, or when reviewing third-party integrations. |
| `review-swift` | Swift-specific code review focused on JUDGMENT-level design a linter and the compiler can't decide — state modeling with enums and value types (make invalid states unrepresentable), optional and error modeling, concurrency isolation intent, ARC ownership, SwiftUI identity/lifetime/dependencies, and escape hatches (`!`, `as!`, `try!`, `@unchecked Sendable`) that compile but hide a modeling problem. Deliberately does NOT duplicate SwiftLint, swift-format, or Swift 6 strict-concurrency diagnostics. Auto-invoked by `code-review` on Swift projects. Triggers "review swift", "swift review", "swiftui review", "swift concurrency review". |
| `review-todo` | Turn a completed code review into a persistent workflow that immediately proposes the complete ordered implementation plan, waits for whole-plan approval, then implements and commits every accepted finding. Use after a review when the user invokes review-todo, says "turn this review into a todo list", "work through these review findings", supplies directives such as "fix 2, 3; ignore 7", asks to revise or approve the plan, or resumes review work. Do not use to perform the original code review. |
| `review-typescript` | TypeScript-specific code review focused on JUDGMENT-level type design a linter can't decide — type modeling (make invalid states unrepresentable), inference-vs-annotation calls, and casts/`any` that hide a real modeling problem. Deliberately does NOT duplicate typescript-eslint. Auto-invoked by `code-review` on TypeScript projects. Triggers "review typescript", "typescript review", "type design review". |
| `second-opinion` | Get external AI opinions on a problem or question. Use when you want diverse perspectives from the agent CLIs you are not running (Claude, Codex, Pi, OpenCode). |

### Planning & research

| Skill | Description |
|---|---|
| `blind-spots` | Surface the decisions a plan or design left silently assumed, by interviewing the user in dependency order until nothing is unstated. Use when the user says "blind spots", "grill me", "stress-test this plan", "poke holes in this", "what am I missing", "interrogate this design", "what haven't I decided", or hands over a loose idea to sharpen before building. Do NOT use to explain a previous reply in more detail (use `huh`), to generate ideas when it is unclear what to build (use `ideation`), or to review an already-written plan with agents (use `review-plan`). |
| `evaluate-tech` | Structured evaluation before adopting a library, tool, or hosted service — enumerate candidates wide, then score every one against an identical rubric where maintenance health is a mandatory gate, not an afterthought. Use when the user asks "which library/package should I use", "what should we use for X", "which service/vendor should we pick", "is this package still maintained", "alternatives to X", "should we add this dependency", "should we switch to X", "pick a tool/service for", "evaluate this dependency/tool/service", or is choosing between named options to adopt. Covers code dependencies (npm, pip, pub, cargo, go), CLI/dev tools and dev software, and SaaS/API/hosted services. For learning how to USE something already chosen, or for open-ended technical research, use research-tech instead. |
| `ideation` | Generate ideas with structure when you're stumped — on what to build next, what the real problem is, or how to solve it. Pulls in research for context, diverges wide using matched frameworks, then converges on a prioritized few. Use when the user says "I'm stuck", "I'm stumped", "ideate", "brainstorm ideas", "help me think of", "what could I add", "what should I build", "I don't know what the problem is", "how could I solve", or wants idea generation on any topic (product, technical, business, writing, personal). For auditing an existing product against its users, use review-product instead. |
| `longshot` | Run a long autonomous build session from a brief — interrogate every open decision up front with `blind-spots`, then execute for hours without check-ins, deciding ambiguities as recorded rulings instead of stopping to ask. Per task a fresh implementer subagent, an independent spec+quality reviewer, a fix loop, then a whole-branch review and a handoff report with rulings, deferred questions and a squash proposal. Use when the user says "longshot", "work on this independently", "run with this", "ask me everything up front then go", "I'll be away", or hands over a multi-hour feature or package to build end to end. Do NOT use for a single small change — use `plan` for that. |
| `plan` | Lightweight planning workflow — delegate read-only planning to a Fable subagent, then implement in auto mode after a single go-ahead gate. The middle tier between "just do it" (tiny tasks) and heavyweight superpowers planning (big features). Never enters plan mode, so it sidesteps the plan-mode permission prompts. Use when the user invokes /plan, or wants a plan for a medium-sized task before implementing. |
| `research-general` | Research a non-technical topic online (science, history, news, policy, regional/regulatory, consumer purchases, personal decisions, fact-check). The default for research in non-code repos (e.g. a notes vault). For technical/developer topics — libraries, errors, tooling, and even choosing/evaluating dev tools or products — use `research-tech`. |
| `research-tech` | Research any technical / developer topic online — libraries, errors, best-practice/how-to, tool·library·model comparisons, product capabilities, and ecosystem/community signal. Use when you'll act on the answer as a developer (write code, debug, choose a tool). For non-technical topics (science, history, consumer, personal, fact-check) use `research-general`. |
| `review-plan` | Multi-agent review of implementation plans. Use after creating a plan but before implementing, especially for complex or risky changes. |
| `review-product` | Review a product from the user's perspective — build/refine a user persona, map their use cases (jobs-to-be-done), then audit the product for friction, gaps, and things to add or change. Triggers "review product", "product review", "review from the user's perspective", "product/UX critique", "what's missing for users". Use --live to also exercise the running app. |

### Testing & debugging

| Skill | Description |
|---|---|
| `debug-log` | Add debug logging to trace code execution. Use when debugging, tracing control flow, or investigating unexpected behavior. Any language (JS/TS, Python, Go). |
| `hard-fix` | Escalation workflow for stubborn bugs. Use when a bug persists after multiple fix attempts, you've tried several approaches, or you're stuck. |
| `perf-test` | Set up and run performance tests (profiling, load testing, or E2E scenarios), preserving occasional manual procedures and results for future repetition. Use when measuring code or endpoint performance, or before/after optimization work. |
| `pre-existing` | Fix any test/lint/type/build/CI failure instead of dismissing it as pre-existing, flaky, or unrelated. Triggers on red checks or `/pre-existing`. |
| `qa` | Exercise a developed feature through its real user or consumer interface, enumerate paths and edge/error/loading states first, and report evidence and coverage. Use for "qa", "QA the last feature", "test this feature end to end", "manual QA", or "check the user flows". Defaults to the last developed feature; accepts a feature, URL, command, app, or other scope. Covers web, native apps, CLIs, agent plugins, libraries, and backends. Use test for suite work and code-review for source review. |
| `test` | Assess test state and run the right action (default, no args): run the suite, then find failures, coverage gaps, and quality issues and route into fix, generate, or review. Explicit modes: review (--review, check test quality), generate (--generate <target>, create tests). Scope: --staged, --changed, --all, or context-based. Use when unsure what the tests need, or for test quality and creation. |

### Git & session history

| Skill | Description |
|---|---|
| `check-agent-logs` | Search past Claude Code, Codex, OpenCode, and Pi session logs to recover context from earlier work across the current project and sibling checkouts. Use when a bug, topic, or decision was handled in a previous session but its agent or checkout is unknown; when the user says "we fixed/discussed this before", "find the session where", "recover prior context", "check agent logs", "check Claude projects", "search past sessions/transcripts", or "which checkout was that in". Do not use for aggregate failure-pattern analysis; use review-logs for that. |
| `commit` | Commit ONLY the changes this session made, never another agent's work in the same checkout. With a message argument, makes one commit; with no argument, splits the session's work into the fewest self-contained commits and generates a short feat/fix/chore message for each. Use when the user says "commit", "commit this", "commit my changes", "commit just my/this session's changes", or invokes commit — especially when multiple agents share one working tree. |
| `resolve-conflicts` | Resolve git conflicts from any operation (merge, rebase, cherry-pick, stash, revert). Use when encountering conflicted files during git operations. |
| `review-logs` | Analyze Claude Code session transcripts for failure patterns and suggest fixes. Triggers "review logs", "session analysis", "failure patterns". |
| `squash-commits` | Squash unpushed commits into clean, higher-level feat/fix/chore commits that follow the project commit policy. Use when local history has too many small/WIP/fixup commits (common after superhuman or gsd runs), or the user says "squash commits", "squash my commits", "tidy history", "clean up commits", "combine commits before pushing". |
| `status` | Report the current coding-session status: summarize staged, unstaged, and untracked files; identify the last task and whether its work is present or committed; report code-review coverage; summarize active plans or review todos; list remaining session work; and recommend the next task. Use when the user invokes status or asks 'where are we?', 'what changed?', 'what is left?', or 'what should I do next?' about the current coding session. Do not use for service health or deployment status. |

### Docs & writing

| Skill | Description |
|---|---|
| `deslop` | Copy-edit text to strip AI/LLM writing tells ("slop") and make it read as human-written — overused words (delve, showcase, robust), significance-inflation phrases ("stands as a testament to", "plays a pivotal role"), scene-setting openers ("in today's fast-paced world"), hedging, em-dash overuse, rule-of-three, and "it's not X, it's Y" parallelism. Use when asked to "deslop", "de-slop", "remove AI tells", "make this sound less like AI/ChatGPT", "make this sound human", or copy-edit a draft (.md, .txt, prose, emails, docs) that reads as machine-generated. |
| `doc` | Assess documentation and run the right action: check changed code when the tree is dirty, otherwise review the whole repo for gaps, staleness, and quality. Explicit modes: --review, --update, --generate, or --session to capture durable knowledge from the current conversation or a transcript. Use for doc creation, freshness, quality, or saving occasional manual test procedures and results for future repetition; routine automated suite runs do not need test records. |
| `explain` | Generate project explanation docs in docs/explain/ covering architecture, flows, syntax, system APIs, infra, and testing, or explain a code diff, commit, branch, or PR directly in the conversation with --diff. |
| `huh` | Expand an explanation with the surrounding context needed to understand it. Use when the user invokes `huh`, asks to explain the previous reply in more detail, or supplies text to unpack. |
| `improve-agent-instructions` | Audit and improve the always-loaded agent instruction files (AGENTS.md, CLAUDE.md, GEMINI.md). Triggers "check/audit/update/improve/fix/revise CLAUDE.md or AGENTS.md", "project memory optimization", "trim my instruction file". Not for general docs. |
| `library-docs` | Generate and refresh a per-repo `library-use` reference — official docs, changelog links, pinned versions, and distilled correct-usage conventions for the repo's fast-moving / niche libraries. Use when the user says "library-docs", "doc links", "document the libraries we use", "generate/refresh library docs", "library conventions", or wants a per-repo doc-links reference the agent (and `review-library-use`) can consult. On re-run it version-checks every entry and updates it. |
| `read-docs` | Search internal project docs (docs/, README.md, CLAUDE.md, *.md) for patterns, conventions, architecture. Use proactively before features, in new code areas, or when debugging. |

### Environment & tools

| Skill | Description |
|---|---|
| `guide` | Walk the user through a multi-step task (e.g. cloud console / permission / dashboard setup) with a live step tracker that is re-printed at the bottom of every reply so they never scroll up. Use when the user asks to "guide me through", "walk me through", "give me step by step" instructions, "how do I set up ..." for a UI/console task, or invokes guide. Also use when, mid-guide, they say a step "isn't working", "the menu isn't there", or ask a clarifying question about a step. |
| `pdf` | Read, extract, merge, split, rotate, watermark, create, fill forms, encrypt/decrypt, or OCR PDF files. Use whenever a `.pdf` is mentioned or a PDF is requested. |
| `skill-creator` | Guide for creating or improving Claude skills. Triggers "create a skill", "build a skill", "new skill", "improve this skill", "skill for [use case]". |
| `temp` | Make temporary code changes for testing that can be easily undone. Use when user says "temp", "temporary change", "temporarily enable/disable/show/hide", or needs to force a UI state, bypass a guard, or flip a feature flag for local testing. Also handles "temp undo" to revert all temporary changes, and "temp list" to show them. |

## License

MIT

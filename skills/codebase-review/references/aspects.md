# Aspect catalog

The menu Phase 2 picks from. Each aspect lists the questions its reviewer answers. Copy the
relevant questions into the reviewer's brief and add project-specific ones, such as named files,
known suspicions or the user's own questions. Skip aspects the project does not have, and add
ones it does have (native layers, a CMS, hardware protocols).

Every aspect also answers the three standing questions:

- **Is it consistent?** Does the same concern use the same mechanism everywhere, or do two or
  three patterns coexist? Count each pattern with grep and name the canonical one.
- **Do the docs match?** Check the claims that ADRs, READMEs and the agent instruction files make
  about this area against the code.
- **What is tested?** Note the coverage of the area, and the untested paths that matter.

## Order

Run them in this order, because later aspects build on the docs that earlier ones wrote.

1. **Orientation:** system overview, docs inventory
2. **Foundations:** state, API, persistence, caching, startup, navigation, auth
3. **Cross-cutting:** errors/offline/monitoring, analytics, UI components, DI/contexts,
   layering, dependencies, tooling/CI, agent setup, tests, security, performance, a11y/i18n
4. **Features:** one deep dive per user-facing feature area
5. **Synthesis:** consistency sweep, consolidation, hotspots, architecture and roadmap

Within a tier, aspects whose scopes do not overlap can run in parallel.

## Orientation

**System overview.** What the systems and repos are, how they connect (protocols, auth,
shared contracts) and which external services each one calls. Include a mermaid diagram. Name
each repo's stack, entry points and build/run commands.

**Docs inventory.** Every doc in the repos: a one-paragraph summary for each, or two paragraphs
for long ones. For ADRs, a list with each one checked against the code, with anything no longer
true highlighted. Also list what is missing: the areas a newcomer needs that nothing documents.

## Foundations

**State.** What state is kept where: server cache, global stores, context, component state,
persistent storage. Where each piece comes from and who writes it. Is there a single source of
truth for each piece, and is server data kept separate from local-only data? What do the
transform/normalisation layers do?

**API and network.** Which APIs and endpoints are called, from where, and when. List recurring
and background requests, and the request order on a cold start. Cover client setup,
interceptors, auth headers and retries, and whether error handling is centralised.

**Persistence.** What is stored on device or disk, in which store and with what keys. Cover
schema and versioning, migrations, what survives logout or reinstall, and secrets in storage.

**Caching.** Cache lifetimes per data type, prefetching before the user looks at anything,
invalidation, and query-key conventions. Does any endpoint have two caches, or a key that misses
a dimension (locale, market, user)?

**Startup and resume.** The native and runtime init order, module-scope side effects, the
provider tree, what each step awaits and what runs in parallel, with the critical path marked
on a timeline. Cover the logged-in and logged-out cold start, resume from background, and every
listener on app-state, focus or network, with counts. Assess whether it is optimised (serial
awaits, eager work, duplicate fetches) and orderly (single owner, implicit ordering, races,
timeouts).

**Navigation.** Navigator structure, gating (forced update, maintenance, onboarding, auth),
deep links and universal links on each platform, and guards that some call sites bypass.

**Auth and session.** Login flows, token storage and refresh, logout and account switch, and
what state survives an exit. Count the code paths that end a session. Note server-side
counterparts where a sibling repo holds them.

## Cross-cutting

**Errors, loading, offline, monitoring.** The error taxonomy, user-facing error and loading
states, offline detection and its writers, retry behaviour, crash and error reporting (what is
sent, PII in payloads, sampling, environment tags), and logging.

**Analytics.** Every mechanism: raw calls, declarative props, auto-tracking. Cover consent,
queueing before consent, duplicate and dead events, naming consistency, and user identity.

**UI components and styling.** An inventory: what exists, use counts with the area each is used
in, the styling systems in use and which one is current, components only used in stories or
not at all, and dead or out-of-date components.

**DI and contexts.** What contexts or providers exist, what each one carries, the provider
order, re-render cost, and contexts used as global mutable state.

**Layering and dependency graph.** Who imports whom: are layers respected (screens, then
components, then logic, then services)? Find cycles and give a diagram. Check whether external
dependencies sit behind facades or are imported everywhere, and count them per package.

**External dependencies.** Each direct runtime dependency: version against latest, maintenance
health, whether it has been superseded, and whether anything records why it is pinned old. Use
`evaluate-tech` only for a replacement decision.

**Tooling and CI.** Static analysis (lint, types, dead-code tools and their config), formatting,
git hooks, CI pipelines, release and signing, secrets in CI, and whether each check actually
checks what it claims to.

**Agent setup.** Agent instruction files, skills, rules and hooks in the repo. Are they up to
date, how often do they change, and do their claims match the code?

**Tests.** Test types and counts, what each layer covers, the patterns in use and whether they
are consistent, query priorities (labels and roles over test ids), weak tests that assert
nothing, mocks that hide behaviour, and the gaps that matter. Run the suite and coverage
yourself. `test --review` supplies the quality lens.

**Security.** Secrets and tokens in code, logs and crash payloads; storage of credentials;
transport; WebView and deep-link attack surface; update signing; and dependency advisories.
`review-security` supplies the lens.

**Performance.** Bundle size and eager imports, render hot paths, list virtualisation, memory,
and N+1 request patterns. `review-perf` supplies the lens.

**Accessibility and i18n.** Labels and roles, focus, dynamic type, hard-coded strings,
pluralisation, and RTL and locale formatting.

## Features

One deep dive per user-facing feature area, such as shop, onboarding, playback or settings.
Split a large area into slices with disjoint scopes, one reviewer each, sharing a brief file.
Each deep dive covers:

- the user flows end to end, with the screens and the calls behind each step
- the logic check: business rules, edge cases, empty, error and loading states, and market or
  locale differences that leak into screens
- the data shapes and how they are normalised
- tests for the flows
- bugs with a concrete repro scenario

## Synthesis

**Consistency sweep.** `review-consistency --all`, area by area, over the patterns the earlier
aspects found in competition: two error-handling styles, three styling systems, or mixed query
key formats. Pick the canonical pattern for each and list its outliers.

**Consolidation.** Run two passes in parallel:

- **Docs consistency:** do the review docs contradict each other, and are cross-links and line
  references still valid at the current HEAD?
- **Findings staleness:** re-check each open finding at the current HEAD, and merge duplicates
  found by different aspects.

**Hotspots.** Rank files by git churn × size × bug-fix commits. Where are the risky, frequently
changed files, and do the findings cluster there?

**Architecture and roadmap.** Zoom out. What is the architecture actually, compared with what the
docs say? Name the cross-cutting themes behind clusters of findings (for example, "five ways to
end a session"). Produce a ranked roadmap, where each item lists its findings, its cost (days or
weeks) and what it unblocks. Use `review-architecture` as the lens, and check the roadmap with
`second-opinion`.

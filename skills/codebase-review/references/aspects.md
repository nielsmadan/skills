# Aspect catalog

The menu Phase 2 picks from, grouped by project type. Each aspect lists the questions its
reviewer answers. Copy them into the reviewer's brief and add project-specific ones, such as
named files, known suspicions or the user's own questions.

## Picking aspects

1. **Tag the types** during recon, per repo or package, with the signals that decided each tag:
   `Types: app/ → mobile app; api/ → backend; packages/ui → library: UI component — signals: …`.
   A project can carry several tags. A docs site with an interactive search app is
   `static site` + `web frontend`.
2. **Take Core plus every section that matches a tag.** Sections shared by several types
   (Client apps, Native apps, Web delivery) apply when any of their types is tagged.
3. **Deduplicate.** One concern is one aspect per repo, even when two sections name it (caching
   in a backend and in its web client are two repos, so two aspects; caching named twice for one
   repo is one).
4. **Account for every aspect of the matched sections.** Each one is either planned or listed
   under Skipped with a one-line reason ("no network layer: the library does no I/O").
5. **Add what the catalog lacks:** a CMS, a hardware protocol, a native bridge, a plugin
   marketplace, a domain rule engine.

| Type | Signals | Feature unit for deep dives |
|---|---|---|
| Mobile app | `ios/`, `android/`, app targets, store metadata | feature areas and their screens |
| Desktop app | Electron, Tauri, a macOS or Windows app target, installers | feature areas and their windows |
| Web frontend | an SPA or SSR app with client state and API calls | pages and user flows |
| Static site | generator config (Hugo, Jekyll, Astro, Docusaurus), mostly content files | page types and content sections |
| CLI | a `bin` entry, an argument parser, no long-running server | commands |
| Backend | a server entry, routes, migrations, a Dockerfile or deploy config | endpoints and domains |
| Library | a published package manifest, public exports, no app entry | modules and capabilities |

Library subtypes: UI component, SDK or API client, utility or core, framework or plugin host.

## Standing questions

Every aspect also answers these three:

- **Is it consistent?** Does the same concern use the same mechanism everywhere, or do two or
  three patterns coexist? Count each pattern with grep and name the canonical one.
- **Do the docs match?** Check the claims that ADRs, READMEs and the agent instruction files make
  about this area against the code.
- **What is tested?** Note the coverage of the area, and the untested paths that matter.

## Order

Run them in this order, because later aspects build on the docs that earlier ones wrote.

1. **Orientation:** system overview, docs inventory
2. **Foundations:** the aspects marked **(F)** in the matched sections, the ones other aspects
   lean on (state, data model, API contract, public API, command map, startup)
3. **Cross-cutting:** everything else from Core and the matched sections
4. **Features:** one deep dive per feature unit (see the table above)
5. **Synthesis:** consistency sweep, consolidation, hotspots, architecture and roadmap

Within a tier, aspects whose scopes do not overlap can run in parallel.

## Core (every project)

**System overview.** What the systems and repos are, how they connect (protocols, auth,
shared contracts) and which external services each one calls. Include a mermaid diagram. Name
each repo's type tags, stack, entry points and build/run commands.

**Docs inventory.** Every doc in the repos: a one-paragraph summary for each, or two paragraphs
for long ones. For ADRs, a list with each one checked against the code, with anything no longer
true highlighted. Also list what is missing: the areas a newcomer needs that nothing documents.

**Architecture and layering.** Who imports whom: are the layers respected? Find cycles and give
a diagram. Check whether external dependencies sit behind facades or are imported everywhere,
and count them per package. Name the module boundaries and whether the code honours them.

**Error handling and logging.** The error taxonomy, where errors are caught, translated or
swallowed, what reaches the user or caller, and what gets logged at which level. Look for
secrets and personal data in logs.

**Config and environment.** Every config source (files, env vars, flags, remote config, build
time vs run time), the precedence between them, defaults, validation at startup, and config
that differs per environment without anything recording why.

**External dependencies.** Each direct runtime dependency: version against latest, maintenance
health, whether it has been superseded, and whether anything records why it is pinned old. Use
`evaluate-tech` only for a replacement decision.

**Tooling and CI.** Static analysis (lint, types, dead-code tools and their config), formatting,
git hooks, CI pipelines, secrets in CI, and whether each check actually checks what it claims to.

**Build and release.** How a release is cut: versioning, changelog, signing, artifacts, who can
publish, and the manual steps nobody wrote down. Is the build reproducible?

**Tests.** Test types and counts, what each layer covers, the patterns in use and whether they
are consistent, weak tests that assert nothing, mocks that hide behaviour, and the gaps that
matter. For UI code, query priorities (labels and roles over test ids). Run the suite and
coverage yourself. `test --review` supplies the quality lens.

**Security.** Secrets and tokens in code, logs and crash payloads; storage of credentials;
transport; input that reaches a shell, a query or a file path; and dependency advisories.
`review-security` supplies the lens. The type sections add their own attack surface.

**Performance.** The hot paths for this type of project (render, request, command, call),
algorithmic complexity, memory, and repeated I/O. `review-perf` supplies the lens.

**Agent setup.** Agent instruction files, skills, rules and hooks in the repo. Are they up to
date, how often do they change, and do their claims match the code?

## Client apps (mobile, desktop, web frontend)

**State (F).** What state is kept where: server cache, global stores, context, component state,
persistent storage. Where each piece comes from and who writes it. Is there a single source of
truth for each piece, and is server data kept separate from local-only data? What do the
transform and normalisation layers do?

**Network client and data caching (F).** Which APIs and endpoints are called, from where, and
when. List recurring and background requests, and the request order on first load. Cover client
setup, interceptors, auth headers, retries, and whether error handling is centralised. Then the
cache: lifetimes per data type, prefetching, invalidation, key conventions. Does any endpoint
have two caches, or a key that misses a dimension (locale, market, user)?

**Auth and session (F).** Login flows, token storage and refresh, logout and account switch, and
what state survives an exit. Count the code paths that end a session. Note server-side
counterparts where a sibling repo holds them.

**Navigation and deep links.** Navigator or router structure, gating (forced update,
maintenance, onboarding, auth), deep links and universal links, and guards that some call sites
bypass.

**UI components and design system.** An inventory: what exists, use counts with the area each is
used in, the styling systems in use and which one is current, design tokens, components only
used in stories or not at all, and dead or out-of-date components.

**DI and contexts.** What contexts, providers or injected services exist, what each one carries,
the provider order, re-render cost, and contexts used as global mutable state.

**Error, loading, empty and offline states.** What the user sees when a request fails, is slow,
returns nothing, or the device is offline. Who detects offline, retry behaviour, and screens
with no error state at all.

**Crash and error monitoring.** What is sent, personal data in payloads, sampling, environment
and release tags, source maps or symbol upload, and errors that never reach the monitor.

**Analytics and consent.** Every mechanism: raw calls, declarative props, auto-tracking. Cover
consent, queueing before consent, duplicate and dead events, naming consistency, and user
identity.

**Accessibility and i18n.** Labels and roles, focus order, dynamic type or zoom, contrast,
hard-coded strings, pluralisation, RTL, and locale formatting of dates, numbers and currency.

## Native apps (mobile, desktop)

**Persistence and offline (F).** What is stored on device or disk, in which store and with what
keys. Cover schema and versioning, migrations, what survives logout, reinstall or an update,
secrets in storage, and what works offline.

**Startup and lifecycle (F).** The native and runtime init order, module-scope side effects, the
provider tree, what each step awaits and what runs in parallel, with the critical path marked
on a timeline. Cover the logged-in and logged-out cold start, resume from background, and every
listener on app state, focus or network, with counts. Assess whether it is optimised (serial
awaits, eager work, duplicate fetches) and orderly (single owner, implicit ordering, races,
timeouts).

**App updates.** Forced and soft updates, over-the-air updates, auto-update, and how an old
client behaves against a newer backend.

**Permissions and notifications.** Which OS permissions are requested, when and with what
explanation, what happens on denial, and local notifications.

### Mobile only

- **Push and background execution:** token registration, payload handling in each app state,
  background fetch and tasks, and what the OS kills.
- **Store policies:** privacy manifests, data-safety declarations, review guidelines the app
  risks, and in-app purchase rules.
- **Device and OS fragmentation:** minimum OS versions, screen sizes, notches and safe areas,
  low-end devices, and OS-version branches in the code.
- **Native modules and bridges:** custom native code, its parity across iOS and Android, and
  who maintains it.

### Desktop only

- **Windows, menus and shortcuts:** window lifecycle and state restore, menu structure,
  keyboard shortcuts and their conflicts with the OS.
- **OS integration:** tray or menu bar, file associations, URL schemes, drag and drop, the
  clipboard, and launch at login.
- **Signing, notarisation and sandboxing:** certificates, entitlements, hardened runtime, and
  what breaks when the sandbox is on.
- **Process model and IPC:** main and renderer or helper processes, what crosses each
  boundary, and whether that channel is validated.
- **Platform parity:** behaviour that differs between macOS, Windows and Linux, and paths,
  line endings or shells assumed to be one platform's.

## Web delivery (web frontend, static site)

**URLs, routes and redirects.** The URL scheme, its stability, redirect maps, canonical URLs,
404 handling, and broken internal and external links.

**SEO and metadata.** Titles and descriptions, sitemaps, robots rules, structured data, social
preview images, and pages that cannot be indexed by accident.

**Web performance.** Core Web Vitals, bundle size and code splitting, images and fonts,
third-party scripts, and the waterfall on first load. Measure with Lighthouse where it can run.

**Browser support.** The supported browsers, polyfills, progressive enhancement, and what
happens with JavaScript off where that matters.

**Hosting, CDN and caching headers.** Where it is hosted, cache headers per asset type, cache
busting, preview deploys, and environment differences between preview and production.

**Web security.** CSP and the other security headers, XSS sinks, CORS, CSRF, cookies'
attributes, and secrets or internal URLs shipped in the client bundle.

## Web frontend only

**Rendering strategy (F).** Server, static or client rendering per route, hydration,
streaming, data fetching on the server versus the client, and mismatches between them.

**Forms and validation.** Client and server validation and whether they agree, error display,
double submits, and unsaved-change handling.

## Static site only

**Content model and authoring (F).** Content types and their front-matter schema, the CMS if
there is one, previews, who publishes and how, and content that breaks the schema.

**Templates and layouts.** Consistency between page types, duplicated markup, and shared
components or partials.

**Build pipeline.** Generator config, build time, generated assets, plugins, and whether a clean
checkout builds the same site.

**Embeds, forms and third parties.** Form handlers, comment systems, video and map embeds, their
privacy cost and consent, and their weight.

Static sites also take **Analytics and consent** and **Accessibility and i18n** from Client
apps, with i18n covering how translated content stays in sync.

## CLI

**Command map (F).** Every command and subcommand, what each does, overlaps between them, and
commands that should be one or be split. `release-review` is the deeper pass over every
parameter before a release.

**Flags, arguments and defaults (F).** Naming consistency across commands, short and long
forms, defaults that surprise, required arguments, and flags that interact.

**Config files, env vars and precedence.** Where config is read from, the precedence between
flags, env vars and files, and whether `--help` and the docs state it.

**Output contract.** Human and machine output (`--json`), stdout versus stderr, exit codes,
colour and TTY detection, and output that scripts depend on.

**Error messages and help.** Whether each error says what went wrong and what to do, `--help`
accuracy, and examples in the help text.

**Interactive versus scripted use.** Prompts, confirmations, `--yes`, behaviour without a TTY,
and progress output in CI logs.

**Filesystem and side-effect safety.** Dry runs, `--force`, idempotency, atomic writes,
partial failure, and anything destructive without a confirmation.

**Install and upgrade.** Distribution channels, upgrade path, migration of old config or state,
and shell completion.

**Cross-platform behaviour.** Paths, shells, line endings, and platform-specific branches.

**Startup time.** Time to first output, eager imports, and work done for every command that
only some commands need.

**Telemetry.** What is collected, opt-in or opt-out, and how to turn it off.

## Backend

**API contracts and versioning (F).** Endpoints or RPCs, their schemas, versioning, breaking
changes, and whether the published spec matches the handlers.

**Data model and migrations (F).** Schema, constraints, indexes, migration history, migrations
that lock or rewrite large tables, and whether rollback is possible.

**Authentication and authorisation (F).** How callers are identified, where permissions are
checked, and endpoints that skip the check.

**Transactions and consistency.** Transaction boundaries, race conditions, idempotency of
writes, and what happens on partial failure.

**Jobs, queues and schedules.** Background jobs, retries, dead letters, duplicate delivery,
scheduled tasks, and their monitoring.

**External integrations.** Each third-party call: timeouts, retries, circuit breaking,
idempotency keys, and webhooks with their signature checks.

**Caching.** What is cached, where, the invalidation rules, and stale data a user can see.

**Observability.** Logs, metrics, traces, health checks, alerts, and whether an incident could
be diagnosed from them.

**Deploy and runtime.** Containers, scaling, graceful shutdown, migrations on deploy, resource
limits, and environment parity.

**Rate limiting and abuse.** Limits per caller, expensive endpoints, enumeration, and
unbounded queries.

**Multi-tenancy and isolation.** How tenants are separated, queries missing a tenant filter, and
noisy neighbours.

**Data privacy and retention.** Personal data stored, retention and deletion, exports, and data
copied into logs or analytics.

## Library (every subtype)

**Public API surface (F).** Everything exported, naming consistency, what is public by accident,
and parameters or overloads that should not exist. `review-interfaces` supplies the lens.

**Error model (F).** What consumers see when things fail: exceptions, result types or error
codes, whether it is consistent, and whether errors carry enough to act on.

**Concurrency contract (F).** Thread safety, async boundaries, cancellation, and what the docs
promise about them.

**Encapsulation.** Internals that leak through types, mutable shared state, and global side
effects on import.

**Semver, deprecation and changelog.** Whether past releases followed semver, how deprecations
are announced and removed, and whether the changelog matches the diffs.

**Platform support matrix.** Supported language, runtime and OS versions, what CI actually
tests, and conditional code paths per platform.

**Packaging and distribution.** Manifest correctness, what the published artifact contains,
entry points, module formats, and size.

**Dependency footprint.** What consumers inherit, version ranges that are too tight or too
loose, and optional dependencies.

**Consumer docs and examples.** API reference coverage, getting-started, examples that still
compile, and migration guides.

**Testability for consumers.** Whether consumers can mock, fake or inject it, and test helpers
the library ships.

### UI component library

- **Theming and customisation:** tokens, overrides, and what consumers cannot change without
  forking.
- **Component accessibility:** roles, labels, keyboard and focus handling built into each
  component.
- **Behaviour inside hosts:** layout in different containers, sizing, and conflicts with the
  host's styles or event handling.
- **Controlled and uncontrolled state:** which components support which, and state that gets out
  of sync with the host.
- **Previews and snapshots:** stories or previews per component and state, and visual
  regression tests.

### SDK or API client

- **Fidelity to the wire contract:** models against the server spec, missing or extra fields,
  and unknown enum values.
- **Auth and tokens:** credential handling, refresh, and secrets that end up in logs.
- **Retries, timeouts and pagination:** defaults, configurability, and idempotency of retried
  calls.
- **Generated code:** what is generated, from which spec, and hand edits that a regeneration
  would lose.
- **Server compatibility:** behaviour against older and newer server versions.

### Utility or core

- **Correctness at the edges:** empty, huge, Unicode and boundary inputs, and property-based
  tests.
- **Complexity:** the algorithmic cost of each public function, and whether it is documented.
- **Determinism:** hidden dependence on time, locale, randomness or environment.

### Framework or plugin host

- **Extension points and lifecycle:** hooks, their order, and the guarantees around them.
- **Plugin API stability:** what plugins depend on, and how breaking changes reach them.
- **Plugin isolation:** what a faulty or hostile plugin can break.
- **Scaffolding:** templates and generators, and whether their output passes the project's own
  checks.

## Features

One deep dive per feature unit from the type table: a feature area, a page or flow, a command,
an endpoint group, or a library module. Split a large unit into slices with disjoint scopes,
one reviewer each, sharing a brief file. Each deep dive covers:

- the flows end to end, from the user's or caller's first action to the result, with the code
  behind each step
- the logic check: business rules, edge cases, empty, error and loading states, and market or
  locale differences that leak through
- the data shapes and how they are transformed
- tests for the flows
- bugs with a concrete repro scenario

## Synthesis

**Consistency sweep.** `review-consistency --all`, area by area, over the patterns the earlier
aspects found in competition: two error-handling styles, three styling systems, or mixed key
formats. Pick the canonical pattern for each and list its outliers.

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

# Evaluation Criteria

Core criteria apply to every candidate. Then add exactly one profile block (Library / Tool / Service).

## Core (always)

### C1. Maintenance health — GATE

The one criterion that is never optional. Gather:

| Signal | How |
|--------|-----|
| Last release date | `gh release list -R o/r -L 5`, or registry (below) |
| Commit velocity, 52 weeks | `gh api repos/o/r/stats/participation` — array of weekly commit counts, oldest first |
| **Commit substance** | **Mandatory follow-up to velocity — a raw count is not a health signal.** `gh api --paginate --slurp "repos/o/r/commits?since=YYYY-MM-DD&per_page=100" \| jq 'add \| group_by(.author.login) \| map({(.[0].author.login // "unknown"): length}) \| add'` to get the authorship split, then read the titles. Note the exact form: `--paginate` alone caps at 30 results, and `--jq` runs *per page* so it silently returns per-page counts — use `--slurp` and pipe to a separate `jq` (gh rejects `--slurp` combined with `--jq`). Separate bot dependency bumps (`renovate[bot]`, `dependabot[bot]`) and CI/toolchain churn from real feature and bugfix work. Then narrow to the code that matters: `gh api "repos/o/r/commits?path=<src dir>&since=..."`. A repo whose year is 90% Renovate is in maintenance-only mode however busy the graph looks. |
| Archived / deprecated | `gh repo view o/r --json isArchived,archivedAt`; npm `deprecated` field; PyPI `Development Status ::` classifier |
| Bus factor | `gh api repos/o/r/contributors?per_page=20` — how many humans committed in the last year, not all-time |
| Issue responsiveness | `gh issue list -R o/r --state open -L 20 --json createdAt,comments` — are recent issues answered by a maintainer, or unanswered for months? Also check whether *maintainers* have commented at all recently: `gh api --paginate --slurp "repos/o/r/issues/comments?since=YYYY-MM-DD&per_page=100" \| jq 'add \| map(select(.author_association \| IN("OWNER","MEMBER","COLLABORATOR"))) \| length'` (same `--slurp` caveat as above). Zero over 12+ months means nobody is home, whatever the release cadence says. |
| Open-issue trend | Open count alone is meaningless for a big project. Median age of the oldest open issues is the signal. Pair it with PR throughput — `gh pr list -R o/r --state open \| wc -l` vs. merged in the last year. A large open-PR backlog with few merges means community fixes do not land, so budget for maintaining your own patches. |
| **Next-major trajectory** | `npm view <pkg> dist-tags` (or `gh release list --include-prereleases`) for `next`/`beta`/`alpha`; `gh api repos/o/r/milestones?state=open`; `gh api repos/o/r/branches --jq '[.[].name]'` for a `v6`/`next`/`2.x` branch. **Interpret, don't just retrieve** — a pre-release tag *below* `latest` is an orphaned beta, not active work. |
| Successor | Search "`{name}` deprecated in favor of", README banners, pinned issues |

**Reading next-major trajectory.** It cuts both ways, so state which case applies:

- **Rescues a stale-looking current release** — quiet `main` because the work is on the v-next branch. Check that the branch has recent commits before crediting it.
- **Condemns it** — maintainers triaging bug reports into "v-next scope" while the shipping version gets nothing means the version you would install is in maintenance-only mode.
- **Is a cost either way** — a v-next that lands is a migration you are signing up for. If it changes module format, minimum runtime, or the core API, price that in C4.
- **Means nothing** — a v-next "planned" for years with no branch, no milestone, and no pre-release is a decay signal, not a roadmap.

**Verdict rules:**

- **Unmaintained** — no release in 18+ months AND no commits in 12+ months. Do not recommend without an explicit, argued exception.
- **The "done" exception** — a small, complete-scope package (single pure function, stable format parser, finished spec implementation) can be legitimately finished rather than abandoned. Claiming this requires *all* of: tiny surface area, no unaddressed security advisories, no open issues describing breakage on current runtimes. State it as an explicit argument, never as an assumption.
- **At risk** — single maintainer with no commits in 6 months; or a maintainer who has publicly asked for a successor; or last release predates a major breaking change in its host platform; or **the year's commits are overwhelmingly bot bumps and CI churn with no substantive change to the code you depend on**; or no maintainer has answered an issue in 12+ months.
- **Healthy** — releases within ~6 months, ongoing **substantive** commits (verified against the commit-substance row, not just the velocity count), and maintainer-answered issues.

Report the *dates*, not adjectives. "Last release 2024-03-11 (28 months ago)" beats "somewhat stale".

A recent release is not by itself evidence of health. Cutting a tag is cheap; the questions that decide the verdict are whether anyone is *changing the code*, whether anyone *answers users*, and whether fixes *land*. Weigh those above cadence.

### C2. Adoption and trajectory

Direction matters more than magnitude. A package at 40k weekly downloads climbing beats one at 400k halving.

- npm: `curl -s "https://api.npmjs.org/downloads/range/last-year/{pkg}"` — compare first vs. last month
- PyPI: pypistats.org · pub.dev: package page "likes/popularity" · crates.io: `downloads` + `recent_downloads`
- Production dependents: npm "Dependents" tab, `gh search code`, GitHub "Used by"

**Never cite GitHub star counts as evidence of quality or adoption.** Stars are trivially bought. See `../../research-tech/references/fake-stars.md` for the full checklist; quick tell is >10k stars with a fork-to-star ratio under ~5%.

### C3. Fit

Does it do the job as framed in Step 1 — not "is it good". Note what's missing, and whether missing pieces have escape hatches (plugin API, raw access, ejectable) or are hard walls.

### C4. Integration cost

Estimate in files-touched and hours, and **name every soft constraint it asks you to change** (see SKILL.md Step 2). This is where soft constraints belong — they are a cost line, never an elimination.

### C5. License and ownership

- License (SPDX), and compatibility with the project's distribution model
- **Relicense risk** — has it changed license before? Single-vendor-owned with a CLA, VC-funded, no foundation governance? That is the pattern behind the Redis/Terraform/Elasticsearch/Sentry relicenses. Vendor-owned + CLA + permissive-today is a risk to state, not a clean bill of health.
- Foundation-governed or multi-org maintained is materially safer than single-vendor.

### C6. Security and supply chain

- Known advisories: `npm audit`, `osv.dev`, GitHub Security Advisories, `gh api repos/o/r/security-advisories`
- Transitive dependency count — every one is a takeover surface. `npm view {pkg} dependencies`, or install into a scratch dir and count.
- Maintainer count and account age — a single-maintainer package with 10M downloads is a supply-chain target
- Release provenance/signing (npm provenance attestation, sigstore)

### C7. Exit cost

How hard to remove in 18 months. Is it hideable behind an interface, or does it colonize call sites / own the data format / define the types that flow through the app? A mediocre candidate with a cheap exit often beats a better one that is load-bearing everywhere.

### C8. Docs and DX

Completeness, accuracy against current version, working examples, error-message quality, TypeScript/type-hint quality, test/mocking story.

---

## Profile: Library / package

Add to core:

- **Size** — bundlephobia.com (min+gzip), tree-shakeability (ESM, `sideEffects: false`). Matters for web/mobile, mostly irrelevant server-side — say which applies.
- **Module format** — ESM/CJS/dual. ESM-only in a CJS codebase is a real migration, not a footnote.
- **Types** — bundled vs. DefinitelyTyped vs. none. Bundled and generated-from-source is best; a stale `@types/*` is a recurring tax.
- **Peer-dependency strictness** — does it pin the host framework tightly? That predicts how badly it blocks *your* upgrades.
- **Runtime/platform support** — Node versions, browsers, RN/Hermes, edge/workers, SSR.
- **Transitive weight** — total install size and dep count.

## Profile: Tool / CLI / dev software

Add to core:

- **Install and update path** — package manager availability (brew/mise/npm/cargo), single binary vs. runtime required, self-update story
- **Platform coverage** — macOS arm64, Linux, Windows/WSL; CI runner availability
- **CI integration** — official action/image, exit codes, machine-readable output (JSON), speed on a real repo
- **Config surface and migration** — can it import config from the incumbent? Is config stable across majors?
- **Editor/agent integration** — LSP, editor plugins, MCP server if relevant
- **Upgrade pain history** — read the last 2 major-version changelogs. Frequency and severity of breaking changes predicts your future.

## Profile: Hosted service / SaaS / API

Add to core:

- **Pricing at your scale and 10x** — compute both. Find the cliff (per-seat, per-event, egress, overage rate). Free-tier limits and what happens at the ceiling.
- **Data export completeness** — the real exit cost. Can you get *everything* out, via API, in a usable format? "There is an export button" is not the same as "the export includes historical events".
- **SLA and incident history** — published SLA with credits vs. marketing uptime. Read the status-page history, not the headline number.
- **Data residency and compliance** — regions, GDPR/SOC2/HIPAA as actually required by the project
- **Vendor durability** — funding stage, acquisition history, whether the product is the company's core business or a side bet. A side bet gets sunset.
- **Auth and access model** — SSO/SAML pricing tier, API token scoping, audit logs
- **Rate limits and quotas** — the ones that bite in production, not the marketing numbers
- **Self-host escape hatch** — does an open-source or on-prem version exist as a fallback?

---

## Registry quick reference

| Ecosystem | Last publish + metadata |
|-----------|------------------------|
| npm | `npm view {pkg} time.modified version deprecated maintainers license` |
| PyPI | `curl -s https://pypi.org/pypi/{pkg}/json` — `info.version`, `urls[0].upload_time`, `info.license`, `info.yanked` |
| pub.dev | `curl -s https://pub.dev/api/packages/{pkg}` — `latest.version`, `latest.published` |
| crates.io | `curl -s -H "User-Agent: eval" https://crates.io/api/v1/crates/{name}` — `crate.updated_at`, `crate.downloads`, `crate.recent_downloads` |
| Go | `curl -s https://proxy.golang.org/{module}/@latest` |

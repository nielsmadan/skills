# Per-Candidate Agent Prompt

Dispatch one `general-purpose` sub-agent per candidate, **all in a single message** so they run in parallel. Every agent gets the identical template so results come back comparable.

Substitute: `{CANDIDATE}` · `{JOB}` (the Step 1 job statement) · `{PROFILE}` (Library / Tool / Service) · `{HARD}` (hard constraints) · `{SOFT}` (soft constraints) · `{TODAY}` · `{CRITERIA_PATH}` (absolute path to this skill's `references/criteria.md` — resolve it, since the skill root differs per harness: `~/.claude/skills/…` for Claude Code, `~/.agents/skills/…` elsewhere).

---

```
Evaluate ONE candidate for a technology decision. You are one of several agents each
evaluating a different candidate against an identical rubric — do not compare against
other candidates, do not recommend. Report evidence.

CANDIDATE: {CANDIDATE}
JOB TO BE DONE: {JOB}
PROFILE: {PROFILE}
HARD CONSTRAINTS (must hold): {HARD}
SOFT CONSTRAINTS (current codebase choices — these are COSTS to quantify, never
disqualifiers): {SOFT}
TODAY'S DATE: {TODAY}

Read {CRITERIA_PATH}. Evaluate core criteria C1-C8 plus the {PROFILE} profile block.
Follow its commands and registry reference.

RULES
- C1 (maintenance health) is mandatory and comes first. Report absolute dates AND months
  elapsed relative to {TODAY}. If you cannot establish a last-release date, say so —
  never assume it is current.
- Cite a URL or the exact command output for every factual claim. No claim from memory:
  your training data is stale, which is exactly the failure mode this rubric exists to
  prevent.
- Never cite a GitHub star count as evidence of quality or adoption.
- If the candidate violates a SOFT constraint, price the change in files-touched and
  hours. Do not mark it as a failure.
- If the candidate violates a HARD constraint, STOP. Return ONLY the one-line summary, the
  hard-constraint verdict with its evidence, and Sources. Do NOT fill in C1-C8 or the
  profile block — the candidate is already eliminated and that work is discarded unread. A
  four-line report is the correct output here, not a failure to be thorough. The RETURN
  structure below is the PASS shape; this rule overrides it.
- Distinguish "verified" from "could not determine". Unknown is a legitimate finding and
  more useful than a confident guess.
- Escalate evidence in cost order, and stop as soon as the question is settled: registry
  and repo metadata → source and docs → a small local run → a large generated fixture or
  benchmark. Reach the expensive tier only when the cheaper ones are inconclusive, or when
  you have a specific failure hypothesis worth proving (a default that is unsafe for this
  job, a limit that might not hold at scale). If reading the source already answers it,
  say so and skip the benchmark — a confirmatory benchmark of a settled fact is waste.

Fetching: WebFetch for plain HTML and github.com. `mcp__jina__read_url` for JS-heavy pages
(modern docs, SPAs) and for Reddit/StackOverflow, which block WebFetch.

RETURN exactly this structure, nothing else (if the hard-constraint check FAILS, return only
the first three lines plus Sources — see the STOP rule above):

## {CANDIDATE}
**One-line:** what it is and who makes it
**Hard-constraint check:** PASS / FAIL — which one, why

### C1 Maintenance — HEALTHY | AT RISK | UNMAINTAINED | UNKNOWN
- Last release: YYYY-MM-DD (N months ago), version X
- Commits last 12mo: N (source: participation stats)
- Commit substance: N bot / N human; what the human commits actually changed, and whether
  any touched the code path this job depends on
- Contributors active last 12mo: N
- Archived/deprecated: yes/no + evidence
- Issue responsiveness: (are recent issues maintainer-answered? oldest-open median age;
  maintainer comments in the last 12mo; open-PR backlog vs. merged)
- Next-major trajectory: pre-release dist-tags / open milestones / v-next branch — and
  which of criteria.md's four readings applies (rescues / condemns / costs / means nothing)
- Successor named: yes/no
- Verdict rationale, 1-2 sentences

### C2 Adoption — direction + numbers with dates
### C3 Fit — covers / missing / escape hatches for the missing
### C4 Integration cost — estimate + each soft constraint it asks us to change, priced
### C5 License and ownership — SPDX, governance, relicense risk
### C6 Security and supply chain — advisories, transitive dep count, maintainer count
### C7 Exit cost — LOW | MEDIUM | HIGH + why
### C8 Docs and DX
### Profile-specific ({PROFILE})
(the profile block's criteria)

### Killer facts
Up to 3 findings that would most change a decision-maker's mind, either direction.

### Unknowns
What you could not verify, and what you tried.

### Sources
- URL — what it established — date
```

# Scoring, Triage & Output Format

Load after the review agents have returned (Steps 4, 4.5 and 5).

## Step 4: Independent Confidence Scoring

Collect all issues from the review agents. Then launch **parallel scorer agents** — one per issue (or batch small groups if there are many). On a harness where each sub-agent is a full child session rather than a cheap in-process one, batch by default: ~5 issues per scorer, and never more than ~10 scorers total. Each scorer receives:
- The issue description and location
- The relevant code context (read the file around the reported lines)
- The CLAUDE.md guidelines

Each scorer independently assigns a confidence score 0-100:
- **0**: False positive, not a real issue
- **25**: Might be real but unlikely
- **50**: Plausible but minor or uncertain
- **75**: Likely real and worth noting
- **100**: Certain, clear problem

The scorer should NOT know which agent found the issue. It evaluates purely based on the code and the claim.

**Filter**: Only issues scoring >= 80 pass through to the output.

Each scorer also returns the Step 4.5 triage fields in the *same* response — see below. Do not dispatch a second round of agents for triage.

## Step 4.5: Likelihood & Blast-Radius Triage

Confidence answers "is this claim true?". It does not answer "will this ever happen?" — an issue can be 95/100 real and still require a once-in-the-universe alignment of conditions. This step adds that second axis so improbable findings stop being presented as work to do.

**Same dispatch, no extra agents.** Extend each Step 4 scorer's prompt to also return a `likelihood` bucket and a `blast_radius` rating alongside its confidence score. Discard the triage fields for any issue that fails the >= 80 confidence gate. Cost stays at one agent per issue.

### Likelihood buckets

The scorer must state *how* it checked reachability — trace the callers with Grep/Read and name the specific upstream guard, validation, or type constraint it found.

| Bucket | Definition |
|---|---|
| `routine` | Occurs on a normal request or common input; the path is already exercised. |
| `plausible` | Needs an ordinary but specific condition that *will* occur in production eventually — load, timeout, retry-after-failure, restart, malformed-but-realistic input. |
| `rare` | Needs an unusual combination — crafted or adversarial input, a narrow race window, or an invariant elsewhere already broken. |
| `theoretical` | Provably excluded given the actual call sites and validation. **The scorer MUST cite the exact `file:line` of the guard, type, or validation that excludes it.** Without that citation it may not use this bucket — fall back to `rare`. |

The citation requirement exists to stop `theoretical` from becoming a vibes-based "probably never happens" escape hatch.

### Blast radius

| Rating | Definition |
|---|---|
| `low` | Cosmetic or local; no data or user impact. |
| `medium` | User-visible bug, recoverable. |
| `high` | Data loss, security breach, outage, financial harm, or corruption. |

### Routing rule

| Likelihood | Blast radius | Destination |
|---|---|---|
| `routine` / `plausible` | any | Normal severity section, untagged — exactly as today. |
| `rare` / `theoretical` | `low` / `medium` | `Improbable / Not Worth Handling` appendix. One line, no fix guidance. |
| `rare` / `theoretical` | `high` | **Stays in its normal severity section**, tagged inline `(rare — <reachability reason, <=8 words>)`. |

That last row is load-bearing: rare-but-catastrophic is never suppressed, only flagged as low-frequency.

**Scope:** triage applies only to the itemized findings from the internal aspect agents (Agents 1–10), matching Step 4's scope. Comment preflight results and external advisor prose are not discrete scoreable issues — leave them untouched.

**Do not push this upstream to Step 3c.** Aspect agents must not self-assess likelihood at emit time, for the same reason Step 3c already forbids them assigning confidence scores: an agent that just found an edge case is motivated to describe it as plausible rather than "will basically never happen." Emission and likelihood-judging stay separate.

## Step 5: Format Output

Only include sections with findings from the agents that actually ran. If an aspect was not selected, omit it — do not render an empty section.

### Critical Issues (Must Fix)
[List issues that could cause bugs, security vulnerabilities, or data loss.
 Tag any rare/theoretical + high-blast-radius issue inline: `(rare — <reason>)`]

### Improvements (Should Fix)
[List issues that violate patterns, reduce maintainability, or hurt performance.
 Same `(rare — <reason>)` tagging rule applies.]

### Suggestions (Nice to Have)
[List minor style issues, potential refactors, or enhancements]

### Improbable / Not Worth Handling
[Render only if non-empty. One line per item, no fix guidance:
 {file}:{line} — {one-line issue} — {bucket}: {one-line reachability reason}]

This section is terse and placed last by convention — "collapsed" means one-liners at the bottom, not a UI disclosure widget. Terminal output has no working `<details>`; don't add one.

### External Advisor Reviews (--multi only)

If `--multi` was used, add one subsection per advisor that responded, titled with the advisor's name as reported by `second-opinion`:

#### {advisor name}
{that advisor's review}

#### Cross-Model Agreement
{note areas where the external advisors agree/disagree with the Claude agents - highlight consensus issues (flagged by multiple models) as higher confidence}

For each issue, explain:
1. What the problem is
2. Why it matters
3. How to fix it (with code example if helpful)

## Next: back to SKILL.md Step 6

**Printing this output does not end the run.** Return to `SKILL.md` and do **Step 6: Offer to Fix** — the mandatory AskUserQuestion prompt letting the user pick a fix scope. Do not end the turn on the formatted output alone.

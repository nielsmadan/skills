# Scoring, Triage & Output Format

Load after the review agents have returned (Steps 4 to 5).

## Step 4: Independent Confidence Scoring

Collect all issues from the review agents.

**Autofix items first.** Set aside every issue tagged `autofix` and check it against the test in `references/agents.md`: one right answer, no behaviour change, local. For a deletion, re-run the grep yourself, string literals included. Items that pass skip scoring and are applied in Step 4.6. An item that fails joins the scoring set like any other issue.

**Score every remaining issue.** Merge exact duplicates (the same defect at the same location from several agents) and nothing else. Do not send only the "top" claims, drop issues you judge minor, or skip the round because you checked the claims yourself. Past runs did all three, and most clean-code and interface findings never reached a scorer.

Launch **parallel scorer agents** — one per issue (or batch small groups if there are many). On a harness where each sub-agent is a full child session rather than a cheap in-process one, batch by default: ~5 issues per scorer, and never more than ~10 scorers total. Each scorer reads the code around the reported lines itself.

Give every scorer the prompt below **verbatim**, filling in only the braces. Do not add framing about which claims are real defects or worth acting on. Past main threads asked whether a claim was "true and worth acting on", which turned confidence into an importance vote and dropped true design findings at 60–79.

```
You are checking claims from a code review. For each claim, read the code it cites and enough of its callers, tests and related files to decide whether it is true. You are not told which reviewer wrote it.

Project guidelines:
{relevant AGENTS.md / CLAUDE.md excerpts}

Claims:
{n}. {file}:{line} — {the claim as the reviewer wrote it, with its stated consequence}

Return, for each claim:
- confidence (0-100): how sure you are that the claim is TRUE, meaning the code does or contains what it describes. This is not how much it matters.
    0   false: the code does not do this, or the claim misreads it
    25  probably false
    50  could not confirm or refute it from the code
    75  probably true, but one link in the chain is unverified
    100 verified: you traced it in the code
  A true claim about structure (duplication, naming, coupling, a leaky or misleading interface, dead code) scores as high as a true claim about a crash. "No bug today", "cosmetic" and "a maintainability point" describe impact; put them in impact, never in confidence.
- evidence: one line naming the file:line you checked.
- impact: critical | should | suggestion
    critical    can cause wrong results, a security hole, data loss or an outage
    should      a defect on a less critical path, or a design problem that will cost real work or cause bugs as the code changes
    suggestion  true and worth doing, but small
- likelihood: routine | plausible | rare | theoretical | structural (definitions below)
- blast_radius: low | medium | high
- reachability: for rare, how you checked; for theoretical, the file:line of the guard, type or validation that excludes it.
```

Paste the likelihood and blast-radius tables from Step 4.5 under the prompt.

The scorer should NOT know which agent found the issue. It evaluates purely based on the code and the claim.

**Filter**: Only issues scoring >= 80 pass through to the output. The scorer's `impact` sets each survivor's section in Step 5.

## Step 4.5: Likelihood & Blast-Radius Triage

Confidence answers "is this claim true?". It does not answer "will this ever happen?" — an issue can be 95/100 real and still require a once-in-the-universe alignment of conditions. This step adds that second axis so improbable findings stop being presented as work to do.

**Same dispatch, no extra agents.** The Step 4 prompt already asks for `likelihood` and `blast_radius`. Discard the triage fields for any issue that fails the >= 80 confidence gate.

### Likelihood buckets

The scorer must state *how* it checked reachability — trace the callers with Grep/Read and name the specific upstream guard, validation, or type constraint it found.

| Bucket | Definition |
|---|---|
| `routine` | Occurs on a normal request or common input; the path is already exercised. |
| `plausible` | Needs an ordinary but specific condition that *will* occur in production eventually — load, timeout, retry-after-failure, restart, malformed-but-realistic input. |
| `rare` | Needs an unusual combination — crafted or adversarial input, a narrow race window, or an invariant elsewhere already broken. |
| `theoretical` | Provably excluded given the actual call sites and validation. **The scorer MUST cite the exact `file:line` of the guard, type, or validation that excludes it.** Without that citation it may not use this bucket — fall back to `rare`. |
| `structural` | Not an event: the finding is about the code's shape (duplication, naming, coupling, interface design, dead code). Its cost is paid on every change, so "how often does it happen" does not apply. |

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
| `routine` / `plausible` / `structural` | any | Normal severity section, untagged. |
| `rare` / `theoretical` | `low` / `medium` | `Improbable / Not Worth Handling` appendix. One line, no fix guidance. |
| `rare` / `theoretical` | `high` | **Stays in its normal severity section**, tagged inline `(rare — <reachability reason, <=8 words>)`. |

That last row is load-bearing: rare-but-catastrophic is never suppressed, only flagged as low-frequency.

**Scope:** triage applies only to the itemized findings from the internal aspect agents (Agents 1–10), matching Step 4's scope. Preflight cleanup results, applied `autofix` items and external advisor prose are not discrete scoreable issues — leave them untouched.

**Do not push this upstream to Step 3c.** Aspect agents must not self-assess likelihood at emit time, for the same reason Step 3c already forbids them assigning confidence scores: an agent that just found an edge case is motivated to describe it as plausible rather than "will basically never happen." Emission and likelihood-judging stay separate.

## Step 4.6: Apply Autofix Items

Apply the `autofix` items that passed the check in Step 4. Do this after triage and before rendering, so the report describes the code as it now is. If an edit shifts lines in a file that also has a scored finding, update that finding's line number.

These edits are part of the review, not the fix prompt: they are listed under `Applied automatically` in Step 5 and never offered in Step 6.

## Step 5: Format Output

Only include sections with findings from the agents that actually ran. If an aspect was not selected, omit it — do not render an empty section. Place each surviving finding in the section matching its scorer's `impact`.

### Critical Issues (Must Fix)
[List issues that could cause bugs, security vulnerabilities, or data loss.
 Tag any rare/theoretical + high-blast-radius issue inline: `(rare — <reason>)`]

### Improvements (Should Fix)
[List issues that violate patterns, reduce maintainability, or hurt performance.
 Same `(rare — <reason>)` tagging rule applies.]

### Suggestions (Nice to Have)
[List minor style issues, potential refactors, or enhancements]

### Applied automatically
[Render only if non-empty. One line per item:
 {file}:{line} — {what changed} ({aspect that found it})]

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

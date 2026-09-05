---
name: review-plan
description: Multi-agent review of implementation plans. Use after creating a plan but before implementing, especially for complex or risky changes.
argument-hint: '[path to plan file or use current plan context]'
effort: xhigh
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Plan Review

Comprehensive review of implementation plans using parallel specialized agents.

## Usage

```
/review-plan                          # Review plan from current context
/review-plan path/to/plan.md          # Review specific plan file
```

## Gotchas
- The External Opinion agent depends on the `codex` CLI tool being installed and on PATH. If it is missing, that section of the synthesis is silently blank.
- Vague plans get only generic feedback and soft warnings, giving a false sense of validation. Plans need implementation-level specifics (file paths, function names, data flow) to get useful review.

## Workflow

### Step 1: Extract Plan and Check Internal Docs

Get the plan to review:
- If path provided, read the file
- Otherwise, use the plan from current conversation context
- Summarize: problem statement, proposed solution, key implementation steps

**Check internal documentation:**
Use Grep to search for relevant keywords in `docs/` and `*.md` files. Look for documented patterns, architectural guidelines, or gotchas related to the plan's area.

### Step 2: Determine Review Scope

Based on plan complexity, decide:
- **Simple** (single file, minor change): Skip research agent, 2 alternatives
- **Medium** (few files, new feature): All agents, 3 alternatives
- **Complex** (architectural, multi-system): All agents + research, 4 alternatives

**Do NOT shortcut this workflow:**
- "I already know the issues" -- External perspectives find blind spots you can't see
- "This will take too long" -- Parallel agents run simultaneously, the time cost is minimal

### Step 3: Spawn Review Agents in Parallel

**CRITICAL:** Launch agents in a SINGLE message with multiple tool calls.
Do NOT invoke one at a time. Do NOT stop after the first agent.

| Agent | Purpose | How |
|-------|---------|------|
| **External Opinion** | Get Codex input | `second-opinion` skill |
| **Alternatives** | Propose 2-4 other solutions | read-only sub-agent |
| **Robustness** | Check for fragile patterns | read-only sub-agent |
| **Adversarial** | Maximally critical review | read-only sub-agent |
| **Research** | Relevant practices online | `research-tech` skill |

**Read-only** means Claude Code's `Explore` or any harness's read-only agent profile — an agent type with no agent-spawning tool. The three review agents return findings, never files, so they need nothing more; and a general-purpose agent would decompose "check for fragile patterns" into its own fan-out.

**This skill nests two skills that each fan out on their own** (`research-tech` spawns up to 8; `second-opinion` queries every configured advisor). Three agents here plus those two is already the budget. Do not also spawn ad-hoc extra reviewers, and do not let the Research row expand into a full multi-round research session — one `research-tech` invocation, scoped to the plan's riskiest assumption.

See [references/agent-prompts.md](references/agent-prompts.md) for full prompt templates for each agent.

### Step 4: Synthesize Findings

Collect all agent results and synthesize:

```markdown
## Plan Review: {plan_name}

### External Opinion

**Codex:** {summary}

### Alternative Approaches

| Approach | Key Advantage | Key Disadvantage |
|----------|---------------|------------------|
| Current plan | {pro} | {con} |
| Alt 1: {name} | {pro} | {con} |
| Alt 2: {name} | {pro} | {con} |

**Recommendation:** {stick with plan / consider alternative X / hybrid}

### Robustness Issues

**Critical (must fix):**
- {issue}: {fix}

**Warnings:**
- {issue}: {fix}

### Adversarial Findings

**Valid concerns:**
- {concern}: {how to address}

**Dismissed concerns:**
- {concern}: {why it's not a real issue}

### Research Insights
(if applicable)
- {relevant finding}

---

## Revised Plan Recommendations

{specific improvements to make based on all feedback}

### Changes to Make
1. {change 1}
2. {change 2}

### Questions to Resolve
- {unresolved question}
```

### Step 5: Update Plan

If significant issues found, offer to revise the plan incorporating the feedback.

## Examples

**Review a refactor plan -- agents find a robustness issue:**
> /review-plan

Spawns parallel review agents against the current plan. The robustness agent flags that the migration has no rollback path if it fails midway, and the adversarial agent identifies a race condition under concurrent writes. The synthesis recommends adding a rollback step and a distributed lock.

**Review an auth plan with research agent:**
> /review-plan docs/plans/auth-redesign.md

Reviews the auth redesign plan with all agents including the research agent, which finds that the proposed token rotation strategy has a known edge case documented in the OAuth 2.1 spec. The synthesis recommends adjusting the refresh window based on the research findings.

## Troubleshooting

### Review agents disagree on approach
**Solution:** Focus on the points of consensus first, then evaluate the disagreements by weighing each agent's reasoning against your project constraints. Use the adversarial agent's concerns as a tiebreaker -- if it flags real risk in one approach, prefer the safer alternative.

### Plan is too vague for meaningful review
**Solution:** Add concrete details before running the review: specify which files change, what data flows through the system, and what the failure modes are. Agents produce generic feedback when the plan lacks implementation-level specifics.

## Notes

- Use the Skill tool for `second-opinion` and `research-tech` - do not write slash commands directly
- External opinion provides model diversity (Codex)
- The adversarial agent should be harsh - that's its job
- Robustness review catches patterns that "work in testing, fail in prod" - see [references/robustness-patterns.md](references/robustness-patterns.md) for examples
- Research agent finds relevant practices and known issues online
- Always synthesize all agent results into actionable improvements

---
name: breakdown-milestone
description: Break a milestone (e.g. M0) into incremental sprints of working software. Triggers "breakdown milestone", "split milestone", "plan milestone", "sprint plan for MX".
effort: high
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Breakdown Milestone

Break a milestone from `docs/planning/milestones/` into sprints — incremental chunks of working, verifiable software.

## Instructions

### Step 1: Load context

1. Read the milestone file from `docs/planning/milestones/` matching the argument (e.g., `M2` reads `m2-*.md`).
2. Read `docs/product-design.md`, `docs/architecture.md`, and `docs/tech-stack.md` for architectural context.
3. If prior milestones have sprint files in `docs/planning/sprints/`, scan them to understand what's already been built. Do not re-read milestone files for completed milestones — the sprint files are the source of truth for what was delivered.

### Step 2: Draft sprints

Each sprint must:

- **Produce working software.** At the end of a sprint, something new is demonstrably functional. "Set up the database schema" is not a sprint — "Create and display a minimal project page (schema + API + UI)" is.
- **Be incremental.** Each sprint builds on the previous one. Earlier sprints deliver a thin vertical slice; later sprints widen and deepen.
- **Include frontend and backend work together** when both are needed to make a feature work. Never have a "backend-only sprint" followed by a "frontend-only sprint" for the same feature — wire them together.
- **Have a clear verification method.** Describe what you can do/see to confirm the sprint is done.
- **Have a reasonable focus.** One primary goal, though supporting work (e.g., adding a DB column needed for the main feature) is fine.

Follow standard agile principles:
- Thin vertical slices over horizontal layers
- Working software over comprehensive documentation
- Respond to feedback over following a plan
- Deliver value early and often

### Step 3: Ask clarifying questions

Before finalizing, ask the user about any ambiguities:
- Scope decisions (e.g., "Should the config panel be editable in this milestone or read-only?")
- Priority trade-offs (e.g., "Should we prioritize the social handle check or the SEO analysis first?")
- Technical uncertainties (e.g., "The milestone mentions Namecheap API — do you have API access set up?")

Keep questions focused and actionable. Don't ask about things the docs already answer.

### Step 4: Write sprint files

Save each sprint to `docs/planning/sprints/` with the naming convention:

```
s{sprint}-{short-description}.md
```

Sprint IDs are globally sequential across milestones — check existing sprint files to determine the next number.

Examples: `s1-monorepo-hello-world.md`, `s7-iterative-brainstorming.md`

Each sprint file should contain:

```markdown
# Sprint {Y}: {Title}

**Milestone:** M{X} — {Milestone Name}
**Depends on:** {Previous sprint or "None"}
**Goal:** {One sentence — what is the user-visible outcome?}

## What's New After This Sprint

{2-3 sentences describing what a user/developer can now do that they couldn't before.}

## Scope

{Bulleted list of what this sprint delivers. Be specific but stay at the user-story level — not individual database columns, but meaningful capabilities.}

## Out of Scope

{Anything that might seem related but is deliberately deferred to a later sprint.}

## Verification

{Step-by-step description of how to verify this sprint is done. "Visit X, do Y, see Z."}
```

### Step 5: Present summary

After writing the files, present a numbered list of all sprints with their one-line goals so the user can review the overall flow.

## Examples

### Example 1: Breaking down M1 (Brainstorming)

User says: `/breakdown-milestone M1`

Actions:
1. Read `docs/planning/milestones/m1-brainstorming.md`
2. Read architectural docs for context
3. Check if M0 sprints exist (to know what's already built)
4. Draft sprints like:
   - S5: Landing page + project creation (user enters description, project saved to DB, basic page shown)
   - S6: Name generation (generate button calls AI, names displayed in batch)
   - S7: Pick/skip + iterative rounds (clicking names moves them, "generate more" uses picks as context)
   - S8: Config inference + AI transparency (AI suggests settings, shows reasoning before generation)
5. Ask: "The milestone mentions model comparison — should that be a sprint or a side task within one of the generation sprints?"
6. Write sprint files and present summary

## Troubleshooting

### Milestone file not found
**Cause:** Naming mismatch between argument and file.
**Solution:** Glob for `docs/planning/milestones/m{N}*.md` to find the right file. If no match, list available milestones.

### Sprints are too large
**Cause:** Trying to fit too much into one sprint.
**Solution:** Apply the "can I verify this in one sitting?" test. If a sprint has more than 5-7 scope items, split it.

### Sprints don't build on each other
**Cause:** Thinking in layers (all backend, then all frontend) instead of slices.
**Solution:** Each sprint should touch whatever layers are needed to deliver one working feature. Reorder so each sprint adds visible, testable functionality.

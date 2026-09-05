---
name: breakdown-sprint
description: Break a sprint (e.g. s1) into ordered, parallelizable tasks following agile user-story principles. Triggers "breakdown sprint", "task breakdown", "plan sprint tasks".
effort: high
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Breakdown Sprint

Break a sprint from `docs/planning/sprints/` into ordered tasks — incremental user stories that build on each other, with parallelization opportunities marked.

## Instructions

### Step 1: Load context

1. Read the sprint file from `docs/planning/sprints/` matching the argument (e.g., `s1` reads `s1-*.md`).
2. Read the parent milestone file from `docs/planning/milestones/` for broader context.
3. Read `docs/tech-stack.md` and `docs/architecture.md` for implementation details.
4. If previous sprints in the same milestone have task files, scan them to understand what's already been built.

### Step 2: Draft tasks as user stories

Each task should:

- **Be a meaningful increment.** "As a developer, I can hit the health endpoint and get a 200" — not "Create the health endpoint file." Tasks deliver observable outcomes.
- **Be incremental.** Start with the simplest working version, then extend. Example progression for a user profile:
  1. Create users table + basic GET endpoint + minimal UI showing the name
  2. Extend profile to show payment history and past projects
  3. Add profile editing with form validation
- **Include enough detail to act on.** Each task should mention the key layers involved (e.g., "schema, API route, UI component") and any specific technical choices, but not dictate exact implementation line by line.
- **Follow INVEST criteria:**
  - **I**ndependent — minimize dependencies between tasks (mark where dependencies exist)
  - **N**egotiable — describe the what, not the exact how
  - **V**aluable — each task delivers something useful
  - **E**stimable — small enough to reason about
  - **S**mall — completable in a focused session
  - **T**estable — clear done condition

### Step 3: Order and mark parallelism

Assign each task:
- **Order number** — sequential execution order
- **Parallel group** (if applicable) — tasks in the same group can be worked on simultaneously

Use this format for each task:

```markdown
### Task {N}: {Title}
**Parallel group:** {group letter, or "sequential"}
**Depends on:** {task number(s), or "none"}

**Story:** As a {role}, I can {action} so that {benefit}.

**Scope:**
- {What this task delivers, at the user-story level}
- {Key layers involved: schema/API/worker/UI}
- {Any specific technical notes}

**Done when:** {How to verify this task is complete}
```

Rules for parallelism:
- Tasks in the same parallel group have no dependencies on each other
- Tasks in a parallel group may all depend on the same prior task(s)
- Sequential tasks depend on the task before them
- Be conservative — only mark as parallel when truly independent

### Step 4: Ask clarifying questions

Before finalizing, ask about:
- Ambiguous scope boundaries between tasks
- Technical decisions that affect task ordering
- Whether any tasks should be combined or split further

### Step 5: Write task file

Save to `docs/planning/sprints/` with the naming convention:

```
{sprint-id}-tasks.md
```

Example: `s1-monorepo-hello-world-tasks.md`

The file should contain:

```markdown
# Tasks: Sprint {Y} — {Sprint Title}

**Sprint:** s{Y}
**Total tasks:** {N}
**Parallel groups:** {list groups, e.g., "A (tasks 2-4), B (tasks 6-7)"}

## Execution Order

{A concise visual showing the order and parallelism}

Example:
1 -> [2, 3, 4] -> 5 -> [6, 7] -> 8

## Tasks

### Task 1: ...
(task details as defined above)
```

### Step 6: Present summary

After writing the file, present:
1. The execution order diagram
2. A numbered list of tasks with one-line descriptions
3. Which tasks can be parallelized

## Examples

### Example 1: Breaking down a brainstorming sprint

User says: `/breakdown-sprint s6`

Actions:
1. Read `docs/planning/sprints/s6-*.md`
2. Read milestone and architecture docs
3. Draft tasks like:
   - Task 1: Wire up OpenRouter client with Langfuse tracing (sequential — foundation for AI calls)
   - Task 2: Build brainstorming API endpoint that generates names (depends on 1)
   - Task 3: Create name display component showing themed batch (parallel group A — no API dependency for UI scaffolding)
   - Task 4: Connect generate button to API and display streaming results (depends on 2, 3)
4. Ask: "Should model comparison be a separate task or embedded in the generation task?"
5. Write task file and present summary

## Troubleshooting

### Sprint file not found
**Cause:** Naming mismatch between argument and file.
**Solution:** Glob for `docs/planning/sprints/{arg}*.md` to find the right file. If no match, list available sprints.

### Tasks are too granular
**Cause:** Breaking down to implementation steps instead of user stories.
**Solution:** Apply the "so that {benefit}" test. If you can't articulate user/developer benefit, the task is too small. Merge it up.

### Tasks are too large
**Cause:** Combining multiple meaningful increments into one task.
**Solution:** If a task has more than 4-5 scope items or touches more than 3 layers, consider splitting. Apply the incremental test: can you deliver a simpler version first?

### Too few parallel groups
**Cause:** Being overly conservative about dependencies.
**Solution:** Ask: "Does task B actually need task A's output, or just the same prerequisites?" UI scaffolding and backend logic can often be parallel if they share a common dependency.

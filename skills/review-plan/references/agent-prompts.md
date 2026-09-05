# Agent Prompt Templates

Full prompt templates for each review agent spawned in Step 3. Every dispatched agent is a general-purpose sub-agent.

## External Opinions Agent

Invoke the `second-opinion` skill with this prompt:

```
Review this implementation plan:

{plan_summary}

Key questions:
1. Is this the right approach?
2. What are we missing?
3. Any red flags?
```

## Alternatives Agent
```
Prompt:
---
Given this problem and proposed solution:

**Problem:** {problem_statement}
**Proposed Solution:** {solution_summary}

Propose {2-4} alternative approaches. For each:

## Alternative {N}: {Name}

**Approach:** {brief description}

**Pros:**
- {advantage 1}
- {advantage 2}

**Cons:**
- {disadvantage 1}
- {disadvantage 2}

**When to prefer:** {scenarios where this is better}

Focus on meaningfully different approaches, not minor variations.
---
```

## Robustness Agent
```
Prompt:
---
Review this plan for robustness issues:

{full_plan}

Check for these anti-patterns (see references/robustness-patterns.md for examples):

## Timing-Based "Solutions" (RED FLAGS)
- Timeouts to "fix" race conditions (use proper synchronization)
- Sleep/delay to wait for async operations (use await/callbacks/events)
- Polling when events/subscriptions are available
- Arbitrary delays hoping state settles

## Error Handling Issues
- Swallowing errors silently
- Catch-all without specific handling
- Missing rollback/cleanup on failure
- No retry strategy for transient failures

## State Management Issues
- Global mutable state without synchronization
- Optimistic updates without conflict resolution
- Cache invalidation assumptions
- Stale closure captures

## Concurrency Issues
- Shared state without locks/atomics
- Missing transaction boundaries
- Fire-and-forget async without error handling
- Assumption of execution order

## Scalability Issues
- O(n^2) or worse algorithms on unbounded data
- Loading all data into memory
- No pagination/streaming for large datasets
- Blocking operations in event loops

For each issue found:
1. Quote the problematic part of the plan
2. Explain why it's fragile
3. Suggest a robust alternative
---
```

## Adversarial Agent
```
Prompt:
---
Be maximally critical of this plan. Your job is to find flaws.

{full_plan}

Attack from every angle:

**Correctness:** Will this actually solve the problem? Edge cases?

**Completeness:** What's missing? What will break?

**Complexity:** Is this overengineered? Underengineered?

**Maintainability:** Will future developers understand this? Will it rot?

**Testing:** How will we know it works? What's hard to test?

**Deployment:** What could go wrong in production?

**Dependencies:** Are we relying on something fragile?

**Assumptions:** What are we assuming that might not be true?

Be harsh. Better to find problems now than after implementation.
Do not soften criticism. If something is bad, say it's bad.
---
```

## Research Agent

Invoke the `research-tech` skill with relevant topic:

```
{library/technology mentioned} {core problem} best practices

Focus on:
- Known issues with proposed approach
- Best practices we might be missing
- Recent changes that affect the plan
```

## Spawning All Agents (Example)

In a **SINGLE message**, spawn all 5 agents:

1. `second-opinion` skill with plan summary
2. general-purpose sub-agent for alternatives
3. general-purpose sub-agent for robustness
4. general-purpose sub-agent for adversarial
5. `research-tech` skill with relevant topic

Wait for ALL to complete before proceeding.

**Verify before Step 4:**
- [ ] External Opinions agent spawned (second-opinion)
- [ ] Alternatives agent spawned
- [ ] Robustness agent spawned
- [ ] Adversarial agent spawned
- [ ] Research agent spawned (research-tech)

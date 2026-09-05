# Hard Fix — Agent Prompts & Templates

## Phase 2: Agent Task Prompts

### Research Agent

```
research-tech {library_if_any} {error_or_symptom}

Focus on: known bugs, breaking changes, similar issues others faced
```

### Debug Agent

```
debug-log {problem_area}

Add comprehensive logging to trace the exact execution path and state
```

### History Agent

```
review-history {affected_files_or_area}

Look for: recent changes, when it last worked, who touched it, past similar issues
```

### Library Source Agent

```
Subagent type: general-purpose
Prompt:
---
Investigate the source code of libraries involved in this issue:

Problem: {description}
Libraries involved: {library_names}

1. Find the library source code:
   - node_modules/{library}/ for JS/TS
   - Look for .dart files in pub cache for Flutter
   - site-packages/{library}/ for Python
   - vendor/ or go modules for Go

2. Locate the relevant functions/classes being used

3. Read the actual implementation and look for:
   - Undocumented behavior or edge cases
   - Default values that might cause issues
   - Error handling that swallows errors
   - Race conditions or timing assumptions
   - Version-specific behavior

4. Check if our usage matches what the library expects

Return findings about how the library actually works vs how we're using it.
---
```

### Second Opinion Agent

```
second-opinion

Problem: {description}
Tried: {list of attempted fixes}
Symptoms: {what's happening}

What are we missing?
```

---

## Phase 3: Synthesis Examples

**BAD synthesis (superficial):**
```
Root Cause: The API call is failing.
Evidence: Got a 500 error in the logs.
Fix: Add a try-catch.
```

**GOOD synthesis (investigative):**
```
Root Cause: Race condition between auth token refresh and API call.
Evidence:
- Debug logs: Token refresh starts at T+0, API call at T+50ms, refresh completes T+200ms
- History: Started after PR #234 moved token refresh to background
- Library source: axios doesn't queue requests during refresh by default
- Research: Known issue axios#4193, recommended fix is axios-auth-refresh
Fix: Add request queuing during token refresh using axios-auth-refresh interceptor.
```

The difference: superficial stops at symptoms, good traces to mechanism.

---

## Phase 5: Presentation Template

```markdown
## Hard Fix Analysis: {problem}

**Root Cause** (Confidence: High/Medium/Low): {mechanism, not symptom}

**Evidence**: {one key finding per source}

**Recommended Fix**: {specific steps}

**Alternatives**: {if main fix fails}

**Validation**: {how to verify}
```

---

## Phase 7: Log Template

Write to `docs/log/YYYY-MM-DD-{Issue}.md`:

```markdown
# {Issue Title}

**Date:** {date} | **Area:** {files/components}

## Problem & Symptoms
{what was happening}

## Root Cause
{what was actually wrong - the mechanism}

## Solution
{what fixed it, with code if relevant}

## Prevention
{how to avoid in future}
```

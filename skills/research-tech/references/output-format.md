# Output Format Template

Lead with the synthesis, then include only the supporting detail sections relevant to the query. Skip sections that would repeat the synthesis.

```markdown
## Research Results: {topic}

### Synthesis

**Goal:** {one-line summary of what user is trying to achieve}

**Recommended Approach:**
{what the research suggests, prioritizing recent authoritative sources}

**Key Findings (weighted by credibility):**
- {finding from high-credibility source}
- {finding from high-credibility source}
- {finding from medium source, noting caveat if needed}

**Confidence:** {High/Medium/Low}
- Based on: {e.g., "3 high-credibility sources agree"}
- Caveats: {any outdated info factored in, unresolved conflicts, gaps in research}

**Key References:**
1. [{title}]({url}) — {why this source matters, e.g., "official migration guide"}
2. [{title}]({url}) — {why this source matters, e.g., "maintainer confirmed fix in this issue"}
3. [{title}]({url}) — {why this source matters} (optional, only if 3rd source significantly shaped the conclusion)

---

### Supporting Details

(Include only sections relevant to the query, and only findings not already covered in the synthesis above)

#### Comparison
(only if comparison query)

**{Option A}:**
- Pros: {list}
- Cons: {list}
- Best for: {use cases}

**{Option B}:**
- Pros: {list}
- Cons: {list}
- Best for: {use cases}

#### Specific Error Matches
(only if error was provided)
{causes and fixes not already in synthesis}

#### Version/Changelog
(only if version was mentioned)
{breaking changes and migration info}

#### Conflicts
(only if sources disagree on something material)
- {source A} says X, but {source B} says Y
- **Resolution:** {which to trust and why}
```

# Output Format Template

Lead with the answer. Keep it concise. Only add sections that provide value beyond the main answer.

```markdown
## {topic}

{Direct answer to the question. State the recommended approach or key finding up front. Use **inline source counts** for transparency — e.g., "(3 sources)", "(2 high-authority sources)", or "(1 source, low confidence)" next to specific claims.}

{For empirical questions, lead with what the strongest evidence shows. For historical questions, lead with what primary sources show. For comparisons, lead with the headline trade-off. For claim verification, lead with the verdict.}

**Key references:**
1. [{title}]({url}) — {why this source matters, e.g., "2023 meta-analysis pooling 47 studies"}
2. [{title}]({url}) — {why this source matters, e.g., "primary government data from BLS"}
3. [{title}]({url}) — {why this source matters} (only if a 3rd source significantly shaped the answer)

{STOP HERE if the answer above covers it. Only add sections below if they provide substantial additional value beyond what the direct answer already states.}

---

#### Background
(only when grounding is useful — contested terminology, unfamiliar entities, niche field)
{Encyclopedic context with the entry's own cited sources}

#### Evidence
(empirical / scientific / scholarly questions, when there's nuance the headline answer didn't capture)
- **{Finding}** — {study type, sample, date, citation}. {What it shows.}
- **{Finding}** — {study type, sample, date, citation}. {What it shows.}

Include where studies disagree and what drives the disagreement (sample, endpoint, methodology).

#### Comparison
(only for comparison queries with meaningful pros/cons to lay out)
**{Option A}:** Strengths · Weaknesses · Best for
**{Option B}:** Strengths · Weaknesses · Best for

Note where the choice depends on values vs. where there's an empirical answer.

#### Regional details
(only if region-specific info wasn't already in the main answer)
{Local regulations, pricing, availability, locale-specific authoritative sources}

#### Claim Verification
(only if user provided a specific claim to verify)
- **The claim:** "{exact_claim}"
- **Verdict:** {true / mostly true / mixed / mostly false / false / unproven}
- **Strongest evidence for:** {source(s)}
- **Strongest evidence against:** {source(s)}
- **Origin of the claim:** {original source if findable, or "untraceable"}

#### Historical Context
(only if historical query — primary documents and contemporaneous reporting that didn't fit in the headline)

#### Conflicts
(only if sources disagree on something material)
- {source A} says X, but {source B} says Y
- **Resolution:** {which to trust and why — authority, scope, recency, primary vs secondary}

#### Open Questions
(only if material gaps remain — what the search did not resolve and why)
```

## Guidelines

- **No empty sections.** If a section would just repeat the headline answer or has nothing material to add, skip it entirely.
- **Inline source counts.** Use "(N sources)" or "(1 source, low confidence)" next to claims to show how well-supported they are. This replaces a separate Confidence block in most cases.
- **Confidence is implicit when source counts are visible.** Only call out confidence explicitly when it's notably low, when sources conflict and the conflict matters, or when the topic is fast-moving and the answer might shift.
- **Shorter is better.** A 5-sentence answer with 3 good sources beats a structured report with empty sections. Resist the urge to fill every available section.
- **Flag affiliate/sponsored sources** when they materially shaped the answer — readers should know if a recommendation came from a comparison site that earns commission.
- **For regional queries**, name the locale explicitly in the answer (don't assume the reader knows you searched in German).

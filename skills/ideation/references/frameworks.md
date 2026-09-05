# Ideation Frameworks

A library of structured idea-generation methods. Each entry: **what it is**, **the
procedure** (how to actually run it), and a **mini-example**. Pick 2-3 per session —
matched to the stuck-state by the routing table in `SKILL.md`. Don't run them all; the
point is to apply the few that fit, well.

Skim only the entries the router selects. Each is self-contained.

---

## Problem-framing methods
*Use when the user isn't sure what the real problem is, or is solving the wrong one.*

### Jobs-to-be-Done (JTBD)
**What:** Frame the need as the "job" someone hires the thing to do, in a situation —
independent of any current solution. The single best problem-definition lens.
**Procedure:**
1. State the job as: *"When [situation], I want to [motivation], so I can [expected
   outcome]."*
2. Strip out the current solution — describe progress the person is trying to make, not
   the product they use.
3. List competing "solutions" they hire today (including doing nothing, or a spreadsheet).
4. Find where every current solution underserves the job — that gap is the real problem.
**Example:** Not "users want a faster export button" but *"When I finish a report at 6pm,
I want to hand it off without re-checking formatting, so I can leave on time"* — reframes
the problem from speed to trust in the output.

### First Principles
**What:** Strip the problem to irreducible truths, discard inherited assumptions, rebuild.
Best when stuck inside conventional framing.
**Procedure:**
1. Write the problem as currently stated. List every assumption baked into it.
2. For each assumption ask: *is this physically/logically necessary, or just convention?*
3. Keep only what's necessary. Restate the problem using only those primitives.
4. Rebuild solutions from the primitives, ignoring how it's "normally" done.
**Example:** "We need a cheaper way to ship batteries" → primitives: cost of raw materials
vs. assembled price → reframe as "why not buy materials and assemble ourselves?"

### Inversion / Worst Possible Idea
**What:** Ask how to *cause* the problem or guarantee failure, then invert. Surfaces hidden
assumptions and failure modes a blank page hides.
**Procedure:**
1. Ask: *"How could we make this problem far worse / guarantee total failure?"*
2. Generate that list freely — it's easier and looser than generating good ideas.
3. Invert each bad idea into its opposite, or read the list as a catalogue of risks to
   design against.
**Example:** "How do we make onboarding fail?" → "force signup before showing any value" →
invert → "show value before asking for signup."

### 10x vs 10% reframe
**What:** Force an order-of-magnitude reframe to surface ideas incremental thinking hides.
**Procedure:** Ask the question twice. *"How would I improve this 10%?"* (tuning) then
*"How would this work if it had to be 10x better / serve 10x the users / cost 1/10th?"*
The 10x version usually requires abandoning the current approach — that's the signal.
**Example:** 10%: cache the query. 10x: don't run the query — precompute and push.

---

## Feature-ideation methods
*Use when extending something that already exists — what to add that complements it.*

### SCAMPER
**What:** A transform checklist applied to an existing thing. The workhorse for "improve
or extend what's here."
**Procedure:** Walk each lever against the current product/feature and note what each
suggests:
- **S**ubstitute — swap a component, material, rule, or step for another.
- **C**ombine — merge two features, flows, or data sources into one.
- **A**dapt — borrow a mechanism from elsewhere that fits this context.
- **M**odify/Magnify — scale a dimension up or down (more, less, bigger, smaller).
- **P**ut to other use — repurpose an existing capability for a new job.
- **E**liminate — remove a step, option, or component. What if it weren't there?
- **R**everse — flip the order, roles, or direction of a flow.
**Example:** Export feature → *Eliminate*: drop the format picker, infer it. *Combine*:
merge export + share into one action. *Reverse*: let recipients pull instead of senders push.

### Multi-perspective personas
**What:** Generate ideas as specific, named stakeholders. The cheapest reliable diversity
boost — concrete, not a vague "think differently."
**Procedure:**
1. Pick 3-5 concrete lenses for the domain. Defaults for product: **PM** (strategic fit,
   metrics), **Designer** (flow, friction), **Engineer** (what's now-cheap to build),
   **Power user**, **First-timer**. For non-product: pick relevant roles (e.g. skeptic,
   newcomer, the person who pays, a 10-year-old, a rival).
2. Generate 3-5 ideas *from each lens independently* — don't let them blur.
3. Merge and dedupe; the disagreements between lenses are often the richest ideas.
**Example:** Engineer sees a cheap real-time hook; PM sees it enabling a notifications
feature; Designer warns it adds noise → synthesized idea: opt-in digest, not live pings.

### Morphological analysis
**What:** Decompose into independent parameters, list options per parameter, combine across
the grid. Exhaustive combination coverage.
**Procedure:**
1. Break the thing into 3-4 independent dimensions (e.g. *capability × surface × user × trigger*).
2. List 3-6 concrete options under each.
3. Walk combinations — especially non-obvious cross-cells — and keep the ones that spark.
**Example:** Capability {summarize, alert, compare} × Surface {inline, email, widget} ×
Trigger {manual, scheduled, on-change} → "compare + email + on-change" = a diff-digest feature.

---

## Solution-generation methods
*Use when the problem is defined and you need ways to solve it.*

### Crazy 8s (forced volume)
**What:** Time-boxed quantity to push past the obvious first answer. Quantity unlocks quality.
**Procedure:** Generate 8 *distinct* solutions fast, deferring all judgment. Force real
variation — no two may share the same core mechanism. The first 2-3 will be obvious; the
value is in 4-8 where you're forced to reach.
**Example:** "Reduce support load" → in-app answers, better empty states, a status page,
proactive emails, a community forum, smarter error messages, a chatbot, a refund-first policy.

### Analogical / cross-domain transfer
**What:** Abstract the problem, find a far domain that solved an analogue, port the mechanism
back. The highest-novelty technique — rivals haven't seen the source domain.
**Procedure:**
1. Abstract the problem to its essence ("distribute a scarce shared resource fairly").
2. Ask: *who else, in a totally different field, has this exact abstract problem?* (nature,
   logistics, games, biology, finance, traffic…).
3. Study how they solve it. Port the mechanism, not the surface.
**Example:** Rate-limiting → traffic systems use metered on-ramps → token-bucket throttling.
Caching invalidation → libraries use due-dates → TTLs.

### Lateral thinking / provocation (PO)
**What:** Deliberately absurd statements as stepping-stones to escape dominant patterns.
Use when linear thinking is exhausted.
**Procedure:**
1. State a provocation — something deliberately impossible or reversed ("PO: the app has no
   buttons" / "PO: the user does the work, not us").
2. Don't evaluate it. Ask: *what's interesting here? what would have to be true? what does
   this move toward?*
3. Harvest the realistic idea the provocation points at.
**Example:** "PO: onboarding takes zero steps" → what if the first action *is* the signup,
account created lazily on first save → deferred-account onboarding.

### TRIZ contradiction resolution
**What:** When blocked by a trade-off ("better X forces worse Y"), resolve the contradiction
instead of compromising.
**Procedure:**
1. Name the contradiction precisely: improving **X** currently worsens **Y**.
2. Ask the inventive moves: *separate in time* (do X then Y, not both at once), *separate in
   space* (X here, Y there), *separate by condition* (X for some cases, Y for others), or
   *change the system* so the trade-off dissolves.
**Example:** "More validation (X) means a slower form (Y)" → separate in time: validate
async after submit, not blocking keystrokes.

---

## Convergence (always end here)
*After diverging, narrow. Never present a raw idea-dump as the answer.*

### Diverge → converge discipline
**What:** Keep generation and judgment in separate phases. Judging mid-generation kills volume.
**Procedure:** Generate wide with judgment OFF. Then switch modes: cluster similar ideas,
discard duplicates, and score the rest. Pick a **top N** (usually 3-5) to develop.

### Scoring + riskiest assumption
**What:** Turn a wide list into a prioritized few, each carrying its biggest unknown.
**Procedure:** For each surviving idea, capture:
- **Impact** — how much it moves the goal (H/M/L).
- **Effort/cost** — rough size (S/M/L).
- **Riskiest assumption** — the one thing that, if false, kills it. This is the next thing to
  test — it turns ideation into action.
Lead with high-impact / low-effort. Present as the output table in `SKILL.md`.

### Six Thinking Hats (optional, for evaluating a shortlist)
**What:** Examine each shortlisted idea from six fixed modes, one at a time, to pressure-test it.
**Procedure:** For an idea, cycle: **White** (facts/data), **Red** (gut feeling), **Black**
(risks, why it fails), **Yellow** (upside, why it works), **Green** (how to improve it),
**Blue** (does it fit the goal). Keeps evaluation balanced instead of anchoring on the first reaction.

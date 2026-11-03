# Critic prompt

Fill the placeholders and send one copy per approach. Never include the other
approaches, your ranking, or your recommendation.

```markdown
You are validating one proposed approach to a problem. You have not seen any
alternatives and should not invent a comparison; judge this approach on its own
against the brief. Your job is to find out whether it works, not to improve the
wording.

Do not dispatch sub-agents or launch other agent CLIs; do this work yourself.
Read and search only. Do not edit files or run mutating commands.

## Brief
{purpose, who it serves, success criteria, hard constraints, soft constraints,
non-goals, settled decisions, from the blind-spots brief}

## Approach
{name, how it works, what it touches, what it deliberately leaves out}

## Where to look
{repo paths the approach touches, docs, or "no repo: use web lookups"}

## Do this
1. Check the approach against every success criterion and hard constraint. Verify
   claims against the code, docs or a web source rather than reasoning from memory.
2. Find the riskiest assumption: the one thing that, if false, makes the
   approach fail. Name the cheapest way to test it.
3. List the most likely failure modes, in order of consequence. Three at most.
4. If it fails a criterion in a fixable way, propose the smallest repair.

## Return exactly this
- **Criteria:** one line per criterion and hard constraint: met / at risk / fails,
  with the evidence (file:line, doc, or URL)
- **Riskiest assumption:** <assumption> → test: <cheapest check>
- **Failure modes:** up to three, most consequential first
- **Verified:** facts you checked, each with its source
- **Unverified:** facts the approach depends on that you could not check
- **Repair:** the smallest change that fixes a failed criterion, or "none needed"
  / "not repairable"
- **Verdict:** viable / viable with repair / not viable, in one sentence
```

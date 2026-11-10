# Domain modeling within doc

Make the project's important concepts precise enough that people and agents use the same words
for the same things. Apply this to the requested area, not as a prerequisite to every doc edit.

## Establish the meaning

1. Read existing definitions, relevant decisions, and representative code paths. Follow any
   glossary map or context-specific definitions already present; identical words can mean
   different things in different domains.
2. Identify the specific ambiguity: one word for two concepts, multiple names for one concept,
   or a claimed relationship that disagrees with the implementation. Cite the competing uses.
3. Test the distinction with a concrete scenario. For example, can a workspace contain several
   sessions, and can a session survive closing its window? Use the answer to sharpen the terms;
   do not invent a relationship from class names alone.
4. Use explicit user decisions and established project definitions to resolve meaning. Code
   establishes what happens today, but may implement the intended model incorrectly. When the
   evidence leaves a material choice open, ask a focused question and continue independent doc
   work. Record the discrepancy without silently choosing a product rule or renaming code.
5. Once resolved and writes are authorized by the current mode or request, update the canonical
   definition and affected in-scope living docs together. Do not turn glossary maintenance into
   an implementation refactor or rewrite historical decisions.

## Keep a small canonical glossary

Reuse the project's location and format, including root `GLOSSARY.md` or a terminology section
inside a feature doc. Do not create a second glossary for the same context. If there is no home,
put a few local definitions in the relevant doc; recurring concepts shared across areas can earn
`docs/glossary.md`. Add a pointer from the existing doc map. A glossary does not require upgrading
the whole documentation profile or creating a hierarchy of contexts.

An entry needs a canonical term and a concise domain definition. Add an alias, a contrast with a
nearby concept, a scope, or a short example only when it resolves real ambiguity. Describe what
the concept means, not its class fields, storage schema, implementation plan, or every possible
state. Put behavior in the feature/flow doc and implementation in the technical doc, linking
instead of repeating them. Ordinary programming vocabulary needs no glossary entry.

For example, after the project confirms the distinction:

> **Session:** one agent conversation and its retained state. A session may outlive the terminal
> window used to interact with it; closing that window does not mean the session is complete.

Missing glossary files are not findings by themselves. During assess/review, show the ambiguity
and its consequence before proposing a definition or a new home, using the shared review grading.

## Record consequential decisions selectively

Use an ADR when the choice has meaningful reversal cost, would be surprising without its
context, and resolves a genuine trade-off. A simple naming clarification usually needs only a
definition; brief local rationale can stay in the relevant doc's `Why` section.

Follow the repository's ADR location and format; the default is `docs/decisions/` and the template
in [generate-templates.md](generate-templates.md). Preserve the append-only lifecycle in
[principles.md](principles.md). Supersede a changed decision through a new record and the old
record's status/link, rather than rewriting its reasoning.

## Source

Inspired by [Matt Pocock's domain-modeling skill](https://github.com/mattpocock/skills/tree/main/skills/engineering/domain-modeling),
adapted to doc's existing modes, document locations, and lifecycle rules.

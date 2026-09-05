# Instruction-File Update Guidelines

## Core Principle

Only add information that genuinely helps future sessions. Every line loads into every
session, so every line must earn its place: *would removing this cause a mistake?*

## What TO Add

1. **Gotchas and non-obvious patterns** — prevents repeated debugging. The single
   highest-value category
2. **Commands/workflows discovered** — saves rediscovery
3. **Conventions that differ from the tool's defaults** — a convention the tooling already
   enforces by default is noise
4. **Cross-module knowledge no single file reveals** — ordering requirements, invariants,
   which layer owns what
5. **Configuration quirks** — environment-specific knowledge
6. **Pointers** — a line routing to the skill or `docs/` file that carries the depth

## What NOT to Add

1. **Anything derivable from the repo** — directory layouts, framework names, file
   inventories, dependency lists, "UserService handles users" (the name says that)
2. **Anything the harness already supplies** — a catalog of available skills, tools, or
   slash commands. Agents get those injected; restating them doubles the token cost and
   goes stale. Put trigger wording in the skill's own `description:` instead
3. **Long procedures** — a multi-step checklist or rule set belongs in a skill or a
   `docs/` file that loads when relevant, referenced from here in a line
4. **Rules already stated elsewhere** — in the global instruction file, in another section,
   or in a bundled skill. State it once, in the narrowest place that covers it
5. **Generic best practices** — "write tests", "use good names" (universal, not project-specific)
6. **One-off fixes** — "fixed bug in commit abc123" (won't recur)
7. **Verbose explanations** — prefer `Auth: JWT with HS256` over a paragraph about JWT

## What to Flag for Removal

Auditing is not only additive. Propose cutting:

- Sections that restate the file system or the harness's own context
- Inline procedures that should be extracted into a skill
- Rules that contradict another rule or the tool's default behavior — name both sides and
  ask the user which wins; don't silently pick one
- Blanket absolutes that are wrong for a recognizable subset of cases. **But leave rules
  that encode the user's actual preference alone** — house style, commit format, review
  policy. Preference is what this file is *for*; only guardrails-against-failure are
  candidates for removal, and even then the user decides

## Validation Checklist

- Each addition is project-specific and non-derivable
- Nothing duplicates the global file, another section, or a skill
- Depth is behind a pointer, not inline
- Commands are tested and work; file paths are accurate
- No new rule conflicts with an existing one
- Expressed as concisely as possible

# Instruction-File Quality Criteria

Applies to the always-loaded instruction file — `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
or a package-level equivalent. Every line loads into **every** session, so the bar is
"would removing this line cause a mistake?"

## Scoring Rubric

### 1. Gotchas & non-obvious knowledge (25 points)

The highest-value content — what an agent cannot learn by reading the repo.

- **25**: Rich in real gotchas: quirks, footguns, "seems like it should work but doesn't",
  invariants, ordering requirements, cross-module knowledge no single file reveals
- **18**: Several genuine gotchas, some areas uncovered
- **10**: A couple of gotchas among mostly generic content
- **5**: Token gotcha section
- **0**: None

### 2. Commands & divergent conventions (20 points)

Build/test/lint/deploy invocations, and conventions that **differ from the tool's defaults**.
A convention identical to what the tooling already does by default scores nothing.

- **20**: Essential commands present and correct; conventions listed are genuinely divergent
- **15**: Most commands present; some listed conventions are just defaults restated
- **10**: Basic commands only
- **5**: Few commands, several wrong
- **0**: None

### 3. Non-derivable & non-duplicated (20 points)

Deduct for anything the agent already has or can trivially get.

- **20**: Nothing greppable or already-in-context. No directory listings, no framework
  names, no restated signatures, no catalog of skills/tools/commands the harness already
  injects, no content repeated in another instruction file or across sections
- **15**: One or two derivable passages
- **10**: A whole section is derivable (a directory tree, a tool catalog)
- **5**: Much of the file restates the repo
- **0**: Mostly a map of things the agent can see

**Look specifically for:** directory-structure trees, file inventories, tables listing
available skills/agents/tools (the harness supplies these), lists of dependencies
(`package.json` has them), and the same policy stated in both the global and the project
file.

### 4. Progressive disclosure (15 points)

Depth belongs behind a pointer, not inline in the always-loaded file.

- **15**: Long procedures, checklists, and rule sets live in skills or `docs/` and are
  referenced by a line or two. The instruction file routes; it doesn't contain
- **10**: Mostly routes, one long inline procedure that should be extracted
- **5**: Several multi-paragraph procedures inline
- **0**: The file is a manual — everything the project might ever need, always loaded

**The extraction test:** if a passage is only relevant to *some* sessions, it should be a
skill or a `docs/` file the agent loads when relevant.

### 5. Currency (10 points)

- **10**: Commands work; file references resolve; described behavior matches the code
- **7**: Minor staleness
- **3**: Several dead references
- **0**: Severely outdated

### 6. Internal consistency (10 points)

- **10**: No rule contradicts another rule, the harness's own defaults, or a bundled skill.
  Positive phrasing over "don't" lists
- **7**: One mild tension
- **3**: A clear conflict an agent must resolve mid-task
- **0**: Multiple contradictory instructions

**Conflicts are expensive**: an agent facing "match the surrounding code's comment density"
in one place and "never write comments" in another must spend reasoning deciding which
wins, and may pick wrong. Flag the conflict; let the user decide which survives.

## Size

Target roughly **<200 lines**. Over that, the finding is usually "extract to skills/docs",
not "write more tersely". A bloated file makes the agent ignore the rules that matter.

## Red Flags

- Directory trees, file inventories, or tables of available skills/tools/commands
- The same rule stated in both the global and the project instruction file
- Commands that would fail (wrong paths, missing deps); references to deleted files
- Rules that contradict each other or the tool's own defaults
- **Over-constraining absolutes** where judgment would serve better — a blanket "NEVER do
  X" that is wrong for a recognizable subset of cases. **Judgment call:** if the rule
  encodes a genuine user/team *preference* (house style, commit format, git policy), it
  stays regardless — preference is exactly what this file is for. Flag it only when the
  rule was a guardrail against a failure mode rather than an expression of taste.
- Generic advice not specific to the project ("write tests", "use good names")
- Copy-paste from templates without customization; "TODO" items never completed

# Instruction-File Templates

Applies to `AGENTS.md` (canonical) and `CLAUDE.md` (ideally a `@AGENTS.md` bridge).

## Principles

- **Lightweight**: briefly say what the repo is for; spend the rest of the budget on gotchas
- **Concise**: one line per concept when possible
- **Actionable**: commands should be copy-paste ready
- **Non-derivable**: never restate what the agent can read off the file system or the repo
- **Pointer-first**: depth lives in a skill or `docs/`, referenced from here in a line
- **Current**: reflects actual codebase state

## Recommended Sections (use only what's relevant)

Nearly every file needs Commands and Gotchas. The rest are situational — an empty
section is worse than a missing one.

### Commands
```markdown
## Commands
| Command | Description |
|---------|-------------|
| `<command>` | <description> |
```

### Entry points
A short **map**, not an inventory. Name the few files someone must find to start, and
stop. A directory tree belongs nowhere in this file — the agent can list the directory.
```markdown
## Entry points
- `<path>` — <what starts / lives here>
```

### Gotchas
The highest-value section. Usually the longest one.
```markdown
## Gotchas
- <non-obvious thing that causes issues>
```

### Conventions
Only conventions that **differ from the tool's defaults**. A convention the formatter or
linter already enforces is noise here — enforce it in the tool, not in prose.
```markdown
## Conventions
- <convention that differs from the default, and why>
```

### Environment
```markdown
## Environment
Required:
- `<VAR_NAME>` - <purpose>
Setup:
- <setup step>
```

### Testing
```markdown
## Testing
- `<test command>` - <what it tests>
```

### Further reading
The progressive-disclosure hook: route to depth instead of inlining it.
```markdown
## Further reading
- <topic> → `<skill name>` skill / `docs/<file>.md`
```

## Project Templates

### Minimal
```markdown
# <Project Name>
<One-line description>

## Commands
| Command | Description |
|---------|-------------|
| `<command>` | <description> |

## Gotchas
- <gotcha>
```

### Package/Module (monorepo)
```markdown
# <Package Name>
<Purpose>

## Usage
```
<import/usage example>
```

## Notes
- <important note that isn't obvious from the exports>
```
Skip a "Key Exports" list — the agent reads the index/barrel file for that.

### Monorepo Root
```markdown
# <Monorepo Name>
<Description>

## Packages
| Package | Description | Path |
|---------|-------------|------|
| `<name>` | <purpose> | `<path>` |

## Commands
| Command | Description |
|---------|-------------|
| `<command>` | <description> |

## Cross-Package Patterns
- <shared pattern that no single package reveals>
```
The package table earns its place only when the mapping from name to purpose isn't
obvious from the directory names — otherwise cut it.

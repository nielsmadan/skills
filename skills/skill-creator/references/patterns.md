# Skill Patterns & Resources

Reference material for skill design decisions. Read this when planning a skill's architecture, choosing resource types, or organizing content for progressive disclosure.

## Resource Types

### scripts/

Executable code (Python, Bash, etc.) for tasks requiring deterministic reliability.

**When to use:**
- The same code gets rewritten repeatedly across invocations
- Deterministic reliability is needed (code > language instructions)
- Complex operations that are error-prone when generated each time

**Examples:** `scripts/rotate_pdf.py`, `scripts/validate.sh`, `scripts/export_data.py`

**Notes:**
- Token-efficient: can be executed without loading into context
- May still need to be read by Claude for patching or environment-specific adjustments
- Always test scripts by running them before finalizing

### references/

Documentation loaded into context as needed to inform Claude's process.

**When to use:**
- Detailed information Claude should reference while working
- Content that makes SKILL.md too long (approaching 5,000 words)
- Domain-specific knowledge that only applies in certain scenarios

**Examples:** `references/schema.md` for database schemas, `references/api-docs.md` for API specs, `references/policies.md` for company rules

**Guidelines:**
- Keep references one level deep from SKILL.md (no nested subdirectories)
- For files >100 lines, include a table of contents at the top
- If files are >10k words, include grep search patterns in SKILL.md so Claude can find relevant sections
- Information should live in either SKILL.md or references, not both
- Reference from SKILL.md with clear instructions on when to read each file

### assets/

Files used in the output Claude produces, not loaded into context.

**When to use:**
- Templates, images, icons, fonts needed in final output
- Boilerplate code that gets copied/modified
- Brand assets or sample documents

**Examples:** `assets/logo.png`, `assets/template.pptx`, `assets/hello-world/` (project boilerplate)

## Progressive Disclosure Patterns

Skills use three loading levels:

1. **Metadata** (name + description) — Always in context (~100 words)
2. **SKILL.md body** — Loaded when skill triggers (<5k words)
3. **Bundled resources** — Loaded as needed by Claude (unlimited)

Keep SKILL.md focused on core instructions. Split content when approaching the size limit. When splitting, reference files from SKILL.md with clear guidance on when to read them.

### Pattern 1: High-level guide with references

Best for skills with extensive reference material (API docs, style guides).

```markdown
# PDF Processing

## Quick start
Extract text with pdfplumber:
[core code example]

## Advanced features
- **Form filling**: See `references/forms.md` for complete guide
- **API reference**: See `references/api.md` for all methods
- **Examples**: See `references/examples.md` for common patterns
```

Claude loads each reference file only when that feature is needed.

### Pattern 2: Domain-specific organization

Best for skills spanning multiple domains or frameworks. Organize by domain to avoid loading irrelevant context.

```
bigquery-skill/
├── SKILL.md (overview + navigation)
└── references/
    ├── finance.md (revenue, billing metrics)
    ├── sales.md (opportunities, pipeline)
    └── product.md (API usage, features)
```

When a user asks about sales metrics, Claude only reads `references/sales.md`.

Works equally well for multi-framework skills:

```
cloud-deploy/
├── SKILL.md (workflow + provider selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

### Pattern 3: Conditional details

Best for skills where most users need basics but some need advanced features.

```markdown
# DOCX Processing

## Creating documents
Use docx-js for new documents. See `references/docx-js.md`.

## Editing documents
For simple edits, modify the XML directly.
**For tracked changes**: See `references/redlining.md`
**For OOXML details**: See `references/ooxml.md`
```

## Degrees of Freedom

Match the level of specificity to the task's fragility and variability:

**High freedom** (text-based instructions): Use when multiple approaches are valid, decisions depend on context, or heuristics guide the approach.
- Example: "Choose an appropriate data visualization for the user's dataset"

**Medium freedom** (pseudocode or parameterized scripts): Use when a preferred pattern exists but some variation is acceptable.
- Example: "Use this template but adjust the styling to match the project's conventions"

**Low freedom** (exact scripts, few parameters): Use when operations are fragile, consistency is critical, or a specific sequence must be followed.
- Example: `scripts/rotate_pdf.py --input {file} --degrees {angle}`

Think of Claude exploring a path: a narrow bridge with cliffs needs specific guardrails (low freedom), while an open field allows many routes (high freedom).

---
name: review-logs
description: Analyze Claude Code session transcripts for failure patterns and suggest fixes. Triggers "review logs", "session analysis", "failure patterns".
argument-hint: '[--days N] [--project <name>] [--verbose]'
effort: medium
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Review Logs

Scan recent Claude Code session transcripts for recurring failure patterns and generate actionable recommendations.

## Review grading

Use only these finding priorities, in descending order:

- **Critical Issues (Must Fix):** a verified path causes data loss, a security failure, a materially
  wrong operation, or makes a core workflow unusable without reasonable recovery.
- **Improvements (Should Fix):** an ordinary supported workflow demonstrably fails or repeatedly
  imposes substantial friction, or a concrete design defect creates meaningful maintenance cost.
- **Suggestions (Nice to Have):** a worthwhile improvement with small practical impact, including
  optional polish, local simplification, and rare recoverable edge cases.

Grade the demonstrated consequence, realistic reachability, and available recovery against project
priorities. A category, missing convention, hypothetical future problem, or confidence that a claim
is true does not set its priority. Do not assign automatic severity floors or ceilings. Keep
unverified claims in validation gaps, outside the graded finding count; distinguish suggestions
from defects. For plans, trace the consequence if implemented and state the assumptions.

Use the short labels **Must Fix**, **Should Fix**, and **Nice to Have** in summaries and ledgers.
Keep effort, verification status, user-facing change size, and tool/vendor diagnostic ratings
separate. When called by `code-review`, return its requested evidence and impact fields; the parent
owns scoring and final triage. Otherwise apply this rubric directly. Omit empty priority sections.

## Usage

```
/review-logs
/review-logs --days 7
/review-logs --project juggler
/review-logs --days 30 --verbose
```

## Gotchas
- The `--project` filter is case-sensitive and must exactly match the directory name. `--project MyApp` vs `my-app` gives zero results with no indication of the mismatch.
- In repos with read-only git policies, every blocked `git add`/`git commit` appears as a failure, dominating results and obscuring real problems. Filter known-policy denials from the output.

## Workflow

### Step 1: Parse Arguments

Extract from `$ARGUMENTS`:
- `--days N` — lookback window (default: 14)
- `--project <name>` — filter to a specific project
- `--verbose` — include problematic session IDs for manual review

### Step 2: Run Extraction Script

Find the script using Glob:

```
Glob pattern: **/review-logs/scripts/extract_signals.py
Path: ~/.claude
```

Run the extraction with the discovered path:

```bash
python3 <discovered-path>/extract_signals.py --days <N> [--project <name>] --output /tmp/review-logs-output.json
```

### Step 3: Read and Analyze Output

Read `/tmp/review-logs-output.json` and present findings in severity order:

| Category | What to Present |
|----------|-----------------|
| High-frequency retry loops | What's making the model stuck; suggest CLAUDE.md guidance to prevent it |
| Permission denials (unexpected) | Suggest specific `settings.json` allowlist additions with exact JSON |
| Top failing commands | Distinguish fixable patterns from expected failures |
| Misbehavior patterns | Suggest CLAUDE.md rules or hook scripts |
| Error distribution by project | Where problems concentrate |
| Problematic sessions | Only with `--verbose`; session IDs for manual review |

Grade verified recommendations using Review grading; frequency alone is not severity.
Keep distribution statistics and session listings separate from findings.

### Step 4: Generate Recommendations

For each finding, produce a **concrete fix** — not vague advice. Examples:

**Permission denial fix:**
> Add to `settings.json` allowlist:
> ```json
> "Bash(npm run build:*)"
> ```

**Retry loop fix:**
> Add to `CLAUDE.md`:
> ```
> When X fails, do not retry. Instead, check Y first.
> ```

**Misbehavior fix:**
> Add to `CLAUDE.md`:
> ```
> Do not use `gh api` for issue comments. Use `gh issue view <num> --comments` instead.
> ```

### Step 5: Summary

End with a quick stats line:

```
Scanned {N} sessions across {M} projects ({date_range}). Found {errors} errors, {retries} retry loops, {denials} permission denials.
```

## Examples

**Basic 14-day scan:**
```
/review-logs
```
Typical output:
```
## Improvements (Should Fix)

### Repeated build retries
1. `npm run build` retried 4+ times in 6 sessions — model keeps re-running after TypeScript errors instead of fixing them
   → Add to CLAUDE.md: "When `npm run build` fails with type errors, fix the type errors before re-running."

### Permission denials blocking the normal workflow
1. `Bash(docker compose up)` denied 12 times across 4 sessions
   → Add to settings.json allowlist: "Bash(docker compose *)"

Scanned 47 sessions across 3 projects (2026-02-05 to 2026-02-19). Found 31 errors, 3 retry loops, 14 permission denials.
```

**Project-filtered scan with longer window:**
```
/review-logs --days 30 --project my-app --verbose
```

## Troubleshooting

**No sessions found:**
- Check `--days` value — default is 14, increase if sessions are older
- Check `--project` filter — must match the project directory name exactly (case-sensitive)
- Verify sessions exist at `~/.claude/projects/`

**Script not found:**
- The extraction script lives at `<skill-dir>/scripts/extract_signals.py`
- If Glob finds nothing, the skill may not be installed — re-clone or copy the `review-logs` skill folder into `~/.claude/*/claude/skills/`

**Output too noisy:**
- Expected failures (e.g., git write commands blocked by read-only policy) can dominate results
- Use `--project` to narrow scope to the project you care about
- The script already applies top-N limits, but very active users may still see long output

## Notes

- The extraction script uses only Python stdlib — no dependencies to install
- Sessions are at `~/.claude/projects/*/UUID.jsonl`
- The script scans only that live tree, so sessions rotated out by retention silently do not appear — a "Scanned N sessions" line can be a bounded window, not the full history. Point the `CLAUDE_DIR` constant in `extract_signals.py` at a different root to scan an archived copy.
- Script filters by file mtime before opening files, so large directories are fast
- Output is capped at ~200-400 lines via top-N limits and truncation

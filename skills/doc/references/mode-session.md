# Session Mode (`--session`)

**Invocation:** `doc --session [--md <conversation.md>] [--report <file>]`

Integrate the durable knowledge from one work session into the project's docs. Without
`--md`, use the current conversation and its available tool results. When supplied, `--md`
selects a rendered conversation (plain markdown of USER/ASSISTANT turns); do not silently
mix in the current session's environment or results. You do NOT read Claude Code `.jsonl`
files here. Capture does not depend on a code diff or rerun completed tests.

Extract and place five kinds of knowledge, using the SAME layout and conventions as
`--update`/`--generate` (see `references/principles.md`):

1. **Gotchas** — pitfalls, surprises, "things we ran into" → the `## Gotchas` section of
   the most relevant module/feature doc.
2. **Decision rationale** — why a product/tech decision was made → the `## Why` section.
3. **Behavior changes** — what the session actually changed → refresh the affected
   `## How it works (current state)` sections.
4. **External findings** — what we learned about a *dependency, platform, harness or external
   API* by probing it: a behavior that contradicts its docs, a version-specific quirk, a
   limit we hit → `docs/reference/<subject>.md`. Sessions are the main source of these, and
   the reason the bucket exists: the finding cost an experiment here and will otherwise be
   re-established from scratch next time. Carry the **date and the version probed** across
   from the session, plus how it was probed; if the session only read upstream's docs, that
   is a *documented* claim with a link, not a verified one. Correct-usage conventions for one
   library go to `library-docs` / `library-use` instead.
5. **Occasional manual tests** — performance measurements, restore drills, compatibility
   experiments, and other test operations outside the routine automated suite →
   `docs/tests/<name>/`. Read [manual-tests.md](manual-tests.md) and preserve both the
   reusable procedure and a dated run record. Routine suite/CI runs do not qualify just
   because someone launched them manually. Keep missing historical details explicitly
   unrecorded rather than reconstructing them from today's checkout.

## Rules

- Find the right target docs via `docs/overview.md` and the existing tree. Prefer
  augmenting existing docs over creating new ones.
- **Never touch `docs/product/`** (owned by `review-product`).
- Only record durable, project-specific knowledge — skip transient chatter and
  anything already documented. It is fine to conclude there is nothing worth adding.
- **Preview** the proposed edits to the user and apply on confirmation. Leave changes
  **uncommitted** (the user commits).
- **Fallback:** if the repo has no `docs/`, qualifying manual tests still go directly into
  `docs/tests/<name>/`. For other knowledge without a suitable home, write a single
  `docs/session-harvests/<name>.md`; derive the name from the transcript filename or the
  current session's topic. Link test records rather than duplicating them in the harvest.
- **Report:** if `--report <file>` is given, write the list of doc files you created or
  edited to it, one path per line (repo-relative). If nothing was integrated, write an
  empty file. This is how the caller records what was harvested.

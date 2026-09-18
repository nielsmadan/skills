# Documentation cleanup

Cleanup is complete when useful knowledge has a canonical home and the superseded files
are removed. Apply this during assess and to cleanup findings selected from review.

## Define the retained set

Use the project's explicit documentation rules first, then the chosen profile in
[principles.md](principles.md). When the user requests the standard layout, treat legacy
folder references in project instructions (such as `docs/prd/`) as migration candidates,
not a reason to preserve that layout. Include the instruction-reference updates in the
plan; retain a legacy layout only when the user explicitly chooses it. Edit generated
instructions through their authoritative source.

State the intended destinations in the plan. The set is
the doc types the repo needs and the files with a distinct purpose within them; it is
not a filename whitelist. A Lean flow doc needs to earn its place even when its path fits.

- Keep the profile's warranted docs plus justified `reference/`, `tests/`, and `user/`
  content. Root entry points and contributor docs follow the project's conventions.
- Preserve ADRs, incident records, and manual test runs with their evidence as history.
  Extracting a lesson does not make its historical source disposable. Classify by content
  and lifecycle, including historical records found outside the standard folders.
- Identify separately owned docs (`product/`, `explain/`, published sites), generated
  outputs and their sources, active plans, and supporting assets before proposing removals.
  These are outside automatic cleanup. Edit generated documentation through its owner.
- Include legacy buckets such as `docs/prd/` and `docs/api/`, redundant guides, exhaustive
  code catalogs, temporary session harvests, and completed scratch plans as candidates.
  An unfamiliar directory name alone is insufficient evidence for deletion.

## Extract, verify, remove

1. **Inventory the scope.** Inspect the actual files, including known gitignored scratch
   such as `docs/superpowers/`; a tracked-file list misses it. A scoped run cleans its
   selected area; a wider structural finding belongs in the plan. Inspect symlink targets
   and ownership without traversing into another repo or deleting a shared target.
2. **Read every candidate before proposing its removal.** Identify useful behavior,
   rationale, gotchas, external findings, procedures, and evidence. Map each unique item
   to an existing canonical doc or a warranted new doc in the retained set. Name content
   that is already covered, obsolete, or cheaply derivable; an empty extraction is valid
   when nothing useful remains. Resolve conflicting claims against code or evidence;
   preserve uncertainty and original verification dates rather than inventing certainty.
3. **Plan each migration and removal together.** Show `source → content to preserve →
   destination → file to remove`, with a reason for retaining any exception. Include
   incoming links and required assets. Assess/review use their existing plan approval;
   an approved cleanup request already authorizes its listed removals. Do not add another
   confirmation. If ownership, an active plan, or useful content has no clear resolution,
   retain that candidate and explain what decision is needed; continue the other items.
4. **Write and verify destinations first.** Merge useful content without copying stale
   catalogs or duplicating existing prose. Apply the destination's lifecycle and evidence
   rules. Check every extracted item against the source, then repair incoming links,
   anchors, indexes, instruction-file pointers, and document-relative asset paths.
5. **Remove the superseded files.** Delete only the reviewed, authorized sources once
   their useful content and references are handled. Remove emptied directories; never
   recursively delete a folder containing unreviewed files. Completed scratch plans and
   fully integrated session harvests can be removed; retain plans still driving work.
6. **Verify completion.** Re-inventory the scope, check destinations and links, and search
   for references to removed paths, including tracked and known ignored documentation.
   Report what was extracted, where it lives, which files were removed, and any retained
   exceptions or blockers. Remaining approved candidates mean cleanup is unfinished.

## Other modes

- `--review` includes cleanup findings in its scoped assessment and applies selected ones
  with this workflow.
- `--update` reports scoped cleanup candidates with migration/removal details; apply them
  when cleanup is already authorized, otherwise include them in the proposed follow-up.
- `--generate` and `--session` use canonical destinations from the retained set. Their
  targeted writes do not implicitly authorize removing unrelated documentation.

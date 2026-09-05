# Occasional Manual Test Records

Use `docs/tests/` (plural) for test operations run manually from time to time: performance
measurements, restore drills, compatibility experiments, or other checks outside the routine
automated suite. A scripted operation qualifies; cadence and purpose decide. Running the
normal unit/integration/E2E suite by hand does not qualify, and routine CI or scheduled
benchmark runs do not get records here.

## Layout

Keep every qualifying operation's documentation and run records together:

```text
docs/tests/<name>/
  README.md
  runs/
    YYYY-MM-DD-<label>.md
```

Use a stable, descriptive name such as `checkout-load` or `backup-restore`. Reuse an existing
operation's directory. If its docs already live under `docs/perf/` or another location, move
that operation into `docs/tests/` when it is in scope, preserving history and updating inbound
links. Do not create a second copy. Add an index only when navigation needs one; run count
alone does not justify an index or a heavier doc profile.

Keep runnable scripts and fixtures in the project's existing test/script locations and link
them from the procedure. Preserve any ad hoc script or input needed to repeat the operation
before its temporary copy disappears; do not leave the recipe pointing into a temp directory.
Store small useful outputs beside the run record; link large traces or logs from existing
durable artifact storage. All written procedures and result summaries go under `docs/tests/`.

## Reusable procedure (`README.md`)

Maintain this as the current way to repeat the operation:

- **Purpose and when to run:** the question it answers and the occasion that warrants it.
- **Prerequisites and inputs:** tools/versions, environment, configuration, fixtures or data
  generation, input identifiers/seeds, and any state the operation relies on.
- **Steps:** working directory, exact commands/flags, setup/reset and cleanup, with links to
  scripts instead of copied implementations. Record how required credentials are supplied,
  never their values.
- **Evaluation:** expected behavior, metrics/units, thresholds or comparison criteria, and
  limitations that affect interpretation.
- **Recorded runs:** links to dated results. If a run is the comparison baseline, identify
  it explicitly here and link it rather than duplicating its measurements.

## Dated run (`runs/YYYY-MM-DD-<label>.md`)

Create a separate record for each meaningful execution, including failures. Use a time or
sequence suffix when needed to avoid overwriting another run on the same date. If the run
date is missing, use `undated-<label>.md` and state the capture date separately. Record:

- **Identity:** when the test ran, its purpose, code revision, and relevant local changes.
  A commit alone does not identify modified code; preserve the relevant patch or another
  durable identifier when available.
- **Actual setup:** environment/tool versions, inputs and configuration used, exact invocation,
  and any deviations from the procedure. Link the procedure's revision or preserve its
  run-specific steps so later README edits do not erase how this run was performed.
- **Results:** observations or measurements with units, exit status/failures, and links to
  raw evidence. Distinguish actual results from expected values and explanations.
- **Conclusion:** what the evidence supports, limitations, and any comparison to a named
  prior run. Record relevant setup differences before interpreting a change as a regression
  or improvement.

For performance runs, include hardware, build mode, dataset/workload, concurrency, duration
or iteration count, warmup, repetitions, and measurement/aggregation method. Reuse comparable
settings for before/after measurements; record deliberate changes explicitly.

## Capture and maintenance

- Capture from the current conversation or supplied transcript/output. Only record what that
  evidence establishes. Mark missing dates, revisions, settings, or results as **not recorded**;
  today's environment or capture date cannot stand in for the historical run's setup.
- Saving an existing run does not execute the test again. Explain any missing prerequisite
  for repeating it, without filling gaps through an unrequested rerun.
- `README.md` is live: update commands and prerequisites when they change. `runs/` and its
  evidence are historical: never rewrite them to match current code or replace an old result
  with a new one. Fix navigation links as needed; correct a factual error with a dated
  addendum that preserves the original observation.
- Re-capturing the same session should reuse its existing record. Append newly recovered
  evidence with its provenance instead of inventing a second execution.
- A durable finding about an external tool can also belong in `docs/reference/`; link the
  test record as evidence rather than copying the procedure and results into both places.

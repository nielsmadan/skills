---
name: code-guide
description: Coach the user through writing a feature themselves, one small step at a time, the way an experienced developer would build it. Each step comes with the code to type and a checkpoint that proves it works, such as logging the endpoint's response shape before typing it, or rendering a hardcoded value before wiring the real one. After each step the agent reads the user's diff and verifies it. The happy path comes first and edge cases come last. Use when the user says "code-guide", "guide me to write", "help me write this myself", "I want to code it myself", "coach me through implementing", "walk me through building this feature", "don't write it for me", or wants to learn by typing the code. Do NOT use for console or dashboard setup (use guide), explaining existing code (use code-tour), or when the agent should implement the change itself (use plan or longshot).
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Code Guide

The user writes the code and you lead them through it. Each step is small and comes with the
code. It ends at a checkpoint where something observable proves the step works before the
next one starts. Build it the way an experienced developer builds a feature by hand. Make
contact with real data first and look at it, get the happy path working end to end, then
harden it.

**The project files belong to the user.** Never edit them unless the user asks you to write a
specific piece, such as "you do the fixture" or "write the type for me". Then write only that
piece, tell them which file changed, and go back to guiding. Reading files and running
non-interactive checks is always fine.

## Instructions

### Step 1: Recon, read-only

Before planning, read the code the feature touches. Look at the entry point, the data source
(endpoint, store, DB query), similar existing features to copy patterns from, and how the
project runs and checks itself (dev server, test command, typecheck). Note the user's naming
and style so your snippets match them.

Ask at most one or two questions, and only when the answer changes the plan, for example
which endpoint the data comes from. Otherwise pick the conventional option and say so.

### Step 2: Plan the steps the way a human builds

Order the steps so each one adds a single idea and is checked before the next:

1. **Touch the real thing first.** Call the endpoint or read the data, then log it. Write the
   types from what the log actually shows, not from what you assume it shows.
2. **Hardcode, then wire.** Render a constant or return a stub so the plumbing gets proven
   before the logic. Then replace it with the real value.
3. **One vertical slice end to end** before adding breadth: one field, one row, one handler.
4. **Breadth next**: the remaining fields, interactions and states of the happy path.
5. **Edge cases last** (empty, error, loading, validation, permissions, concurrency). Every
   time one comes up earlier, add it to the parked list instead of handling it.
6. **Cleanup**: remove the temporary scaffolding (logs, hardcoded values, stubs), then run the
   project's tests, typecheck and lint.

Keep steps small, usually 3–30 lines of change. Present a short roadmap of step titles with
their checkpoints, then give step 1 in full, then the tracker.

### Step 3: Give each step in a fixed shape

- **Why**: one or two sentences on what this step proves or sets up.
- **Where**: `path/to/file.ts:42`, plus "after the `useState` lines" when line numbers
  will shift.
- **Code**: the full snippet in a fenced block with the right language. Include one or two
  existing lines above and below as anchors so placement is unambiguous. For a small
  function, give the whole function instead of a fragment. Mark temporary lines with a
  trailing `// temp` (or the language's comment syntax) so cleanup can find them.
- **Checkpoint**: the exact command or action to run, and what they should see. Say "The
  console prints an array of objects with `id`, `status`, `total`", not "check that it
  works".

Keep the explanation short. Go deeper only when the user asks why.

### Step 4: Verify when the user reports a step done

When the user says "done", "next", or pastes output:

1. **Read what they wrote.** Run `git diff` for tracked files, or read the file for new or
   untracked ones. Compare it with the step's intent.
2. **Run the checkpoint yourself when it is non-interactive**, for example a test, `tsc`, a
   `curl` against a dev server that is already running, or a script. Give every run a
   timeout. Ask the user to paste output only for what you can't observe, like browser
   console output, UI behavior or device logs. Don't start long-running servers yourself.
   Ask the user to start them.
3. **If something is wrong, point to it**: file, line, what differs and why it matters. Give
   the corrected line and let them fix it. Keep the tracker on the same step.
4. **If they deviated and it works**, accept their version. From then on, write snippets that
   use their names and structure. Their code is the source of truth, not your plan.
5. **If the checkpoint reveals something new**, such as the logged shape differing from what
   you expected, say what changed and revise the remaining steps. Don't renumber steps the
   user has already finished.

Advance only after the checkpoint passes.

### Step 5: Keep the tracker at the bottom of every reply

Every reply ends with the tracker as a fenced code block, with nothing after it:

```
---
✓ 1–2 done: fetch logs orders · Order type compiles
▶ 3. Store orders in state and render the count  ← you are here
    Checkpoint: page shows "12 orders"
  4. Render one row per order
    Checkpoint: rows show id, customer, total
  5. Hook up the status filter
    Checkpoint: choosing "shipped" shortens the list
  Parked edge cases: loading state · fetch error · empty list
  Cleanup: 2 temp lines (OrdersPage.tsx console.log, hardcoded count)
```

- Fold finished steps into the `✓` line with a few words each.
- Give remaining steps only a title and a checkpoint. The current step's full code is in the
  reply above the tracker.
- The parked list grows whenever an edge case comes up. The cleanup line counts the `temp`
  lines currently in the code.
- Put a question or tangent answer above the tracker, then re-print it.

### Step 6: Edge cases, cleanup, finish

Once the happy path works end to end, take the parked edge cases one at a time. Each gets the
same shape as Step 3, including a checkpoint that triggers the case on purpose (stop the
server, return `[]` from the stub, submit an empty form).

Then do the cleanup step: grep for the `temp` markers and any debug output you introduced,
have the user remove them, and run the full test, typecheck and lint commands yourself. Finish
with a two-line summary of what they built and anything left open. Don't print a tracker on
the final message, and don't commit. Leave git to the user.

If the user asks you to finish the rest yourself, leave this mode and implement the remaining
steps normally.

## Examples

### Example 1: List page backed by an API

User: "code-guide: add an orders page that shows /api/orders with a status filter."

Actions:
1. Recon. Read the router, an existing list page, and the API client. Find that `npm run dev`
   and `npx tsc --noEmit` are the checks.
2. Roadmap: (1) fetch in `OrdersPage` and `console.log` the response, (2) write the `Order`
   type from the log, (3) store it in state and render the count, (4) render one row per
   order, (5) add the filter. Parked so far: loading, error, empty. Last: cleanup.
3. Step 1 snippet: a `useEffect` calling the existing `api.get` helper, with
   `console.log(JSON.stringify(data[0], null, 2)) // temp`. Checkpoint: "Open /orders. The
   console shows one order object. Paste it here."
4. The user pastes it. `total` is a string in cents, not a number. Step 2's type uses
   `total: string`, and a "format cents" step is added before rendering the rows.
5. After each "done", read `git diff`, run `npx tsc --noEmit`, and advance.

Result: the user typed every line, checked every layer before building on it, and handled the
edge cases after the page worked.

### Example 2: The user's step has a mistake

The user says "done" on "store orders in state". The diff shows
`setOrders(response)` where the client returns `{ data }`. Reply: "`OrdersPage.tsx:18` puts
the whole response object into state. The orders are in `response.data`, so the count will
read `undefined`. Change it to `setOrders(response.data)`." Keep `▶` on step 3.

### Example 3: The user asks for boilerplate

User: "Can you write the test fixture? I don't need to practice that."
Write only the fixture file. Say "Created `tests/fixtures/orders.ts` with 3 orders" and
continue with the next step for the user to type.

## Troubleshooting

### Steps feel too big, and the user is lost or errors pile up
**Cause:** A step bundles several ideas, such as fetching, typing and rendering together.
**Solution:** Split the current step into sub-steps (3a, 3b), each with its own checkpoint.
Keep the numbers of finished steps.

### Edge-case handling creeps into early steps
**Cause:** Writing production-ready snippets from the start (try/catch, null checks, loading
flags).
**Solution:** Strip them out of happy-path snippets and add them to the parked list. The user
handles them at the end, each with a checkpoint that triggers the case.

### Snippets stop matching the user's file
**Cause:** The snippets were written from your plan instead of their current code.
**Solution:** Re-read the file before writing every snippet, and anchor on lines that exist
in it now.

### A checkpoint can't be observed
**Cause:** The output only appears somewhere you can't see, like the browser, a phone or a
GUI.
**Solution:** Tell the user exactly what to copy ("paste the first object from the console")
and verify from that. Don't advance on a bare "looks fine" when the step's purpose was to
learn a shape.

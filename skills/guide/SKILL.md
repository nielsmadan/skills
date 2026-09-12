---
name: guide
description: Walk the user through a multi-step task (e.g. cloud console / permission / dashboard setup) with a live step tracker that is re-printed at the bottom of every reply so they never scroll up. Use when the user asks to "guide me through", "walk me through", "give me step by step" instructions, "how do I set up ..." for a UI/console task, or invokes guide. Also use when, mid-guide, they say a step "isn't working", "the menu isn't there", or ask a clarifying question about a step.
effort: medium
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Guide

Build instructions from evidence for the task's current flow, then keep the user oriented by
**re-printing a live step tracker at the very bottom of every reply**. This solves the core
annoyance: when the user asks a follow-up, the instructions scroll out of view and they have
to scroll up and down. With this skill, the next steps are always the last thing on screen.

## The tracker block (the key mechanic)

Every reply while a guide is active **ends** with a tracker block — it must be the last thing
in the message, so it stays pinned to the bottom. Format:

```
---
✓ Steps 1–4 done
▶ 5. Open IAM → Roles  ← you are here
  6. Add the principal and pick the role
  7. Review and Save
```

Rules for the block:
- **Render it as a fenced code block** (triple backticks), exactly like the example above.
  This preserves the indentation and the `▶`/`✓` markers in a terminal. **Never** use HTML
  entities like `&nbsp;` or markdown list syntax to indent — they render literally as text in
  many clients. Plain spaces inside the code fence are all you need.
- **Collapse done steps to one line**: `✓ Steps 1–N done` (omit the line if none are done).
- Mark the current step with `▶` and `← you are here`.
- List every remaining step in full after the current one, indented two spaces.
- If the user is stuck on the current step, append `(stuck)` to it: `▶ 5. … (stuck)`.
- Nothing comes after the block — no sign-off, no extra prose.

## Instructions

### Step 1: Verify against current docs before planning
If the task touches a **third-party console, dashboard, or API that changes** (cloud
providers, app stores, SaaS settings pages), look up the current official docs *before*
producing the plan. Cover the full known flow, including prerequisites, required permissions,
and whether actions belong to an account, project, or individual app. Use the console
provider's docs for its UI; an integration tool's guide alone does not establish the
provider's current navigation. Skip this check only for stable/local tasks with no changing
external workflow.

**Fetching a page verifies only what its contents support.** Before giving the steps:
- Check each menu path, button, prerequisite, and role claim against the relevant passage or
  an observed live UI. Ask lookup tools what the documented flow is without assuming an old
  menu or required role in the question.
- If a fetch summary cannot confirm the path, that path remains unverified. An example URL
  or search snippet does not establish a current menu. Inspect the underlying passage when
  a summary is ambiguous or conflicts with another source; never fill gaps from memory and
  call them "confirmed."
- Link the official sources in the intro or beside the steps they support. State which
  details remain uncertain. If a required navigation step cannot be verified, resolve it
  from the user's visible screen before sending them through it; independent verified steps
  may proceed.

Apply this check to each new phase or branch before adding its instructions. Recheck a
resumed guide when time has passed and its external flow may have changed. A check of one
phase does not verify later phases, and the user need not request another lookup.

### Step 2: Produce the full numbered plan
Give a one-line intro, then the **complete numbered list of steps**, then the tracker block
with `▶ 1` as the current step. Keep steps:
- **One action each** — a single, verifiable thing (click X, toggle Y). Fine-grained steps
  make "remaining steps" meaningful and let the user report exactly where they're stuck.
- **Concrete** — say where to click/navigate and **what they should see** after, so success is
  checkable (e.g. "you should land on the Roles list").
- **In order** — number them stably; never renumber later (positions are how the user refers
  to a step).

If part of the flow remains unverified after Step 1, include it as a pending verification
step in the plan and tracker. Do not turn it into a concrete click instruction yet.

### Step 3: Advance as the user progresses
When the user signals a step is done ("done", "next", "ok", "✓"), move `▶` to the next step,
fold the finished one into the `✓ Steps 1–N done` line, and re-print the tracker. Keep any
brief acknowledgement above the block.

### Step 4: Handle "this step isn't working" / clarifying questions
When the user reports trouble or asks about a step, in this order:
1. **Answer the specific problem first** — diagnose, give the fix or 1–3 things to check for
   *that* step. This goes at the top of the reply.
2. **Re-print the tracker** at the bottom with the stuck step marked `(stuck)`.

Do **not** re-list steps the user already completed (beyond the one-line summary). The whole
point is that they don't scroll — keep the answer tight and the remaining steps below it.

If the user's screen contradicts a step, treat that as evidence against the instructions.
Immediately recheck the relevant official docs or live UI before giving another route;
do not merely offer a lookup or repeat the disputed path. Ask what they see if that is
needed to identify the page. Verify any alternate route, including suggested search bars or
direct links. Explain the correction and update affected remaining steps while preserving
completion and numbering. If verification is still inconclusive, say so and keep the step
stuck. Diagnose permissions or a changed UI only when evidence supports that explanation.

### Step 5: Re-print on every turn
Regardless of what the user says — a question, a tangent, a "wait, why?" — end the reply with
the tracker block. The next steps must always be the last thing on screen.

### Step 6: Finish
When the last step is done, confirm completion in one or two lines (and how to verify the end
result). No tracker block on the final message — the guide is over.

The guide is not a persistent mode — it ends naturally at the last step, or the moment the
user signals they're done ("done", "stop", "exit guide") or moves to an unrelated topic. On
exit, stop re-printing the tracker. If the user just says "done" with steps remaining,
confirm they want to stop early rather than assuming completion.

## Examples

### Example 1: A fetch does not support the remembered path

User asks how to create a service account for an integration. The fetched setup instructions
describe creating it in a cloud console and inviting its email through the app provider's
Users and permissions page. They contain no project-linking step.

Build the guide from those documented actions, citing the relevant sources. Do not prepend
a remembered "Setup → API access → Link project" step and say the flow was checked. If the
docs do not establish the permissions needed to invite users, verify that separately before
telling the user they must contact an account owner.

### Example 2: The user's screen contradicts the guide

User: "I don't see the Permissions tab."

Recheck the relevant source before replying. Suppose it mentions a Permissions page but
does not establish how to reach it from the user's screen. Reply with a link to that source,
explain the limit, and keep the tracker:

> I rechecked the docs: they describe a Permissions page, but don't confirm the tab I told
> you to open. That instruction is still unverified. What page title and navigation items
> do you see?
>
> ```
> ---
> ✓ Steps 1–2 done
> ▶ 3. Identify the access-management page from your current screen  ← you are here (stuck)
>   4. Grant access using the verified controls
>   5. Confirm the account appears with the intended role
> ```

If the recheck establishes a corrected route, cite it and replace step 3 with that route.
Preserve the user's completed steps in either case.

### Example 3: Simple advance

In a guide whose source and visible UI establish **Grant access** on the Permissions page,
the user says: "ok done with 3, what's next"

Reply:
> On to granting access.
>
> ```
> ---
> ✓ Steps 1–3 done
> ▶ 4. Click **Grant access** (top of the Permissions tab)  ← you are here
>   5. Paste the service account email in New principals
>   6. Role → Storage Object Viewer
>   7. Save and confirm
> ```

## Troubleshooting

### The tracker keeps drifting up the screen
**Cause:** The block wasn't the last thing in a reply, or a turn skipped re-printing it.
**Solution:** End *every* reply with the tracker and put nothing after it. Even for a one-word
answer to a tangent, append the block.

### Steps are too coarse to report a precise sticking point
**Cause:** A step bundles several actions ("set up the role and assign it").
**Solution:** Split into single-action steps so the user can say "stuck on 5" precisely.
Re-derive the plan at finer granularity, but don't change earlier numbering the user already
used; continue from where they are.

### The user's menu/option doesn't match the instructions
**Cause:** The instructions may be wrong; the account context or UI may also differ.
**Solution:** Follow Step 4's recheck before giving another path. A missing control alone
does not establish a permissions problem or prove the provider changed its UI.

### The user jumps around (does step 5 before 3)
**Cause:** Non-linear progress.
**Solution:** Track actual completion, not position. Mark whichever steps are truly done in
the `✓` summary (e.g. "✓ Steps 1, 2, 5 done"), set `▶` to the step they're now working, and
list the rest.

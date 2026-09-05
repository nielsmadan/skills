---
name: guide
description: Walk the user through a multi-step task (e.g. cloud console / permission / dashboard setup) with a live step tracker that is re-printed at the bottom of every reply so they never scroll up. Use when the user asks to "guide me through", "walk me through", "give me step by step" instructions, "how do I set up ..." for a UI/console task, or invokes guide. Also use when, mid-guide, they say a step "isn't working", "the menu isn't there", or ask a clarifying question about a step.
effort: medium
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Guide

Deliver step-by-step instructions for a hands-on task and keep the user oriented by
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
producing the plan — don't rely on memory of menu names or flows. UIs and even whole
workflows get reshuffled or retired (e.g. a "link project" step that no longer exists). A
60-second doc check up front catches these before the user hits a missing menu mid-guide.
Skip this only for stable/local tasks (shell setup, file edits) where there's no moving UI.
Note in the intro when the plan reflects a doc you just checked, and still invite correction
if their screen differs.

### Step 2: Produce the full numbered plan
Give a one-line intro, then the **complete numbered list of steps**, then the tracker block
with `▶ 1` as the current step. Keep steps:
- **One action each** — a single, verifiable thing (click X, toggle Y). Fine-grained steps
  make "remaining steps" meaningful and let the user report exactly where they're stuck.
- **Concrete** — say where to click/navigate and **what they should see** after, so success is
  checkable (e.g. "you should land on the Roles list").
- **In order** — number them stably; never renumber later (positions are how the user refers
  to a step).

If the target UI changes often or you're unsure it's current, say so up front and offer to
look it up rather than guessing menu names.

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

If a menu/option genuinely isn't where expected, consider that the UI may have changed: offer
an alternate path, ask what they *do* see, or look up the current UI before insisting.

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

### Example 1: Cloud permission setup, with a snag mid-way

User says: "Guide me through giving a service account read access to a GCS bucket."

First reply — intro + full plan + tracker:
> Here's the path in the Google Cloud console:
>
> 1. Open the Cloud console and pick the right project (top bar).
> 2. Go to Cloud Storage → Buckets, click the bucket.
> 3. Open the **Permissions** tab.
> 4. Click **Grant access**.
> 5. In **New principals**, paste the service account email.
> 6. In **Role**, choose *Storage Object Viewer*.
> 7. Click **Save**, then confirm the principal appears in the list.
>
> ---
> ▶ 1. Open the Cloud console and pick the project  ← you are here
>   2. Cloud Storage → Buckets, click the bucket
>   3. Open the Permissions tab
>   4. Click Grant access
>   5. Paste the service account email in New principals
>   6. Role → Storage Object Viewer
>   7. Save and confirm

User: "I'm on the bucket but I don't see a Permissions tab."

Reply — answer first, then tracker with `(stuck)`:
> It's there but easy to miss: the tabs are along the top of the bucket detail page
> (Objects · Configuration · **Permissions** · Protection). If you only see *Objects*, the
> page is still loading the bucket detail — make sure you clicked the bucket **name**, not its
> checkbox. Still missing? You may lack `storage.buckets.getIamPolicy` on the bucket; tell me
> what tabs you do see.
>
> ---
> ✓ Steps 1–2 done
> ▶ 3. Open the Permissions tab  ← you are here (stuck)
>   4. Click Grant access
>   5. Paste the service account email in New principals
>   6. Role → Storage Object Viewer
>   7. Save and confirm

Result: the user fixes step 3 and the remaining steps are right there at the bottom — no
scrolling back up to find where they were.

### Example 2: Simple advance

User: "ok done with 3, what's next"

Reply:
> On to granting access.
>
> ---
> ✓ Steps 1–3 done
> ▶ 4. Click **Grant access** (top of the Permissions tab)  ← you are here
>   5. Paste the service account email in New principals
>   6. Role → Storage Object Viewer
>   7. Save and confirm

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
**Cause:** The console UI changed, or they're on a different version/region/tier.
**Solution:** Don't insist on the wording. Ask what they actually see, offer the alternate
path, or look up the current UI. Update the relevant remaining step, keep the numbering.

### The user jumps around (does step 5 before 3)
**Cause:** Non-linear progress.
**Solution:** Track actual completion, not position. Mark whichever steps are truly done in
the `✓` summary (e.g. "✓ Steps 1, 2, 5 done"), set `▶` to the step they're now working, and
list the rest.

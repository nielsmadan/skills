---
name: deslop
description: Copy-edit text to strip AI/LLM writing tells ("slop") and make it read as human-written — overused words (delve, showcase, robust), significance-inflation phrases ("stands as a testament to", "plays a pivotal role"), scene-setting openers ("in today's fast-paced world"), hedging, em-dash overuse, rule-of-three, and "it's not X, it's Y" parallelism. Use when asked to "deslop", "de-slop", "remove AI tells", "make this sound less like AI/ChatGPT", "make this sound human", or copy-edit a draft (.md, .txt, prose, emails, docs) that reads as machine-generated.
argument-hint: "[file path or pasted text] [--report]"
effort: medium
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Deslop

Copy-edit text to remove LLM writing patterns so it reads as human-written.

## The core idea

Slop is text engineered to *sound* authoritative while saying little: inflated
vocabulary, formulaic significance-frames, reflexive hedging, and mechanical
structure. The job is **not** find-and-replace from a synonym table — that just
makes *differently* robotic text. The job is to **delete the inflation and
force a concrete specific**, while preserving the author's meaning and voice.

Two rules that override everything else:
1. **Density, not isolated words.** One "crucial" on a page is fine. Act on
   clusters and reflexive use.
2. **Don't over-edit.** Legitimate uses stay; voice and meaning are preserved;
   no facts change. When in doubt, lighter edit + flag it.

## Flags

- `--report` — detect and list tells with locations; do **not** rewrite. Use
  when the author wants to edit themselves.
- Default — rewrite the text, removing tells, then summarize what changed.

## Workflow

### Step 1: Get the text and mode

- **File path in the prompt** (`.md`, `.txt`, etc.) → read it.
- **Text pasted in the conversation** → operate on that.
- **Neither** → ask the user to paste the text or give a path. Don't proceed
  without input.
- `--report` present → detection-only mode (Step 4 only).

### Step 2: Read the full catalog

Read `references/patterns.md`. It holds the word lists, phrase lists,
structural tells, and — critically — section 4 "What NOT to touch". Don't skip
it; the anti-over-editing guidance is half the skill.

### Step 3: Run the detector for coverage

```bash
python3 scripts/flag.py <file>        # or:  cat file | python3 scripts/flag.py -
```

It scans for known tells and prints each with a line number and category, plus
em-dash density. It **over-flags on purpose** — every hit is a *candidate*, not
a verdict. Use it so nothing is missed in long text; then judge each in context
yourself. (For pasted text, write it to a scratch file first, or just scan by
eye against the catalog for short passages.)

### Step 4: Edit (or report)

**Report mode (`--report`):** present the detector's findings grouped by
category, add any structural/tonal tells the script can't catch (rule-of-three,
both-sides non-conclusions, copula avoidance, over-bolding), and stop. Don't
rewrite.

**Default (rewrite) mode:** for each candidate, decide in context:
- **Delete** the inflation when it adds nothing ("plays a pivotal role in" →
  state what it does, or cut). This is the most common fix.
- **Replace** with a concrete specific or a plain word when one fits — but
  **vary** replacements; don't turn every "delve" into "explore".
- **Keep** legitimate/technical/literal uses and intentional voice.
- **Restructure** the tics: collapse rule-of-three to one precise word, undo
  "not X, it's Y" to the positive claim, restore normal punctuation for
  overused em-dashes, turn copula-avoidance ("serves as") back into "is",
  cut reflexive "In conclusion"/"Overall" wrap-ups.

Preserve formatting that helps; convert reflexive bolding/emoji-bullets/
over-headed text back to prose where prose reads better.

### Step 5: Output

- **File input:** apply edits and show a concise diff (or write a `*.deslopped`
  copy if the user prefers not to overwrite — ask if unsure for important
  files).
- **Pasted input:** return the cleaned text.
- Then add a short **changelog**: what categories you cut/changed, and — just as
  important — **what you deliberately left** and why (e.g. "kept 'robust' — it's
  the statistical term of art here"). This builds trust and surfaces judgment
  calls for the user to override.

## Examples

### Example 1: Rewrite a draft file

User: "deslop blog-draft.md"

1. Read `blog-draft.md` and `references/patterns.md`.
2. `python3 scripts/flag.py blog-draft.md` → 18 candidates, em-dashes 4.1/1000.
3. Edit: cut the "In today's fast-paced world" opener; "stands as a testament
   to" → "shows"; collapse "powerful, flexible, and intuitive" → "flexible";
   undo two "it's not X — it's Y" constructions; restore commas for 5 of 7
   em-dashes; keep one literal "landscape" (about hiking).
4. Show diff + changelog noting the literal "landscape" was kept.

### Example 2: Report only

User: "run deslop --report on this" + pasted text

Write text to a scratch file, run `flag.py`, present findings grouped by
category with line refs, add the structural tells the script misses, and stop —
no rewrite.

### Example 3: Pasted paragraph

User: "make this sound less like ChatGPT: <paragraph>"

Scan against the catalog (short enough to skip the script), rewrite removing
the tells, return the cleaned paragraph + a one-line note on the main changes.

## Troubleshooting

### The rewrite reads flattened / lost the author's voice
**Cause:** Over-editing — mechanical removal of every flagged word, including
ones that carried tone or precision.
**Solution:** Re-read section 4 of `references/patterns.md`. Act on density, not
every hit; keep intentional register; prefer deleting *empty* inflation over
swapping *every* word. Offer a lighter pass.

### The detector flagged a legitimate word (literal "landscape", "robust" in stats)
**Cause:** The script over-flags by design; it can't see context.
**Solution:** Keep the legitimate use and note it in the changelog. The script
is a coverage net, not a judge — you decide.

### Replacements themselves sound like AI
**Cause:** One-to-one synonym swapping across the whole text creates a new tell
(every "delve" → "explore").
**Solution:** Vary word choice, or — better — delete the inflated frame and
state the concrete point. The catalog's guiding principle is deletion over
substitution.

### Nothing flagged but it still reads like AI
**Cause:** The real signal is structural/tonal (formulaic arcs, both-sides
non-conclusions, even paragraph rhythm, vague claims), which a word list can't
catch.
**Solution:** Apply section 3 of the catalog by judgment: vary sentence length,
land conclusions on a position, replace vague claims with specifics, break the
intro-body-summary template.

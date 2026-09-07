#!/usr/bin/env python3
"""Flag candidate AI writing tells in text — a coverage aid, not a judge.

Scans prose for known single-word, phrase, and structural tells and reports each
with its line number and category. It deliberately OVER-flags: every hit is a
*candidate* for a human to judge in context, never an automatic edit.

Code is not prose. Fenced blocks, inline code, link targets, URLs, HTML tags and
YAML frontmatter are masked out before scanning, so `--not --remotes` and a
literal underscore are not tells.

Project vocabulary is not slop. Terms listed in a `.deslopignore` (nearest one
found walking up from the file) or in `$XDG_CONFIG_HOME/deslop/ignore` are
suppressed and reported as a count, so a domain term of art stops costing
judgment on every run.

Usage:
    flag.py FILE
    cat FILE | flag.py -
    flag.py --json FILE          # machine-readable output
    flag.py --all FILE           # include low-signal hits on reference docs
    flag.py --genre persuasive FILE
    flag.py --ignore harness,comprehensive FILE
"""
import argparse
import json
import os
import re
import sys

# Single words: strongest signals first, then puffery/verbs. Matched whole-word,
# case-insensitive. Kept intentionally tight to limit noise.
WORDS = [
    # flagship
    "delve", "delves", "delving", "tapestry", "testament", "underscore",
    "underscores", "underscoring", "showcase", "showcases", "showcasing",
    "pivotal", "realm", "intricate", "intricacies", "boasts", "boasting",
    "foster", "fostering", "leverage", "leveraging", "harness", "harnessing",
    "robust",
    # live-era verbs
    "enhance", "enhances", "enhancing", "highlighting", "emphasizing",
    "elevate", "empower", "empowering", "unlock", "unleash", "amplify",
    "streamline", "facilitate", "cultivate", "illuminate", "resonate",
    "embark", "unravel", "elucidate", "encompass", "garner", "bolster",
    "exemplify", "utilize", "utilise",
    # puffery adjectives
    "vibrant", "bustling", "crucial", "essential", "paramount", "integral",
    "profound", "nuanced", "multifaceted", "comprehensive", "holistic",
    "seamless", "ever-evolving", "cutting-edge", "transformative",
    "groundbreaking", "game-changing", "revolutionary", "meticulous",
    "meticulously", "enduring", "unwavering", "invaluable",
    # stiff transitions (sentence-initial caught separately too)
    "furthermore", "moreover", "additionally", "consequently",
    "subsequently", "notably", "nonetheless", "nevertheless",
]

# Multi-word phrases / collocations. Regex, case-insensitive.
PHRASES = [
    r"\bstands? as a testament\b",
    r"\bserves? as a testament\b",
    r"\ba testament to\b",
    r"\bplays? a (?:pivotal|crucial|vital|key|significant) role\b",
    r"\b(?:underscores?|highlights?) the (?:importance|significance)\b",
    r"\b(?:left|leaves) an indelible mark\b",
    r"\bmarks? a (?:turning point|paradigm shift)\b",
    r"\bpaving the way for\b",
    r"\bsetting the stage for\b",
    r"\b(?:valuable|actionable) insights\b",
    r"\bthe (?:multifaceted|intricate|complex) (?:nature|interplay)\b",
    r"\bnavigating the complexit(?:y|ies)\b",
    r"\bshed light on\b",
    r"\bin today'?s (?:fast-paced|digital|ever-evolving|rapidly evolving)\b",
    r"\bin the (?:age|realm) of\b",
    r"\bin the ever-evolving\b",
    r"\bin a world where\b",
    r"\bwhen it comes to\b",
    r"\bat the end of the day\b",
    r"\bnestled in the heart of\b",
    r"\brich (?:cultural heritage|history)\b",
    r"\bstunning natural beauty\b",
    r"\b(?:diverse|rich|vibrant) tapestry\b",
    r"\bunwavering commitment\b",
    r"\bcommitment to excellence\b",
    r"\bseamless integration\b",
    r"\btreasure trove\b",
    r"\bgame[- ]changer\b",
    r"\bin conclusion\b",
    r"\bin summary\b",
    r"\bit'?s worth noting\b",
    r"\bit'?s important to (?:note|remember|consider)\b",
    r"\bit is worth (?:noting|mentioning)\b",
    r"\bneedless to say\b",
    r"\bone might argue\b",
]

# Structural tics. (label, regex)
STRUCTURAL = [
    # A contrastive pivot is required: bare "not X ... it is Y" is ordinary negation.
    ("negative-parallelism", r"\b(?:not|(?:is|are|was|were|do|does|did)n't) (?:just |merely |only |about )?[^.;—]{1,40}[,;—]\s*(?:but|it's|it is)\b"),
    ("negative-parallelism", r"\b(?:not|(?:is|are|was|were|do|does|did)n't) (?:just |merely |only )[^.,;—]{1,40}\s+but\b"),
    ("false-range", r"\bfrom ([^.,;]{1,40}) to ([^.,;]{1,40})\b"),
]

# Evaluative / stance words. Repetition of one of these across a document is a
# framing tic — the writer asserting a judgment rather than showing it. Subject
# nouns repeat legitimately in technical prose; these do not.
STANCE = [
    "honest", "honestly", "genuine", "genuinely", "truly", "obviously",
    "clearly", "simply", "easily", "powerful", "elegant", "elegantly",
    "careful", "carefully", "deliberate", "deliberately", "intentional",
    "intentionally", "crucial", "essential", "important", "critical",
    "significant", "notable", "remarkable", "interesting", "surprising",
    "tricky", "subtle", "straightforward", "seamless", "robust", "thoughtful",
    "sensible", "reasonable", "natural", "naturally", "ideal", "perfect",
    "proper", "properly", "meaningful", "compelling",
]
ECHO_MIN = 3

WORD_RE = re.compile(r"\b(" + "|".join(re.escape(w) for w in WORDS) + r")\b", re.I)
PHRASE_RES = [re.compile(p, re.I) for p in PHRASES]
STRUCT_RES = [(label, re.compile(p, re.I)) for label, p in STRUCTURAL]
STANCE_RE = re.compile(r"\b(" + "|".join(STANCE) + r")\b", re.I)

# Categories that carry little signal in reference documentation, where the
# vocabulary is fixed by the subject rather than chosen for effect.
LOW_SIGNAL_IN_REFERENCE = {"word", "false-range"}


def _blank(text, start, end):
    """Replace a span with spaces, preserving newlines so line numbers hold."""
    span = text[start:end]
    return text[:start] + "".join("\n" if c == "\n" else " " for c in span) + text[end:]


def mask_code(text):
    """Blank out everything that is not prose. Returns (masked_text, code_ratio)."""
    original_lines = text.count("\n") + 1

    # YAML frontmatter: a leading --- block.
    if text.startswith("---\n"):
        end = text.find("\n---", 3)
        if end != -1:
            close = text.find("\n", end + 1)
            text = _blank(text, 0, close if close != -1 else len(text))

    # Fenced code blocks (``` or ~~~), including the fence lines themselves.
    out, in_fence, fence_char, masked_lines = [], False, "", 0
    for line in text.split("\n"):
        stripped = line.lstrip()
        if not in_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
            in_fence, fence_char = True, stripped[0]
            out.append(" " * len(line))
            masked_lines += 1
            continue
        if in_fence:
            out.append(" " * len(line))
            masked_lines += 1
            if stripped.startswith(fence_char * 3):
                in_fence = False
            continue
        out.append(line)
    text = "\n".join(out)

    # Inline code spans, longest runs of backticks first.
    for rx in (re.compile(r"``[^`]+``"), re.compile(r"`[^`\n]+`")):
        while True:
            m = rx.search(text)
            if not m:
                break
            text = _blank(text, m.start(), m.end())

    # Markdown link targets, bare URLs, HTML tags.
    for pattern in (r"\]\([^)\n]*\)", r"https?://\S+", r"<[^>\n]{1,120}>"):
        rx = re.compile(pattern)
        while True:
            m = rx.search(text)
            if not m:
                break
            text = _blank(text, m.start(), m.end())

    return text, (masked_lines / original_lines if original_lines else 0.0)


def load_ignores(path, extra):
    """Collect ignore terms: global config, nearest .deslopignore, --ignore."""
    terms, sources = set(), []

    xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    global_ignore = os.path.join(xdg, "deslop", "ignore")
    for candidate in (global_ignore,):
        if os.path.isfile(candidate):
            terms |= _read_ignore(candidate)
            sources.append(candidate)

    if path and path != "-":
        d = os.path.dirname(os.path.abspath(path))
        while True:
            candidate = os.path.join(d, ".deslopignore")
            if os.path.isfile(candidate):
                terms |= _read_ignore(candidate)
                sources.append(candidate)
                break
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent

    if extra:
        added = {t.strip().lower() for t in extra.split(",") if t.strip()}
        terms |= added
        if added:
            sources.append("--ignore")

    return terms, sources


def _read_ignore(path):
    terms = set()
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.split("#", 1)[0].strip().lower()
                if line:
                    terms.add(line)
    except OSError:
        pass
    return terms


def detect_genre(text, code_ratio):
    """Reference docs state behavior; persuasive pages make a case."""
    if code_ratio >= 0.12:
        return "reference"
    words = max(len(text.split()), 1)
    pitch = len(re.findall(
        r"\b(?:you|your|we|our|why|instead of|compared|versus|vs\.?|better|"
        r"choose|prefer|worth)\b", text, re.I))
    return "persuasive" if pitch / words * 1000 >= 18 else "reference"


def stem(word):
    """Fold adverb and comparative forms so honest/honestly count as one tic."""
    w = word.lower()
    for suffix in ("ly", "ness"):
        if w.endswith(suffix) and len(w) - len(suffix) >= 5:
            return w[: -len(suffix)]
    return w


def find_echoes(prose):
    counts = {}
    for m in STANCE_RE.finditer(prose):
        counts.setdefault(stem(m.group(0)), []).append(m.group(0).lower())
    return {w: forms for w, forms in counts.items() if len(forms) >= ECHO_MIN}


def scan(text, ignores):
    prose, code_ratio = mask_code(text)
    findings, suppressed = [], 0

    for i, line in enumerate(prose.splitlines(), 1):
        hits = []
        for m in WORD_RE.finditer(line):
            hits.append(("word", m.group(0)))
        for rx in PHRASE_RES:
            for m in rx.finditer(line):
                hits.append(("phrase", m.group(0)))
        for label, rx in STRUCT_RES:
            for m in rx.finditer(line):
                if label == "false-range" and m.lastindex == 2:
                    lo, hi = m.group(1).strip().lower(), m.group(2).strip().lower()
                    # "from project to project" is a span; "from 191 to 88" is a
                    # measurement. Only decorative ranges are the tell.
                    if lo == hi or any(c.isdigit() for c in lo + hi):
                        continue
                hits.append((label, m.group(0).strip()))
        for cat, match in hits:
            if match.lower() in ignores:
                suppressed += 1
            else:
                findings.append((i, cat, match))

    em = prose.count("—")
    words_total = max(len(prose.split()), 1)
    echoes = {w: p for w, p in find_echoes(prose).items() if w not in ignores}
    return findings, em, words_total, suppressed, code_ratio, echoes, prose


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="text file, or - for stdin")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--all", action="store_true",
                    help="show low-signal word hits on reference docs too")
    ap.add_argument("--genre", choices=("auto", "reference", "persuasive"),
                    default="auto")
    ap.add_argument("--ignore", default="",
                    help="comma-separated terms to suppress, on top of .deslopignore")
    args = ap.parse_args()

    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    ignores, sources = load_ignores(args.file, args.ignore)
    findings, em, words_total, suppressed, code_ratio, echoes, prose = scan(text, ignores)

    genre = args.genre if args.genre != "auto" else detect_genre(prose, code_ratio)
    demote = genre == "reference" and not args.all
    shown = [f for f in findings if not (demote and f[1] in LOW_SIGNAL_IN_REFERENCE)]
    demoted = len(findings) - len(shown)
    em_per_1k = round(em / words_total * 1000, 1)

    if args.as_json:
        print(json.dumps({
            "genre": genre,
            "prose_words": words_total,
            "code_ratio": round(code_ratio, 3),
            "findings": [{"line": l, "category": c, "match": t} for l, c, t in shown],
            "demoted_low_signal": demoted,
            "suppressed_by_ignore": suppressed,
            "ignore_sources": sources,
            "echoes": {w: len(p) for w, p in echoes.items()},
            "em_dashes": em, "em_dashes_per_1000_words": em_per_1k,
            "total": len(shown),
        }, indent=2))
        return

    print(f"genre: {genre}  ({words_total} prose words, {int(code_ratio * 100)}% code)")
    if sources:
        print(f"ignore: {suppressed} hit(s) suppressed via {', '.join(sources)}")

    by_cat = {}
    for line, cat, match in shown:
        by_cat.setdefault(cat, []).append((line, match))
    for cat in sorted(by_cat):
        print(f"\n## {cat} ({len(by_cat[cat])})")
        for line, match in by_cat[cat]:
            print(f"  L{line}: {match}")

    if echoes:
        print(f"\n## stance-word echo ({len(echoes)})")
        for w, forms in sorted(echoes.items(), key=lambda kv: -len(kv[1])):
            spelling = "/".join(sorted(set(forms)))
            print(f"  {len(forms)}×  {spelling}"
                  "  ← asserting a judgment repeatedly; show it once")

    print(f"\n## em-dashes: {em} total, {em_per_1k}/1000 words"
          + ("  ← high, likely overused" if em_per_1k >= 3 else ""))

    if demoted:
        print(f"\n{demoted} single-word hit(s) hidden: low signal in reference prose."
              " Re-run with --all to see them.")

    total = len(shown) + len(echoes)
    if total:
        print(f"\nTotal candidates: {total}. These are CANDIDATES — judge each in context.")
    elif em_per_1k >= 3:
        print("\nNo word or structural tells. Punctuation density is the only signal here.")
    else:
        print("\nNo obvious tells flagged. (Density is the real signal — read it anyway.)")


if __name__ == "__main__":
    main()

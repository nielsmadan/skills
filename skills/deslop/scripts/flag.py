#!/usr/bin/env python3
"""Flag candidate AI writing tells in text — a coverage aid, not a judge.

Scans for known single-word, phrase, and a few structural tells and reports
each with its line number and category. It deliberately OVER-flags: every hit
is a *candidate* for a human/Claude to judge in context, never an automatic
edit. Legitimate uses will be flagged too — that's expected.

Usage:
    flag.py FILE
    cat FILE | flag.py -
    flag.py --json FILE        # machine-readable output
"""
import argparse
import json
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
    ("negative-parallelism", r"\b(?:it'?s|it is|this is)?\s*not (?:just |merely |only )?[^.,;—]{1,40},?\s*(?:but|it'?s|it is)\b"),
    ("negative-parallelism", r"\bnot (?:just |merely |only )[^.—]{1,40}—\s*(?:it'?s|it is|but)\b"),
    ("false-range", r"\bfrom [^.,;]{1,40} to [^.,;]{1,40}\b"),
]

WORD_RE = re.compile(r"\b(" + "|".join(re.escape(w) for w in WORDS) + r")\b", re.I)
PHRASE_RES = [re.compile(p, re.I) for p in PHRASES]
STRUCT_RES = [(label, re.compile(p, re.I)) for label, p in STRUCTURAL]


def scan(text):
    findings = []
    for i, line in enumerate(text.splitlines(), 1):
        for m in WORD_RE.finditer(line):
            findings.append((i, "word", m.group(0)))
        for rx in PHRASE_RES:
            for m in rx.finditer(line):
                findings.append((i, "phrase", m.group(0)))
        for label, rx in STRUCT_RES:
            for m in rx.finditer(line):
                findings.append((i, label, m.group(0).strip()))
    # em-dash density is a whole-text signal
    em = text.count("—")
    words_total = max(len(text.split()), 1)
    return findings, em, words_total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="text file, or - for stdin")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    findings, em, words_total = scan(text)
    em_per_1k = round(em / words_total * 1000, 1)

    if args.as_json:
        print(json.dumps({
            "findings": [{"line": l, "category": c, "match": t} for l, c, t in findings],
            "em_dashes": em, "em_dashes_per_1000_words": em_per_1k,
            "total": len(findings),
        }, indent=2))
        return

    if not findings and em_per_1k < 3:
        print("No obvious tells flagged. (Density is the real signal — read it anyway.)")
        return

    by_cat = {}
    for line, cat, match in findings:
        by_cat.setdefault(cat, []).append((line, match))
    for cat in sorted(by_cat):
        print(f"\n## {cat} ({len(by_cat[cat])})")
        for line, match in by_cat[cat]:
            print(f"  L{line}: {match}")
    print(f"\n## em-dashes: {em} total, {em_per_1k}/1000 words"
          + ("  ← high, likely overused" if em_per_1k >= 3 else ""))
    print(f"\nTotal candidates: {len(findings)}. These are CANDIDATES — judge each in context.")


if __name__ == "__main__":
    main()

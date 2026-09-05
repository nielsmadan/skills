#!/usr/bin/env python3
"""Stage a subset of hunks from one file's unstaged diff into the git index.

Use when another session ALSO edited a file you edited this session, so a plain
`git add <file>` would sweep in their changes. This stages only the hunks you
name, leaving the rest of the working-tree changes unstaged.

Usage:
    stage-hunks.py <file> <hunk> [<hunk> ...]
    stage-hunks.py <file> --list

`<hunk>` is 1-based into the hunks shown by `git diff -- <file>`. Run with
--list first to see the numbered hunks, decide which are yours, then re-run
with those numbers.

Notes:
  - Operates on the UNSTAGED diff (working tree vs index). Run before staging.
  - Text hunks only. For new/deleted/binary files use plain `git add` / `git rm`.
  - Hunks are anchored to their old-side line ranges (valid against the index),
    so applying a non-contiguous subset is safe.
"""
import subprocess
import sys


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def get_diff(path):
    r = run(["git", "diff", "--", path])
    if r.returncode != 0:
        sys.exit(f"git diff failed for {path}:\n{r.stderr}")
    return r.stdout


def split_diff(diff_text):
    """Return (header, [hunk_str, ...]). header is everything before first @@."""
    lines = diff_text.splitlines(keepends=True)
    header, hunks, cur = [], [], None
    for line in lines:
        if line.startswith("@@"):
            if cur is not None:
                hunks.append("".join(cur))
            cur = [line]
        elif cur is None:
            header.append(line)
        else:
            cur.append(line)
    if cur is not None:
        hunks.append("".join(cur))
    return "".join(header), hunks


def main():
    argv = sys.argv[1:]
    if len(argv) < 2:
        sys.exit(__doc__)
    path = argv[0]
    diff_text = get_diff(path)
    if not diff_text.strip():
        sys.exit(f"No unstaged changes in {path} (already staged, or unchanged).")
    header, hunks = split_diff(diff_text)
    if not hunks:
        sys.exit(f"No text hunks in {path} (binary/mode change?). Use plain git add.")

    if argv[1] in ("--list", "-l"):
        for i, h in enumerate(hunks, 1):
            first = h.splitlines()[0]
            body = "".join(l for l in h.splitlines(keepends=True)[1:])
            print(f"=== hunk {i}: {first}")
            print(body.rstrip("\n"))
            print()
        return

    try:
        want = sorted({int(x) for x in argv[1:]})
    except ValueError:
        sys.exit("hunk numbers must be integers (or use --list)")
    for n in want:
        if n < 1 or n > len(hunks):
            sys.exit(f"hunk {n} out of range (file has {len(hunks)} hunks)")

    patch = header + "".join(hunks[n - 1] for n in want)
    r = run(["git", "apply", "--cached", "--recount", "-"], input=patch)
    if r.returncode != 0:
        sys.exit(f"git apply --cached failed:\n{r.stderr}\n"
                 "The working tree may have shifted. Re-run with --list and retry.")
    print(f"Staged hunk(s) {', '.join(map(str, want))} of {path}.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

ROOTS = {
    "claude": ".claude/skills",
    "codex": ".agents/skills",
    "cursor": ".cursor/skills",
    "droid": ".factory/skills",
    "opencode": ".opencode/skills",
    "pi": ".pi/skills",
}


def fingerprint(folder):
    digest = hashlib.sha256()
    for path in sorted(folder.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            digest.update(str(path.relative_to(folder)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def discover(root, harness):
    directories = list(
        dict.fromkeys([ROOTS[harness], *ROOTS.values(), ".codex/skills"])
    )
    skills = {}
    for directory in directories:
        for entry in sorted((root / directory).glob("codebase-review-*/SKILL.md")):
            name = entry.parent.name
            candidate = {"path": str(entry), "fingerprint": fingerprint(entry.parent)}
            skills.setdefault(name, []).append(candidate)
    return [
        {
            "name": name,
            "path": copies[0]["path"],
            "copies": copies,
            "conflict": len({copy["fingerprint"] for copy in copies}) > 1,
        }
        for name, copies in sorted(skills.items())
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Discover project-local codebase review extensions."
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--harness", choices=ROOTS, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            {
                "root": str(args.root.resolve()),
                "extensions": discover(args.root.resolve(), args.harness),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

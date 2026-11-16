#!/usr/bin/env python3
import argparse
import collections
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import tarfile
import tempfile
from pathlib import Path

TOOLS = {
    "dependency-cruiser": "18.7.2",
    "typescript": "5.8.3",
    "eslint": "8.57.1",
    "@typescript-eslint/parser": "8.28.0",
}
EXCLUDE = r"(^|/)(node_modules|dist|build|coverage|__tests__|__mocks__|generated|\.codebase-review)(/|$)|\.(test|spec|generated)\.|\.d\.[cm]?ts$"
EXTENSIONS = {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"}


def run(command, cwd, timeout=180):
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise RuntimeError(
            f"Command timed out after {timeout}s: {command[0]}"
        ) from None
    return process.returncode, stdout, stderr


def git(root, *args):
    code, stdout, stderr = run(["git", *args], root)
    if code:
        raise RuntimeError(stderr.decode(errors="replace"))
    return stdout.decode()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def cycle_clusters(violations):
    groups = []
    for item in violations:
        if item.get("type") != "cycle":
            continue
        cycle = [node["name"] for node in item["cycle"]]
        members = set(cycle) | {item["from"], item["to"]}
        overlapping = [group for group in groups if members & group["members"]]
        groups = [group for group in groups if group not in overlapping]
        groups.append(
            {
                "members": members.union(*(group["members"] for group in overlapping)),
                "cycles": [cycle]
                + [cycle for group in overlapping for cycle in group["cycles"]],
            }
        )
    return [
        {
            "files": sorted(group["members"]),
            "diagnostics": len(group["cycles"]),
            "examples": group["cycles"][:3],
        }
        for group in sorted(
            groups, key=lambda group: (-len(group["members"]), sorted(group["members"]))
        )
    ]


def provision(cache, output):
    identity = hashlib.sha256(json.dumps(TOOLS, sort_keys=True).encode()).hexdigest()[
        :16
    ]
    folder = cache / identity
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "install.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(
                "Tool setup is running in another collector; retry after it finishes"
            ) from None
        if not (folder / "ready.json").exists():
            write_json(
                folder / "package.json", {"private": True, "dependencies": TOOLS}
            )
            code, stdout, stderr = run(
                ["npm", "install", "--ignore-scripts", "--no-audit", "--no-fund"],
                folder,
            )
            (output / "install.log").write_bytes(stdout + stderr)
            if code:
                raise RuntimeError(
                    f"Tool installation failed ({code}); see install.log"
                )
            write_json(folder / "ready.json", TOOLS)
    return folder / "node_modules"


def analyze_graph(snapshot, scope, tsconfig, tools, output, exclude, files):
    config = {
        "forbidden": [
            {
                "name": "runtime-cycle",
                "severity": "warn",
                "from": {},
                "to": {"circular": True},
            },
            {
                "name": "unresolved",
                "severity": "warn",
                "from": {},
                "to": {"couldNotResolve": True},
            },
        ],
        "options": {
            "doNotFollow": {"path": "node_modules"},
            "exclude": {"path": exclude},
            "tsPreCompilationDeps": False,
        },
    }
    if tsconfig:
        config["options"]["tsConfig"] = {"fileName": str(snapshot / tsconfig)}
    write_json(output / "dependency-config.json", config)
    code, stdout, stderr = run(
        [
            str(tools / ".bin/depcruise"),
            scope,
            "--config",
            str(output / "dependency-config.json"),
            "--output-type",
            "json",
        ],
        snapshot,
    )
    (output / "dependencies.json").write_bytes(stdout)
    (output / "dependencies.stderr").write_bytes(stderr)
    if code not in (0, 1):
        return {"status": "failed", "exit_code": code}
    data = json.loads(stdout)
    summary = data["summary"]
    unresolved = [v for v in summary["violations"] if v["rule"]["name"] == "unresolved"]
    ts = [
        t
        for t in summary["environment"]["transpilersFound"]
        if t["name"] == "typescript"
    ]
    available = bool(ts and ts[0]["available"])
    escaped = [
        item["source"]
        for item in data["modules"]
        if not (snapshot / item["source"]).resolve().is_relative_to(snapshot)
        and "node_modules" not in Path(item["source"]).parts
    ]
    missing = sorted(set(files) - {item["source"] for item in data["modules"]})
    return {
        "status": "complete"
        if available and not unresolved and not escaped and not missing and files
        else "partial",
        "modules": summary["totalCruised"],
        "dependencies": summary["totalDependenciesCruised"],
        "typescript_available": available,
        "unresolved": unresolved,
        "source_outside_snapshot": escaped,
        "missing_inputs": missing,
        "clusters": cycle_clusters(summary["violations"]),
    }


def analyze_complexity(snapshot, files, tools, output, churn):
    report = []
    errors = []
    for start in range(0, len(files), 100):
        command = [
            str(tools / ".bin/eslint"),
            *files[start : start + 100],
            "--no-eslintrc",
            "--no-inline-config",
            "--no-ignore",
            "--parser",
            str(tools / "@typescript-eslint/parser/dist/index.js"),
            "--parser-options",
            '{"ecmaVersion":2022,"sourceType":"module","ecmaFeatures":{"jsx":true}}',
            "--rule",
            'complexity:["warn",20]',
            "--format",
            "json",
        ]
        code, stdout, stderr = run(command, snapshot)
        errors.append(stderr.decode(errors="replace"))
        if code not in (0, 1):
            (output / "complexity.stderr").write_text("\n".join(errors))
            return {"status": "failed", "exit_code": code}
        report.extend(json.loads(stdout))
    compact = [
        {
            "file": str(Path(f["filePath"]).relative_to(snapshot)),
            "messages": f["messages"],
        }
        for f in report
    ]
    write_json(output / "complexity.json", compact)
    (output / "complexity.stderr").write_text("\n".join(errors))
    candidates = []
    failures = []
    for item in compact:
        for message in item["messages"]:
            if message.get("ruleId") == "complexity":
                value = int(re.search(r"complexity of (\d+)", message["message"])[1])
                commits = churn[item["file"]]
                candidates.append(
                    {
                        "file": item["file"],
                        "line": message["line"],
                        "complexity": value,
                        "file_commits": commits,
                        "rank": value * commits,
                        "message": message["message"],
                    }
                )
            elif message.get("severity") == 2:
                failures.append({"file": item["file"], **message})
    return {
        "status": "partial" if failures or not files else "complete",
        "files": len(files),
        "errors": failures,
        "candidates": sorted(
            candidates,
            key=lambda item: (-item["rank"], -item["complexity"], item["file"]),
        ),
    }


def borrow_dependencies(root, snapshot, package_dirs):
    for relative in package_dirs:
        source = root / relative / "node_modules"
        destination = snapshot / relative / "node_modules"
        if not source.is_dir() or destination.exists():
            continue
        destination.mkdir(parents=True)
        for entry in source.iterdir():
            if entry.name.startswith("."):
                continue
            entries = (
                list(entry.iterdir())
                if entry.name.startswith("@") and entry.is_dir()
                else [entry]
            )
            for dependency in entries:
                target = dependency.resolve()
                if (
                    target.is_relative_to(root)
                    and "node_modules" not in target.relative_to(root).parts
                ):
                    target = snapshot / target.relative_to(root)
                link = destination / dependency.relative_to(source)
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(target, target_is_directory=True)


def collect(args, output):
    root = Path(git(args.root, "rev-parse", "--show-toplevel").strip())
    if root.resolve() != args.root.resolve():
        raise ValueError(
            "--root must be the Git repository root; use --scope for a package"
        )
    if args.tool_cache.resolve().is_relative_to(root.resolve()):
        raise ValueError(
            "The analysis tool cache must be outside the reviewed repository"
        )
    if args.days <= 0:
        raise ValueError("--days must be positive")
    sha = git(root, "rev-parse", "--verify", f"{args.ref}^{{commit}}").strip()
    scope = Path(args.scope)
    config = Path(args.tsconfig) if args.tsconfig else None
    for path in [scope, *([config] if config else [])]:
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(
                "Scope and tsconfig must be repository-relative paths without '..'"
            )
    exclude = "|".join([EXCLUDE, *args.exclude])
    re.compile(exclude)
    tracked = git(
        root, "ls-tree", "-r", "--name-only", "-z", sha, "--", str(scope)
    ).split("\0")
    files = [
        f
        for f in tracked
        if f and Path(f).suffix in EXTENSIONS and not re.search(exclude, f)
    ]
    timestamp = int(git(root, "show", "-s", "--format=%ct", sha).strip())
    names = git(
        root,
        "log",
        sha,
        f"--since=@{timestamp - args.days * 86400}",
        "--format=",
        "--name-only",
        "-z",
        "--",
        str(scope),
    )
    churn = collections.Counter(
        name.strip("\n") for name in names.split("\0") if name.strip("\n")
    )
    result = {
        "schema_version": 1,
        "collector": "typescript-structure-v1",
        "collector_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "root": str(root),
        "baseline": sha,
        "scope": str(scope),
        "tsconfig": str(config) if config else None,
        "exclude": exclude,
        "tools": TOOLS,
        "churn_days": args.days,
        "inputs": files,
        "dependency_context": "Existing node_modules are borrowed for resolution only; installed versions are not proof of baseline dependency versions.",
    }
    write_json(output / "summary.json", {**result, "status": "running"})
    tools = provision(args.tool_cache, output)
    with tempfile.TemporaryDirectory(prefix="codebase-typescript-") as temporary:
        temporary = Path(temporary).resolve()
        archive = temporary / "source.tar"
        code, stdout, stderr = run(["git", "archive", sha], root)
        if code:
            raise RuntimeError(stderr.decode(errors="replace"))
        archive.write_bytes(stdout)
        snapshot = temporary / "source"
        snapshot.mkdir()
        with tarfile.open(archive) as bundle:
            bundle.extractall(snapshot, filter="data")
        package_dirs = {
            Path("."),
            *(
                path.parent.relative_to(snapshot)
                for path in snapshot.rglob("package.json")
            ),
        }
        borrow_dependencies(root, snapshot, sorted(package_dirs))
        if not (snapshot / scope).exists() or (
            config and not (snapshot / config).is_file()
        ):
            raise ValueError("Scope or tsconfig is absent at the approved revision")
        result["graph"] = analyze_graph(
            snapshot, str(scope), config, tools, output, exclude, files
        )
        write_json(output / "summary.json", {**result, "status": "running"})
        result["complexity"] = analyze_complexity(snapshot, files, tools, output, churn)
    result["status"] = (
        "complete"
        if all(result[k]["status"] == "complete" for k in ("graph", "complexity"))
        else "partial"
    )
    write_json(output / "summary.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Collect TypeScript structural evidence at a committed revision. Requires Python 3.12+, Node 22/24/26+, npm, Git."
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--scope", default=".")
    parser.add_argument("--tsconfig")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Additional repository-relative exclusion regex; repeatable",
    )
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--tool-cache",
        type=Path,
        default=Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
        / "codebase-review-typescript",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        parser.error(
            "--output must be empty; reuse recorded evidence or choose a new directory"
        )
    try:
        result = collect(args, output)
    except (OSError, ValueError, RuntimeError, KeyError, tarfile.TarError) as error:
        result = {"status": "failed", "error": str(error)}
        if (output / "summary.json").exists():
            result = {**json.loads((output / "summary.json").read_text()), **result}
        write_json(output / "summary.json", result)
    print(
        json.dumps({"status": result["status"], "report": str(output / "summary.json")})
    )
    raise SystemExit(0 if result["status"] == "complete" else 2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator


AGENTS = ("claude", "codex", "opencode", "pi")


@dataclass(frozen=True)
class Roots:
    claude_projects: Path
    claude_archive: Path
    codex_sessions: Path
    opencode_db: Path
    pi_sessions: Path

    @classmethod
    def from_environment(cls) -> "Roots":
        home = Path.home()
        xdg_data = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
        claude_dir = Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude"))
        codex_dir = Path(os.environ.get("CODEX_HOME", home / ".codex"))
        pi_dir = Path(os.environ.get("PI_CODING_AGENT_DIR", home / ".pi" / "agent"))
        return cls(
            claude_projects=claude_dir / "projects",
            claude_archive=xdg_data / "ringleader" / "archive",
            codex_sessions=codex_dir / "sessions",
            opencode_db=xdg_data / "opencode" / "opencode.db",
            pi_sessions=Path(
                os.environ.get("PI_CODING_AGENT_SESSION_DIR", pi_dir / "sessions")
            ),
        )


@dataclass
class SessionMeta:
    agent: str
    session_id: str
    source: str
    title: str | None = None
    cwd: str | None = None
    branch: str | None = None
    first_ts: str | None = None
    last_ts: str | None = None

    @property
    def ref(self) -> str:
        return f"{self.agent}:{self.session_id}"


@dataclass(frozen=True)
class Entry:
    role: str
    text: str
    timestamp: str | None = None


@dataclass
class MatchResult:
    meta: SessionMeta
    matches: int
    snippets: list[str]


@dataclass(frozen=True)
class SearchOptions:
    cwd: str
    scope: str
    app: str | None
    cutoff: float | None
    context: int
    max_snippets: int


def encode_claude_path(path: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "-", path)


def normalized_path(path: str) -> str:
    return os.path.normcase(os.path.abspath(os.path.expanduser(path)))


def cwd_in_scope(session_cwd: str | None, options: SearchOptions) -> bool:
    if not session_cwd:
        return options.scope == "all" and not options.app
    actual = normalized_path(session_cwd)
    if options.app:
        return options.app.lower() in actual.lower()
    target = normalized_path(options.cwd)
    if options.scope == "all":
        return True
    if options.scope == "current":
        return actual == target
    return actual == target or os.path.dirname(actual) == os.path.dirname(target)


def timestamp_sort_value(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (ValueError, OverflowError):
        return 0.0


def iso_from_millis(value: int | float | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(float(value) / 1000, timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


def update_timestamps(meta: SessionMeta, value: str | None) -> None:
    if not value:
        return
    if meta.first_ts is None or timestamp_sort_value(value) < timestamp_sort_value(meta.first_ts):
        meta.first_ts = value
    if meta.last_ts is None or timestamp_sort_value(value) > timestamp_sort_value(meta.last_ts):
        meta.last_ts = value


def compact_title(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()[:120]


def flatten_content(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(filter(None, (flatten_content(item) for item in value)))
    if not isinstance(value, dict):
        return ""
    parts: list[str] = []
    for key in (
        "text",
        "thinking",
        "reason",
        "name",
        "tool",
        "arguments",
        "input",
        "output",
        "content",
        "error",
    ):
        if key in value:
            item = value[key]
            if isinstance(item, (dict, list)):
                parts.append(json.dumps(item, ensure_ascii=False))
            elif item is not None:
                parts.append(str(item))
    return "\n".join(parts)


def snippet(text: str, match: re.Match[str], context: int) -> str:
    start = max(0, match.start() - context)
    end = min(len(text), match.end() + context)
    result = re.sub(r"\s+", " ", text[start:end]).strip()
    return ("…" if start else "") + result + ("…" if end < len(text) else "")


def scan_entries(
    meta: SessionMeta,
    entries: Iterable[Entry],
    pattern: re.Pattern[str],
    options: SearchOptions,
) -> MatchResult | None:
    if not cwd_in_scope(meta.cwd, options):
        return None
    matches = 0
    snippets: list[str] = []
    first_user_text: str | None = None
    if meta.title:
        for found in pattern.finditer(meta.title):
            matches += 1
            if len(snippets) < options.max_snippets:
                snippets.append(f"[title] {snippet(meta.title, found, options.context)}")
    for entry in entries:
        update_timestamps(meta, entry.timestamp)
        if first_user_text is None and entry.role == "user" and entry.text.strip():
            first_user_text = entry.text
        for found in pattern.finditer(entry.text):
            matches += 1
            if len(snippets) < options.max_snippets:
                snippets.append(f"[{entry.role}] {snippet(entry.text, found, options.context)}")
    if meta.title is None and first_user_text:
        meta.title = compact_title(first_user_text)
    if not matches:
        return None
    return MatchResult(meta=meta, matches=matches, snippets=snippets)


def recent_enough(path: Path, cutoff: float | None) -> bool:
    if cutoff is None:
        return True
    try:
        return path.stat().st_mtime >= cutoff
    except OSError:
        return False


def jsonl_records(path: Path) -> Iterator[dict]:
    try:
        with path.open(errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    yield value
    except OSError:
        return


def claude_entry(record: dict) -> Entry | None:
    parts: list[str] = []
    message = record.get("message")
    if isinstance(message, dict):
        parts.append(flatten_content(message.get("content")))
    elif isinstance(message, str):
        parts.append(message)
    result = record.get("toolUseResult")
    if isinstance(result, str):
        parts.append(result)
    text = "\n".join(filter(None, parts))
    if not text:
        return None
    return Entry(str(record.get("type", "unknown")), text, record.get("timestamp"))


def claude_session(path: Path, pattern: re.Pattern[str], options: SearchOptions) -> MatchResult | None:
    meta = SessionMeta("claude", path.stem, str(path))
    entries: list[Entry] = []
    for record in jsonl_records(path):
        meta.cwd = meta.cwd or record.get("cwd")
        meta.branch = meta.branch or record.get("gitBranch")
        title = record.get("customTitle") or record.get("aiTitle") or record.get("slug")
        if isinstance(title, str):
            meta.title = title
        update_timestamps(meta, record.get("timestamp"))
        entry = claude_entry(record)
        if entry:
            entries.append(entry)
    return scan_entries(meta, entries, pattern, options)


def claude_candidate_paths(root: Path, options: SearchOptions) -> Iterator[Path]:
    if not root.is_dir():
        return
    directories = [path for path in root.iterdir() if path.is_dir()]
    if not options.app and options.scope != "all":
        target = encode_claude_path(normalized_path(options.cwd))
        if options.scope == "current":
            directories = [path for path in directories if path.name == target]
        else:
            parent = encode_claude_path(os.path.dirname(normalized_path(options.cwd))) + "-"
            directories = [
                path for path in directories if path.name == target or path.name.startswith(parent)
            ]
    elif options.app:
        needle = options.app.lower()
        directories = [path for path in directories if needle in path.name.lower()]
    for directory in directories:
        for path in directory.rglob("*.jsonl"):
            if recent_enough(path, options.cutoff):
                yield path


def search_claude(
    roots: Roots, pattern: re.Pattern[str], options: SearchOptions
) -> tuple[list[MatchResult], list[str]]:
    available = [root for root in (roots.claude_projects, roots.claude_archive) if root.is_dir()]
    if not available:
        raise FileNotFoundError(
            f"Claude stores not found: {roots.claude_projects}, {roots.claude_archive}"
        )
    warnings = [
        f"Claude source unavailable: {root}"
        for root in (roots.claude_projects, roots.claude_archive)
        if not root.is_dir()
    ]
    results: dict[str, MatchResult] = {}
    for root in available:
        for path in claude_candidate_paths(root, options):
            result = claude_session(path, pattern, options)
            if result and (
                result.meta.session_id not in results
                or timestamp_sort_value(result.meta.last_ts)
                > timestamp_sort_value(results[result.meta.session_id].meta.last_ts)
            ):
                results[result.meta.session_id] = result
    return list(results.values()), warnings


def codex_entry(record: dict) -> Entry | None:
    if record.get("type") == "turn_context":
        payload = record.get("payload", {})
        summary = payload.get("summary") if isinstance(payload, dict) else None
        if isinstance(summary, str):
            return Entry("summary", summary, record.get("timestamp"))
        return None
    if record.get("type") != "response_item":
        return None
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return None
    kind = str(payload.get("type", "response_item"))
    role = str(payload.get("role", kind))
    if role in ("developer", "system"):
        return None
    text = flatten_content(payload.get("content"))
    if role == "user" and text.lstrip().startswith("# AGENTS.md instructions"):
        return None
    if kind == "function_call":
        text = "\n".join(filter(None, (str(payload.get("name", "")), str(payload.get("arguments", "")))))
    elif kind in ("function_call_output", "custom_tool_call_output"):
        text = str(payload.get("output", ""))
    if not text:
        return None
    return Entry(role, text, record.get("timestamp"))


def codex_session(path: Path, pattern: re.Pattern[str], options: SearchOptions) -> MatchResult | None:
    meta = SessionMeta("codex", path.stem, str(path))
    entries: list[Entry] = []
    for record in jsonl_records(path):
        if record.get("type") == "session_meta" and isinstance(record.get("payload"), dict):
            payload = record["payload"]
            meta.session_id = str(payload.get("id") or payload.get("session_id") or path.stem)
            meta.cwd = payload.get("cwd")
            git = payload.get("git")
            if isinstance(git, dict):
                meta.branch = git.get("branch")
            update_timestamps(meta, payload.get("timestamp"))
            if not cwd_in_scope(meta.cwd, options):
                return None
        update_timestamps(meta, record.get("timestamp"))
        entry = codex_entry(record)
        if entry:
            entries.append(entry)
    return scan_entries(meta, entries, pattern, options)


def search_codex(
    roots: Roots, pattern: re.Pattern[str], options: SearchOptions
) -> tuple[list[MatchResult], list[str]]:
    if not roots.codex_sessions.is_dir():
        raise FileNotFoundError(f"Codex sessions not found: {roots.codex_sessions}")
    results = []
    for path in roots.codex_sessions.rglob("*.jsonl"):
        if recent_enough(path, options.cutoff):
            result = codex_session(path, pattern, options)
            if result:
                results.append(result)
    return results, []


def pi_entry(record: dict) -> Entry | None:
    if record.get("type") != "message" or not isinstance(record.get("message"), dict):
        return None
    message = record["message"]
    text = flatten_content(message.get("content"))
    if not text:
        return None
    return Entry(str(message.get("role", "message")), text, record.get("timestamp"))


def pi_session(path: Path, pattern: re.Pattern[str], options: SearchOptions) -> MatchResult | None:
    meta = SessionMeta("pi", path.stem, str(path))
    entries: list[Entry] = []
    for record in jsonl_records(path):
        if record.get("type") == "session":
            meta.session_id = str(record.get("id") or path.stem)
            meta.cwd = record.get("cwd")
            title = record.get("name")
            if isinstance(title, str):
                meta.title = title
            if not cwd_in_scope(meta.cwd, options):
                return None
        if record.get("type") == "session_name" and isinstance(record.get("name"), str):
            meta.title = record["name"]
        update_timestamps(meta, record.get("timestamp"))
        entry = pi_entry(record)
        if entry:
            entries.append(entry)
    return scan_entries(meta, entries, pattern, options)


def search_pi(
    roots: Roots, pattern: re.Pattern[str], options: SearchOptions
) -> tuple[list[MatchResult], list[str]]:
    if not roots.pi_sessions.is_dir():
        raise FileNotFoundError(f"Pi sessions not found: {roots.pi_sessions}")
    results = []
    for path in roots.pi_sessions.rglob("*.jsonl"):
        if recent_enough(path, options.cutoff):
            result = pi_session(path, pattern, options)
            if result:
                results.append(result)
    return results, []


def open_opencode(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(f"OpenCode database not found: {path}")
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def opencode_entry(row: sqlite3.Row) -> Entry | None:
    try:
        message = json.loads(row["message_data"])
        part = json.loads(row["part_data"])
    except (TypeError, json.JSONDecodeError):
        return None
    role = str(message.get("role", "message")) if isinstance(message, dict) else "message"
    if not isinstance(part, dict):
        return None
    kind = str(part.get("type", "part"))
    if kind in ("text", "reasoning"):
        text = str(part.get("text", ""))
    elif kind == "tool":
        text = "\n".join(
            filter(None, (str(part.get("tool", "")), flatten_content(part.get("state"))))
        )
    else:
        text = flatten_content(part)
    if not text:
        return None
    timestamp = iso_from_millis(row["part_created"] or row["message_created"])
    return Entry(role, text, timestamp)


def opencode_entries(connection: sqlite3.Connection, session_id: str) -> Iterator[Entry]:
    rows = connection.execute(
        """
        SELECT m.data AS message_data, p.data AS part_data,
               m.time_created AS message_created, p.time_created AS part_created
        FROM message AS m
        JOIN part AS p ON p.message_id = m.id
        WHERE m.session_id = ?
        ORDER BY m.time_created, p.time_created, p.id
        """,
        (session_id,),
    )
    for row in rows:
        entry = opencode_entry(row)
        if entry:
            yield entry


def search_opencode(
    roots: Roots, pattern: re.Pattern[str], options: SearchOptions
) -> tuple[list[MatchResult], list[str]]:
    connection = open_opencode(roots.opencode_db)
    try:
        results = []
        for row in connection.execute(
            "SELECT id, directory, title, time_created, time_updated FROM session"
        ):
            updated = float(row["time_updated"]) / 1000
            if options.cutoff is not None and updated < options.cutoff:
                continue
            meta = SessionMeta(
                agent="opencode",
                session_id=str(row["id"]),
                source=f"{roots.opencode_db}#session={row['id']}",
                title=row["title"],
                cwd=row["directory"],
                first_ts=iso_from_millis(row["time_created"]),
                last_ts=iso_from_millis(row["time_updated"]),
            )
            if not cwd_in_scope(meta.cwd, options):
                continue
            result = scan_entries(meta, opencode_entries(connection, meta.session_id), pattern, options)
            if result:
                results.append(result)
        return results, []
    finally:
        connection.close()


SEARCHERS = {
    "claude": search_claude,
    "codex": search_codex,
    "opencode": search_opencode,
    "pi": search_pi,
}


def locate_jsonl(agent: str, session_id: str, roots: Roots) -> Path:
    if agent == "claude":
        search_roots = (roots.claude_projects, roots.claude_archive)
    elif agent == "codex":
        search_roots = (roots.codex_sessions,)
    else:
        search_roots = (roots.pi_sessions,)
    name_matches: list[Path] = []
    for root in search_roots:
        if not root.is_dir():
            continue
        name_matches.extend(root.rglob(f"*{session_id}*.jsonl"))
    if name_matches:
        return max(name_matches, key=lambda path: path.stat().st_mtime)
    for root in search_roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.jsonl"):
            records = jsonl_records(path)
            first = next(records, {})
            candidate = first.get("id")
            payload = first.get("payload")
            if isinstance(payload, dict):
                candidate = payload.get("id") or payload.get("session_id") or candidate
            if str(candidate) == session_id:
                return path
    raise FileNotFoundError(f"Session not found: {agent}:{session_id}")


def read_jsonl_session(agent: str, path: Path) -> tuple[SessionMeta, list[Entry]]:
    meta = SessionMeta(agent, path.stem, str(path))
    entries: list[Entry] = []
    for record in jsonl_records(path):
        if agent == "claude":
            meta.cwd = meta.cwd or record.get("cwd")
            meta.branch = meta.branch or record.get("gitBranch")
            title = record.get("customTitle") or record.get("aiTitle") or record.get("slug")
            if isinstance(title, str):
                meta.title = title
            entry = claude_entry(record)
        elif agent == "codex":
            if record.get("type") == "session_meta" and isinstance(record.get("payload"), dict):
                payload = record["payload"]
                meta.session_id = str(payload.get("id") or payload.get("session_id") or path.stem)
                meta.cwd = payload.get("cwd")
                git = payload.get("git")
                if isinstance(git, dict):
                    meta.branch = git.get("branch")
            entry = codex_entry(record)
        else:
            if record.get("type") == "session":
                meta.session_id = str(record.get("id") or path.stem)
                meta.cwd = record.get("cwd")
                if isinstance(record.get("name"), str):
                    meta.title = record["name"]
            entry = pi_entry(record)
        update_timestamps(meta, record.get("timestamp"))
        if entry:
            entries.append(entry)
    if meta.title is None:
        first_user = next((entry.text for entry in entries if entry.role == "user"), None)
        if first_user:
            meta.title = compact_title(first_user)
    return meta, entries


def read_opencode_session(session_id: str, roots: Roots) -> tuple[SessionMeta, list[Entry]]:
    connection = open_opencode(roots.opencode_db)
    try:
        row = connection.execute(
            "SELECT id, directory, title, time_created, time_updated FROM session WHERE id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            raise FileNotFoundError(f"Session not found: opencode:{session_id}")
        meta = SessionMeta(
            "opencode",
            str(row["id"]),
            f"{roots.opencode_db}#session={row['id']}",
            row["title"],
            row["directory"],
            first_ts=iso_from_millis(row["time_created"]),
            last_ts=iso_from_millis(row["time_updated"]),
        )
        return meta, list(opencode_entries(connection, session_id))
    finally:
        connection.close()


def parse_ref(value: str) -> tuple[str, str]:
    agent, separator, session_id = value.partition(":")
    if not separator or agent not in AGENTS or not session_id:
        raise ValueError("session ref must be AGENT:SESSION_ID")
    return agent, session_id


def print_meta(meta: SessionMeta) -> None:
    print(f"agent  : {meta.agent}")
    print(f"ref    : {meta.ref}")
    print(f"source : {meta.source}")
    if meta.title:
        print(f"title  : {meta.title}")
    if meta.cwd:
        print(f"cwd    : {meta.cwd}")
    if meta.branch:
        print(f"branch : {meta.branch}")
    print(f"when   : {meta.first_ts or '?'}  →  {meta.last_ts or '?'}")


def print_transcript(meta: SessionMeta, entries: Iterable[Entry]) -> None:
    print_meta(meta)
    print()
    for entry in entries:
        timestamp = f"{entry.timestamp} " if entry.timestamp else ""
        print(f"{timestamp}[{entry.role}]")
        print(entry.text.rstrip())
        print()


def print_results(results: list[MatchResult], agents: list[str], query: str, incomplete: bool) -> None:
    qualifier = " (incomplete)" if incomplete else ""
    print(f"Searched {', '.join(agents)} for /{query}/{qualifier}")
    if not results:
        print("No matching sessions.")
        return
    print(f"Found {len(results)} matching session(s), newest first:\n")
    for result in results:
        print("=" * 70)
        print_meta(result.meta)
        print(f"matches: {result.matches}")
        for value in result.snippets:
            print(f"  • {value[:500]}")
        print()


def selected_agents(args: argparse.Namespace) -> tuple[list[str], bool]:
    explicit = [agent for agent in AGENTS if getattr(args, agent)]
    all_mode = args.all or (not explicit and not args.current)
    selected = set(AGENTS if all_mode else explicit)
    if args.current:
        current = os.environ.get("AGENT_HARNESS", "").lower()
        if current not in AGENTS:
            raise ValueError(
                "--current requires AGENT_HARNESS from an agent wrapper; use an explicit selector"
            )
        selected.add(current)
    return [agent for agent in AGENTS if agent in selected], all_mode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search session logs across agent harnesses")
    parser.add_argument("query", nargs="?", help="regex to search for")
    for agent in AGENTS:
        parser.add_argument(f"--{agent}", action="store_true", help=f"search {agent} sessions")
    parser.add_argument("--current", action="store_true", help="search the invoking agent")
    parser.add_argument("--all", action="store_true", help="search all agents (default)")
    parser.add_argument("--read", metavar="REF", help="print one AGENT:SESSION_ID transcript")
    parser.add_argument("--cwd", default=os.getcwd(), help="project directory for scope matching")
    parser.add_argument(
        "--scope",
        choices=("siblings", "current", "all"),
        default="siblings",
        help="project scope (default: siblings)",
    )
    parser.add_argument("--app", help="match this substring against session cwd values")
    parser.add_argument("--days", type=int, help="only sessions updated within the last N days")
    parser.add_argument("--case-sensitive", action="store_true")
    parser.add_argument("--context", type=int, default=160, help="snippet characters on each side")
    parser.add_argument("--max-snippets", type=int, default=3, help="snippets per session")
    parser.add_argument("--max-results", type=int, default=50, help="maximum sessions to print")
    return parser


def main(argv: list[str] | None = None, roots: Roots | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    roots = roots or Roots.from_environment()
    if args.read:
        try:
            agent, session_id = parse_ref(args.read)
            if agent == "opencode":
                meta, entries = read_opencode_session(session_id, roots)
            else:
                path = locate_jsonl(agent, session_id, roots)
                meta, entries = read_jsonl_session(agent, path)
            print_transcript(meta, entries)
            return 0
        except (FileNotFoundError, ValueError, sqlite3.Error) as error:
            print(str(error), file=sys.stderr)
            return 2
    if not args.query:
        parser.error("query is required unless --read is used")
    if args.days is not None and args.days < 0:
        parser.error("--days must be non-negative")
    if args.context < 0 or args.max_snippets < 0 or args.max_results < 1:
        parser.error("context/snippet limits must be non-negative and max-results must be positive")
    try:
        agents, all_mode = selected_agents(args)
        pattern = re.compile(args.query, 0 if args.case_sensitive else re.IGNORECASE)
    except (ValueError, re.error) as error:
        print(str(error), file=sys.stderr)
        return 2
    cutoff = None
    if args.days is not None:
        cutoff = datetime.now(timezone.utc).timestamp() - args.days * 86400
    options = SearchOptions(
        cwd=args.cwd,
        scope=args.scope,
        app=args.app,
        cutoff=cutoff,
        context=args.context,
        max_snippets=args.max_snippets,
    )
    results: list[MatchResult] = []
    warnings: list[str] = []
    searched: list[str] = []
    for agent in agents:
        try:
            found, provider_warnings = SEARCHERS[agent](roots, pattern, options)
        except (FileNotFoundError, sqlite3.Error) as error:
            if not all_mode:
                print(str(error), file=sys.stderr)
                return 2
            warnings.append(str(error))
            continue
        results.extend(found)
        warnings.extend(provider_warnings)
        searched.append(agent)
    if not searched:
        print("No selected agent stores were available.", file=sys.stderr)
        return 2
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    results.sort(key=lambda result: timestamp_sort_value(result.meta.last_ts), reverse=True)
    print_results(results[: args.max_results], searched, args.query, bool(warnings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

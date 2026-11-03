#!/usr/bin/env python3
"""Extract failure signals from Claude Code session transcripts.

Scans ~/.claude/projects/*/UUID.jsonl for retry loops, permission denials,
command failures, and other patterns. Outputs compact JSON for analysis.

Usage:
    python3 extract_signals.py --days 14 --output /tmp/review-logs-output.json
    python3 extract_signals.py --days 7 --project juggler --output /tmp/out.json
"""

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from glob import glob
from pathlib import Path
from typing import Any


# --- Constants ---

CLAUDE_DIR = Path.home() / ".claude" / "projects"
SESSION_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl$"
)
MAX_MSG_LEN = 200
MAX_CMD_LEN = 100
TOP_COMMANDS = 20
TOP_SESSIONS = 10
TOP_SAMPLES = 5
RETRY_THRESHOLD = 3
PROGRESS_INTERVAL = 10

# Detection patterns
PERMISSION_DENIED_PATTERNS = ["Permission to use", "permission to use"]
PERMISSION_DENIED_CONFIRM = ["denied", "Denied"]
USER_REJECTED_PATTERNS = ["doesn't want to proceed", "does not want to proceed"]
COMMAND_FAILED_PATTERN = re.compile(r"Exit code[:\s]+(\d+)")
FILE_NOT_FOUND_PATTERNS = ["File does not exist", "No such file"]
INTERRUPTED_PATTERNS = ["interrupted"]
GH_API_MISUSE_PATTERN = re.compile(
    r"gh\s+api\s+repos/[^/]+/[^/]+/(issues|pulls|releases|actions)"
)
GIT_WRITE_PATTERN = re.compile(
    r"\bgit\s+(add|commit|push|checkout|mv|rm)\b"
)
GIT_UNNECESSARY_C_PATTERN = re.compile(r"\bgit\s+-C\s+")
HOOK_BLOCK_EXIT_PATTERN = re.compile(r'"exit(?:_code|Code)":\s*([1-9]\d*)')


# --- Data structures ---


@dataclass
class SessionStats:
    session_id: str
    project: str
    total_tool_calls: int = 0
    total_errors: int = 0
    errors: list = field(default_factory=list)
    retry_loops: list = field(default_factory=list)
    misbehaviors: list = field(default_factory=list)
    permission_denials: list = field(default_factory=list)
    user_rejections: list = field(default_factory=list)
    command_failures: list = field(default_factory=list)
    file_not_found: list = field(default_factory=list)
    interrupted: list = field(default_factory=list)
    hook_blocks: list = field(default_factory=list)


def truncate(s: str, max_len: int) -> str:
    if not s:
        return ""
    s = s.replace("\n", " ").strip()
    if len(s) > max_len:
        return s[:max_len - 3] + "..."
    return s


def extract_text(content: Any) -> str:
    """Extract text from message content (string or list of blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "tool_result":
                    # Recurse into tool_result content
                    parts.append(extract_text(block.get("content", "")))
            elif isinstance(block, str):
                parts.append(block)
        return " ".join(parts)
    return str(content)


def extract_tool_uses(content: Any) -> list[dict]:
    """Extract tool_use blocks from assistant message content."""
    if not isinstance(content, list):
        return []
    return [
        block for block in content
        if isinstance(block, dict) and block.get("type") == "tool_use"
    ]


def extract_tool_results(content: Any) -> list[dict]:
    """Extract tool_result blocks from user message content."""
    if not isinstance(content, list):
        return []
    return [
        block for block in content
        if isinstance(block, dict) and block.get("type") == "tool_result"
    ]


def get_bash_command(tool_use: dict) -> str | None:
    """Get the command from a Bash tool_use block."""
    inp = tool_use.get("input", {})
    if isinstance(inp, dict):
        return inp.get("command")
    return None


def check_permission_denied(text: str) -> bool:
    for pat in PERMISSION_DENIED_PATTERNS:
        if pat in text:
            for confirm in PERMISSION_DENIED_CONFIRM:
                if confirm in text:
                    return True
    return False


def check_user_rejected(text: str) -> bool:
    return any(pat in text for pat in USER_REJECTED_PATTERNS)


def check_file_not_found(text: str) -> bool:
    return any(pat in text for pat in FILE_NOT_FOUND_PATTERNS)


def check_interrupted(text: str) -> bool:
    return any(pat in text for pat in INTERRUPTED_PATTERNS)


def process_session(filepath: Path, project_name: str) -> SessionStats | None:
    """Process a single session JSONL file, extracting signals in a single pass."""
    session_id = filepath.stem
    stats = SessionStats(session_id=session_id, project=project_name)

    # Track tool calls for retry detection
    tool_call_map: dict[str, dict] = {}  # tool_use_id -> {name, input, command}
    tool_call_sequence: list[str] = []  # sequence of tool names for retry detection
    last_bash_commands: list[tuple[str, bool]] = []  # (command, failed) for same-cmd retry
    session_cwd: str | None = None

    try:
        with open(filepath, "r", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg_type = msg.get("type")
                role = msg.get("role")
                content = msg.get("message", {}).get("content", "") if msg.get("message") else msg.get("content", "")

                # Extract cwd from session init if available
                if msg_type == "system" and not session_cwd:
                    text = extract_text(content)
                    cwd_match = re.search(r"working directory[:\s]+([^\s,]+)", text, re.IGNORECASE)
                    if cwd_match:
                        session_cwd = cwd_match.group(1)

                # Also check for cwd in the message directly
                if not session_cwd and isinstance(msg, dict):
                    session_cwd = msg.get("cwd") or msg.get("workingDirectory")

                # --- Assistant messages: check for tool_use blocks ---
                if role == "assistant" or msg_type == "assistant":
                    actual_content = msg.get("message", {}).get("content", content) if msg.get("message") else content
                    tool_uses = extract_tool_uses(actual_content)

                    for tu in tool_uses:
                        stats.total_tool_calls += 1
                        tool_name = tu.get("name", "")
                        tool_id = tu.get("id", "")
                        tool_input = tu.get("input", {})

                        tool_call_map[tool_id] = {
                            "name": tool_name,
                            "input": tool_input,
                        }

                        # Track sequence for retry detection
                        tool_call_sequence.append(tool_name)

                        # Check Bash tool_use for misbehavior patterns
                        if tool_name == "Bash":
                            cmd = get_bash_command(tu)
                            if cmd:
                                tool_call_map[tool_id]["command"] = cmd

                                # gh api misuse
                                if GH_API_MISUSE_PATTERN.search(cmd):
                                    stats.misbehaviors.append({
                                        "pattern": "gh_api_misuse",
                                        "sample": truncate(cmd, MAX_CMD_LEN),
                                    })

                                # git write attempts
                                if GIT_WRITE_PATTERN.search(cmd):
                                    stats.misbehaviors.append({
                                        "pattern": "git_write_attempt",
                                        "sample": truncate(cmd, MAX_CMD_LEN),
                                    })

                                # Unnecessary -C flag
                                if session_cwd and GIT_UNNECESSARY_C_PATTERN.search(cmd):
                                    c_match = re.search(r"git\s+-C\s+(\S+)", cmd)
                                    if c_match:
                                        c_dir = c_match.group(1).rstrip("/")
                                        s_cwd = session_cwd.rstrip("/")
                                        if c_dir == s_cwd:
                                            stats.misbehaviors.append({
                                                "pattern": "unnecessary_git_c_flag",
                                                "sample": truncate(cmd, MAX_CMD_LEN),
                                            })

                                # Track for same-command retry detection
                                last_bash_commands.append((cmd, False))

                # --- User messages / tool results: check for errors ---
                if role == "user" or msg_type == "user":
                    actual_content = msg.get("message", {}).get("content", content) if msg.get("message") else content
                    tool_results = extract_tool_results(actual_content)

                    for tr in tool_results:
                        is_error = tr.get("is_error", False)
                        result_text = extract_text(tr.get("content", ""))
                        tool_use_id = tr.get("tool_use_id", "")

                        if is_error:
                            stats.total_errors += 1
                            matched_call = tool_call_map.get(tool_use_id, {})
                            tool_name = matched_call.get("name", "unknown")
                            cmd = matched_call.get("command", "")

                            error_entry = {
                                "tool": tool_name,
                                "error": truncate(result_text, MAX_MSG_LEN),
                            }
                            if cmd:
                                error_entry["command"] = truncate(cmd, MAX_CMD_LEN)
                            stats.errors.append(error_entry)

                            # Mark last bash command as failed for retry detection
                            if tool_name == "Bash" and last_bash_commands:
                                last_bash_commands[-1] = (last_bash_commands[-1][0], True)

                        # Check specific patterns in error results
                        if is_error or result_text:
                            text = result_text

                            if check_permission_denied(text):
                                matched_call = tool_call_map.get(tool_use_id, {})
                                cmd = matched_call.get("command", "")
                                tool_name = matched_call.get("name", "unknown")
                                is_git_write = bool(cmd and GIT_WRITE_PATTERN.search(cmd))
                                stats.permission_denials.append({
                                    "tool": tool_name,
                                    "command": truncate(cmd, MAX_CMD_LEN) if cmd else "",
                                    "expected": is_git_write,
                                    "sample": truncate(text, MAX_MSG_LEN),
                                })

                            if check_user_rejected(text):
                                stats.user_rejections.append({
                                    "sample": truncate(text, MAX_MSG_LEN),
                                })

                            if is_error:
                                cmd_match = COMMAND_FAILED_PATTERN.search(text)
                                if cmd_match:
                                    matched_call = tool_call_map.get(tool_use_id, {})
                                    cmd = matched_call.get("command", "")
                                    stats.command_failures.append({
                                        "command": truncate(cmd, MAX_CMD_LEN) if cmd else "",
                                        "exit_code": cmd_match.group(1),
                                        "error": truncate(text, MAX_MSG_LEN),
                                    })

                                if check_file_not_found(text):
                                    stats.file_not_found.append({
                                        "sample": truncate(text, MAX_MSG_LEN),
                                    })

                                if check_interrupted(text):
                                    stats.interrupted.append({
                                        "sample": truncate(text, MAX_MSG_LEN),
                                    })

                    # Also check non-tool-result user messages
                    if not tool_results:
                        text = extract_text(actual_content)
                        if check_permission_denied(text):
                            stats.permission_denials.append({
                                "tool": "unknown",
                                "command": "",
                                "expected": False,
                                "sample": truncate(text, MAX_MSG_LEN),
                            })
                        if check_user_rejected(text):
                            stats.user_rejections.append({
                                "sample": truncate(text, MAX_MSG_LEN),
                            })

                # --- Progress messages: hook blocks ---
                if msg_type == "progress":
                    text = json.dumps(msg) if isinstance(msg, dict) else str(msg)
                    hook_match = HOOK_BLOCK_EXIT_PATTERN.search(text)
                    if hook_match:
                        stats.hook_blocks.append({
                            "sample": truncate(text, MAX_MSG_LEN),
                        })

    except (OSError, IOError) as e:
        print(f"  Warning: could not read {filepath}: {e}", file=sys.stderr)
        return None

    # --- Detect retry loops ---
    if len(tool_call_sequence) >= RETRY_THRESHOLD:
        i = 0
        while i < len(tool_call_sequence):
            tool_name = tool_call_sequence[i]
            run_len = 1
            while (i + run_len < len(tool_call_sequence)
                   and tool_call_sequence[i + run_len] == tool_name):
                run_len += 1
            if run_len >= RETRY_THRESHOLD:
                stats.retry_loops.append({
                    "tool": tool_name,
                    "count": run_len,
                })
            i += run_len

    # --- Detect same-command retries ---
    if len(last_bash_commands) >= 2:
        for i in range(1, len(last_bash_commands)):
            prev_cmd, prev_failed = last_bash_commands[i - 1]
            curr_cmd, _ = last_bash_commands[i]
            if prev_failed and prev_cmd == curr_cmd:
                stats.retry_loops.append({
                    "tool": "Bash(same_cmd)",
                    "count": 2,
                    "sample": truncate(curr_cmd, MAX_CMD_LEN),
                })

    return stats


def find_sessions(
    days: int, project_filter: str | None
) -> list[tuple[Path, str]]:
    """Find session files within the time window, filtered by mtime."""
    cutoff = time.time() - (days * 86400)
    sessions = []

    if not CLAUDE_DIR.exists():
        print(f"Error: {CLAUDE_DIR} does not exist", file=sys.stderr)
        return sessions

    for project_dir in CLAUDE_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        project_name = project_dir.name

        if project_filter:
            if project_filter.lower() not in project_name.lower():
                continue

        for f in project_dir.iterdir():
            if not f.is_file():
                continue
            if not SESSION_PATTERN.match(f.name):
                continue
            try:
                if f.stat().st_mtime >= cutoff:
                    sessions.append((f, project_name))
            except OSError:
                continue

    return sessions


def aggregate(all_stats: list[SessionStats]) -> dict:
    """Aggregate session stats into the output schema."""
    # Collect across sessions
    error_by_category: dict[str, dict] = defaultdict(lambda: {"count": 0, "samples": []})
    failing_commands: dict[str, dict] = defaultdict(lambda: {"count": 0, "sample_error": ""})
    permission_denied: dict[str, dict] = defaultdict(lambda: {"count": 0, "expected": False})
    retry_by_tool: dict[str, int] = defaultdict(int)
    total_retry_loops = 0
    misbehavior_by_pattern: dict[str, dict] = defaultdict(lambda: {"count": 0, "samples": []})
    total_tool_calls = 0
    total_errors = 0
    projects = set()
    earliest_session = None
    latest_session = None

    for stats in all_stats:
        total_tool_calls += stats.total_tool_calls
        total_errors += stats.total_errors
        projects.add(stats.project)

        # Errors by category
        for e in stats.permission_denials:
            cat = "permission_denied"
            error_by_category[cat]["count"] += 1
            if len(error_by_category[cat]["samples"]) < TOP_SAMPLES:
                error_by_category[cat]["samples"].append(e.get("sample", ""))

        for e in stats.user_rejections:
            cat = "user_rejected"
            error_by_category[cat]["count"] += 1
            if len(error_by_category[cat]["samples"]) < TOP_SAMPLES:
                error_by_category[cat]["samples"].append(e.get("sample", ""))

        for e in stats.command_failures:
            cat = "command_failed"
            error_by_category[cat]["count"] += 1
            if len(error_by_category[cat]["samples"]) < TOP_SAMPLES:
                error_by_category[cat]["samples"].append(e.get("error", ""))

            # Track failing commands
            cmd = e.get("command", "unknown")
            if cmd:
                failing_commands[cmd]["count"] += 1
                if not failing_commands[cmd]["sample_error"]:
                    failing_commands[cmd]["sample_error"] = e.get("error", "")

        for e in stats.file_not_found:
            cat = "file_not_found"
            error_by_category[cat]["count"] += 1
            if len(error_by_category[cat]["samples"]) < TOP_SAMPLES:
                error_by_category[cat]["samples"].append(e.get("sample", ""))

        for e in stats.interrupted:
            cat = "interrupted"
            error_by_category[cat]["count"] += 1
            if len(error_by_category[cat]["samples"]) < TOP_SAMPLES:
                error_by_category[cat]["samples"].append(e.get("sample", ""))

        for e in stats.hook_blocks:
            cat = "hook_blocked"
            error_by_category[cat]["count"] += 1
            if len(error_by_category[cat]["samples"]) < TOP_SAMPLES:
                error_by_category[cat]["samples"].append(e.get("sample", ""))

        # Permission denials
        for e in stats.permission_denials:
            cmd = e.get("command") or e.get("tool", "unknown")
            permission_denied[cmd]["count"] += 1
            permission_denied[cmd]["expected"] = e.get("expected", False)

        # Retry loops
        for r in stats.retry_loops:
            total_retry_loops += 1
            retry_by_tool[r["tool"]] += r.get("count", 1)

        # Misbehaviors
        for m in stats.misbehaviors:
            pat = m["pattern"]
            misbehavior_by_pattern[pat]["count"] += 1
            if len(misbehavior_by_pattern[pat]["samples"]) < TOP_SAMPLES:
                misbehavior_by_pattern[pat]["samples"].append(m.get("sample", ""))

    # Build session rankings
    session_error_rates = []
    session_retry_counts = []
    for stats in all_stats:
        if stats.total_tool_calls > 0:
            error_rate = stats.total_errors / stats.total_tool_calls
        else:
            error_rate = 0
        session_error_rates.append({
            "session_id": stats.session_id,
            "project": stats.project,
            "error_rate": round(error_rate, 3),
            "errors": stats.total_errors,
            "tool_calls": stats.total_tool_calls,
        })
        if stats.retry_loops:
            session_retry_counts.append({
                "session_id": stats.session_id,
                "project": stats.project,
                "retry_loops": len(stats.retry_loops),
            })

    session_error_rates.sort(key=lambda x: x["error_rate"], reverse=True)
    session_retry_counts.sort(key=lambda x: x["retry_loops"], reverse=True)

    # Top failing commands
    top_failing = sorted(failing_commands.items(), key=lambda x: x[1]["count"], reverse=True)[:TOP_COMMANDS]

    # Top permission denied
    top_perm = sorted(permission_denied.items(), key=lambda x: x[1]["count"], reverse=True)[:TOP_COMMANDS]

    # Misbehaviors
    misbehavior_list = [
        {"pattern": pat, "count": data["count"], "samples": data["samples"]}
        for pat, data in sorted(misbehavior_by_pattern.items(), key=lambda x: x[1]["count"], reverse=True)
    ]

    return {
        "meta": {
            "days": None,  # filled by caller
            "sessions_scanned": len(all_stats),
            "projects": len(projects),
            "project_names": sorted(projects),
            "total_tool_calls": total_tool_calls,
            "total_errors": total_errors,
        },
        "error_summary": {
            "by_category": {
                cat: {"count": data["count"], "samples": data["samples"]}
                for cat, data in sorted(error_by_category.items(), key=lambda x: x[1]["count"], reverse=True)
            }
        },
        "top_failing_commands": [
            {"command": cmd, "count": data["count"], "sample_error": data["sample_error"]}
            for cmd, data in top_failing
        ],
        "permission_denied_commands": [
            {"command": cmd, "count": data["count"], "expected": data["expected"]}
            for cmd, data in top_perm
        ],
        "retry_loops": {
            "total": total_retry_loops,
            "by_tool": dict(sorted(retry_by_tool.items(), key=lambda x: x[1], reverse=True)),
            "worst_sessions": session_retry_counts[:5],
        },
        "problematic_sessions": session_error_rates[:TOP_SESSIONS],
        "misbehavior_patterns": misbehavior_list,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract failure signals from Claude Code session transcripts"
    )
    parser.add_argument(
        "--days", type=int, default=14,
        help="Lookback window in days (default: 14)"
    )
    parser.add_argument(
        "--project", type=str, default=None,
        help="Filter to sessions matching this project name (substring match)"
    )
    parser.add_argument(
        "--output", type=str, required=True,
        help="Output JSON file path"
    )
    args = parser.parse_args()

    print(f"Scanning sessions from last {args.days} days...", file=sys.stderr)
    if args.project:
        print(f"Filtering to project: {args.project}", file=sys.stderr)

    sessions = find_sessions(args.days, args.project)
    print(f"Found {len(sessions)} sessions to scan", file=sys.stderr)

    if not sessions:
        # Write empty output
        output = {
            "meta": {
                "days": args.days,
                "sessions_scanned": 0,
                "projects": 0,
                "project_names": [],
                "total_tool_calls": 0,
                "total_errors": 0,
            },
            "error_summary": {"by_category": {}},
            "top_failing_commands": [],
            "permission_denied_commands": [],
            "retry_loops": {"total": 0, "by_tool": {}, "worst_sessions": []},
            "problematic_sessions": [],
            "misbehavior_patterns": [],
        }
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"No sessions found. Empty output written to {args.output}", file=sys.stderr)
        return

    all_stats = []
    for i, (filepath, project_name) in enumerate(sessions):
        if (i + 1) % PROGRESS_INTERVAL == 0:
            print(f"  Processing session {i + 1}/{len(sessions)}...", file=sys.stderr)

        stats = process_session(filepath, project_name)
        if stats:
            all_stats.append(stats)

    print(f"Processed {len(all_stats)} sessions successfully", file=sys.stderr)

    output = aggregate(all_stats)
    output["meta"]["days"] = args.days

    # Compute date range from file mtimes
    mtimes = []
    for filepath, _ in sessions:
        try:
            mtimes.append(filepath.stat().st_mtime)
        except OSError:
            pass
    if mtimes:
        earliest = datetime.fromtimestamp(min(mtimes)).strftime("%Y-%m-%d")
        latest = datetime.fromtimestamp(max(mtimes)).strftime("%Y-%m-%d")
        output["meta"]["date_range"] = f"{earliest} to {latest}"
    else:
        output["meta"]["date_range"] = "unknown"

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Output written to {args.output}", file=sys.stderr)
    print(f"Summary: {output['meta']['total_errors']} errors, "
          f"{output['retry_loops']['total']} retry loops across "
          f"{output['meta']['sessions_scanned']} sessions", file=sys.stderr)


if __name__ == "__main__":
    main()

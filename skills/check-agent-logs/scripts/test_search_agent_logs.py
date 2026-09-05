from __future__ import annotations

import importlib.util
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("search_agent_logs.py")
SPEC = importlib.util.spec_from_file_location("search_agent_logs", MODULE_PATH)
search_agent_logs = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = search_agent_logs
SPEC.loader.exec_module(search_agent_logs)


class SearchAgentLogsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.roots = search_agent_logs.Roots(
            claude_projects=root / "claude-projects",
            claude_archive=root / "claude-archive",
            codex_sessions=root / "codex-sessions",
            opencode_db=root / "opencode" / "opencode.db",
            pi_sessions=root / "pi-sessions",
        )
        self.cwd = "/work/app/dev1"
        self.sibling = "/work/app/dev2"
        self.make_claude_session(self.roots.claude_projects, "claude-live", self.cwd, "needle live")
        self.make_claude_session(
            self.roots.claude_archive, "claude-archived", self.sibling, "needle archived"
        )
        self.make_codex_session("codex-session", self.cwd, "needle codex")
        self.make_pi_session("pi-session", self.sibling, "needle pi")
        self.make_opencode_db("opencode-session", self.cwd, "needle opencode")

    def tearDown(self):
        self.directory.cleanup()

    def write_jsonl(self, path: Path, records: list[dict]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(record) + "\n" for record in records))

    def make_claude_session(self, root: Path, session_id: str, cwd: str, text: str) -> None:
        folder = root / search_agent_logs.encode_claude_path(cwd)
        self.write_jsonl(
            folder / f"{session_id}.jsonl",
            [
                {
                    "type": "user",
                    "cwd": cwd,
                    "gitBranch": "main",
                    "timestamp": "2026-08-10T10:00:00Z",
                    "message": {"content": text},
                },
                {"type": "ai-title", "aiTitle": f"Title {session_id}"},
            ],
        )

    def make_codex_session(self, session_id: str, cwd: str, text: str) -> None:
        path = self.roots.codex_sessions / "2026" / "08" / f"rollout-{session_id}.jsonl"
        self.write_jsonl(
            path,
            [
                {
                    "type": "session_meta",
                    "timestamp": "2026-08-10T10:00:00Z",
                    "payload": {
                        "id": session_id,
                        "cwd": cwd,
                        "timestamp": "2026-08-10T10:00:00Z",
                        "git": {"branch": "feature"},
                    },
                },
                {
                    "type": "response_item",
                    "timestamp": "2026-08-10T10:01:00Z",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "# AGENTS.md instructions\nneedle bootstrap",
                            }
                        ],
                    },
                },
                {
                    "type": "response_item",
                    "timestamp": "2026-08-10T10:02:00Z",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": text}],
                    },
                },
            ],
        )

    def make_pi_session(self, session_id: str, cwd: str, text: str) -> None:
        path = self.roots.pi_sessions / "encoded" / f"session-{session_id}.jsonl"
        self.write_jsonl(
            path,
            [
                {
                    "type": "session",
                    "id": session_id,
                    "cwd": cwd,
                    "timestamp": "2026-08-10T10:00:00Z",
                },
                {
                    "type": "message",
                    "timestamp": "2026-08-10T10:03:00Z",
                    "message": {"role": "user", "content": text},
                },
            ],
        )

    def make_opencode_db(self, session_id: str, cwd: str, text: str) -> None:
        self.roots.opencode_db.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.roots.opencode_db)
        connection.executescript(
            """
            CREATE TABLE session (
                id TEXT PRIMARY KEY, directory TEXT, title TEXT,
                time_created INTEGER, time_updated INTEGER
            );
            CREATE TABLE message (
                id TEXT PRIMARY KEY, session_id TEXT, time_created INTEGER, data TEXT
            );
            CREATE TABLE part (
                id TEXT PRIMARY KEY, message_id TEXT, time_created INTEGER, data TEXT
            );
            """
        )
        connection.execute(
            "INSERT INTO session VALUES (?, ?, ?, ?, ?)",
            (session_id, cwd, "OpenCode title", 1786356000000, 1786356060000),
        )
        connection.execute(
            "INSERT INTO message VALUES (?, ?, ?, ?)",
            ("message-1", session_id, 1786356000000, json.dumps({"role": "user"})),
        )
        connection.execute(
            "INSERT INTO part VALUES (?, ?, ?, ?)",
            ("part-1", "message-1", 1786356060000, json.dumps({"type": "text", "text": text})),
        )
        connection.commit()
        connection.close()

    def run_main(self, arguments: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = search_agent_logs.main(arguments, self.roots)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_default_searches_all_agents_and_claude_archive(self):
        status, stdout, stderr = self.run_main(["needle", "--cwd", self.cwd])
        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        for ref in (
            "claude:claude-live",
            "claude:claude-archived",
            "codex:codex-session",
            "opencode:opencode-session",
            "pi:pi-session",
        ):
            self.assertIn(f"ref    : {ref}", stdout)
        self.assertIn("title  : needle codex", stdout)
        self.assertNotIn("needle bootstrap", stdout)

    def test_provider_flags_compose_and_current_uses_wrapper_marker(self):
        status, stdout, _ = self.run_main(["needle", "--claude", "--pi", "--cwd", self.cwd])
        self.assertEqual(status, 0)
        self.assertIn("claude:claude-live", stdout)
        self.assertIn("pi:pi-session", stdout)
        self.assertNotIn("codex:codex-session", stdout)
        with patch.dict(os.environ, {"AGENT_HARNESS": "opencode"}):
            status, stdout, _ = self.run_main(["needle", "--current", "--cwd", self.cwd])
        self.assertEqual(status, 0)
        self.assertIn("opencode:opencode-session", stdout)
        self.assertNotIn("claude:claude-live", stdout)

    def test_current_without_marker_fails(self):
        with patch.dict(os.environ, {}, clear=True):
            status, _, stderr = self.run_main(["needle", "--current"])
        self.assertEqual(status, 2)
        self.assertIn("AGENT_HARNESS", stderr)

    def test_current_project_scope_excludes_sibling(self):
        status, stdout, _ = self.run_main(
            ["needle", "--claude", "--cwd", self.cwd, "--scope", "current"]
        )
        self.assertEqual(status, 0)
        self.assertIn("claude:claude-live", stdout)
        self.assertNotIn("claude:claude-archived", stdout)

    def test_session_titles_are_searchable(self):
        status, stdout, _ = self.run_main(
            ["OpenCode title", "--opencode", "--cwd", self.cwd]
        )
        self.assertEqual(status, 0)
        self.assertIn("opencode:opencode-session", stdout)
        self.assertIn("[title] OpenCode title", stdout)

    def test_app_regex_and_case_controls(self):
        status, stdout, _ = self.run_main(
            ["needle (live|archived)", "--claude", "--app", "dev2", "--cwd", "/elsewhere"]
        )
        self.assertEqual(status, 0)
        self.assertIn("claude:claude-archived", stdout)
        self.assertNotIn("claude:claude-live", stdout)
        status, stdout, _ = self.run_main(
            ["NEEDLE", "--claude", "--case-sensitive", "--cwd", self.cwd]
        )
        self.assertEqual(status, 0)
        self.assertIn("No matching sessions", stdout)

    def test_days_filters_old_jsonl_sessions(self):
        codex_path = next(self.roots.codex_sessions.rglob("*.jsonl"))
        os.utime(codex_path, (1, 1))
        status, stdout, _ = self.run_main(
            ["needle", "--codex", "--scope", "all", "--days", "1"]
        )
        self.assertEqual(status, 0)
        self.assertIn("No matching sessions", stdout)

    def test_read_renders_jsonl_and_opencode_sessions(self):
        status, stdout, _ = self.run_main(["--read", "codex:codex-session"])
        self.assertEqual(status, 0)
        self.assertIn("ref    : codex:codex-session", stdout)
        self.assertIn("needle codex", stdout)
        self.assertNotIn("needle bootstrap", stdout)
        status, stdout, _ = self.run_main(["--read", "opencode:opencode-session"])
        self.assertEqual(status, 0)
        self.assertIn("ref    : opencode:opencode-session", stdout)
        self.assertIn("needle opencode", stdout)

    def test_explicit_missing_provider_fails_but_all_is_incomplete(self):
        missing = search_agent_logs.Roots(
            self.roots.claude_projects,
            self.roots.claude_archive,
            self.roots.codex_sessions.parent / "missing",
            self.roots.opencode_db,
            self.roots.pi_sessions,
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = search_agent_logs.main(["needle", "--codex"], missing)
        self.assertEqual(status, 2)
        self.assertIn("Codex sessions not found", stderr.getvalue())
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = search_agent_logs.main(["needle", "--all", "--scope", "all"], missing)
        self.assertEqual(status, 0)
        self.assertIn("(incomplete)", stdout.getvalue())
        self.assertIn("Codex sessions not found", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
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
            cursor_projects=root / "cursor" / "projects",
            cursor_chats=root / "cursor" / "chats",
            devin_db=root / "devin" / "sessions.db",
            droid_sessions=root / "droid-sessions",
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
        self.make_cursor_session("cursor-session", self.cwd, "needle cursor")
        self.make_devin_db("devin-session", self.cwd)
        self.make_droid_session("droid-session", self.cwd, "needle droid")
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

    def make_cursor_session(self, session_id: str, cwd: str, text: str) -> None:
        folder = (
            self.roots.cursor_projects / "work-app-dev1" / "agent-transcripts" / session_id
        )
        prompt = (
            "<timestamp>Monday, Aug 10, 2026, 12:07 PM (UTC+2)</timestamp>\n"
            f"<user_query>\n{text}\n</user_query>"
        )
        self.write_jsonl(
            folder / f"{session_id}.jsonl",
            [
                {"role": "user", "message": {"content": [{"type": "text", "text": prompt}]}},
                {
                    "role": "assistant",
                    "message": {
                        "content": [
                            {"type": "text", "text": "looking"},
                            {
                                "type": "tool_use",
                                "name": "Shell",
                                "input": {"command": "grep needle-in-cursor-tool"},
                            },
                        ]
                    },
                },
                {"type": "turn_ended", "status": "success"},
            ],
        )
        self.write_jsonl(
            folder / "subagents" / "cursor-subagent.jsonl",
            [{"role": "user", "message": {"content": [{"type": "text", "text": "needle subagent"}]}}],
        )
        meta = self.roots.cursor_chats / "hash" / session_id / "meta.json"
        meta.parent.mkdir(parents=True)
        meta.write_text(
            json.dumps(
                {
                    "createdAtMs": 1786356360000,
                    "updatedAtMs": 1786356480000,
                    "title": "Cursor title",
                    "cwd": cwd,
                }
            )
        )

    def make_devin_db(self, session_id: str, cwd: str) -> None:
        self.roots.devin_db.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.roots.devin_db)
        connection.executescript(
            """
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY, working_directory TEXT NOT NULL, backend_type TEXT,
                model TEXT, agent_mode TEXT, created_at INTEGER NOT NULL,
                last_activity_at INTEGER NOT NULL, title TEXT, main_chain_id INTEGER,
                hidden INTEGER NOT NULL DEFAULT 0, metadata TEXT
            );
            CREATE TABLE message_nodes (
                row_id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
                node_id INTEGER NOT NULL, parent_node_id INTEGER, chat_message TEXT NOT NULL,
                created_at INTEGER NOT NULL, metadata TEXT
            );
            CREATE TABLE subagent_heads (
                session_id TEXT NOT NULL, agent_id TEXT NOT NULL,
                chain_node_id INTEGER NOT NULL, updated_at INTEGER NOT NULL
            );
            """
        )
        connection.execute(
            "INSERT INTO sessions (id, working_directory, backend_type, model, agent_mode,"
            " created_at, last_activity_at, title, main_chain_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (session_id, cwd, "windsurf", "swe", "normal", 1786356000, 1786356360, "Devin title", 4),
        )
        connection.execute(
            "INSERT INTO subagent_heads VALUES (?, ?, ?, ?)", (session_id, "sidekick", 6, 1786356360)
        )

        def message(role: str, minute: int, content: str, source: str, **extra) -> str:
            metadata = {
                "created_at": f"2026-08-10T10:0{minute}:00Z",
                "telemetry": {"source": source},
                **extra.pop("metadata", {}),
            }
            return json.dumps({"role": role, "content": content, "metadata": metadata, **extra})

        prompt_metadata = {
            "is_user_input": True,
            "extensions": {"chisel/acp-content-blocks": [{"type": "text", "text": "needle devin"}]},
        }
        nodes = [
            (0, None, message("system", 0, "needle system prompt", "sysprompt")),
            (1, 0, message("user", 1, "expanded skill body\nneedle devin", "user",
                           metadata=prompt_metadata)),
            (2, 1, message("assistant", 2, "needle draft", "assistant")),
            (3, 1, message(
                "assistant", 3, "looking", "assistant",
                thinking={"thinking": "needle reasoning", "signature": "opaque"},
                tool_calls=[{"name": "exec", "arguments": {"command": "grep needle-in-devin-tool"}}],
            )),
            (4, 3, message("tool", 4, "needle in devin tool output", "tool_result")),
            (5, None, message("user", 5, "needle subagent task", "subagent_task",
                              metadata={"is_user_input": True})),
            (6, 5, message("assistant", 6, "needle from sidekick", "assistant")),
        ]
        connection.executemany(
            "INSERT INTO message_nodes (session_id, node_id, parent_node_id, chat_message,"
            " created_at) VALUES (?, ?, ?, ?, ?)",
            [(session_id, node, parent, chat, 1786356000) for node, parent, chat in nodes],
        )
        connection.commit()
        connection.close()

    def make_droid_session(self, session_id: str, cwd: str, text: str) -> None:
        folder = self.roots.droid_sessions / search_agent_logs.encode_claude_path(cwd)
        self.write_jsonl(
            folder / f"{session_id}.jsonl",
            [
                {
                    "type": "session_start",
                    "id": session_id,
                    "title": f"Title {session_id}",
                    "cwd": cwd,
                },
                {
                    "type": "message",
                    "timestamp": "2026-08-10T10:04:00Z",
                    "message": {
                        "role": "user",
                        "content": [],
                        "visibility": "user_only",
                        "hookEventName": "SessionStart",
                    },
                },
                {
                    "type": "message",
                    "timestamp": "2026-08-10T10:05:00Z",
                    "message": {"role": "user", "content": [{"type": "text", "text": text}]},
                },
                {
                    "type": "message",
                    "timestamp": "2026-08-10T10:06:00Z",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "tool_use", "name": "Bash", "input": {"command": "grep needle"}},
                            {"type": "tool_result", "content": "needle in tool output"},
                        ],
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
            "cursor:cursor-session",
            "cursor:cursor-subagent",
            "devin:devin-session",
            "droid:droid-session",
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

    def test_droid_session_is_read_with_title_and_visible_messages(self):
        status, stdout, _ = self.run_main(["--read", "droid:droid-session"])
        self.assertEqual(status, 0)
        self.assertIn("ref    : droid:droid-session", stdout)
        self.assertIn("title  : Title droid-session", stdout)
        self.assertIn(f"cwd    : {self.cwd}", stdout)
        self.assertIn("needle droid", stdout)
        self.assertEqual(stdout.count("[user/message]"), 1)

    def test_kind_filter_separates_conversation_from_tool_traffic(self):
        status, stdout, _ = self.run_main(
            ["needle", "--droid", "--cwd", self.cwd, "--kind", "message", "--max-snippets", "9"]
        )
        self.assertEqual(status, 0)
        self.assertIn("needle droid", stdout)
        self.assertNotIn("needle in tool output", stdout)
        status, stdout, _ = self.run_main(
            ["needle", "--droid", "--cwd", self.cwd, "--kind", "tool", "--max-snippets", "9"]
        )
        self.assertEqual(status, 0)
        self.assertIn("needle in tool output", stdout)
        self.assertNotIn("[user/message] needle droid", stdout)

    def test_score_ranks_conversation_above_tool_traffic(self):
        status, stdout, _ = self.run_main(
            ["needle", "--droid", "--cwd", self.cwd, "--format", "json"]
        )
        self.assertEqual(status, 0)
        result = json.loads(stdout)["results"][0]
        self.assertEqual(result["by_kind"], {"message": 1, "tool": 2})
        self.assertEqual(result["score"], 3.0 * 1 + 1.0 * 2)

    def test_json_search_output_carries_stable_fields(self):
        status, stdout, _ = self.run_main(
            ["needle", "--codex", "--cwd", self.cwd, "--format", "json"]
        )
        self.assertEqual(status, 0)
        payload = json.loads(stdout)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["sort"], "score")
        result = payload["results"][0]
        self.assertEqual(result["ref"], "codex:codex-session")
        self.assertEqual(result["cwd"], self.cwd)
        self.assertEqual(result["branch"], "feature")
        self.assertTrue(result["snippets"])

    def test_read_mode_controls_transcript_density(self):
        status, stdout, _ = self.run_main(["--read", "droid:droid-session", "--format", "json"])
        self.assertEqual(status, 0)
        lite = json.loads(stdout)
        self.assertEqual(lite["mode"], "lite")
        self.assertNotIn("needle in tool output", lite["body"])
        status, stdout, _ = self.run_main(
            ["--read", "droid:droid-session", "--mode", "log", "--format", "json"]
        )
        self.assertEqual(status, 0)
        log = json.loads(stdout)
        self.assertIn("needle in tool output", log["body"])
        self.assertGreater(log["total_chars"], lite["total_chars"])

    def test_read_truncates_with_a_resumable_offset(self):
        status, stdout, _ = self.run_main(
            ["--read", "droid:droid-session", "--format", "json", "--max-chars", "20"]
        )
        self.assertEqual(status, 0)
        first = json.loads(stdout)
        self.assertTrue(first["truncated"])
        self.assertEqual(first["returned_chars"], 20)
        self.assertEqual(first["next_offset"], 20)
        status, stdout, _ = self.run_main(
            [
                "--read",
                "droid:droid-session",
                "--format",
                "json",
                "--offset",
                str(first["next_offset"]),
            ]
        )
        self.assertEqual(status, 0)
        rest = json.loads(stdout)
        self.assertFalse(rest["truncated"])
        self.assertEqual(first["body"] + rest["body"], self.read_body("droid:droid-session"))

    def read_body(self, ref: str) -> str:
        _, stdout, _ = self.run_main(["--read", ref, "--format", "json"])
        return json.loads(stdout)["body"]

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
        missing = replace(self.roots, codex_sessions=self.roots.codex_sessions.parent / "missing")
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


    def run_timeline(self, arguments: list[str]) -> tuple[int, str, str]:
        with patch.dict(os.environ, {"TZ": "UTC"}):
            time.tzset()
            try:
                return self.run_main(["--timeline", "--scope", "all", *arguments])
            finally:
                time.tzset()

    def make_claude_timeline_session(self) -> None:
        folder = self.roots.claude_projects / search_agent_logs.encode_claude_path(self.cwd)
        def record(kind: str, stamp: str, content, **extra) -> dict:
            return {
                "type": kind,
                "cwd": self.cwd,
                "gitBranch": "main",
                "timestamp": f"2026-08-11T{stamp}:00Z",
                "message": {"role": kind, "content": content},
                **extra,
            }
        self.write_jsonl(
            folder / "claude-timeline.jsonl",
            [
                record("user", "09:00", "first prompt", origin={"kind": "human"}),
                record("assistant", "09:10", [{"type": "text", "text": "working"}]),
                record("user", "09:20", "second prompt"),
                record("user", "11:00", "peer note", isMeta=True, origin={"kind": "peer"}),
                record("assistant", "11:15", [{"type": "text", "text": "done"}]),
                record("user", "11:40", "summary", isCompactSummary=True),
                {"type": "ai-title", "aiTitle": "Timeline work"},
            ],
        )
        self.write_jsonl(
            folder / "claude-timeline" / "subagents" / "agent-1.jsonl",
            [record("user", "09:05", "subagent prompt")],
        )

    def test_timeline_splits_sessions_at_idle_gaps_and_counts_human_prompts(self):
        self.make_claude_timeline_session()
        status, stdout, stderr = self.run_timeline(
            ["--claude", "--since", "2026-08-11", "--until", "2026-08-11"]
        )
        self.assertEqual((status, stderr), (0, ""))
        self.assertIn("2026-08-11 09:00 \u2192 11:40  active 1h00m  claude:claude-timeline", stdout)
        self.assertIn("title  : Timeline work", stdout)
        self.assertIn("  09:00\u201309:20  20m, 2 prompt(s)", stdout)
        self.assertIn("  11:00\u201311:40  40m, 0 prompt(s)", stdout)
        self.assertIn("  2026-08-11  1h00m", stdout)
        self.assertEqual(stdout.count("=" * 70), 1)

    def test_timeline_json_clips_to_window_and_merges_overlapping_days(self):
        self.make_claude_timeline_session()
        status, stdout, _ = self.run_timeline(
            ["--since", "2026-08-10T10:01", "--until", "2026-08-11T09:15", "--format", "json"]
        )
        self.assertEqual(status, 0)
        payload = json.loads(stdout)
        refs = [session["ref"] for session in payload["sessions"]]
        self.assertEqual(
            refs,
            ["devin:devin-session", "opencode:opencode-session", "codex:codex-session",
             "pi:pi-session", "droid:droid-session", "cursor:cursor-session",
             "claude:claude-timeline"],
        )
        self.assertEqual(
            payload["sessions"][0]["spans"],
            [{"start": "2026-08-10T10:01:00+00:00", "end": "2026-08-10T10:06:00+00:00",
              "minutes": 5, "prompts": 1}],
        )
        claude = payload["sessions"][-1]
        self.assertEqual(
            claude["spans"],
            [{"start": "2026-08-11T09:00:00+00:00", "end": "2026-08-11T09:10:00+00:00",
              "minutes": 10, "prompts": 1}],
        )
        self.assertEqual(payload["daily_active_minutes"], {"2026-08-10": 6, "2026-08-11": 10})

    def test_cursor_session_takes_cwd_and_title_from_chat_metadata(self):
        status, stdout, _ = self.run_main(
            ["needle", "--cursor", "--cwd", self.cwd, "--scope", "current", "--format", "json"]
        )
        self.assertEqual(status, 0)
        results = {result["ref"]: result for result in json.loads(stdout)["results"]}
        self.assertEqual(sorted(results), ["cursor:cursor-session", "cursor:cursor-subagent"])
        session = results["cursor:cursor-session"]
        self.assertEqual(session["title"], "Cursor title")
        self.assertEqual(session["cwd"], self.cwd)
        self.assertEqual(session["first_ts"], "2026-08-10T10:06:00Z")
        self.assertEqual(session["last_ts"], "2026-08-10T10:08:00Z")
        self.assertEqual(results["cursor:cursor-subagent"]["cwd"], self.cwd)
        self.assertEqual(results["cursor:cursor-subagent"]["title"], "needle subagent")

    def test_cursor_read_strips_prompt_wrappers_and_keeps_tools_for_log_mode(self):
        status, stdout, _ = self.run_main(["--read", "cursor:cursor-session"])
        self.assertEqual(status, 0)
        self.assertIn("2026-08-10T10:07:00Z [user/message]\nneedle cursor\n", stdout)
        self.assertIn("[assistant/message]\nlooking", stdout)
        self.assertNotIn("needle-in-cursor-tool", stdout)
        status, stdout, _ = self.run_main(["--read", "cursor:cursor-session", "--mode", "log"])
        self.assertEqual(status, 0)
        self.assertIn("needle-in-cursor-tool", stdout)

    def test_cursor_without_chat_metadata_is_incomplete_and_scoped_out(self):
        shutil.rmtree(self.roots.cursor_chats)
        status, stdout, stderr = self.run_main(["needle", "--all", "--cwd", self.cwd])
        self.assertEqual(status, 0)
        self.assertIn("(incomplete)", stdout)
        self.assertIn("Cursor chat metadata unavailable", stderr)
        self.assertIn("claude:claude-live", stdout)
        status, stdout, _ = self.run_main(["needle", "--cursor", "--scope", "all"])
        self.assertEqual(status, 0)
        self.assertIn("cursor:cursor-session", stdout)

    def test_devin_search_reads_only_the_kept_main_and_subagent_chains(self):
        status, stdout, _ = self.run_main(
            ["needle", "--devin", "--cwd", self.cwd, "--scope", "current", "--format", "json",
             "--max-snippets", "9"]
        )
        self.assertEqual(status, 0)
        [result] = json.loads(stdout)["results"]
        self.assertEqual(result["ref"], "devin:devin-session")
        self.assertEqual(result["title"], "Devin title")
        self.assertEqual(result["cwd"], self.cwd)
        self.assertEqual(result["first_ts"], "2026-08-10T10:00:00Z")
        self.assertEqual(result["last_ts"], "2026-08-10T10:06:00Z")
        self.assertEqual(result["by_kind"], {"message": 3, "meta": 1, "tool": 2})

    def test_devin_read_shows_the_typed_prompt_and_keeps_tools_for_log_mode(self):
        status, stdout, _ = self.run_main(["--read", "devin:devin-session", "--format", "json"])
        self.assertEqual(status, 0)
        self.assertEqual(
            json.loads(stdout)["body"],
            "2026-08-10T10:01:00Z [user/message]\nneedle devin\n\n"
            "2026-08-10T10:03:00Z [assistant/message]\nlooking\n\n"
            "2026-08-10T10:05:00Z [user/message]\nneedle subagent task\n\n"
            "2026-08-10T10:06:00Z [assistant/message]\nneedle from sidekick\n\n",
        )
        status, stdout, _ = self.run_main(["--read", "devin:devin-session", "--mode", "log"])
        self.assertEqual(status, 0)
        self.assertIn('exec\n{"command": "grep needle-in-devin-tool"}', stdout)
        self.assertIn("[tool/tool]\nneedle in devin tool output", stdout)
        self.assertIn("[assistant/meta]\nneedle reasoning", stdout)

    def test_devin_missing_database_fails_when_selected(self):
        self.roots.devin_db.unlink()
        status, _, stderr = self.run_main(["needle", "--devin"])
        self.assertEqual(status, 2)
        self.assertIn("Devin database not found", stderr)
        self.assertFalse(self.roots.devin_db.exists())

    def test_timeline_requires_a_start(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit):
            search_agent_logs.main(["--timeline"], self.roots)
        self.assertIn("--timeline needs --since or --days", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

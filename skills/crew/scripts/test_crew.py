import json
import subprocess
from pathlib import Path

import pytest

import crew


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


def commit(cwd, name, content):
    (Path(cwd) / name).write_text(content)
    git(cwd, "add", name)
    git(cwd, "commit", "--quiet", "-m", f"chore: write {name}")
    return git(cwd, "rev-parse", "HEAD")


def run(monkeypatch, cwd, *argv):
    monkeypatch.chdir(cwd)
    return crew.main(list(argv))


@pytest.fixture(autouse=True)
def git_identity(monkeypatch):
    for key, value in {
        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
        "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
    }.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def clones(tmp_path, git_identity):
    origin = tmp_path / "origin"
    origin.mkdir()
    git(origin, "init", "--quiet", "-b", "main")
    commit(origin, "base.txt", "base\n")
    paths = {}
    for name in ("dev1", "dev2", "dev3"):
        git(tmp_path, "clone", "--quiet", str(origin), name)
        paths[name] = (tmp_path / name).resolve()
    return paths


@pytest.fixture
def crew_of_clones(clones, monkeypatch):
    lead = clones["dev1"]
    assert run(monkeypatch, lead, "init", "--session", "lead-session") == 0
    for name in ("dev2", "dev3"):
        assert run(monkeypatch, lead, "add", name, str(clones[name])) == 0
        assert run(monkeypatch, clones[name], "join") == 0
    return clones


def test_join_records_the_lead_and_catches_up(crew_of_clones, monkeypatch, capsys):
    lead, worker = crew_of_clones["dev1"], crew_of_clones["dev2"]
    tip = commit(lead, "lead.txt", "lead\n")
    git(worker, "checkout", "--quiet", "main")

    assert run(monkeypatch, worker, "sync") == 0

    assert git(worker, "rev-parse", "HEAD") == tip
    state = json.loads((worker / ".git" / "crew.json").read_text())
    assert state == {"role": "worker", "name": "dev2", "lead_path": str(lead)}


def test_integrate_fast_forwards_and_fans_out_to_idle_members(crew_of_clones, monkeypatch, capsys):
    lead, w2, w3 = crew_of_clones["dev1"], crew_of_clones["dev2"], crew_of_clones["dev3"]
    tip = commit(w2, "fix.txt", "fix\n")

    assert run(monkeypatch, lead, "integrate", "dev2") == 0

    assert git(lead, "rev-parse", "main") == tip
    assert git(w3, "rev-parse", "HEAD") == tip
    assert "dev3: fast-forwarded" in capsys.readouterr().out


def test_fan_out_skips_dirty_busy_and_unintegrated_members(crew_of_clones, tmp_path, monkeypatch, capsys):
    lead, w2, w3 = crew_of_clones["dev1"], crew_of_clones["dev2"], crew_of_clones["dev3"]
    before_w3 = git(w3, "rev-parse", "HEAD")
    (w3 / "base.txt").write_text("edited\n")
    w2_work = commit(w2, "work.txt", "work\n")
    commit(lead, "lead.txt", "lead\n")

    assert run(monkeypatch, lead, "sync", "--all") == 0

    out = capsys.readouterr().out
    assert "dev2: skipped, has unintegrated commits" in out
    assert "dev3: skipped, uncommitted changes" in out
    assert git(w2, "rev-parse", "HEAD") == w2_work
    assert git(w3, "rev-parse", "HEAD") == before_w3


def test_fan_out_honours_skip(crew_of_clones, monkeypatch, capsys):
    lead, w3 = crew_of_clones["dev1"], crew_of_clones["dev3"]
    before = git(w3, "rev-parse", "HEAD")
    commit(lead, "lead.txt", "lead\n")

    assert run(monkeypatch, lead, "sync", "--all", "--skip", "dev3") == 0

    assert "dev3: skipped (busy)" in capsys.readouterr().out
    assert git(w3, "rev-parse", "HEAD") == before


def test_stale_worker_must_rebase_before_it_can_be_integrated(crew_of_clones, monkeypatch):
    lead, w2, w3 = crew_of_clones["dev1"], crew_of_clones["dev2"], crew_of_clones["dev3"]
    commit(w2, "a.txt", "a\n")
    commit(w3, "b.txt", "b\n")
    assert run(monkeypatch, lead, "integrate", "dev2") == 0
    before = git(lead, "rev-parse", "main")

    assert run(monkeypatch, lead, "integrate", "dev3") == crew.EXIT_NOT_FF
    assert git(lead, "rev-parse", "main") == before
    assert run(monkeypatch, w3, "sync") == crew.EXIT_NOT_FF
    assert run(monkeypatch, w3, "sync", "--rebase") == 0
    assert run(monkeypatch, lead, "integrate", "dev3") == 0

    assert git(lead, "log", "--format=%s", "-2").splitlines() == ["chore: write b.txt", "chore: write a.txt"]


def test_rebase_conflict_stops_with_conflict_code(crew_of_clones, monkeypatch):
    lead, w2, w3 = crew_of_clones["dev1"], crew_of_clones["dev2"], crew_of_clones["dev3"]
    commit(w2, "same.txt", "two\n")
    commit(w3, "same.txt", "three\n")
    assert run(monkeypatch, lead, "integrate", "dev2", "--no-fan-out") == 0

    assert run(monkeypatch, w3, "sync", "--rebase") == crew.EXIT_CONFLICT

    assert (w3 / ".git" / "rebase-merge").exists()


def test_integrate_refused_by_uncommitted_edit_to_same_file(crew_of_clones, monkeypatch):
    lead, w2 = crew_of_clones["dev1"], crew_of_clones["dev2"]
    before = git(lead, "rev-parse", "main")
    commit(w2, "base.txt", "worker\n")
    (lead / "base.txt").write_text("user edit\n")

    assert run(monkeypatch, lead, "integrate", "dev2") == crew.EXIT_REFUSED

    assert git(lead, "rev-parse", "main") == before
    assert (lead / "base.txt").read_text() == "user edit\n"


def test_dry_run_lists_commits_without_moving_the_branch(crew_of_clones, monkeypatch, capsys):
    lead, w2 = crew_of_clones["dev1"], crew_of_clones["dev2"]
    before = git(lead, "rev-parse", "main")
    commit(w2, "fix.txt", "fix\n")

    assert run(monkeypatch, lead, "integrate", "dev2", "--dry-run") == 0

    assert "chore: write fix.txt" in capsys.readouterr().out
    assert git(lead, "rev-parse", "main") == before


def test_worktree_member_integrates_without_fetching(clones, monkeypatch, capsys):
    lead = clones["dev1"]
    assert run(monkeypatch, lead, "init") == 0
    assert run(monkeypatch, lead, "add", "w1", "--new-worktree") == 0
    worktree = lead.parent / "dev1-w1"
    assert git(worktree, "branch", "--show-current") == "crew/w1"
    assert run(monkeypatch, worktree, "join") == 0
    tip = commit(worktree, "fix.txt", "fix\n")

    assert run(monkeypatch, lead, "integrate", "w1") == 0

    assert git(lead, "rev-parse", "main") == tip


def test_join_from_unregistered_checkout_names_the_add_command(crew_of_clones, tmp_path, monkeypatch, capsys):
    lead = crew_of_clones["dev1"]
    stray = tmp_path / "stray"
    git(tmp_path, "clone", "--quiet", str(tmp_path / "origin"), "stray")

    assert run(monkeypatch, stray, "join") == crew.EXIT_ERROR

    assert f"crew add NAME {stray.resolve()}" in capsys.readouterr().err


def test_status_reports_each_member(crew_of_clones, monkeypatch, capsys):
    lead, w2 = crew_of_clones["dev1"], crew_of_clones["dev2"]
    commit(w2, "fix.txt", "fix\n")
    capsys.readouterr()

    assert run(monkeypatch, lead, "status") == 0

    out = capsys.readouterr().out
    assert "dev2: main @" in out and "1 unintegrated commit(s)" in out
    assert "dev3: main @" in out and "level with the integration branch" in out


@pytest.fixture
def invited(clones, monkeypatch):
    lead = clones["dev1"]
    assert run(monkeypatch, lead, "init", "--session", "lead-session") == 0
    assert run(monkeypatch, lead, "add", "dev2", str(clones["dev2"])) == 0
    return clones


@pytest.mark.parametrize("lead_arg", ["lead-session", "PATH"])
def test_join_accepts_the_lead_session_name_or_path(invited, monkeypatch, capsys, lead_arg):
    lead, worker = invited["dev1"], invited["dev2"]
    arg = str(lead) if lead_arg == "PATH" else lead_arg

    assert run(monkeypatch, worker, "join", arg) == 0

    assert "joined as dev2" in capsys.readouterr().out
    assert json.loads((worker / ".git" / "crew.json").read_text())["role"] == "worker"


def test_join_with_another_lead_name_is_refused(invited, monkeypatch, capsys):
    worker = invited["dev2"]

    assert run(monkeypatch, worker, "join", "other-lead") == crew.EXIT_ERROR

    assert f"this checkout was added by {invited['dev1']}" in capsys.readouterr().err
    assert json.loads((worker / ".git" / "crew.json").read_text())["role"] == "invited"


def test_status_in_an_invited_checkout_names_the_lead(invited, monkeypatch, capsys):
    assert run(monkeypatch, invited["dev2"], "status") == 0

    assert "invited as dev2 by lead-session" in capsys.readouterr().out


def test_a_member_of_one_crew_cannot_be_added_to_another(invited, monkeypatch, capsys):
    other_lead = invited["dev3"]
    assert run(monkeypatch, other_lead, "init") == 0

    assert run(monkeypatch, other_lead, "add", "dev2", str(invited["dev2"])) == crew.EXIT_ERROR
    assert f"`crew remove dev2`" in capsys.readouterr().err

    assert run(monkeypatch, invited["dev1"], "remove", "dev2") == 0
    assert not (invited["dev2"] / ".git" / "crew.json").exists()
    assert run(monkeypatch, other_lead, "add", "dev2", str(invited["dev2"])) == 0

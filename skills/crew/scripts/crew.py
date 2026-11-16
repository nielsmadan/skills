#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

STATE_FILE = "crew.json"
LEAD_REF = "refs/crew/lead"

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NOT_FF = 3
EXIT_REFUSED = 4
EXIT_CONFLICT = 5


class CrewError(Exception):
    def __init__(self, message, code=EXIT_ERROR):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Git:
    cwd: Path

    def run(self, *args, check=True):
        proc = subprocess.run(
            ["git", "-C", str(self.cwd), *args], capture_output=True, text=True
        )
        if check and proc.returncode != 0:
            raise CrewError(f"git {' '.join(args)} failed in {self.cwd}:\n{proc.stderr.strip()}")
        return proc

    def out(self, *args):
        return self.run(*args).stdout.strip()

    def ok(self, *args):
        return self.run(*args, check=False).returncode == 0


def toplevel(path):
    proc = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise CrewError(f"{path} is not inside a git checkout")
    return Path(proc.stdout.strip()).resolve()


def state_path(git):
    return Path(git.out("rev-parse", "--absolute-git-dir")) / STATE_FILE


def load_state(git):
    path = state_path(git)
    return json.loads(path.read_text()) if path.exists() else None


def save_state(git, state):
    state_path(git).write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def require_lead(git):
    state = load_state(git)
    if not state or state.get("role") != "lead":
        raise CrewError(f"{git.cwd} is not a crew lead; run `crew init` there first")
    return state


def require_worker(git):
    state = load_state(git)
    if not state or state.get("role") != "worker":
        raise CrewError(f"{git.cwd} has not joined a crew; run `crew join` first")
    return state


def current_branch(git):
    return git.out("branch", "--show-current")


def is_dirty(git):
    return bool(git.out("status", "--porcelain", "--untracked-files=no"))


def same_repo(a, b):
    return Path(a.out("rev-parse", "--path-format=absolute", "--git-common-dir")).resolve() == Path(
        b.out("rev-parse", "--path-format=absolute", "--git-common-dir")
    ).resolve()


def relation(git, head, tip):
    if head == tip:
        return "equal"
    if git.ok("merge-base", "--is-ancestor", head, tip):
        return "behind"
    if git.ok("merge-base", "--is-ancestor", tip, head):
        return "ahead"
    return "diverged"


def counts(git, base, tip):
    ahead = int(git.out("rev-list", "--count", f"{base}..{tip}"))
    behind = int(git.out("rev-list", "--count", f"{tip}..{base}"))
    return ahead, behind


def member_tip(lead_git, state, name):
    member = state["members"][name]
    if member["kind"] == "worktree":
        return lead_git.out("rev-parse", f"refs/heads/{member['branch']}")
    lead_git.out(
        "fetch", "--no-tags", "--quiet", member["path"],
        f"+refs/heads/{member['branch']}:refs/crew/{name}",
    )
    return lead_git.out("rev-parse", f"refs/crew/{name}")


def lead_tip_for(worker_git, lead_path, branch, kind):
    if kind == "worktree":
        return worker_git.out("rev-parse", f"refs/heads/{branch}")
    worker_git.out("fetch", "--no-tags", "--quiet", str(lead_path), f"+refs/heads/{branch}:{LEAD_REF}")
    return worker_git.out("rev-parse", LEAD_REF)


def describe(rel, ahead, behind):
    return {
        "equal": "level with the integration branch",
        "behind": f"behind by {behind}",
        "ahead": f"{ahead} unintegrated commit(s)",
        "diverged": f"{ahead} unintegrated commit(s), {behind} behind (needs `crew sync --rebase`)",
    }[rel]


def catch_up(worker_git, tip, rebase):
    head = worker_git.out("rev-parse", "HEAD")
    rel = relation(worker_git, head, tip)
    if rel == "equal":
        return "already level with the lead"
    if rel == "ahead":
        ahead, _ = counts(worker_git, tip, head)
        return f"contains the lead's tip; {ahead} unintegrated commit(s) on top"
    if is_dirty(worker_git):
        raise CrewError("uncommitted changes to tracked files; commit or stash them first", EXIT_REFUSED)
    if rel == "behind":
        worker_git.out("merge", "--ff-only", "--quiet", tip)
        return f"fast-forwarded {head[:9]} -> {tip[:9]}"
    if not rebase:
        ahead, behind = counts(worker_git, tip, head)
        raise CrewError(
            f"{ahead} unintegrated commit(s) and {behind} new on the lead; "
            "if this is finished work, run `crew sync --rebase`; if it should already be integrated, "
            "report it to the lead instead of resetting",
            EXIT_NOT_FF,
        )
    proc = worker_git.run("rebase", "--quiet", tip, check=False)
    if proc.returncode != 0:
        raise CrewError(
            "rebase stopped on a conflict; resolve it (resolve-conflicts), then `git rebase --continue`, "
            f"or `git rebase --abort`:\n{proc.stdout.strip()}\n{proc.stderr.strip()}",
            EXIT_CONFLICT,
        )
    return f"rebased onto {tip[:9]}; HEAD is {worker_git.out('rev-parse', '--short', 'HEAD')}"


def cmd_init(args):
    git = Git(toplevel(Path.cwd()))
    state = load_state(git)
    if state and state.get("role") in ("worker", "invited"):
        raise CrewError("this checkout is a crew worker; a lead lives in its own checkout")
    branch = args.branch or current_branch(git)
    if not branch:
        raise CrewError("detached HEAD; pass --branch")
    if current_branch(git) != branch:
        raise CrewError(f"the lead must have {branch} checked out; it has {current_branch(git) or 'a detached HEAD'}")
    members = (state or {}).get("members", {})
    session = args.session or (state or {}).get("lead_session")
    save_state(git, {"role": "lead", "integration_branch": branch, "lead_session": session,
                     "lead_path": str(git.cwd), "members": members})
    print(f"lead: {git.cwd} · integration branch: {branch} · session: {session or '(unset)'}")
    print(f"tip: {git.out('rev-parse', '--short', branch)}")


def cmd_add(args):
    lead = Git(toplevel(Path.cwd()))
    state = require_lead(lead)
    branch = state["integration_branch"]
    if args.name in state["members"]:
        raise CrewError(f"{args.name} is already a member; `crew remove {args.name}` first")
    if args.new_worktree:
        path = Path(args.path or lead.cwd.parent / f"{lead.cwd.name}-{args.name}").resolve()
        worker_branch = f"crew/{args.name}"
        lead.out("worktree", "add", "--quiet", str(path), "-b", worker_branch, branch)
        member = {"path": str(path), "branch": worker_branch, "kind": "worktree"}
    else:
        if not args.path:
            raise CrewError("pass the checkout path, or --new-worktree")
        path = toplevel(args.path)
        if path == lead.cwd:
            raise CrewError("that is the lead's own checkout")
        worker = Git(path)
        worker_branch = current_branch(worker)
        if not worker_branch:
            raise CrewError(f"{path} has a detached HEAD; check out a branch there first")
        kind = "worktree" if same_repo(lead, worker) else "clone"
        if kind == "worktree" and worker_branch == branch:
            raise CrewError(f"{path} is a worktree on {branch}; a worker needs its own branch")
        member = {"path": str(path), "branch": worker_branch, "kind": kind}
        existing = load_state(worker) or {}
        if existing.get("role") == "lead":
            raise CrewError(f"{path} is itself a crew lead")
        if existing.get("lead_path") not in (None, str(lead.cwd)):
            raise CrewError(f"{path} already belongs to the crew led from {existing['lead_path']}; "
                            f"that lead runs `crew remove {existing.get('name')}` first")
        tip = member_tip(lead, {**state, "members": {args.name: member}}, args.name)
        if not lead.ok("merge-base", tip, branch):
            raise CrewError(f"{path} shares no history with {branch}")
    save_state(Git(Path(member["path"])), {"role": "invited", "name": args.name, "lead_path": str(lead.cwd)})
    state["members"][args.name] = member
    save_state(lead, state)
    print(f"added {args.name}: {member['path']} ({member['kind']}, branch {member['branch']})")
    print(f"in that checkout: start a session, name it {args.name}, and run `crew join`")


def cmd_remove(args):
    lead = Git(toplevel(Path.cwd()))
    state = require_lead(lead)
    member = state["members"].pop(args.name, None)
    if not member:
        raise CrewError(f"no member {args.name}")
    save_state(lead, state)
    path = Path(member["path"])
    if path.exists():
        worker = Git(path)
        if (load_state(worker) or {}).get("lead_path") == str(lead.cwd):
            state_path(worker).unlink()
    print(f"removed {args.name} from the crew; its checkout and branch are untouched")
    if member["kind"] == "worktree":
        print(f"to delete them: git worktree remove {member['path']} && git branch -d {member['branch']}")


def resolve_lead(worker, lead_arg):
    own = load_state(worker) or {}
    invited_by = Path(own["lead_path"]) if own.get("role") in ("invited", "worker") else None
    if invited_by and invited_by.exists():
        session = (load_state(Git(invited_by)) or {}).get("lead_session")
        if lead_arg in (None, session, str(invited_by)):
            return invited_by
    if lead_arg and Path(lead_arg).is_dir():
        return toplevel(lead_arg)
    if lead_arg:
        found = f"this checkout was added by {invited_by}" if invited_by else "no lead has added this checkout"
        raise CrewError(f"{lead_arg} is neither the lead session that added this checkout nor a directory "
                        f"({found}); the lead runs `crew add NAME {worker.cwd}`")
    raise CrewError(f"no lead has added this checkout; the lead runs `crew add NAME {worker.cwd}`, "
                    "or pass the lead's checkout path")


def cmd_join(args):
    worker = Git(toplevel(Path.cwd()))
    lead_path = resolve_lead(worker, args.lead)
    if lead_path == worker.cwd:
        raise CrewError("this is the lead's checkout; join from a worker checkout")
    lead_state = require_lead(Git(lead_path))
    names = [n for n, m in lead_state["members"].items() if Path(m["path"]).resolve() == worker.cwd]
    if not names:
        listed = ", ".join(f"{n}={m['path']}" for n, m in lead_state["members"].items()) or "none"
        raise CrewError(f"{worker.cwd} is not registered with the lead (members: {listed}); "
                        f"the lead runs `crew add NAME {worker.cwd}`")
    name = names[0]
    member = lead_state["members"][name]
    if current_branch(worker) != member["branch"]:
        raise CrewError(f"registered on branch {member['branch']}, but {current_branch(worker) or 'detached HEAD'} "
                        "is checked out")
    save_state(worker, {"role": "worker", "name": name, "lead_path": str(lead_path)})
    tip = lead_tip_for(worker, lead_path, lead_state["integration_branch"], member["kind"])
    outcome = catch_up(worker, tip, rebase=False)
    print(f"joined as {name} · lead {lead_path} · session {lead_state.get('lead_session') or '(unset)'}")
    print(f"checkout {worker.cwd} · branch {member['branch']} · integration branch "
          f"{lead_state['integration_branch']}")
    print(f"sync: {outcome}")
    print(f"HEAD {worker.out('rev-parse', '--short', 'HEAD')}")


def worker_context(worker):
    state = require_worker(worker)
    lead_path = Path(state["lead_path"])
    lead_state = require_lead(Git(lead_path))
    member = lead_state["members"].get(state["name"])
    if not member:
        raise CrewError(f"the lead no longer lists {state['name']}")
    return state, lead_path, lead_state, member


def sync_all(lead, state, skip):
    branch = state["integration_branch"]
    tip = lead.out("rev-parse", branch)
    for name, member in sorted(state["members"].items()):
        path = Path(member["path"])
        if name in skip:
            print(f"{name}: skipped (busy)")
            continue
        if not path.exists():
            print(f"{name}: skipped, {path} is missing")
            continue
        worker = Git(path)
        if current_branch(worker) != member["branch"]:
            print(f"{name}: skipped, {current_branch(worker) or 'detached HEAD'} is checked out, "
                  f"not {member['branch']}")
            continue
        try:
            lead_tip = lead_tip_for(worker, lead.cwd, branch, member["kind"])
            rel = relation(worker, worker.out("rev-parse", "HEAD"), lead_tip)
            if rel in ("ahead", "diverged"):
                print(f"{name}: skipped, has unintegrated commits")
                continue
            print(f"{name}: {catch_up(worker, lead_tip, rebase=False)}")
        except CrewError as err:
            print(f"{name}: skipped, {err}")
    return tip


def cmd_sync(args):
    here = Git(toplevel(Path.cwd()))
    state = load_state(here)
    if state and state.get("role") == "lead":
        if not args.all:
            raise CrewError("this is the lead; `crew sync --all` brings the members up to date")
        sync_all(here, state, set(args.skip or []))
        return
    if args.all:
        raise CrewError("--all runs from the lead's checkout")
    _, lead_path, lead_state, member = worker_context(here)
    if current_branch(here) != member["branch"]:
        raise CrewError(f"check out {member['branch']} first")
    tip = lead_tip_for(here, lead_path, lead_state["integration_branch"], member["kind"])
    print(catch_up(here, tip, rebase=args.rebase))


def cmd_integrate(args):
    lead = Git(toplevel(Path.cwd()))
    state = require_lead(lead)
    branch = state["integration_branch"]
    if args.name not in state["members"]:
        raise CrewError(f"no member {args.name}")
    if current_branch(lead) != branch:
        raise CrewError(f"the lead must have {branch} checked out")
    base = lead.out("rev-parse", branch)
    tip = member_tip(lead, state, args.name)
    rel = relation(lead, tip, base)
    if rel in ("equal", "behind"):
        print(f"{args.name}: nothing to integrate")
        return
    if rel == "diverged":
        ahead, behind = counts(lead, base, tip)
        raise CrewError(
            f"{args.name} is not on top of {branch} ({ahead} unintegrated, {behind} behind); "
            f"ask {args.name} to run `crew sync --rebase` and re-report",
            EXIT_NOT_FF,
        )
    print(lead.out("log", "--reverse", "--format=%h %s", "--shortstat", f"{base}..{tip}"))
    if args.dry_run:
        print(f"dry run: {branch} would fast-forward {base[:9]} -> {tip[:9]}")
        return
    proc = lead.run("merge", "--ff-only", "--quiet", tip, check=False)
    if proc.returncode != 0:
        raise CrewError(
            f"git refused the fast-forward, usually because of uncommitted edits to the same files:\n"
            f"{proc.stderr.strip()}\nonce they are resolved: git merge --ff-only {tip}",
            EXIT_REFUSED,
        )
    print(f"{branch}: {base[:9]} -> {tip[:9]}")
    if args.fan_out:
        sync_all(lead, state, set(args.skip or []) | {args.name})


def cmd_status(args):
    here = Git(toplevel(Path.cwd()))
    state = load_state(here)
    if not state:
        raise CrewError(f"{here.cwd} is not part of a crew")
    if state["role"] == "invited":
        lead_state = load_state(Git(Path(state["lead_path"]))) or {}
        print(f"invited as {state['name']} by {lead_state.get('lead_session') or state['lead_path']}; "
              "run `crew join` to take briefs")
        return
    if state["role"] == "worker":
        _, lead_path, lead_state, member = worker_context(here)
        tip = lead_tip_for(here, lead_path, lead_state["integration_branch"], member["kind"])
        head = here.out("rev-parse", "HEAD")
        ahead, behind = counts(here, tip, head)
        print(f"worker {state['name']} · lead {lead_path} · session {lead_state.get('lead_session') or '(unset)'}")
        print(f"branch {current_branch(here)} @ {head[:9]} · {describe(relation(here, head, tip), ahead, behind)}"
              f"{' · dirty' if is_dirty(here) else ''}")
        return
    branch = state["integration_branch"]
    base = here.out("rev-parse", branch)
    print(f"lead {here.cwd} · {branch} @ {base[:9]} · session {state.get('lead_session') or '(unset)'}")
    for name, member in sorted(state["members"].items()):
        path = Path(member["path"])
        if not path.exists():
            print(f"  {name}: {path} is missing")
            continue
        worker = Git(path)
        joined = (load_state(worker) or {}).get("role") == "worker"
        try:
            tip = member_tip(here, state, name)
        except CrewError as err:
            print(f"  {name}: {err}")
            continue
        ahead, behind = counts(here, base, tip)
        flags = [member["kind"], "joined" if joined else "not joined"]
        if is_dirty(worker):
            flags.append("dirty")
        if current_branch(worker) != member["branch"]:
            flags.append(f"on {current_branch(worker) or 'detached HEAD'}")
        print(f"  {name}: {member['branch']} @ {tip[:9]} · {describe(relation(here, tip, base), ahead, behind)} · "
              f"{', '.join(flags)} · {path}")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="crew", description="Local git plumbing for a crew: one lead checkout, worker checkouts, no pushes."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="make this checkout the lead")
    p.add_argument("--branch", help="integration branch (default: the current branch)")
    p.add_argument("--session", help="the lead session's name, for workers to message")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("add", help="register a worker checkout (lead)")
    p.add_argument("name")
    p.add_argument("path", nargs="?", help="existing checkout, or the new worktree's path")
    p.add_argument("--new-worktree", action="store_true", help="create a worktree on branch crew/NAME")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("remove", help="unregister a worker; leaves its checkout alone (lead)")
    p.add_argument("name")
    p.set_defaults(func=cmd_remove)

    p = sub.add_parser("join", help="join the crew whose lead added this checkout (worker)")
    p.add_argument("lead", nargs="?", help="the lead's session name or checkout path, to confirm or override")
    p.set_defaults(func=cmd_join)

    p = sub.add_parser("sync", help="catch up to the lead (worker), or fan out to every member (--all, lead)")
    p.add_argument("--rebase", action="store_true", help="rebase unintegrated commits onto the lead's tip")
    p.add_argument("--all", action="store_true")
    p.add_argument("--skip", action="append", help="member to leave alone (repeatable)")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("integrate", help="fast-forward the integration branch to a worker's branch (lead)")
    p.add_argument("name")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-fan-out", dest="fan_out", action="store_false",
                   help="do not bring the other members up to date afterwards")
    p.add_argument("--skip", action="append", help="member to leave out of the fan-out (repeatable)")
    p.set_defaults(func=cmd_integrate)

    p = sub.add_parser("status", help="where every member stands against the integration branch")
    p.set_defaults(func=cmd_status)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        args.func(args)
    except CrewError as err:
        print(f"crew: {err}", file=sys.stderr)
        return err.code
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())

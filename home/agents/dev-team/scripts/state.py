#!/usr/bin/env python3
"""Local state and verification for explicitly invoked development-team runs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone

ACTIVE_STAGES = {"feedback", "specifying", "awaiting_approval", "implementing", "verifying", "reviewing", "fixing"}
AXES = ("standards", "spec", "impact")
DEFAULT_AXES = ["standards", "spec"]
STAGES = ACTIVE_STAGES | {"ready_local", "needs_input", "blocked", "cancelled"}


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, stdout=subprocess.PIPE).stdout


def root_of(path):
    return Path(os.fsdecode(git(path, "rev-parse", "--show-toplevel")).strip()).resolve()


def home_for(root):
    digest = hashlib.sha256(os.fsencode(root)).hexdigest()[:10]
    return Path.home() / "claude-plans" / root.name / "dev-team" / digest


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".state-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_active(root):
    pointer = home_for(root) / "active.json"
    if not pointer.exists():
        raise ValueError("No active development-team run")
    run_file = Path(json.loads(pointer.read_text())["stateFile"])
    state = json.loads(run_file.read_text())
    if state["repo"] != str(root):
        raise ValueError("Run belongs to a different repository")
    return run_file, state


def fingerprint(root, base):
    h = hashlib.sha256()
    h.update(git(root, "rev-parse", "HEAD"))
    h.update(git(root, "diff", "--binary", base))
    h.update(git(root, "status", "--porcelain=v1", "-z"))
    raw = git(root, "ls-files", "--others", "--exclude-standard", "-z")
    for name in sorted(part for part in raw.split(b"\0") if part):
        path = root / os.fsdecode(name)
        h.update(name)
        if path.is_symlink():
            h.update(os.fsencode(os.readlink(path)))
        elif path.is_file():
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(chunk)
    return h.hexdigest()


def split(value):
    return [part.strip() for part in value.split(",") if part.strip()]


def split_axes(value):
    axes = split(value)
    bad = [axis for axis in axes if axis not in AXES]
    if bad:
        raise ValueError("Unknown review axis: " + ", ".join(bad))
    return axes


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("start", "require", "status", "approve", "stage", "snapshot", "check", "review", "finish"):
        command = sub.add_parser(name)
        command.add_argument("--repo", required=True)
        if name in ("start", "require"):
            command.add_argument("--axes", default="", help="comma list of required review axes: standards,spec,impact")
            command.add_argument("--checks", default="", help="comma list of required check names")
        if name == "start":
            command.add_argument("--session", default="")
        if name == "approve":
            command.add_argument("--spec", required=True)
            command.add_argument("--plan", required=True)
        if name == "stage":
            command.add_argument("--name", choices=sorted(ACTIVE_STAGES), required=True)
        if name == "check":
            command.add_argument("--name", required=True)
            command.add_argument("command", nargs=argparse.REMAINDER)
        if name == "review":
            command.add_argument("--axis", choices=AXES, required=True)
            command.add_argument("--verdict", choices=("pass", "fail"), required=True)
            command.add_argument("--evidence", required=True)
        if name == "finish":
            command.add_argument("--name", choices=("ready_local", "blocked", "cancelled"), required=True)
    args = parser.parse_args()
    root = root_of(Path(args.repo))
    if args.action == "start":
        try:
            _, old = read_active(root)
            if old["stage"] in ACTIVE_STAGES | {"needs_input"}:
                raise ValueError("An unfinished run already exists: " + old["runId"])
        except ValueError as error:
            if not str(error).startswith("No active"):
                raise
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
        run_file = home_for(root) / run_id / "state.json"
        base = git(root, "rev-parse", "HEAD").decode().strip()
        state = {"runId": run_id, "repo": str(root), "sessionId": args.session,
                 "baseSha": base, "baselineSnapshot": fingerprint(root, base),
                 "stage": "specifying", "approval": None, "checks": {}, "reviewSnapshot": None, "reviews": {},
                 "requiredAxes": split_axes(args.axes) or DEFAULT_AXES, "requiredChecks": split(args.checks)}
        atomic_json(run_file, state)
        atomic_json(home_for(root) / "active.json", {"stateFile": str(run_file)})
        print(run_file)
        return
    run_file, state = read_active(root)
    if args.action == "require":
        if state["stage"] in ("reviewing", "ready_local"):
            raise ValueError("Required checks and axes can only change before review")
        if args.axes:
            state["requiredAxes"] = split_axes(args.axes)
        if args.checks:
            state["requiredChecks"] = split(args.checks)
        atomic_json(run_file, state)
        print(json.dumps({"requiredAxes": state["requiredAxes"], "requiredChecks": state["requiredChecks"]}))
        return
    if args.action == "status":
        print(json.dumps(state, indent=2))
        return
    if args.action == "snapshot":
        print(fingerprint(root, state["baseSha"]))
        return
    if args.action == "approve":
        if state["stage"] not in ("specifying", "awaiting_approval", "needs_input"):
            raise ValueError("Approval is only valid before implementation")
        for value in (args.spec, args.plan):
            artifact = Path(value).resolve()
            if not artifact.is_file() or run_file.parent.resolve() not in artifact.parents:
                raise ValueError("Approved artifact must be inside the run directory: " + value)
        state["approval"] = {"spec": str(Path(args.spec).resolve()),
                             "plan": str(Path(args.plan).resolve()),
                             "specHash": hashlib.sha256(Path(args.spec).read_bytes()).hexdigest(),
                             "planHash": hashlib.sha256(Path(args.plan).read_bytes()).hexdigest(),
                             "at": datetime.now(timezone.utc).isoformat()}
        state["stage"] = "implementing"
    elif args.action == "stage":
        if args.name in ("implementing", "verifying", "reviewing", "fixing") and not state["approval"]:
            raise ValueError("Spec and plan approval required")
        state["stage"] = args.name
        if args.name == "reviewing":
            state["reviewSnapshot"] = fingerprint(root, state["baseSha"])
    elif args.action == "check":
        if not state["approval"]:
            raise ValueError("Spec and plan approval required")
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        if not command:
            raise ValueError("Verification command required")
        before = fingerprint(root, state["baseSha"])
        result = subprocess.run(command, cwd=str(root), check=False)
        after = fingerprint(root, state["baseSha"])
        state["checks"][args.name] = {"command": command, "exitCode": result.returncode,
                                     "snapshot": after, "changedDuringCheck": before != after}
        atomic_json(run_file, state)
        raise SystemExit(result.returncode)
    elif args.action == "review":
        current = fingerprint(root, state["baseSha"])
        if state["stage"] != "reviewing" or state["reviewSnapshot"] != current:
            raise ValueError("Review requires a frozen current snapshot")
        evidence = Path(args.evidence).resolve()
        if not evidence.is_file():
            raise ValueError("Review evidence file does not exist")
        state["reviews"][args.axis] = {"verdict": args.verdict, "evidence": str(evidence),
                                       "evidenceHash": hashlib.sha256(evidence.read_bytes()).hexdigest(),
                                       "snapshot": current}
    elif args.action == "finish":
        if args.name == "ready_local":
            current = fingerprint(root, state["baseSha"])
            if not state["approval"] or not state["checks"]:
                raise ValueError("Approval and checks required")
            missing = [name for name in state.get("requiredChecks", []) if name not in state["checks"]]
            if missing:
                raise ValueError("Required checks not run: " + ", ".join(missing))
            if hashlib.sha256(Path(state["approval"]["spec"]).read_bytes()).hexdigest() != state["approval"]["specHash"] or hashlib.sha256(Path(state["approval"]["plan"]).read_bytes()).hexdigest() != state["approval"]["planHash"]:
                raise ValueError("Approved spec or plan changed")
            if any(item["exitCode"] or item["changedDuringCheck"] or item["snapshot"] != current
                   for item in state["checks"].values()):
                raise ValueError("Checks are failed or stale")
            if state["reviewSnapshot"] != current:
                raise ValueError("Review snapshot is missing or stale")
            required = set(state.get("requiredAxes", DEFAULT_AXES))
            if not required <= set(state["reviews"]):
                raise ValueError("Review axes required: " + ", ".join(sorted(required - set(state["reviews"]))))
            for review in state["reviews"].values():
                if review["verdict"] != "pass" or review["snapshot"] != current or hashlib.sha256(Path(review["evidence"]).read_bytes()).hexdigest() != review["evidenceHash"]:
                    raise ValueError("A review failed or is stale")
        state["stage"] = args.name
    atomic_json(run_file, state)
    print(run_file)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, subprocess.CalledProcessError, OSError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)

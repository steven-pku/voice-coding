#!/usr/bin/env python3
"""Local coordination records. No model calls, task dispatch, or authorization engine."""

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.1"
SCHEMA = "voice-coding/board-v1"
FRESH_SECONDS = 300
TERMINAL_STATES = {"closed", "cancelled"}
STATES = {"planned", "active", "worker_complete", "verified"} | TERMINAL_STATES
NATIVE_STATES = {"running", "completed", "failed", "unknown"}


class BoardError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise BoardError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def nonempty(value):
    return isinstance(value, str) and 0 < len(value.strip()) <= 2000


def age(stamp):
    require(isinstance(stamp, str), "timestamp must be a string")
    try:
        parsed = datetime.fromisoformat(stamp)
        require(parsed.tzinfo is not None, "timestamp must include timezone")
        seconds = (datetime.now(timezone.utc) - parsed).total_seconds()
    except (ValueError, TypeError) as exc:
        raise BoardError("invalid timestamp") from exc
    require(seconds >= -5, "timestamp is in the future")
    return max(0, seconds)


def exact_keys(value, keys, label):
    require(isinstance(value, dict) and set(value) == set(keys.split()),
            f"invalid {label} fields")


def ref(value):
    exact_keys(value, "task_id host", "native identity")
    require(all(nonempty(v) for v in value.values()), "identity must be nonempty")
    return value["host"], value["task_id"]


def digest(path):
    with Path(path).open("rb") as stream:
        h = hashlib.sha256()
        for block in iter(lambda: stream.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def historical_path(value):
    require(nonempty(value), "historical path required")
    p = Path(value)
    require(p.is_absolute() and str(p) == value and os.path.normpath(value) == value,
            "historical path must be absolute and normalized")
    return p


def within(root, value, historical=False):
    if historical:
        p = historical_path(value)
        require(p == root or root in p.parents, "path escapes project root")
        return p
    p = Path(value).expanduser()
    p = (p if p.is_absolute() else root / p).resolve()
    require(p == root or root in p.parents, "path escapes project root")
    return p


def validate(board):
    exact_keys(board, "schema revision controller tasks", "board")
    require(board["schema"] == SCHEMA, "unsupported board schema")
    require(type(board["revision"]) is int and board["revision"] >= 1,
            "revision must be a positive integer")
    controller = ref(board["controller"])
    identities = set()
    require(isinstance(board["tasks"], list), "tasks must be a list")
    keys, requests, scopes = set(), set(), []
    for task in board["tasks"]:
        exact_keys(task, "key title project_root write_scope request_ref native state hold "
                   "observation verification closure events" +
                   (" cancellation" if "cancellation" in task else ""), "task")
        key = task["key"]
        require(isinstance(key, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", key),
                "task key must be a lowercase slug")
        require(key not in keys, "duplicate task key")
        keys.add(key)
        require(nonempty(task["title"]) and nonempty(task["request_ref"]),
                "title and request reference required")
        require(task["request_ref"] not in requests, "duplicate request reference")
        requests.add(task["request_ref"])
        require(task["state"] in STATES, "invalid coordination state")
        terminal = task["state"] in TERMINAL_STATES
        require(nonempty(task["project_root"]), "project root required")
        root = Path(task["project_root"])
        if terminal:
            historical_path(task["project_root"])
        else:
            require(root.is_absolute() and root.resolve() == root, "project root is not canonical")
        require(isinstance(task["write_scope"], list), "write scope must be a list")
        own = []
        for value in task["write_scope"]:
            require(nonempty(value), "write path required")
            path = within(root, value, historical=terminal)
            require(str(path) == value, "write scope changed or is not canonical")
            require(path not in own, "duplicate write scope")
            own.append(path)
        if not terminal:
            for path in own:
                for other_key, other in scopes:
                    # Conservatively reserve case aliases even on case-sensitive hosts.
                    folded_path, folded_other = Path(str(path).casefold()), Path(str(other).casefold())
                    require(other_key == key or not (
                        folded_path == folded_other or folded_path in folded_other.parents or
                        folded_other in folded_path.parents),
                            f"write scope conflict: {key} and {other_key}")
                scopes.append((key, path))
        if task["native"] is not None:
            identity = ref(task["native"])
            require(identity != controller, "controller identity cannot be reused")
            if not terminal:
                require(identity not in identities, "duplicate active native identity")
                identities.add(identity)
        require(task["state"] in {"planned", "cancelled"} or task["native"] is not None,
                "bound task identity required")
        if task["hold"] is not None:
            exact_keys(task["hold"], "reason request_ref at", "hold")
            require(nonempty(task["hold"]["reason"]) and nonempty(task["hold"]["request_ref"]),
                    "hold reason and request reference required")
            age(task["hold"]["at"])
            require(task["state"] != "closed", "closed task cannot be held")
        observation = task["observation"]
        if observation is not None:
            exact_keys(observation, "state evidence at", "observation")
            require(task["native"] is not None, "cannot observe an unbound task")
            require(observation["state"] in NATIVE_STATES and nonempty(observation["evidence"]),
                    "invalid observation")
            age(observation["at"])
        verification = task["verification"]
        if verification is not None:
            exact_keys(verification, "artifacts check evidence at", "verification")
            require(nonempty(verification["check"]) and nonempty(verification["evidence"]),
                    "verification evidence required")
            age(verification["at"])
            require(isinstance(verification["artifacts"], list) and verification["artifacts"],
                    "verification artifacts required")
            for artifact in verification["artifacts"]:
                exact_keys(artifact, "path sha256", "artifact")
                require(nonempty(artifact["path"]), "artifact path required")
                require(str(within(root, artifact["path"], historical=terminal)) == artifact["path"],
                        "artifact path changed")
                require(isinstance(artifact["sha256"], str) and
                        re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]), "invalid artifact hash")
        if task["state"] in {"worker_complete", "verified", "closed"}:
            require(observation is not None and observation["state"] == "completed",
                    "completed observation required")
        if task["state"] in {"verified", "closed"}:
            require(verification is not None, "verification record required")
        elif task["state"] != "cancelled":
            require(verification is None, "verification attached to unverified state")
        if task["closure"] is not None:
            exact_keys(task["closure"], "evidence at", "closure")
            require(nonempty(task["closure"]["evidence"]), "closure evidence required")
            age(task["closure"]["at"])
        require((task["state"] == "closed") == (task["closure"] is not None),
                "closure/state mismatch")
        require((task["state"] == "cancelled") == ("cancellation" in task),
                "cancellation/state mismatch")
        if task["state"] == "cancelled":
            cancellation = task["cancellation"]
            exact_keys(cancellation, "request_ref evidence outcome at", "cancellation")
            require(nonempty(cancellation["request_ref"]) and nonempty(cancellation["evidence"]),
                    "explicit cancellation request and reconciliation evidence required")
            require(cancellation["request_ref"] != task["request_ref"] and
                    (task["hold"] is None or
                     cancellation["request_ref"] != task["hold"]["request_ref"]),
                    "cancellation requires its own user request")
            age(cancellation["at"])
            if task["native"] is None:
                require(cancellation["outcome"] == "not_created" and observation is None and
                        verification is None, "unbound cancellation requires confirmed non-creation")
            else:
                require(cancellation["outcome"] == "stopped" and observation is not None and
                        observation["state"] in {"failed", "completed"},
                        "bound cancellation requires confirmed terminal execution")
        require(isinstance(task["events"], list) and task["events"], "events required")
        for event in task["events"]:
            exact_keys(event, "action evidence at", "event")
            require(nonempty(event["action"]) and nonempty(event["evidence"]), "event evidence required")
            age(event["at"])
    return board


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON field; preserve and reconcile the board")
        result[key] = value
    return result


def load(path):
    require(not path.is_symlink(), "board must not be a symlink")
    require(path.stat().st_nlink == 1, "board must not be hard-linked")
    try:
        return validate(json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object))
    except json.JSONDecodeError as exc:
        raise BoardError("invalid board JSON; preserve it and recover from evidence") from exc


@contextmanager
def locked(path):
    lock = path.with_name(path.name + ".lock")
    try:
        fd = os.open(str(lock), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise BoardError("board is locked; do not retry mutations until the writer is reconciled") from exc
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink()


def save(path, board):
    validate(board)
    require(not path.is_symlink(), "board must not be a symlink")
    fd, temporary = tempfile.mkstemp(prefix=".voice-coding-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(board, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def event(task, action, evidence):
    require(nonempty(evidence), "evidence/request reference required")
    task["events"].append({"action": action, "evidence": evidence, "at": now()})


def mutate(board, args):
    command = args.command
    if command == "register":
        root = Path(args.project_root).expanduser().resolve(strict=True)
        require(root.is_dir(), "project root must be a directory")
        task = {"key": args.key, "title": args.title, "project_root": str(root),
                "write_scope": [str(within(root, p)) for p in args.write],
                "request_ref": args.request_ref, "native": None, "state": "planned",
                "hold": None, "observation": None, "verification": None,
                "closure": None, "events": []}
        event(task, command, args.request_ref)
        board["tasks"].append(task)
        return
    matches = [t for t in board["tasks"] if t["key"] == args.key]
    require(len(matches) == 1, "unknown task key")
    task = matches[0]
    require(task["state"] not in TERMINAL_STATES,
            "terminal task is immutable; use a new request key")
    if command == "cancel":
        require(nonempty(args.request_ref) and nonempty(args.evidence),
                "explicit cancellation request and reconciliation evidence required")
        if task["native"] is None:
            require(args.outcome == "not_created", "confirm non-creation before cancelling")
        else:
            observation = task["observation"]
            require(args.outcome == "stopped" and observation is not None and
                    observation["state"] in {"failed", "completed"},
                    "confirm stopped execution with a terminal observation before cancelling")
            require(age(observation["at"]) <= FRESH_SECONDS,
                    "observation is stale; exact-read again")
        task["cancellation"] = {"request_ref": args.request_ref, "evidence": args.evidence,
                                "outcome": args.outcome, "at": now()}
        task["state"] = "cancelled"
        event(task, command, args.evidence)
        return
    if command == "hold":
        require(task["hold"] is None, "task is already held")
        task["hold"] = {"reason": args.reason, "request_ref": args.request_ref, "at": now()}
        event(task, command, args.request_ref)
        return
    if command == "resume":
        require(task["hold"] is not None, "task is not held")
        require(args.request_ref != task["hold"]["request_ref"], "new resume request required")
        task["hold"] = None
        event(task, command, args.request_ref)
        return
    if command == "observe":
        require(task["native"] is not None, "bind exact task first")
        task["observation"] = {"state": args.state, "evidence": args.evidence, "at": now()}
        task["state"] = "worker_complete" if args.state == "completed" else "active"
        task["verification"] = None
        event(task, command, args.evidence)
        return
    if command == "bind":
        require(task["native"] is None, "task already bound; never redispatch automatically")
        task["native"] = {"task_id": args.task_id, "host": args.host}
        task["state"] = "active"
        event(task, command, args.evidence)
        return
    require(task["hold"] is None, "task is held; verification and closure are prohibited")
    if command == "verify":
        require(task["state"] == "worker_complete", "fresh completed observation required")
        require(age(task["observation"]["at"]) <= FRESH_SECONDS, "observation is stale; exact-read again")
        root = Path(task["project_root"])
        artifacts = []
        for value in args.artifact:
            path = within(root, value)
            require(path.is_file(), "verification artifact must be an existing file")
            artifacts.append({"path": str(path), "sha256": digest(path)})
        task["verification"] = {"artifacts": artifacts, "check": args.check,
                                "evidence": args.evidence, "at": now()}
        task["state"] = "verified"
    elif command == "close":
        require(task["state"] == "verified", "controller verification required before closure")
        require(age(task["observation"]["at"]) <= FRESH_SECONDS, "observation is stale; exact-read and verify again")
        for artifact in task["verification"]["artifacts"]:
            require(digest(artifact["path"]) == artifact["sha256"], "artifact changed since verification")
        task["closure"] = {"evidence": args.evidence, "at": now()}
        task["state"] = "closed"
    else:
        raise BoardError("unsupported command")
    event(task, command, args.evidence)


def execute(args):
    path = Path(args.board).expanduser().absolute()
    if args.command in {"check", "status"}:
        board = load(path)
        if args.command == "check":
            return {"ok": True, "revision": board["revision"], "tasks": len(board["tasks"]),
                    "scope": "local structure only", "dispatch_authorized": False}
        return {"revision": board["revision"], "controller": board["controller"],
                "coverage": "registered tasks only", "tasks": [
                    {"key": t["key"], "title": t["title"], "native": t["native"],
                     "state": t["state"], "held": t["hold"] is not None,
                     "native_state": t["observation"]["state"] if t["observation"] else "unknown",
                     "evidence_at": t["observation"]["at"] if t["observation"] else None,
                     "fresh": age(t["observation"]["at"]) <= FRESH_SECONDS if t["observation"] else False}
                    for t in board["tasks"]]}
    if args.command == "init":
        path.parent.mkdir(parents=True, exist_ok=True)
    with locked(path):
        if args.command == "init":
            require(not path.exists() and not path.is_symlink(), "board already exists; refusing overwrite")
            board = {"schema": SCHEMA, "revision": 1,
                     "controller": {"task_id": args.controller_id, "host": args.host}, "tasks": []}
        else:
            board = load(path)
            require(board["revision"] == args.revision, "stale revision; read the board and reconcile")
            mutate(board, args)
            board["revision"] += 1
        save(path, board)
    return {"ok": True, "revision": board["revision"], "native_action_executed": False}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("init", "register", "bind", "observe", "hold", "resume", "cancel", "verify", "close", "status", "check"):
        command = sub.add_parser(name)
        command.add_argument("board", help="private JSON board path (keep outside the public package)")
        if name not in {"init", "register", "status", "check"}:
            command.add_argument("key")
        if name not in {"init", "status", "check"}:
            command.add_argument("--revision", type=int, required=True)
        if name == "init":
            command.add_argument("--controller-id", required=True)
        if name in {"init", "bind"}:
            command.add_argument("--host", required=True)
        if name == "register":
            command.add_argument("--key", required=True)
            command.add_argument("--title", required=True)
            command.add_argument("--project-root", required=True)
            command.add_argument("--write", action="append", default=[])
        if name in {"register", "hold", "resume", "cancel"}:
            command.add_argument("--request-ref", required=True)
        if name == "bind":
            command.add_argument("--task-id", required=True)
        if name in {"bind", "observe", "verify", "close", "cancel"}:
            command.add_argument("--evidence", required=True)
        if name == "cancel":
            command.add_argument("--outcome", choices=("not_created", "stopped"), required=True,
                                 help="controller-confirmed non-creation or stopped execution; not a stop command")
        if name == "observe":
            command.add_argument("--state", choices=sorted(NATIVE_STATES), required=True)
        if name == "hold":
            command.add_argument("--reason", required=True)
        if name == "verify":
            command.add_argument("--artifact", action="append", required=True)
            command.add_argument("--check", required=True, help="controller's checked result; never executed")
    return p


def main():
    try:
        print(json.dumps(execute(parser().parse_args()), ensure_ascii=False, indent=2))
        return 0
    except (BoardError, OSError, TypeError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

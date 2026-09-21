#!/usr/bin/env python3
"""Run a synthetic, offline lifecycle using the real CLI and disposable files."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    script = Path(__file__).resolve().with_name("voice_coding.py")
    print("SYNTHETIC / OFFLINE: no native tasks, no model calls.", flush=True)
    with tempfile.TemporaryDirectory(prefix="voice-coding-demo-") as directory:
        root = Path(directory).resolve()
        project = root / "sample-project"
        project.mkdir()
        board = root / "private-board.json"

        def run(command, *arguments):
            args = [sys.executable, str(script), command, str(board)]
            args.extend(str(value) for value in arguments)
            if command not in {"init", "status", "check"}:
                revision = json.loads(board.read_text())["revision"]
                args.extend(["--revision", str(revision)])
            result = subprocess.run(args, capture_output=True, text=True, timeout=10)
            if result.returncode:
                raise RuntimeError(f"Offline CLI {command} failed: {result.stderr.strip()}")
            output = json.loads(result.stdout)
            if command not in {"status", "check"} and output.get("native_action_executed") is not False:
                raise RuntimeError("CLI did not preserve the offline contract")
            return output

        run("init", "--controller-id", "synthetic-controller", "--host", "offline")
        for key in ("docs", "tests"):
            run("register", "--key", key, "--title", "Synthetic " + key,
                "--project-root", project, "--write", key,
                "--request-ref", "synthetic-request-" + key)
            run("bind", key, "--task-id", "synthetic-task-" + key,
                "--host", "offline", "--evidence", "synthetic binding; no task created")
        run("hold", "tests", "--reason", "Synthetic user pause",
            "--request-ref", "synthetic-pause-tests")
        artifact = project / "docs" / "result.txt"
        artifact.parent.mkdir()
        artifact.write_text("Synthetic documentation result.\n")
        run("observe", "docs", "--state", "completed",
            "--evidence", "synthetic observation; no native task queried")
        if artifact.read_text() != "Synthetic documentation result.\n":
            raise RuntimeError("Independent artifact inspection failed")
        run("verify", "docs", "--artifact", artifact,
            "--check", "demo independently read and compared exact artifact contents",
            "--evidence", "synthetic-controller-review")
        run("close", "docs", "--evidence", "synthetic closure after controller verification")
        # Completion evidence never clears a previously recorded pause.
        run("observe", "tests", "--state", "completed",
            "--evidence", "synthetic completion while paused")
        result = run("status")
        tasks = {task["key"]: task for task in result["tasks"]}
        if tasks["docs"]["state"] != "closed" or tasks["tests"]["held"] is not True:
            raise RuntimeError("Demo lifecycle or pause preservation failed")
        checked = run("check")
        if checked.get("dispatch_authorized") is not False:
            raise RuntimeError("Structural check must not authorize dispatch")
        print("docs: completed → independently verified → closed")
        print("tests: completion recorded; user pause preserved; no verification or closure")
        print("Structural check: PASS; native dispatch authorized: false")
    print("Disposable demo files cleaned up. No existing board was accessed.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"OFFLINE DEMO FAILED: {exc}", file=sys.stderr)
        sys.exit(1)

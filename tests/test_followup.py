"""Existing native owners can receive a new request after reviewed closure."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "voice_coding.py"


class FollowupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="voice-followup-test-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve()
        self.board = self.project / "private-board.json"
        self.call("init", "--controller-id", "synthetic-controller", "--host", "offline")

    def read(self):
        return json.loads(self.board.read_text())

    def call(self, command, *arguments, reject=False):
        before = self.board.read_bytes() if self.board.exists() else None
        args = [sys.executable, "-B", str(SCRIPT), command, str(self.board)]
        args.extend(str(value) for value in arguments)
        if command not in {"init", "status", "check"}:
            args.extend(["--revision", str(self.read()["revision"])])
        result = subprocess.run(args, capture_output=True, text=True, timeout=10)
        if reject:
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertEqual(self.board.read_bytes(), before)
        else:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def register(self, key):
        self.call("register", "--key", key, "--title", "Synthetic " + key,
                  "--project-root", self.project, "--request-ref", "synthetic-request-" + key)

    def bind(self, key, owner="synthetic-owner", reject=False):
        self.call("bind", key, "--task-id", owner, "--host", "offline",
                  "--evidence", "synthetic-owner-readback", reject=reject)

    def close_first(self):
        self.register("first")
        self.bind("first")
        artifact = self.project / "synthetic-report.txt"
        artifact.write_text("Synthetic report independently inspected.\n")
        self.call("observe", "first", "--state", "completed", "--evidence", "synthetic-completion")
        self.call("verify", "first", "--artifact", artifact,
                  "--check", "independent report inspection passed", "--evidence", "synthetic-review")
        self.call("close", "first", "--evidence", "synthetic-closure")

    def test_new_request_reuses_closed_owner_without_changing_history(self):
        self.close_first()
        closed = self.read()["tasks"][0]
        self.register("followup")
        self.bind("followup")
        first, followup = self.read()["tasks"]
        self.assertEqual(first, closed)
        self.assertEqual(followup["native"], closed["native"])
        self.assertEqual(followup["state"], "active")
        self.assertIsNone(followup["verification"])
        self.assertIsNone(followup["closure"])
        self.call("check")

    def test_inflight_followup_still_excludes_another_request_for_same_owner(self):
        self.close_first()
        self.register("followup")
        self.bind("followup")
        self.register("duplicate")
        self.bind("duplicate", reject=True)
        self.assertIsNone(self.read()["tasks"][2]["native"])

    def test_followup_does_not_make_closed_record_mutable(self):
        self.close_first()
        self.register("followup")
        self.bind("followup")
        self.call("observe", "first", "--state", "running",
                  "--evidence", "synthetic-later-observation", reject=True)
        self.call("resume", "first", "--request-ref", "synthetic-later-request", reject=True)

    def test_controller_identity_remains_excluded_after_other_owner_closes(self):
        self.close_first()
        self.register("followup")
        self.bind("followup", owner="synthetic-controller", reject=True)


if __name__ == "__main__":
    unittest.main()

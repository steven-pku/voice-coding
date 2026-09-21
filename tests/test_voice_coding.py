"""Offline CLI contract tests; all identities and evidence are synthetic."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "voice_coding.py"


class BoardContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="voice-coding-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project = self.root / "project"
        self.project.mkdir()
        self.board = self.root / "private-board.json"
        self.call("init", "--controller-id", "synthetic-controller", "--host", "offline")

    def read(self):
        return json.loads(self.board.read_text())

    def task(self, key="alpha"):
        return next(t for t in self.read()["tasks"] if t["key"] == key)

    def call(self, command, *arguments, reject=False, revision=None):
        before = self.board.read_bytes() if self.board.exists() else None
        args = [sys.executable, str(SCRIPT), command, str(self.board)]
        args.extend(str(a) for a in arguments)
        if command not in {"init", "status", "check"}:
            revision = self.read()["revision"] if revision is None else revision
            args.extend(["--revision", str(revision)])
        result = subprocess.run(args, capture_output=True, text=True, timeout=10)
        if reject:
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertEqual(self.board.read_bytes(), before, "rejected operation changed the board")
            return result
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        if command not in {"status", "check"}:
            self.assertIs(payload["native_action_executed"], False)
        return payload

    def register(self, key="alpha", scope="alpha", root=None, request=None, **kw):
        args = ["--key", key, "--title", "Synthetic " + key,
                "--project-root", str(root or self.project),
                "--request-ref", request or "synthetic-request-" + key]
        if scope is not None:
            args.extend(["--write", str(scope)])
        return self.call("register", *args, **kw)

    def bind(self, key="alpha", native=None, host="offline", **kw):
        return self.call("bind", key, "--task-id", native or "synthetic-task-" + key,
                         "--host", host, "--evidence", "synthetic-bind-readback", **kw)

    def observe(self, key="alpha", state="completed", **kw):
        return self.call("observe", key, "--state", state,
                         "--evidence", "synthetic-native-readback", **kw)

    def completed(self):
        self.register()
        self.bind()
        self.observe()
        artifact = self.project / "alpha" / "result.txt"
        artifact.parent.mkdir()
        artifact.write_text("Synthetic result.\n")
        return artifact

    def verify(self, artifact, key="alpha", check="independent inspection passed", **kw):
        return self.call("verify", key, "--artifact", artifact, "--check", check,
                         "--evidence", "synthetic-controller-review", **kw)

    def rewrite_fixture(self, mutate):
        board = self.read()
        mutate(board)
        self.board.write_text(json.dumps(board))

    def test_two_tasks_close_verified_work_and_preserve_other_hold(self):
        artifact = self.completed()
        self.register("beta", "beta")
        self.bind("beta")
        self.call("hold", "beta", "--reason", "user paused",
                  "--request-ref", "synthetic-pause-beta")
        self.verify(artifact)
        self.call("close", "alpha", "--evidence", "synthetic-closure-review")
        result = self.call("status")
        self.assertEqual(result["coverage"], "registered tasks only")
        alpha, beta = result["tasks"]
        self.assertEqual(alpha["state"], "closed")
        self.assertTrue(beta["held"])
        self.assertEqual(beta["native_state"], "unknown")
        self.assertEqual(len(self.task()["verification"]["artifacts"][0]["sha256"]), 64)

    def test_duplicate_request_ref_rejected_even_with_new_task_key(self):
        self.register()
        self.register("beta", "beta", request="synthetic-request-alpha", reject=True)

    def test_duplicate_task_key_rejected(self):
        self.register()
        self.register(request="different-request", scope="beta", reject=True)

    def test_duplicate_native_identity_rejected(self):
        self.register()
        self.bind()
        self.register("beta", "beta")
        self.bind("beta", native="synthetic-task-alpha", reject=True)

    def test_controller_identity_cannot_be_bound_as_worker(self):
        self.register()
        self.bind(native="synthetic-controller", reject=True)

    def test_identity_includes_host(self):
        self.register()
        self.bind()
        self.register("beta", "beta")
        self.bind("beta", native="synthetic-task-alpha", host="other-offline-host")
        self.assertEqual(self.task("beta")["native"]["host"], "other-offline-host")

    def test_rebinding_existing_task_rejected(self):
        self.register()
        self.bind()
        self.bind(native="another-native-id", reject=True)

    def test_equal_and_nested_scopes_conflict(self):
        self.register(scope="shared")
        for scope in ("shared", "shared/result.txt", "."):
            with self.subTest(scope=scope):
                self.register("beta", scope, reject=True)

    def test_parent_scope_conflicts_with_registered_child(self):
        self.register(scope="shared/result.txt")
        self.register("beta", "shared", reject=True)

    def test_overlapping_real_scope_across_project_roots_rejected(self):
        nested = self.project / "nested"
        nested.mkdir()
        self.register(scope="nested/result.txt")
        self.register("beta", ".", root=nested, reject=True)

    def test_symlink_alias_does_not_hide_write_conflict(self):
        real = self.project / "real"
        real.mkdir()
        (self.project / "alias").symlink_to(real, target_is_directory=True)
        self.register(scope="real")
        self.register("beta", "alias/result.txt", reject=True)

    def test_symlink_project_alias_does_not_hide_conflict(self):
        alias = self.root / "project-alias"
        alias.symlink_to(self.project, target_is_directory=True)
        self.register()
        self.register("beta", "alpha/child", root=alias, reject=True)

    def test_scope_cannot_escape_using_parent_or_absolute_path(self):
        for scope in ("../outside.txt", self.root / "outside.txt"):
            with self.subTest(scope=scope):
                self.register(scope=scope, reject=True)

    def test_scope_cannot_escape_through_symlink(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.project / "escape").symlink_to(outside, target_is_directory=True)
        self.register(scope="escape/result.txt", reject=True)

    def test_later_symlink_retargeting_does_not_reassign_scope(self):
        target = self.project / "owned"
        target.mkdir()
        self.register(scope="owned/result.txt")
        target.rmdir()
        target.symlink_to(self.root, target_is_directory=True)
        self.call("check", reject=True)
        self.bind(reject=True)

    def test_read_only_tasks_can_share_project(self):
        self.register(scope=None)
        self.register("beta", scope=None)
        self.assertEqual(self.call("check")["tasks"], 2)

    def test_stale_revision_does_not_lose_existing_change(self):
        prior = self.read()["revision"]
        self.register()
        self.register("beta", "beta", revision=prior, reject=True)
        self.assertEqual([t["key"] for t in self.read()["tasks"]], ["alpha"])

    def test_two_writers_with_same_revision_commit_only_once(self):
        revision = self.read()["revision"]
        children = []
        for key in ("alpha", "beta"):
            args = [sys.executable, str(SCRIPT), "register", str(self.board),
                    "--key", key, "--title", "Synthetic " + key,
                    "--project-root", str(self.project), "--write", key,
                    "--request-ref", "synthetic-request-" + key,
                    "--revision", str(revision)]
            children.append(subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        results = [(child.communicate(timeout=10), child.returncode) for child in children]
        self.assertEqual(sum(code == 0 for _, code in results), 1, results)
        self.assertEqual(self.read()["revision"], revision + 1)
        self.assertEqual(len(self.read()["tasks"]), 1)

    def test_existing_lock_blocks_and_is_preserved(self):
        lock = self.board.with_name(self.board.name + ".lock")
        lock.write_text("synthetic-other-writer")
        self.register(reject=True)
        self.assertEqual(lock.read_text(), "synthetic-other-writer")

    def test_invalid_json_is_not_overwritten(self):
        self.board.write_text('{"schema":')
        self.call("check", reject=True)
        self.register(revision=1, reject=True)
        self.assertFalse(self.board.with_name(self.board.name + ".lock").exists())

    def test_ambiguous_duplicate_json_keys_fail_closed(self):
        text = self.board.read_text()
        self.board.write_text(text.replace('"revision": 1', '"revision": 99, "revision": 1'))
        self.call("check", reject=True)
        self.register(revision=1, reject=True)

    def test_init_does_not_replace_existing_board(self):
        self.call("init", "--controller-id", "replacement", "--host", "offline", reject=True)

    def test_symlink_and_hardlink_boards_cannot_be_mutated(self):
        original = self.root / "original.json"
        self.board.rename(original)
        before = original.read_bytes()
        self.board.symlink_to(original)
        self.register(revision=1, reject=True)
        self.assertEqual(original.read_bytes(), before)
        self.board.unlink()
        os.link(original, self.board)
        self.register(revision=1, reject=True)
        self.assertEqual(original.read_bytes(), before)

    def test_completed_observation_keeps_hold_and_blocks_verification(self):
        artifact = self.completed()
        self.call("hold", "alpha", "--reason", "user paused",
                  "--request-ref", "synthetic-pause")
        self.observe()
        self.assertIsNotNone(self.task()["hold"])
        self.verify(artifact, reject=True)
        self.call("close", "alpha", "--evidence", "synthetic-close", reject=True)

    def test_resume_requires_distinct_request_and_does_not_dispatch(self):
        self.register()
        self.bind()
        self.call("hold", "alpha", "--reason", "user paused",
                  "--request-ref", "synthetic-pause")
        self.call("resume", "alpha", "--request-ref", "synthetic-pause", reject=True)
        self.call("resume", "alpha", "--request-ref", "synthetic-explicit-resume")
        self.assertIsNone(self.task()["hold"])
        self.assertEqual(self.task()["observation"], None)

    def test_held_planned_task_cannot_bind(self):
        self.register()
        self.call("hold", "alpha", "--reason", "user paused",
                  "--request-ref", "synthetic-pause")
        self.bind(reject=True)

    def test_worker_completion_cannot_close_without_controller_verification(self):
        self.completed()
        self.assertEqual(self.task()["state"], "worker_complete")
        self.assertIsNone(self.task()["verification"])
        self.call("close", "alpha", "--evidence", "worker says done", reject=True)

    def test_failure_and_unknown_are_not_completion(self):
        artifact = self.completed()
        for state in ("failed", "unknown", "running"):
            with self.subTest(state=state):
                self.observe(state=state)
                self.assertNotEqual(self.task()["state"], "worker_complete")
                self.verify(artifact, reject=True)

    def test_stale_observation_cannot_verify(self):
        artifact = self.completed()
        old = (datetime.now(timezone.utc) - timedelta(minutes=6)).isoformat()
        self.rewrite_fixture(lambda board: board["tasks"][0]["observation"].update(at=old))
        self.assertFalse(self.call("status")["tasks"][0]["fresh"])
        self.verify(artifact, reject=True)

    def test_future_observation_rejected_without_repairing_it(self):
        artifact = self.completed()
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        self.rewrite_fixture(lambda board: board["tasks"][0]["observation"].update(at=future))
        self.call("check", reject=True)
        self.verify(artifact, reject=True)

    def test_naive_observation_timestamp_rejected(self):
        self.completed()
        self.rewrite_fixture(lambda board: board["tasks"][0]["observation"].update(at="2026-01-01T00:00:00"))
        self.call("check", reject=True)

    def test_artifact_outside_project_is_not_hashed(self):
        self.completed()
        outside = self.root / "private.txt"
        outside.write_text("Synthetic outside data")
        self.verify(outside, reject=True)
        self.assertNotIn("Synthetic outside data", self.board.read_text())

    def test_artifact_symlink_escape_rejected(self):
        artifact = self.completed()
        outside = self.root / "outside.txt"
        outside.write_text("Synthetic outside data")
        artifact.unlink()
        artifact.symlink_to(outside)
        self.verify(artifact, reject=True)

    def test_artifact_hash_drift_blocks_close(self):
        artifact = self.completed()
        self.verify(artifact)
        artifact.write_text("Changed after review")
        self.call("close", "alpha", "--evidence", "synthetic-close", reject=True)
        self.assertEqual(self.task()["state"], "verified")

    def test_stale_observation_blocks_close_even_after_verification(self):
        artifact = self.completed()
        self.verify(artifact)
        old = (datetime.now(timezone.utc) - timedelta(minutes=6)).isoformat()
        self.rewrite_fixture(lambda board: board["tasks"][0]["observation"].update(at=old))
        self.call("close", "alpha", "--evidence", "synthetic-close", reject=True)

    def test_new_native_observation_invalidates_old_verification(self):
        artifact = self.completed()
        self.verify(artifact)
        self.observe()
        self.assertIsNone(self.task()["verification"])
        self.call("close", "alpha", "--evidence", "synthetic-close", reject=True)

    def test_check_string_is_stored_as_data_never_executed(self):
        artifact = self.completed()
        marker = self.root / "must-not-exist.txt"
        command = f"touch '{marker}'; $(touch '{marker}'); __import__('os').system('touch {marker}')"
        self.verify(artifact, check=command)
        self.assertEqual(self.task()["verification"]["check"], command)
        self.assertFalse(marker.exists())

    def test_structure_check_is_read_only_and_never_authorizes_dispatch(self):
        self.register()
        before = self.board.read_bytes()
        result = self.call("check")
        self.assertEqual(result["scope"], "local structure only")
        self.assertIs(result["dispatch_authorized"], False)
        self.assertEqual(self.board.read_bytes(), before)
        self.assertIsNone(self.task()["native"])

    def test_closed_task_cannot_be_resumed_or_reobserved(self):
        artifact = self.completed()
        self.verify(artifact)
        self.call("close", "alpha", "--evidence", "synthetic-close")
        self.observe(reject=True)
        self.call("resume", "alpha", "--request-ref", "new-request", reject=True)
        self.register("beta", "alpha")


if __name__ == "__main__":
    unittest.main()

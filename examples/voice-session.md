# Synthetic Voice session

Everything below is fictional. Task keys and evidence references are illustrative. This is a conversation example, not a transcript of a tested native Voice session.

Run `python3 scripts/demo.py` from the repository root for the separate local ledger demo. That demo makes no model or network calls and does not create native tasks.

## Start with a small request

**User:** Use $voice-coding. Be the controller for this project. Create two new tasks: review the documentation and review the tests. Keep both read-only. Bring their findings back here.

**Controller actions:**

1. Read the current project instructions and state. Confirm the two reviews can proceed independently.
2. Use the native project tools to identify the target project and host.
3. Register two request keys, such as `docs-review` and `tests-review`, with the user's request reference and empty write scopes.
4. Create the two explicitly requested native tasks. Bind each ready task ID and host from the actual tool response; do not derive IDs from titles.
5. Use bounded native waits and inspect returned results before reporting.

**Controller:** The documentation review and test review are running. Both are read-only. I will bring back findings that need a decision and results ready for review.

That spoken status is appropriate only after the native responses establish it.

## Check progress

**User:** How are those two reviews doing?

**Controller actions:** Refresh native state. Suppose the documentation task reports completion while the test review still runs. Record these as observations.

**Controller:** The documentation task reports completion; I still need to inspect its findings. The test review is running.

The controller does not mark the documentation result verified simply because the task completed.

## Hold and stop

**User:** Hold the test review. Do not give it any more work.

**Controller actions:** Record the hold against the current board revision, with the user's request reference. Do not send more work to that task. Keep its write scope reserved if it has one.

**Controller:** I have put further dispatch on hold. That does not interrupt work already running.

**User:** Stop its running work as well.

If no applicable native stop tool is available:

**Controller:** Stopping this task is unsupported by the tools available here. Use the native task's stop control. I will keep further dispatch on hold and check the task state again.

Do not archive the task or end Voice as a substitute for stopping it.

**User:** Resume the test review within its original read-only scope.

**Controller actions:** Record the explicit resume request, refresh native state, and decide whether a follow-up is needed. Do not restart a task that already finished, or resend work with an uncertain delivery outcome.

## Check results, then close

When a task reports completion, the controller reads its artifacts and checks the claims that matter. It records the actual artifact paths, check description, and evidence reference using `verify`.

`verify` records a controller assertion and artifact hashes. It does not run the named check or prove the assertion. If files change afterward, the recorded hashes describe the earlier files.

After addressing outstanding items, the controller records a separate `close` decision and reports what was checked. If evidence is missing, leave the item open and state what is missing.

## Two cases to handle explicitly

**Creation result is uncertain.** A task-creation call times out after `docs-review` was registered. Inspect native tasks before retrying. If a matching task is confirmed, bind it; if the outcome remains uncertain, keep the request unresolved. Do not launch another copy merely because no ready ID reached the controller.

**Write scopes overlap.** The user later requests two edits in the same directory. Register the intended paths before dispatch. Sequence the work or obtain a revised non-overlapping scope. A held task still reserves its write scope. The local conflict check only sees registered work; it is not a sandbox or a filesystem lock.

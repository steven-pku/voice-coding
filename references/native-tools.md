# Native Codex tools

The controller uses the tools available in the current Codex environment. Tool availability and names can change; inspect the current descriptions before acting. Do not invent a callable API from this reference or substitute an unrelated runtime silently.

OpenAI's [Voice guide](https://learn.chatgpt.com/docs/features/voice), checked on 2026-09-07, describes Voice in an existing task and creating, checking, or following up on tasks. Availability depends on rollout. Voice differs from dictation, which converts speech into a written prompt. This repository supplies the coordination workflow, not the audio feature.

## Common task operations

These are current Codex app tool names, without a provider-specific namespace prefix. They are tools for the controller to call, not shell commands or endpoints used by the Python helper.

| Intent | Native operation | Controller responsibility |
|---|---|---|
| Find a project | `list_projects` | Use a returned project ID; check whether it is a Git repository. |
| Find existing tasks | `list_threads` | Match title, project, and host. Use the returned title when referring to a task. |
| Inspect a task | `read_thread` | Read current state and relevant recent evidence before deciding what follows. |
| Create a new task | `create_thread` | Require an explicit creation request; pre-register its request key; record the returned identity. |
| Check progress | `wait_threads` | Prefer compact snapshots and bounded waits; retain returned cursors. |
| Continue a task | `send_message_to_thread` | Stay within scope; do not continue a held task without an explicit resume request. |
| Show a task | `navigate_to_codex_page` | Navigate only when the user asks to open or show it. |
| Archive a task | `set_thread_archived` | Archiving is organization, not evidence that execution stopped or outputs passed review. |
| End Voice | `end_realtime_voice_call` | End only when the user explicitly asks to end the call; this does not stop coding tasks. |

For project task creation, inspect the returned `isGitRepository` value. Use a worktree for a Git project by default and a local environment otherwise; follow an explicit user request to work directly in the saved project. Do not invent a branch, model, or project ID.

## Creation can be asynchronous

1. Register the request key and intended scope in the local board before calling `create_thread`.
2. If a ready result provides a task ID and host, bind those exact returned values with an evidence reference.
3. Setup can instead return a pending client ID. That is not a task ID for tools that require one. Keep the request pending and inspect native state until the ready identity is established.
4. After a timeout, lost response, or uncertain delivery, check existing tasks and their evidence before retrying. The ledger cannot guarantee that native task creation is idempotent.

## Stop is a separate capability

There is no universal stop operation in the tool set assumed by this candidate. If the current environment has no applicable native interruption tool, report `unsupported` and direct the user to the native task controls. Do not archive a task, end Voice, or record a local hold and claim that a running process was stopped.

The board's `hold` prevents further dispatch through this workflow and preserves the task's intended write scope. A held task may still be running. Check native state and keep the distinction visible in the next update.

## Observation and verification

A native `completed` result is an observation. The controller reads the returned artifacts, performs the relevant checks, and records verification separately. The helper stores the controller's assertion and artifact hashes; it does not evaluate the artifacts or run the named checks.

Use the native task ID and host for lookup; keep native state separate from local workflow decisions such as a hold. If a tool is missing or its response is inconclusive, record uncertainty and explain the specific limitation.

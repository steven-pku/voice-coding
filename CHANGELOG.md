# Changelog

## 0.1.0 — Public preview · 2026-09-21

First public source preview under MIT. The four-job macOS/Linux and Python 3.10/3.13 CI matrix passed. No release tag or GitHub Release has been created; live Voice acceptance remains separate.

- A project-local Codex Skill for using existing Voice and native task tools from one controller task.
- Guidance for explicitly requested task creation, fresh status checks, bounded follow-up, holds, and separate controller verification.
- A Python 3.10+ standard-library helper for local task pointers, revision-checked updates, intended write scopes, and artifact-hash receipts.
- A project-local installer that refuses to overwrite an existing Skill destination.
- Synthetic examples and a local demo with no model calls, network calls, or native task execution.
- English and Chinese quick starts, native-tool mapping, security guidance, and MIT licensing.

The helper is a ledger. It does not implement speech recognition, dispatch work, enforce a sandbox, or terminate native tasks. See [VALIDATION.md](VALIDATION.md) for actual checks and remaining limits.

# Voice Coding

[中文](README.zh-CN.md) · [Skill](SKILL.md) · [Validation](VALIDATION.md)

Use Codex's existing Voice feature to coordinate several coding tasks from one controller task. Tell the controller what to start, ask what has changed, and review the results before closing the work.

**v0.1.0 public preview.** It packages a workflow and a small local ledger; Codex provides Voice and the task tools. [Offline CI](https://github.com/steven-pku/voice-coding/actions/workflows/check.yml) covers Python 3.10 and 3.13 on macOS and Linux. See [validation evidence and limits](VALIDATION.md) before relying on live Voice behavior.

## Start here

You need Codex with the relevant task tools, access to Voice, and Python 3.10+ for the optional local helper. Voice availability depends on rollout. Voice is an ongoing conversation; dictation turns speech into a written prompt. See [OpenAI's Voice guide](https://learn.chatgpt.com/docs/features/voice).

First, try the local demo from this checkout:

```sh
python3 scripts/demo.py
```

It uses synthetic tasks in a temporary directory. It makes no model or network calls and does not create or run Codex tasks.

Then read [the installer](scripts/install.py) and install the Skill into your target project:

```sh
python3 scripts/install.py --project /path/to/target-project
```

Replace the path with your project. The installer copies the Skill and its supporting files into that project's `.agents/skills/voice-coding/`. It refuses an existing destination and makes no global installation.

Open a **new Codex task in that project** and explicitly invoke `$voice-coding`. Check that the Skill is available there before relying on it; successful copying alone does not prove loading. Start Voice in that task when available.

## A first conversation

> Use $voice-coding. Be the controller for this project. Create two new tasks: one to review the documentation and one to review the tests. Both are read-only. Report their findings here; do not publish anything.

Then:

> Check those two tasks. Tell me what needs attention and what is ready for review.

The controller identifies each native task by its returned task ID and host, checks fresh state, and brings the results back. Work with overlapping write paths stays sequential. See the [synthetic session](examples/voice-session.md) for holds, uncertain creation, and verification.

## What the helper does

The optional standard-library helper records task pointers, intended write scopes, observations, and controller verification receipts. It never calls a model, accesses the network, or dispatches work.

From this checkout:

```sh
python3 scripts/voice_coding.py init /path/to/local/board.json --controller-id my-controller --host local
python3 scripts/voice_coding.py status /path/to/local/board.json
python3 scripts/voice_coding.py check /path/to/local/board.json
```

Replace `my-controller` and `local` with the exact task ID and host from your environment; these are illustrative placeholders. Use a private local board path and keep it out of version control. After installation, the helper is also at `.agents/skills/voice-coding/scripts/voice_coding.py` in the target project. See `--help` and [SKILL.md](SKILL.md) for registration, binding, observations, and verification. Every modifying command after `init` requires the current `--revision N` to reject stale updates.

## Boundaries

- Voice input never enlarges permissions. This workflow asks for explicit text authorization for publishing, spending, credential changes, or destructive actions; a broad goal does not grant it.
- A reported task completion is an observation. The controller reviews artifacts and records verification separately, then closes the task after resolving outstanding items.
- A ledger hold prevents further dispatch in this workflow. It does **not** terminate a native task or process. If the available tools cannot stop it, the controller reports that limitation and directs you to the native UI.
- Write scopes are paths on the machine running the helper. They are compared conservatively across all records, regardless of a task's host ID; remote filesystem scopes are not modeled. This is not a sandbox or a lock on other applications. Held tasks retain their write scopes.
- Native tools vary by environment. There is no promised cross-runtime control layer, background daemon, or automatic task resumption. See [native tool mapping](references/native-tools.md).

[Security](SECURITY.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [MIT license](LICENSE)

# Voice Coding contributors

Keep the project small: native Codex Voice and task tools provide execution;
the Python standard-library helper only records coordination metadata.

- Read README.md and SECURITY.md before changing behavior.
- Never use private task IDs, account information, local paths, transcripts, or credentials in fixtures.
- Offline tests must not call models, providers, native tasks, or network services.
- Preserve holds, exact identity, independent verification, and request deduplication.
- A local board is not an authorization system or a filesystem sandbox.
- Run `python3 scripts/check.py` after changes. Add regressions for behavior defects.
- Keep release-files.txt synchronized with intentional public files.
- Do not publish, push, create tags, install globally, or change runtime settings without explicit user authorization.

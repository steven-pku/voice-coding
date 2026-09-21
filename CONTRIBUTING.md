# Contributing

Keep Voice Coding small: a useful Codex Skill, clear native-tool guidance, and a standard-library helper for local records. A change should make an actual coordination step easier to perform or verify.

## Before proposing a change

1. Read [SKILL.md](SKILL.md), [SECURITY.md](SECURITY.md), and the current [validation record](VALIDATION.md).
2. Run the checks and synthetic demo from the repository root:

   ```sh
   python3 scripts/check.py
   python3 scripts/demo.py
   ```

3. Keep English and Chinese README behavior aligned. Check local document links and installation instructions from a clean copy.
4. Use only synthetic task IDs, paths, host names, and artifacts in examples or reports. Keep local boards and real transcripts outside the public tree.

No account, model call, or network access is required for these local checks. A passing demo proves the recorded local scenario; it does not prove native Voice or task-tool behavior.

## Good changes

- Describe the observed problem, the resulting behavior, and the relevant verification.
- Keep each change focused. Add a regression test for a behavioral defect, especially one affecting revision checks, path conflicts, holds, or verification. Avoid tests that merely repeat documentation text.
- Preserve the distinction between observation, controller verification, and closure.
- Treat unsupported native capabilities as unsupported. Do not add automatic retries, task resumption, provider fallback, or network calls to make a scenario appear successful.
- Record new verification results and limitations in `VALIDATION.md`; do not rewrite old evidence as if a new check had run.

## Before a release

Check the actual intended release tree for private data, local configuration, generated boards, credentials, and broken links. Confirm that the Skill, version metadata, changelog, README, and release notes describe the same candidate. Test project-local installation into an empty destination and confirm that an existing destination is preserved.

Claim Skill discovery only after checking a new Codex process. Discovery is separate from reliable triggering or an end-to-end Voice exercise. Keep GitHub publication and remote CI marked pending until their remote results have been checked.

Changes are distributed under the repository's [MIT license](LICENSE). See [SECURITY.md](SECURITY.md) before reporting a security concern.

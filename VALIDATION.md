# Validation

Version: **0.1.0**. Status: **public preview**.

The reproducible entry point is `python3 scripts/check.py`. It runs offline tests, a synthetic two-task CLI demonstration, public-file inventory checks, local Markdown link checks and heuristic private-data scans. All fixtures are synthetic. It does not invoke a model, provider or native task.

## Local checks · 2026-09-07

Environment: macOS arm64, Python 3.14.7. The GitHub workflow targets Python 3.10 and 3.13 on macOS and Linux; those remote jobs have not run.

| Check | Observed result |
|---|---|
| CLI and installation tests | 46 tests passed, including duplicate identity/request rejection, concurrent revision conflict, held completion, stale evidence, artifact drift, path escapes and closed-owner follow-up. |
| Two-task first-use demo | Passed in a disposable directory: one task verified and closed, the other still held. Synthetic observations only. |
| Skill format | Official local Skill Creator validator passed. |
| Fresh process discovery | Project-local installation advertised exactly one `voice-coding` entry in a new Codex process; exit 0, empty startup stderr, zero model calls. This proves discovery, not model behavior or live Voice loading. |
| Package boundary | 24 allowlisted public files; local links, whitespace and heuristic private-data checks passed. Export refuses existing destinations and copies no Git history or runtime state. |
| Independent review | No remaining blocking findings after the corrections below. Review was offline. |

The first sandboxed discovery attempt failed on a host startup write. The same inspection succeeded with an approved sandbox escalation; no global configuration was changed. Discovery testing uses the current installed CLI's local prompt inspection, not an app-server or a model turn.

## Corrections caught before publication

- Ambiguous JSON with duplicate keys was initially accepted by the standard parser. The loader now rejects duplicate fields at every object level; a regression verifies that rejected state remains byte-identical.
- A closed record initially prevented a new request from using its existing native owner. Active identities remain unique, closed history remains immutable, and a new request can bind the previous owner after fresh inspection. Four follow-up regressions passed.
- Installed copies now include the MIT notice. Scope documentation explicitly describes local, conservative path comparison without claiming remote filesystem coordination.

## First public CI · 2026-09-21

[GitHub Actions run 35609717910](https://github.com/steven-pku/voice-coding/actions/runs/35609717910) passed all four jobs (macOS/Linux × Python 3.10/3.13) at public commit `6e85c0d551edb77d14e9b2d06ef5ac20bc1d0434`. Each job ran the 46-test suite, synthetic demo, package checks and whitespace check. Root also reran the 46 tests and demo locally before upload. The earlier 2026-09-07 observations above remain historical evidence.

The helper records controller assertions. Offline success does not prove live Voice behavior, a trusted approval carrier, exactly-once native dispatch, complete task discovery, forced process termination, or user acceptance. Native task tooling and Voice availability depend on the user's current environment.

Sources checked for this package: [official Voice documentation](https://learn.chatgpt.com/docs/features/voice), [official skill best practices](https://learn.chatgpt.com/guides/best-practices), and the task tool descriptions available during development. The package adapts the coordination patterns from private practice; no private runtime, state ledger, session history or audio is included.

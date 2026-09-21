# Public preview and release process

The v0.1.0 public preview is available at [steven-pku/voice-coding](https://github.com/steven-pku/voice-coding). The initial public commit is `6e85c0d551edb77d14e9b2d06ef5ac20bc1d0434`; [its four CI jobs passed](https://github.com/steven-pku/voice-coding/actions/runs/35609717910). No release tag or GitHub Release has been created. Do not push private development history.

## Preparing subsequent updates

Before publishing, run `python3 scripts/check.py` on the exact public tree and inspect the complete file list in `release-files.txt`. Review the MIT license, README claims and validation limits together. The exporter copies only allowlisted files and refuses an existing destination:

```sh
python3 scripts/export.py /path/to/new-public-tree
```

The caller chooses the destination; nothing is uploaded or initialized in Git by this command. Run the same checks in the exported tree. Real boards and account evidence never belong in this tree. The privacy check is a heuristic, so a human review of the final commit is still required.

After explicit publication approval, use the intended GitHub account and push only reviewed public commits to the existing repository. Inspect commit author/committer metadata as well as file content; use the account's GitHub noreply address when a private email must not be disclosed. Do not upload internal validation receipts or inherit private remotes. Repository owner, remote creation, push, tags and Releases are external actions; this preparation does not perform them.

Read GitHub Actions after the first push before claiming remote CI success. A release tag and a GitHub Release, if desired, follow that check. This candidate makes no claim about end-to-end Voice testing on another user's account.

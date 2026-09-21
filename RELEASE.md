# First public release

The v0.1.0 candidate is intended for a new, clean repository. Do not push the private development repository or its history.

Before publishing, run `python3 scripts/check.py` on the exact public tree and inspect the complete file list in `release-files.txt`. Review the MIT license, README claims and validation limits together. The exporter copies only allowlisted files and refuses an existing destination:

```sh
python3 scripts/export.py /path/to/new-public-tree
```

The caller chooses the destination; nothing is uploaded or initialized in Git by this command. Run the same checks in the exported tree. Real boards and account evidence never belong in this tree. The privacy check is a heuristic, so a human review of the final commit is still required.

After explicit publication approval, use the intended GitHub account to create an empty `voice-coding` repository, connect only this clean local repository, and push its reviewed commit. Do not upload internal validation receipts or inherit private remotes. Repository owner, remote creation, push, tags and Releases are external actions; this preparation does not perform them.

Read GitHub Actions after the first push before claiming remote CI success. A release tag and a GitHub Release, if desired, follow that check. This candidate makes no claim about end-to-end Voice testing on another user's account.

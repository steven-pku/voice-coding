#!/usr/bin/env python3
"""Install only this skill into an existing project's .agents/skills directory."""

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

FILES = ("SKILL.md", "LICENSE", "agents/openai.yaml", "scripts/voice_coding.py", "references/native-tools.md")


def install(project, source=None):
    source = source or Path(__file__).resolve().parents[1]
    project = Path(project).expanduser().resolve(strict=True)
    if not project.is_dir():
        raise ValueError("project must be an existing directory")
    parent = project / ".agents" / "skills"
    for component in (project / ".agents", parent):
        if component.is_symlink():
            raise ValueError("installation ancestors must not be symlinks")
    destination = parent / "voice-coding"
    if destination.exists() or destination.is_symlink():
        raise ValueError("voice-coding already exists; review the existing installation before replacing it")
    for relative in FILES:
        path = source / relative
        if not path.is_file() or path.is_symlink() or source.resolve() not in path.resolve().parents:
            raise ValueError("missing or unsafe skill resource: " + relative)
    parent.mkdir(parents=True, exist_ok=True)
    lock = parent / ".voice-coding-install.lock"
    fd = os.open(str(lock), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    staging = None
    try:
        if destination.exists() or destination.is_symlink():
            raise ValueError("installation appeared concurrently; refusing overwrite")
        staging = Path(tempfile.mkdtemp(prefix=".voice-coding-install-", dir=parent))
        for relative in FILES:
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, target)
        staging.rename(destination)
        staging = None
    finally:
        if staging is not None:
            shutil.rmtree(staging)
        lock.unlink()
    return {"installed": str(destination), "files": len(FILES), "runtime_loading_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.project), indent=2))
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

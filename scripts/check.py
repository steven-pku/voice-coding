#!/usr/bin/env python3
"""Offline release check: allowlisted files, links, privacy patterns, tests and demo."""

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def public_files(root):
    entries = (root / "release-files.txt").read_text(encoding="utf-8").splitlines()
    if not entries or len(entries) != len(set(entries)):
        raise ValueError("empty or duplicate release manifest")
    for entry in entries:
        path = Path(entry)
        if path.is_absolute() or ".." in path.parts or str(path) != entry:
            raise ValueError("unsafe release path")
        full = root / path
        if not full.is_file() or full.is_symlink() or root.resolve() not in full.resolve().parents:
            raise ValueError("missing or symlinked release file: " + entry)
    return entries


def inspect(root):
    entries = public_files(root)
    actual = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if ".git" in relative.parts or "__pycache__" in relative.parts:
            continue
        if path.is_symlink():
            raise ValueError("release tree contains symlink: " + str(relative))
        if path.is_file():
            actual.add(str(relative))
    if actual != set(entries):
        raise ValueError("release inventory mismatch: " + str(sorted(actual ^ set(entries))))
    # Heuristics supplement review; they do not certify the absence of secrets.
    patterns = {
        "personal home": r"/(?:Users|home)/[A-Za-z0-9_.-]+/",
        "email": r"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "private key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "provider token": r"(?:sk-|ghp_|github_pat_)[A-Za-z0-9_\-]{20,}",
        "native UUID": r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    }
    for relative in entries:
        path = root / relative
        content = path.read_text(encoding="utf-8")
        if not content.endswith("\n") or any(line.rstrip() != line for line in content.splitlines()):
            raise ValueError("whitespace issue: " + relative)
        for label, pattern in patterns.items():
            if re.search(pattern, content):
                raise ValueError(f"possible {label} in {relative}; inspect before export")
        if path.suffix == ".md":
            # Remove fenced/inline code so syntax examples are not treated as links.
            prose = re.sub(r"```.*?```", "", content, flags=re.S)
            prose = re.sub(r"`[^`]*`", "", prose)
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", prose):
                if re.match(r"https?://|mailto:|#", target):
                    continue
                target = unquote(target.split("#", 1)[0].strip("<>"))
                resolved = (path.parent / target).resolve()
                if root.resolve() not in resolved.parents or not resolved.exists():
                    raise ValueError(f"broken local link in {relative}: {target}")
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    if not skill.startswith("---\nname: voice-coding\ndescription: ") or "\n---\n" not in skill[4:]:
        raise ValueError("invalid skill frontmatter")
    return entries


def main():
    try:
        entries = inspect(ROOT)
        commands = ([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
                    [sys.executable, "-B", "scripts/demo.py"])
        for command in commands:
            subprocess.run(command, cwd=ROOT, check=True, timeout=120)
        print(json.dumps({"ok": True, "public_files": len(entries),
                          "validation": "offline only", "remote_ci_run": False}, indent=2))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

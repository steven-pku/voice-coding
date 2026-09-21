#!/usr/bin/env python3
"""Copy the public allowlist to a NEW directory. Never copy Git or local state."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path
import sys

from check import inspect


def export(source, destination):
    source = source.resolve()
    destination = destination.expanduser().absolute()
    entries = inspect(source)
    if destination.exists() or destination.is_symlink():
        raise ValueError("export destination already exists; refusing overwrite")
    if source == destination.resolve() or source in destination.resolve().parents:
        raise ValueError("export must be outside the source tree")
    destination.mkdir(parents=True, exist_ok=False)
    for relative in entries:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, target)
    inspect(destination)
    hashes = {p: hashlib.sha256((destination / p).read_bytes()).hexdigest() for p in entries}
    for relative, expected in hashes.items():
        if hashlib.sha256((source / relative).read_bytes()).hexdigest() != expected:
            raise ValueError("source changed during export; inspect the partial export")
    return {"files": len(entries), "sha256": hashes, "published": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(export(Path(__file__).resolve().parents[1], args.destination), indent=2))
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

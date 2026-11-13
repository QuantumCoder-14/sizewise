#!/usr/bin/env python3
"""
sizewise - find out what is actually eating your disk.

Usage:
    python sizewise.py                  summary of the current folder
    python sizewise.py ~/Downloads      summary of another folder
    python sizewise.py --top 20         show the 20 largest entries
    python sizewise.py --files          files only, no folder rollup
    python sizewise.py --json           machine-readable output

Read-only: it walks the tree and prints. It never deletes or moves anything.
Symlinks are not followed, so it cannot loop.

Stdlib only.
"""

import argparse
import json
import os
import sys
from pathlib import Path

APP = "sizewise"
VERSION = "1.0"


def human(size):
    size = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def scan(root):
    """
    Walk root once. Returns a dict with:
      total      bytes under root
      files      number of files
      folders    number of directories
      top_files  list of (path, size) for the biggest files
      top_dirs   list of (path, size) for the biggest immediate children
    Directory totals include everything beneath them.
    """
    root = Path(root)
    total = 0
    file_count = 0
    dir_count = 0
    files = []
    child_totals = {}

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        if current != root:
            dir_count += 1
        for name in filenames:
            path = current / name
            try:
                if path.is_symlink():
                    continue
                size = path.stat().st_size
            except OSError:
                continue
            total += size
            file_count += 1
            files.append((str(path), size))
            # credit every top-level child the file sits under
            try:
                relative = path.relative_to(root)
            except ValueError:
                continue
            top = relative.parts[0] if len(relative.parts) > 1 else "(files in root)"
            child_totals[top] = child_totals.get(top, 0) + size

    files.sort(key=lambda item: item[1], reverse=True)
    dirs = sorted(child_totals.items(), key=lambda item: item[1], reverse=True)
    return {
        "root": str(root),
        "total": total,
        "files": file_count,
        "folders": dir_count,
        "top_files": files,
        "top_dirs": dirs,
    }


def report(result, top=10, files_only=False):
    print(f"\n  {APP} {VERSION} - {result['root']}\n")
    print(f"  {human(result['total'])} in {result['files']:,} file(s), "
          f"{result['folders']:,} folder(s)")

    if not files_only and result["top_dirs"]:
        print(f"\n  Largest {'entries' if True else ''}")
        for name, size in result["top_dirs"][:top]:
            share = (size / result["total"] * 100) if result["total"] else 0
            bar = "#" * max(1, int(share / 4))
            print(f"    {human(size):>9}  {share:5.1f}%  {bar:<25}  {name}")

    if result["top_files"]:
        print("\n  Largest files")
        for path, size in result["top_files"][:top]:
            print(f"    {human(size):>9}  {path}")

    if result["files"] == 0:
        print("\n  Empty folder.")
    print()


def main(argv=None):
    p = argparse.ArgumentParser(prog=APP, description="See where disk space went.")
    p.add_argument("path", nargs="?", default=".", help="folder to scan (default: here)")
    p.add_argument("--top", type=int, default=10, help="how many entries to show (default 10)")
    p.add_argument("--files", action="store_true", help="skip the folder rollup")
    p.add_argument("--json", action="store_true", help="print JSON instead of a report")
    p.add_argument("--version", action="version", version=f"{APP} {VERSION}")
    args = p.parse_args(argv)

    root = Path(os.path.expanduser(args.path))
    if not root.exists():
        print(f"{APP}: no such folder: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"{APP}: not a folder: {root}", file=sys.stderr)
        return 2

    result = scan(root)
    if args.json:
        print(json.dumps({
            "root": result["root"],
            "total": result["total"],
            "files": result["files"],
            "folders": result["folders"],
            "top_files": result["top_files"][:args.top],
            "top_dirs": result["top_dirs"][:args.top],
        }, indent=2))
    else:
        report(result, args.top, args.files)
    return 0


if __name__ == "__main__":
    sys.exit(main())

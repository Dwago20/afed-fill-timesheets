#!/usr/bin/env python3
"""Install this extracted skill into the local Codex skills directory."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_NAME = "afed-fill-timesheets"


def ignored(_directory: str, names: list[str]) -> set[str]:
    ignored_names = {".DS_Store", "__pycache__"}
    ignored_names.update(name for name in names if name.endswith(".pyc"))
    ignored_names.update(name for name in names if name.endswith(".zip"))
    return ignored_names


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install the AFED Timesheet Assistant skill locally."
    )
    parser.add_argument(
        "--destination",
        default=str(Path.home() / ".codex" / "skills"),
        help="Parent skills directory (default: ~/.codex/skills)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing install after moving it to a timestamped backup.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(__file__).resolve().parents[1]
    if source.name != SKILL_NAME or not (source / "SKILL.md").is_file():
        print("Installer is not inside a valid skill package.", file=sys.stderr)
        return 2

    parent = Path(args.destination).expanduser().resolve()
    target = parent / SKILL_NAME
    if target == source:
        print(f"Already installed at {target}")
        return 0

    parent.mkdir(parents=True, exist_ok=True)
    staging = parent / f".{SKILL_NAME}.installing"
    if staging.exists():
        shutil.rmtree(staging)

    backup: Path | None = None
    try:
        shutil.copytree(source, staging, ignore=ignored)
        if target.exists():
            if not args.force:
                print(
                    f"{target} already exists. Re-run with --force to replace it.",
                    file=sys.stderr,
                )
                shutil.rmtree(staging)
                return 3
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            backup = parent / f"{SKILL_NAME}.backup-{stamp}"
            target.rename(backup)
        staging.rename(target)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if backup is not None and backup.exists() and not target.exists():
            backup.rename(target)
        raise

    print(f"Installed {SKILL_NAME} at {target}")
    if backup is not None:
        print(f"Previous installation backed up at {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

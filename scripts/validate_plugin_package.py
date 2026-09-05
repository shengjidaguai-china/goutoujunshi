#!/usr/bin/env python3
"""Check that the Skill-only Plugin keeps the existing Skill runtime in sync."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_SKILL = ROOT / "plugins" / "goutoujunshi" / "skills" / "goutoujunshi"
ERRORS: list[str] = []


def files_under(directory: Path) -> dict[str, Path]:
    if not directory.is_dir():
        return {}
    return {
        path.relative_to(directory).as_posix(): path
        for path in directory.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


def compare_file(relative_path: str) -> None:
    source = ROOT / relative_path
    mirror = PLUGIN_SKILL / relative_path
    if not source.is_file():
        ERRORS.append(f"missing source runtime file: {relative_path}")
        return
    if not mirror.is_file():
        ERRORS.append(f"missing plugin runtime file: {relative_path}")
        return
    if source.read_bytes() != mirror.read_bytes():
        ERRORS.append(f"plugin runtime file differs from source: {relative_path}")


def compare_tree(relative_directory: str) -> None:
    source_root = ROOT / relative_directory
    mirror_root = PLUGIN_SKILL / relative_directory
    source_files = files_under(source_root)
    mirror_files = files_under(mirror_root)

    for relative_path in sorted(set(source_files) - set(mirror_files)):
        ERRORS.append(
            f"missing plugin runtime file: {Path(relative_directory, relative_path).as_posix()}"
        )
    for relative_path in sorted(set(mirror_files) - set(source_files)):
        ERRORS.append(
            f"unexpected plugin runtime file: {Path(relative_directory, relative_path).as_posix()}"
        )
    for relative_path in sorted(set(source_files) & set(mirror_files)):
        if source_files[relative_path].read_bytes() != mirror_files[relative_path].read_bytes():
            ERRORS.append(
                "plugin runtime file differs from source: "
                f"{Path(relative_directory, relative_path).as_posix()}"
            )


def main() -> int:
    if not PLUGIN_SKILL.is_dir():
        ERRORS.append(f"missing plugin Skill directory: {PLUGIN_SKILL}")
    compare_file("SKILL.md")
    for directory in ("agents", "references", "documentation"):
        compare_tree(directory)
    for relative_path in ("scripts/memory_store.py", "scripts/validate_skill.py"):
        compare_file(relative_path)

    if ERRORS:
        for error in ERRORS:
            print(f"ERROR: {error}")
        return 1
    print("plugin runtime mirror validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

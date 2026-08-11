#!/usr/bin/env python3
"""Build a deterministic plugin release ZIP."""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from typing import Optional


INCLUDE = (".codex-plugin", "skills", "hooks", "LICENSE", "README.md")


def _files(root: Path) -> list[Path]:
    files: list[Path] = []
    for name in INCLUDE:
        path = root / name
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(
                item
                for item in path.rglob("*")
                if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"
            )
        else:
            raise ValueError(f"release input is missing: {name}")
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def package(root: Path, output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = "agent-project-governance"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in _files(root):
            relative = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(f"{prefix}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if path.suffix == ".py" else 0o644) << 16
            archive.writestr(info, path.read_bytes())
    return len(_files(root))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="package-release")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        count = package(Path(args.root).resolve(), Path(args.output).resolve())
    except (OSError, ValueError) as exc:
        print(f"package-release: {exc}", file=sys.stderr)
        return 1
    print(f"Packaged {count} files into {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

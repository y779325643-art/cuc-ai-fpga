"""Build deterministic SHA-256 inventories for immutable dataset releases."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys
import tempfile


RELEASE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
HASH_CHUNK_SIZE = 1024 * 1024


def ensure_within_root(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"path escapes repository root: {path}")
    return resolved


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(HASH_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def release_directories(root: Path, release_id: str) -> tuple[Path, Path]:
    if not RELEASE_ID_PATTERN.fullmatch(release_id):
        raise ValueError(f"unsafe release ID: {release_id!r}")

    payload = ensure_within_root(root / "datasets" / release_id, root)
    exports = ensure_within_root(root / "datasets" / f"{release_id}_exports", root)
    for path in (payload, exports):
        if not path.is_dir():
            raise FileNotFoundError(f"release directory is missing: {path}")
    return payload, exports


def inventory_records(root: Path, release_id: str) -> list[tuple[str, str]]:
    roots = release_directories(root, release_id)
    files: list[tuple[str, Path]] = []
    for release_root in roots:
        for candidate in release_root.rglob("*"):
            if not candidate.is_file():
                continue
            ensure_within_root(candidate, root)
            relative_path = candidate.relative_to(root).as_posix()
            files.append((relative_path, candidate))

    return [
        (sha256_file(path), relative_path)
        for relative_path, path in sorted(files, key=lambda item: item[0])
    ]


def write_inventory(root: Path, release_id: str) -> Path:
    records = inventory_records(root, release_id)
    output_dir = ensure_within_root(root / "datasets" / "manifests", root)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = ensure_within_root(output_dir / f"{release_id}.sha256", root)

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=output_dir,
            prefix=f".{release_id}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            for digest, relative_path in records:
                temporary.write(f"{digest}  {relative_path}\n".encode("utf-8"))
        temporary_path.replace(output_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    return output_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--release", action="append", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print(f"repository root is missing: {root}", file=sys.stderr)
        return 2

    try:
        for release_id in args.release:
            output_path = write_inventory(root, release_id)
            print(output_path.relative_to(root).as_posix())
    except (FileNotFoundError, OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

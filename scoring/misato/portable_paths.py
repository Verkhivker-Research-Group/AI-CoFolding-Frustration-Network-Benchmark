"""Resolve manifest paths relative to this checkout, never to a user's PC."""
from __future__ import annotations

import os
from pathlib import Path, PureWindowsPath


REPO_ROOT = Path(__file__).resolve().parents[2]
_configured_data = Path(os.environ.get("PLB_BENCH_DATA_ROOT", "data")).expanduser()
DATA_ROOT = (_configured_data if _configured_data.is_absolute()
             else REPO_ROOT / _configured_data).resolve()


def resolve_path(value: str, repo_root: Path = REPO_ROOT) -> Path:
    """Resolve a repository-relative path and reject absolute/traversal paths."""
    if not value:
        raise ValueError("empty manifest path")
    normalized = value.replace("\\", "/")
    if Path(normalized).is_absolute() or PureWindowsPath(value).is_absolute():
        raise ValueError("manifest paths must be repository-relative")
    root = repo_root.resolve()
    relative = Path(normalized)
    if relative.parts[0] == "data":
        path = (DATA_ROOT / Path(*relative.parts[1:])).resolve()
        if not path.is_relative_to(DATA_ROOT):
            raise ValueError("manifest path escapes data root")
        return path
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("manifest path escapes repository root")
    return path


def relative_path(path: Path, repo_root: Path = REPO_ROOT) -> str:
    """Serialize a local input path without exposing its host location."""
    resolved = path.resolve()
    if resolved.is_relative_to(DATA_ROOT):
        return (Path("data") / resolved.relative_to(DATA_ROOT)).as_posix()
    try:
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError as error:
        raise ValueError("input must be located under the repository root") from error

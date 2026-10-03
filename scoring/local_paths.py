"""Portable locations shared by the standalone scoring scripts."""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def configured_data_root() -> Path:
    """Use an explicit data root or the repository's ignored ``data`` folder."""
    value = Path(os.environ.get("PLB_BENCH_DATA_ROOT", "data")).expanduser()
    return (value if value.is_absolute() else REPO_ROOT / value).resolve()


DATA_ROOT = configured_data_root()

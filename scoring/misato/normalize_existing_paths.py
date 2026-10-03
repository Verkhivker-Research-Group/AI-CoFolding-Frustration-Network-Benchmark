"""Convert legacy MISATO table paths to the portable archive layout.

This is a one-time, deterministic migration; numerical and status fields are
copied unchanged. Run with --write only after reviewing the dry-run counts.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from collections import Counter
from pathlib import Path, PureWindowsPath


TABLES = (
    "crystal_pose_all.csv",
    "inventory/primary_ligand_identity.csv",
    "inventory/raw_prediction_records.csv",
    "inventory/target_manifest.csv",
    "misato_score_all_heavy_selected_v3.csv",
    "misato_score_all_selected_v2.csv",
    "misato_score_all_strict_v1.csv",
    "misato_score_allcopies_v1.csv",
    "pose_qm_graph_audit_v1/pose_qm_graph_audit.csv",
)
PATH_COLUMNS = {
    "pose_path", "source_path", "equibind_path", "diffdock_path",
    "equibind_primary_path", "diffdock_primary_path", "reference_path",
}


def normalize(value: str) -> str:
    if not value:
        return value
    parts = value.replace("\\", "/").split("/")
    lowered = [part.lower() for part in parts]
    if "equibind_output" in lowered:
        tail = parts[lowered.index("equibind_output") + 1:]
        if len(tail) != 2 or not tail[1].lower().endswith(".sdf"):
            raise ValueError(f"Unexpected EquiBind path layout: {value}")
        return "/".join(("data", "misato", "poses", "equibind", *tail))
    if "misatodiffdockresults" in lowered:
        tail = parts[max(i for i, item in enumerate(lowered) if item == "misatodiffdockresults") + 1:]
        if len(tail) != 2 or not tail[1].lower().endswith(".sdf"):
            raise ValueError(f"Unexpected DiffDock path layout: {value}")
        return "/".join(("data", "misato", "poses", "diffdock", *tail))
    if lowered[:2] == ["misato_output", "rcsb_asymmetric_unit"]:
        if len(parts) != 3 or not parts[2].lower().endswith(".cif"):
            raise ValueError(f"Unexpected reference path layout: {value}")
        return f"data/misato/references/{parts[2]}"
    if PureWindowsPath(value).is_absolute() or Path(value).is_absolute():
        raise ValueError(f"Unrecognized absolute path: {value}")
    return value.replace("\\", "/")


def update_table(path: Path, write: bool) -> tuple[int, Counter[str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        if not fields:
            raise ValueError(f"Missing header: {path}")
        rows = list(reader)
    changes: Counter[str] = Counter()
    for row in rows:
        for field in PATH_COLUMNS & row.keys():
            old = row[field]
            new = normalize(old)
            if old != new:
                changes[field] += 1
                row[field] = new
    if write and changes:
        fd, temporary = tempfile.mkstemp(dir=path.parent, suffix=".csv")
        try:
            with os.fdopen(fd, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            os.replace(temporary, path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise
    return len(rows), changes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("misato_output"))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    results = {}
    for name in TABLES:
        count, changes = update_table(args.output_dir / name, args.write)
        results[name] = {"rows": count, "path_changes": dict(changes)}
    summary_path = args.output_dir / "inventory/inventory_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["sources"] = {
        "equibind_root": "data/misato/poses/equibind",
        "diffdock_root": "data/misato/poses/diffdock",
    }
    if args.write:
        summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

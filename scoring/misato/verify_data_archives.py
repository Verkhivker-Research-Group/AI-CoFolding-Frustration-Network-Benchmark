"""Check that portable MISATO CSV inputs are present in local data ZIPs."""
from __future__ import annotations

import argparse
import csv
import json
import tempfile
from collections import Counter
from pathlib import Path, PureWindowsPath
from zipfile import ZipFile

try:
    from .normalize_existing_paths import PATH_COLUMNS, TABLES
except ImportError:  # direct script execution
    from normalize_existing_paths import PATH_COLUMNS, TABLES


def validate(output_dir: Path, archive_dir: Path) -> dict[str, object]:
    poses = archive_dir / "misato_delivered_poses.zip"
    refs = archive_dir / "misato_reference_cifs.zip"
    manifest = json.loads((archive_dir / "archive_manifest.json").read_text(encoding="utf-8"))
    recorded = {item["file"]: item for item in manifest["archives"]}
    for archive in (poses, refs):
        if archive.name not in recorded or archive.stat().st_size != recorded[archive.name]["bytes"]:
            raise ValueError(f"Archive manifest size mismatch: {archive.name}")
    with ZipFile(poses) as pose_zip, ZipFile(refs) as ref_zip:
        pose_members = {info.filename: info for info in pose_zip.infolist()}
        ref_members = {info.filename: info for info in ref_zip.infolist()}
        if len(pose_members) != len(pose_zip.infolist()) or len(ref_members) != len(ref_zip.infolist()):
            raise ValueError("Duplicate archive members")
        if (len(pose_members) != recorded[poses.name]["members"] or
                len(ref_members) != recorded[refs.name]["members"]):
            raise ValueError("Archive manifest member-count mismatch")
        counts: Counter[str] = Counter()
        for name in TABLES:
            with (output_dir / name).open(newline="", encoding="utf-8-sig") as handle:
                for row in csv.DictReader(handle):
                    counts["table_rows"] += 1
                    for field in PATH_COLUMNS & row.keys():
                        value = row[field]
                        if not value:
                            continue
                        if PureWindowsPath(value).is_absolute() or Path(value).is_absolute():
                            raise ValueError(f"Absolute {field} in {name}: {value}")
                        if not value.startswith("data/misato/"):
                            raise ValueError(f"Unexpected {field} in {name}: {value}")
                        members = ref_members if value.startswith("data/misato/references/") else pose_members
                        if value not in members:
                            raise FileNotFoundError(f"Missing archive member: {value}")
                        if field == "source_path" and row.get("file_size_bytes"):
                            if members[value].file_size != int(row["file_size_bytes"]):
                                raise ValueError(f"Size mismatch: {value}")
                        counts[f"verified_{field}"] += 1
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sample_pose = next(iter(pose_members))
            sample_ref = next(iter(ref_members))
            pose_zip.extract(sample_pose, root)
            ref_zip.extract(sample_ref, root)
            if not (root / sample_pose).is_file() or not (root / sample_ref).is_file():
                raise AssertionError("Clean extraction smoke test failed")
        return {"pose_members": len(pose_members), "reference_members": len(ref_members),
                "checks": dict(sorted(counts.items())), "sample_extraction": "passed"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("misato_output"))
    parser.add_argument("--archive-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.output_dir, args.archive_dir), indent=2))


if __name__ == "__main__":
    main()

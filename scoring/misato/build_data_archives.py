"""Package delivered MISATO poses and static references for a clean checkout.

Archive members use the same repository-relative paths as the CSV manifests.
Source directories are read-only. The outputs are local Zenodo-upload candidates;
this script does not publish them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def files(root: Path, suffix: str) -> list[Path]:
    if not root.is_dir():
        raise FileNotFoundError(root)
    return sorted(path for path in root.rglob(f"*{suffix}") if path.is_file())


def write_archive(output: Path, members: list[tuple[Path, str]]) -> dict[str, object]:
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "x", compression=ZIP_DEFLATED, compresslevel=1, allowZip64=True) as archive:
        for index, (source, name) in enumerate(members, 1):
            archive.write(source, name)
            if index % 1000 == 0:
                print(f"{output.name}: {index}/{len(members)}", flush=True)
    return {"file": output.name, "members": len(members),
            "bytes": output.stat().st_size, "sha256": digest(output)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equibind-root", type=Path, required=True)
    parser.add_argument("--diffdock-root", type=Path, required=True)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    outputs = [args.out_dir / "misato_delivered_poses.zip",
               args.out_dir / "misato_reference_cifs.zip",
               args.out_dir / "archive_manifest.json"]
    if any(path.exists() for path in outputs):
        raise FileExistsError("Archive output exists; choose an unused output directory")
    pose_members = []
    for method, root in (("equibind", args.equibind_root), ("diffdock", args.diffdock_root)):
        for source in files(root, ".sdf"):
            relative = source.relative_to(root)
            if len(relative.parts) != 2:
                raise ValueError(f"Unexpected {method} layout: {source}")
            pose_members.append((source, f"data/misato/poses/{method}/{relative.as_posix()}"))
    references = files(args.reference_root, ".cif")
    reference_members = [(path, f"data/misato/references/{path.name}") for path in references]
    if len(set(name for _, name in pose_members + reference_members)) != len(pose_members) + len(reference_members):
        raise ValueError("Archive member collision")
    print(f"Packaging {len(pose_members)} poses and {len(reference_members)} references", flush=True)
    result = {
        "layout": "Extract both ZIPs into the repository root; data/ is ignored by Git.",
        "archives": [write_archive(outputs[0], pose_members),
                     write_archive(outputs[1], reference_members)],
    }
    outputs[2].write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()

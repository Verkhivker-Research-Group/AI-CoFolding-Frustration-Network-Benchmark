"""Portable MISATO paths and local archive layout, without chemistry deps."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from unittest.mock import patch

from scoring.misato.build_data_archives import write_archive
from scoring.misato.create_manifest import archived_path
from scoring.misato.normalize_existing_paths import normalize
from scoring.misato import portable_paths


class PathMigrationTests(unittest.TestCase):
    def test_new_manifest_uses_the_same_layout(self):
        self.assertEqual(archived_path("equibind", "ABCD", "lig_equibind_corrected.sdf"),
                         "data/misato/poses/equibind/ABCD/lig_equibind_corrected.sdf")

    def test_legacy_sources_map_to_archive_layout(self):
        self.assertEqual(
            normalize(r"X:\arbitrary\equibind_output\ABCD\lig_equibind_corrected.sdf"),
            "data/misato/poses/equibind/ABCD/lig_equibind_corrected.sdf",
        )
        self.assertEqual(
            normalize(r"X:\arbitrary\MisatoDiffdockResults\ABCD\rank1.sdf"),
            "data/misato/poses/diffdock/ABCD/rank1.sdf",
        )
        self.assertEqual(
            normalize(r"misato_output\rcsb_asymmetric_unit\ABCD.cif"),
            "data/misato/references/ABCD.cif",
        )

    def test_paths_resolve_in_another_checkout_or_data_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "elsewhere"
            with patch.object(portable_paths, "DATA_ROOT", data):
                value = "data/misato/poses/diffdock/ABCD/rank1.sdf"
                self.assertEqual(portable_paths.resolve_path(value, root),
                                 data / "misato/poses/diffdock/ABCD/rank1.sdf")
                self.assertEqual(portable_paths.relative_path(
                    data / "misato/poses/diffdock/ABCD/rank1.sdf", root), value)
            with self.assertRaises(ValueError):
                portable_paths.resolve_path("../outside.sdf", root)
            with self.assertRaises(ValueError):
                portable_paths.resolve_path("C:/private/pose.sdf", root)

    def test_archive_member_matches_manifest_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pose = root / "rank1.sdf"
            pose.write_text("sample", encoding="utf-8")
            archive = root / "poses.zip"
            name = "data/misato/poses/diffdock/ABCD/rank1.sdf"
            result = write_archive(archive, [(pose, name)])
            self.assertEqual(result["members"], 1)
            with ZipFile(archive) as handle:
                self.assertEqual(handle.namelist(), [name])
                self.assertEqual(handle.read(name), b"sample")


if __name__ == "__main__":
    unittest.main()

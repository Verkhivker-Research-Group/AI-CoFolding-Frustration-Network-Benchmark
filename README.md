# AI Co-Folding Frustration Network Benchmark

## Examining Prediction Limits of AI Co-Folding Models for Detection of Ligand Binding: Unmasking the Biophysical Grammar Using Frustration Analysis and Network Modeling

This repository contains the structural benchmarking code and processed results carried forward from the [AI Co-Folding Allostery Benchmark Revision](https://github.com/Verkhivker-Research-Group/AI-CoFolding-Allostery-Benchmark-Revision), together with an evaluation of DiffDock and EquiBind poses delivered for MISATO complexes. The MISATO workflow scores existing ligand poses against static crystal references. It does not regenerate Lucas Turano's docking predictions or use MISATO molecular dynamics frames as docking inputs.

## Pipeline Overview

The analysis is organized into the following stages:

1. Inventory delivered predictions and define the primary-pose cohort.
2. Audit ligand identity, experimental references, and data coverage.
3. Score ligand placement and protein-ligand contacts.
4. Retain per-pose status, reference assignment, and metric provenance.
5. Export method-specific tables for downstream statistical analysis.

The stage directories `0_setup/` through `5_aggregate/` and the `plb_bench` package retain the earlier orthosteric and allosteric co-folding benchmark. The MISATO-specific implementation is in `scoring/misato/`. These are distinct evaluation regimes and should not be pooled without accounting for receptor mode and metric definitions.

## Models and Datasets

| Component | Models represented | Evaluation input |
| --- | --- | --- |
| Inherited orthosteric and allosteric benchmarks | AlphaFold 3, Chai-1, Boltz-2, Protenix, DynamicBind | Processed results and scoring code from the previous benchmark |
| MISATO delivered-pose evaluation | DiffDock, EquiBind | Delivered SDF poses and RCSB asymmetric-unit crystal CIFs |

The MISATO source dataset was assembled from PDBbind structures and provides QM and MD data. The original MISATO HDF5 files are not tracked here. According to the collaborator's report, the docking runs used a static RCSB receptor and a ligand conformer built from QM coordinates; they did not use MISATO MD frames or the official MD train, validation, and test splits. The original docking input preparation, model invocation, and complete failure logs are not present, so this repository supports reanalysis of delivered poses rather than exact reproduction of those runs.

### MISATO cohort accounting

| Quantity | DiffDock | EquiBind |
| --- | ---: | ---: |
| Delivered primary poses | 8,419 | 8,565 |
| Poses with formal pose RMSD, lDDT-PLI, and static-receptor QS in the final merged table | 7,780 | 7,899 |
| Poses with gnina CNNscore in the final merged table | 8,419 | 8,565 |

The delivered primary poses span 8,606 unique target IDs, with 8,379 IDs represented by both methods. These counts are denominators for delivered outputs, not the complete 19,413-entry MISATO QM set and not measures of model failure rate. The [cohort accounting](misato_output/methods_accounting_v7/cohort_accounting.json) distinguishes directly observed files from collaborator-reported input and failure counts. The [target manifest](misato_output/inventory/target_manifest.csv) provides per-ID delivery status.

## Evaluation Metrics

### Inherited co-folding benchmark

The earlier pipeline reports ligand pose RMSD, pocket RMSD, ligand-inclusive QS, lDDT-PLI, and available model confidence. Its pocket and interface metrics can include receptor placement and conformational error. The previous repository documents those metrics and its model-specific selection rules.

### MISATO static-receptor docking

| Metric | Definition and interpretation |
| --- | --- |
| Pose RMSD | OpenStructure symmetry-aware ligand heavy-atom RMSD against an assigned crystal ligand copy. Scored rows carry the exact reference and metric source. |
| lDDT-PLI | OpenStructure local distance difference test for the protein-ligand interface. |
| Static-receptor QS | Ligand-inclusive contact agreement against the same crystal polymer receptor. It is not interchangeable with co-folding QS, which can include receptor error. |
| Native confidence | DiffDock's delivered confidence logit, recovered by matching the primary SDF to confidence-bearing output by SHA-256. EquiBind did not provide a corresponding native score, so its field is blank. |
| Rescore confidence | gnina `--score_only` CNNscore for each delivered pose. This is a common rescoring scale, not a method-native score and not a second docking run. Because MISATO derives from PDBbind, this score should not be interpreted as an unbiased absolute accuracy estimate. |
| Pocket RMSD | Not applicable to the rigid-receptor MISATO runs because the receptor is the reference crystal structure. The final MISATO export omits this column. |

The reference audit handles multiple crystal ligand copies and records cases that cannot be assigned or graph-matched. Multi-residue recovery is tracked separately from single-residue scoring. Blank metrics indicate unavailable or inapplicable results, never numeric zero.

## Output Files

| Location | Contents |
| --- | --- |
| `evalspreadsheets/misato_v4/diffdockmainligand.csv` | Final DiffDock table, one row per delivered primary pose |
| `evalspreadsheets/misato_v4/equibindmainligand.csv` | Final EquiBind table, one row per delivered primary pose |
| `misato_output/misato_static_metrics_v1.csv` | Full per-pose metrics, score status, reference assignment, confidence source, and exclusion reason |
| `evalspreadsheets/misato_v3/pose_provenance.csv` | Compact pose-level provenance and status sidecar |
| `misato_output/methods_accounting_v7/` | Cohort counts and per-pose provenance used for Methods reporting |
| `evalspreadsheets/main/`, `evalspreadsheets/allo/`, `evalspreadsheets/asd_best/`, `evalspreadsheets/asd_avg/`, `evalspreadsheets/pla_best/`, `evalspreadsheets/pla_avg/` | Preserved outputs from the earlier co-folding benchmark |

The two MISATO v4 CSVs have columns `id`, `pose rmsd`, `qs score`, `lddt-pli`, `confidence`, and `rescore_confidence`. In these files, `qs score` means **static-receptor QS**. For direct DiffDock versus EquiBind comparisons, use the paired subset and report its denominator separately. Do not replace blank values with zero. The full metrics and provenance tables should be used when filtering status or inspecting exclusions.

## Repository Structure

- `0_setup/` through `5_aggregate/`: staged preparation, normalization, scoring, and aggregation code inherited from the co-folding benchmark.
- `scoring/plb_bench/`: the reusable scoring package and its tests.
- `scoring/misato/`: MISATO inventory, reference audits, static docking scores, multi-residue recovery, gnina rescoring, static QS, and exports.
- `misato_output/`: versioned intermediate and final MISATO score tables and accounting records.
- `evalspreadsheets/`: analysis-ready method-specific CSVs.
- `plb_bench_output/`: retained benchmark-level intermediate tables.
- `references/`: small mappings tracked in Git. Large crystal CIFs are distributed separately.
- `environment-misato.yml`: WSL/Linux environment specification for MISATO analysis.

Large SDF and CIF inputs are intentionally excluded from Git. The companion data package uses `data/misato/poses/{equibind,diffdock}/` and `data/misato/references/`. Manifest paths are relative to the repository root. `PLB_BENCH_DATA_ROOT` can point to a separate extracted `data/` directory.

## Reproducing the MISATO Evaluation Tables

Run the chemistry and OpenStructure-dependent stages in a Linux environment such as WSL. From the repository root:

```bash
conda env create -f environment-misato.yml
conda activate misato-benchmark

# Extract the companion pose and reference ZIPs into this repository root.
unzip /path/to/misato_delivered_poses.zip -d .
unzip /path/to/misato_reference_cifs.zip -d .

python scoring/misato/verify_data_archives.py --archive-dir /path/to/archive
python -m unittest discover -s scoring/misato/tests
```

The tracked `misato_output/misato_static_metrics_v1.csv` can be re-exported to the final compact schema without rerunning structural scoring. Select an output directory that does not already exist:

```bash
python scoring/misato/export_evalspreadsheets_v4.py \
  --source misato_output/misato_static_metrics_v1.csv \
  --out-dir /tmp/misato_v4_check
```

Recomputing the underlying scores additionally requires the extracted SDF and CIF archives, OpenStructure 2.11.1, and the versioned scripts in `scoring/misato/`. Recomputing CNNscore requires a separate `gnina` executable. Reproducing Lucas's original docking generation would require his input-preparation and model-run artifacts, which are not included. The earlier co-folding pipelines also require their separate raw prediction archives.

## Data Provenance and References

1. MISATO dataset and paper: [MISATO: machine learning dataset of protein-ligand complexes for structure-based drug discovery](https://doi.org/10.1038/s43588-024-00627-2); [original MISATO data](https://zenodo.org/records/7711953); [dataset code](https://github.com/t7morgen/misato-dataset).
2. Experimental structures: [RCSB Protein Data Bank](https://www.rcsb.org/). Individual PDB entries retain their own deposition and publication citations.
3. Earlier benchmarking code and results: [AI Co-Folding Allostery Benchmark Revision](https://github.com/Verkhivker-Research-Group/AI-CoFolding-Allostery-Benchmark-Revision).

The companion archive's file guide records ZIP contents, SHA-256 checksums, the delivered-pose cohort, and the original MISATO files that are not rehosted. The repository and the archive should be cited by their final release identifiers once assigned.

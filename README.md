# INFOCOM 2027 Anonymous Artifact

This repository accompanies the submitted paper with locked CSV evidence, figures, selected metadata, verification scripts, and small recipe-level smoke tests. It supports result inspection and configuration validation without packaging raw flow tables, packet captures, serialized arrays, checkpoints, tokenizer payloads, or full training logs.

Full-scale reproduction requires compatible external data and model assets. The included scripts verify evidence files, validate preprocessing/window-construction recipes, and run synthetic smoke tests.

## Quick Start

Verify the packaged evidence:

```bash
python scripts/data_preparation/verify_feature_and_label_mappings.py
python scripts/verification/verify_remaining_locked_sources.py
python scripts/verification/verify_streaming_temporalization_benchmark.py
python scripts/verification/verify_robustness_sensitivity.py
python scripts/verification/verify_manifest_integrity.py
```

Validate the recipe interfaces with synthetic or dry-run inputs:

```bash
python scripts/smoke_test_training_interface.py
python scripts/train.py --config configs/shallow_session.yaml --dry-run
python scripts/train.py --config configs/llm_modernbert_512.yaml --dry-run
python scripts/build_windows.py --config configs/build_windows_session.yaml --dry-run
python scripts/data_preparation/harmonize_schema.py --self-test
```

## Repository Layout

- `manifest/`: source map, claim-to-file map, run index, scope summary,
  checksums, and artifact manifest.
- `evidence/locked_sources/`: CSV sources for paper tables and figures,
  including the structural-preservation evidence and shallow-capacity
  parameter-count audit.
- `evidence/locked_sources/structural_preservation/`: locked evidence and
  notes for the structural-preservation diagnostic in Table I.
- `evidence/locked_sources/rq5_cross_dataset/`: locked evidence and
  notes for the RQ5 cross-dataset generalization table.
- `evidence/locked_sources/temporalization_streaming/`: locked evidence and notes for the matched streaming temporalization microbenchmark.
- `evidence/seed_level/`: compact seed-level summaries for reported
  variability.
- `evidence/deployment/`: deployment benchmark summary.
- `evidence/robustness_sensitivity/`: robustness and sensitivity summary.
- `figures/paper/`: paper PDF figures 1--8 and PNG previews.
- `figures/supplementary/`: supplementary ablation figures retained as supplementary evidence.
- `verification/reports/`: verification summaries.
- `scripts/`: self-contained verification, data-preparation, benchmark-summary,
  and recipe helpers.
- `configs/`: recipe configs documenting external inputs and hyperparameters.
- `src_artifact/`: minimal model, metric, data, and recipe helpers used by the
  scripts.
- `run_metadata/`: selected metadata for representative paper
  configurations.

Start with `manifest/paper_source_map.yaml` for the paper-level source map.

## Supplementary Material

The supplementary appendix is available in
`docs/supplementary/`.

This material expands the paper appendix with additional implementation
details, dataset notes, schema harmonization notes, model descriptions,
experimental settings, additional ablations, reproducibility guidance, and
frequently asked questions.

Start with `docs/supplementary/README.md`, which links to the supplementary
sections:

- `01_overview.md`: overview of the supplementary material.
- `02_datasets.md`: dataset descriptions and scope.
- `03_schema_harmonization.md`: schema alignment and preprocessing details.
- `04_feature_schema.md`: feature schema summary.
- `05_experimental_setup.md`: experimental configuration.
- `06_transformer_models.md`: shallow and pretrained transformer model details.
- `07_design_guidelines.md`: practical design recommendations.
- `08_additional_ablations.md`: supplementary ablation summaries.
- `09_reproducibility.md`: reproducibility and artifact-use notes.
- `10_faq.md`: artifact FAQ.

The supplementary material provides additional implementation and ablation details. It does not
contain raw traffic data, restricted logs, serialized arrays, checkpoints, or
identifying project metadata.

## Feature and Label Harmonization

The schema and label mapping layer is documented in
`docs/feature_specification.csv`, `docs/source_feature_mapping.csv`,
`docs/schema_harmonization.md`, and `docs/label_harmonization.csv`.

The reference recipe `scripts/data_preparation/harmonize_schema.py` applies
source-to-canonical feature mapping, derived-feature construction, identifier
exclusion, and label mapping rules to compatible input tables. Derived frequency
state is fitted on training rows and reused for validation/test rows.

Run `python scripts/data_preparation/verify_feature_and_label_mappings.py` and
`python scripts/data_preparation/harmonize_schema.py --self-test` to validate
the packaged specifications.

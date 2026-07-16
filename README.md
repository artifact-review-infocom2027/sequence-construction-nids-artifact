# INFOCOM 2027 Anonymous Artifact

The repository includes paper-facing figure files, locked CSV evidence,
selected metadata, verification scripts, and smoke-tested recipe interfaces.

This repository accompanies the submitted paper and provides locked evidence
files, selected metadata, and runnable helper scripts for inspecting the
reported results. It is organized as a compact companion repository for result
verification and recipe-level reproducibility.

The repository contains paper-facing CSV evidence, paper-facing figures,
selected public run metadata, verification summaries, recipe configs, and small
smoke-test scripts. The verification scripts check evidence files and validate
training/configuration interfaces without requiring private data.

The repository scope excludes raw flow tables, packet captures, serialized
window arrays, model checkpoints, tokenizer payloads, and full training logs
because those assets are private, licensed, or too large for this anonymous
companion package. Full-scale reproduction uses the documented configs with
external data and model assets supplied by the evaluator.

## Quick Start

Run these commands from the repository root:

```bash
python scripts/smoke_test_training_interface.py
python scripts/train.py --config configs/shallow_session.yaml --dry-run
python scripts/train.py --config configs/llm_modernbert_512.yaml --dry-run
python scripts/build_windows.py --config configs/build_windows_session.yaml --dry-run
```

## Repository Layout

- `manifest/`: public source map, claim-to-file map, run index, scope summary,
  checksums, and artifact manifest.
- `evidence/locked_sources/`: CSV sources for paper tables and figures,
  including the Table II parameter-count audit.
- `evidence/seed_level/`: compact seed-level summaries for reported
  variability.
- `evidence/deployment/`: deployment benchmark summary.
- `evidence/robustness_sensitivity/`: robustness and sensitivity summary.
- `figures/`: paper-facing PDF figures and PNG previews.
- `verification/reports/`: public verification summaries.
- `scripts/`: self-contained verification, data-preparation, benchmark-summary,
  and recipe helpers.
- `configs/`: recipe configs documenting external inputs and hyperparameters.
- `src_artifact/`: minimal model, metric, data, and recipe helpers used by the
  scripts.
- `run_metadata/`: selected public metadata for representative paper
  configurations.

Start with `manifest/paper_source_map.yaml` for the paper-level source map.

## Feature and Label Harmonization

The public schema and label mapping layer is documented in
`docs/feature_specification.csv`, `docs/source_feature_mapping.csv`,
`docs/schema_harmonization.md`, and `docs/label_harmonization.csv`.

The reference recipe `scripts/data_preparation/harmonize_schema.py` applies
source-to-canonical feature mapping, derived-feature construction, identifier
exclusion, and label mapping rules to evaluator-supplied tables.

Run `python scripts/data_preparation/verify_feature_and_label_mappings.py` and
`python scripts/data_preparation/harmonize_schema.py --self-test` to validate
the packaged specifications.

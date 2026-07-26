# Reproducibility

This repository supports result verification, local smoke tests, and documented recipes for experiments that require external data or model assets.

## 1. Verify reported results

Evidence supporting the paper is stored under `evidence/locked_sources/`. `manifest/paper_source_map.yaml` maps paper components to their sources, while `manifest/artifact_claim_to_file_map.csv` provides a claim-level index.

Run:

```bash
python scripts/data_preparation/verify_feature_and_label_mappings.py
python scripts/verification/verify_remaining_locked_sources.py
python scripts/verification/verify_streaming_temporalization_benchmark.py
python scripts/verification/verify_robustness_sensitivity.py
python scripts/verification/verify_manifest_integrity.py
```

## 2. Run local smoke tests

The smoke tests use synthetic inputs and write only under `outputs/`.

```bash
python scripts/smoke_test_training_interface.py
python scripts/train.py --config configs/shallow_session.yaml --dry-run
python scripts/train.py --config configs/llm_modernbert_512.yaml --dry-run
python scripts/build_windows.py --config configs/build_windows_session.yaml --dry-run
python scripts/data_preparation/harmonize_schema.py --self-test
```

## 3. Apply the harmonization recipe

Derived frequency state must be fitted on training rows and reused for validation and test rows. Output files are restricted to `outputs/`.

```bash
# Fit on training data and save the fitted state.
python scripts/data_preparation/harmonize_schema.py \
  --input train.csv \
  --source-dataset CICIDS \
  --fit-state-output outputs/derived_state.json \
  --output outputs/train_harmonized.csv

# Reuse the training-fitted state without refitting.
python scripts/data_preparation/harmonize_schema.py \
  --input validation.csv \
  --source-dataset CICIDS \
  --state-input outputs/derived_state.json \
  --output outputs/validation_harmonized.csv
```

The reference harmonizer performs schema mapping, identifier exclusion, label normalization, and the documented derived features. Model normalization is not implemented by this helper; full experiments must fit normalization statistics on the training split and apply them unchanged to validation and test data.

## 4. Full-scale experiment recipes

The YAML files under `configs/` document expected inputs and key hyperparameters. The included command-line interfaces validate those configurations and provide synthetic smoke tests. Full training and checkpoint-based inference require the original experiment pipeline together with compatible datasets, serialized windows, tokenizers, and model assets.

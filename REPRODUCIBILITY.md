# Reproducibility

This repository supports three levels of reproducibility: verifying reported tables and figures from CSVs, running local smoke tests, and using documented recipes for full-scale reproduction with external assets.

## 1. Verify Results

Paper-facing evidence files live under `evidence/locked_sources/`, with a source map in `manifest/paper_source_map.yaml` and a claim map in `manifest/artifact_claim_to_file_map.csv`. Verification reports in `verification/reports/` summarize the values.

Useful command:

```bash
python scripts/verification/verify_remaining_locked_sources.py
```

## 2. Run Local Smoke Tests

The smoke tests use synthetic examples and recipe configs. They validate the public interfaces and write only under `outputs/`.

```bash
python scripts/smoke_test_training_interface.py
python scripts/train.py --config configs/shallow_session.yaml --dry-run
python scripts/train.py --config configs/llm_modernbert_512.yaml --dry-run
python scripts/build_windows.py --config configs/build_windows_session.yaml --dry-run
```

## 3. Full-Scale Reproduction Recipes

The configs document the expected external inputs and hyperparameters for full-scale reproduction. Evaluators supplying compatible flow tables, window files, checkpoints, tokenizer assets, and model assets can adapt the recipes without relying on private paths.

The shallow serialized-text recipes describe session-coherent windows with window length 32 and stride 16. LLM recipes document encoder-style and decoder-style context settings. The helper scripts validate these recipes while keeping the anonymous repository free of private datasets and model payloads.

## Feature and Label Mapping Check

```bash
python scripts/data_preparation/verify_feature_and_label_mappings.py
python scripts/data_preparation/harmonize_schema.py --self-test
```

Full data harmonization uses external flow tables supplied by the evaluator. The public reference script documents source-to-canonical feature mapping, derived-feature construction, identifier exclusion, and label normalization.

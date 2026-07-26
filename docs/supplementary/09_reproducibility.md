# Reproducibility

The repository supports evidence verification, configuration inspection, and synthetic smoke tests. It does not include raw datasets, serialized windows, pretrained model payloads, or full checkpoints.

Run the dry-run commands from the repository root:

```bash
python scripts/smoke_test_training_interface.py
python scripts/train.py --config configs/shallow_session.yaml --dry-run
python scripts/train.py --config configs/llm_modernbert_512.yaml --dry-run
python scripts/build_windows.py --config configs/build_windows_session.yaml --dry-run
```

Run the verification checks:

```bash
python scripts/data_preparation/verify_feature_and_label_mappings.py
python scripts/data_preparation/harmonize_schema.py --self-test
python scripts/verification/verify_remaining_locked_sources.py
python scripts/verification/verify_streaming_temporalization_benchmark.py
python scripts/verification/verify_robustness_sensitivity.py
python scripts/verification/verify_manifest_integrity.py
```

The harmonization command requires an explicit training-fit or transform mode. Use `--fit-state-output` on training data and reuse the saved state through `--state-input` for validation and test data. Full-scale training requires compatible external data and model assets.

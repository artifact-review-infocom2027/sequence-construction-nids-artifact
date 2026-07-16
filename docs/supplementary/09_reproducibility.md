# Reproducibility

The public artifact supports evidence verification, configuration inspection,
and smoke-tested recipe interfaces. It does not include raw datasets,
serialized windows, pretrained model payloads, or full checkpoints.

Run the public dry-run commands from the repository root:

```bash
python scripts/smoke_test_training_interface.py
python scripts/train.py --config configs/shallow_session.yaml --dry-run
python scripts/train.py --config configs/llm_modernbert_512.yaml --dry-run
python scripts/build_windows.py --config configs/build_windows_session.yaml --dry-run
```

Run the public verification checks:

```bash
python scripts/data_preparation/verify_feature_and_label_mappings.py
/usr/bin/python3 scripts/verification/verify_remaining_locked_sources.py
```

The dry-run commands validate configuration structure and public interfaces.
Full-scale reproduction requires compatible external data and model assets
provided by the evaluator.

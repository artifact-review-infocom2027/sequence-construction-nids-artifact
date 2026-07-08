# Data

The public artifact contains four data classes: locked result CSVs for paper tables and figures, selected public metadata for representative configurations, paper-facing PDF/PNG figures, and synthetic smoke-test examples. These files are sufficient to inspect the reported values and validate the helper scripts.

The artifact does not include raw flow tables, packet captures, serialized window arrays, model checkpoints, tokenizer payloads, or full training logs. Those assets are outside the repository scope for privacy, licensing, and size reasons. Full-scale reproduction uses external assets documented by the recipe configs.

## Feature and Label Specifications

This repository includes public feature and label mapping specifications for the harmonized evaluation schema. `docs/source_feature_mapping.csv` records source-to-canonical mappings, derived-feature transforms, sentinel handling, and model-input status. `scripts/data_preparation/harmonize_schema.py` is a reference implementation for evaluator-supplied CSV or Parquet tables.

# Repository Scope

This repository is scoped to paper-result verification and recipe-level reproducibility. It packages fixed evidence files, selected metadata, figures, and small helper scripts that run without raw data.

Full raw-data processing, checkpoint training, tokenizer assets, and complete experiment logs are outside the scope of this repository. The included configs document the external inputs and hyperparameters expected for full-scale reproduction.

## Feature and Label Specifications

This repository includes feature and label mapping specifications for the harmonized evaluation schema. The harmonization script applies the documented source-to-canonical feature map, model-input selection, identifier exclusion, and label rules to evaluator-supplied tables.

# Repository Scope

This repository is scoped to paper-result verification and recipe-level reproducibility. It packages locked evidence files, selected public metadata, public figures, and small helper scripts that run without raw data.

Full raw-data processing, checkpoint training, tokenizer assets, and complete experiment logs are outside this anonymous companion repository. The included configs document the external inputs and hyperparameters expected for full-scale reproduction.

## Feature and Label Specifications

This repository includes public feature and label mapping specifications for the harmonized evaluation schema. The public harmonization script applies the documented source-to-canonical feature map, model-input selection, identifier exclusion, and label rules to evaluator-supplied tables.

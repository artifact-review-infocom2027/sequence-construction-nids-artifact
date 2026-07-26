# Feature Specification

The feature specification describes the harmonized 47-field pipeline
schema used by the paper. It comprises 46 model-input attributes plus one
temporalization/control key, `symm_ips_ports`, that supports session-aware
window construction and is not supplied as a predictive transformer input.

Identifier-like control fields are not model predictors. Fields used only for
grouping or window construction are marked with `model_input=false` in
`feature_specification.csv`.

See `docs/feature_specification.csv` for the complete machine-readable table.

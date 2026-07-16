# Schema Harmonization

Schema harmonization maps dataset-specific columns into a shared public feature
interface. The main public references are:

- `docs/schema_harmonization.md`
- `docs/source_feature_mapping.csv`
- `docs/label_harmonization.csv`
- `docs/feature_specification.csv`

## Source-to-Canonical Mapping

The source-to-canonical mapping records how dataset-specific fields are aligned
to common names before representation construction. Equivalent packet, byte,
timing, TCP, application, TLS, and derived features are standardized so that the
same model interface can be used across the evaluated datasets.

## Missing and Sentinel Handling

The harmonization layer separates true numeric values from missing or
not-applicable values. Missing inputs are represented consistently before model
preparation, and derived features are computed only from available compatible
source columns. This keeps feature construction deterministic across datasets
while avoiding private source paths or raw records in the artifact.

## Label Harmonization

Dataset-specific labels are mapped into the public label space documented in
`docs/label_harmonization.csv`. The verification script
`scripts/data_preparation/verify_feature_and_label_mappings.py` checks the
packaged feature and label specifications.

# Schema Harmonization

The public schema contains 47 pipeline fields. Predictor fields are marked with `model_input=true`; fields used only for temporalization/control are marked `model_input=false`.

The schema layer is documented by three files:

- `docs/feature_specification.csv`: canonical public fields, data type, role, and model-input status.
- `docs/source_feature_mapping.csv`: source-to-canonical mappings, derived-feature transforms, and sentinel handling for unavailable source fields.
- `docs/excluded_identifier_fields.csv`: identifiers and control columns removed from model inputs.

The reference script `scripts/data_preparation/harmonize_schema.py` applies these public rules to evaluator-supplied CSV or Parquet tables. It strips known source headers, maps native names with exact normalized aliases or scoped patterns, computes public derived features, fills unavailable fields with public sentinels, removes identifier/control fields by exact alias, and emits only fields marked as model inputs plus an optional harmonized label.

When multiple native fields map to the same canonical feature, the public recipe coalesces them using deterministic priority rules. Directional CICIDS fields are preferred over aggregate packet-length summaries; MQCIDS application-service aliases are coalesced; UNSW `attack_cat` is preferred over binary `Label` for attack-family mapping.

For CICIDS, packet counts come from `Tot Fwd Pkts` and `Tot Bwd Pkts`; packet-rate fields are not used as packet counts. Directional byte-rate fields are derived from directional bytes divided by duration when source rate columns are unavailable.

`symm_ips_ports` is documented as a temporalization key only. It can support window/session construction, but it is not a predictor field in the public model schema.

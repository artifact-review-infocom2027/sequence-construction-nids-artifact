# Schema Harmonization

The shared schema contains 47 pipeline fields. Predictor fields are marked with `model_input=true`; fields used only for temporalization or control are marked with `model_input=false`.

The schema layer is documented by three files:

- `docs/feature_specification.csv`: canonical fields, data type, role, and model-input status.
- `docs/source_feature_mapping.csv`: source-to-canonical mappings, derived-feature transforms, and handling of unavailable fields.
- `docs/excluded_identifier_fields.csv`: identifiers and control columns removed from model inputs.

The reference script `scripts/data_preparation/harmonize_schema.py` applies these rules to compatible CSV or Parquet tables. It normalizes source column names, coalesces aliases in a deterministic order, computes the documented derived features, fills unavailable fields with sentinels, removes identifier/control fields, and emits model-input fields plus an optional harmonized label.

When several native fields can populate the same canonical feature, the mapping file records the priority and whether the relationship is exact, a fallback, or a documented proxy. For example, CICIDS aggregate active, idle, and flow-IAT statistics are retained as numeric timing or flow-dynamics proxies; they are not described as direct semantic equivalents of TCP transaction-depth, response-byte, jitter, or directional inter-packet fields.

Destination-port frequency state used by `port_rarity` is fitted on training rows and then reused for validation and test rows. The command-line interface requires either `--fit-state-output` or `--state-input` for non-dry-run processing. The reference harmonizer does not fit model normalization parameters; full experiments must fit normalization on training data and apply the same parameters to validation and test data.

For CICIDS, packet counts come from `Tot Fwd Pkts` and `Tot Bwd Pkts`; packet-rate columns are not treated as counts. Directional byte-rate fields are derived from directional bytes and duration when source rate columns are unavailable. For MQCIDS, application-service aliases are coalesced. For UNSW-NB15, `attack_cat` is preferred over binary `Label` for attack-family mapping.

`symm_ips_ports` is a temporalization key. It may be used for session/window construction, but it is not a predictive model input.

# Feature Schema

The shared schema documents 47 pipeline fields. Of these, 46 are model-input
attributes and one field, `symm_ips_ports`, is a temporalization/control key
used for session-aware window construction rather than as a predictive
transformer input. The categories mirror the paper feature table and are
summarized below.

| Category | Count |
| --- | ---: |
| Flow Statistics | 18 |
| Timing | 9 |
| TCP | 6 |
| Application | 8 |
| TLS | 3 |
| Derived | 3 |
| Temporalization/control key | 1 |
| Total documented fields | 47 |
| Model-input attributes | 46 |

The detailed feature list is packaged in `docs/feature_specification.csv`, with
human-readable notes in `docs/feature_specification.md`. Source-to-canonical
column mappings are recorded in `docs/source_feature_mapping.csv`.

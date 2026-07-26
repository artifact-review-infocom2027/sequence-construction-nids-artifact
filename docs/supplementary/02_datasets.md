# Datasets

The main evaluation uses three network-intrusion datasets: UNSW-NB15,
CICIDS2018, and MQCIDS. The repository records the harmonized feature and
label interfaces used to align these sources for model evaluation.

## Split Protocol

Experiments use a 70/15/15 train, validation, and test split. Normalization
statistics are fit on the training split only and then applied to validation and
test records. This avoids leaking validation or test distribution information
into preprocessing.

## Identifier Exclusion

Identifier-like fields are excluded from model inputs. Examples include fields
that directly encode endpoint identities, ports when treated as identifiers, or
other columns whose primary role is source-specific lookup rather than traffic
behavior. The packaged file `docs/excluded_identifier_fields.csv` lists the
identifier-exclusion policy.

## Repository Scope

The artifact contains schema, label, and evidence summaries. Raw flow tables,
packet captures, serialized windows, and checkpoint files are outside the
repository scope.

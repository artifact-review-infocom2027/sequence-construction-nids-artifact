# Structural Preservation Diagnostics

This directory contains reviewer-facing structural-preservation diagnostics for the submitted transformer-based NIDS paper. The diagnostics compare timestamp-based sliding windows with session-coherent temporalization using the same source-flow universe within each dataset.

## Metrics

For a reconstructed session, eligible related-flow pairs are pairs of flows from the same session whose within-session distance is less than the window length `k`.

- `retention`: fraction of all eligible related-flow pairs that co-occur in at least one diagnostic window.
- `fragmentation`: `1 - retention`.
- `purity`: average dominant-session share inside each window.
- `emittable_retention`: retention restricted to sessions with length at least `k`.
- `emittable_fragmentation`: `1 - emittable_retention`.
- `flow_coverage`: fraction of flows belonging to sessions with length at least `k`.
- `pair_coverage`: fraction of eligible related-flow pairs belonging to sessions with length at least `k`.

## Paper Table

`structural_preservation_paper_table.csv` and `structural_preservation_paper_table.tex` use the main paper setting `k=32, stride=16`. The paper table reports dataset-level values for UNSW-NB15, CICIDS2018, and MQCIDS, plus a macro-average row.

The paper table uses emittable related-flow retention and fragmentation because the inspected session-window implementations drop sessions shorter than `k`; they do not pad short sessions. Emittable related-flow retention separates within-window structural preservation from short-session coverage.

## CICIDS Short-Session Caveat

CICIDS2018 contains many reconstructed sessions shorter than the main window length. The global retention metric therefore underestimates session-coherent retention because many short sessions cannot emit session-coherent windows under the actual implementation. The full CSV keeps both global and emittable metrics so this effect remains visible.

## Sensitivity Settings

The full summary CSV includes sensitivity settings:

- `k=8, stride=4`
- `k=16, stride=8`
- `k=32, stride=16`

No model training or paper figure generation is performed by this diagnostic layer.

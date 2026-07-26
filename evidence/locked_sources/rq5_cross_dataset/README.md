# RQ5 Cross-Dataset Generalization

This directory contains the supplementary cross-dataset transfer table used
for RQ5. Cross-dataset transfer is a stress test: models are trained on one
dataset and evaluated directly on another without fine-tuning. Session-coherent
temporalization is not claimed to solve domain shift universally.

## Files

- `rq5_cross_dataset_raw.csv`: preserved copy of the finalized cross-dataset
  input table.
- `rq5_cross_dataset_paper_table.csv`: parsed paper table with deltas and
  an average row.
- `rq5_cross_dataset_paper_table.tex`: compact LaTeX table source for the
  paper.
- `rq5_cross_dataset_statistics.json`: exact paired signed-rank trend
  diagnostics for Macro-F1 and transfer robustness gap deltas.

## Processing Notes

Fully blank rows are ignored during table construction. Any pre-existing
average row is excluded before recomputing the final Avg. row over the six
directed transfer rows. The finalized input contained no duplicate directed
transfers and no Train=Test rows.

`delta_f1` is computed as `session_f1 - sliding_f1`.

`delta_trg` is computed as `trg_sliding - trg_session`, so positive values
indicate a smaller transfer robustness gap for Session.

The table supports modest average transfer robustness gains, with one negative
transfer direction. The paired signed-rank diagnostics are positive/modest but
statistically inconclusive: Macro-F1 uses W+ = 11, one-sided p = 0.19,
rank-biserial = 0.47; TRG uses W+ = 14, one-sided p = 0.28, rank-biserial =
0.33. Zero Macro-F1 differences are excluded from the signed-rank statistic and
reported in the statistics JSON. No star notation or broad improvement claim is used.

# RQ5 Cross-Dataset Generalization

This directory contains the reviewer-facing cross-dataset transfer table used for RQ5.

## Files

- `rq5_cross_dataset_raw.csv`: preserved copy of the finalized cross-dataset input table.
- `rq5_cross_dataset_paper_table.csv`: parsed paper-facing table with deltas and an average row.
- `rq5_cross_dataset_paper_table.tex`: compact LaTeX table source for the paper.

## Processing Notes
Cross-dataset transfer is a stress test: models are trained on one dataset and evaluated directly on another without fine-tuning. Session-coherent temporalization is not claimed to solve domain shift universally. The table supports modest average transfer robustness gains, with one negative transfer direction.

`delta_f1` is computed as `session_f1 - sliding_f1`.

`delta_trg` is computed as `trg_sliding - trg_session`, so positive values indicate a smaller transfer robustness gap for Session.

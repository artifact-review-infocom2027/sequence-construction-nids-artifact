# Verified Results Summary

The repository evidence files support the paper tables and figures through locked CSVs and paper-facing PDF/PNG figures.

| Component | Evidence | Status |
| --- | --- | --- |
| Representation ablation | `evidence/locked_sources/representation/representation_ablation.csv` | supported |
| Temporalization comparison | `evidence/locked_sources/temporalization/temporalization_values.csv` and `figures/temporalization/temporalization_comparison.png` | supported |
| Capacity ablation | `evidence/locked_sources/capacity/capacity_ablation_meanstd.csv` and `figures/capacity/capacity_heatmap.png` | supported |
| Table II parameter counts | `evidence/locked_sources/capacity/table2_shallow_params_audit.csv` | supported |
| Head ablation | `evidence/locked_sources/head_ablation/head_ablation_meanstd.csv` and `figures/head_ablation/head_ablation.png` | supported |
| LLM comparisons | `evidence/locked_sources/llm_comparison/` | supported |
| Context length | `evidence/locked_sources/context_length/llm_context_length_meanstd.csv` | supported |
| Per-dataset validation | `evidence/locked_sources/per_dataset_validation/per_dataset_validation.csv` | supported |
| Efficiency | `evidence/locked_sources/efficiency/efficiency_context_tradeoff.csv` and `figures/efficiency/efficiency_context_tradeoff.png` | supported |
| Robustness and sensitivity | `evidence/robustness_sensitivity/robustness_sensitivity_summary.csv` | supported |

Metric definitions are summarized in `METRICS.md`. The claim-to-file map is `manifest/artifact_claim_to_file_map.csv`.

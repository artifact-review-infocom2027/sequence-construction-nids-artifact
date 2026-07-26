# Design Guidelines

The evidence supports the following design guidelines.

| Guideline | Evidence |
| --- | --- |
| Prefer session-coherent temporalization for windowed shallow models. | Figure 2 evidence in `evidence/locked_sources/temporalization/temporalization_values.csv`. |
| Use the capacity sweep to identify operating points rather than assuming larger models are always better. | Figure 3 and Table IV evidence in `evidence/locked_sources/capacity/`. |
| Report parameter and throughput tradeoffs together. | Shallow capacity parameter audit in `evidence/locked_sources/capacity/shallow_capacity_parameter_audit.csv`. |
| Treat shallow and pretrained-model comparisons carefully because parameter scale and metric definitions differ by family. | Figure 5 and Figure 6 evidence in `evidence/locked_sources/llm_comparison/` and `evidence/locked_sources/efficiency/`. |
| Exclude identifier fields and document feature harmonization. | Schema files in `docs/`. |

For the shallow capacity tradeoff, moving from the strongest operating point
`(64,4,2)` to the largest evaluated shallow configuration `(256,4,8)` increases
parameters from 0.65M to 3.38M, a 5.2x increase, while throughput decreases from
0.40M to 0.13M flows/s, a 3.1x decrease. Macro-F1 changes from 0.947 to 0.934.

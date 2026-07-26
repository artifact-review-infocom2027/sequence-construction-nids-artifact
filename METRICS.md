# Metrics

Evidence tables report Accuracy, Macro-F1, PR-AUC, and throughput using the units stated in each file.

## Macro-F1

The shallow-transformer tables use **present-label Macro-F1**: class-wise F1 is averaged over labels that occur in the evaluated split (`y_true`). A prediction assigned to a label absent from `y_true` is not added as a separate averaged class, but it still counts as an error for the sample's true class. The helper `paper_macro_f1` in `src_artifact/metrics.py` implements this convention.

Some run metadata also contains `macro_f1_reference`. This is an all-label diagnostic retained from the source evaluation records. It is not used for the paper figures or tables. A task can define seven labels while a particular split contains fewer because some attack families may be absent from that split.

Pretrained-model comparison files retain the Macro-F1 values produced by their corresponding evaluation records. The source map identifies the evidence used for each comparison.

## PR-AUC

PR-AUC is macro-averaged over the evaluable classes defined by the source table. Capacity and head-ablation tables use the present-label PR-AUC fields from their fixed evidence files.

## Throughput

Construction and inference are measured separately:

- **Temporalization input flows/s**: unique timestamp-ordered flow records consumed per second by the CPU window-construction benchmark in Section III-E.
- **Inference windows/s**: model windows evaluated per second.
- **Inference processed-flow positions/s**: `windows/s * window length`. Overlapping windows therefore count repeated flow positions. This is the convention used for the windowed inference rates supporting Figures 2--7.
- **Unique stream advancement**: non-overlapping progress through the original flow stream. It is distinct from processed-flow positions/s.

The repository does not report a combined end-to-end rate. Temporalization construction and transformer inference should not be added or treated as a single acceleration measurement.

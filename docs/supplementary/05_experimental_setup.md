# Experimental Setup

The repository records the paper configuration choices used by the
reported experiment families. Controlled comparisons keep the relevant pipeline
components fixed within each comparison, while shallow-transformer and
pretrained-model families use family-appropriate optimization, batch-size,
precision, and token-budget settings. Exact recipe settings are documented by
the corresponding packaged configs.

## Family-Specific Recipe Settings

- Shallow serialized-text transformer recipes use session-coherent windows with
  window length 32, stride 16, dropout 0.1, batch size 256, epoch budget 20,
  maximum token length 512, and learning rate `0.001` in
  `configs/shallow_session.yaml`.
- ModernBERT recipe configs use batch size 8, epoch budget 3, maximum token
  length 512, and learning rate `0.00002` in
  `configs/llm_modernbert_512.yaml`.
- Qwen2.5-0.5B recipe configs use batch size 8, epoch budget 1, maximum token
  length 512, and learning rate `0.00002` in
  `configs/llm_qwen_512.yaml`.

Data splits, representation, temporalization, and evaluation conventions are
matched where applicable within each reported comparison. The dry-run scripts
validate configuration structure without loading experiment data or model assets.

## Metrics

The artifact reports Macro-F1, PR-AUC, Accuracy, and throughput where
applicable. Macro-F1 is used because intrusion labels are imbalanced and a
balanced class-sensitive metric is needed alongside accuracy.

## Throughput Reporting

The repository keeps construction and inference rates separate. The Section III-E streaming benchmark reports CPU temporalization input flows/s: unique timestamp-ordered input records consumed per second while constructing windows from precomputed session identifiers. Figures 2--7 use inference throughput from locked result tables. When those figures report processed-flow positions/s for windowed models, the value is `windows/s * window length`, so overlapping windows count repeated positions. This is different from unique streaming advancement through the original flow sequence. End-to-end throughput, including both temporalization and model inference, was not measured.

## Hardware Reporting

Hardware-specific benchmark evidence is provided through the packaged deployment
summary rather than machine-identifying host details. See
`evidence/deployment/deployment_benchmark_summary.csv`.

## Reproduction Scope

The scripts validate configuration and evidence consistency. Full-scale training
requires compatible external data and model assets that are not included in the
repository.

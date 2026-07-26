# FAQ

## Why use session windows?

Session windows preserve local behavioral context while keeping inference units
bounded and comparable across datasets.

## Why report Macro-F1?

Macro-F1 gives each class equal weight and is useful when intrusion labels are
imbalanced. Accuracy and PR-AUC are reported alongside it where applicable.

## Why use shallow transformers?

The shallow transformer family provides a compact operating range with strong
performance and high throughput. The capacity sweep spans 0.20M--3.38M
trainable parameters.

## Why not rely only on pretrained language models?

Pretrained models provide useful baselines, but the evaluated 110M--494M model
range is 169x--759x larger than the strongest 0.65M-parameter shallow operating
point. The comparison therefore reports quality, throughput, and parameter scale
together.

## Why exclude identifier fields?

Identifier exclusion reduces the risk that models memorize dataset-specific
endpoint or source artifacts rather than learning behavioral traffic patterns.

## What is excluded from the artifact?

Raw flow tables, packet captures, serialized windows, checkpoint payloads,
tokenizer payloads, and full training logs are outside this repository.

## What can be reproduced from this repository?

The repository supports inspection of locked evidence files, regeneration of selected checks, validation of
feature and label specifications, smoke-tested dry runs, and tracing of paper figures
and tables through the source map.

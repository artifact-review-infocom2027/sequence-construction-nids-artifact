# Overview

The artifact documents a transformer-based network intrusion detection pipeline
with five main stages: input control, representation, temporalization,
transformer inference, and prediction aggregation.

## Pipeline Stages

1. Input control standardizes flow-level records and removes identifier fields
   that could let a model memorize dataset-specific endpoints.
2. Representation converts harmonized flow features into paper-facing model
   inputs such as flow tokens, structured field tokens, or serialized text.
3. Temporalization forms per-flow examples, legacy windows, or session-coherent
   windows depending on the experiment family.
4. Transformer backbones process the chosen representation using shallow
   transformer models or pretrained language-model baselines.
5. Aggregation and prediction convert model outputs into intrusion-detection
   scores and labels for the reported metrics.

The public artifact focuses on locked CSV evidence, paper-facing figures,
selected metadata, and runnable verification or dry-run helpers. It does not
package private raw datasets, checkpoint payloads, or full training logs.

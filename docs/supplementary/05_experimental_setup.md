# Experimental Setup

The public artifact records the paper-facing configuration choices used by the
reported experiment families.

## Shared Training Settings

- Optimizer: Adam
- Learning rate: `1e-4`
- Batch size: 256
- Dropout: 0.1
- Epoch budget: 20 epochs with early stopping
- Session window size: 32 flows
- Stride: 16 flows
- Maximum text length: 512 tokens

## Metrics

The artifact reports Macro-F1, PR-AUC, Accuracy, and throughput where
applicable. Macro-F1 is used because intrusion labels are imbalanced and a
balanced class-sensitive metric is needed alongside accuracy.

## Throughput Reporting

Processed-flow throughput is defined as effective processed flow records divided
by inference time. For windowed temporalization comparisons, processed flow
records are computed as windows multiplied by window length. This measures
inference processing capacity and is distinct from unique streaming advancement
under overlapping windows.

## Hardware Reporting

Hardware-specific benchmark evidence is provided through the packaged deployment
summary rather than private host details. See
`evidence/deployment/posthoc_deployment_full_benchmark_summary.csv` for the
public deployment benchmark summary.

## Public Reproducibility Scope

The public scripts validate configuration and evidence consistency. Full-scale
training requires evaluator-supplied data and model assets that are not included
in the anonymous artifact package.

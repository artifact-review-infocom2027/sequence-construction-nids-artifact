# Matched Streaming Temporalization Benchmark

This directory contains supplementary evidence for the matched streaming temporalization microbenchmark of CPU-side window construction.

The benchmark isolates rolling-window construction after the flow stream has already been ordered. Both methods consume the same timestamp-ordered stream, use the same window length and stride, use the same rolling-state implementation, and perform the same checksum work when a window is emitted.

## Files

- `streaming_temporalization_raw_runs.csv`: measured repetitions used to recompute the aggregate statistics.
- `streaming_temporalization_summary.csv`: medians and interquartile ranges by benchmark selection and method.
- `streaming_temporalization_comparison.csv`: paper-aligned comparison values for the main benchmark and complete-session robustness check.
- `streaming_temporalization_correctness.json`: PASS/FAIL correctness summary.
- `streaming_temporalization_environment.json`: sanitized benchmark environment summary.

## Interpretation

The main benchmark shows that session-aware construction sustains 1.06 million input flows/s, incurs a 2.17x runtime cost relative to global sliding, and emits approximately 50% fewer windows.

The complete-session robustness check shows that session-aware construction sustains 1.02 million input flows/s, incurs a 2.33x runtime cost, and emits approximately 58% fewer windows.

The aggregate row is an arithmetic mean across those two locked selections: runtime ratio `(2.16691421152 + 2.33040334621) / 2 = 2.248658778865`, session processing rate `(1057839.45096 + 1024179.26252) / 2 = 1041009.35674` input flows/s, and window reduction `(50.470677452 + 58.1182435386) / 2 = 54.2944604953%`. Rounded for the paper, these are 2.25x, 1.04 million input flows/s, and 54%.

These results describe CPU-side window construction conditioned on precomputed session identifiers. They do not constitute end-to-end NIDS throughput, do not measure session-ID derivation, and should not be combined with inference throughput as a single acceleration claim. Construction and inference are separately measured stages.

# Matched Streaming Temporalization Microbenchmark

This supplementary benchmark isolates CPU-side streaming window-construction overhead. It is conditioned on precomputed session identifiers and does not measure session-ID derivation.

Both methods consume the same timestamp-ordered flow stream. Global sliding uses one rolling state. Session-aware construction uses keyed rolling state based on precomputed session identifiers and removes completed state using precomputed session-completion positions.

Both methods use window length `k=32`, stride `s=16`, identical rolling-window logic, and identical checksum work. Sorting, loading, filtering, model inference, and session-ID derivation are outside the timed region. Each method uses one warm-up repetition and seven measured repetitions; medians are reported.

The main benchmark shows session construction is 2.17x slower than global sliding, sustains 1.06 million input flows/s, and emits approximately 50% fewer windows.

The complete-session robustness check shows session construction is 2.33x slower, sustains 1.02 million input flows/s, and emits approximately 58% fewer windows.

These results support the paper range of 1.02--1.06 million input flows/s, 2.17--2.33x runtime cost, and 50--58% fewer windows. The overhead is measurable but operationally feasible. The results do not constitute end-to-end NIDS throughput. Figure 2 inference throughput remains a separate measurement stage.

Evidence files are in `evidence/locked_sources/temporalization_streaming/`. The verification script is `scripts/verification/verify_streaming_temporalization_benchmark.py`.

## Aggregate Calculation

The paper average is the arithmetic mean of the main benchmark and complete-session robustness check: runtime ratio `2.248658778865`, session input rate `1041009.35674` flows/s, and window reduction `54.2944604953%`. These construction measurements are reported separately from inference throughput.

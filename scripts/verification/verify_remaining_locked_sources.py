#!/usr/bin/env python3
from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [
    "evidence/locked_sources/representation/representation_ablation.csv",
    "evidence/locked_sources/temporalization/temporalization_values.csv",
    "evidence/locked_sources/capacity/capacity_ablation_meanstd.csv",
    "evidence/locked_sources/head_ablation/head_ablation_meanstd.csv",
    "evidence/locked_sources/llm_comparison/shallow_vs_llm_comparison.csv",
    "evidence/locked_sources/context_length/llm_context_length_meanstd.csv",
    "evidence/locked_sources/llm_comparison/llm_pretraining_meanstd.csv",
    "evidence/locked_sources/llm_comparison/encoder_decoder_comparison.csv",
    "evidence/locked_sources/per_dataset_validation/per_dataset_validation.csv",
    "evidence/locked_sources/efficiency/efficiency_context_tradeoff.csv",
]
summary = []
for rel in SOURCES:
    path = ROOT / rel
    rows = []
    if path.exists():
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
    summary.append({"artifact_file": rel, "exists": path.exists(), "rows": len(rows)})
absent = [row for row in summary if not row["exists"]]
out = ROOT / "outputs/packaged_verification_summary.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"status": "PASS" if not absent else "ABSENT", "sources": summary}, indent=2))
print(json.dumps({"status": "PASS" if not absent else "ABSENT", "checked_files": len(summary), "absent_files": len(absent)}, indent=2))
raise SystemExit(1 if absent else 0)

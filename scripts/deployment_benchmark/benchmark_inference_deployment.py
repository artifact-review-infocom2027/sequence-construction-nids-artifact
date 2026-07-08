#!/usr/bin/env python3
from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "evidence/deployment/posthoc_deployment_full_benchmark_summary.csv"
rows = []
if CSV_PATH.exists():
    with CSV_PATH.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
print(json.dumps({"status": "summary_only", "source": str(CSV_PATH.relative_to(ROOT)), "rows": len(rows)}, indent=2))

#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "evidence/robustness_sensitivity/robustness_sensitivity_summary.csv"
CAPACITY = ROOT / "evidence/locked_sources/capacity/capacity_ablation_meanstd.csv"
HEAD = ROOT / "evidence/locked_sources/head_ablation/head_ablation_meanstd.csv"
LLM = ROOT / "evidence/locked_sources/llm_comparison/encoder_decoder_comparison.csv"
CONTEXT = ROOT / "evidence/locked_sources/context_length/llm_context_length_meanstd.csv"
TOL = 1e-5
ALLOWED_EVIDENCE_TYPES = {"repeated_seed", "window_size"}
ALLOWED_COMPONENTS = {
    "capacity_seed_variability",
    "head_ablation_seed_variability",
    "context_length_seed_variability",
    "llm_context_seed_variability",
    "window_size_sensitivity_summary",
    "supplementary_sensitivity_summary",
}
NOTE_PREFIX_BY_METRIC = {
    "present_f1": "present-label Macro-F1",
    "macro_f1": "Macro-F1",
    "all_label_macro_f1": "all-label Macro-F1",
    "accuracy": "Accuracy",
    "pr_auc": "PR-AUC",
    "throughput_flows_per_sec": "Inference throughput in flows/s",
    "throughput_windows_per_sec": "Inference throughput in windows/s",
}



def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def close(a: str, b: str, tol: float = TOL) -> bool:
    if a == "" and b == "":
        return True
    af = float(a)
    bf = float(b)
    return abs(af - bf) <= max(tol, abs(bf) * 1e-9)


def main() -> int:
    failures: list[str] = []
    summary = rows(SUMMARY)
    seen_ids: set[str] = set()
    for row in summary:
        result_id = row.get("public_result_id", "")
        if not result_id:
            failures.append("row without public_result_id")
        elif result_id in seen_ids:
            failures.append(f"duplicate public_result_id: {result_id}")
        seen_ids.add(result_id)
        if row.get("evidence_type") not in ALLOWED_EVIDENCE_TYPES:
            failures.append(f"unexpected evidence_type for {result_id}: {row.get('evidence_type')}")
        if row.get("component") not in ALLOWED_COMPONENTS:
            failures.append(f"unexpected component for {result_id}: {row.get('component')}")
        metric = row.get("metric", "")
        expected_prefix = NOTE_PREFIX_BY_METRIC.get(metric)
        if expected_prefix is None:
            failures.append(f"unexpected metric for {result_id}: {metric}")
        elif not row.get("notes", "").startswith(expected_prefix):
            failures.append(f"metric-specific note mismatch for {result_id}")

    cap = {(r["d_model"], r["n_layers"], r["n_heads"]): r for r in rows(CAPACITY)}
    head = {(r["pool"], r["causal"], r["family"]): r for r in rows(HEAD)}
    llm = {(r["throughput_max_len"], r["family"]): r for r in rows(LLM)}
    context = {r["throughput_max_len"]: r for r in rows(CONTEXT)}
    checked = 0
    metric_map = {
        "present_f1": ("macro_f1_mean", "macro_f1_std"),
        "macro_f1": ("macro_f1_mean", "macro_f1_std"),
        "all_label_macro_f1": ("macro_f1_reference_mean", "macro_f1_reference_std"),
        "accuracy": ("accuracy_mean", "accuracy_std"),
        "pr_auc": ("pr_auc_mean", "pr_auc_std"),
        "throughput_flows_per_sec": ("throughput_flows_per_sec_mean", "throughput_flows_per_sec_std"),
    }
    for row in summary:
        cond = row["condition"]
        metric = row["metric"]
        if row["source_table"] == str(SUMMARY.relative_to(ROOT)):
            continue
        source = None
        if cond.startswith("capacity "):
            m = re.search(r"d=(\d+) L=(\d+) H=(\d+)", cond)
            if m:
                source = cap.get(m.groups())
        elif cond.startswith("head "):
            m = re.search(r"head (.+) pool=([^ ]+) causal=(\d+)$", cond)
            if m:
                family, pool, causal = m.groups()
                source = head.get((pool, causal, family))
        elif cond.startswith("throughput_max_len="):
            m = re.search(r"throughput_max_len=([0-9.]+) family=(.+)$", cond)
            if m:
                source = llm.get(m.groups())
            else:
                m = re.search(r"throughput_max_len=([0-9.]+)$", cond)
                if m:
                    key = str(float(m.group(1)))
                    source = context.get(key)
        if source is None:
            failures.append(f"missing source row for {row['public_result_id']} {cond}")
            continue
        if metric not in metric_map:
            continue
        mean_col, std_col = metric_map[metric]
        if "Macro-F1" in source and metric == "macro_f1":
            mean_col, std_col = "Macro-F1", ""
        if "throughput_flows_s" in source and metric == "throughput_flows_per_sec":
            mean_col, std_col = "throughput_flows_s", ""
        if mean_col not in source and metric == "accuracy" and "accuracy" in source:
            mean_col, std_col = "accuracy", ""
        if mean_col not in source and metric == "throughput_flows_per_sec" and "flows_per_sec_mean" in source:
            mean_col, std_col = "flows_per_sec_mean", "flows_per_sec_std"
        if mean_col not in source:
            failures.append(f"missing source metric {mean_col} for {row['public_result_id']}")
            continue
        if not close(row["mean"], source[mean_col]):
            failures.append(f"mean mismatch for {row['public_result_id']}")
        if std_col and std_col in source and row["std"] and not close(row["std"], source[std_col]):
            failures.append(f"std mismatch for {row['public_result_id']}")
        if "n" in source and row["n"] != source["n"]:
            failures.append(f"n mismatch for {row['public_result_id']}")
        checked += 1
    result = {"status": "PASS" if not failures else "FAIL", "rows": len(summary), "source_checked_rows": checked, "failures": failures}
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

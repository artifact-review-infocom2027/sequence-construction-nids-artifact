#!/usr/bin/env python3
"""Verify matched-streaming temporalization evidence."""
from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVDIR = ROOT / "evidence" / "locked_sources" / "temporalization_streaming"
RAW = EVDIR / "streaming_temporalization_raw_runs.csv"
COMP = EVDIR / "streaming_temporalization_comparison.csv"
CORRECT = EVDIR / "streaming_temporalization_correctness.json"


def close(a: float, b: float, tol: float) -> bool:
    return abs(float(a) - float(b)) <= tol


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def median(rows: list[dict[str, str]], column: str) -> float:
    return float(statistics.median(float(row[column]) for row in rows))


def first_int(rows: list[dict[str, str]], column: str) -> int:
    return int(float(rows[0][column]))


def main() -> int:
    raw = read_csv(RAW)
    comp_rows = {row["benchmark_selection"]: row for row in read_csv(COMP)}
    correct = json.loads(CORRECT.read_text())
    failures: list[str] = []
    if correct.get("status") != "PASS":
        failures.append("correctness status is not PASS")
    expected = {
        "main benchmark": {
            "session_fps_range": (1.02e6, 1.06e6),
            "ratio": 2.167,
            "global_windows": 197800,
            "session_windows": 97969,
            "window_reduction_range": (50.0, 51.0),
        },
        "complete-session robustness check": {
            "session_fps_range": (1.02e6, 1.06e6),
            "ratio": 2.330,
            "global_windows": 171595,
            "session_windows": 71867,
            "window_reduction_range": (58.0, 59.0),
        },
    }
    recomputed_rows: list[dict[str, float | str]] = []
    aggregate_inputs: list[dict[str, float]] = []
    for selection, exp in expected.items():
        selection_rows = [row for row in raw if row["benchmark_selection"] == selection]
        if not selection_rows:
            failures.append(f"missing raw rows for {selection}")
            continue
        by_method = {
            method: [row for row in selection_rows if row["method"] == method]
            for method in ("global sliding", "session-aware")
        }
        if not by_method["global sliding"] or not by_method["session-aware"]:
            failures.append(f"missing method rows for {selection}")
            continue
        global_elapsed = median(by_method["global sliding"], "elapsed_sec")
        session_elapsed = median(by_method["session-aware"], "elapsed_sec")
        ratio = session_elapsed / global_elapsed
        session_fps = median(by_method["session-aware"], "input_flows_per_sec")
        global_windows = first_int(by_method["global sliding"], "emitted_windows")
        session_windows = first_int(by_method["session-aware"], "emitted_windows")
        reduction = (1.0 - session_windows / global_windows) * 100.0
        row = comp_rows.get(selection)
        if row is None:
            failures.append(f"missing comparison row for {selection}")
            continue
        if not close(float(row["session_global_runtime_ratio"]), ratio, 0.002):
            failures.append(f"runtime ratio mismatch for {selection}")
        if not close(float(row["window_reduction_percent"]), reduction, 0.002):
            failures.append(f"window reduction mismatch for {selection}")
        if not (exp["session_fps_range"][0] <= session_fps <= exp["session_fps_range"][1]):
            failures.append(f"session throughput outside paper range for {selection}")
        if not close(ratio, exp["ratio"], 0.005):
            failures.append(f"paper ratio mismatch for {selection}")
        if global_windows != exp["global_windows"] or session_windows != exp["session_windows"]:
            failures.append(f"window count mismatch for {selection}")
        if not (exp["window_reduction_range"][0] <= reduction <= exp["window_reduction_range"][1]):
            failures.append(f"window reduction outside paper range for {selection}")
        current = {
            "benchmark_selection": selection,
            "session_input_flows_per_sec": session_fps,
            "runtime_ratio": ratio,
            "window_reduction_percent": reduction,
        }
        recomputed_rows.append(current)
        aggregate_inputs.append({
            "session_input_flows_per_sec": session_fps,
            "runtime_ratio": ratio,
            "window_reduction_percent": reduction,
        })
    aggregate = {}
    if len(aggregate_inputs) == 2:
        aggregate = {
            "benchmark_selection": "average",
            "session_input_flows_per_sec": statistics.mean(r["session_input_flows_per_sec"] for r in aggregate_inputs),
            "runtime_ratio": statistics.mean(r["runtime_ratio"] for r in aggregate_inputs),
            "window_reduction_percent": statistics.mean(r["window_reduction_percent"] for r in aggregate_inputs),
        }
        row = comp_rows.get("average")
        if row is None:
            failures.append("missing comparison row for average")
        else:
            if not close(float(row["session_median_input_flows_per_sec"]), aggregate["session_input_flows_per_sec"], 0.01):
                failures.append("average session throughput mismatch")
            if not close(float(row["session_global_runtime_ratio"]), aggregate["runtime_ratio"], 1e-9):
                failures.append("average runtime ratio mismatch")
            if not close(float(row["window_reduction_percent"]), aggregate["window_reduction_percent"], 1e-9):
                failures.append("average window reduction mismatch")
            if not close(aggregate["runtime_ratio"], 2.248658778865, 1e-9):
                failures.append("paper average runtime ratio mismatch")
            if not close(aggregate["session_input_flows_per_sec"], 1041009.35674, 0.01):
                failures.append("paper average session input throughput mismatch")
            if not close(aggregate["window_reduction_percent"], 54.2944604953, 1e-9):
                failures.append("paper average window reduction mismatch")
    result = {"status": "PASS" if not failures else "FAIL", "failures": failures, "recomputed": recomputed_rows, "aggregate": aggregate}
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

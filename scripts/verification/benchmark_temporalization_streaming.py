#!/usr/bin/env python3
"""Matched streaming temporalization benchmark helper.

This script benchmarks CPU-side rolling-window construction conditioned on
precomputed session identifiers. It does not derive session IDs from raw flows
and does not run model inference.
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import time
from array import array
from collections import Counter
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

K_DEFAULT = 32
S_DEFAULT = 16


class RollingWindowState:
    __slots__ = ("row_ids", "timestamps", "count", "next_pos", "k", "s")

    def __init__(self, k: int, s: int) -> None:
        self.k = int(k)
        self.s = int(s)
        self.row_ids = array("q", [0]) * self.k
        self.timestamps = array("q", [0]) * self.k
        self.count = 0
        self.next_pos = 0

    def append(self, row_id: int, timestamp: int) -> None:
        pos = self.next_pos
        self.row_ids[pos] = int(row_id)
        self.timestamps[pos] = int(timestamp)
        self.next_pos = (pos + 1) % self.k
        self.count += 1

    def should_emit(self) -> bool:
        return self.count >= self.k and ((self.count - self.k) % self.s == 0)

    def window_edge_payload(self) -> Tuple[int, int, int, int]:
        first_pos = self.next_pos
        last_pos = (self.next_pos - 1) % self.k
        return (
            int(self.row_ids[first_pos]),
            int(self.row_ids[last_pos]),
            int(self.timestamps[first_pos]),
            int(self.timestamps[last_pos]),
        )


def checksum_update(checksum: int, first_id: int, last_id: int, length: int, first_ts: int, last_ts: int) -> int:
    mask = (1 << 64) - 1
    value = (((first_id + 0x9E3779B185EBCA87) & mask) ^ ((last_id << 17) & mask) ^ ((length << 33) & mask) ^ (first_ts & mask) ^ ((last_ts << 7) & mask))
    return ((checksum * 0x100000001B3) ^ value) & mask


def load_ordered_stream(path: Path, timestamp_col: str, row_id_col: str, dataset_col: str, session_col: str) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)
    required = [timestamp_col, row_id_col, dataset_col, session_col]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    out = pd.DataFrame({
        "timestamp": pd.to_datetime(df[timestamp_col], errors="raise").astype("int64"),
        "row_id": df[row_id_col].astype("int64"),
        "session_key": df[dataset_col].astype(str) + "::" + df[session_col].astype(str),
    })
    return out.sort_values(["timestamp", "row_id"], kind="mergesort").reset_index(drop=True)


def global_streaming(rows: pd.DataFrame, k: int, s: int) -> Dict[str, object]:
    state = RollingWindowState(k, s)
    checksum = 1469598103934665603
    emitted = 0
    was_enabled = gc.isenabled()
    gc.disable()
    t0 = time.perf_counter()
    try:
        for row_id, timestamp in zip(rows["row_id"].array, rows["timestamp"].array):
            state.append(int(row_id), int(timestamp))
            if state.should_emit():
                first_id, last_id, first_ts, last_ts = state.window_edge_payload()
                checksum = checksum_update(checksum, first_id, last_id, k, first_ts, last_ts)
                emitted += 1
    finally:
        elapsed = time.perf_counter() - t0
        if was_enabled:
            gc.enable()
    return {"method": "global sliding", "elapsed_sec": elapsed, "emitted_windows": emitted, "checksum": f"{checksum:016x}", "states_created": 1, "peak_concurrent_states": 1, "final_states": 1}


def session_streaming(rows: pd.DataFrame, k: int, s: int) -> Dict[str, object]:
    last_occurrence = {key: idx for idx, key in enumerate(rows["session_key"].array)}
    states: Dict[str, RollingWindowState] = {}
    checksum = 1469598103934665603
    emitted = 0
    states_created = 0
    peak_concurrent_states = 0
    was_enabled = gc.isenabled()
    gc.disable()
    t0 = time.perf_counter()
    try:
        for idx, (row_id, timestamp, session_key) in enumerate(zip(rows["row_id"].array, rows["timestamp"].array, rows["session_key"].array)):
            state = states.get(session_key)
            if state is None:
                state = RollingWindowState(k, s)
                states[session_key] = state
                states_created += 1
                peak_concurrent_states = max(peak_concurrent_states, len(states))
            state.append(int(row_id), int(timestamp))
            if state.should_emit():
                first_id, last_id, first_ts, last_ts = state.window_edge_payload()
                checksum = checksum_update(checksum, first_id, last_id, k, first_ts, last_ts)
                emitted += 1
            if last_occurrence[session_key] == idx:
                del states[session_key]
    finally:
        elapsed = time.perf_counter() - t0
        if was_enabled:
            gc.enable()
    return {"method": "session-aware", "elapsed_sec": elapsed, "emitted_windows": emitted, "checksum": f"{checksum:016x}", "states_created": states_created, "peak_concurrent_states": peak_concurrent_states, "final_states": len(states)}


def expected_session_windows(rows: pd.DataFrame, k: int, s: int) -> int:
    counts = Counter(rows["session_key"].array)
    return sum(max(0, math.floor((n - k) / s) + 1) for n in counts.values())


def run_benchmark(args: argparse.Namespace) -> Dict[str, object]:
    rows = load_ordered_stream(Path(args.input), args.timestamp_col, args.row_id_col, args.dataset_col, args.session_col)
    global_result = global_streaming(rows, args.k, args.s)
    session_result = session_streaming(rows, args.k, args.s)
    global_expected = max(0, math.floor((len(rows) - args.k) / args.s) + 1)
    session_expected = expected_session_windows(rows, args.k, args.s)
    checks = {
        "global_count_matches_formula": global_result["emitted_windows"] == global_expected,
        "session_count_matches_formula": session_result["emitted_windows"] == session_expected,
        "session_window_count_not_above_global": session_result["emitted_windows"] <= global_result["emitted_windows"],
        "session_states_cleaned_up": session_result["final_states"] == 0,
    }
    return {"input_rows": len(rows), "k": args.k, "s": args.s, "global": global_result, "session": session_result, "checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def self_test() -> Dict[str, object]:
    rows = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=12, freq="s"),
        "row_id": range(12),
        "dataset": ["demo"] * 12,
        "session": ["a"] * 6 + ["b"] * 6,
    })
    tmp = Path("_streaming_temporalization_self_test.csv")
    rows.to_csv(tmp, index=False)
    try:
        args = argparse.Namespace(input=str(tmp), timestamp_col="timestamp", row_id_col="row_id", dataset_col="dataset", session_col="session", k=4, s=2)
        result = run_benchmark(args)
    finally:
        tmp.unlink(missing_ok=True)
    if result["status"] != "PASS":
        raise SystemExit(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Matched streaming window-construction benchmark conditioned on precomputed session identifiers.")
    parser.add_argument("--input", help="CSV or Parquet file containing timestamp, row ID, dataset ID, and precomputed session ID columns.")
    parser.add_argument("--timestamp-col", default="timestamp")
    parser.add_argument("--row-id-col", default="row_id")
    parser.add_argument("--dataset-col", default="dataset_id")
    parser.add_argument("--session-col", default="session_id")
    parser.add_argument("--k", type=int, default=K_DEFAULT, help="Window length; default 32.")
    parser.add_argument("--s", type=int, default=S_DEFAULT, help="Stride; default 16.")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic synthetic smoke test requiring no external data.")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.input:
        parser.error("--input is required unless --self-test is used")
    print(json.dumps(run_benchmark(args), indent=2))


if __name__ == "__main__":
    main()

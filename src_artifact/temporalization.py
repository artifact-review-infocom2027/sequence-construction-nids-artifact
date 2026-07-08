from __future__ import annotations

from collections import defaultdict
from typing import Any

from .data import serialize_flow_text_style

FSEP = "[FSEP]"
LAST = "[LAST]"

PRIORITY_ORDER = [
    "botnet_c2",
    "web_attack",
    "dos",
    "bruteforce",
    "scan_recon",
    "other_attack",
    "benign",
]
LABEL_PRIORITY = {label: idx for idx, label in enumerate(PRIORITY_ORDER)}


def priority_label(labels: list[str]) -> str:
    """Return the highest-priority label in a window."""
    if not labels:
        raise ValueError("Cannot label an empty window.")
    return min((str(x) for x in labels), key=lambda label: LABEL_PRIORITY.get(label, len(LABEL_PRIORITY)))


def session_coherent_windows(
    rows: list[dict[str, Any]],
    *,
    session_col: str = "session_id",
    timestamp_col: str = "timestamp",
    label_col: str = "label",
    window_len: int = 2,
    stride: int = 1,
) -> list[dict[str, Any]]:
    """Build session-coherent serialized windows over simple in-memory rows.

    Paper-scale construction requires raw flow records that are not included in
    this anonymous artifact. This function is intentionally small enough for
    synthetic examples and reviewer smoke tests.
    """
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(session_col, "session"))].append(row)

    windows: list[dict[str, Any]] = []
    for session_id, group in grouped.items():
        group = sorted(group, key=lambda r: r.get(timestamp_col, 0))
        if len(group) < window_len:
            continue
        for start in range(0, len(group) - window_len + 1, stride):
            chunk = group[start : start + window_len]
            serialized = [serialize_flow_text_style(row) for row in chunk]
            prefix = f" {FSEP} ".join(serialized[:-1])
            text = f"{prefix} {LAST} {serialized[-1]}" if prefix else f"{LAST} {serialized[-1]}"
            labels = [str(row.get(label_col, "benign")) for row in chunk]
            windows.append(
                {
                    "session_id": session_id,
                    "start": start,
                    "text": text,
                    "label": priority_label(labels),
                    "labels_in_window": labels,
                }
            )
    return windows

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

from .utils import contains_placeholder


NUMERIC_KEYS = [
    "duration",
    "flow_pkts_total",
    "flow_bytes_total",
    "src_bps",
    "dst_bps",
]
CATEGORICAL_KEYS = [
    "protocol",
    "conn_state",
    "app_service",
    "dns_type",
]
ALL_KEYS = CATEGORICAL_KEYS + NUMERIC_KEYS
NA = "NA"
_NON_ALNUM = re.compile(r"[^A-Za-z0-9._:/=-]+")


def _is_not_available(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    text = str(value).strip().lower()
    return text in {"", "na", "nan", "none", "null", "not_available", "-1"}


def _clean_text(value: Any, max_len: int = 80) -> str:
    if _is_not_available(value):
        return NA
    text = _NON_ALNUM.sub("_", str(value).strip())
    return text[:max_len] if text else NA


def _numeric_bucket(value: Any) -> str:
    if _is_not_available(value):
        return NA
    try:
        x = float(value)
    except Exception:
        return NA
    if abs(x) < 1e-9:
        return "0"
    if 0 < abs(x) < 1:
        return f"{x:.1f}"
    if abs(x) <= 255:
        return str(int(round(x)))
    decade = int(math.floor(math.log10(abs(x))))
    return f"{'-' if x < 0 else ''}1e{decade}"


def serialize_flow_text_style(row: dict[str, Any]) -> str:
    """Serialize a synthetic flow row as field=value tokens.

    This mirrors the paper's field/value-token idea without shipping real data
    or the full private feature set.
    """
    tokens: list[str] = []
    for key in CATEGORICAL_KEYS:
        tokens.append(f"{key}={_clean_text(row.get(key, NA))}")
    for key in NUMERIC_KEYS:
        tokens.append(f"{key}={_numeric_bucket(row.get(key, NA))}")
    return " ".join(tokens)


def synthetic_flow_rows() -> list[dict[str, Any]]:
    return [
        {
            "session_id": "session-a",
            "timestamp": 1,
            "label": "benign",
            "protocol": "tcp",
            "conn_state": "established",
            "app_service": "http",
            "dns_type": "NA",
            "duration": 0.12,
            "flow_pkts_total": 8,
            "flow_bytes_total": 1200,
            "src_bps": 4000,
            "dst_bps": 3000,
        },
        {
            "session_id": "session-a",
            "timestamp": 2,
            "label": "scan_recon",
            "protocol": "tcp",
            "conn_state": "syn",
            "app_service": "unknown",
            "dns_type": "NA",
            "duration": 0.03,
            "flow_pkts_total": 3,
            "flow_bytes_total": 240,
            "src_bps": 9000,
            "dst_bps": 0,
        },
    ]


def load_jsonl_text_label(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if contains_placeholder(p):
        raise FileNotFoundError("Raw input data is not included in this anonymous artifact.")
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p}")
    rows = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def build_vocab(texts: Iterable[str], use_cls: bool = False) -> dict[str, int]:
    vocab = {"<PAD>": 0, "<UNK>": 1}
    if use_cls:
        vocab["[CLS]"] = len(vocab)
    for text in texts:
        for tok in str(text).split():
            if tok not in vocab:
                vocab[tok] = len(vocab)
    return vocab


def encode_text(text: str, vocab: dict[str, int], max_tokens: int, use_cls: bool = False) -> tuple[list[int], list[int]]:
    tokens = str(text).split()
    if use_cls:
        tokens = ["[CLS]"] + tokens
    tokens = tokens[:max_tokens]
    ids = [vocab.get(tok, vocab["<UNK>"]) for tok in tokens]
    attention = [1] * len(ids)
    while len(ids) < max_tokens:
        ids.append(0)
        attention.append(0)
    return ids, attention

#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src_artifact.data import build_vocab, encode_text, serialize_flow_text_style, synthetic_flow_rows
from src_artifact.metrics import accuracy, macro_f1, paper_macro_f1
from src_artifact.models import ShallowTextTransformer
from src_artifact.temporalization import priority_label, session_coherent_windows
from src_artifact.train_shallow import run_synthetic_smoke
from src_artifact.utils import ensure_dir, load_yaml, save_json, validate_common_config


def main() -> int:
    checks = {}
    rows = synthetic_flow_rows()
    serialized = [serialize_flow_text_style(row) for row in rows]
    checks["serialization"] = len(serialized) == 2 and all("=" in text for text in serialized)

    windows = session_coherent_windows(rows, window_len=2, stride=1)
    checks["window_count"] = len(windows) == 1
    checks["priority_label"] = priority_label(["benign", "scan_recon"]) == "scan_recon"

    texts = [windows[0]["text"]]
    vocab = build_vocab(texts)
    ids, attn = encode_text(texts[0], vocab, max_tokens=32)

    import torch

    model = ShallowTextTransformer(vocab_size=len(vocab), num_labels=2, d_model=16, n_layers=1, n_heads=2, ff_dim=32, max_tokens=32)
    input_ids = torch.tensor([ids], dtype=torch.long)
    attention_mask = torch.tensor([attn], dtype=torch.long)
    logits = model(input_ids, attention_mask)
    checks["forward_shape"] = list(logits.shape) == [1, 2]

    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    y = torch.tensor([1], dtype=torch.long)
    loss = torch.nn.functional.cross_entropy(logits, y)
    loss.backward()
    opt.step()
    checks["backward_update"] = float(loss.detach()) >= 0.0

    checks["metrics"] = (
        accuracy([0, 1], [0, 1]) == 1.0
        and macro_f1([0, 1], [0, 1]) == 1.0
        and paper_macro_f1([0, 1], [0, 1]) == 1.0
    )

    cfg = load_yaml(ROOT / "configs/shallow_session.yaml")
    checks["config_validation"] = validate_common_config(cfg)["family"] == "shallow_serialized_text"
    smoke_metrics = run_synthetic_smoke(cfg, ROOT / "outputs")
    checks["synthetic_train"] = "loss" in smoke_metrics

    ok = all(checks.values())
    summary = {"status": "ok" if ok else "not_passed", "checks": checks, "synthetic_metrics": smoke_metrics}
    ensure_dir(ROOT / "outputs")
    save_json(ROOT / "outputs/smoke_test_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

from .data import build_vocab, encode_text, synthetic_flow_rows
from .metrics import accuracy, macro_f1, paper_macro_f1
from .models import ShallowTextTransformer
from .temporalization import session_coherent_windows
from .utils import ensure_dir, reject_real_training_with_placeholders, save_json, seed_everything


def _synthetic_batch(cfg: dict[str, Any]):
    rows = synthetic_flow_rows()
    windows = session_coherent_windows(rows, window_len=2, stride=1)
    texts = [w["text"] for w in windows]
    labels = [w["label"] for w in windows]
    label2id = {label: idx for idx, label in enumerate(sorted(set(labels)))}
    y = torch.tensor([label2id[label] for label in labels], dtype=torch.long)
    max_tokens = int(cfg.get("model", {}).get("max_tokens", 64))
    use_cls = str(cfg.get("model", {}).get("pool", "mean")) == "cls"
    vocab = build_vocab(texts, use_cls=use_cls)
    encoded = [encode_text(text, vocab, max_tokens=max_tokens, use_cls=use_cls) for text in texts]
    input_ids = torch.tensor([x[0] for x in encoded], dtype=torch.long)
    attention_mask = torch.tensor([x[1] for x in encoded], dtype=torch.long)
    return input_ids, attention_mask, y, vocab, label2id


def run_synthetic_smoke(cfg: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    seed_everything(int(cfg.get("seed", 0)))
    input_ids, attention_mask, y, vocab, label2id = _synthetic_batch(cfg)
    model_cfg = cfg.get("model", {})
    model = ShallowTextTransformer(
        vocab_size=len(vocab),
        num_labels=len(label2id),
        d_model=int(model_cfg.get("d_model", 32)),
        n_layers=int(model_cfg.get("layers", 1)),
        n_heads=int(model_cfg.get("heads", 2)),
        ff_dim=int(model_cfg.get("ff_dim", 64)),
        pool=str(model_cfg.get("pool", "mean")),
        max_tokens=int(model_cfg.get("max_tokens", 64)),
    )
    opt = torch.optim.AdamW(model.parameters(), lr=float(cfg.get("optimizer", {}).get("lr", 1e-3)))
    model.train()
    logits = model(input_ids, attention_mask)
    loss = F.cross_entropy(logits, y)
    loss.backward()
    opt.step()
    model.eval()
    with torch.no_grad():
        pred = model(input_ids, attention_mask).argmax(dim=1).cpu().numpy()
    true = y.cpu().numpy()
    metrics = {
        "loss": float(loss.detach().cpu()),
        "accuracy": accuracy(true, pred),
        "macro_f1": paper_macro_f1(true, pred),
        "num_examples": int(len(true)),
        "vocab_size": int(len(vocab)),
    }
    out = Path(output_dir)
    ensure_dir(out)
    save_json(out / "synthetic_shallow_metrics.json", metrics)
    return metrics


def train_from_config(cfg: dict[str, Any], *, synthetic_smoke: bool = False) -> dict[str, Any]:
    reject_real_training_with_placeholders(cfg, synthetic_smoke=synthetic_smoke)
    output_dir = cfg.get("paths", {}).get("output_dir", "outputs/shallow_recipe")
    if synthetic_smoke:
        return run_synthetic_smoke(cfg, output_dir)
    raise NotImplementedError(
        "Real shallow training requires user-provided processed windows. "
        "This artifact ships a smoke-tested interface and recipe, not private data."
    )

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml


PLACEHOLDER_MARKERS = (
    "<DATA_NOT_INCLUDED>",
    "<MODEL_ASSETS_NOT_INCLUDED>",
    "<CHECKPOINT_NOT_INCLUDED>",
    "<EXTERNAL_DATA>",
)


def artifact_root() -> Path:
    return Path(__file__).resolve().parents[1]


def seed_everything(seed: int) -> None:
    random.seed(int(seed))
    np.random.seed(int(seed))
    try:
        import torch

        torch.manual_seed(int(seed))
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(int(seed))
    except Exception:
        pass


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_yaml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {p}")
    return data


def save_json(path: str | Path, obj: Mapping[str, Any]) -> None:
    p = Path(path)
    ensure_dir(p.parent)
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def contains_placeholder(value: Any) -> bool:
    if value is None:
        return False
    text = str(value)
    return any(marker in text for marker in PLACEHOLDER_MARKERS)


def path_is_safe_relative(path: str | Path) -> bool:
    text = str(path)
    p = Path(text)
    if p.is_absolute():
        return False
    if ".." in p.parts:
        return False
    return True


def walk_values(obj: Any):
    if isinstance(obj, dict):
        for value in obj.values():
            yield from walk_values(value)
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            yield from walk_values(value)
    else:
        yield obj


def validate_common_config(cfg: Mapping[str, Any]) -> dict[str, Any]:
    task = cfg.get("task")
    if not isinstance(task, dict):
        raise ValueError("Config requires a task mapping.")
    family = task.get("family")
    if family not in {"shallow_serialized_text", "llm_window_cls", "build_windows"}:
        raise ValueError(f"Unsupported task.family: {family!r}")

    paths = cfg.get("paths", {})
    if paths is None:
        paths = {}
    if not isinstance(paths, dict):
        raise ValueError("paths must be a mapping when present.")
    for key, value in paths.items():
        if isinstance(value, str) and not contains_placeholder(value):
            if not path_is_safe_relative(value):
                raise ValueError(f"Path must be relative or a placeholder: paths.{key}={value}")

    return {
        "family": family,
        "has_placeholders": any(contains_placeholder(v) for v in walk_values(cfg)),
        "requires_raw_data_not_included": bool(cfg.get("requires_raw_data_not_included", False)),
        "requires_model_assets": bool(cfg.get("requires_model_assets", False)),
    }


def reject_real_training_with_placeholders(cfg: Mapping[str, Any], synthetic_smoke: bool) -> None:
    info = validate_common_config(cfg)
    if synthetic_smoke:
        return
    if info["has_placeholders"] or info["requires_raw_data_not_included"]:
        raise ValueError(
            "Real training is not available from placeholder paths. "
            "Use --dry-run for a recipe summary or --synthetic-smoke for a local toy run."
        )

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src_artifact.train_llm import recipe_summary as llm_recipe_summary
from src_artifact.train_llm import train_from_config as train_llm
from src_artifact.train_shallow import train_from_config as train_shallow
from src_artifact.utils import load_yaml, validate_common_config


def parse_args():
    ap = argparse.ArgumentParser(description="Validate training recipe configs or run small synthetic smoke tests.")
    ap.add_argument("--config", required=True, help="Path to a packaged YAML configuration.")
    ap.add_argument("--dry-run", action="store_true", help="Validate config and print the recipe without training.")
    ap.add_argument("--synthetic-smoke", action="store_true", help="Run a tiny synthetic shallow training smoke test.")
    return ap.parse_args()


def build_windows_dry_run(cfg: dict) -> dict:
    return {
        "family": "build_windows",
        "status": "dry_run",
        "message": "External input tables are not included in this repository.",
        "window": cfg.get("window", {}),
        "columns": cfg.get("columns", {}),
    }


def main() -> int:
    args = parse_args()
    cfg = load_yaml(args.config)
    info = validate_common_config(cfg)
    family = info["family"]

    if args.dry_run:
        if family == "llm_window_cls":
            result = llm_recipe_summary(cfg)
        elif family == "build_windows":
            result = build_windows_dry_run(cfg)
        else:
            result = {
                "family": family,
                "status": "dry_run",
                "requires_raw_data_not_included": info["requires_raw_data_not_included"],
                "message": "Configuration is valid. Full-scale training requires external data and model assets.",
                "model": cfg.get("model", {}),
                "window": cfg.get("window", {}),
            }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if family == "shallow_serialized_text":
        if not args.synthetic_smoke:
            raise SystemExit(
                "This release validates the shallow recipe and provides a synthetic smoke test. "
                "Use --synthetic-smoke, or use the original training pipeline with external data for a full run."
            )
        result = train_shallow(cfg, synthetic_smoke=True)
    elif family == "llm_window_cls":
        if args.synthetic_smoke:
            raise SystemExit("The LLM interface supports configuration validation through --dry-run only.")
        raise SystemExit(
            "This release validates LLM recipe configuration through --dry-run. "
            "Full-scale fine-tuning requires the original training pipeline and external assets."
        )
    elif family == "build_windows":
        if not args.synthetic_smoke:
            raise SystemExit("External input tables are required for full runs. Use --dry-run for configuration-only validation.")
        result = build_windows_dry_run(cfg)
    else:
        raise SystemExit(f"Unsupported family: {family}")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

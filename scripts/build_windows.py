#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src_artifact.utils import contains_placeholder, load_yaml, validate_common_config


def parse_args():
    ap = argparse.ArgumentParser(description="Dry-run recipe for session-coherent window construction.")
    ap.add_argument("--config", default="configs/build_windows_session.yaml")
    ap.add_argument("--dry-run", action="store_true", help="Validate and print the recipe.")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    cfg = load_yaml(args.config)
    info = validate_common_config(cfg)
    if info["family"] != "build_windows":
        raise SystemExit("This script expects task.family: build_windows")
    paths = cfg.get("paths", {})
    if any(contains_placeholder(v) for v in paths.values()):
        print("Raw input data is not included in this anonymous artifact.")
    summary = {
        "status": "dry_run",
        "message": "Window construction recipe validated. No private data was read.",
        "columns": cfg.get("columns", {}),
        "window": cfg.get("window", {}),
        "label_rule": cfg.get("label_rule", "priority"),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

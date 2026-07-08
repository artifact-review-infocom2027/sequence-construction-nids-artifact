from __future__ import annotations

from typing import Any

from .models import HFWindowClassifierRecipe, HFWindowRecipe, require_transformers_available
from .utils import reject_real_training_with_placeholders


def recipe_summary(cfg: dict[str, Any]) -> dict[str, Any]:
    model = cfg.get("model", {})
    recipe = HFWindowClassifierRecipe(
        HFWindowRecipe(
            base_model=str(model.get("base_model", "")),
            head=str(model.get("head", "last_token")),
            max_len=int(model.get("max_len", 512)),
            num_labels=int(model.get("num_labels", 7)),
        )
    )
    return {
        "family": "llm_window_cls",
        "base_model": recipe.recipe.base_model,
        "head": recipe.recipe.head,
        "max_len": recipe.recipe.max_len,
        "requires": recipe.required_assets(),
        "note": "Dry run only. Real training requires external data and model assets.",
    }


def train_from_config(cfg: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    if dry_run:
        return recipe_summary(cfg)
    reject_real_training_with_placeholders(cfg, synthetic_smoke=False)
    require_transformers_available()
    raise NotImplementedError(
        "Real LLM training is a recipe in this anonymous artifact. "
        "Provide external JSONL windows and model assets before implementing a full run."
    )

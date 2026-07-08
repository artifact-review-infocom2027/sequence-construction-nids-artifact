from __future__ import annotations

import math
from dataclasses import dataclass

import torch
import torch.nn as nn


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 4096):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        pos = torch.arange(0, max_len, dtype=torch.float32).unsqueeze(1)
        div = torch.exp(torch.arange(0, d_model, 2, dtype=torch.float32) * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div[: pe[:, 1::2].shape[1]])
        self.register_buffer("pe", pe, persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[: x.size(1)].unsqueeze(0)


class AttentionPooling(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.scorer = nn.Linear(d_model, 1)

    def forward(self, h: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        scores = self.scorer(h).squeeze(-1)
        scores = scores.masked_fill(attention_mask == 0, -1e9)
        weights = torch.softmax(scores, dim=1).unsqueeze(-1)
        return (h * weights).sum(dim=1)


class ShallowTextTransformer(nn.Module):
    """Compact PyTorch model matching the paper's shallow-transformer recipe.

    This preserves the conceptual architecture used for the artifact recipes.
    It is intentionally compact for public recipe validation.
    """

    def __init__(
        self,
        *,
        vocab_size: int,
        num_labels: int,
        d_model: int = 128,
        n_layers: int = 1,
        n_heads: int = 2,
        ff_dim: int = 256,
        dropout: float = 0.1,
        pool: str = "mean",
        max_tokens: int = 512,
    ):
        super().__init__()
        self.pool = str(pool)
        self.emb = nn.Embedding(vocab_size, d_model, padding_idx=0)
        self.pos = PositionalEncoding(d_model=d_model, max_len=max_tokens + 1)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=ff_dim,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.enc = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.attn_pool = AttentionPooling(d_model) if self.pool == "attn" else None
        self.drop = nn.Dropout(dropout)
        self.head = nn.Linear(d_model, num_labels)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        x = self.pos(self.emb(input_ids))
        pad_mask = attention_mask == 0
        h = self.enc(x, src_key_padding_mask=pad_mask)
        if self.pool == "cls":
            pooled = h[:, 0, :]
        elif self.pool == "last":
            lengths = attention_mask.sum(dim=1).clamp(min=1)
            idx = (lengths - 1).view(-1, 1, 1).expand(-1, 1, h.size(-1))
            pooled = h.gather(1, idx).squeeze(1)
        elif self.pool == "attn":
            pooled = self.attn_pool(h, attention_mask)
        else:
            mask = attention_mask.unsqueeze(-1).to(h.dtype)
            pooled = (h * mask).sum(dim=1) / torch.clamp(mask.sum(dim=1), min=1.0)
        return self.head(self.drop(pooled))


@dataclass
class HFWindowRecipe:
    base_model: str
    head: str
    max_len: int
    num_labels: int


def require_transformers_available() -> None:
    try:
        import transformers  # noqa: F401
    except Exception as exc:
        raise RuntimeError(
            "The LLM training recipe requires transformers and model assets. "
            "The synthetic smoke test does not download or instantiate a Hugging Face model."
        ) from exc


class HFWindowClassifierRecipe:
    """A lightweight recipe placeholder for HF window classifiers.

    Real model construction is deliberately deferred so dry runs do not download
    model assets.
    """

    def __init__(self, recipe: HFWindowRecipe):
        self.recipe = recipe

    def required_assets(self) -> list[str]:
        return [
            f"model/tokenizer assets for {self.recipe.base_model}",
            "train/validation/test JSONL windows with text and label fields",
        ]

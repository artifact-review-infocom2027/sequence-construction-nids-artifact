# src/models/window_heads.py
from dataclasses import dataclass
from typing import Optional, Literal

import torch
import torch.nn as nn
from transformers import AutoModel, AutoModelForCausalLM, PreTrainedModel

# ---------------------------------------------------------------------
# Types & small configs
# ---------------------------------------------------------------------

HeadType = Literal["cls", "gap", "last_token", "flatten", "featurewise"]


@dataclass
class HeadConfig:
    hidden_size: int
    num_labels: int
    head_type: HeadType = "last_token"
    # For 'flatten' head
    flatten_proj: int = 512           # project token dim H -> P before flatten
    flatten_max_tokens: int = 512     # cap #tokens used by flatten (keeps dims stable)
    dropout: float = 0.1
    # [LAST] token id (if tokenizer provided it). Used by 'last_token' head.
    last_token_id: Optional[int] = None


# ---------------------------------------------------------------------
# Small MLP used by all heads
# ---------------------------------------------------------------------

class _MLP(nn.Module):
    def __init__(self, inp: int, num_labels: int, hidden: int = 0, dropout: float = 0.1):
        super().__init__()
        if hidden > 0:
            self.net = nn.Sequential(
                nn.Dropout(dropout),
                nn.Linear(inp, hidden),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(hidden, num_labels),
            )
        else:
            self.net = nn.Sequential(
                nn.Dropout(dropout),
                nn.Linear(inp, num_labels),
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# ---------------------------------------------------------------------
# Main wrapper: encoder/decoder backbone + window heads
# ---------------------------------------------------------------------

class WindowedHFClassifier(nn.Module):
    """
    Wraps a HF backbone and applies a head over the token sequence:
      - 'cls'         : take first token (CLS/first position)
      - 'gap'         : mean-pool over attention_mask
      - 'last_token'  : use position of [LAST] token if present else last non-pad
      - 'flatten'     : flatten (B, T, H) -> (B, T*P) after projecting H->P
      - 'featurewise' : time-distributed linear over tokens -> mean pool -> MLP
    """
    def __init__(self, base_model: PreTrainedModel, cfg: HeadConfig):
        super().__init__()
        self.encoder = base_model
        self.cfg = cfg

        H = cfg.hidden_size
        if cfg.head_type == "cls":
            self.head = _MLP(H, cfg.num_labels, hidden=H, dropout=cfg.dropout)
        elif cfg.head_type == "gap":
            self.head = _MLP(H, cfg.num_labels, hidden=H, dropout=cfg.dropout)
        elif cfg.head_type == "last_token":
            self.head = _MLP(H, cfg.num_labels, hidden=H, dropout=cfg.dropout)
        elif cfg.head_type == "flatten":
            self.token_proj = nn.Linear(H, cfg.flatten_proj)
            self.head = _MLP(
                cfg.flatten_proj * cfg.flatten_max_tokens,
                cfg.num_labels,
                hidden=cfg.flatten_proj,
                dropout=cfg.dropout,
            )
        elif cfg.head_type == "featurewise":
            self.time_linear = nn.Linear(H, H)
            self.head = _MLP(H, cfg.num_labels, hidden=H, dropout=cfg.dropout)
        else:
            raise ValueError(f"Unknown head_type: {cfg.head_type}")

    def _get_last_positions(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """
        For 'last_token': find index of [LAST] if available; otherwise last non-pad.
        Returns tensor (B,) of positions.
        """
        B, T = input_ids.size()
        device = input_ids.device

        if self.cfg.last_token_id is not None:
            is_last = (input_ids == self.cfg.last_token_id)           # (B,T) bool
            any_last = is_last.any(dim=1)                              # (B,)
            last_valid = attention_mask.sum(dim=1) - 1                 # (B,)

            # CUDA-safe: cast to int64 before argmax
            rev = is_last.flip(dims=[1]).to(torch.int64)
            rev_idx = torch.argmax(rev, dim=1)                         # index from the end
            last_pos = (T - 1) - rev_idx                                # convert to forward index

            # where there is no [LAST], fall back to last valid token
            last_pos = torch.where(any_last, last_pos, last_valid)
            return last_pos.to(device)

        return (attention_mask.sum(dim=1) - 1).to(device)

    def forward(self, input_ids=None, attention_mask=None, labels=None, **kwargs):
        # ---- sanitize trainer-specific kwargs (ModernBERT, etc.) ----
        kwargs.pop("num_items_in_batch", None)
        kwargs.pop("return_loss", None)
        # Some models don't accept this; we only rely on attention_mask anyway.
        kwargs.pop("position_ids", None)

        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask, **kwargs)
        last_hidden = outputs.last_hidden_state  # (B, T, H)
        B, T, H = last_hidden.shape

        if self.cfg.head_type == "cls":
            pooled = last_hidden[:, 0]
            logits = self.head(pooled)

        elif self.cfg.head_type == "gap":
            mask = attention_mask.unsqueeze(-1)              # (B, T, 1)
            summed = (last_hidden * mask).sum(dim=1)
            denom = mask.sum(dim=1).clamp(min=1)
            pooled = summed / denom
            logits = self.head(pooled)

        elif self.cfg.head_type == "last_token":
            pos = self._get_last_positions(input_ids, attention_mask)    # (B,)
            idx = pos.view(B, 1, 1).expand(-1, 1, H)                      # (B,1,H)
            gathered = last_hidden.gather(dim=1, index=idx).squeeze(1)   # (B,H)
            logits = self.head(gathered)

        elif self.cfg.head_type == "flatten":
            max_tokens = min(T, self.cfg.flatten_max_tokens)
            x = last_hidden[:, :max_tokens, :]                # (B, max_tokens, H)
            x = self.token_proj(x)                            # (B, max_tokens, P)
            x = x.reshape(B, -1)                              # (B, max_tokens*P)
            # right-pad with zeros to fixed (flatten_max_tokens * flatten_proj)
            want = self.cfg.flatten_max_tokens * self.cfg.flatten_proj
            if x.size(1) < want:
                x = torch.cat([x, x.new_zeros(B, want - x.size(1))], dim=1)
            logits = self.head(x)

        elif self.cfg.head_type == "featurewise":
            proj = self.time_linear(last_hidden)              # (B, T, H)
            mask = attention_mask.unsqueeze(-1)
            pooled = (proj * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
            logits = self.head(pooled)

        else:
            raise RuntimeError("unreachable")

        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, self.cfg.num_labels), labels.view(-1))

        return {"loss": loss, "logits": logits}


# ---------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------

def _load_backbone(base_model_id: str, config=None, trust_remote_code: bool = False) -> PreTrainedModel:
    """
    Prefer an encoder backbone (AutoModel). If that fails (pure decoder LMs),
    fall back to AutoModelForCausalLM but still use last_hidden_state.
    """
    try:
        return AutoModel.from_pretrained(base_model_id, config=config, trust_remote_code=trust_remote_code)
    except Exception:
        # e.g., Qwen-only checkpoints
        return AutoModelForCausalLM.from_pretrained(base_model_id, config=config, trust_remote_code=trust_remote_code)


def build_model(
    base_model_id: str,
    num_labels: int,
    head_type: HeadType,
    tokenizer,
    config=None,
    trust_remote_code: bool = False,
    dropout: float = 0.1,
) -> WindowedHFClassifier:
    """
    Build backbone + classification head. Also resizes embeddings to include any
    newly added special tokens (e.g., [FSEP], [LAST]).
    """
    base = _load_backbone(base_model_id, config=config, trust_remote_code=trust_remote_code)

    # Resize token embeddings if tokenizer has new special tokens
    try:
        base.resize_token_embeddings(len(tokenizer))
    except Exception:
        # Some models (rare) may not expose resize; safe to ignore.
        pass

    hidden_size = getattr(base.config, "hidden_size", None)
    if hidden_size is None:
        hidden_size = getattr(base.config, "d_model", None)
    if hidden_size is None:
        raise ValueError("Cannot determine hidden size from backbone config.")

    # [LAST] token id if present
    try:
        last_id = tokenizer.convert_tokens_to_ids("[LAST]")
        if last_id is None or last_id == tokenizer.unk_token_id:
            last_id = None
    except Exception:
        last_id = None

    cfg = HeadConfig(
        hidden_size=hidden_size,
        num_labels=num_labels,
        head_type=head_type,
        dropout=dropout,
        last_token_id=last_id,
    )

    return WindowedHFClassifier(base, cfg)

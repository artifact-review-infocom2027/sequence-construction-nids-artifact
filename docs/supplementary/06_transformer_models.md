# Transformer Models

The paper compares shallow transformer models with pretrained encoder and
decoder language-model baselines. Parameter counts are reported as trainable or
model-family counts according to the evidence used by each comparison.

| Model Family | Architecture | Pretraining | Parameters | Role |
| --- | --- | --- | ---: | --- |
| Shallow Transformer | Encoder/Decoder | None | 0.20M--3.38M | Primary model |
| ModernBERT | Encoder | General | 149M | Long-context encoder |
| DeBERTa-v3 | Encoder | General | 183M | Encoder baseline |
| CTI-BERT | Encoder | Domain | 110M | Security-specific encoder |
| ModernBERT-DAPT | Encoder | Domain | 149M | Domain-adapted encoder |
| Qwen-0.5B | Decoder | General | 494M | Decoder LLM |

The shallow capacity sweep spans 0.20M--3.38M trainable parameters. The strongest
shallow operating point is `(d,L,H)=(64,4,2)` with 0.65M parameters, Macro-F1
0.947, PR-AUC 0.958, Accuracy 0.996, and 0.40M flows/s. The largest evaluated
shallow configuration is `(256,4,8)` with 3.38M parameters, Macro-F1 0.934,
PR-AUC 0.936, Accuracy 0.995, and 0.13M flows/s.

Relative to the 0.65M-parameter strongest shallow operating point, the
pretrained model range of 110M--494M parameters is 169x--759x larger.

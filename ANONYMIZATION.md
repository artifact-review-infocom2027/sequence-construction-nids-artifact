# Anonymization

This repository uses paper terminology, anonymous run identifiers, and repository-relative evidence paths. It excludes private datasets, checkpoints, tokenizer payloads, full run folders, account-specific logs, and local machine paths.

Selected metadata files are retained only when they support result inspection and contain no local paths or restricted payloads. Checksums and a run index are provided under `manifest/`.

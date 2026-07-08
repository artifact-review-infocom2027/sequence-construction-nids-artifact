# Anonymization

The staged artifact uses public paper terminology, public run identifiers, and repository-local evidence paths. It excludes private datasets, checkpoints, tokenizer payloads, full run folders, account-specific logs, and local machine paths.

Selected metadata files are retained only when they support paper-result inspection and contain no private paths or payloads. Checksums and a public run index are provided under `manifest/`.

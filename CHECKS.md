# Checks

The repository contains the files listed in `manifest/artifact_manifest.csv`. Verification and dry-run commands must pass, all mapped paths must resolve, and the checksum policy must validate before release.

Paper figures are stored in `figures/paper/` and are limited to Figures 1--8. Supplementary ablation figures are stored in `figures/supplementary/`. Feature, schema, and label harmonization files are stored in `docs/`.

A concise record of the release checks is stored in `outputs/verification_command_results.csv`.

## Checksum Policy

`manifest/checksums_sha256.txt` contains SHA-256 hashes for every intended tracked artifact file except `manifest/checksums_sha256.txt` itself. The checksum file is self-excluded because its final contents cannot contain a stable hash of itself.

`manifest/artifact_manifest.csv` lists every intended tracked artifact file. Its `sha256` and `size_bytes` fields are intentionally blank for `manifest/artifact_manifest.csv` and `manifest/checksums_sha256.txt`: the manifest avoids hashing itself, and it avoids a checksum-file hash that would create a recursive dependency. `scripts/verification/verify_manifest_integrity.py` enforces this documented acyclic policy.

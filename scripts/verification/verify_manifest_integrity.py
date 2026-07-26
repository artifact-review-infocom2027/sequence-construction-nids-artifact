#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import csv
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CHECKSUMS = ROOT / "manifest/checksums_sha256.txt"
MANIFEST = ROOT / "manifest/artifact_manifest.csv"
DOCUMENTED_SHA_EXCLUSIONS = {
    "manifest/artifact_manifest.csv": "manifest file excludes its own SHA in artifact_manifest.csv; it is hashed by checksums_sha256.txt",
    "manifest/checksums_sha256.txt": "checksum file excludes itself from checksums_sha256.txt and from artifact_manifest.csv to avoid recursive hashing",
}


def repo_files() -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    files = []
    for line in proc.stdout.splitlines():
        rel = line.strip()
        if not rel:
            continue
        if (ROOT / rel).is_file():
            files.append(rel)
    return sorted(files)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_checksums() -> dict[str, str]:
    out = {}
    with CHECKSUMS.open() as handle:
        for lineno, line in enumerate(handle, start=1):
            line = line.rstrip("\n")
            if not line:
                continue
            digest, rel = line.split("  ", 1)
            out[rel] = digest
    return out


def read_manifest() -> dict[str, dict[str, str]]:
    with MANIFEST.open(newline="") as handle:
        return {row["artifact_path"]: row for row in csv.DictReader(handle)}


def main() -> int:
    files = repo_files()
    failures = []
    manifest = read_manifest()
    checksums = read_checksums()

    expected_checksum_files = [f for f in files if f != "manifest/checksums_sha256.txt"]
    if set(checksums) != set(expected_checksum_files):
        failures.append({
            "check": "checksum_scope",
            "missing": sorted(set(expected_checksum_files) - set(checksums)),
            "unexpected": sorted(set(checksums) - set(expected_checksum_files)),
        })
    for rel, expected in checksums.items():
        actual = sha256(ROOT / rel)
        if actual != expected:
            failures.append({"check": "checksum_hash", "path": rel, "expected": expected, "actual": actual})

    if set(manifest) != set(files):
        failures.append({
            "check": "manifest_scope",
            "missing": sorted(set(files) - set(manifest)),
            "unexpected": sorted(set(manifest) - set(files)),
        })
    for rel, row in manifest.items():
        row_hash = row.get("sha256", "")
        if rel in DOCUMENTED_SHA_EXCLUSIONS:
            if row_hash:
                failures.append({"check": "manifest_documented_exclusion", "path": rel, "issue": "sha256 should be empty"})
            continue
        if not row_hash:
            failures.append({"check": "manifest_hash_present", "path": rel})
        elif row_hash != sha256(ROOT / rel):
            failures.append({"check": "manifest_hash", "path": rel, "expected": row_hash, "actual": sha256(ROOT / rel)})

    result = {
        "status": "PASS" if not failures else "FAIL",
        "file_count": len(files),
        "checksum_entries": len(checksums),
        "manifest_entries": len(manifest),
        "documented_sha_exclusions": DOCUMENTED_SHA_EXCLUSIONS,
        "failures": failures,
    }
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

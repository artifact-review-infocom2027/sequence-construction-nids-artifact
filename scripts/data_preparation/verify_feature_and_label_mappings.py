#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OUTPUTS = ROOT / "outputs"
PUBLIC_LABELS = {"benign", "botnet_c2", "bruteforce", "dos", "other_attack", "scan_recon", "web_attack"}
REQUIRED_FEATURE_COLUMNS = ["feature", "type", "source", "role", "model_input", "description"]
REQUIRED_SOURCE_COLUMNS = ["source_dataset", "native_field_or_pattern", "canonical_feature", "transform", "availability", "model_input", "notes"]
REQUIRED_LABEL_SCOPES = {"UNSW", "CICIDS", "MQCIDS", "any"}
FORBIDDEN_TERMS = ["Suri" + "cata", "suri" + "cata"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def public_text_files() -> list[Path]:
    suffixes = {".md", ".csv", ".yaml", ".yml", ".json", ".py", ".txt"}
    return [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in suffixes and ".git" not in p.parts]


def forbidden_string_hits() -> list[str]:
    hits = []
    for path in public_text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for term in FORBIDDEN_TERMS:
            if term in text:
                hits.append(path.relative_to(ROOT).as_posix())
                break
    return sorted(set(hits))


def main() -> int:
    feature_path = DOCS / "feature_specification.csv"
    source_path = DOCS / "source_feature_mapping.csv"
    label_path = DOCS / "label_harmonization.csv"
    excluded_path = DOCS / "excluded_identifier_fields.csv"

    features = read_csv(feature_path)
    source_rows = read_csv(source_path)
    labels = read_csv(label_path)
    excluded = read_csv(excluded_path)

    feature_names = {row["feature"] for row in features}
    source_features = {row["canonical_feature"] for row in source_rows}
    label_set = {row["harmonized_label"] for row in labels}
    label_scopes = {row["source_dataset"] for row in labels}
    source_scopes = {row["source_dataset"] for row in source_rows}
    excluded_names = {row["field_pattern"].lower() for row in excluded}
    identifier_inputs = [row["feature"] for row in features if row.get("model_input", "").lower() == "true" and row["feature"].lower() in excluded_names]
    symm_rows = [row for row in features if row["feature"] == "symm_ips_ports"]
    bad_rate_count_rows = [row for row in source_rows if row["source_dataset"] == "CICIDS2018" and row["native_field_or_pattern"] in {"Fwd Pkts/s", "Bwd Pkts/s", "Flow Pkts/s"} and row["canonical_feature"] in {"src_pkts", "dst_pkts"}]
    pkt_len_rows = [row for row in source_rows if row["source_dataset"] == "CICIDS2018" and row["native_field_or_pattern"] == "Pkt Len Mean"]
    competing_direct_rows = [row for row in source_rows if row["source_dataset"] == "CICIDS2018" and row["native_field_or_pattern"] == "Pkt Len Mean" and "fallback" not in (row["transform"] + " " + row["notes"]).lower()]
    alias_rows_without_coalesce_note = [row for row in source_rows if row["source_dataset"] == "MQCIDS" and " / " in row["native_field_or_pattern"] and row["canonical_feature"] in {"app_service", "http_host", "http_url", "http_ua", "tls_ja3", "tls_ja3s", "tls_sni", "dns_name", "dns_type", "ssh_client_ver", "ssh_server_ver", "conn_state"} and "coalesc" not in row["notes"].lower()]
    forbidden_hits = forbidden_string_hits()

    self_test = subprocess.run([sys.executable, str(ROOT / "scripts/data_preparation/harmonize_schema.py"), "--self-test"], cwd=ROOT, text=True, capture_output=True)
    self_json = {}
    self_path = OUTPUTS / "harmonize_schema_self_test.json"
    if self_path.exists():
        self_json = json.loads(self_path.read_text(encoding="utf-8"))
    self_checks = self_json.get("checks", {})

    checks = {
        "feature_rows": len(features),
        "feature_row_count_ok": len(features) == 47,
        "feature_columns_ok": all(col in features[0] for col in REQUIRED_FEATURE_COLUMNS) if features else False,
        "source_feature_mapping_present": source_path.exists(),
        "source_mapping_columns_ok": all(col in source_rows[0] for col in REQUIRED_SOURCE_COLUMNS) if source_rows else False,
        "all_features_have_source_mapping": feature_names.issubset(source_features),
        "source_mapping_has_mqcids_rows": "MQCIDS" in source_scopes,
        "source_mapping_scope_clean": all(scope in {"CICIDS2018", "UNSW-NB15", "MQCIDS", "all"} for scope in source_scopes),
        "cicids_packet_counts_use_count_columns": not bad_rate_count_rows,
        "pkt_len_mean_marked_fallback": bool(pkt_len_rows) and not competing_direct_rows,
        "mqcids_alias_rows_note_coalescing": not alias_rows_without_coalesce_note,
        "public_scope_strings_clean": not forbidden_hits,
        "excluded_identifier_fields_present": bool(excluded),
        "identifier_model_inputs": identifier_inputs,
        "public_labels_present": PUBLIC_LABELS.issubset(label_set),
        "label_scopes_present": REQUIRED_LABEL_SCOPES.issubset(label_scopes),
        "label_scopes_clean": label_scopes.issubset({"public", "UNSW", "CICIDS", "MQCIDS", "any"}),
        "symm_ips_ports_model_input_false": bool(symm_rows) and symm_rows[0].get("model_input", "").lower() == "false",
        "harmonization_self_test_passed": self_test.returncode == 0,
        "self_test_duplicate_columns_absent": self_checks.get("duplicate_columns_absent") is True,
        "self_test_cicids_directional_pkt_mean_preferred": self_checks.get("cicids_directional_pkt_mean_preferred") is True,
        "self_test_unsw_attack_cat_preferred": self_checks.get("unsw_attack_cat_preferred") is True,
        "self_test_mqcids_service_coalesced": self_checks.get("mqcids_service_coalesced") is True,
    }
    ok = all(v is True for k, v in checks.items() if k not in {"feature_rows", "identifier_model_inputs"}) and not identifier_inputs
    result = {"status": "PASS" if ok else "CHECK", "checks": checks, "self_test_stdout": self_test.stdout.strip()}
    OUTPUTS.mkdir(exist_ok=True)
    (OUTPUTS / "feature_mapping_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

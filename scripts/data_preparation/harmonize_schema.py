#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OUTPUTS = ROOT / "outputs"
NUMERIC_SENTINEL = 0.0
CATEGORICAL_SENTINEL = "<MISSING>"

PUBLIC_LABELS = {"benign", "botnet_c2", "bruteforce", "dos", "other_attack", "scan_recon", "web_attack"}
CICIDS_PREFIXES = ["dos attacks-", "ddos attack-", "web attack -", "web attack-"]

STAGING_CANDIDATES = {
    "timestamp": ["timestamp", "Timestamp", "stime", "Stime", "flow.start"],
    "duration": ["duration", "Flow Duration", "dur"],
    "protocol": ["protocol", "Protocol", "proto"],
    "src_ip": ["src_ip", "Src IP", "srcip", "source_ip", "source ip"],
    "dst_ip": ["dst_ip", "Dst IP", "dstip", "dest_ip", "dest ip", "destination_ip", "destination ip"],
    "src_port": ["src_port", "Src Port", "sport", "source_port", "source port"],
    "dst_port": ["dst_port", "Dst Port", "dsport", "dport", "dest_port", "dest port", "destination_port", "destination port"],
    "fwd_pkts": ["fwd_pkts", "Tot Fwd Pkts", "spkts", "Spkts", "flow.pkts_toserver", "pkts_toserver", "pkts toserver"],
    "bwd_pkts": ["bwd_pkts", "Tot Bwd Pkts", "dpkts", "Dpkts", "flow.pkts_toclient", "pkts_toclient", "pkts toclient"],
    "fwd_bytes": ["fwd_bytes", "TotLen Fwd Pkts", "sbytes", "Sbytes", "flow.bytes_toserver", "bytes_toserver", "bytes toserver"],
    "bwd_bytes": ["bwd_bytes", "TotLen Bwd Pkts", "dbytes", "Dbytes", "flow.bytes_toclient", "bytes_toclient", "bytes toclient"],
}

DIRECT_CANDIDATES = {
    "src_ttl": ["src_ttl", "sttl"],
    "dst_ttl": ["dst_ttl", "dttl"],
    "src_loss": ["src_loss", "sloss"],
    "dst_loss": ["dst_loss", "dloss"],
    "src_bps": ["src_bps", "sload"],
    "dst_bps": ["dst_bps", "dload"],
    "src_pkts": ["src_pkts"],
    "dst_pkts": ["dst_pkts"],
    "src_win": ["src_win", "swin"],
    "dst_win": ["dst_win", "dwin"],
    "src_tcp_bytes": ["src_tcp_bytes", "stcpb"],
    "dst_tcp_bytes": ["dst_tcp_bytes", "dtcpb"],
    "src_pkt_mean": ["src_pkt_mean", "Fwd Pkt Len Mean", "smean", "Pkt Len Mean"],
    "dst_pkt_mean": ["dst_pkt_mean", "Bwd Pkt Len Mean", "dmean", "Pkt Len Mean"],
    "tcp_trans_depth": ["tcp_trans_depth", "trans_depth", "trans depth", "Active Mean"],
    "tcp_resp_bytes": ["tcp_resp_bytes", "response_body_len", "response body len", "Active Std"],
    "src_jitter": ["src_jitter", "sjit", "Idle Mean"],
    "dst_jitter": ["dst_jitter", "djit", "Idle Std"],
    "src_intpkt": ["src_intpkt", "sintpkt", "Flow IAT Mean"],
    "dst_intpkt": ["dst_intpkt", "dintpkt", "Flow IAT Std"],
    "tcp_rtt": ["tcp_rtt", "tcprtt"],
    "tcp_synack_time": ["tcp_synack_time", "synack"],
    "tcp_ack_time": ["tcp_ack_time", "ackdat"],
    "count_same_state_ttl": ["count_same_state_ttl", "ct_state_ttl", "ct state ttl"],
    "count_http_methods": ["count_http_methods", "ct_flw_http_mthd", "ct flw http mthd"],
    "conn_state": ["conn_state", "flow.state", "flow_state", "state"],
    "app_service": ["app_service", "app_proto", "service"],
    "http_host": ["http_host", "http.hostname", "http.host"],
    "http_url": ["http_url", "http.url", "http.uri"],
    "http_ua": ["http_ua", "http.http_user_agent", "http_user_agent", "http user agent"],
    "tls_ja3": ["tls_ja3", "tls.ja3.hash"],
    "tls_ja3s": ["tls_ja3s", "tls.ja3s.hash"],
    "tls_sni": ["tls_sni", "tls.sni"],
    "dns_name": ["dns_name", "dns.rrname", "dns.query"],
    "dns_type": ["dns_type", "dns.rrtype", "dns.type"],
    "ssh_client_ver": ["ssh_client_ver", "ssh.client.software"],
    "ssh_server_ver": ["ssh_server_ver", "ssh.server.software"],
}

LABEL_CANDIDATES = {
    "attack_cat": ["attack_cat", "attack cat"],
    "label_binary_or_native": ["Label", "label"],
    "mqcids_label": ["label", "tier2_label_final", "tier2_label", "fine_label", "fine label"],
}


def normalize_name(value: object) -> str:
    text = "" if value is None else str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_label(value: object) -> str:
    text = "" if value is None else str(value).strip().lower()
    for prefix in CICIDS_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix):]
    return re.sub(r"\s+", " ", text.replace("_", " ").replace("-", " ")).strip()


def make_unique_columns(columns: Iterable[object]) -> list[str]:
    seen: dict[str, int] = {}
    result = []
    for col in columns:
        name = str(col).strip()
        count = seen.get(name, 0)
        result.append(name if count == 0 else f"{name}__dup{count}")
        seen[name] = count + 1
    return result


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_feature_spec() -> pd.DataFrame:
    return pd.read_csv(DOCS / "feature_specification.csv")


def load_source_mapping() -> list[dict[str, str]]:
    path = DOCS / "source_feature_mapping.csv"
    return read_csv_rows(path) if path.exists() else []


def load_label_rules() -> list[dict[str, str]]:
    return read_csv_rows(DOCS / "label_harmonization.csv")


def load_excluded_aliases() -> set[str]:
    aliases = set()
    for row in read_csv_rows(DOCS / "excluded_identifier_fields.csv"):
        aliases.add(normalize_name(row["field_pattern"]))
    aliases.update(normalize_name(x) for x in [
        "src_ip", "dst_ip", "source_ip", "destination_ip", "dest_ip",
        "src_port", "dst_port", "source_port", "destination_port", "sport", "dport", "dest_port",
        "flow_id", "uid", "timestamp", "raw_time", "dataset_id", "split",
    ])
    return aliases


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError("input must be CSV or Parquet")


def column_lookup(df: pd.DataFrame) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for col in df.columns:
        lookup.setdefault(normalize_name(col), []).append(col)
    return lookup


def first_existing_series(df: pd.DataFrame, candidates: Iterable[str]) -> pd.Series | None:
    lookup = column_lookup(df)
    result: pd.Series | None = None
    for candidate in candidates:
        for col in lookup.get(normalize_name(candidate), []):
            series = df[col]
            if isinstance(series, pd.DataFrame):
                series = series.iloc[:, 0]
            series = series.copy()
            non_empty = series.notna() & (series.astype(str).str.strip() != "")
            if result is None:
                result = series
            else:
                result = result.where(result.notna() & (result.astype(str).str.strip() != ""), series)
            if bool(non_empty.all()):
                return result
    return result


def coalesce_to_canonical(df: pd.DataFrame, canonical: str, candidates: Iterable[str]) -> None:
    series = first_existing_series(df, [canonical, *list(candidates)])
    if series is not None:
        df[canonical] = series


def detect_source_dataset(df: pd.DataFrame, requested: str) -> str:
    if requested.lower() != "auto":
        return requested
    cols = set(column_lookup(df).keys())
    if {"flow duration", "tot fwd pkts", "tot bwd pkts"} & cols:
        return "CICIDS"
    if {"srcip", "sport", "attack cat", "stime"} & cols:
        return "UNSW"
    if {"app proto", "app service", "pkts toserver", "bytes toserver"} & cols:
        return "MQCIDS"
    return "public"


def safe_output_path(path: Path) -> Path:
    resolved = path.resolve()
    output_root = OUTPUTS.resolve()
    if output_root not in resolved.parents and resolved != output_root:
        raise ValueError("output must be under outputs")
    return resolved


def numeric_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([NUMERIC_SENTINEL] * len(df), index=df.index, dtype="float64")
    series = df[col]
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    return pd.to_numeric(series, errors="coerce").fillna(NUMERIC_SENTINEL)


def prepare_base_frame(raw: pd.DataFrame, source_dataset: str) -> tuple[pd.DataFrame, str]:
    df = raw.copy()
    df.columns = make_unique_columns(df.columns)
    source = detect_source_dataset(df, source_dataset)

    for canonical, candidates in STAGING_CANDIDATES.items():
        coalesce_to_canonical(df, canonical, candidates)
    for canonical, candidates in DIRECT_CANDIDATES.items():
        coalesce_to_canonical(df, canonical, candidates)

    for canonical, candidates in LABEL_CANDIDATES.items():
        coalesce_to_canonical(df, canonical, candidates)

    if "timestamp" in df.columns:
        ts = df["timestamp"]
        df = df[ts.astype(str).str.strip().str.lower() != "timestamp"].copy()
        parsed = pd.to_datetime(df["timestamp"], errors="coerce", dayfirst=True)
        fallback = pd.to_datetime(pd.to_numeric(df["timestamp"], errors="coerce"), unit="s", errors="coerce")
        df["timestamp"] = parsed.fillna(fallback)
        if source.lower().startswith("cicids"):
            df = df[df["timestamp"].isna() | (df["timestamp"] >= pd.Timestamp("2018-01-01"))].copy()

    if source.lower().startswith("cicids") and "duration" in df.columns:
        df["duration"] = pd.to_numeric(df["duration"], errors="coerce").clip(lower=0) / 1_000_000.0

    if not df.columns.is_unique:
        duplicates = sorted({c for c in df.columns if list(df.columns).count(c) > 1})
        raise ValueError(f"Duplicate canonical columns after coalescing: {duplicates}")
    return df, source


def compute_derived(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    fwd_pkts = numeric_series(df, "fwd_pkts")
    bwd_pkts = numeric_series(df, "bwd_pkts")
    fwd_bytes = numeric_series(df, "fwd_bytes")
    bwd_bytes = numeric_series(df, "bwd_bytes")
    duration = numeric_series(df, "duration")

    if "flow_pkts_total" not in df.columns:
        df["flow_pkts_total"] = fwd_pkts + bwd_pkts
    if "flow_bytes_total" not in df.columns:
        df["flow_bytes_total"] = fwd_bytes + bwd_bytes
    if "src_pkts" not in df.columns:
        df["src_pkts"] = fwd_pkts
    if "dst_pkts" not in df.columns:
        df["dst_pkts"] = bwd_pkts
    if "src_tcp_bytes" not in df.columns:
        df["src_tcp_bytes"] = fwd_bytes
    if "dst_tcp_bytes" not in df.columns:
        df["dst_tcp_bytes"] = bwd_bytes
    if "src_bps" not in df.columns:
        df["src_bps"] = fwd_bytes / (duration + 1e-6)
    if "dst_bps" not in df.columns:
        df["dst_bps"] = bwd_bytes / (duration + 1e-6)
    if "burst_rate" not in df.columns:
        df["burst_rate"] = pd.to_numeric(df["flow_pkts_total"], errors="coerce").fillna(0.0) / (duration + 1e-6)
    if "bdr" not in df.columns:
        upper = pd.concat([fwd_bytes, bwd_bytes], axis=1).max(axis=1)
        lower = pd.concat([fwd_bytes, bwd_bytes], axis=1).min(axis=1)
        df["bdr"] = upper / (lower + 1e-6)
    if "port_rarity" not in df.columns:
        if "dst_port" in df.columns:
            counts = df["dst_port"].astype(str).map(df["dst_port"].astype(str).value_counts())
            df["port_rarity"] = 1.0 / counts.replace(0, pd.NA).astype(float)
        else:
            df["port_rarity"] = NUMERIC_SENTINEL
    if "temporal_persistence" not in df.columns:
        key_cols = [c for c in ["src_ip", "dst_ip", "src_port", "dst_port", "protocol"] if c in df.columns]
        if "timestamp" in df.columns and key_cols:
            tmp = df[["timestamp", *key_cols]].copy()
            tmp["_idx"] = range(len(tmp))
            tmp = tmp.sort_values(key_cols + ["timestamp"])
            tmp["_delta"] = tmp.groupby(key_cols)["timestamp"].diff().dt.total_seconds().fillna(0.0)
            df["temporal_persistence"] = tmp.sort_values("_idx")["_delta"].to_numpy()
        else:
            df["temporal_persistence"] = NUMERIC_SENTINEL
    if "entropy_bucket" not in df.columns:
        df["entropy_bucket"] = CATEGORICAL_SENTINEL

    if not df.columns.is_unique:
        duplicates = sorted({c for c in df.columns if list(df.columns).count(c) > 1})
        raise ValueError(f"Duplicate canonical columns after derived feature construction: {duplicates}")
    return df


def choose_label_values(raw: pd.DataFrame, mapped: pd.DataFrame, source: str, label_column: str | None) -> pd.Series | None:
    if label_column:
        series = first_existing_series(raw, [label_column])
        if series is not None:
            return series
        if label_column in mapped.columns:
            return mapped[label_column]
    if source.lower().startswith("unsw"):
        series = first_existing_series(mapped, ["attack_cat"])
        if series is not None:
            return series
        return first_existing_series(mapped, ["label_binary_or_native", "label"])
    if source.lower().startswith("mqcids"):
        return first_existing_series(mapped, ["mqcids_label", "label", "tier2_label_final", "fine_label", "fine label"])
    return first_existing_series(mapped, ["label_binary_or_native", "label", "Label"])


def drop_identifier_columns(df: pd.DataFrame) -> pd.DataFrame:
    aliases = load_excluded_aliases()
    drop = [col for col in df.columns if normalize_name(col) in aliases]
    return df.drop(columns=drop, errors="ignore")


def select_model_features(df: pd.DataFrame, spec: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for _, row in spec.iterrows():
        if str(row["model_input"]).lower() != "true":
            continue
        feature = row["feature"]
        if feature in df.columns:
            out[feature] = df[feature]
        elif row["type"] == "numeric":
            out[feature] = NUMERIC_SENTINEL
        else:
            out[feature] = CATEGORICAL_SENTINEL
    return out


def label_rule_order(rules: Iterable[dict[str, str]], source_dataset: str) -> list[dict[str, str]]:
    source = source_dataset.lower()
    scoped = []
    fallback = []
    final = []
    for rule in rules:
        ds = rule["source_dataset"].lower()
        if rule["rule_type"] == "final_label_space":
            final.append(rule)
        elif ds in {source, "any"}:
            scoped.append(rule)
        elif ds == "public":
            final.append(rule)
        elif rule["rule_type"] == "fallback_rule":
            fallback.append(rule)
    return scoped + final + fallback


def map_one_label(value: object, rules: list[dict[str, str]], source_dataset: str) -> str:
    text = normalize_label(value)
    compact = text.replace(" ", "_")
    if compact in PUBLIC_LABELS:
        return compact
    for rule in label_rule_order(rules, source_dataset):
        if rule["rule_type"] == "fallback_rule":
            continue
        pattern = rule["native_label_or_pattern"].lower().replace("_", " ")
        if re.search(pattern, text):
            return rule["harmonized_label"]
    if text and text not in {"benign", "normal", "nan", "none"}:
        return "other_attack"
    return "benign"


def harmonize_frame(df: pd.DataFrame, source_dataset: str, label_column: str | None) -> pd.DataFrame:
    raw = df.copy()
    raw.columns = make_unique_columns(raw.columns)
    mapped, source = prepare_base_frame(raw, source_dataset)
    mapped = compute_derived(mapped)
    label_values = choose_label_values(raw, mapped, source, label_column)
    mapped = drop_identifier_columns(mapped)
    out = select_model_features(mapped, load_feature_spec())
    if label_values is not None:
        rules = load_label_rules()
        out["label"] = [map_one_label(v, rules, source) for v in label_values.tolist()]
    if not out.columns.is_unique:
        duplicates = sorted({c for c in out.columns if list(out.columns).count(c) > 1})
        raise ValueError(f"Duplicate output columns: {duplicates}")
    return out


def run_self_test() -> dict[str, object]:
    spec_model_count = int((load_feature_spec()["model_input"].astype(str).str.lower() == "true").sum())
    excluded = {"src_ip", "dst_ip", "src_port", "dst_port", "timestamp"}

    cicids = pd.DataFrame({
        "Timestamp": ["01/01/2018 00:00:01", "01/01/2018 00:00:02", "01/01/2018 00:00:03", "01/01/2018 00:00:04"],
        "Flow Duration": [1000000, 2000000, 3000000, 4000000],
        "Tot Fwd Pkts": [10, 8, 6, 4],
        "Tot Bwd Pkts": [5, 3, 2, 1],
        "TotLen Fwd Pkts": [1000, 800, 600, 400],
        "TotLen Bwd Pkts": [500, 300, 200, 100],
        "Pkt Len Mean": [111, 112, 113, 114],
        "Fwd Pkt Len Mean": [210, 208, 206, 204],
        "Bwd Pkt Len Mean": [105, 103, 102, 101],
        "Fwd Pkts/s": [999, 998, 997, 996],
        "Bwd Pkts/s": [899, 898, 897, 896],
        "Src IP": ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4"],
        "Dst IP": ["10.0.1.1", "10.0.1.2", "10.0.1.3", "10.0.1.4"],
        "Src Port": [1234, 1235, 1236, 1237],
        "Dst Port": [80, 22, 443, 53],
        "Protocol": [6, 6, 6, 17],
        "Label": ["DDoS", "SSH-Bruteforce", "Web Attack - SQL Injection", "Benign"],
    })
    cicids_mapped, _ = prepare_base_frame(cicids, "CICIDS")
    cicids_out = harmonize_frame(cicids, "CICIDS", None)

    unsw = pd.DataFrame({
        "dur": [1.0, 2.0, 3.0],
        "spkts": [3, 4, 5],
        "dpkts": [1, 2, 3],
        "sbytes": [300, 400, 500],
        "dbytes": [100, 200, 300],
        "proto": ["tcp", "udp", "tcp"],
        "srcip": ["10.0.0.1", "10.0.0.2", "10.0.0.3"],
        "dstip": ["10.0.1.1", "10.0.1.2", "10.0.1.3"],
        "sport": [111, 222, 333],
        "dsport": [80, 53, 443],
        "Label": [1, 1, 0],
        "attack_cat": ["Reconnaissance", "DoS", "Normal"],
    })
    unsw_mapped, _ = prepare_base_frame(unsw, "UNSW")
    unsw_out = harmonize_frame(unsw, "UNSW", None)

    mqcids = pd.DataFrame({
        "timestamp": ["2024-01-01T00:00:01", "2024-01-01T00:00:02"],
        "src_ip": ["10.1.0.1", "10.1.0.2"],
        "dest_ip": ["10.2.0.1", "10.2.0.2"],
        "src_port": [4444, 5555],
        "dest_port": [80, 8080],
        "proto": ["tcp", "tcp"],
        "app_proto": ["http", "http"],
        "app_service": ["web", "api"],
        "http.hostname": ["a.example", "b.example"],
        "http.host": ["alt-a.example", "alt-b.example"],
        "flow.pkts_toserver": [6, 7],
        "flow.pkts_toclient": [2, 3],
        "flow.bytes_toserver": [600, 700],
        "flow.bytes_toclient": [200, 300],
        "label": ["rce", "command injection"],
    })
    mqcids_mapped, _ = prepare_base_frame(mqcids, "MQCIDS")
    mqcids_out = harmonize_frame(mqcids, "MQCIDS", None)

    checks = {
        "duplicate_columns_absent": cicids_mapped.columns.is_unique and unsw_mapped.columns.is_unique and mqcids_mapped.columns.is_unique and cicids_out.columns.is_unique and unsw_out.columns.is_unique and mqcids_out.columns.is_unique,
        "cicids_directional_pkt_mean_preferred": cicids_out["src_pkt_mean"].tolist() == [210, 208, 206, 204] and cicids_out["dst_pkt_mean"].tolist() == [105, 103, 102, 101],
        "cicids_packet_counts_from_counts": cicids_out["src_pkts"].tolist() == [10, 8, 6, 4] and cicids_out["dst_pkts"].tolist() == [5, 3, 2, 1],
        "cicids_packet_counts_not_rates": cicids_out["src_pkts"].tolist() != [999, 998, 997, 996] and cicids_out["dst_pkts"].tolist() != [899, 898, 897, 896],
        "cicids_labels_mapped": cicids_out["label"].tolist() == ["dos", "bruteforce", "web_attack", "benign"],
        "unsw_attack_cat_preferred": unsw_out["label"].tolist() == ["scan_recon", "dos", "benign"],
        "unsw_identifiers_dropped": not bool(excluded & set(unsw_out.columns)),
        "mqcids_service_coalesced": mqcids_out["app_service"].tolist() == ["web", "api"],
        "mqcids_labels_mapped": mqcids_out["label"].tolist() == ["web_attack", "web_attack"],
        "mqcids_identifiers_dropped": not bool(excluded & set(mqcids_out.columns)),
        "model_columns_plus_label": all(len(out.columns) == spec_model_count + 1 for out in [cicids_out, unsw_out, mqcids_out]),
    }
    result = {"status": "PASS" if all(checks.values()) else "CHECK", "checks": checks, "case_rows": {"cicids": int(len(cicids_out)), "unsw": int(len(unsw_out)), "mqcids": int(len(mqcids_out))}, "columns": int(len(cicids_out.columns))}
    OUTPUTS.mkdir(exist_ok=True)
    (OUTPUTS / "harmonize_schema_self_test.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply the public schema and label harmonization recipe.")
    parser.add_argument("--input", type=Path, help="User-supplied CSV or Parquet table.")
    parser.add_argument("--source-dataset", default="auto", help="Dataset scope for label and source-column rules; default auto-detects from columns.")
    parser.add_argument("--label-column", default=None, help="Optional label column to harmonize.")
    parser.add_argument("--output", type=Path, default=OUTPUTS / "harmonized_preview.csv")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        result = run_self_test()
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "PASS" else 1

    spec = load_feature_spec()
    source_map = load_source_mapping()
    rules = load_label_rules()
    if args.input is None:
        summary = {"status": "PASS", "feature_rows": int(len(spec)), "model_input_rows": int((spec["model_input"].astype(str).str.lower() == "true").sum()), "source_mapping_rows": int(len(source_map)), "label_rule_rows": int(len(rules))}
        OUTPUTS.mkdir(exist_ok=True)
        (OUTPUTS / "harmonize_schema_dry_run.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 0

    df = read_table(args.input)
    out = harmonize_frame(df, args.source_dataset, args.label_column)
    if args.dry_run:
        print(json.dumps({"status": "PASS", "input_rows": int(len(df)), "output_columns": list(out.columns)}, indent=2))
        return 0
    output = safe_output_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output, index=False)
    print(json.dumps({"status": "PASS", "output": str(output.relative_to(ROOT.resolve())), "rows": int(len(out))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

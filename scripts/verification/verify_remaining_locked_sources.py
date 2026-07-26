#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import csv
import itertools
import json
import math
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/packaged_verification_summary.json"
SUMMARY_MD = ROOT / "verification/reports/verified_results_summary.md"
CLAIM_MAP = ROOT / "manifest/artifact_claim_to_file_map.csv"
SOURCE_MAP = ROOT / "manifest/paper_source_map.yaml"
TOL = 5e-4

SOURCES = [
    "evidence/locked_sources/representation/representation_ablation.csv",
    "evidence/locked_sources/temporalization/temporalization_values.csv",
    "evidence/locked_sources/capacity/capacity_ablation_meanstd.csv",
    "evidence/locked_sources/head_ablation/head_ablation_meanstd.csv",
    "evidence/locked_sources/llm_comparison/shallow_vs_llm_comparison.csv",
    "evidence/locked_sources/context_length/llm_context_length_meanstd.csv",
    "evidence/locked_sources/llm_comparison/llm_pretraining_meanstd.csv",
    "evidence/locked_sources/llm_comparison/encoder_decoder_comparison.csv",
    "evidence/locked_sources/per_dataset_validation/per_dataset_validation.csv",
    "evidence/locked_sources/efficiency/efficiency_context_tradeoff.csv",
    "evidence/locked_sources/temporalization_streaming/streaming_temporalization_comparison.csv",
    "evidence/locked_sources/structural_preservation/structural_preservation_paper_table.csv",
    "evidence/locked_sources/structural_preservation/structural_preservation_summary.csv",
    "evidence/locked_sources/rq5_cross_dataset/rq5_cross_dataset_paper_table.csv",
    "evidence/locked_sources/rq5_cross_dataset/rq5_cross_dataset_statistics.json",
]

EXPECTED_STRUCTURAL = {
    "UNSW": (0.114, 0.756, 0.886, 0.244, 0.286, 1.000),
    "CICIDS": (0.027, 0.742, 0.973, 0.258, 0.049, 1.000),
    "MQCIDS": (0.148, 0.757, 0.852, 0.243, 0.236, 1.000),
    "Avg.": (0.096, 0.752, 0.904, 0.248, 0.190, 1.000),
}

EXPECTED_PER_DATASET = {
    "UNSW": (0.9872970202209838, 0.7100098635510794, 0.7612389335355016),
    "CICIDS": (0.9960621793618601, 0.9216936196576652, 0.9355024350745916),
    "MQCIDS": (0.9959749552772809, 0.9448771616737932, 0.9329641383426701),
}

EXPECTED_RQ5 = {
    ("CICIDS", "UNSW"): (0.420, 0.423, 0.003, 0.199, 0.198, 0.001),
    ("CICIDS", "MQCIDS"): (0.333, 0.333, 0.000, 0.181, 0.161, 0.020),
    ("UNSW", "MQCIDS"): (0.383, 0.439, 0.056, 0.612, 0.557, 0.055),
    ("UNSW", "CICIDS"): (0.480, 0.506, 0.026, 0.477, 0.451, 0.026),
    ("MQCIDS", "UNSW"): (0.479, 0.482, 0.003, 0.506, 0.510, -0.004),
    ("MQCIDS", "CICIDS"): (0.387, 0.355, -0.032, 0.598, 0.637, -0.039),
    ("Avg.", ""): (0.414, 0.423, 0.009, 0.429, 0.419, 0.010),
}

REQUIRED_CORE_COMPONENTS = [
    "Table I -- structural preservation",
    "Figure 2 / RQ1 -- temporalization",
    "Figure 3 / RQ2 -- capacity ablation",
    "Figure 4 and Table III -- aggregation/head ablation",
    "Figure 5 and Table IV -- shallow versus pretrained transformers",
    "Figures 6 and 7 -- context and efficiency",
    "Figure 8 -- per-dataset validation",
    "Table V / RQ5 -- cross-dataset generalization",
    "Table V / RQ5 -- statistical trend diagnostics",
    "Section III-E -- matched streaming temporalization benchmark",
]


def read_csv(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open(newline="") as handle:
        return list(csv.DictReader(handle))


def close(actual: float, expected: float, tol: float = TOL) -> bool:
    return abs(float(actual) - float(expected)) <= tol


def add(checks: list[dict[str, object]], source: str, item: str, metric: str, actual: object, expected: object, ok: bool) -> None:
    checks.append({
        "source": source,
        "item": item,
        "metric": metric,
        "actual": actual,
        "expected": expected,
        "status": "PASS" if ok else "FAIL",
    })


def signed_rank_stats(diffs: list[float]) -> dict[str, float | int]:
    nonzero = [d for d in diffs if abs(d) > 1e-12]
    pairs = sorted((abs(d), i, d) for i, d in enumerate(nonzero))
    ranks = [0.0] * len(nonzero)
    i = 0
    while i < len(pairs):
        j = i + 1
        while j < len(pairs) and abs(pairs[j][0] - pairs[i][0]) < 1e-12:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[pairs[k][1]] = avg_rank
        i = j
    w_plus = sum(rank for rank, diff in zip(ranks, nonzero) if diff > 0)
    w_minus = sum(rank for rank, diff in zip(ranks, nonzero) if diff < 0)
    total = sum(ranks)
    ge = 0
    count = 0
    for signs in itertools.product([0, 1], repeat=len(ranks)):
        wp = sum(rank for rank, sign in zip(ranks, signs) if sign)
        ge += int(wp >= w_plus - 1e-12)
        count += 1
    return {
        "n_total": len(diffs),
        "n_nonzero": len(nonzero),
        "zero_differences": len(diffs) - len(nonzero),
        "w_plus": w_plus,
        "w_minus": w_minus,
        "one_sided_p_session_greater": ge / count if count else 1.0,
        "rank_biserial": (w_plus - w_minus) / total if total else 0.0,
    }


def verify_structural(checks: list[dict[str, object]]) -> None:
    rel = "evidence/locked_sources/structural_preservation/structural_preservation_paper_table.csv"
    rows = {r["dataset"]: r for r in read_csv(rel)}
    cols = [
        "sliding_retention", "session_retention", "sliding_fragmentation",
        "session_fragmentation", "sliding_purity", "session_purity",
    ]
    for dataset, expected_values in EXPECTED_STRUCTURAL.items():
        row = rows.get(dataset)
        add(checks, rel, dataset, "row_present", row is not None, True, row is not None)
        if not row:
            continue
        for col, expected in zip(cols, expected_values):
            actual = float(row[col])
            add(checks, rel, dataset, col, round(actual, 3), expected, close(round(actual, 3), expected))
        add(checks, rel, dataset, "k", row.get("k"), "32", row.get("k") == "32")
        add(checks, rel, dataset, "stride", row.get("stride"), "16", row.get("stride") == "16")
        add(checks, rel, dataset, "retention_type", row.get("retention_type"), "emittable_related_pairs", row.get("retention_type") == "emittable_related_pairs")
        add(checks, rel, dataset, "sliding_fragmentation_identity", float(row["sliding_retention"]) + float(row["sliding_fragmentation"]), 1.0, close(float(row["sliding_retention"]) + float(row["sliding_fragmentation"]), 1.0))
        add(checks, rel, dataset, "session_fragmentation_identity", float(row["session_retention"]) + float(row["session_fragmentation"]), 1.0, close(float(row["session_retention"]) + float(row["session_fragmentation"]), 1.0))
        add(checks, rel, dataset, "session_purity", round(float(row["session_purity"]), 3), 1.0, close(round(float(row["session_purity"]), 3), 1.0))


def verify_per_dataset(checks: list[dict[str, object]]) -> None:
    rel = "evidence/locked_sources/per_dataset_validation/per_dataset_validation.csv"
    rows = {r["dataset"]: r for r in read_csv(rel)}
    for dataset, expected_values in EXPECTED_PER_DATASET.items():
        row = rows.get(dataset)
        add(checks, rel, dataset, "row_present", row is not None, True, row is not None)
        if not row:
            continue
        for col, expected in zip(["accuracy", "macro_f1", "pr_auc_macro"], expected_values):
            actual = float(row[col])
            add(checks, rel, dataset, col, actual, expected, close(actual, expected, 1e-9))


def verify_rq5(checks: list[dict[str, object]]) -> None:
    rel = "evidence/locked_sources/rq5_cross_dataset/rq5_cross_dataset_paper_table.csv"
    rows = {(r["train"], r["test"]): r for r in read_csv(rel)}
    cols = ["sliding_f1", "session_f1", "delta_f1", "trg_sliding", "trg_session", "delta_trg"]
    for key, expected_values in EXPECTED_RQ5.items():
        row = rows.get(key)
        add(checks, rel, " -> ".join([x for x in key if x]), "row_present", row is not None, True, row is not None)
        if not row:
            continue
        for col, expected in zip(cols, expected_values):
            actual = round(float(row[col]), 3)
            add(checks, rel, " -> ".join([x for x in key if x]), col, actual, expected, close(actual, expected))
    pairs = [r for r in read_csv(rel) if r["train"] != "Avg."]
    f1 = [float(r["delta_f1"]) for r in pairs]
    trg = [float(r["delta_trg"]) for r in pairs]
    stats_rel = "evidence/locked_sources/rq5_cross_dataset/rq5_cross_dataset_statistics.json"
    stats = json.loads((ROOT / stats_rel).read_text())
    expected_stats = {
        "macro_f1_delta_session_minus_sliding": signed_rank_stats(f1),
        "trg_delta_sliding_minus_session": signed_rank_stats(trg),
    }
    for block, expected in expected_stats.items():
        got = stats[block]
        for field, exp in expected.items():
            actual = got[field]
            ok = close(float(actual), float(exp), 1e-9)
            add(checks, stats_rel, block, field, actual, exp, ok)


def count_json_objects(rel: str) -> int:
    obj = json.loads((ROOT / rel).read_text())
    if isinstance(obj, dict):
        return len(obj)
    if isinstance(obj, list):
        return len(obj)
    return 1


def row_or_object_count(rel: str) -> dict[str, int | None]:
    path = ROOT / rel
    if not path.exists():
        return {"row_count": None, "object_count": None}
    if path.suffix == ".csv":
        return {"row_count": len(read_csv(rel)), "object_count": None}
    if path.suffix == ".json":
        return {"row_count": None, "object_count": count_json_objects(rel)}
    return {"row_count": None, "object_count": None}


def verify_sources_exist() -> list[dict[str, object]]:
    summary = []
    for rel in SOURCES:
        path = ROOT / rel
        counts = row_or_object_count(rel)
        summary.append({"artifact_file": rel, "exists": path.exists(), **counts})
    return summary


def evidence_entry(rel: str) -> dict[str, object]:
    path = ROOT / rel
    return {
        "artifact_path": rel,
        "exists": path.exists(),
        **row_or_object_count(rel),
    }


def build_verification_matrix(status: str) -> list[dict[str, Any]]:
    def record(component: str, claim: str, paths: list[str], verifier: str, notes: str = "") -> dict[str, Any]:
        evidence = [evidence_entry(path) for path in paths]
        return {
            "paper_component": component,
            "claim_evaluation": claim,
            "artifact_path": paths[0] if paths else None,
            "evidence": evidence,
            "verifier": verifier,
            "status": "PASS" if status == "PASS" and all(e["exists"] for e in evidence) else "FAIL",
            "notes": notes,
        }

    return [
        record(
            "Table I -- structural preservation",
            "Retention, fragmentation, purity, k=32, s=16, all three datasets, averages, and fragmentation = 1 - retention.",
            [
                "evidence/locked_sources/structural_preservation/structural_preservation_paper_table.csv",
                "evidence/locked_sources/structural_preservation/structural_preservation_summary.csv",
                "evidence/locked_sources/structural_preservation/structural_preservation_sanity.json",
            ],
            "scripts/verification/verify_remaining_locked_sources.py",
        ),
        record(
            "Figure 2 / RQ1 -- temporalization",
            "Per-flow, legacy timestamp windowing, and session-coherent temporalization; Macro-F1, accuracy, and inference throughput after sequences exist.",
            ["evidence/locked_sources/temporalization/temporalization_values.csv"],
            "scripts/verification/verify_remaining_locked_sources.py",
        ),
        record(
            "Figure 3 / RQ2 -- capacity ablation",
            "Architecture grid, Macro-F1, parameter counts, and throughput; capacity and parameter audit supporting Figure 3 and Table IV.",
            [
                "evidence/locked_sources/capacity/capacity_ablation_meanstd.csv",
                "evidence/locked_sources/capacity/shallow_capacity_parameter_audit.csv",
            ],
            "scripts/verification/verify_remaining_locked_sources.py",
        ),
        record(
            "Figure 4 and Table III -- aggregation/head ablation",
            "Encoder/decoder mean, CLS, attention, last-token aggregation; Macro-F1, PR-AUC, accuracy, and throughput.",
            ["evidence/locked_sources/head_ablation/head_ablation_meanstd.csv"],
            "scripts/verification/verify_remaining_locked_sources.py",
        ),
        record(
            "Figure 5 and Table IV -- shallow versus pretrained transformers",
            "ST operating points, ModernBERT, Qwen2.5-0.5B, parameters, Macro-F1, accuracy, and throughput.",
            [
                "evidence/locked_sources/llm_comparison/shallow_vs_llm_comparison.csv",
                "evidence/locked_sources/capacity/shallow_capacity_parameter_audit.csv",
            ],
            "scripts/verification/verify_remaining_locked_sources.py",
        ),
        record(
            "Figures 6 and 7 -- context and efficiency",
            "Shallow transformer and ModernBERT context/token-budget tradeoff; quality and inference throughput.",
            ["evidence/locked_sources/efficiency/efficiency_context_tradeoff.csv"],
            "scripts/verification/verify_remaining_locked_sources.py",
            "Efficiency evidence uses explicit context length, quality metric, and flows/s columns.",
        ),
        record(
            "Figure 8 -- per-dataset validation",
            "UNSW/CICIDS/MQCIDS accuracy, Macro-F1, and PR-AUC; UNSW values are 0.9872970202209838, 0.7100098635510794, and 0.7612389335355016.",
            ["evidence/locked_sources/per_dataset_validation/per_dataset_validation.csv"],
            "scripts/verification/verify_remaining_locked_sources.py",
        ),
        record(
            "Table V / RQ5 -- cross-dataset generalization",
            "Six directed transfers and average Sliding/Session Macro-F1, delta F1, Sliding/Session TRG, and delta TRG.",
            [
                "evidence/locked_sources/rq5_cross_dataset/rq5_cross_dataset_paper_table.csv",
                "evidence/locked_sources/rq5_cross_dataset/rq5_cross_dataset_paper_table.tex",
                "evidence/locked_sources/rq5_cross_dataset/rq5_cross_dataset_raw.csv",
            ],
            "scripts/verification/verify_remaining_locked_sources.py",
        ),
        record(
            "Table V / RQ5 -- statistical trend diagnostics",
            "Macro-F1 W+=11, p=0.1875, rank-biserial=0.4667; TRG W+=14, p=0.28125, rank-biserial=0.3333; positive/modest and statistically inconclusive.",
            ["evidence/locked_sources/rq5_cross_dataset/rq5_cross_dataset_statistics.json"],
            "scripts/verification/verify_remaining_locked_sources.py",
            "Trend diagnostics are descriptive and do not encode significance-star claims.",
        ),
        record(
            "Section III-E -- matched streaming temporalization benchmark",
            "Conditioned on precomputed session identifiers; 1.02--1.06 million input flows/s, 2.17--2.33x runtime cost, 50--58% fewer windows; no end-to-end throughput claim.",
            [
                "evidence/locked_sources/temporalization_streaming/streaming_temporalization_comparison.csv",
                "evidence/locked_sources/temporalization_streaming/streaming_temporalization_raw_runs.csv",
                "evidence/locked_sources/temporalization_streaming/streaming_temporalization_summary.csv",
                "evidence/locked_sources/temporalization_streaming/streaming_temporalization_correctness.json",
            ],
            "scripts/verification/verify_streaming_temporalization_benchmark.py",
        ),
        record(
            "Supplementary representation ablation",
            "Representation-ablation source retained as supplementary evidence.",
            ["evidence/locked_sources/representation/representation_ablation.csv"],
            "scripts/verification/verify_remaining_locked_sources.py",
        ),
        record(
            "Supplementary ablations",
            "Context length, pretraining, encoder-decoder, robustness, and sensitivity evidence are supplementary only.",
            [
                "evidence/locked_sources/context_length/modernbert_context_ablation.csv",
                "evidence/locked_sources/llm_comparison/llm_pretraining_meanstd.csv",
                "evidence/locked_sources/llm_comparison/encoder_decoder_comparison.csv",
                "evidence/robustness_sensitivity/robustness_sensitivity_summary.csv",
            ],
            "scripts/verification/verify_robustness_sensitivity.py",
        ),
    ]


def verify_summary_consistency(matrix: list[dict[str, Any]]) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    md_text = SUMMARY_MD.read_text() if SUMMARY_MD.exists() else ""
    claim_text = CLAIM_MAP.read_text() if CLAIM_MAP.exists() else ""
    source_text = SOURCE_MAP.read_text() if SOURCE_MAP.exists() else ""
    matrix_components = {r["paper_component"] for r in matrix}

    def check(item: str, metric: str, actual: object, expected: object, ok: bool) -> None:
        add(checks, "verification_summary_alignment", item, metric, actual, expected, ok)

    for component in REQUIRED_CORE_COMPONENTS:
        check(component, "markdown_component_present", component in md_text, True, component in md_text)
        check(component, "json_component_present", component in matrix_components, True, component in matrix_components)

    for record in matrix:
        component = record["paper_component"]
        evidence = record.get("evidence", [])
        check(component, "all_evidence_paths_exist", all(e.get("exists") for e in evidence), True, all(e.get("exists") for e in evidence))

    current_text = md_text + "\n" + json.dumps(matrix)
    required_current_phrases = [
        "Figure 3 and Table IV",
        "Table V / RQ5",
        "Section III-E",
    ]
    for phrase in required_current_phrases:
        check(phrase, "current_label_present", phrase in current_text, True, phrase in current_text)

    with (ROOT / "evidence/locked_sources/efficiency/efficiency_context_tradeoff.csv").open(newline="") as handle:
        efficiency_header = next(csv.reader(handle))
    required_efficiency_columns = {"family", "context_axis_label", "quality_metric", "flows_per_sec"}
    missing_efficiency_columns = sorted(required_efficiency_columns - set(efficiency_header))
    check(
        "Figures 6 and 7 -- context and efficiency",
        "required_columns_present",
        missing_efficiency_columns,
        [],
        not missing_efficiency_columns,
    )

    for key in ["table_i", "table_v", "figure_8", "section_iii_e_streaming_temporalization_microbenchmark"]:
        check(key, "source_map_entry_present", key in source_text, True, key in source_text)
    for phrase in ["Table I structural preservation", "Table V / RQ5", "Section III-E matched streaming temporalization"]:
        check(phrase, "claim_map_entry_present", phrase in claim_text, True, phrase in claim_text)

    claim_paths = []
    if CLAIM_MAP.exists():
        with CLAIM_MAP.open(newline="") as handle:
            for row in csv.DictReader(handle):
                artifact_file = row.get("artifact_file", "").strip()
                if artifact_file:
                    claim_paths.append(artifact_file)
    missing_claim_paths = [path for path in claim_paths if not (ROOT / path).exists()]
    check("manifest/artifact_claim_to_file_map.csv", "claim_map_paths_exist", missing_claim_paths, [], not missing_claim_paths)

    source_paths = []
    for line in source_text.splitlines():
        if ":" not in line:
            continue
        value = line.split(":", 1)[1].strip().strip('"\'')
        if not value or " " in value:
            continue
        if "/" in value or value.endswith((".csv", ".json", ".yaml", ".md", ".py", ".pdf", ".png", ".tex")):
            source_paths.append(value)
    missing_source_paths = [path for path in source_paths if not (ROOT / path).exists()]
    check("manifest/paper_source_map.yaml", "source_map_paths_exist", missing_source_paths, [], not missing_source_paths)

    return checks


def main() -> int:
    summary = verify_sources_exist()
    checks: list[dict[str, object]] = []
    for row in summary:
        add(checks, row["artifact_file"], "file", "exists", row["exists"], True, bool(row["exists"]))
    verify_structural(checks)
    verify_per_dataset(checks)
    verify_rq5(checks)
    numeric_failures = [c for c in checks if c["status"] != "PASS"]
    provisional_status = "PASS" if not numeric_failures else "FAIL"
    matrix = build_verification_matrix(provisional_status)
    consistency_checks = verify_summary_consistency(matrix)
    failures = numeric_failures + [c for c in consistency_checks if c["status"] != "PASS"]
    result = {
        "status": "PASS" if not failures else "FAIL",
        "sources": summary,
        "verification_matrix": matrix,
        "numeric_checks": checks,
        "summary_consistency_checks": consistency_checks,
        "failures": failures,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "status": result["status"],
        "checked_files": len(summary),
        "verification_records": len(matrix),
        "numeric_checks": len(checks),
        "summary_consistency_checks": len(consistency_checks),
        "failures": len(failures),
    }, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

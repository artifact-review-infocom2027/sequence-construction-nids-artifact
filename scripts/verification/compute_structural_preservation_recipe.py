#!/usr/bin/env python3
"""
Reviewer-facing recipe for structural-preservation diagnostics.

This recipe documents the expected input schema and efficient metric logic used
for the locked structural-preservation evidence. It is intentionally
input-driven: reviewers may provide their own flow table with the required
columns and reproduce the calculation without private datasets.

Expected input columns:
- dataset: dataset name, for example UNSW, CICIDS, or MQCIDS
- split: split identifier; windows are constructed within each split
- timestamp: sortable timestamp or numeric time key
- session_id: reconstructed communication-session identifier

Metrics:
- eligible pairs: same-session flow pairs with within-session distance < k
- emittable pairs: eligible pairs from sessions with length >= k
- retention: fraction of pairs co-occurring in at least one window
- fragmentation: 1 - retention
- purity: average dominant-session share per window

The implementation avoids all-pairs expansion by iterating offsets d=1..k-1
within session-sorted flow order and testing whether each pair can be covered by
at least one stride-aligned window start.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd


def ceil_to_stride(lo: np.ndarray, stride: int) -> np.ndarray:
    return ((lo + stride - 1) // stride) * stride


def covered_by_window(left: np.ndarray, right: np.ndarray, scope_len: np.ndarray, k: int, stride: int) -> np.ndarray:
    lo = np.maximum(right - k + 1, 0)
    hi = np.minimum(left, scope_len - k)
    return ceil_to_stride(lo, stride) <= hi


def timestamp_purity(session_codes_by_time: np.ndarray, split_lengths: list[int], k: int, stride: int) -> tuple[int, float]:
    total = 0
    dominant = 0.0
    offset = 0
    for n in split_lengths:
        arr = session_codes_by_time[offset:offset + n]
        offset += n
        if n < k:
            continue
        counter = None
        prev = None
        for start in range(0, n - k + 1, stride):
            if counter is None:
                counter = Counter(int(x) for x in arr[start:start + k])
            else:
                for x in arr[prev:start]:
                    xi = int(x)
                    counter[xi] -= 1
                    if counter[xi] <= 0:
                        del counter[xi]
                for x in arr[prev + k:start + k]:
                    counter[int(x)] += 1
            prev = start
            dominant += max(counter.values()) / float(k)
            total += 1
    return total, dominant / total if total else float('nan')


def compute(df: pd.DataFrame, k: int, stride: int) -> pd.DataFrame:
    required = {'dataset', 'split', 'timestamp', 'session_id'}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f'missing required columns: {missing}')

    rows = []
    for dataset, dfg in df.groupby('dataset', sort=False):
        dfg = dfg.dropna(subset=['split', 'timestamp', 'session_id']).copy()
        dfg['timestamp_key'] = pd.to_datetime(dfg['timestamp'], errors='coerce', utc=True)
        if dfg['timestamp_key'].isna().all():
            dfg['timestamp_key'] = pd.to_numeric(dfg['timestamp'], errors='coerce')
        dfg = dfg.dropna(subset=['timestamp_key']).copy()
        dfg = dfg.reset_index(drop=True)
        dfg['session_key'] = dfg['split'].astype(str) + '\x1f' + dfg['session_id'].astype(str)
        dfg['session_code'] = pd.factorize(dfg['session_key'], sort=False)[0].astype(np.int64)
        n_flows = len(dfg)

        by_time = dfg.sort_values(['split', 'timestamp_key'], kind='mergesort').reset_index(drop=False)
        by_time['time_rank'] = by_time.groupby('split', sort=False).cumcount().astype(np.int64)
        split_lengths = by_time.groupby('split', sort=False).size().to_numpy(dtype=np.int64)
        split_len_map = by_time.groupby('split', sort=False).size().to_dict()
        by_time['split_len'] = by_time['split'].map(split_len_map).astype(np.int64)
        time_rank = np.empty(n_flows, dtype=np.int64)
        split_len = np.empty(n_flows, dtype=np.int64)
        time_rank[by_time['index'].to_numpy(dtype=np.int64)] = by_time['time_rank'].to_numpy(dtype=np.int64)
        split_len[by_time['index'].to_numpy(dtype=np.int64)] = by_time['split_len'].to_numpy(dtype=np.int64)
        session_codes_by_time = by_time['session_code'].to_numpy(dtype=np.int64)

        by_session = dfg.assign(orig_index=np.arange(n_flows, dtype=np.int64)).sort_values(
            ['session_code', 'timestamp_key'], kind='mergesort'
        ).reset_index(drop=True)
        sess_codes = by_session['session_code'].to_numpy(dtype=np.int64)
        orig = by_session['orig_index'].to_numpy(dtype=np.int64)
        t_rank = time_rank[orig]
        s_len_by_row = split_len[orig]

        starts = np.flatnonzero(np.r_[True, sess_codes[1:] != sess_codes[:-1]])
        lengths = np.diff(np.r_[starts, len(sess_codes)]).astype(np.int64)
        pos = np.empty(len(sess_codes), dtype=np.int64)
        sess_len = np.empty(len(sess_codes), dtype=np.int64)
        for start, length in zip(starts, lengths):
            end = start + int(length)
            pos[start:end] = np.arange(int(length), dtype=np.int64)
            sess_len[start:end] = int(length)

        eligible = timestamp_retained = session_retained = 0
        emittable = timestamp_emit_retained = session_emit_retained = 0
        for d in range(1, k):
            valid = sess_codes[:-d] == sess_codes[d:]
            if not valid.any():
                continue
            idx = np.flatnonzero(valid)
            eligible += int(len(idx))
            left = np.minimum(t_rank[idx], t_rank[idx + d])
            right = np.maximum(t_rank[idx], t_rank[idx + d])
            ts_cov = covered_by_window(left, right, s_len_by_row[idx], k, stride)
            sess_cov = covered_by_window(pos[idx], pos[idx + d], sess_len[idx], k, stride)
            timestamp_retained += int(ts_cov.sum())
            session_retained += int(sess_cov.sum())
            emit_mask = sess_len[idx] >= k
            emittable += int(emit_mask.sum())
            timestamp_emit_retained += int(ts_cov[emit_mask].sum())
            session_emit_retained += int(sess_cov[emit_mask].sum())

        ts_windows, ts_purity = timestamp_purity(session_codes_by_time, [int(x) for x in split_lengths], k, stride)
        session_windows = int(((lengths[lengths >= k] - k) // stride + 1).sum()) if (lengths >= k).any() else 0
        flow_coverage = float(lengths[lengths >= k].sum() / n_flows) if n_flows else float('nan')
        pair_coverage = float(emittable / eligible) if eligible else float('nan')
        for method, retained, emit_retained, n_windows, purity in [
            ('Sliding', timestamp_retained, timestamp_emit_retained, ts_windows, ts_purity),
            ('Session', session_retained, session_emit_retained, session_windows, 1.0 if session_windows else float('nan')),
        ]:
            rows.append({
                'dataset': dataset,
                'method': method,
                'k': k,
                'stride': stride,
                'retention': retained / eligible if eligible else float('nan'),
                'fragmentation': 1.0 - retained / eligible if eligible else float('nan'),
                'emittable_retention': emit_retained / emittable if emittable else float('nan'),
                'emittable_fragmentation': 1.0 - emit_retained / emittable if emittable else float('nan'),
                'purity': purity,
                'flow_coverage': flow_coverage,
                'pair_coverage': pair_coverage,
                'n_windows': n_windows,
                'eligible_related_pairs': eligible,
                'emittable_related_pairs': emittable,
            })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description='Compute structural-preservation metrics from a reviewer-supplied flow table.')
    parser.add_argument('--input-csv', required=True, help='CSV containing dataset, split, timestamp, and session_id columns')
    parser.add_argument('--output-csv', required=True, help='Path to write metric summary CSV')
    parser.add_argument('--k', type=int, default=32)
    parser.add_argument('--stride', type=int, default=16)
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    out = compute(df, k=args.k, stride=args.stride)
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)


if __name__ == '__main__':
    main()

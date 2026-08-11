#!/usr/bin/env python3
"""Summarize paired recovery trials without storing transcripts or source content."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from typing import Any, Optional


def _positive(values: list[float], label: str) -> list[float]:
    if not values or any(value <= 0 for value in values):
        raise ValueError(f"{label} requires one or more positive durations")
    return values


def summarize(
    baseline: list[float], governed: list[float], threshold_percent: float
) -> dict[str, Any]:
    baseline_values = _positive(baseline, "baseline")
    governed_values = _positive(governed, "governed")
    if threshold_percent < 0 or threshold_percent > 100:
        raise ValueError("threshold percent must be between 0 and 100")
    baseline_median = statistics.median(baseline_values)
    governed_median = statistics.median(governed_values)
    improvement = ((baseline_median - governed_median) / baseline_median) * 100
    relative_pass = improvement >= threshold_percent
    absolute_pass = governed_median <= 300
    if relative_pass and absolute_pass:
        verdict = "effect_threshold_met"
    elif improvement > 0 and absolute_pass:
        verdict = "directional_benefit"
    else:
        verdict = "effect_not_demonstrated"
    return {
        "schema_version": "0.3",
        "baseline": {"samples_seconds": baseline_values, "median_seconds": baseline_median},
        "governed": {"samples_seconds": governed_values, "median_seconds": governed_median},
        "improvement_percent": improvement,
        "threshold_percent": threshold_percent,
        "passed_relative_threshold": relative_pass,
        "passed_absolute_five_minute_threshold": absolute_pass,
        "verdict": verdict,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trial-summary")
    parser.add_argument("--baseline", type=float, action="append", required=True)
    parser.add_argument("--governed", type=float, action="append", required=True)
    parser.add_argument("--threshold-percent", type=float, default=50.0)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = summarize(args.baseline, args.governed, args.threshold_percent)
    except ValueError as exc:
        print(f"trial-summary: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            f"Baseline median: {result['baseline']['median_seconds']:.3f}s\n"
            f"Governed median: {result['governed']['median_seconds']:.3f}s\n"
            f"Improvement: {result['improvement_percent']:.1f}%\n"
            f"Verdict: {result['verdict']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

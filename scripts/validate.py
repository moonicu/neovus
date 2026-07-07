"""Proxy validation: does NeoVUS's evidence point the right way?

The headline test uses ClinVar *reclassification* events: for variants that moved
across the VUS boundary (VUS → pathogenic or VUS → benign), does the tool's
transparent in-silico evidence agree with the *new* classification? No ClinVar
label is used as a feature — only REVEL / AlphaMissense / CADD / gnomAD.

    uv run python scripts/validate.py                       # curated benchmark
    uv run python scripts/validate.py --benchmark benchmark/benchmark.csv

Works with either benchmark schema (a 'direction' column, or ClinVar
significance / reclass_to columns).
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter

from neovus.scoring import evidence_direction
from neovus.sources import myvariant


def direction_from(sig: str | None) -> str | None:
    s = (sig or "").lower()
    if "pathogenic" in s:
        return "pathogenic"
    if "benign" in s:
        return "benign"
    return None


def true_label(row: dict) -> str | None:
    """Ground-truth direction for a benchmark row, schema-agnostic."""
    if row.get("direction"):
        return direction_from(row["direction"]) or row["direction"].strip().lower()
    # Prefer the settled current classification; fall back to the reclass target.
    return (direction_from(row.get("clinvar_current_significance"))
            or direction_from(row.get("reclass_to")))


def is_reclassified(row: dict) -> bool:
    return str(row.get("reclassified", "")).strip().lower() == "yes"


def score(rows: list[dict]) -> dict:
    called = correct = 0
    conf = Counter()
    for r in rows:
        true = true_label(r)
        if true not in ("pathogenic", "benign"):
            continue
        ann = myvariant.annotate_variant(r["variant_genomic_grch38"])
        if ann is None:
            continue
        d = evidence_direction(ann)
        if d.call == "uncertain":
            continue
        called += 1
        correct += (d.call == true)
        conf[(true, d.call)] += 1
    return {"called": called, "correct": correct, "conf": conf}


def _print(title: str, s: dict) -> None:
    c, n = s["correct"], s["called"]
    print(f"\n{title}")
    print(f"  direction accuracy: {c}/{n} = {c/n:.1%}" if n else "  (no callable variants)")
    conf = s["conf"]
    tp, fp = conf[("pathogenic", "pathogenic")], conf[("benign", "pathogenic")]
    fn = conf[("pathogenic", "benign")]
    if tp + fp:
        print(f"  pathogenic precision: {tp/(tp+fp):.1%}", end="")
    if tp + fn:
        print(f"   recall: {tp/(tp+fn):.1%}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", default="benchmark/neonatal_vus_benchmark.csv")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.benchmark)))
    if args.limit:
        rows = rows[:args.limit]
    reclass = [r for r in rows if is_reclassified(r)]

    print("=" * 60)
    print(f"NeoVUS proxy validation — {args.benchmark}")
    print(f"variants: {len(rows)} | reclassified across VUS boundary: {len(reclass)}")
    print("=" * 60)

    _print("ALL variants (current ClinVar direction):", score(rows))
    if reclass:
        _print("RECLASSIFIED subset (evidence vs the NEW classification):", score(reclass))
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

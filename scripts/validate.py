"""Proxy validation: does NeoVUS's evidence point the right way?

For each benchmark variant (labelled pathogenic / benign by ClinVar's current
classification), we run NeoVUS's annotation, aggregate the in-silico evidence into
a direction, and check agreement with the ClinVar label. This is the open-data
proxy the project promises: on variants whose classification is now settled, does
the tool's transparent evidence lean the right way?

    uv run python scripts/validate.py --benchmark benchmark/benchmark.csv

No ClinVar label is used as a feature — only REVEL/AlphaMissense/CADD/gnomAD.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter

from neovus.scoring import evidence_direction
from neovus.sources import myvariant


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", default="benchmark/benchmark.csv")
    ap.add_argument("--limit", type=int, default=0, help="cap variants (0 = all)")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.benchmark)))
    if args.limit:
        rows = rows[:args.limit]

    called = 0            # variants with a directional call
    correct = 0
    confusion = Counter()  # (true, predicted)
    per_gene = Counter()
    per_gene_ok = Counter()
    no_evidence = 0

    for r in rows:
        true = r["direction"].strip().lower()
        if true not in ("pathogenic", "benign"):
            continue
        ann = myvariant.annotate_variant(r["variant_genomic_grch38"])
        if ann is None:
            no_evidence += 1
            continue
        d = evidence_direction(ann)
        if d.call == "uncertain":
            no_evidence += 1
            continue
        called += 1
        per_gene[r["gene"]] += 1
        ok = (d.call == true)
        correct += ok
        per_gene_ok[r["gene"]] += ok
        confusion[(true, d.call)] += 1

    total_labeled = sum(1 for r in rows if r["direction"].strip().lower() in ("pathogenic", "benign"))
    acc = correct / called if called else 0.0

    print("=" * 60)
    print("NeoVUS proxy validation — evidence-direction agreement")
    print("=" * 60)
    print(f"benchmark variants (labelled):   {total_labeled}")
    print(f"with a directional call:         {called}")
    print(f"uncalled (no in-silico signal):  {no_evidence}")
    print(f"\nDIRECTION ACCURACY:              {correct}/{called} = {acc:.1%}")
    print("\nConfusion (true → predicted):")
    for true in ("pathogenic", "benign"):
        for pred in ("pathogenic", "benign"):
            print(f"  {true:11} → {pred:11}: {confusion[(true, pred)]}")
    # precision/recall for pathogenic
    tp = confusion[("pathogenic", "pathogenic")]
    fp = confusion[("benign", "pathogenic")]
    fn = confusion[("pathogenic", "benign")]
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    print(f"\nPathogenic precision: {prec:.1%}   recall: {rec:.1%}")
    print("\nPer-gene accuracy:")
    for g in sorted(per_gene):
        print(f"  {g:10} {per_gene_ok[g]}/{per_gene[g]}")
    print("=" * 60)


if __name__ == "__main__":
    main()

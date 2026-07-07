"""Reproducibly build the neonatal benchmark from ClinVar (via MyVariant.info).

For each neonatal gene we pull ClinVar-classified variants on both sides of the
VUS boundary (pathogenic / likely-pathogenic and benign / likely-benign), each
with a real ClinVar Variation ID. This is the labelled set the proxy validation
scores the tool against. Fully reproducible: re-run to regenerate.

    uv run python scripts/build_benchmark.py --out benchmark/benchmark.csv

Open public data only (ClinVar via MyVariant). No patient data.
"""

from __future__ import annotations

import argparse
import csv
import sys

import requests

BASE = "https://myvariant.info/v1/query"
UA = {"User-Agent": "neovus-kg/0.1 benchmark-builder"}

# Neonatal / early-infantile disease genes for the benchmark.
GENES = ["KCNQ2", "SCN2A", "KCNQ3", "CFTR", "GAA", "ACADM", "ARX", "CDKL5",
         "GALT", "KCNT1", "OTC", "PAH", "PDHA1", "POLG", "SCN1A", "SLC25A13",
         "SLC2A1", "STXBP1"]

PATHO = "Pathogenic OR Likely_pathogenic"
BENIGN = "Benign OR Likely_benign"

FIELDS = ("_id,clinvar.variant_id,clinvar.rcv.clinical_significance,"
          "clinvar.rcv.conditions.name,dbnsfp.hgvsp")

HEADER = ["gene", "variant_genomic_grch38", "clinvar_variation_id", "variant_protein",
          "disease", "clinvar_current_significance", "direction"]


def _first(v):
    return v[0] if isinstance(v, list) else v


def _condition(rcv) -> str:
    """First informative condition name across the RCV records."""
    recs = rcv if isinstance(rcv, list) else [rcv]
    for r in recs:
        conds = (r or {}).get("conditions")
        for c in (conds if isinstance(conds, list) else [conds]):
            name = (c or {}).get("name", "")
            if name and name.lower() not in ("not provided", "not specified"):
                return name
    return ""


def query(gene: str, sig: str, size: int) -> list[dict]:
    q = f'clinvar.gene.symbol:{gene} AND clinvar.rcv.clinical_significance:({sig})'
    r = requests.get(BASE, params={"q": q, "fields": FIELDS, "size": size,
                                   "assembly": "hg38"}, headers=UA, timeout=30)
    r.raise_for_status()
    return r.json().get("hits", [])


def rows_for(gene: str, per_side: int) -> list[dict]:
    out = []
    for sig, direction in ((PATHO, "pathogenic"), (BENIGN, "benign")):
        for h in query(gene, sig, per_side):
            cv = h.get("clinvar") or {}
            rcv = cv.get("rcv") or []
            sig_label = _first(rcv).get("clinical_significance") if rcv else ""
            out.append({
                "gene": gene,
                "variant_genomic_grch38": h["_id"],
                "clinvar_variation_id": cv.get("variant_id", ""),
                "variant_protein": _first((h.get("dbnsfp") or {}).get("hgvsp")) or "",
                "disease": _condition(rcv),
                "clinvar_current_significance": sig_label,
                "direction": direction,
            })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="benchmark/benchmark.csv")
    ap.add_argument("--per-side", type=int, default=4,
                    help="variants per gene per side (pathogenic / benign)")
    args = ap.parse_args()

    all_rows: list[dict] = []
    for g in GENES:
        try:
            rows = rows_for(g, args.per_side)
            all_rows += rows
            print(f"  {g}: {len(rows)} variants", file=sys.stderr)
        except Exception as e:
            print(f"  {g}: FAILED {e}", file=sys.stderr)

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(all_rows)
    print(f"\nWrote {len(all_rows)} variants across {len(GENES)} genes -> {args.out}")


if __name__ == "__main__":
    main()

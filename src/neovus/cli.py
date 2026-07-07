"""Terminal renderer for a NeoVUS report.

    uv run neovus chr20:g.63446815G>A --gene KCNQ2 --hpo "HP:0001250,HP:0010851"
"""

from __future__ import annotations

import argparse

from .pipeline import build_report
from .report import Report


def render(report: Report) -> str:
    v = report.variant
    L = ["=" * 72, f"NeoVUS-KG report — {v.gene}  {v.hgvs or v.genomic}", "=" * 72]

    if report.warnings:
        L.append("\n⚠  WARNINGS")
        L += [f"   - {w}" for w in report.warnings]

    L.append("\n▶ SUMMARY")
    L.append(f"   {report.summary or '(none)'}")

    L.append("\n▶ VARIANT ANNOTATION")
    for c in report.variant_evidence:
        L.append(f"     {'•' if c.is_supported else '‼'} {c.statement}")
        for ev in c.evidence:
            L.append(f"         ↳ {ev.cite()}")

    L.append("\n▶ CANDIDATE DISEASES (gene→disease, ranked)")
    if not report.candidate_diseases:
        L.append("     (none found)")
    for i, d in enumerate(report.candidate_diseases, 1):
        score = f"  match={d.score:.0%}" if d.score else ""
        L.append(f"   {i}. {d.name}  ({d.source_id}){score}")
        for c in d.claims:
            for ev in c.evidence:
                L.append(f"         ↳ {ev.cite()}")

    if report.checklist:
        L.append("\n▶ NEONATAL CHECKLIST")
        labels = {"symptom": "Symptoms/signs (HPO, by frequency)",
                  "workup": "Work-up", "follow-up": "Follow-up"}
        for cat in ("symptom", "workup", "follow-up"):
            items = [i for i in report.checklist if i.category == cat]
            if not items:
                continue
            L.append(f"   — {labels.get(cat, cat)} —")
            for item in items:
                L.append(f"     • {item.text}")
                for c in item.claims:
                    for ev in c.evidence:
                        L.append(f"         ↳ {ev.cite()}")

    if report.structural:
        L.append("\n▶ PROTEIN-STRUCTURAL CONTEXT")
        L.append(f"   {report.structural.summary}")
        for c in report.structural.claims:
            for ev in c.evidence:
                L.append(f"         ↳ {ev.cite()}")

    L.append("\n▶ AUDIT")
    L.append(f"   total citations: {len(report.all_evidence())} | "
             f"unsupported claims: {len(report.unsupported_claims())}")
    L.append("=" * 72)
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="NeoVUS-KG terminal report")
    ap.add_argument("variant", help="MyVariant id, e.g. chr20:g.63446815G>A")
    ap.add_argument("--gene", help="Gene symbol (inferred if omitted)")
    ap.add_argument("--hpo", default="", help="Comma-separated HPO terms")
    args = ap.parse_args()
    hpo = [t.strip() for t in args.hpo.split(",") if t.strip()]
    print(render(build_report(args.variant, gene=args.gene, hpo_terms=hpo)))


if __name__ == "__main__":
    main()

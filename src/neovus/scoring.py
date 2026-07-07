"""Aggregate in-silico evidence into a transparent pathogenic/benign direction.

This is NOT a classifier that replaces ACMG — it's an auditable summary of what the
public in-silico predictors collectively point to, with every contributing reason
listed. Used in the report ("evidence leans …") and by the proxy validation, which
checks this direction against ClinVar's eventual (re)classification.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Direction:
    call: str                       # "pathogenic" | "benign" | "uncertain"
    score: int                      # signed vote total
    reasons: list[str] = field(default_factory=list)


def evidence_direction(ann) -> Direction:
    """Vote from REVEL, AlphaMissense, CADD, and gnomAD frequency.

    Each predictor contributes ±1. Missense predictors are absent for non-missense
    variants, so CADD (defined genome-wide) and population frequency keep those from
    being uncalled.
    """
    score = 0
    reasons: list[str] = []

    if ann.revel is not None:
        if ann.revel > 0.5:
            score += 1; reasons.append(f"REVEL {ann.revel:.2f} > 0.5 (pathogenic-leaning)")
        else:
            score -= 1; reasons.append(f"REVEL {ann.revel:.2f} ≤ 0.5 (benign-leaning)")

    if ann.alphamissense_pred in ("P", "B"):
        if ann.alphamissense_pred == "P":
            score += 1; reasons.append("AlphaMissense = likely pathogenic")
        else:
            score -= 1; reasons.append("AlphaMissense = likely benign")

    if ann.cadd_phred is not None:
        if ann.cadd_phred >= 20:
            score += 1; reasons.append(f"CADD {ann.cadd_phred:.0f} ≥ 20 (deleterious-leaning)")
        else:
            score -= 1; reasons.append(f"CADD {ann.cadd_phred:.0f} < 20 (tolerated-leaning)")

    if ann.gnomad_af is not None and ann.gnomad_af >= 1e-3:
        score -= 1
        reasons.append(f"gnomAD AF {ann.gnomad_af:.1e} ≥ 1e-3 (too common for a severe neonatal disease)")

    call = "pathogenic" if score > 0 else "benign" if score < 0 else "uncertain"
    return Direction(call=call, score=score, reasons=reasons)

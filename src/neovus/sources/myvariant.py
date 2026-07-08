"""MyVariant.info client — the annotation workhorse.

One request aggregates the in-silico scores (CADD, REVEL, AlphaMissense), gnomAD
population frequency, and the ClinVar link that ACMG-style evidence needs. Each
extracted fact becomes a `Claim` carrying `Evidence` back to its source.

Docs: https://docs.myvariant.info/
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..evidence import Claim, Evidence
from ._http import first, get_json, max_num

BASE = "https://myvariant.info/v1"


@dataclass
class VariantAnnotation:
    variant_id: str                  # MyVariant _id, e.g. "chr20:g.63446815G>A"
    gene: str | None = None
    protein_change: str | None = None
    clinvar_id: int | None = None
    clinvar_significance: str | None = None
    cadd_phred: float | None = None
    revel: float | None = None
    alphamissense: float | None = None
    alphamissense_pred: str | None = None
    gnomad_af: float | None = None
    claims: list[Claim] = field(default_factory=list)
    raw: dict | None = None


def _clinvar_url(vid: int | None) -> str | None:
    return f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{vid}/" if vid else None


def _allele_freq(block) -> float | None:
    """Safely pull gnomAD allele frequency from a possibly-None/odd-shaped block."""
    af = block.get("af") if isinstance(block, dict) else None
    if isinstance(af, dict):
        val = af.get("af")
        return first(val) if isinstance(val, list) else val
    return None


def _clinvar_protein(clinvar: dict) -> str | None:
    """Canonical RefSeq protein change (p.…) from ClinVar's NP_ HGVS."""
    prot = ((clinvar.get("hgvs") or {}).get("protein"))
    for p in (prot if isinstance(prot, list) else [prot]) if prot else []:
        if isinstance(p, str) and ":p." in p:
            return p.split(":", 1)[1]
    return None


def annotate_variant(variant_id: str, assembly: str = "hg38") -> VariantAnnotation | None:
    """Annotate one variant by MyVariant id (e.g. 'chr20:g.63446815G>A')."""
    try:
        data = get_json(f"{BASE}/variant/{variant_id}", {"assembly": assembly})
    except Exception:
        return None
    if not data or "_id" not in data:
        return None

    clinvar = data.get("clinvar") or {}
    dbnsfp = data.get("dbnsfp") or {}
    am = dbnsfp.get("alphamissense") or {}

    rcv = clinvar.get("rcv") or []
    sig = None
    if isinstance(rcv, list) and rcv:
        head = first(rcv)
        sig = head.get("clinical_significance") if isinstance(head, dict) else None
    elif isinstance(rcv, dict):
        sig = rcv.get("clinical_significance")

    # Prefer the canonical RefSeq (NP_) protein change from ClinVar over the first
    # dbNSFP isoform, so display and residue→domain mapping use one numbering.
    protein_change = _clinvar_protein(clinvar) or first(dbnsfp.get("hgvsp"))

    cadd = max_num((data.get("cadd") or {}).get("phred")) or max_num((dbnsfp.get("cadd") or {}).get("phred"))
    revel = max_num((dbnsfp.get("revel") or {}).get("score"))
    am_score = max_num(am.get("score"))
    gnomad_af = _allele_freq(data.get("gnomad_genome")) or _allele_freq(data.get("gnomad_exome"))

    ann = VariantAnnotation(
        variant_id=data["_id"],
        gene=first(dbnsfp.get("genename")),
        protein_change=protein_change,
        clinvar_id=clinvar.get("variant_id"),
        clinvar_significance=sig,
        cadd_phred=cadd,
        revel=revel,
        alphamissense=am_score,
        alphamissense_pred=first(am.get("pred")),
        gnomad_af=gnomad_af,
        raw=data,
    )

    src = "rest:myvariant"
    mv_url = f"https://myvariant.info/v1/variant/{data['_id']}"
    if sig:
        ann.claims.append(Claim(f"ClinVar clinical significance: {sig}").add(
            Evidence("ClinVar", f"variation/{ann.clinvar_id}", _clinvar_url(ann.clinvar_id),
                     "aggregated ClinVar classification", retrieved=src)))
    if revel is not None:
        ann.claims.append(Claim(f"REVEL {revel:.3f} (>0.5 supports pathogenic)").add(
            Evidence("dbNSFP/REVEL", ann.variant_id, mv_url, "in-silico missense predictor", retrieved=src)))
    if am_score is not None:
        ann.claims.append(Claim(
            f"AlphaMissense {am_score:.3f} ({ann.alphamissense_pred or '?'}; P=likely pathogenic)").add(
            Evidence("AlphaMissense", ann.variant_id, mv_url, "in-silico missense predictor", retrieved=src)))
    if cadd is not None:
        ann.claims.append(Claim(f"CADD phred {cadd:.1f} (higher = more deleterious)").add(
            Evidence("CADD", ann.variant_id, mv_url, "in-silico deleteriousness", retrieved=src)))
    if gnomad_af is not None:
        ann.claims.append(Claim(
            f"gnomAD allele frequency {gnomad_af:.2e} ({'rare' if gnomad_af < 1e-4 else 'not rare'})").add(
            Evidence("gnomAD", ann.variant_id, mv_url, "population allele frequency", retrieved=src)))
    return ann

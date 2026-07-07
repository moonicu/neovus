"""Assemble an evidence-trailed Report for one variant.

Structured reasoning upstream, language only at the end:
  1. annotation ...... MyVariant (ClinVar, REVEL, AlphaMissense, CADD, gnomAD)
  2. diseases ........ HPO/Orphanet gene→disease, ranked by HPO-term overlap
  3. checklist ....... top disease's phenotypes, prioritised by frequency
  4. structural ...... UniProt domains + AlphaFold, residue→domain mapping
  5. summary ......... generated last
"""

from __future__ import annotations

import re

from .evidence import Claim, Evidence
from .report import (CandidateDisease, ChecklistItem, Report, StructuralImpact,
                     VariantInput)
from .scoring import evidence_direction
from .sources import alphafold, hpo, myvariant, uniprot

_TOP_DISEASES = 5
_TOP_PHENOTYPES = 12

# HPO categories that are clinical modifiers, not symptoms/signs — keep them out
# of the neonatal symptom checklist (they describe onset/inheritance, not findings).
_NON_CLINICAL_CATEGORIES = {
    "Inheritance", "Clinical modifier", "Clinical course", "Onset",
    "Frequency", "Blood group", "Past medical history",
}


def _residue(protein_change: str | None) -> int | None:
    if not protein_change:
        return None
    m = re.search(r"(\d+)", protein_change)
    return int(m.group(1)) if m else None


def build_report(variant_id: str, gene: str | None = None,
                 hpo_terms: list[str] | None = None) -> Report:
    ann = myvariant.annotate_variant(variant_id)
    gene = gene or (ann.gene if ann else None)

    report = Report(variant=VariantInput(
        gene=gene or "?", genomic=variant_id, hpo_terms=hpo_terms or []))
    if ann is None:
        report.warnings.append(f"Variant '{variant_id}' not found in MyVariant.info.")
        return report
    report.variant.hgvs = ann.protein_change
    report.variant_evidence = list(ann.claims)

    # Auditable direction: what the in-silico predictors collectively point to.
    direction = evidence_direction(ann)
    if direction.call != "uncertain" and direction.reasons:
        report.variant_evidence.append(Claim(
            f"Aggregated in-silico evidence leans {direction.call} "
            f"({'; '.join(direction.reasons)})").add(Evidence(
                "NeoVUS (derived)", ann.variant_id,
                f"https://myvariant.info/v1/variant/{ann.variant_id}",
                "vote over REVEL / AlphaMissense / CADD / gnomAD", retrieved="derived")))

    # Candidate diseases + checklist
    top_disease = None
    if gene:
        try:
            diseases = hpo.rank_diseases(hpo.gene_diseases(gene), hpo_terms)
        except Exception as e:
            diseases = []
            report.warnings.append(f"HPO gene→disease lookup failed for {gene}: {e}")
        for d in diseases[:_TOP_DISEASES]:
            report.candidate_diseases.append(CandidateDisease(
                name=d.name, source_id=d.id, score=d.match_score, claims=list(d.claims)))
        if diseases:
            top_disease = diseases[0]
    if top_disease is not None:
        report.checklist = _checklist_from_disease(top_disease)

    # Structural context
    if gene:
        try:
            prot = uniprot.lookup_gene(gene)
        except Exception as e:
            prot = None
            report.warnings.append(f"UniProt lookup failed for {gene}: {e}")
        if prot:
            residue = _residue(ann.protein_change)
            dom = uniprot.domain_at_residue(prot, residue)
            af = alphafold.lookup(prot.accession)
            if dom:
                where = (f"residue {residue} falls in {dom['type']} "
                         f"'{dom.get('description') or '?'}' ({dom['begin']}–{dom['end']})")
            elif residue:
                where = f"residue {residue} not within an annotated domain/TM feature"
            else:
                where = "residue position unavailable"
            structural = StructuralImpact(
                summary=f"{prot.name or gene} ({prot.accession}); {where}.",
                domain=(dom.get("description") if dom else None),
                claims=list(prot.claims))
            if af.claim:
                structural.claims.append(af.claim)
            report.structural = structural

    report.summary = _summarize(ann, report, top_disease)
    return report


def _checklist_from_disease(disease) -> list[ChecklistItem]:
    """Phenotypes of the top disease as neonatal symptom items, by HPO frequency."""
    clinical = [p for p in disease.phenotypes
                if (p.category or "") not in _NON_CLINICAL_CATEGORIES]
    phenos = sorted(clinical, key=lambda p: p.freq_rank, reverse=True)
    items: list[ChecklistItem] = []
    for p in phenos[:_TOP_PHENOTYPES]:
        freq = f" [{p.frequency}]" if p.frequency else ""
        ev = Evidence("HPO", p.hpo_id, hpo.term_url(p.hpo_id),
                      f"phenotype of {disease.name}{freq}", retrieved="rest:hpo-jax")
        items.append(ChecklistItem(text=f"{p.name}{freq}", category="symptom",
                                   claims=[Claim(f"{p.name} ({p.hpo_id})").add(ev)]))
    return items


def _summarize(ann, report: Report, top_disease) -> str:
    bits = [f"{report.variant.gene} {ann.protein_change or ann.variant_id}:"]
    if ann.clinvar_significance:
        bits.append(f"ClinVar reports this as {ann.clinvar_significance}.")
    scores = []
    if ann.revel is not None:
        scores.append(f"REVEL {ann.revel:.2f}")
    if ann.alphamissense is not None:
        scores.append(f"AlphaMissense {ann.alphamissense:.2f} ({ann.alphamissense_pred})")
    if ann.cadd_phred is not None:
        scores.append(f"CADD {ann.cadd_phred:.0f}")
    if scores:
        bits.append("In-silico: " + ", ".join(scores) + ".")
    if ann.gnomad_af is not None:
        bits.append(f"Population frequency {ann.gnomad_af:.1e}.")
    if top_disease is not None:
        lead = f"Top gene-linked condition: {top_disease.name}"
        if top_disease.match_score:
            lead += f" (phenotype match {top_disease.match_score:.0%})"
        bits.append(lead + ".")
    if report.structural:
        bits.append(report.structural.summary)
    bits.append("Every statement above links to its source; verify before clinical use.")
    return " ".join(bits)

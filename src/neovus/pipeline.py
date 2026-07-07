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

from .checklists import load_gene_checklist
from .evidence import Claim, Evidence
from .report import (CandidateDisease, ChecklistItem, Report, StructuralImpact,
                     VariantInput)
from .scoring import evidence_direction
from .sources import alphafold, hpo, myvariant, uniprot
from .sources.resolve import resolve

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


def _needs_gene(variant: str) -> bool:
    """A bare c./p. notation (no gene prefix) can't be placed without a gene."""
    return bool(re.match(r"^[cp]\.", variant.strip(), re.IGNORECASE)) and ":" not in variant


def build_report(variant: str, gene: str | None = None,
                 hpo_terms: list[str] | None = None) -> Report:
    variant = (variant or "").strip()
    report = Report(variant=VariantInput(
        gene=(gene or "?"), genomic=variant, hpo_terms=hpo_terms or []))
    if not variant:
        report.warnings.append("No variant entered. Enter e.g. c.629G>A, p.Arg210His, "
                               "rs796053235, or chr20:g.63444720C>T.")
        return report
    if not gene and _needs_gene(variant):
        report.warnings.append(f"'{variant}' is a bare {variant[:2]} notation — please also "
                               "enter the gene so it can be placed on the genome.")
        return report

    # Accept what's on the report (rsID / c.HGVS / p.HGVS / genomic) → MyVariant id.
    res = resolve(variant, gene)
    report.variant.genomic = res.variant_id or variant
    if res.variant_id is None:
        report.warnings.append(
            (res.note or f"Could not resolve '{variant}'.")
            + "  Check the gene symbol and notation (e.g. c.629G>A, p.Arg210His, rs#).")
        return report

    ann = myvariant.annotate_variant(res.variant_id)
    gene = gene or (ann.gene if ann else None)
    report.variant.gene = gene or "?"
    if ann is None:
        report.warnings.append(
            f"'{variant}' resolved to {res.variant_id} but is not in MyVariant.info.")
        return report
    # Prefer the canonical (RefSeq NP_) protein change from the recoder over the
    # first dbNSFP isoform, so display and residue→domain mapping use one numbering.
    protein_change = res.protein or ann.protein_change
    report.variant.hgvs = protein_change

    # Record the input normalization as its own auditable step.
    if res.method != "genomic" and res.note:
        report.variant_evidence.append(Claim(res.note).add(Evidence(
            "Ensembl Variant Recoder", res.source_notation,
            "https://rest.ensembl.org/variant_recoder", "input normalization (GRCh38)",
            retrieved="rest:ensembl")))
    report.variant_evidence += list(ann.claims)

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
        else:
            report.warnings.append(
                f"No gene→disease associations found for '{gene}' in HPO — "
                "check the gene symbol (HGNC).")
    if top_disease is not None:
        report.checklist = _checklist_from_disease(top_disease)
    # Curated work-up / follow-up actions for the gene (symptoms come from HPO above).
    if gene:
        report.checklist += load_gene_checklist(gene)

    # Structural context
    if gene:
        try:
            prot = uniprot.lookup_gene(gene)
        except Exception as e:
            prot = None
            report.warnings.append(f"UniProt lookup failed for {gene}: {e}")
        if prot:
            residue = _residue(protein_change)
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
            if dom and residue:
                report.headline.structure = f"residue {residue} · {_short_domain(dom)}"
            elif residue:
                report.headline.structure = f"residue {residue} · outside annotated domains"

    # Scannable header facts
    report.headline.clinvar_significance = ann.clinvar_significance
    report.headline.direction = direction.call
    report.headline.revel = ann.revel
    report.headline.alphamissense = ann.alphamissense
    report.headline.alphamissense_pred = ann.alphamissense_pred
    report.headline.cadd = ann.cadd_phred
    report.headline.gnomad_af = ann.gnomad_af
    if top_disease is not None:
        report.headline.top_condition = top_disease.name
        report.headline.top_condition_match = top_disease.match_score

    report.summary = _summarize(ann, report, top_disease)
    return report


def _short_domain(dom: dict) -> str:
    """Human-friendly domain label, e.g. 'voltage-sensor Segment S4'."""
    desc = dom.get("description") or dom.get("type") or "domain"
    # UniProt descriptions look like "Helical; Voltage-sensor; Name=Segment S4".
    name = None
    for part in desc.split(";"):
        part = part.strip()
        if part.startswith("Name="):
            name = part[5:].strip()
    parts = [p.strip() for p in desc.split(";") if p.strip() and not p.strip().startswith("Name=")]
    label = name or (parts[0] if parts else desc)
    if name and any("voltage-sensor" in p.lower() for p in parts):
        label = f"voltage-sensor {name}"
    return label


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
    bits = [f"{report.variant.gene} {report.variant.hgvs or ann.variant_id}:"]
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

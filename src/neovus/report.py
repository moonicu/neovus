"""The evidence-trailed report object.

One structured object the pipeline assembles and the UI renders. Every section is
built from `Claim`s so the evidence trail is intrinsic to the data model.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .evidence import Claim, Evidence


@dataclass
class VariantInput:
    gene: str
    hgvs: str | None = None       # protein change, e.g. "p.Arg210His"
    genomic: str | None = None    # e.g. "chr20:g.63446815G>A" (GRCh38)
    hpo_terms: list[str] = field(default_factory=list)


@dataclass
class CandidateDisease:
    name: str
    source_id: str                # ORPHA/OMIM/MONDO id
    score: float | None = None    # ranking score (provenance in `claims`)
    claims: list[Claim] = field(default_factory=list)


@dataclass
class ChecklistItem:
    text: str
    category: str                 # "symptom" | "workup" | "follow-up"
    claims: list[Claim] = field(default_factory=list)


@dataclass
class StructuralImpact:
    summary: str
    domain: str | None = None
    claims: list[Claim] = field(default_factory=list)
    # data for the protein-track visual
    accession: str | None = None
    length: int | None = None
    residue: int | None = None
    domains: list[dict] = field(default_factory=list)   # {type, description, begin, end}


@dataclass
class Headline:
    """Structured key facts for a scannable header (the UI renders these as
    badges + metrics instead of one long sentence)."""
    clinvar_significance: str | None = None
    direction: str | None = None            # pathogenic | benign | uncertain
    direction_score: int = 0                # signed vote total
    direction_reasons: list[str] = field(default_factory=list)
    revel: float | None = None
    alphamissense: float | None = None
    alphamissense_pred: str | None = None
    cadd: float | None = None
    gnomad_af: float | None = None
    top_condition: str | None = None
    top_condition_match: float | None = None
    structure: str | None = None            # short residue/domain phrase


@dataclass
class Report:
    variant: VariantInput
    headline: Headline = field(default_factory=Headline)
    variant_evidence: list[Claim] = field(default_factory=list)
    candidate_diseases: list[CandidateDisease] = field(default_factory=list)
    checklist: list[ChecklistItem] = field(default_factory=list)
    structural: StructuralImpact | None = None
    summary: str = ""
    warnings: list[str] = field(default_factory=list)

    def _all_claims(self) -> list[Claim]:
        claims: list[Claim] = list(self.variant_evidence)
        for d in self.candidate_diseases:
            claims += d.claims
        for item in self.checklist:
            claims += item.claims
        if self.structural:
            claims += self.structural.claims
        return claims

    def all_evidence(self) -> list[Evidence]:
        out: list[Evidence] = []
        for c in self._all_claims():
            out.extend(c.evidence)
        return out

    def unsupported_claims(self) -> list[Claim]:
        """Claims with no backing evidence — surfaced, never hidden."""
        return [c for c in self._all_claims() if not c.is_supported]

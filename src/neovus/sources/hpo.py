"""HPO / JAX ontology client — gene → diseases → phenotypes.

The JAX HPO network API returns, for a gene, its associated diseases (Orphanet/OMIM/
MONDO ids) and, for a disease, its phenotypes grouped by organ category with frequency
+ onset metadata. That metadata drives candidate-disease ranking and a phenotype-based
neonatal checklist. Every fact carries Evidence back to HPO and the source disease.

API: https://ontology.jax.org/api
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..evidence import Claim, Evidence
from ._http import get_json

BASE = "https://ontology.jax.org/api"

_FREQ_RANK = {
    "Obligate": 5, "Very frequent": 4, "Frequent": 3,
    "Occasional": 2, "Very rare": 1, "Excluded": 0,
}
_NEONATAL_HINTS = ("neonatal", "infantile", "congenital", "infancy", "newborn", "early-infantile")


def disease_url(disease_id: str) -> str:
    return f"https://hpo.jax.org/browse/disease/{disease_id}"


def term_url(hpo_id: str) -> str:
    return f"https://hpo.jax.org/browse/term/{hpo_id}"


@dataclass
class Phenotype:
    hpo_id: str
    name: str
    category: str | None = None
    frequency: str | None = None
    onset: str | None = None
    source_disease: str | None = None

    @property
    def freq_rank(self) -> int:
        return _FREQ_RANK.get(self.frequency or "", 0)


@dataclass
class Disease:
    id: str
    name: str
    mondo_id: str | None = None
    description: str | None = None
    phenotypes: list[Phenotype] = field(default_factory=list)
    match_score: float | None = None
    claims: list[Claim] = field(default_factory=list)

    @property
    def is_neonatal(self) -> bool:
        return any(h in self.name.lower() for h in _NEONATAL_HINTS)


def ncbi_gene_id(symbol: str) -> str | None:
    try:
        data = get_json(f"{BASE}/network/search/gene", {"q": symbol})
    except Exception:
        return None
    results = data.get("results") or []
    for r in results:
        if r.get("name", "").upper() == symbol.upper():
            return r.get("id")
    return results[0].get("id") if results else None


def gene_diseases(symbol: str) -> list[Disease]:
    """Diseases associated with a gene (phenotypes filled lazily in rank_diseases)."""
    gid = ncbi_gene_id(symbol)
    if not gid:
        return []
    data = get_json(f"{BASE}/network/annotation/{gid}")
    out: list[Disease] = []
    for d in data.get("diseases", []):
        dis = Disease(id=d["id"], name=d.get("name", "?"), mondo_id=d.get("mondoId"),
                      description=d.get("description"))
        dis.claims.append(Claim(f"{symbol} is associated with {dis.name}").add(
            Evidence("HPO/Orphanet", dis.id, disease_url(dis.id),
                     f"gene–disease association (via {gid})", retrieved="rest:hpo-jax")))
        out.append(dis)
    return out


def disease_phenotypes(disease_id: str) -> tuple[str | None, list[Phenotype]]:
    """(description, phenotypes) for a disease, flattened across organ categories."""
    data = get_json(f"{BASE}/network/annotation/{disease_id}")
    desc = (data.get("disease") or {}).get("description")
    phenos: list[Phenotype] = []
    for category, items in (data.get("categories") or {}).items():
        for it in items:
            meta = it.get("metadata") or {}
            phenos.append(Phenotype(
                hpo_id=it["id"], name=it.get("name", "?"), category=category,
                frequency=meta.get("frequency") or None,
                onset=meta.get("onset") or None,
                source_disease=disease_id,
            ))
    return desc, phenos


def rank_diseases(diseases: list[Disease], hpo_terms: list[str] | None) -> list[Disease]:
    """Rank candidates. With clinician HPO terms: by phenotype-term overlap.
    Otherwise: neonatal-relevance then phenotype breadth."""
    terms = {t.strip() for t in (hpo_terms or []) if t.strip()}
    for d in diseases:
        if not d.phenotypes:
            desc, phenos = disease_phenotypes(d.id)
            d.description = d.description or desc
            d.phenotypes = phenos
        if terms:
            overlap = terms & {p.hpo_id for p in d.phenotypes}
            d.match_score = len(overlap) / len(terms)
            if overlap:
                d.claims.append(Claim(
                    f"Matches {len(overlap)}/{len(terms)} supplied HPO terms: "
                    f"{', '.join(sorted(overlap))}").add(
                    Evidence("HPO", d.id, disease_url(d.id),
                             "phenotype overlap with clinician-supplied terms",
                             retrieved="rest:hpo-jax")))

    return sorted(diseases,
                  key=lambda d: (d.match_score or 0.0, d.is_neonatal, len(d.phenotypes)),
                  reverse=True)

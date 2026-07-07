"""UniProt client — gene symbol → reviewed protein entry + domain features."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..evidence import Claim, Evidence
from ._http import get_json

BASE = "https://rest.uniprot.org/uniprotkb"


@dataclass
class ProteinInfo:
    accession: str
    name: str | None = None
    length: int | None = None
    domains: list[dict] = field(default_factory=list)   # {type, description, begin, end}
    claims: list[Claim] = field(default_factory=list)


def lookup_gene(gene: str, organism_id: int = 9606) -> ProteinInfo | None:
    data = get_json(f"{BASE}/search", {
        "query": f"gene_exact:{gene} AND organism_id:{organism_id} AND reviewed:true",
        "fields": "accession,protein_name,length,ft_domain,ft_transmem",
        "format": "json", "size": 1,
    })
    results = data.get("results") or []
    if not results:
        return None
    e = results[0]
    acc = e["primaryAccession"]
    name = (((e.get("proteinDescription") or {}).get("recommendedName") or {})
            .get("fullName") or {}).get("value")
    length = (e.get("sequence") or {}).get("length")

    domains = []
    for feat in e.get("features", []):
        if feat.get("type") in ("Domain", "Transmembrane"):
            loc = feat.get("location", {})
            domains.append({
                "type": feat.get("type"),
                "description": feat.get("description"),
                "begin": (loc.get("start") or {}).get("value"),
                "end": (loc.get("end") or {}).get("value"),
            })

    info = ProteinInfo(accession=acc, name=name, length=length, domains=domains)
    url = f"https://www.uniprot.org/uniprotkb/{acc}"
    info.claims.append(Claim(
        f"UniProt {acc}: {name or gene}, {length or '?'} aa, "
        f"{len(domains)} annotated domain/TM features").add(
        Evidence("UniProt", acc, url, "protein entry + domains", retrieved="rest:uniprot")))
    return info


def domain_at_residue(info: ProteinInfo, residue: int | None) -> dict | None:
    """Which annotated domain/TM feature contains the given residue (1-based)?"""
    if residue is None:
        return None
    for d in info.domains:
        b, e = d.get("begin"), d.get("end")
        if isinstance(b, int) and isinstance(e, int) and b <= residue <= e:
            return d
    return None

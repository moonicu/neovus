"""AlphaFold client — UniProt accession → predicted-structure availability + links."""

from __future__ import annotations

from dataclasses import dataclass

from ..evidence import Claim, Evidence
from ._http import get_json

BASE = "https://alphafold.ebi.ac.uk/api"


@dataclass
class StructureInfo:
    accession: str
    available: bool
    model_url: str | None = None
    viewer_url: str | None = None
    claim: Claim | None = None


def lookup(accession: str) -> StructureInfo:
    viewer = f"https://alphafold.ebi.ac.uk/entry/{accession}"
    try:
        data = get_json(f"{BASE}/prediction/{accession}")
    except Exception:
        data = None
    if not data:
        return StructureInfo(accession, available=False, viewer_url=viewer)

    entry = data[0] if isinstance(data, list) and data else {}
    model_url = entry.get("pdbUrl") or entry.get("cifUrl")
    info = StructureInfo(accession, available=True, model_url=model_url, viewer_url=viewer)
    info.claim = Claim(f"AlphaFold predicted structure available for {accession}").add(
        Evidence("AlphaFold", accession, viewer, "predicted 3D model (domain-impact context)",
                 retrieved="rest:alphafold"))
    return info

"""Resolve a clinician's variant notation to a MyVariant genomic id.

A neonatologist reads a genetic report that says `KCNQ2 c.629G>A`, `p.Arg210His`,
or `rs796053235` — not a genomic coordinate. This resolver accepts what's actually
on the report and returns the `chrN:g.…` id MyVariant needs, using the Ensembl
Variant Recoder (which also gets strand right — KCNQ2 c.629G>A is genomic C>T).

API: https://rest.ensembl.org/variant_recoder
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import quote

from ._http import get_json

RECODER = "https://rest.ensembl.org/variant_recoder/human"

_GENOMIC_RE = re.compile(r"^chr[\dXYMT]+:g\.", re.IGNORECASE)
_CDNA_OR_PROT_RE = re.compile(r"^[cp]\.", re.IGNORECASE)
_NC_RE = re.compile(r"^NC_0*(\d+)\.\d+:g\.(.+)$")


@dataclass
class Resolved:
    variant_id: str | None          # chrN:g.… for MyVariant, or None if unresolved
    source_notation: str            # what the user typed (possibly gene-prefixed)
    method: str                     # "genomic" | "ensembl-variant-recoder"
    protein: str | None = None      # canonical p.XXX (RefSeq NP_) when available
    note: str | None = None


def _nc_to_chr(hgvsg: str) -> str | None:
    """NC_000020.11:g.63444720C>T → chr20:g.63444720C>T (GRCh38 RefSeq → UCSC)."""
    m = _NC_RE.match(hgvsg)
    if not m:
        return None
    num, rest = int(m.group(1)), m.group(2)
    chrom = {23: "X", 24: "Y", 12920: "MT"}.get(num, str(num))
    return f"chr{chrom}:g.{rest}"


def resolve(raw: str, gene: str | None = None) -> Resolved:
    """Normalise a report notation to a MyVariant id."""
    q = raw.strip()

    # Already a genomic MyVariant id — use directly.
    if _GENOMIC_RE.match(q):
        return Resolved(q, q, "genomic")

    # Bare c./p. notation → prefix the gene so the recoder can place it.
    query = q
    if gene and _CDNA_OR_PROT_RE.match(q):
        query = f"{gene}:{q}"

    try:
        data = get_json(f"{RECODER}/{quote(query, safe=':')}", {"fields": "hgvsg,hgvsp"})
    except Exception as e:
        return Resolved(None, query, "ensembl-variant-recoder",
                        note=f"could not resolve '{query}': {e}")

    hgvsgs: list[str] = []
    hgvsps: list[str] = []
    for item in data if isinstance(data, list) else []:
        for v in item.values():
            if isinstance(v, dict):
                hgvsgs += v.get("hgvsg") or []
                hgvsps += v.get("hgvsp") or []

    # Canonical protein change: prefer a RefSeq NP_ entry, take the p.… part.
    protein = None
    for h in hgvsps:
        if h.startswith("NP_") and ":p." in h:
            protein = h.split(":", 1)[1]
            break

    for h in hgvsgs:
        mv = _nc_to_chr(h)
        if mv:
            return Resolved(mv, query, "ensembl-variant-recoder", protein=protein,
                            note=f"'{query}' → {mv} (Ensembl Variant Recoder, GRCh38)")

    return Resolved(None, query, "ensembl-variant-recoder",
                    note=f"no chromosomal GRCh38 mapping found for '{query}'")

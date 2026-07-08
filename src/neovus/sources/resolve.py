"""Resolve a clinician's variant notation to a MyVariant genomic id.

A neonatologist reads a report that says `KCNQ2 c.629G>A`, `p.Arg210His`, or
`rs796053235` — not a genomic coordinate. We accept all of those.

Strategy (resilient to any one service being down):
  1. genomic `chrN:g.…`            → use directly, no network.
  2. everything else               → MyVariant.info first (ClinVar/dbSNP index;
                                      clinically flagged variants are in ClinVar),
  3. if MyVariant misses           → Ensembl Variant Recoder as a fallback (also
                                      handles novel variants not yet in ClinVar).

MyVariant is the primary because it stays up when Ensembl REST has outages, and
because it returns the canonical RefSeq protein change alongside the genomic id.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import quote

from ._http import get_json

MYVARIANT = "https://myvariant.info/v1"
RECODER = "https://rest.ensembl.org/variant_recoder/human"

_GENOMIC_RE = re.compile(r"^chr[\dXYMT]+:g\.", re.IGNORECASE)
_RSID_RE = re.compile(r"^rs\d+$", re.IGNORECASE)
_CDNA_RE = re.compile(r"^c\.", re.IGNORECASE)
_PROT_RE = re.compile(r"^p\.", re.IGNORECASE)
_NC_RE = re.compile(r"^NC_0*(\d+)\.\d+:g\.(.+)$")


@dataclass
class Resolved:
    variant_id: str | None          # chrN:g.… for MyVariant, or None if unresolved
    source_notation: str
    method: str                     # "genomic" | "myvariant" | "ensembl-variant-recoder"
    protein: str | None = None      # canonical p.XXX (RefSeq NP_) when available
    note: str | None = None


def _nc_to_chr(hgvsg: str) -> str | None:
    """NC_000020.11:g.63444720C>T → chr20:g.63444720C>T (RefSeq → UCSC, GRCh38)."""
    m = _NC_RE.match(hgvsg)
    if not m:
        return None
    num, rest = int(m.group(1)), m.group(2)
    chrom = {23: "X", 24: "Y", 12920: "MT"}.get(num, str(num))
    return f"chr{chrom}:g.{rest}"


def _myvariant_query(raw: str, gene: str | None) -> str:
    """Build the most specific MyVariant query for a notation."""
    q = raw.strip()
    if _RSID_RE.match(q):
        return f"dbsnp.rsid:{q.lower()}"
    if ":" in q and re.search(r":[cp]\.", q):          # transcript:c / gene:p already
        return f'"{q}"'
    if _PROT_RE.match(q) and gene:
        return f'clinvar.gene.symbol:{gene} AND dbnsfp.hgvsp:"{q}"'
    if _CDNA_RE.match(q) and gene:
        return f'{gene} AND "{q}"'
    return f'{gene} AND "{q}"' if gene else f'"{q}"'


def _canonical_protein(hit: dict) -> str | None:
    prot = (((hit.get("clinvar") or {}).get("hgvs") or {}).get("protein"))
    for p in (prot if isinstance(prot, list) else [prot]) if prot else []:
        if isinstance(p, str) and ":p." in p:
            return p.split(":", 1)[1]
    return None


def _resolve_myvariant(raw: str, gene: str | None) -> Resolved | None:
    query = _myvariant_query(raw, gene)
    try:
        data = get_json(f"{MYVARIANT}/query", {
            "q": query, "fields": "_id,clinvar.hgvs.protein", "size": 5, "assembly": "hg38"})
    except Exception:
        return None
    hits = data.get("hits") or []
    if not hits:
        return None
    hit = hits[0]
    note = f"'{raw}' → {hit['_id']} (MyVariant / ClinVar)"
    # A protein change can map to several distinct nucleotide/genomic variants.
    # Never silently pick one and pretend it's unique — say so.
    distinct = {h.get("_id") for h in hits if h.get("_id")}
    if len(distinct) > 1:
        note += (f"  ⚠ {len(distinct)} distinct variants match this notation; showing the "
                 "top-ranked — enter the cDNA (c.) or genomic notation to disambiguate.")
    return Resolved(hit["_id"], raw, "myvariant", protein=_canonical_protein(hit), note=note)


def _resolve_ensembl(raw: str, gene: str | None) -> Resolved | None:
    query = f"{gene}:{raw}" if gene and (_CDNA_RE.match(raw) or _PROT_RE.match(raw)) else raw
    try:
        data = get_json(f"{RECODER}/{quote(query, safe=':')}", {"fields": "hgvsg,hgvsp"})
    except Exception:
        return None
    hgvsgs, hgvsps = [], []
    for item in data if isinstance(data, list) else []:
        for v in item.values():
            if isinstance(v, dict):
                hgvsgs += v.get("hgvsg") or []
                hgvsps += v.get("hgvsp") or []
    protein = next((h.split(":", 1)[1] for h in hgvsps if h.startswith("NP_") and ":p." in h), None)
    for h in hgvsgs:
        mv = _nc_to_chr(h)
        if mv:
            return Resolved(mv, query, "ensembl-variant-recoder", protein=protein,
                            note=f"'{query}' → {mv} (Ensembl Variant Recoder, GRCh38)")
    return None


def resolve(raw: str, gene: str | None = None) -> Resolved:
    """Normalise a report notation to a MyVariant id, trying multiple services."""
    q = (raw or "").strip()
    if _GENOMIC_RE.match(q):
        return Resolved(q, q, "genomic")

    for strategy in (_resolve_myvariant, _resolve_ensembl):
        res = strategy(q, gene)
        if res and res.variant_id:
            return res

    return Resolved(None, q, "unresolved",
                    note=f"Could not resolve '{q}' from MyVariant or Ensembl — check the "
                         "gene symbol and notation (e.g. c.629G>A, p.Arg210His, rs#, chr20:g.…).")

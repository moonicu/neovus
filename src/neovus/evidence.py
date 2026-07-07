"""Evidence-trail primitives.

Auditability is a first-class feature: every fact NeoVUS asserts carries an
`Evidence` object saying which database, which record, and (ideally) a link the
clinician can open. A `Claim` bundles a statement with its supporting evidence;
a claim with no evidence is a red flag we surface rather than hide.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Evidence:
    """A single citation backing one claim.

    source:    database / API name, e.g. "ClinVar", "HPO", "UniProt", "AlphaFold".
    record_id: identifier within that source (ClinVar variation id, HPO term, accession).
    url:       resolvable link to the record, when available.
    detail:    short note on what this record contributes.
    retrieved: access path, e.g. "rest:myvariant" — lets us audit *how* it was reached.
    """

    source: str
    record_id: str
    url: str | None = None
    detail: str | None = None
    retrieved: str | None = None
    raw: dict[str, Any] | None = None

    def cite(self) -> str:
        s = f"{self.source}:{self.record_id}"
        if self.url:
            s += f" <{self.url}>"
        if self.detail:
            s += f" — {self.detail}"
        return s


@dataclass
class Claim:
    """An asserted fact plus the evidence backing it."""

    statement: str
    evidence: list[Evidence] = field(default_factory=list)

    @property
    def is_supported(self) -> bool:
        return len(self.evidence) > 0

    def add(self, ev: Evidence) -> "Claim":
        self.evidence.append(ev)
        return self

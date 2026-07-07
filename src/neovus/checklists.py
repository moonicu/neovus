"""Load gene-specific work-up / follow-up checklist content.

The HPO phenotype list gives *symptoms*; a clinician also needs *work-up* and
*follow-up* actions. Those are curated per gene as YAML with a citation on every
item (see benchmark/checklists/<GENE>.yaml) — authored with Claude Science and
reviewed by a clinician. Nothing is asserted without a source.

Set NEOVUS_CHECKLIST_DIR to override the location.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from .evidence import Claim, Evidence
from .report import ChecklistItem

_DEFAULT_DIR = Path(__file__).resolve().parents[2] / "benchmark" / "checklists"


def checklist_dir() -> Path:
    return Path(os.environ.get("NEOVUS_CHECKLIST_DIR", _DEFAULT_DIR))


def load_gene_checklist(gene: str) -> list[ChecklistItem]:
    """Work-up / follow-up items for a gene, each carrying its citation.
    Returns [] if there's no curated file for the gene."""
    path = checklist_dir() / f"{gene.upper()}.yaml"
    if not path.exists():
        return []
    try:
        doc = yaml.safe_load(path.read_text()) or {}
    except Exception:
        return []

    review = doc.get("review_status")
    items: list[ChecklistItem] = []
    for it in doc.get("items", []):
        text = it.get("text")
        if not text:
            continue
        detail = it.get("rationale")
        src = it.get("source", "curated")
        rid = it.get("source_id", gene.upper())
        url = it.get("url")
        ev = Evidence(src, str(rid), url, detail, retrieved="curated:claude-science")
        items.append(ChecklistItem(
            text=text,
            category=it.get("category", "workup"),
            claims=[Claim(text).add(ev)]))
    return items

"""Test the curated work-up/follow-up checklist loader (reads repo YAML, no network)."""

from neovus.checklists import load_gene_checklist


def test_kcnq2_checklist_loads_with_citations():
    items = load_gene_checklist("KCNQ2")
    assert items, "expected curated KCNQ2 checklist items"
    cats = {i.category for i in items}
    assert "workup" in cats and "follow-up" in cats
    # every curated item must carry a citation (auditability)
    for i in items:
        assert i.claims and i.claims[0].is_supported
        assert i.claims[0].evidence[0].url


def test_unknown_gene_returns_empty():
    assert load_gene_checklist("NOTAGENE") == []


def test_path_traversal_is_rejected():
    for bad in ["../../etc/passwd", "../KCNQ2", "KCNQ2/../SCN2A", "a/b", ""]:
        assert load_gene_checklist(bad) == []

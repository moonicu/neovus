"""Offline tests for scoring and variant-notation resolution (no network)."""

from types import SimpleNamespace

from neovus.scoring import evidence_direction
from neovus.sources.resolve import _nc_to_chr, resolve


def _ann(**kw):
    base = dict(revel=None, alphamissense_pred=None, cadd_phred=None, gnomad_af=None)
    base.update(kw)
    return SimpleNamespace(**base)


def test_direction_pathogenic():
    d = evidence_direction(_ann(revel=0.9, alphamissense_pred="P", cadd_phred=30))
    assert d.call == "pathogenic" and d.score == 3


def test_direction_benign_common():
    d = evidence_direction(_ann(revel=0.1, alphamissense_pred="B", cadd_phred=5, gnomad_af=0.02))
    assert d.call == "benign"


def test_direction_uncertain_when_no_signal():
    assert evidence_direction(_ann()).call == "uncertain"


def test_nc_to_chr():
    assert _nc_to_chr("NC_000020.11:g.63444720C>T") == "chr20:g.63444720C>T"
    assert _nc_to_chr("NC_000023.11:g.100A>G") == "chrX:g.100A>G"
    assert _nc_to_chr("not-an-nc") is None


def test_resolve_genomic_passthrough():
    r = resolve("chr20:g.63444720C>T")
    assert r.variant_id == "chr20:g.63444720C>T" and r.method == "genomic"

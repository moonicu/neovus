"""Offline tests for the evidence-trail data model (no network)."""

from neovus.evidence import Claim, Evidence
from neovus.report import CandidateDisease, Report, VariantInput


def test_evidence_cite():
    ev = Evidence("ClinVar", "variation/219241",
                  url="https://www.ncbi.nlm.nih.gov/clinvar/variation/219241/",
                  detail="pathogenic")
    c = ev.cite()
    assert "ClinVar:variation/219241" in c and "pathogenic" in c


def test_claim_support():
    c = Claim("variant is pathogenic")
    assert not c.is_supported
    c.add(Evidence("ClinVar", "variation/219241"))
    assert c.is_supported


def test_report_audit_counts():
    r = Report(variant=VariantInput(gene="KCNQ2", hgvs="p.L107F"))
    r.variant_evidence.append(Claim("sig: Pathogenic").add(Evidence("ClinVar", "219241")))
    r.candidate_diseases.append(CandidateDisease(
        "EIEE7", "OMIM:613720", claims=[Claim("bare assertion")]))
    assert len(r.all_evidence()) == 1
    assert len(r.unsupported_claims()) == 1
    assert r.unsupported_claims()[0].statement == "bare assertion"

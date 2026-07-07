"""NeoVUS-KG — Streamlit point-of-care UI.

Enter one VUS → a ranked, evidence-trailed interpretation where every claim links
back to its source database (auditability is the whole point).

    uv run streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import streamlit as st

from neovus.pipeline import build_report
from neovus.report import Report

st.set_page_config(page_title="NeoVUS-KG", page_icon="🧬", layout="wide")


def _claims_md(claims) -> str:
    lines = []
    for c in claims:
        mark = "" if c.is_supported else "⚠️ "
        lines.append(f"- {mark}{c.statement}")
        for ev in c.evidence:
            label = f"{ev.source}:{ev.record_id}"
            link = f"[{label}]({ev.url})" if ev.url else f"`{label}`"
            note = f" — {ev.detail}" if ev.detail else ""
            lines.append(f"    - ↳ {link}{note}")
    return "\n".join(lines)


def render(report: Report) -> None:
    v = report.variant
    st.subheader(f"{v.gene}  ·  {v.hgvs or v.genomic}")
    for w in report.warnings:
        st.warning(w)

    st.markdown(f"**Summary.** {report.summary or '_(none)_'}")
    st.caption("⚕️ Decision support on open public data — not a diagnosis. "
               "Verify every claim against its linked source before clinical use.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🧬 Variant annotation")
        st.markdown(_claims_md(report.variant_evidence) or "_none_")

        st.markdown("### 🩺 Candidate diseases")
        if not report.candidate_diseases:
            st.markdown("_none found_")
        for i, d in enumerate(report.candidate_diseases, 1):
            score = f" · match **{d.score:.0%}**" if d.score else ""
            with st.expander(f"{i}. {d.name}  ({d.source_id}){score}", expanded=(i == 1)):
                st.markdown(_claims_md(d.claims))

    with c2:
        st.markdown("### ✅ Neonatal checklist")
        if report.checklist:
            labels = {"symptom": "Symptoms / signs (HPO, by frequency)",
                      "workup": "Work-up", "follow-up": "Follow-up"}
            for cat in ("symptom", "workup", "follow-up"):
                items = [i for i in report.checklist if i.category == cat]
                if not items:
                    continue
                st.markdown(f"**{labels[cat]}**")
                for item in items:
                    st.markdown(_claims_md(item.claims))
        else:
            st.markdown("_none_")

        st.markdown("### 🧩 Protein-structural context")
        if report.structural:
            st.markdown(f"_{report.structural.summary}_")
            st.markdown(_claims_md(report.structural.claims))
        else:
            st.markdown("_none_")

    n_cite, n_bad = len(report.all_evidence()), len(report.unsupported_claims())
    st.divider()
    st.markdown(f"**Audit:** {n_cite} citations · "
                + (f"⚠️ {n_bad} unsupported claim(s)" if n_bad else "✅ 0 unsupported claims"))


st.title("🧬 NeoVUS-KG")
st.caption("Transparent, evidence-traceable interpretation of a single neonatal VUS.")

with st.sidebar:
    st.header("Enter a VUS")
    gene = st.text_input("Gene", value="KCNQ2")
    variant = st.text_input("Variant (as written on the report)", value="c.629G>A",
                            help="rsID, cDNA (c.), protein (p.), or genomic — "
                                 "e.g. c.629G>A, p.Arg210His, rs796053235, chr20:g.63444720C>T")
    hpo = st.text_input("HPO phenotype terms (optional, comma-separated)",
                        placeholder="HP:0001250, HP:0010851",
                        help="Supplying the baby's phenotypes re-ranks candidate diseases by match.")
    go = st.button("Interpret", type="primary", use_container_width=True)
    st.markdown("---")
    st.caption("Examples (gene · variant)")
    st.code("KCNQ2   c.629G>A        (p.Arg210His)\n"
            "KCNQ2   p.Arg201Cys\n"
            "SCN2A   c.2558G>A", language=None)

if go:
    if not variant.strip():
        st.error("Enter a variant, e.g. chr20:g.63446815G>A")
    else:
        terms = [t.strip() for t in hpo.split(",") if t.strip()]
        try:
            with st.spinner("Querying ClinVar / MyVariant / HPO / UniProt / AlphaFold…"):
                report = build_report(variant.strip(), gene=gene.strip() or None, hpo_terms=terms)
            render(report)
        except Exception as e:  # never crash the clinician's screen
            st.error(f"Something went wrong reaching the data sources ({type(e).__name__}). "
                     "Please try again in a moment — public APIs occasionally rate-limit.")
            st.caption(f"Detail: {e}")
else:
    st.info("Enter a variant in the sidebar and press **Interpret**.")

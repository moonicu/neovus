"""NeoVUS — Streamlit point-of-care UI.

Enter one VUS → a ranked, evidence-trailed interpretation where every claim links
back to its source database (auditability is the whole point).

    uv run streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import os
import sys

# Make the src-layout `neovus` package importable when the app is run directly
# (e.g. Streamlit Community Cloud), without needing an editable install.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
import streamlit.components.v1 as components

from neovus import visuals
from neovus.pipeline import build_report
from neovus.report import Report


def _svg(markup: str, height: int) -> None:
    components.html(f'<div style="font-family:sans-serif">{markup}</div>', height=height)

st.set_page_config(page_title="NeoVUS", page_icon="🧬", layout="wide",
                   initial_sidebar_state="expanded")

# Keep everything within the viewport on narrow (mobile) screens — no right-edge clipping.
st.markdown("""
<style>
[data-testid="stAppViewContainer"], .main, .block-container { overflow-x: hidden !important; }
.block-container { padding-left: 1rem !important; padding-right: 1rem !important; max-width: 100%; }
svg, iframe { max-width: 100% !important; }
[data-testid="stImage"] img { max-width: 100% !important; height: auto; }
pre, code { white-space: pre-wrap !important; word-break: break-word !important; }
[data-testid="stExpander"] summary p, [data-testid="stMarkdownContainer"] p { overflow-wrap: anywhere; }
</style>
""", unsafe_allow_html=True)


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


def _sig_color(sig: str | None) -> str:
    s = (sig or "").lower()
    if "pathogenic" in s and "benign" not in s:
        return "red"
    if "benign" in s:
        return "green"
    if "conflict" in s or "uncertain" in s:
        return "orange"
    return "gray"


def _dir_color(d: str | None) -> str:
    return {"pathogenic": "red", "benign": "green"}.get(d or "", "gray")


def render(report: Report) -> None:
    v = report.variant
    h = report.headline
    st.subheader(f"{v.gene}  ·  {v.hgvs or v.genomic}")
    st.caption(f"{v.genomic} · GRCh38" + (f"  ·  HPO: {', '.join(v.hpo_terms)}" if v.hpo_terms else ""))

    for w in report.warnings:
        st.warning(w)

    # Classification banner
    banner = []
    if h.clinvar_significance:
        banner.append(f"**ClinVar:** :{_sig_color(h.clinvar_significance)}[{h.clinvar_significance}]")
    if h.direction:
        banner.append(f"**Evidence leans:** :{_dir_color(h.direction)}[{h.direction}]")
    if banner:
        st.markdown("　·　".join(banner))

    # Verdict gauge + in-silico threshold bars
    gcol, scol = st.columns([1, 1])
    with gcol:
        _svg(visuals.verdict_gauge_svg(report), height=80)
        if h.gnomad_af is not None:
            st.caption(f"gnomAD allele frequency: {h.gnomad_af:.1e}")
    with scol:
        bars = visuals.score_bars_svg(report)
        if bars:
            _svg(bars, height=108)

    with st.expander("ℹ️ What do these scores mean?"):
        st.markdown(
            "- **REVEL** (0–1): ensemble **missense** pathogenicity score combining 13 predictors. "
            "**> 0.5** leans pathogenic, **> 0.7** stronger. Missense variants only.\n"
            "- **AlphaMissense** (0–1): DeepMind's missense predictor. Class **P** = likely pathogenic, "
            "**B** = likely benign, **A** = ambiguous (**> 0.564** → likely pathogenic). Missense only.\n"
            "- **CADD** (phred): **genome-wide** deleteriousness — works for any variant type. "
            "**≥ 20** = among the top 1% most deleterious, **≥ 30** = top 0.1%.\n"
            "- **gnomAD AF**: population **allele frequency**. Very rare (**< 0.0001**) is consistent "
            "with a severe neonatal-onset disease; common variants are usually benign.\n\n"
            "_These are computational predictors, not proof. NeoVUS shows them side-by-side with their "
            "thresholds so you can weigh the evidence — it does not compute an ACMG classification._")

    if h.top_condition:
        match = f"  ·  phenotype match **{h.top_condition_match:.0%}**" if h.top_condition_match else ""
        st.markdown(f"**Top condition:** {h.top_condition}{match}")

    # Protein-domain lollipop (where the variant lands)
    track = visuals.protein_track_svg(report)
    if track:
        _svg(track, height=120)

    st.caption("⚕️ Decision support on open public data — not a diagnosis. "
               "Verify every claim against its linked source before clinical use.")

    if report.summary:
        with st.expander("Plain-language summary"):
            st.write(report.summary)

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
                if d.phenotypes:
                    st.markdown("**Associated phenotypes** (HPO, by frequency):")
                    for p in d.phenotypes:
                        freq = f" · _{p['frequency']}_" if p.get("frequency") else ""
                        st.markdown(f"- [{p['name']}](https://hpo.jax.org/browse/term/{p['hpo_id']})"
                                    f" `{p['hpo_id']}`{freq}")

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

    dot = visuals.disease_graph_dot(report)
    if dot:
        st.markdown("### 🕸️ Gene → disease → phenotype")
        st.caption("How the interpretation is reasoned: the gene links to its candidate diseases "
                   "(edge = phenotype match); the top-ranked disease links to its key phenotypes.")
        st.graphviz_chart(dot, use_container_width=True)

    n_cite, n_bad = len(report.all_evidence()), len(report.unsupported_claims())
    st.divider()
    st.markdown(f"**Audit:** {n_cite} citations · "
                + (f"⚠️ {n_bad} unsupported claim(s)" if n_bad else "✅ 0 unsupported claims"))

    from neovus.htmlreport import report_html
    fname = f"neovus_{report.variant.gene}_{(report.variant.hgvs or 'report')}.html".replace(" ", "")
    st.download_button("⬇️ Download printable report (HTML → print to PDF)",
                       data=report_html(report), file_name=fname, mime="text/html")


st.title("🧬 NeoVUS")
st.caption("Transparent, evidence-traceable interpretation of a single neonatal VUS.")
st.caption("📱 On a phone? Tap **»** (top-left) to open the input panel.")

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
    st.markdown("---")
    st.markdown("💬 **Feedback / questions**  \n"
                "[neovus.tool@gmail.com](mailto:neovus.tool@gmail.com?subject=NeoVUS%20feedback)")

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
    st.info("👈 Enter a VUS in the input panel, then press **Interpret**.\n\n"
            "On a phone, tap the **»** arrow at the top-left to open the panel.")

st.divider()
st.caption(
    "NeoVUS · open source: [github.com/moonicu/neovus](https://github.com/moonicu/neovus) · "
    "💬 Feedback: [neovus.tool@gmail.com](mailto:neovus.tool@gmail.com?subject=NeoVUS%20feedback) · "
    "Open public data — not a diagnosis, not a medical device.")

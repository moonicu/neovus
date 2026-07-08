# NeoVUS

**Transparent, evidence-traceable interpretation of a single neonatal VUS (variant of uncertain significance).**

A point-of-care tool for NICU pediatricians / neonatologists. Enter one variant flagged in a
neonatal genomic report — as written on the report (`c.629G>A`, `p.Arg210His`, an rsID, or a
genomic coordinate) — and get back candidate diseases, a neonatal clinical checklist, protein-
structural context, and a plain-language summary, where **every claim links back to its source
database** so the clinician can verify rather than trust a black box.

> Built for **Built with Claude: Life Sciences** (Jul 7–13, 2026), Builder track. Open public data only.
> Not a medical device — decision support only (see `DISCLAIMER.md`).

## Why

A neonatologist in the NICU who hits a VUS has no neonatal-specific, point-of-care tool to interpret
it — whole-exome ranking tools (Exomiser, AMELIE) solve a different problem, and variant databases
(VarSome, Franklin) are built for genetics professionals, not the bedside. NeoVUS interprets ONE
already-flagged variant, for the clinician, with auditability as a first-class feature.

## What it does

**Input:** one variant in whatever notation the report uses, optionally a few HPO phenotype terms.
**Output** — a structured, evidence-trailed report:

1. **Variant annotation** — ClinVar significance + in-silico scores (REVEL, AlphaMissense, CADD) +
   gnomAD frequency, plus an auditable *evidence-direction* vote (leans pathogenic / benign).
2. **Candidate diseases** — gene→disease→phenotype (HPO/Orphanet), re-ranked by how well the baby's
   HPO terms match each disease.
3. **Neonatal checklist** — symptoms/signs (HPO, by frequency) **plus curated work-up & follow-up**
   actions, each cited (GeneReviews / PubMed).
4. **Protein-structural impact** — the residue mapped onto UniProt domains + AlphaFold context.
5. **Plain-language summary** — every statement carrying an evidence trail (DB + record + link).

Visuals: a **protein-domain lollipop** (where the variant lands), **in-silico threshold bars**, a
**benign↔pathogenic verdict gauge**, and a **gene→disease→phenotype graph**.

**Design principle:** structured/algorithmic reasoning upstream; language generation only for the
final explanatory layer. Auditability first — the report tracks its own citation count and flags any
unsupported claim.

## Open-data proxy validation

On neonatal variants that ClinVar **reclassified** across the VUS boundary (VUS → pathogenic/benign),
does NeoVUS's transparent in-silico evidence agree with the *new* classification? No ClinVar label is
used as a feature — only REVEL / AlphaMissense / CADD / gnomAD.

| Set | Direction agreement | Pathogenic precision |
| --- | --- | --- |
| Reclassified subset (n=46 callable) | **84.8%** | **100%** |
| All benchmark variants (n=100 callable) | 90.0% | 100% |

Reproduce: `uv run python scripts/build_benchmark.py` then `uv run python scripts/validate.py`.

## Two Claude products, each for what it's best at

- **Claude Code** built the software: REST clients, pipeline, ranking, visuals, validation, UI.
- **Claude Science** curated, at build time, the knowledge that isn't in any single API: the
  **reclassification benchmark** (ClinVar history) and the **work-up/follow-up checklists** for 18
  neonatal genes (from GeneReviews/PubMed, every item cited, clinician-review flagged).

The runtime tool depends only on **public REST APIs** (reproducible, no local daemon):
ClinVar · MyVariant.info · HPO (JAX) · Orphanet · UniProt · AlphaFold · Ensembl Variant Recoder.

## Quickstart

```bash
uv venv && uv pip install -e .            # or: python -m venv .venv && pip install -e .
uv run neovus "c.629G>A" --gene KCNQ2 --hpo "HP:0001250,HP:0010851"
uv run streamlit run app/streamlit_app.py
```

## Deploy (free, public URL)

The app is Streamlit-Community-Cloud-ready (`app/streamlit_app.py`, `requirements.txt`, no secrets):
push this repo to GitHub, then on [share.streamlit.io](https://share.streamlit.io) point a new app at
`app/streamlit_app.py` (Python 3.12).

## Layout

```
src/neovus/          core package
  sources/           REST clients (MyVariant, HPO, UniProt, AlphaFold, Ensembl resolver)
  evidence.py        evidence-trail primitives (source, record id, url)
  report.py          the evidence-trailed report object
  pipeline.py        assembly: resolve → annotate → diseases → checklist → structural → summary
  scoring.py         auditable in-silico direction vote
  visuals.py         SVG/DOT generators (lollipop, bars, gauge, graph)
  cli.py             terminal report renderer
app/                 Streamlit point-of-care UI
benchmark/           reclassification benchmark + per-gene cited checklists
scripts/             reproducible benchmark builder + proxy validation
tests/               tests
```

## Limitations (honest)

- The **direction vote is a transparent heuristic, not ACMG** — an equal-weight vote over
  REVEL/AlphaMissense/CADD/gnomAD. CADD is defined genome-wide, so for non-missense variants
  (no REVEL/AlphaMissense) the call leans on CADD alone and is weaker; gnomAD only ever votes
  toward benign. It summarises public evidence for the clinician to weigh — it does not classify.
- **Structural mapping** assumes the RefSeq protein numbering matches the UniProt canonical isoform;
  where isoforms differ, the residue→domain position can be off. Treat the lollipop as context.
- **Work-up/follow-up checklists** are Claude-Science-curated drafts, every item cited but flagged
  *clinician-review*; verify before use.
- Variant resolution favours variants known to **ClinVar/dbSNP**; a truly novel variant falls back to
  the Ensembl Variant Recoder and may not resolve during an Ensembl outage.
- Not SpliceAI-aware yet; splicing VUS are under-served.

## License

MIT.

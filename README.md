# NeoVUS-KG

**Transparent, evidence-traceable interpretation of a single neonatal VUS (variant of uncertain significance).**

A point-of-care tool for NICU pediatricians / neonatologists. Enter one variant flagged in a
neonatal genomic report and get back candidate diseases, a neonatal clinical checklist, protein-
structural context, and a plain-language summary — where **every claim links back to its source
database** so the clinician can verify rather than trust a black box.

> Built for **Built with Claude: Life Sciences** (Jul 7–13, 2026), Builder track. Open public data only.
> Not a medical device (see `DISCLAIMER.md`).

## Why

A neonatologist in the NICU who hits a VUS has no neonatal-specific, point-of-care tool to interpret
it — whole-exome ranking tools (Exomiser, AMELIE) solve a different problem. NeoVUS-KG interprets ONE
already-flagged variant, with auditability as a first-class feature.

## What it does

**Input:** one variant (gene + genomic/HGVS), optionally a few HPO phenotype terms.
**Output** — a structured, evidence-trailed report:

1. **Candidate diseases** linked to the gene, ranked (by HPO-term match when phenotypes are given).
2. **Neonatal checklist** — phenotypes/work-up prioritised by frequency.
3. **Protein-structural impact** — domain location + AlphaFold context.
4. **Plain-language summary** — each claim carrying an evidence trail (DB + record + link).

**Design principle:** structured/algorithmic reasoning upstream; language generation only for the
final explanatory layer. Auditability first.

## Data sources (open / public, via direct REST)

ClinVar · MyVariant.info (CADD/REVEL/AlphaMissense/gnomAD) · HPO (JAX) · Orphanet · UniProt · AlphaFold.

Claude Science is used at build time to curate the benchmark and clinical-checklist content (cited);
the runtime tool queries public REST APIs directly for reproducibility.

## Quickstart

```bash
uv venv && uv pip install -e .            # or: python -m venv .venv && pip install -e .
uv run neovus "chr20:g.63446815G>A" --gene KCNQ2 --hpo "HP:0001250,HP:0010851"
uv run streamlit run app/streamlit_app.py
```

## Layout

```
src/neovus/          core package
  sources/           REST clients (MyVariant, HPO, UniProt, AlphaFold) — each returns Evidence
  evidence.py        evidence-trail primitives (source, record id, url)
  report.py          the evidence-trailed report object
  pipeline.py        assembly: annotate → diseases → checklist → structural → summary
  cli.py             terminal report renderer
app/                 Streamlit point-of-care UI
benchmark/           neonatal gene/variant benchmark + checklist content
scripts/             reproducible benchmark builder + validation
tests/               tests
```

## License

MIT.

# NeoVUS-KG — Claude Code Entry Guide (Hackathon Build)

> This file orients Claude Code for the **Built with Claude: Life Sciences** hackathon (Jul 7–13).
> Track: **Builder**. Goal: working software that outlasts the week, plus an open-data validation.

---

## What we're building (one sentence)

A point-of-care tool where a clinician enters **a single VUS** (variant of uncertain significance) found in a neonatal genomic report and gets back a **transparent, evidence-traceable interpretation**: candidate diseases, a neonatal clinical checklist, protein-structural context, and a plain-language report — with every claim linking back to its source database.

## Who it's for

Pediatricians / neonatologists in the NICU who hit a VUS and have no neonatal-specific, point-of-care tool to interpret it. Not bioinformaticians running whole-exome pipelines.

## What it is NOT (scope guardrails)

- **Not** a whole-exome variant *ranking/diagnosis* tool (that's Exomiser / AMELIE / DeepBD's job — a different task). We interpret ONE already-flagged VUS.
- **Not** a trained ML ranking model (no large in-house training cohort in this week).
- **Not** using any patient / institutional / identifiable data. **Open public data only.**

---

## The task, precisely

Input: one variant (gene + HGVS or genomic coordinates), optionally a few HPO phenotype terms.
Output: a structured report containing —
1. **Candidate diseases** linked to that gene (ranked), via gene→disease→phenotype graph.
2. **Neonatal clinical checklist** — associated symptoms, suggested work-up, follow-up items.
3. **Protein-structural impact** — domain location, conservation, AlphaFold context.
4. **Plain-language summary report**, every claim carrying an **evidence trail** (which DB, which record) so the clinician can verify rather than trust a black box.

Design principle: **structured/algorithmic reasoning upstream, language generation only for the final explanatory layer.** Auditability first (this mirrors the SHAP-transparency philosophy from the applicant's prior published clinical tool).

---

## Data sources (all open / public)

| Source | Used for |
| --- | --- |
| ClinVar | variant classification, **reclassification history** (key for validation) |
| ClinGen | gene–disease validity, dosage sensitivity |
| OMIM | gene–phenotype relationships |
| HPO | phenotype terms + phenotype similarity |
| Orphanet | rare-disease associations |
| gnomAD | population allele frequency |
| UniProt | protein domains / annotations |
| AlphaFold | 3D structure / domain-impact context |
| DECIPHER | phenotype-linked variant data |
| In-silico scores | CADD, REVEL, AlphaMissense, SpliceAI |

Note: Ensembl REST API was used in the prior prototype for annotation lookups — reuse where sensible.

## Scope for the week (bounded, so it's finishable solo)

Benchmark set of **~50–100 well-characterized neonatal-disease-associated genes/variants**, drawn from public ClinVar reclassification records. Not genome-wide. Start with a handful of clean example genes (e.g. KCNQ2 — neonatal epileptic encephalopathy, well-annotated, rich structure) before scaling.

---

## Deliverables (definition of done)

1. **Working web app (Streamlit)** — enter a VUS → get the structured checklist + report with visible evidence trail. Clinician-usable without bioinformatics support.
2. **Open-data proxy validation** — using ClinVar variants that were reclassified (VUS → pathogenic/benign) over time, check that the tool surfaces the right disease/direction. Report baseline Top-1 / Top-5 recall and precision.
3. **Open-source repo** on GitHub (github.com/moonicu) with README, reproducible, MIT/appropriate license.

## Tech stack

- **Language:** Python
- **Pipeline:** DB/API queries → annotation → gene-phenotype-disease graph traversal → HPO similarity → AlphaFold domain summary → report assembly
- **Web:** Streamlit (applicant has shipped a bilingual Streamlit clinical app before — reuse patterns)
- **Compute:** Claude Science connectors for genomics/proteomics + AlphaFold; heavy structural work can go to Modal if needed

---

## Suggested 7-day plan

- **Day 1–2:** Open-data backbone. Wire up ClinVar / HPO / OMIM / gnomAD / UniProt / AlphaFold access into a queryable layer. Pick the ~50–100 gene/variant benchmark. Stand up repo + .gitignore.
- **Day 3–4:** Interpretation pipeline. Variant annotation (ACMG evidence + CADD/REVEL/AlphaMissense), gene→disease→phenotype traversal, HPO similarity, AlphaFold domain-impact summary. Assemble the evidence-trailed report object.
- **Day 5:** Streamlit interface. Query box → structured checklist + report, evidence trail exposed. (Familiar ground.)
- **Day 6:** Proxy validation on ClinVar reclassification events. Compute Top-1/Top-5 recall, precision. Sanity-check direction.
- **Day 7:** Polish, README, open-source release, short demo/writeup for submission.

---

## Working preferences (for Claude Code)

- The researcher is a **neonatologist / clinician**, strong on clinical judgment, comfortable with Python/R at a practical (not systems-engineering) level. Explain non-obvious code choices briefly.
- **Never** touch patient/institutional data. If a file looks like real patient data (patient_*.json, variants_*.csv from the clinic), do NOT commit it — it belongs in .gitignore.
- Prefer small, working increments over big rewrites. Get a thin end-to-end slice working early (one gene → full report), then broaden.
- Respect the scope guardrails above; don't drift toward whole-exome ranking or a trained model.
- Keep the evidence trail / auditability as a first-class feature, not an afterthought.

## First actions for Claude Code

1. Create the project structure (e.g. `src/`, `data/`, `benchmark/`, `app/`, `tests/`) and a `.gitignore` that excludes patient data, venvs, caches, and generated reports.
2. Confirm which data sources are reachable from here (Claude Science connectors vs. direct REST APIs) and which need keys.
3. Build a thin vertical slice: one benchmark gene (e.g. KCNQ2) → annotate one variant → produce a minimal evidence-trailed report in the terminal. Then we wrap it in Streamlit.

---

## Context: this is also a longer research project

Outside the hackathon, NeoVUS is a planned clinical study (institutional NGS cohort validation, IRB, multi-site VUS case contribution). For THIS WEEK, ignore the IRB/clinical-study track and build the open-data tool. The hackathon prototype becomes the foundation the later study builds on.

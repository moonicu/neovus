# NeoVUS — Research & Publication Roadmap (record only)

> Forward-looking notes for turning the hackathon prototype into publishable research.
> Not part of the hackathon deliverable; recorded for later. Written 2026-07-08.

## Positioning

Frame the hackathon prototype as **infrastructure for a clinical validation study**, not as
"the paper" itself. The tool becomes publishable the moment it is run on real cases and
evaluated — the software alone is at best an *application note*.

- **As-is publication value:** low–moderate (software/application note only).
- **With a clinical cohort study:** moderate–high (clinical-informatics contribution in an
  underserved niche: neonatal, point-of-care, transparency-first).

## Why the current prototype is not yet a strong paper

1. Core contribution is **integration, not a new method** — aggregates ClinVar / MyVariant /
   HPO / UniProt / AlphaFold; the direction vote is a simple ensemble (low novelty).
2. **Crowded field** — VarSome, Franklin, Exomiser, LIRICAL, InterVar. "Another aggregator"
   invites the reviewer's first question: what's new?
3. **Validation limits / circularity** — candidate-disease recall is near-trivial (diseases
   derive from the gene); the direction vote largely recapitulates that REVEL/AlphaMissense
   already predict pathogenicity. Benchmark is small and LLM-curated (not an expert gold
   standard). No head-to-head vs existing tools.
4. **Checklist content is secondary** (GeneReviews summaries), not new knowledge.

## Publication paths

### Path A — Clinical utility study (strongest; matches the planned IRB cohort) ⭐
Run NeoVUS on real NICU VUS cases from the institutional NGS cohort. Endpoints:
- Does it improve neonatologists' **interpretation time / accuracy / decision confidence**
  vs the standard workflow? (pre/post or usability study)
- Retrospectively, on reclassified cases, did the tool **flag the correct direction early**?
- Target venues: *Genetics in Medicine*, *npj Genomic Medicine*, *JAMIA*, *JMIR*.

### Path B — Rigorous validation study (methods)
Promote the 84.8% proxy result into real research: larger N, **expert-verified** benchmark,
benchmarking vs ACMG / VarSome / InterVar, include splicing, remove circularity,
calibration + statistics (ROC, CIs). Target: *Human Mutation*, *Genetics in Medicine*.

### Path C — Transparency / explainability framing (leverages prior SHAP work)
Extend the applicant's SHAP-transparency philosophy to genomic clinical decision support:
"audit-first, evidence-traceable decision support for neonatal VUS." Novelty is in the
research narrative, not the code.

## What must be added before publication (checklist)

- [ ] **Real clinical cases + clinician evaluation** (currently empty — highest priority)
- [ ] **Expert-verified gold-standard benchmark** (replace/validate the LLM-curated set)
- [ ] **Head-to-head comparison** vs VarSome / InterVar / Exomiser
- [ ] **Statistical rigor** for the direction call: calibration, ROC/AUC, CIs, de-circularized design
- [ ] **Clinician validation of the work-up/follow-up checklists** (ideally multi-site)
- [ ] Splicing awareness (SpliceAI) and non-missense handling
- [ ] Structural mapping validated against isoform/numbering mismatches

## Known methodological weaknesses to fix (from the code review)

- Direction vote is CADD-weighted and coarse; document/curtail CADD-alone calls; near-never
  returns "uncertain."
- RefSeq↔UniProt numbering mismatch can misplace the residue on the domain track.
- Variant resolution favors ClinVar/dbSNP-known variants; novel variants depend on Ensembl.
- ClinVar significance surfaces only the first RCV (hides conflicts).

## Concrete next research steps (rough order)

1. IRB / data-use approval for the institutional neonatal VUS cohort.
2. Assemble an expert-verified neonatal benchmark (variants + reclassification + phenotypes).
3. Re-run validation rigorously with baselines and statistics (Path B).
4. Design the clinician utility study (Path A): endpoints, sample size, workflow integration.
5. Collect usability feedback from the deployed app (already open at neovus.streamlit.app) as
   preliminary UX data.
6. Write up with the transparency/auditability framing (Path C) as the through-line.

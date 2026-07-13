# Submission materials (Built with Claude: Life Sciences — Builder track)

Deadline: **Mon Jul 13, 9:00 PM ET = Tue Jul 14, 10:00 AM KST**. Submit via the CV platform:
3-min demo video + open-source repo + written summary.

## Written summary (≈190 words)

NeoVUS is a point-of-care tool for NICU clinicians who hit a variant of uncertain significance (VUS)
in a neonatal genomic report. Existing tools either rank variants across a whole exome (Exomiser) or
serve genetics professionals (VarSome); none give a neonatologist an actionable, auditable
interpretation of one already-flagged variant. NeoVUS takes the variant as written on the report
(c./p. HGVS, rsID, or coordinate) and returns: ClinVar significance and in-silico evidence with a
transparent pathogenic/benign direction vote; gene→disease candidates re-ranked by the baby's
phenotypes; a neonatal checklist of symptoms plus cited work-up and follow-up actions; and the
variant mapped onto its protein domain. Every statement links to its source database — the report
tracks its own citations and flags unsupported claims. Built with Claude Code; the reclassification
benchmark and clinical checklists were curated with Claude Science (all cited). On ClinVar-reclassified
neonatal variants, NeoVUS's evidence agrees with the eventual reclassification 84.8% of the time at
100% pathogenic precision. Open-source (MIT), reproducible, open public data only.

## 3-minute demo video script

- **0:00–0:25 — the gap.** A neonatologist in the NICU gets a report flagging a VUS. Whole-exome
  rankers and VarSome don't fit the bedside. Name the user.
- **0:25–1:20 — one variant, as written.** Type `KCNQ2` + `c.715G>A` (a genuine **VUS** — ClinVar:
  uncertain) and the baby's phenotypes (`HP:0001250, HP:0010851, HP:0001252`). Report appears. Point
  at: verdict gauge (**leans pathogenic despite the VUS call**), in-silico threshold bars, and the
  **protein lollipop — the variant lands in the S5 transmembrane segment**.
- **1:20–2:05 — actionable + auditable.** Candidate diseases re-ranked to KCNQ2 developmental &
  epileptic encephalopathy (100% phenotype match); neonatal checklist with cited work-up/follow-up;
  click a ClinVar/GeneReviews link to show the evidence trail; download the printable report.
- **2:05–2:40 — it's validated, not a black box.** ClinVar-reclassification proxy: 84.8% direction
  agreement, 100% pathogenic precision. Show `scripts/validate.py` output.
- **2:40–3:00 — two Claude products.** Claude Code built the tool + validation; Claude Science curated
  the reclassification benchmark and the 18-gene cited checklists. Open-source, reproducible.

## Optional — mention the v2 upgrade (in the video close or as a note)

An upgraded **v2** is already in development: it keeps v1's transparency but reasons on the
**ACMG/AMP point framework** — calibrated evidence strengths (REVEL at ClinGen/Pejaver
thresholds), a provisional point-based classification, **PVS1-lite** (gnomAD gene constraint),
**PS1/PM5/PM1** from ClinVar, and clinician-supplied **family/functional evidence (de novo,
segregation, …) that re-classifies live**. Live: `https://neovus2.streamlit.app`.
One line for the summary if space allows: *"A calibrated, ACMG-aware v2 (provisional
point-based classification + live family-evidence input) is already in development."*

## Submission checklist

- [x] Push repo public to github.com/moonicu (MIT ✓) — **PUBLIC: github.com/moonicu/neovus**
- [x] (bonus) Deploy to Streamlit Community Cloud — **live: https://neovus.streamlit.app**
- [x] (bonus) v2 upgrade deployed — **live: https://neovus2.streamlit.app** (confirm public/incognito)
- [ ] Record 3-min demo video (script above) → YouTube **Unlisted**
- [ ] Paste the written summary (≈190 words, above)
- [ ] Add both live URLs + repo link
- [ ] Submit on the CV platform before the deadline (Jul 14, 10:00 AM KST)

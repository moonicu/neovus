"""Self-contained SVG / DOT generators for the report visuals.

Pure functions returning strings — no plotting deps, no network. Rendered in the
Streamlit UI (components.html / graphviz_chart) and embeddable in the HTML report.

Design choices (colourblind-aware): pathogenic/benign are never encoded by colour
alone — every coloured mark carries a text label. Magnitude bars use one hue with
an explicit threshold line; the verdict gauge is a diverging benign↔pathogenic
scale with a neutral midpoint.
"""

from __future__ import annotations

from .report import Report

# Semantic colours (paired with labels everywhere)
_PATHO = "#dc2626"      # red — pathogenic-leaning
_BENIGN = "#0d9488"     # teal — benign-leaning (teal, not green: better vs red for CVD)
_INK = "#1f2937"
_MUTED = "#6b7280"
_TRACK = "#e5e7eb"
_TM = "#3b82f6"         # transmembrane segments
_DOMAIN = "#8b5cf6"     # other domains
_BAR = "#2563eb"        # magnitude fill


def _esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _dot(s) -> str:
    """Escape a Graphviz DOT quoted-string label."""
    return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


# --------------------------------------------------------------------------- #
# 1. Protein-domain lollipop                                                  #
# --------------------------------------------------------------------------- #
def protein_track_svg(report: Report, width: int = 720) -> str | None:
    s = report.structural
    if not s or not s.length:
        return None
    L, x0, x1, top = s.length, 60, width - 30, 54
    span = x1 - x0
    def px(res): return x0 + span * (res / L)

    parts = [f'<svg width="100%" height="100%" viewBox="0 0 {width} 104" '
             'preserveAspectRatio="xMidYMid meet" '
             'xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,Segoe UI,Roboto,sans-serif">']
    # baseline track
    parts.append(f'<rect x="{x0}" y="{top}" width="{span}" height="14" rx="7" fill="{_TRACK}"/>')
    parts.append(f'<text x="{x0-6}" y="{top+11}" text-anchor="end" font-size="11" fill="{_MUTED}">N</text>')
    parts.append(f'<text x="{x1+6}" y="{top+11}" font-size="11" fill="{_MUTED}">{L} aa</text>')

    # domains
    for d in s.domains:
        b, e = d.get("begin"), d.get("end")
        if not (isinstance(b, int) and isinstance(e, int)):
            continue
        kind = d.get("type", "")
        color = _TM if kind == "Transmembrane" else _DOMAIN
        bx, ew = px(b), max(3, px(e) - px(b))
        parts.append(f'<rect x="{bx:.1f}" y="{top}" width="{ew:.1f}" height="14" rx="3" '
                     f'fill="{color}" opacity="0.85"/>')
        # short label if wide enough
        desc = d.get("description") or ""
        name = next((p[5:].strip() for p in desc.split(";") if p.strip().startswith("Name=")), None)
        if name and ew > 26:
            parts.append(f'<text x="{bx+ew/2:.1f}" y="{top+43}" text-anchor="middle" '
                         f'font-size="9" fill="{_MUTED}">{_esc(name)}</text>')

    # variant lollipop
    r = s.residue
    if isinstance(r, int) and 1 <= r <= L:
        vx = px(r)
        label = report.variant.hgvs or f"res {r}"
        parts.append(f'<line x1="{vx:.1f}" y1="26" x2="{vx:.1f}" y2="{top}" stroke="{_PATHO}" stroke-width="2"/>')
        parts.append(f'<circle cx="{vx:.1f}" cy="22" r="7" fill="{_PATHO}"/>')
        # label box
        tw = 8 + 6.4 * len(label)
        lx = min(max(vx - tw / 2, 2), width - tw - 2)
        parts.append(f'<rect x="{lx:.1f}" y="2" width="{tw:.1f}" height="16" rx="4" fill="{_PATHO}"/>')
        parts.append(f'<text x="{lx+tw/2:.1f}" y="14" text-anchor="middle" font-size="11" '
                     f'fill="#fff" font-weight="600">{_esc(label)}</text>')

    parts.append(f'<text x="{x0}" y="90" font-size="11" fill="{_INK}">'
                 f'{_esc(report.variant.gene)} · {_esc(s.accession or "")}</text>')
    parts.append(f'<text x="{x1}" y="90" text-anchor="end" font-size="10" fill="{_MUTED}">'
                 f'■ transmembrane   ■ domain   ● variant</text>')
    parts.append("</svg>")
    return "".join(parts)


# --------------------------------------------------------------------------- #
# 2. In-silico score bars with thresholds                                     #
# --------------------------------------------------------------------------- #
def score_bars_svg(report: Report, width: int = 360) -> str | None:
    h = report.headline
    rows = []
    if h.revel is not None:
        rows.append(("REVEL", h.revel, 1.0, 0.5, f"{h.revel:.2f}"))
    if h.alphamissense is not None:
        rows.append(("AlphaMissense", h.alphamissense, 1.0, 0.5,
                     f"{h.alphamissense:.2f}" + (f" {h.alphamissense_pred}" if h.alphamissense_pred else "")))
    if h.cadd is not None:
        rows.append(("CADD", min(h.cadd, 40), 40.0, 20.0, f"{h.cadd:.0f}"))
    if not rows:
        return None

    x0, bw, rh = 108, width - 108 - 46, 26
    height = len(rows) * rh + 12
    parts = [f'<svg width="100%" height="100%" viewBox="0 0 {width} {height}" '
             'preserveAspectRatio="xMidYMid meet" '
             'xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,Segoe UI,Roboto,sans-serif">']
    for i, (name, val, vmax, thr, txt) in enumerate(rows):
        y = 8 + i * rh
        frac = max(0.0, min(1.0, val / vmax))
        parts.append(f'<text x="0" y="{y+13}" font-size="11" fill="{_INK}">{name}</text>')
        parts.append(f'<rect x="{x0}" y="{y+4}" width="{bw}" height="12" rx="6" fill="{_TRACK}"/>')
        parts.append(f'<rect x="{x0}" y="{y+4}" width="{bw*frac:.1f}" height="12" rx="6" fill="{_BAR}"/>')
        # threshold tick
        tx = x0 + bw * (thr / vmax)
        parts.append(f'<line x1="{tx:.1f}" y1="{y+1}" x2="{tx:.1f}" y2="{y+19}" stroke="{_MUTED}" '
                     f'stroke-width="1.5" stroke-dasharray="2,2"/>')
        parts.append(f'<text x="{width-2}" y="{y+13}" text-anchor="end" font-size="11" '
                     f'fill="{_INK}" font-weight="600">{_esc(txt)}</text>')
    parts.append("</svg>")
    return "".join(parts)


# --------------------------------------------------------------------------- #
# 3. Evidence-direction verdict gauge (diverging)                             #
# --------------------------------------------------------------------------- #
def verdict_gauge_svg(report: Report, width: int = 360) -> str:
    h = report.headline
    score = max(-4, min(4, h.direction_score))
    frac = (score + 4) / 8                       # 0=benign .. 1=pathogenic
    x0, x1, y = 12, width - 12, 30
    span = x1 - x0
    nx = x0 + span * frac
    call = h.direction or "uncertain"
    color = {"pathogenic": _PATHO, "benign": _BENIGN}.get(call, _MUTED)
    parts = [f'<svg width="100%" height="100%" viewBox="0 0 {width} 62" '
             'preserveAspectRatio="xMidYMid meet" '
             'xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,Segoe UI,Roboto,sans-serif">']
    # diverging track: teal → gray → red
    parts.append(f'<defs><linearGradient id="g" x1="0" x2="1">'
                 f'<stop offset="0" stop-color="{_BENIGN}"/><stop offset="0.5" stop-color="#d1d5db"/>'
                 f'<stop offset="1" stop-color="{_PATHO}"/></linearGradient></defs>')
    parts.append(f'<rect x="{x0}" y="{y}" width="{span}" height="10" rx="5" fill="url(#g)"/>')
    parts.append(f'<text x="{x0}" y="{y+26}" font-size="10" fill="{_BENIGN}">benign</text>')
    parts.append(f'<text x="{x1}" y="{y+26}" text-anchor="end" font-size="10" fill="{_PATHO}">pathogenic</text>')
    # needle
    parts.append(f'<polygon points="{nx-6:.1f},{y-6} {nx+6:.1f},{y-6} {nx:.1f},{y+2}" fill="{_INK}"/>')
    parts.append(f'<text x="{width/2:.0f}" y="14" text-anchor="middle" font-size="13" '
                 f'font-weight="700" fill="{color}">evidence leans {_esc(call)}</text>')
    parts.append("</svg>")
    return "".join(parts)


# --------------------------------------------------------------------------- #
# 4. Gene → disease → phenotype graph (Graphviz DOT)                          #
# --------------------------------------------------------------------------- #
def _wrap(text: str, width: int = 20) -> str:
    """Word-wrap a label into Graphviz \\n-separated lines — never truncates,
    so long disease names show in full (the graph just gets a bit taller)."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return "\\n".join(_dot(ln) for ln in lines)


def disease_graph_dot(report: Report, max_diseases: int = 4, max_phenos: int = 5) -> str | None:
    if not report.candidate_diseases:
        return None
    gene = report.variant.gene
    lines = [
        'digraph G {',
        'rankdir=LR; bgcolor="transparent"; pad=0.2; nodesep=0.28; ranksep=0.75;',
        'node [fontname="Helvetica" fontsize=11 style="filled,rounded" shape=box '
        'margin="0.14,0.08"];',
        'edge [color="#9ca3af" fontname="Helvetica" fontsize=10];',
        f'"{gene}" [label="{_dot(gene)}\\n(gene)" fillcolor="#1f2937" fontcolor="white"];',
    ]
    for i, d in enumerate(report.candidate_diseases[:max_diseases]):
        nid, top = f"d{i}", (i == 0)
        fill = "#fee2e2" if top else "#f3f4f6"
        edge_color = "#dc2626" if top else "#9ca3af"
        lines.append(f'"{nid}" [label="{_wrap(d.name)}" fillcolor="{fill}" color="#e5e7eb"];')
        elabel = f'label="match {d.score:.0%}" fontcolor="#dc2626"' if d.score else 'label=""'
        pen = "penwidth=2" if top else "penwidth=1"
        lines.append(f'"{gene}" -> "{nid}" [{elabel} color="{edge_color}" {pen}];')

    # key phenotypes of the TOP disease (ellipses), so the traversal reads clearly
    symptoms = [it for it in report.checklist if it.category == "symptom"][:max_phenos]
    for j, it in enumerate(symptoms):
        pid = f"p{j}"
        label = it.text.split(" [")[0]
        lines.append(f'"{pid}" [label="{_wrap(label, 16)}" shape=ellipse '
                     f'fillcolor="#eff6ff" color="#dbeafe" fontsize=10];')
        lines.append(f'"d0" -> "{pid}" [color="#c7d2fe"];')
    lines.append("}")
    return "\n".join(lines)

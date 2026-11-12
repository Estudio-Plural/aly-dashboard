"""KPI row — premium metric cards with accent bar, icon, sparkline and delta pill."""

import html
import streamlit as st

from utils.styles import COLORS


# Lucide-style mono line icons (16px)
ICONS: dict[str, str] = {
    "users": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
        '<circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/>'
        '<path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'
    ),
    "message": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'
    ),
    "send": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/>'
        '<polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>'
    ),
    "chart": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/>'
        '<line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'
    ),
    "alert-triangle": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
        '<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
    ),
    "alert-circle": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round"><circle cx="12" cy="12" r="10"/>'
        '<line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
    ),
    "flag": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>'
        '<line x1="4" y1="22" x2="4" y2="15"/></svg>'
    ),
    "activity": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
    ),
}


def _sparkline_svg(values, color: str, width: int = 140, height: int = 36) -> str:
    """Build an inline SVG sparkline (line + filled area)."""
    if not values:
        return ""
    vals = [float(v) if v is not None else 0.0 for v in values]
    if len(vals) < 2:
        return ""
    vmin, vmax = min(vals), max(vals)
    rng = (vmax - vmin) or 1.0
    pad = 1.5
    W, H = width - pad * 2, height - pad * 2
    n = len(vals)

    pts = []
    for i, v in enumerate(vals):
        x = pad + (i / (n - 1)) * W
        y = pad + H - ((v - vmin) / rng) * H
        pts.append(f"{x:.1f},{y:.1f}")
    line = " ".join(pts)
    area = f"{pad},{pad + H} " + line + f" {pad + W},{pad + H}"

    return (
        f'<svg class="kpi-card__spark" viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="none">'
        f'<polygon points="{area}" fill="{color}" opacity="0.14"/>'
        f'<polyline points="{line}" fill="none" stroke="{color}" '
        f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )


def _fmt_value(value, prefix: str = "", suffix: str = "") -> str:
    if isinstance(value, bool):
        body = str(value)
    elif isinstance(value, int):
        body = f"{value:,}"
    elif isinstance(value, float):
        body = f"{value:.1f}"
    else:
        body = str(value)
    return f"{prefix}{body}{suffix}"


def _delta_pill(delta, delta_label: str) -> str:
    if delta is None:
        return ""
    positive = delta >= 0
    sign = "+" if positive else ""
    color = COLORS["positive"] if positive else COLORS["negative"]
    bg = "rgba(34,197,94,0.12)" if positive else "rgba(241,91,34,0.12)"
    arrow = "▲" if positive else "▼"
    pct = delta * 100
    label_html = (
        f'<span class="kpi-card__delta-label">{html.escape(delta_label)}</span>'
        if delta_label else ""
    )
    return (
        f'<div class="kpi-card__delta-row">'
        f'<span class="kpi-card__delta" style="color:{color};background:{bg}">'
        f'<span class="kpi-card__delta-arrow">{arrow}</span>'
        f'{sign}{pct:.1f}%'
        f'</span>'
        f'{label_html}'
        f'</div>'
    )


def _delta_abs(curr, prev, label: str) -> str:
    """Diferencia en absoluto contra el período anterior, en gris.

    Con pocas personas un porcentaje engaña: pasar de 13 a 6 es «−53,8 %» en
    rojo, y en un programa chico eso no es una alarma. Por eso se muestra la
    diferencia («−7») con la base al lado, en color neutro (el rojo y el
    naranja quedan para las alertas), y se omite si el período anterior tuvo
    menos de 10: ahí la comparación es ruido.
    """
    if curr is None or prev is None or prev < 10:
        return ""
    diff = int(curr) - int(prev)
    sign = "+" if diff > 0 else ("−" if diff < 0 else "±")
    return (
        f'<div class="kpi-card__delta-row">'
        f'<span class="kpi-card__delta kpi-card__delta--neutral">{sign}{abs(diff):,}</span>'
        f'<span class="kpi-card__delta-label">{html.escape(label)}</span>'
        f'</div>'
    )


def render(metrics: list[dict]):
    """Render a row of premium KPI cards.

    Each metric dict:
        label       str                — display label (uppercased via CSS)
        value       int | float | str  — the main figure
        delta       float | None       — fraction, e.g. 0.12 → +12.0% (formato viejo)
        delta_label str                — context label, e.g. "vs período anterior"
        prev        int | None         — valor del período anterior: si viene, se
                                         muestra la diferencia en absoluto (ver
                                         _delta_abs) en vez del %; delta_label
                                         lleva la base, p. ej. "vs. 13 antes"
        prefix      str                — optional prefix (e.g. "$")
        suffix      str                — optional suffix (e.g. "%")
        accent      str                — color key in COLORS; default "accent"
        icon        str                — key from ICONS
        spark       list[num] | None   — daily series for the sparkline
        caption     str                — optional one-line explanation under the value
    """
    # key="kpis": el CSS estira las tarjetas a la misma altura (styles.py).
    # Una sola fila de KPIs por página, así que la key no se repite.
    with st.container(key="kpis"):
        cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            accent_key = m.get("accent", "accent")
            accent = COLORS.get(accent_key, COLORS["accent"])
            icon_svg = ICONS.get(m.get("icon") or "", "")
            value_html = _fmt_value(m["value"], m.get("prefix", ""), m.get("suffix", ""))
            spark_html = _sparkline_svg(m.get("spark") or [], accent)
            if "prev" in m:
                delta_html = _delta_abs(m["value"], m.get("prev"), m.get("delta_label", ""))
            else:
                delta_html = _delta_pill(m.get("delta"), m.get("delta_label", ""))
            caption = m.get("caption", "")
            caption_html = (
                f'<div class="kpi-card__caption">{html.escape(caption)}</div>'
                if caption else ""
            )

            st.markdown(
                f'<div class="kpi-card" style="--kpi-accent:{accent}">'
                f'<div class="kpi-card__top">'
                f'<span class="kpi-card__label">{html.escape(m["label"])}</span>'
                f'<span class="kpi-card__icon">{icon_svg}</span>'
                f'</div>'
                f'<div class="kpi-card__value">{html.escape(value_html)}</div>'
                f'{caption_html}'
                f'{delta_html}'
                f'{spark_html}'
                f'</div>',
                unsafe_allow_html=True,
            )

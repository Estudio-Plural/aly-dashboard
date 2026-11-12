"""Aly brand styles — global CSS injection for the redesigned dashboard."""

from contextlib import contextmanager

import streamlit as st

COLORS = {
    "bg_app":        "#F7F8FA",
    "bg_sidebar":    "#FFFFFF",
    "bg_sidebar_alt":"#FAFBFC",
    "bg_card":       "#FFFFFF",
    "border":        "#E5E7EB",
    "border_strong": "#D1D5DB",
    "accent":        "#0273e5",
    "accent_soft":   "#EFF6FF",
    "navy":          "#110079",
    "green":         "#91EBF4",
    "red":           "#F15B22",
    "yellow":        "#FFCF24",
    "positive":      "#22C55E",
    "negative":      "#F15B22",
    "text":          "#0C1214",
    # Grises oscuros a propósito: el gris lavado (#9CA3AF) no se leía en
    # pantallas con brillo bajo. Nada de texto más claro que text_muted.
    "text_secondary":"#374151",
    "text_muted":    "#4B5563",
}


def inject():
    css = """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,300..800;1,300..800&family=Oswald:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,400..600,0..1,-50..200" rel="stylesheet">

    <style>
    /* ── Variables ──────────────────────────────────────────────────────── */
    :root {
        --bg-app:         #F7F8FA;
        --bg-sidebar:     #FFFFFF;
        --bg-sidebar-alt: #FAFBFC;
        --bg-card:        #FFFFFF;
        --border:         #E5E7EB;
        --border-strong:  #D1D5DB;
        --accent:         #0273e5;
        --accent-soft:    #EFF6FF;
        --accent-navy:    #110079;
        --accent-green:   #91EBF4;
        --accent-red:     #F15B22;
        --accent-yellow:  #FFCF24;
        --positive:       #22C55E;
        --negative:       #F15B22;
        --text:           #0C1214;
        --text-secondary: #374151;
        --text-muted:     #4B5563;
        --radius:         10px;
        --shadow:         0 1px 3px rgba(17,24,39,0.06), 0 1px 2px rgba(17,24,39,0.04);
        --shadow-md:      0 4px 14px rgba(17,24,39,0.08);
        --shadow-sidebar: 1px 0 0 rgba(17,24,39,0.05);
    }

    /* ── Global reset ───────────────────────────────────────────────────── */
    html, body, [class*="css"], .stApp {
        background-color: var(--bg-app) !important;
        color: var(--text) !important;
        font-family: 'Open Sans', sans-serif !important;
    }

    /* Hide Streamlit chrome */
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent !important; }

    /* ── Sidebar — light ────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border) !important;
        box-shadow: var(--shadow-sidebar) !important;
    }
    [data-testid="stSidebar"] * {
        font-family: 'Open Sans', sans-serif !important;
        color: var(--text) !important;
    }
    /* Material icons must keep their own font so the ligatures resolve */
    [data-testid="stSidebar"] [data-testid="stIconMaterial"],
    [data-testid="stSidebar"] span[class*="material-symbols"],
    [data-testid="stSidebar"] .material-symbols-rounded,
    [data-testid="stSidebar"] .material-symbols-outlined {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined' !important;
        font-weight: normal !important;
        font-style: normal !important;
        font-size: 20px !important;
        color: var(--text-muted) !important;
        line-height: 1 !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-block !important;
        white-space: nowrap !important;
        direction: ltr !important;
        -webkit-font-feature-settings: 'liga' !important;
        -webkit-font-smoothing: antialiased !important;
    }
    [data-testid="stSidebar"] a[aria-current="page"] [data-testid="stIconMaterial"] {
        color: var(--accent) !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--text) !important;
        font-family: 'Oswald', sans-serif !important;
    }

    /* Hide Streamlit's default page nav — we render our own */
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] { display: none !important; }

    /* Sidebar form inputs */
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
    [data-testid="stSidebar"] .stDateInput input {
        background-color: var(--bg-sidebar) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] .stRadio label {
        color: var(--text-muted) !important;
        font-size: 0.68rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }
    [data-testid="stSidebar"] hr { border-color: var(--border) !important; }

    /* Sidebar buttons — ghost style */
    [data-testid="stSidebar"] .stButton > button {
        background-color: var(--bg-sidebar-alt) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: var(--accent-soft) !important;
        color: var(--accent) !important;
        border-color: var(--accent) !important;
    }
    [data-testid="stSidebar"] .stDownloadButton > button {
        background-color: var(--bg-sidebar) !important;
    }

    /* ── Custom sidebar nav (rendered manually in filters.py) ──────────── */
    .nav-section {
        font-family: 'Open Sans', sans-serif !important;
        font-size: 0.64rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.12em !important;
        color: var(--text-muted) !important;
        text-transform: uppercase !important;
        padding: 0.75rem 0.6rem 0.4rem !important;
        margin-top: 0.5rem !important;
    }
    .bot-locked {
        font-family: 'Open Sans', sans-serif;
        font-size: 0.66rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
        background: #F3F4F6;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 0.4rem 0.6rem;
        line-height: 1.5;
    }
    .bot-locked b {
        font-size: 0.92rem;
        text-transform: none;
        letter-spacing: 0;
        color: var(--text);
    }
    [data-testid="stSidebar"] [data-testid="stPageLink"] a,
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
        display: flex !important;
        align-items: center !important;
        gap: 0.6rem !important;
        padding: 0.55rem 0.75rem !important;
        border-radius: 8px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
        background: transparent !important;
        border: none !important;
        transition: background 0.15s, color 0.15s !important;
        margin: 0.15rem 0 !important;
        text-decoration: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
        background: var(--bg-sidebar-alt) !important;
        color: var(--text) !important;
    }
    [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"],
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"],
    [data-testid="stSidebar"] .stPageLink--active a {
        background: var(--accent-soft) !important;
        color: var(--accent) !important;
        font-weight: 600 !important;
        box-shadow: inset 2px 0 0 var(--accent) !important;
    }
    [data-testid="stSidebar"] [data-testid="stPageLink"] a span,
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] span {
        color: inherit !important;
        font-size: inherit !important;
    }

    /* ── Main content ───────────────────────────────────────────────────── */
    [data-testid="stMainBlockContainer"] {
        background-color: var(--bg-app) !important;
        padding: 1.25rem 2rem 3rem !important;
        max-width: 1320px !important;
    }

    /* ── Headings ───────────────────────────────────────────────────────── */
    h1 {
        font-family: 'Oswald', sans-serif !important;
        font-size: 1.75rem !important;
        font-weight: 600 !important;
        color: var(--text) !important;
        letter-spacing: 0.01em !important;
        margin-bottom: 0.25rem !important;
    }
    h2, h3 {
        font-family: 'Open Sans', sans-serif !important;
        color: var(--text-secondary) !important;
    }

    /* ── st.metric fallback (still used in some pages) ──────────────────── */
    [data-testid="metric-container"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 1.1rem 1.25rem !important;
        box-shadow: var(--shadow) !important;
        transition: box-shadow 0.2s, transform 0.2s !important;
    }
    [data-testid="metric-container"]:hover {
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricLabel"] p {
        font-family: 'Open Sans', sans-serif !important;
        font-size: 0.7rem !important;
        font-weight: 700 !important;
        color: var(--text-muted) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.07em !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-family: 'Oswald', sans-serif !important;
        font-size: 2.1rem !important;
        font-weight: 600 !important;
        color: var(--text) !important;
        font-variant-numeric: tabular-nums !important;
        line-height: 1.1 !important;
    }
    [data-testid="stMetricDeltaIcon-Up"]   { color: var(--positive) !important; }
    [data-testid="stMetricDeltaIcon-Down"] { color: var(--negative) !important; }

    /* ── KPI cards — premium (custom HTML) ──────────────────────────────── */
    .kpi-card {
        position: relative;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.05rem 1.25rem 0.9rem 1.4rem;
        box-shadow: var(--shadow);
        overflow: hidden;
        transition: box-shadow 0.2s, transform 0.2s;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }
    .kpi-card::before {
        content: "";
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 3px;
        background: var(--kpi-accent, var(--accent));
    }
    .kpi-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }
    .kpi-card__top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        margin-bottom: 0.35rem;
    }
    .kpi-card__label {
        font-family: 'Open Sans', sans-serif;
        font-size: 0.68rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .kpi-card__icon {
        color: var(--kpi-accent, var(--accent));
        opacity: 0.85;
        display: inline-flex;
        line-height: 0;
    }
    .kpi-card__value {
        font-family: 'Oswald', sans-serif;
        font-size: 2.1rem;
        font-weight: 600;
        color: var(--text);
        font-variant-numeric: tabular-nums;
        line-height: 1.1;
        letter-spacing: 0.01em;
    }
    .kpi-card__delta-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 0.5rem;
        flex-wrap: wrap;
    }
    .kpi-card__delta {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        font-family: 'Open Sans', sans-serif;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        padding: 0.2rem 0.5rem;
        border-radius: 999px;
        font-variant-numeric: tabular-nums;
        line-height: 1;
    }
    .kpi-card__delta--neutral {
        background: var(--bg-app);
        border: 1px solid var(--border);
        color: var(--text);
    }
    .kpi-card__delta-arrow {
        font-size: 0.6rem;
        line-height: 1;
    }
    .kpi-card__delta-label {
        font-family: 'Open Sans', sans-serif;
        font-size: 0.7rem;
        color: var(--text-muted);
        font-weight: 500;
    }
    .kpi-card__spark {
        display: block;
        width: 100%;
        height: 36px;
        margin-top: 0.6rem;
    }
    .kpi-card__caption {
        font-family: 'Open Sans', sans-serif;
        font-size: 0.72rem;
        line-height: 1.25;
        color: var(--text-muted);
        margin-top: 0.4rem;
    }

    /* ── Top bar — language selector pinned top-right ───────────────────── */
    .topbar-lang { display: flex; justify-content: flex-end; }
    /* Compact segmented control in the top bar */
    [data-testid="stSegmentedControl"] button {
        padding: 0.1rem 0.7rem !important;
        font-family: 'Open Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.72rem !important;
        letter-spacing: 0.04em !important;
    }

    /* ── Page header — title, subtitle and period chip ──────────────────── */
    .page-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1.5rem;
    }
    .page-header__text { min-width: 0; }
    .page-header__text h1 {
        margin: 0 !important;
        padding: 0 !important;
    }
    .page-header__subtitle {
        margin: 0.3rem 0 0 !important;
        font-size: 0.875rem;
        color: var(--text-secondary);
        font-family: 'Open Sans', sans-serif;
    }
    .page-header__chip {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.45rem 0.8rem;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 999px;
        font-family: 'Open Sans', sans-serif;
        font-size: 0.78rem;
        color: var(--text-secondary);
        box-shadow: var(--shadow);
        flex-shrink: 0;
        white-space: nowrap;
        margin-top: 0.25rem;
    }
    .page-header__chip svg {
        color: var(--accent);
        flex-shrink: 0;
    }
    .page-header__chip-range {
        font-weight: 600;
        color: var(--text);
        font-variant-numeric: tabular-nums;
    }
    .page-header__chip-sep { color: var(--text-muted); }
    .page-header__chip-span { color: var(--text-secondary); font-weight: 500; }

    /* ── Hero banner (overview top) ────────────────────────────────────── */
    .hero {
        position: relative;
        background: linear-gradient(135deg, #FFFFFF 0%, #EFF6FF 100%);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.4rem 1.6rem 1.35rem;
        margin-bottom: 1.25rem;
        overflow: hidden;
        box-shadow: var(--shadow);
    }
    .hero::after {
        content: "";
        position: absolute;
        top: -60px; right: -60px;
        width: 180px; height: 180px;
        background: radial-gradient(circle, rgba(2,115,229,0.14), transparent 65%);
        pointer-events: none;
    }
    .hero__grid {
        display: grid;
        grid-template-columns: 1fr auto;
        align-items: center;
        gap: 1.5rem;
        position: relative;
        z-index: 1;
    }
    .hero__status {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.3rem 0.7rem;
        background: rgba(34,197,94,0.12);
        border-radius: 999px;
        font-family: 'Open Sans', sans-serif;
        font-size: 0.72rem;
        font-weight: 700;
        color: #15803D;
        letter-spacing: 0.03em;
        margin-bottom: 0.7rem;
    }
    .hero__status--warn {
        background: rgba(255,207,36,0.18);
        color: #92400E;
    }
    .hero__status--crit {
        background: rgba(241,91,34,0.12);
        color: #9A3412;
    }
    .hero__status-dot {
        width: 7px; height: 7px; border-radius: 50%;
        background: currentColor;
        box-shadow: 0 0 0 3px rgba(34,197,94,0.18);
    }
    .hero__headline {
        font-family: 'Open Sans', sans-serif;
        font-size: 1.05rem;
        font-weight: 500;
        color: var(--text);
        line-height: 1.5;
        margin: 0;
    }
    .hero__headline b {
        font-family: 'Oswald', sans-serif;
        font-weight: 600;
        color: var(--text);
        font-size: 1.35rem;
        letter-spacing: 0.01em;
        padding: 0 0.15rem;
        font-variant-numeric: tabular-nums;
    }
    .hero__right {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 0.35rem;
    }
    .hero__meta-label {
        font-family: 'Open Sans', sans-serif;
        font-size: 0.68rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .hero__meta-value {
        font-family: 'Oswald', sans-serif;
        font-size: 1.75rem;
        font-weight: 600;
        color: var(--accent);
        font-variant-numeric: tabular-nums;
        line-height: 1;
    }

    /* ── Card with header (wraps charts/tables) ────────────────────────── */
    .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.65rem 0.25rem 0.55rem;
        margin-bottom: 0.25rem;
    }
    .card-header__left {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        min-width: 0;
    }
    .card-header__icon {
        display: inline-flex;
        color: var(--accent);
        background: var(--accent-soft);
        padding: 0.3rem;
        border-radius: 6px;
        line-height: 0;
    }
    .card-header__title {
        font-family: 'Open Sans', sans-serif;
        font-size: 0.92rem;
        font-weight: 700;
        color: var(--text);
        letter-spacing: 0.005em;
    }
    .card-header__subtitle {
        font-family: 'Open Sans', sans-serif;
        font-size: 0.76rem;
        color: var(--text-muted);
        font-weight: 500;
    }
    .card-header__right {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-family: 'Open Sans', sans-serif;
        font-size: 0.72rem;
        color: var(--text-muted);
        font-weight: 500;
        white-space: nowrap;
    }

    /* Arc gauges (3/4 circle progress, gauge style) */
    .arc-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
        gap: 0.75rem;
        padding: 0.5rem 0.25rem 0.25rem;
    }
    .arc-gauge {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.1rem;
    }
    .arc-gauge__label {
        font-family: 'Open Sans', sans-serif;
        font-size: 0.78rem;
        color: var(--text-secondary);
        font-weight: 600;
        text-align: center;
        margin-bottom: 0.1rem;
    }
    .arc-gauge__svg-wrap {
        position: relative;
        width: 84px;
        height: 84px;
    }
    .arc-gauge__svg-wrap svg {
        width: 100%;
        height: 100%;
    }
    .arc-gauge__value {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Oswald', sans-serif;
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--text);
        font-variant-numeric: tabular-nums;
    }

    /* Stat-list (compact vertical KPI list inside a card) */
    .stat-list {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        padding: 1.1rem 1.25rem;
        height: 100%;
        display: flex;
        flex-direction: column;
        gap: 0.95rem;
    }
    .stat-list__item {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 0.75rem;
        padding-bottom: 0.85rem;
        border-bottom: 1px solid var(--border);
    }
    .stat-list__item:last-child {
        padding-bottom: 0;
        border-bottom: 0;
    }
    .stat-list__label {
        font-family: 'Open Sans', sans-serif;
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-secondary);
    }
    .stat-list__value {
        font-family: 'Oswald', sans-serif;
        white-space: nowrap;
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text);
        font-variant-numeric: tabular-nums;
    }

    /* ── Plotly chart containers ────────────────────────────────────────── */
    .js-plotly-plot {
        background: var(--bg-card) !important;
    }

    /* ── Tarjetas: st.container(border=True, key="card-…") vía card() ──── */
    /* La clase st-key-(key) es la forma documentada de estilar un contenedor;
       no depende de los data-testid internos, que cambian entre versiones.
       OJO: nada de "<" seguido de letra en este CSS, ni en comentarios: el
       sanitizador de st.html lo toma por una etiqueta y descarta la etiqueta style
       completo, sin error. */
    [class*="st-key-card-"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        box-shadow: var(--shadow) !important;
        padding: 0.85rem 1.1rem 1rem !important;
        gap: 0.5rem !important;
    }
    [class*="st-key-card-"] .card-header { padding: 0 0 0.35rem; margin: 0; }
    [class*="st-key-card-"] .stat-list {
        border: 0; box-shadow: none; padding: 0.25rem 0 0.15rem; background: transparent;
        height: auto;
    }

    /* KPIs de la misma altura aunque una tenga más texto que otra: el
       contenedor key="kpis" (kpi_row) estira cada columna hasta la tarjeta.
       Si un día cambian estos data-testid, solo vuelven las alturas
       desparejas; no se rompe nada más. */
    .st-key-kpis [data-testid="stColumn"],
    .st-key-kpis [data-testid="stColumn"] [data-testid="stElementContainer"],
    .st-key-kpis [data-testid="stColumn"] [data-testid="stMarkdown"],
    .st-key-kpis [data-testid="stColumn"] [data-testid="stMarkdown"] > div,
    .st-key-kpis [data-testid="stColumn"] [data-testid="stMarkdownContainer"] {
        display: flex;
        flex-direction: column;
        align-items: stretch;
    }
    .st-key-kpis [data-testid="stColumn"] > [data-testid="stVerticalBlock"],
    .st-key-kpis [data-testid="stColumn"] [data-testid="stElementContainer"],
    .st-key-kpis [data-testid="stColumn"] [data-testid="stMarkdown"],
    .st-key-kpis [data-testid="stColumn"] [data-testid="stMarkdown"] > div,
    .st-key-kpis [data-testid="stColumn"] [data-testid="stMarkdownContainer"],
    .st-key-kpis .kpi-card {
        flex: 1 1 auto;
    }
    [class*="st-key-card-"] [data-testid="stDataFrame"] { box-shadow: none !important; }

    /* Notas bajo una gráfica o un indicador: legibles, no grises lavados. */
    p.note {
        font-family: 'Open Sans', sans-serif !important;
        font-size: 0.8rem !important;
        line-height: 1.5 !important;
        color: var(--text-muted) !important;
        margin: 0.15rem 0 0 !important;
    }
    .note b { color: var(--text); font-weight: 600; }

    /* ── Franja de estado (Inicio) ──────────────────────────────────────── */
    .status-strip {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.6rem 1.4rem;
        padding: 0.7rem 1rem;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        box-shadow: var(--shadow);
        margin-bottom: 1rem;
        font-family: 'Open Sans', sans-serif;
        font-size: 0.84rem;
        color: var(--text-secondary);
    }
    .status-strip b { color: var(--text); font-weight: 600; }
    .status-pill {
        display: inline-flex; align-items: center; gap: 0.45rem;
        padding: 0.25rem 0.7rem; border-radius: 999px;
        font-weight: 700; font-size: 0.78rem;
        background: rgba(34,197,94,0.12); color: #15803D;
    }
    .status-pill--warn { background: rgba(255,207,36,0.22); color: #854D0E; }
    .status-pill--crit { background: rgba(241,91,34,0.14); color: #9A3412; }
    .status-pill::before {
        content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor;
    }
    .status-strip__sep { color: var(--border-strong); }

    /* ── Tabs ────────────────────────────────────────────────────────────── */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 0.25rem !important;
        border-bottom: 1px solid var(--border) !important;
        background: transparent !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        font-family: 'Open Sans', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 0.5rem 1.25rem !important;
        background: transparent !important;
        border: none !important;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom: 2px solid var(--accent) !important;
    }

    /* ── Buttons ─────────────────────────────────────────────────────────── */
    .stButton > button,
    .stFormSubmitButton > button {
        background-color: var(--accent) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Open Sans', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        padding: 0.45rem 1.25rem !important;
        transition: opacity 0.2s, box-shadow 0.2s !important;
    }
    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        opacity: 0.9 !important;
        box-shadow: 0 2px 8px rgba(2,115,229,0.35) !important;
    }
    .stDownloadButton > button {
        background-color: transparent !important;
        color: var(--accent) !important;
        border: 1.5px solid var(--accent) !important;
        border-radius: 8px !important;
        font-family: 'Open Sans', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }

    /* ── DataFrames / Tables ─────────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        overflow: hidden !important;
        box-shadow: var(--shadow) !important;
    }

    /* ── Expanders ───────────────────────────────────────────────────────── */
    [data-testid="stExpander"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow) !important;
    }

    /* ── Alerts ──────────────────────────────────────────────────────────── */
    .stAlert {
        border-radius: var(--radius) !important;
        border: 1px solid var(--border) !important;
        font-size: 0.85rem !important;
    }

    /* ── Dividers ────────────────────────────────────────────────────────── */
    hr { border-color: var(--border) !important; margin: 1rem 0 !important; }

    /* ── Scrollbar ───────────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
    /* ── Móvil ───────────────────────────────────────────────────────────── */
    @media (max-width: 640px) {
        [data-testid="stMainBlockContainer"] { padding: 3rem 1rem 2.5rem !important; }
        .page-header { flex-direction: column; gap: 0.6rem; }
        .page-header__chip { white-space: normal; }
        h1 { font-size: 1.45rem !important; }
        .kpi-card__value { font-size: 1.6rem; }
        .status-strip { gap: 0.4rem 0.9rem; }
        .card-header__left { flex-wrap: wrap; row-gap: 0.15rem; }
        .card-header__subtitle { flex-basis: 100%; }
        .kpi-card { margin-bottom: 0.15rem; }
        [class*="st-key-card-"] { padding: 0.75rem 0.8rem 0.85rem !important; }
    }
    </style>
    """
    st.html(css)


def section_label(text: str):
    """Small all-caps section divider label."""
    st.markdown(
        f'<div style="font-family:\'Open Sans\',sans-serif;font-size:0.7rem;'
        f'font-weight:700;text-transform:uppercase;letter-spacing:0.1em;'
        f'color:{COLORS["text_muted"]};padding-bottom:0.4rem;border-bottom:1px solid {COLORS["border"]};'
        f'margin-bottom:1rem;width:100%">{text}</div>',
        unsafe_allow_html=True,
    )


_MONTHS_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
              "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
_MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _period_chip_html() -> str:
    """Build the right-aligned period chip using filters in st.session_state."""
    d_from = st.session_state.get("filter_from")
    d_to   = st.session_state.get("filter_to")
    if not d_from or not d_to:
        return ""

    lang = st.session_state.get("lang", "es")
    months = _MONTHS_EN if lang == "en" else _MONTHS_ES
    days_word = "days" if lang == "en" else "días"
    span_days = (d_to - d_from).days + 1

    def _fmt(d):
        return f"{months[d.month - 1]} {d.day}"

    icon = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
        'stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>'
        '<line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>'
        '<line x1="3" y1="10" x2="21" y2="10"/></svg>'
    )
    return (
        f'<div class="page-header__chip">{icon}'
        f'<span class="page-header__chip-range">{_fmt(d_from)} → {_fmt(d_to)}</span>'
        f'<span class="page-header__chip-sep">·</span>'
        f'<span class="page-header__chip-span">{span_days} {days_word}</span>'
        f'</div>'
    )


def page_header(title: str, subtitle: str = "", show_period: bool = True):
    """Page title with optional subtitle and an auto period chip (from session filters)."""
    sub_html = (
        f'<p class="page-header__subtitle">{subtitle}</p>' if subtitle else ""
    )
    chip_html = _period_chip_html() if show_period else ""
    st.markdown(
        f'<div class="page-header">'
        f'<div class="page-header__text"><h1>{title}</h1>{sub_html}</div>'
        f'{chip_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Hero banner ─────────────────────────────────────────────────────────────
def hero_banner(
    headline_html: str,
    status_text: str = "",
    status_kind: str = "ok",
    meta_label: str = "",
    meta_value: str = "",
):
    """Big intro banner for the overview page.

    Args:
        headline_html: inline HTML — use <b>value</b> to highlight numbers.
        status_text:   e.g. "Sistema saludable", "3 alertas abiertas". Empty = no status.
        status_kind:   one of "ok" | "warn" | "crit".
        meta_label:    e.g. "ALERTAS ABIERTAS"
        meta_value:    e.g. "3"
    """
    status_cls = {
        "ok":   "",
        "warn": " hero__status--warn",
        "crit": " hero__status--crit",
    }.get(status_kind, "")

    status_html = (
        f'<div class="hero__status{status_cls}">'
        f'<span class="hero__status-dot"></span>{status_text}</div>'
        if status_text else ""
    )

    meta_html = ""
    if meta_label or meta_value:
        meta_html = (
            f'<div class="hero__right">'
            f'<span class="hero__meta-label">{meta_label}</span>'
            f'<span class="hero__meta-value">{meta_value}</span>'
            f'</div>'
        )

    st.markdown(
        f'<div class="hero"><div class="hero__grid">'
        f'<div>{status_html}<p class="hero__headline">{headline_html}</p></div>'
        f'{meta_html}'
        f'</div></div>',
        unsafe_allow_html=True,
    )


# ── Card header (sits above charts / tables) ────────────────────────────────
def card_header(
    title: str,
    subtitle: str = "",
    icon_svg: str = "",
    right_text: str = "",
):
    """Render a consistent header above a chart/table card.

    Args:
        title:      main label (e.g. "Actividad diaria")
        subtitle:   optional muted sub-label
        icon_svg:   optional raw SVG string (16px recommended)
        right_text: optional right-aligned small meta (e.g. "Últimos 30 días")
    """
    icon_html = (
        f'<span class="card-header__icon">{icon_svg}</span>' if icon_svg else ""
    )
    subtitle_html = (
        f'<span class="card-header__subtitle">{subtitle}</span>' if subtitle else ""
    )
    right_html = (
        f'<span class="card-header__right">{right_text}</span>' if right_text else ""
    )
    st.markdown(
        f'<div class="card-header">'
        f'<div class="card-header__left">{icon_html}'
        f'<span class="card-header__title">{title}</span>{subtitle_html}</div>'
        f'{right_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Arc gauges (3/4 circle progress) ────────────────────────────────────────
def _arc_svg(pct: float, accent: str) -> str:
    """Build an SVG 3/4 arc gauge. pct: 0-100."""
    # radius 40, circumference = 2π·40 ≈ 251.3
    # 3/4 arc ≈ 188.5
    full_arc = 188.5
    filled   = max(0.0, min(full_arc, full_arc * (pct / 100)))
    return (
        f'<svg viewBox="0 0 100 100">'
        # background track (full 3/4 arc in light gray)
        f'<circle cx="50" cy="50" r="40" stroke="{COLORS["border"]}" stroke-width="7" '
        f'fill="none" stroke-dasharray="{full_arc:.1f} 251.3" '
        f'stroke-linecap="round" transform="rotate(135 50 50)"/>'
        # filled progress
        f'<circle cx="50" cy="50" r="40" stroke="{accent}" stroke-width="7" '
        f'fill="none" stroke-dasharray="{filled:.1f} 251.3" '
        f'stroke-linecap="round" transform="rotate(135 50 50)"/>'
        f'</svg>'
    )


def arc_row(items: list[dict]):
    """Render a row of arc gauges. Each item: {label, pct, value?, accent?}.

    - pct:    0-100, controls arc fill
    - value:  text inside (defaults to f"{pct}%")
    - accent: color key from COLORS (defaults to "accent")
    """
    cards = []
    for it in items:
        accent = COLORS.get(it.get("accent", "accent"), COLORS["accent"])
        pct    = float(it["pct"])
        value  = it.get("value", f"{pct:.0f}%")
        label  = it["label"]
        cards.append(
            f'<div class="arc-gauge">'
            f'<div class="arc-gauge__label">{label}</div>'
            f'<div class="arc-gauge__svg-wrap">'
            f'{_arc_svg(pct, accent)}'
            f'<div class="arc-gauge__value">{value}</div>'
            f'</div>'
            f'</div>'
        )
    st.markdown(f'<div class="arc-row">{"".join(cards)}</div>', unsafe_allow_html=True)


# ── Stat list (sidebar-style compact KPI stack inside a card) ──────────────
def stat_list(items: list[dict]):
    """Render a vertical list of label→value rows as a single card.

    Each item: {"label": str, "value": str}.
    """
    rows = "".join(
        f'<div class="stat-list__item">'
        f'<span class="stat-list__label">{it["label"]}</span>'
        f'<span class="stat-list__value">{it["value"]}</span>'
        f'</div>'
        for it in items
    )
    st.markdown(f'<div class="stat-list">{rows}</div>', unsafe_allow_html=True)


# ── Tarjeta con encabezado adentro ───────────────────────────────────────────
@contextmanager
def card(key: str, title: str = "", subtitle: str = "", icon_svg: str = "",
         right_text: str = ""):
    """Contenedor con borde, con el encabezado ADENTRO de la caja.

    Antes el encabezado iba suelto encima de la gráfica y cada bloque parecía
    flotar. ``key`` tiene que ser único en la página: Streamlit lo convierte en
    la clase ``st-key-card-<key>``, que es la que estila el CSS.

        with card("diaria", t("activity_over_time"), icon_svg=ICONS["activity"]):
            st.plotly_chart(...)
    """
    with st.container(border=True, key=f"card-{key}"):
        if title:
            card_header(title, subtitle=subtitle, icon_svg=icon_svg, right_text=right_text)
        yield


def note(text: str):
    """Nota legible bajo una gráfica o un indicador (reemplaza st.caption,
    que sale al 60 % de opacidad). Acepta <b> para resaltar."""
    st.markdown(f'<p class="note">{text}</p>', unsafe_allow_html=True)


def status_strip(pill_text: str, pill_kind: str = "ok", items=()):
    """Franja de estado arriba de Inicio: una píldora (ok / warn / crit) y
    pares «etiqueta valor» separados por puntos."""
    kind_cls = {"warn": " status-pill--warn", "crit": " status-pill--crit"}.get(pill_kind, "")
    parts = [f'<span class="status-pill{kind_cls}">{pill_text}</span>']
    for label, value in items:
        parts.append(f'<span>{label} <b>{value}</b></span>')
    st.markdown(f'<div class="status-strip">{"".join(parts)}</div>', unsafe_allow_html=True)

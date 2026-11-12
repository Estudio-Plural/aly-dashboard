"""Página Conversaciones — keywords, temas y resúmenes.

Fuente: public.conversations_data (summary, keywords, flags)
"""

import json
import re
from collections import Counter

import pandas as pd
import streamlit as st

from utils.i18n import t
from utils import db
from utils.styles import COLORS, page_header, section_label
from components.charts import bar_h
from components.filters import get_filters

filters   = get_filters()
date_from = filters["date_from"]
date_to   = filters["date_to"]
lang      = st.session_state.get("lang", "es")

page_header(t("convs_page_title"), t("convs_page_sub"))

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    df_convs    = db.get_conversations_data(date_from, date_to, lang=lang)
    df_summaries = db.get_summaries(date_from, date_to, limit=20, lang=lang)
except Exception as e:
    st.error(f"Error de base de datos: {e}")
    st.stop()

# ── Parse keywords ────────────────────────────────────────────────────────────
def _parse_keywords(text: str) -> list[str]:
    """Parse a keywords text field — handles JSON arrays and CSV strings."""
    if not text or not isinstance(text, str):
        return []
    text = text.strip()
    # Try JSON array
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(k).strip().lower() for k in parsed if k]
    except (json.JSONDecodeError, ValueError):
        pass
    # Try comma / semicolon separated
    parts = re.split(r"[,;|\n]+", text)
    return [p.strip().lower() for p in parts if p.strip()]


all_keywords: list[str] = []
if not df_convs.empty and "keywords" in df_convs.columns:
    for raw in df_convs["keywords"].dropna():
        all_keywords.extend(_parse_keywords(raw))

kw_counter = Counter(all_keywords)
df_keywords = pd.DataFrame(
    kw_counter.most_common(30),
    columns=["keyword", "frequency"]
)

# ── Keywords section ──────────────────────────────────────────────────────────
section_label(t("top_keywords"))

n_convs = len(df_convs) if not df_convs.empty else 0

# Stats strip
k1, k2, k3 = st.columns(3)
with k1:
    st.metric("Conversaciones procesadas", f"{n_convs:,}")
with k2:
    st.metric("Keywords únicas", f"{len(kw_counter):,}")
with k3:
    top_kw = df_keywords.iloc[0]["keyword"].title() if not df_keywords.empty else "—"
    st.metric("Keyword #1", top_kw)

st.markdown("<div style='margin:0.75rem 0'></div>", unsafe_allow_html=True)

if df_keywords.empty:
    st.markdown(
        f"""
        <div style="background:{COLORS['bg_card']};border:1px solid {COLORS['border']};
             border-radius:10px;padding:2rem 1.5rem;text-align:center;margin-bottom:1rem">
            <div style="font-size:2rem;margin-bottom:0.5rem">💬</div>
            <p style="font-family:'Open Sans',sans-serif;font-size:0.95rem;
               color:{COLORS['text']};font-weight:600;margin:0 0 0.25rem">
                {t('top_keywords')}
            </p>
            <p style="font-family:'Open Sans',sans-serif;font-size:0.82rem;
               color:{COLORS['text_secondary']};margin:0">
                {t('no_keywords_yet')}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    col_bar, col_table = st.columns([2, 1])

    with col_bar:
        fig = bar_h(
            df_keywords.head(15), "frequency", "keyword",
            t("top_keywords"), height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown(
            f'<p style="font-family:\'Open Sans\',sans-serif;font-size:0.72rem;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.08em;'
            f'color:{COLORS["text_muted"]};margin-bottom:0.5rem">Top 30</p>',
            unsafe_allow_html=True,
        )
        # Add percentage column
        total_kw = df_keywords["frequency"].sum()
        df_display = df_keywords.copy()
        df_display["% del total"] = (df_display["frequency"] / total_kw * 100).round(1).astype(str) + "%"
        st.dataframe(
            df_display.rename(columns={
                "keyword":   t("keyword"),
                "frequency": t("frequency"),
            }),
            use_container_width=True,
            hide_index=True,
            height=380,
        )

# ── Summaries section ─────────────────────────────────────────────────────────
st.markdown("<div style='margin:1.5rem 0 0.5rem'></div>", unsafe_allow_html=True)
section_label(t("recent_summaries"))

if df_summaries.empty:
    st.markdown(
        f"""
        <div style="background:{COLORS['bg_card']};border:1px solid {COLORS['border']};
             border-radius:10px;padding:2rem 1.5rem;text-align:center">
            <div style="font-size:2rem;margin-bottom:0.5rem">📝</div>
            <p style="font-family:'Open Sans',sans-serif;font-size:0.95rem;
               color:{COLORS['text']};font-weight:600;margin:0 0 0.25rem">
                {t('recent_summaries')}
            </p>
            <p style="font-family:'Open Sans',sans-serif;font-size:0.82rem;
               color:{COLORS['text_secondary']};margin:0">
                Los resúmenes aparecerán aquí cuando el agente los genere.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    for _, row in df_summaries.iterrows():
        conv_id = str(row.get("conversation_id", "—"))[:20]
        summary = str(row.get("summary", ""))
        fecha   = str(row.get("conversation_date", ""))[:16]
        user    = str(row.get("user_number", ""))

        label = f"🗨️  {fecha}  ·  conv `{conv_id}`"
        if user:
            label += f"  ·  {user[-4:]}****"

        with st.expander(label):
            st.markdown(
                f'<p style="font-family:\'Open Sans\',sans-serif;font-size:0.875rem;'
                f'color:{COLORS["text"]};line-height:1.7;margin:0">{summary}</p>',
                unsafe_allow_html=True,
            )

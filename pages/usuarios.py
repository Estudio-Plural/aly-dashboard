"""Página Usuarios — KPIs demográficos + mapa geográfico + ranking de regiones.

El mapa es **config por bot**, no global: solo los bots cuyo ``geo`` es
``"colombia"`` en ``utils/bots.py`` renderizan el choropleth de departamentos
y el panel de cobertura territorial. Los demás (hoy ``mexico`` y ``demo``)
muestran solo el ranking de regiones a ancho completo — sin mapa mal
etiquetado ni un "% del país" que no significa nada fuera de Colombia.
"""

import datetime

import streamlit as st

from utils.i18n import t
from utils import export as deid_export, pseudonym
from utils.bots import bot_label, bot_weekly_deidentified
from utils import db
from utils.bots import bot_geo
from utils.styles import COLORS, page_header, card_header, stat_list
from components.charts import (
    bar_h, choropleth_colombia,
    colombia_region_lookup, _normalize_region,
)
from components.kpi_row import render as kpi_row, ICONS as KPI_ICONS
from components.filters import get_filters


filters   = get_filters()
date_from = filters["date_from"]
date_to   = filters["date_to"]
bot_id    = filters["bot_id"]

page_header(t("users_page_title"), t("users_page_sub"))


# ── Data fetch ───────────────────────────────────────────────────────────────
try:
    df_region = db.get_users_by_region(date_from, date_to, bot_id=bot_id)
    kpis      = db.get_user_kpis(date_from, date_to, bot_id=bot_id)
    conv_m    = db.get_conversation_metrics(date_from, date_to, bot_id=bot_id)
    deltas    = db.get_kpi_deltas(date_from, date_to, bot_id=bot_id)
except Exception as e:
    st.error(f"Error de base de datos: {e}")
    st.stop()


# ── KPI row ──────────────────────────────────────────────────────────────────
n_regions = len(df_region) if not df_region.empty else 0

kpi_row([
    {"label": t("n_users"),     "value": kpis["n_users"],
     "delta": deltas.get("users_delta"), "delta_label": t("vs_prev_period"),
     "accent": "accent", "icon": "users"},
    {"label": t("kpi_regions"), "value": n_regions,
     "delta": None, "accent": "navy", "icon": "activity"},
    {"label": "Msg / usuario",  "value": conv_m["avg_msg_per_user"],
     "delta": None, "accent": "yellow", "icon": "send"},
])

st.markdown("<div style='margin:1.4rem 0 0.25rem'></div>", unsafe_allow_html=True)


# ── Mapa + panel lateral ─────────────────────────────────────────────────────
# El mapa de departamentos solo aplica a bots colombianos (ver utils/bots.py).
has_colombia_map = bot_geo(bot_id) == "colombia"


def _render_region_ranking(limit=10):
    """Ranking de regiones por usuarios. Compartido por ambos layouts."""
    if df_region.empty:
        st.info(t("no_data"))
        return
    top = df_region.head(limit)
    st.plotly_chart(
        bar_h(top, x="n_users", y="region", height=max(220, 36 * len(top))),
        use_container_width=True,
    )


if has_colombia_map:
    lookup      = colombia_region_lookup()
    total_depts = 33  # GeoJSON tiene 33 features

    if df_region.empty:
        n_covered = 0
        unmatched = []
    else:
        matched_mask = df_region["region"].apply(
            lambda r: bool(r) and _normalize_region(r) in lookup
        )
        n_covered = int(matched_mask.sum())
        unmatched = sorted({
            str(r) for r in df_region.loc[~matched_mask, "region"] if r
        })

    pct_covered = round(n_covered / total_depts * 100) if total_depts else 0

    col_map, col_side = st.columns([2, 1])

    with col_map:
        card_header(
            title=t("region_heatmap"),
            subtitle=t("users_card_sub").format(users=kpis["n_users"], regions=n_regions),
            icon_svg=KPI_ICONS["activity"],
        )
        if df_region.empty:
            st.info(t("no_data"))
        else:
            fig_col = choropleth_colombia(df_region, "region", "n_users", height=440)
            st.plotly_chart(fig_col, use_container_width=True)
            if unmatched:
                st.caption(t("unmapped_regions").format(regions=", ".join(unmatched)))

    with col_side:
        card_header(title=t("coverage"), icon_svg=KPI_ICONS["chart"])
        stat_list([
            {"label": t("coverage_depts"), "value": f"{n_covered} / {total_depts}"},
            {"label": t("coverage_pct"),   "value": f"{pct_covered}%"},
        ])

        st.markdown("<div style='margin:0.9rem 0 0'></div>", unsafe_allow_html=True)

        card_header(title=t("region_ranking"), icon_svg=KPI_ICONS["users"])
        _render_region_ranking()

else:
    # Bot sin mapa (ej. México/Semillas): ranking a ancho completo. No se
    # muestra cobertura — "% del país" solo tiene sentido contra un GeoJSON.
    card_header(
        title=t("region_distribution"),
        subtitle=t("users_card_sub").format(users=kpis["n_users"], regions=n_regions),
        icon_svg=KPI_ICONS["users"],
    )
    _render_region_ranking(limit=15)
    st.caption(t("no_geo_map"))


# ── Exportación sin identificar ──────────────────────────────────────────────
# Para el M&E (pedido de Semillas, 2026-11-11): ID seudónimo, fecha/hora y
# alerta de riesgo, sin teléfono ni nombre. El ID sale de la misma llave que el
# Excel de los lunes (utils/pseudonym.py), así que coinciden. Sin llave no se
# ofrece: la promesa es que el ID no cambie entre exportaciones.
@st.cache_data(ttl=600, show_spinner=False)
def _deid_excel(bot_id, date_from, date_to, lang):
    raw = db.get_pseudonymous_export_data(date_from, date_to, bot_id=bot_id)
    date_to_incl = str(datetime.date.fromisoformat(date_to) - datetime.timedelta(days=1))
    return deid_export.build_excel(
        raw, pseudonym.get_key(),
        bot_id=bot_id, program=bot_label(bot_id),
        date_from=date_from, date_to_incl=date_to_incl, lang=lang,
    )


st.markdown("<div style='margin:1.6rem 0 0.25rem'></div>", unsafe_allow_html=True)
card_header(
    title=t("deid_export_title"),
    subtitle=t("deid_export_sub"),
    icon_svg=KPI_ICONS["chart"],
)
if pseudonym.get_key() is None:
    is_admin = st.session_state.get("auth_role") == "admin"
    st.caption(t("deid_export_missing_key") if is_admin else t("deid_export_unavailable"))
else:
    lang = st.session_state.get("lang", "es")
    try:
        xlsx = _deid_excel(bot_id, date_from, date_to, lang)
    except Exception as e:
        st.error(t("deid_export_error").format(e=e))
    else:
        date_to_incl = str(datetime.date.fromisoformat(date_to) - datetime.timedelta(days=1))
        st.download_button(
            label=t("deid_export_button"),
            data=xlsx,
            file_name=deid_export.file_name(bot_id, date_from, date_to_incl, lang),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            on_click="ignore",
            icon=":material/download:",
        )
        st.caption(t("deid_export_note") if bot_weekly_deidentified(bot_id) else t("deid_export_note_plain"))

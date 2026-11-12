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
from utils.styles import COLORS, page_header, card, note
from components.charts import (
    bar_h, choropleth_colombia,
    colombia_region_lookup, _normalize_region, display_region,
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
    deltas    = db.get_kpi_deltas(date_from, date_to, bot_id=bot_id)
    reg       = db.get_registered_users(date_from, date_to, bot_id=bot_id)
except Exception as e:
    st.error(f"Error de base de datos: {e}")
    st.stop()


# ── Regiones para mostrar ────────────────────────────────────────────────────
# «Regional Tolima» y «Tolima» son el mismo departamento (antes y después del
# cambio del onboarding): se agrupan para el ranking, igual que en el mapa.
if not df_region.empty:
    df_rank = (
        df_region.assign(region=df_region["region"].map(display_region))
        .groupby("region", as_index=False)["n_users"].sum()
        .sort_values("n_users", ascending=False)
    )
else:
    df_rank = df_region
n_regions = len(df_rank)

# El mapa de departamentos solo aplica a bots colombianos (ver utils/bots.py).
has_colombia_map = bot_geo(bot_id) == "colombia"
total_depts = 33  # GeoJSON tiene 33 features
if has_colombia_map and not df_region.empty:
    lookup = colombia_region_lookup()
    matched_mask = df_region["region"].apply(lambda r: bool(r) and _normalize_region(r) in lookup)
    n_covered = len({_normalize_region(r) for r in df_region.loc[matched_mask, "region"]})
    unmatched = sorted({str(r) for r in df_region.loc[~matched_mask, "region"] if r})
else:
    n_covered, unmatched = 0, []


# ── KPI row ──────────────────────────────────────────────────────────────────
# Antes: «Total usuarios 6», «Regiones 6», «6 / 33», «18 %» y «6 usuarios ·
# 6 regiones» decían lo mismo. Ahora cada tarjeta responde algo distinto.
kpi_row([
    {"label": t("kpi_active"), "value": kpis["n_users"],
     "prev": deltas.get("users_prev"),
     "delta_label": t("vs_prev_abs").format(prev=deltas.get("users_prev")),
     "accent": "accent", "icon": "users", "caption": t("kpi_active_cap")},
    ({"label": t("kpi_depts"), "value": f"{n_covered} {t('of')} {total_depts}",
      "accent": "navy", "icon": "activity", "caption": t("kpi_depts_cap")}
     if has_colombia_map else
     {"label": t("kpi_regions"), "value": n_regions,
      "accent": "navy", "icon": "activity", "caption": t("kpi_regions_cap")}),
    {"label": t("kpi_new_reg"), "value": reg["nuevos"],
     "accent": "positive", "icon": "send",
     "caption": t("kpi_new_reg_cap").format(total=f"{reg['total']:,}")},
])

st.markdown("<div style='margin:0.9rem 0 0'></div>", unsafe_allow_html=True)


def _render_region_ranking(limit=10):
    """Ranking de regiones por usuarios. Compartido por ambos layouts."""
    if df_rank.empty:
        st.info(t("no_data"))
        return
    top = df_rank.head(limit)
    st.plotly_chart(
        bar_h(top, x="n_users", y="region", height=max(200, 34 * len(top) + 40)),
        use_container_width=True, config={"displayModeBar": False},
    )


if has_colombia_map:
    col_map, col_side = st.columns([2, 1])

    with col_map:
        with card("mapa", t("region_heatmap"), icon_svg=KPI_ICONS["activity"]):
            if df_region.empty:
                st.info(t("no_data"))
            else:
                fig_col = choropleth_colombia(df_region, "region", "n_users", height=420)
                st.plotly_chart(fig_col, use_container_width=True, config={"displayModeBar": False})
                if unmatched:
                    note(t("unmapped_regions").format(regions=", ".join(unmatched)))

    with col_side:
        with card("ranking", t("region_ranking"), icon_svg=KPI_ICONS["users"]):
            _render_region_ranking()

else:
    # Bot sin mapa (ej. México/Semillas): ranking a ancho completo.
    with card("ranking", t("region_distribution"), icon_svg=KPI_ICONS["users"]):
        _render_region_ranking(limit=15)
        note(t("no_geo_map"))


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


st.markdown("<div style='margin:0.9rem 0 0'></div>", unsafe_allow_html=True)
with card("export", t("deid_export_title"), subtitle=t("deid_export_sub"),
          icon_svg=KPI_ICONS["chart"]):
    if pseudonym.get_key() is None:
        is_admin = st.session_state.get("auth_role") == "admin"
        note(t("deid_export_missing_key") if is_admin else t("deid_export_unavailable"))
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
            note(t("deid_export_note") if bot_weekly_deidentified(bot_id) else t("deid_export_note_plain"))

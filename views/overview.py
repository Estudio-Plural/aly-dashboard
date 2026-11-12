"""Página Inicio — franja de estado, indicadores de seguimiento, actividad diaria
y semanal, registro, y el horario de uso plegado al final."""

import datetime as _dt
from zoneinfo import ZoneInfo

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

from utils.i18n import t
from utils import db
from utils.bots import bot_label
from utils.styles import (
    COLORS, page_header, stat_list, card, note, status_strip,
    _MONTHS_ES, _MONTHS_EN,
)
from components.kpi_row import render as kpi_row, ICONS as KPI_ICONS
from components.filters import get_filters


# ── Plotly base layout ────────────────────────────────────────────────────────
_LAYOUT = dict(
    paper_bgcolor=COLORS["bg_card"],
    plot_bgcolor=COLORS["bg_card"],
    font=dict(family="Figtree, sans-serif", size=11, color=COLORS["text"]),
    margin=dict(l=8, r=8, t=16, b=8),
    xaxis=dict(
        gridcolor=COLORS["ramp"][0],
        linecolor=COLORS["border"],
        tickfont=dict(size=10, color=COLORS["text_secondary"]),
        showgrid=True,
    ),
    yaxis=dict(
        gridcolor=COLORS["ramp"][0],
        linecolor=COLORS["border"],
        tickfont=dict(size=10, color=COLORS["text_secondary"]),
        showgrid=True,
    ),
    hoverlabel=dict(
        bgcolor=COLORS["bg_card"],
        bordercolor=COLORS["border"],
        font=dict(family="Figtree, sans-serif", size=11),
    ),
)


TZ = ZoneInfo("America/Bogota")


def _chart_layout(**overrides):
    base = _LAYOUT.copy()
    base.update(overrides)
    return base


def _classify_flag(val) -> str:
    if not val or not isinstance(val, str):
        return "other"
    v = val.lower()
    if "high" in v:
        return "red"
    if "medium" in v:
        return "orange"
    if "red" in v or "rojo" in v or "critico" in v or "crítico" in v:
        return "red"
    if "orange" in v or "naranja" in v or "warning" in v or "advertencia" in v:
        return "orange"
    return "other"


# ── Page ─────────────────────────────────────────────────────────────────────

filters = get_filters()
date_from = filters["date_from"]
date_to   = filters["date_to"]
bot_id    = filters["bot_id"]
lang      = st.session_state.get("lang", "es")

# El título es el programa: con el selector de bot en la barra lateral, «Dashboard
# Aly» no decía qué se estaba viendo.
page_header(bot_label(bot_id), t("ov_page_sub"))


# ── Data fetch ────────────────────────────────────────────────────────────────
try:
    kpis     = db.get_user_kpis(date_from, date_to, bot_id=bot_id)
    n_msg    = db.get_messages_count(date_from, date_to, bot_id=bot_id)
    conv_m   = db.get_conversation_metrics(date_from, date_to, bot_id=bot_id)
    deltas   = db.get_kpi_deltas(date_from, date_to, bot_id=bot_id)
    df_daily = db.get_daily_activity(date_from, date_to, bot_id=bot_id)
    df_flags = db.get_flags_data(date_from, date_to, bot_id=bot_id)
    df_heat  = db.get_activity_heatmap(date_from, date_to, bot_id=bot_id)
    reg      = db.get_registered_users(date_from, date_to, bot_id=bot_id)
    ret      = db.get_returning_users(date_from, date_to, bot_id=bot_id)
    df_week  = db.get_weekly_active_users(date_from, date_to, bot_id=bot_id)
    cov      = db.get_answer_coverage(date_from, date_to, bot_id=bot_id)
    last_msg = db.get_last_activity(bot_id=bot_id)
except Exception as e:
    st.error(f"Error de base de datos: {e}")
    st.stop()


# ── Alertas: cuántas faltan por revisar ──────────────────────────────────────
# Antes el estado y «Alertas abiertas» contaban todas las rojas y naranjas del
# período, revisadas o no: marcar una como revisada no cambiaba nada aquí.
n_alerts = n_pending = n_pending_red = 0
if not df_flags.empty:
    types = df_flags["flags"].apply(_classify_flag)
    actionable = df_flags[types.isin(["red", "orange"])]
    pending = actionable["reviewed_at"].isna() if "reviewed_at" in actionable else pd.Series(True, index=actionable.index)
    n_alerts      = len(actionable)
    n_pending     = int(pending.sum())
    n_pending_red = int((pending & (types[actionable.index] == "red")).sum())

if n_alerts == 0:
    pill_kind, pill_text = "ok", t("status_no_alerts")
elif n_pending == 0:
    pill_kind, pill_text = "ok", t("status_all_reviewed")
else:
    pill_kind = "crit" if n_pending_red else "warn"
    pill_text = t("status_pending").format(n=n_pending)


def _ago(ts) -> str:
    """«hoy», «ayer», «hace 5 días» + la fecha y hora."""
    if ts is None:
        return t("last_message_none")
    today = _dt.datetime.now(TZ).date()
    days = (today - ts.date()).days
    rel = t("ago_today") if days <= 0 else t("ago_yesterday") if days == 1 else t("ago_days").format(n=days)
    months = _MONTHS_EN if lang == "en" else _MONTHS_ES
    return f"{rel} · {ts.day} {months[ts.month - 1].lower()}, {ts:%H:%M}"


status_strip(pill_text, pill_kind, [
    (t("last_message"), _ago(last_msg)),
])


# ── KPI row: lo que pide el seguimiento, no el volumen ───────────────────────
n_days_with_data = len(df_daily)
full_range = pd.date_range(start=date_from, end=date_to, freq="D", inclusive="left")
if df_daily.empty:
    df_daily = pd.DataFrame({"day": full_range, "messages": 0, "users": 0, "sessions": 0})
else:
    df_daily["day"] = pd.to_datetime(df_daily["day"])
    df_daily = (
        df_daily.set_index("day")
        .reindex(full_range, fill_value=0)
        .rename_axis("day")
        .reset_index()
    )

span_days = len(full_range) or 1
n_answered = cov["preguntas"] - cov["sin_info"]

kpi_row([
    {
        "label":       t("kpi_active"),
        "value":       kpis["n_users"],
        "prev":        deltas.get("users_prev"),
        "delta_label": t("vs_prev_abs").format(prev=deltas.get("users_prev")),
        "accent":      "accent",
        "icon":        "users",
        "caption":     t("kpi_active_cap"),
    },
    {
        "label":   t("returning_users"),
        "value":   f"{ret['vuelven']:,} {t('of')} {ret['activos']:,}",
        "accent":  "navy",
        "icon":    "activity",
        "caption": t("kpi_returning_cap"),
    },
    {
        "label":   t("answered_share"),
        "value":   f"{round(100 * n_answered / cov['preguntas'])} %" if cov["preguntas"] else "—",
        "accent":  "positive",
        "icon":    "message",
        "caption": t("kpi_answered_cap").format(a=f"{n_answered:,}", q=f"{cov['preguntas']:,}")
                   if cov["preguntas"] else "",
    },
    {
        "label":   t("kpi_pending"),
        "value":   n_pending,
        "accent":  "red" if n_pending_red else ("yellow" if n_pending else "positive"),
        "icon":    "alert-triangle",
        "caption": t("kpi_pending_cap").format(n=n_alerts),
    },
])
note(t("kpi_notes"))

st.markdown("<div style='margin:0.9rem 0 0'></div>", unsafe_allow_html=True)


# ── Actividad diaria + volumen (2/3 + 1/3) ───────────────────────────────────
col_chart, col_stats = st.columns([2, 1])

with col_chart:
    with card("diaria", t("activity_over_time"), subtitle=t("daily_sub"),
              icon_svg=KPI_ICONS["activity"]):
        if n_days_with_data == 0:
            st.info(t("no_data"))
        else:
            # Barras y un solo eje: con dos ejes y una curva suavizada, el eje
            # de usuarios marcaba fracciones y negativos (−0,111) y la curva
            # inventaba valores entre días. Las personas van en el hover.
            fig = go.Figure(go.Bar(
                x=df_daily["day"],
                y=df_daily["messages"],
                marker_color=COLORS["accent"],
                customdata=df_daily[["users"]],
                hovertemplate="%{x|%d %b}<br><b>%{y}</b> " + t("hover_messages")
                              + " · %{customdata[0]} " + t("hover_users") + "<extra></extra>",
            ))
            fig.update_layout(**_chart_layout(height=270, bargap=0.25, showlegend=False))
            # Eje X fijo al rango elegido y sin zoom: los días sin datos se ven
            # como huecos y el filtro se nota respetado.
            fig.update_xaxes(range=[pd.Timestamp(date_from) - pd.Timedelta(hours=12),
                                    pd.Timestamp(date_to) - pd.Timedelta(hours=12)],
                             fixedrange=True, showgrid=False, tickformat="%d/%m")
            y_max = int(df_daily["messages"].max())
            fig.update_yaxes(fixedrange=True, rangemode="tozero", tickformat=",d",
                             dtick=1 if y_max <= 8 else None)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            if n_days_with_data < span_days:
                note(t("sparse_data_note").format(n=n_days_with_data))

with col_stats:
    with card("volumen", t("volume_title"), icon_svg=KPI_ICONS["chart"]):
        stat_list([
            {"label": t("vol_conversations"), "value": f"{conv_m['total_conversations']:,}"},
            {"label": t("vol_messages"),      "value": f"{n_msg:,}"},
            {"label": t("vol_msg_per_conv"),  "value": f"{conv_m['avg_msg_per_conv']:.1f}"},
        ])

st.markdown("<div style='margin:0.9rem 0 0'></div>", unsafe_allow_html=True)


# ── Usuarios activos por semana + registro (2/3 + 1/3) ───────────────────────
# Semanas de lunes a domingo; las que no tienen actividad van en 0 para que el
# rango elegido se vea completo (misma convención que la actividad diaria).
col_week, col_reg = st.columns([2, 1])

with col_week:
    with card("semanal", t("weekly_active_title"), subtitle=t("weekly_active_sub"),
              icon_svg=KPI_ICONS["users"]):
        d_last = pd.Timestamp(date_to) - pd.Timedelta(days=1)  # date_to llega exclusivo
        first_monday = pd.Timestamp(date_from) - pd.Timedelta(days=pd.Timestamp(date_from).weekday())
        weeks = pd.date_range(start=first_monday, end=d_last, freq="W-MON")
        if df_week.empty:
            df_week = pd.DataFrame({"week": weeks, "users": 0})
        else:
            df_week["week"] = pd.to_datetime(df_week["week"])
            df_week = (
                df_week.set_index("week")
                .reindex(weeks, fill_value=0)
                .rename_axis("week")
                .reset_index()
            )

        if int(df_week["users"].sum()) == 0:
            st.info(t("no_data"))
        else:
            months = _MONTHS_EN if lang == "en" else _MONTHS_ES
            labels = [t("week_label").format(d=f"{w.day} {months[w.month - 1].lower()}")
                      for w in df_week["week"]]
            # Eje categórico con el lunes de cada semana: con fechas, Plotly
            # ponía las marcas en domingo y cada barra parecía de la semana
            # anterior (la barra del 12 oct decía «11 Oct»).
            fig_w = go.Figure(go.Bar(
                x=labels,
                y=df_week["users"],
                marker_color=COLORS["accent"],
                text=df_week["users"],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="%{x}<br><b>%{y}</b> " + t("hover_users") + "<extra></extra>",
            ))
            fig_w.update_layout(**_chart_layout(height=250, bargap=0.35))
            step = 2 if len(labels) > 12 else 1
            fig_w.update_xaxes(type="category", fixedrange=True, showgrid=False,
                               tickvals=labels[::step], ticktext=labels[::step])
            y_dtick = 1 if int(df_week["users"].max()) <= 8 else None
            fig_w.update_yaxes(fixedrange=True, rangemode="tozero", tickformat=",d", dtick=y_dtick)
            st.plotly_chart(fig_w, use_container_width=True, config={"displayModeBar": False})
            note(t("weekly_partial_note"))

with col_reg:
    with card("registro", t("registration_title"), icon_svg=KPI_ICONS["users"]):
        stat_list([
            {"label": t("registered_total"), "value": f"{reg['total']:,}"},
            {"label": t("registered_new"),   "value": f"{reg['nuevos']:,}"},
        ])
        note(t("registration_note"))

st.markdown("<div style='margin:0.9rem 0 0'></div>", unsafe_allow_html=True)


# ── Horario de uso: cerrado por defecto ──────────────────────────────────────
# Con pocas personas el mapa hora × día sale casi vacío; sirve para planear
# (cuándo mandar un recordatorio), no para la lectura de todos los días.
days_es = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
days_en = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
day_labels = days_en if lang == "en" else days_es

with st.expander(t("usage_hours"), icon=":material/schedule:"):
    if df_heat.empty:
        st.info(t("no_data"))
    else:
        hour_totals = df_heat.groupby("hour")["messages"].sum()
        dow_totals = df_heat.groupby("dow")["messages"].sum()
        note(t("usage_hours_note").format(
            h=f"{int(hour_totals.idxmax()):02d}:00",
            d=day_labels[int(dow_totals.idxmax())],
        ))

        matrix = np.zeros((7, 24), dtype=int)
        for _, row in df_heat.iterrows():
            matrix[int(row["dow"]), int(row["hour"])] += int(row["messages"])
        order = [1, 2, 3, 4, 5, 6, 0]  # lunes arriba
        matrix = matrix[order]
        ordered_labels = [day_labels[i] for i in order]

        fig_h = go.Figure(go.Heatmap(
            z=matrix,
            x=[f"{h:02d}" for h in range(24)],
            y=ordered_labels,
            xgap=3,
            ygap=3,
            colorscale=[[0.0, COLORS["ramp"][0]], [0.15, COLORS["ramp"][1]],
                        [0.4, COLORS["ramp"][2]], [0.7, COLORS["ramp"][3]],
                        [1.0, COLORS["ramp"][4]]],
            showscale=False,
            hovertemplate="<b>%{y}</b> · %{x}h<br>%{z} " + t("hover_messages") + "<extra></extra>",
        ))
        fig_h.update_layout(
            paper_bgcolor=COLORS["bg_card"],
            plot_bgcolor=COLORS["bg_card"],
            font=dict(family="Figtree, sans-serif", size=10),
            margin=dict(l=8, r=8, t=8, b=8),
            height=230,
            xaxis=dict(side="bottom", showgrid=False, zeroline=False,
                       linecolor=COLORS["bg_card"],
                       tickfont=dict(size=10, color=COLORS["text_secondary"]),
                       fixedrange=True, ticks=""),
            yaxis=dict(showgrid=False, zeroline=False,
                       linecolor=COLORS["bg_card"],
                       tickfont=dict(size=11, color=COLORS["text_secondary"]),
                       fixedrange=True, ticks="", autorange="reversed"),
        )
        st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})

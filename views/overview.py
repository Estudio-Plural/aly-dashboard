"""Página Inicio — hero, KPIs, growth + stat list, heatmap."""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from utils.i18n import t
from utils import db
from utils.styles import (
    COLORS, page_header, hero_banner, card_header, stat_list,
)
from components.kpi_row import render as kpi_row, ICONS as KPI_ICONS
from components.filters import get_filters


# ── Plotly base layout ────────────────────────────────────────────────────────
_LAYOUT = dict(
    paper_bgcolor=COLORS["bg_card"],
    plot_bgcolor=COLORS["bg_card"],
    font=dict(family="Open Sans, sans-serif", size=11, color=COLORS["text"]),
    margin=dict(l=8, r=8, t=16, b=8),
    xaxis=dict(
        gridcolor="#F3F4F6",
        linecolor=COLORS["border"],
        tickfont=dict(size=10, color=COLORS["text_secondary"]),
        showgrid=True,
    ),
    yaxis=dict(
        gridcolor="#F3F4F6",
        linecolor=COLORS["border"],
        tickfont=dict(size=10, color=COLORS["text_secondary"]),
        showgrid=True,
    ),
    hoverlabel=dict(
        bgcolor=COLORS["bg_card"],
        bordercolor=COLORS["border"],
        font=dict(family="Open Sans, sans-serif", size=11),
    ),
)


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

page_header(t("ov_page_title"), t("ov_page_sub"))


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
except Exception as e:
    st.error(f"Error de base de datos: {e}")
    st.stop()


# ── Hero banner ──────────────────────────────────────────────────────────────
# Derive flag counts for hero status
n_red = n_orange = 0
if not df_flags.empty:
    types = df_flags["flags"].apply(_classify_flag)
    n_red    = int((types == "red").sum())
    n_orange = int((types == "orange").sum())

if n_red > 0:
    status_kind = "crit"
    status_text = t("hero_status_crit").format(n=n_red)
elif n_orange > 0:
    status_kind = "warn"
    status_text = t("hero_status_warn").format(n=n_orange)
else:
    status_kind = "ok"
    status_text = t("hero_status_ok")

# Period span in days
try:
    import datetime as _dt
    d_from = _dt.date.fromisoformat(date_from)
    d_to   = _dt.date.fromisoformat(date_to)
    span_days = max(1, (d_to - d_from).days)
except Exception:
    span_days = 30

headline_html = t("hero_headline_days").format(
    days=span_days,
    users=f"{kpis['n_users']:,}",
    sessions=f"{kpis['n_sessions']:,}",
    msg=f"{n_msg:,}",
)

hero_banner(
    headline_html=headline_html,
    status_text=status_text,
    status_kind=status_kind,
    meta_label=t("hero_meta_label"),
    meta_value=f"{n_red + n_orange}",
)


# ── Fill daily-activity gaps across the full selected range ──────────────────
# Days with no activity render as 0 so the chart visibly spans date_from→date_to
# (date_to comes exclusive from get_filters). Makes the date filter clearly respected.
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


# ── KPI row ───────────────────────────────────────────────────────────────────
if df_daily.empty:
    spark_users = spark_sessions = spark_messages = spark_avg = []
else:
    spark_users    = df_daily["users"].tolist()
    spark_sessions = df_daily["sessions"].tolist()
    spark_messages = df_daily["messages"].tolist()
    spark_avg = (
        (df_daily["messages"] / df_daily["sessions"].replace(0, pd.NA))
        .fillna(0).round(2).tolist()
    )

delta_label = t("vs_prev_period")

kpi_row([
    {
        "label":       t("n_users"),
        "value":       kpis["n_users"],
        "delta":       deltas.get("users_delta"),
        "delta_label": delta_label,
        "accent":      "accent",
        "icon":        "users",
        "spark":       spark_users,
        "caption":     t("kpi_users_cap"),
    },
    {
        "label":       t("n_sessions"),
        "value":       kpis["n_sessions"],
        "delta":       deltas.get("sessions_delta"),
        "delta_label": delta_label,
        "accent":      "navy",
        "icon":        "message",
        "spark":       spark_sessions,
        "caption":     t("kpi_sessions_cap"),
    },
    {
        "label":       t("n_messages"),
        "value":       n_msg,
        "delta":       deltas.get("messages_delta"),
        "delta_label": delta_label,
        "accent":      "positive",
        "icon":        "send",
        "spark":       spark_messages,
        "caption":     t("kpi_messages_cap"),
    },
    {
        "label":       t("avg_msg_per_conv"),
        "value":       conv_m["avg_msg_per_conv"],
        "delta":       None,
        "delta_label": "",
        "accent":      "yellow",
        "icon":        "chart",
        "spark":       spark_avg,
        "caption":     t("kpi_avg_cap"),
    },
])

st.markdown("<div style='margin:1.4rem 0 0.25rem'></div>", unsafe_allow_html=True)


# ── Growth chart + stat list (2/3 + 1/3 grid) ────────────────────────────────
col_chart, col_stats = st.columns([2, 1])

with col_chart:
    card_header(
        title=t("activity_over_time"),
        icon_svg=KPI_ICONS["activity"],
        right_text=t("card_last_n_days").format(n=span_days),
    )

    if n_days_with_data == 0:
        st.info(t("no_data"))
    else:
        df_daily["day"] = pd.to_datetime(df_daily["day"])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_daily["day"],
            y=df_daily["messages"],
            mode="lines",
            name=t("messages_axis"),
            line=dict(color=COLORS["accent"], width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(2,115,229,0.08)",
            hovertemplate="%{x|%d %b}<br><b>%{y}</b> " + t("hover_messages") + "<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=df_daily["day"],
            y=df_daily["users"],
            mode="lines",
            name=t("n_users"),
            line=dict(color=COLORS["yellow"], width=2, dash="dot"),
            hovertemplate="%{x|%d %b}<br><b>%{y}</b> " + t("hover_users") + "<extra></extra>",
            yaxis="y2",
        ))
        fig.update_layout(
            **_chart_layout(
                height=290,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            font=dict(size=10)),
                yaxis2=dict(
                    overlaying="y", side="right",
                    gridcolor="rgba(0,0,0,0)", showgrid=False,
                    tickfont=dict(size=10, color=COLORS["text_secondary"]),
                ),
                hovermode="x unified",
            )
        )
        # Lock the x-axis to the full selected range and disable zoom/pan so the
        # filter is visibly respected (empty days show as 0, not auto-cropped).
        fig.update_xaxes(range=[date_from, date_to], fixedrange=True)
        fig.update_yaxes(fixedrange=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Surface sparse data so an empty stretch doesn't read as a broken filter.
        if n_days_with_data < span_days:
            st.caption(t("sparse_data_note").format(n=n_days_with_data))

with col_stats:
    # Derive peak hour / peak day from heatmap data
    days_es = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
    days_en = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    day_labels = days_en if st.session_state.get("lang") == "en" else days_es

    if df_heat.empty:
        peak_hour_txt = "—"
        peak_day_txt  = "—"
    else:
        hour_totals = df_heat.groupby("hour")["messages"].sum()
        peak_hour_txt = f"{int(hour_totals.idxmax()):02d}:00"
        dow_totals = df_heat.groupby("dow")["messages"].sum()
        peak_day_txt = day_labels[int(dow_totals.idxmax())]

    card_header(
        title=t("peak_hour") + " & " + t("peak_day"),
        icon_svg=KPI_ICONS["chart"],
    )
    stat_list([
        {"label": t("peak_hour"), "value": peak_hour_txt},
        {"label": t("peak_day"),  "value": peak_day_txt},
    ])

st.markdown("<div style='margin:1.2rem 0 0.25rem'></div>", unsafe_allow_html=True)


# ── Usuarios activos por semana + registro y retorno (2/3 + 1/3) ─────────────
# Semanas de lunes a domingo; las que no tienen actividad van en 0 para que el
# rango elegido se vea completo (misma convención que la actividad diaria).
col_week, col_ret = st.columns([2, 1])

with col_week:
    card_header(
        title=t("weekly_active_title"),
        subtitle=t("weekly_active_sub"),
        icon_svg=KPI_ICONS["users"],
    )
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
        fig_w = go.Figure(go.Bar(
            x=df_week["week"],
            y=df_week["users"],
            marker_color=COLORS["accent"],
            hovertemplate=t("hover_week") + " %{x|%d %b}<br><b>%{y}</b> "
                          + t("hover_users") + "<extra></extra>",
        ))
        fig_w.update_layout(**_chart_layout(height=260, bargap=0.35))
        fig_w.update_xaxes(tickformat="%d %b", fixedrange=True)
        # Con pocos usuarios Plotly pone ticks fraccionarios y ",d" los repite
        # (0, 1, 1, 2, 2…): de a uno mientras el máximo sea chico.
        y_dtick = 1 if int(df_week["users"].max()) <= 8 else None
        fig_w.update_yaxes(fixedrange=True, rangemode="tozero", tickformat=",d", dtick=y_dtick)
        st.plotly_chart(fig_w, use_container_width=True, config={"displayModeBar": False})
        st.caption(t("weekly_partial_note"))

with col_ret:
    n_answered = cov["preguntas"] - cov["sin_info"]
    answered_txt = (
        f"{round(100 * n_answered / cov['preguntas'])} % · {n_answered:,} {t('of')} {cov['preguntas']:,}"
        if cov["preguntas"] else "—"
    )
    card_header(title=t("retention_title"), icon_svg=KPI_ICONS["users"])
    stat_list([
        {"label": t("registered_total"), "value": f"{reg['total']:,}"},
        {"label": t("registered_new"),   "value": f"{reg['nuevos']:,}"},
        {"label": t("returning_users"),
         "value": f"{ret['vuelven']:,} {t('of')} {ret['activos']:,}"},
        {"label": t("answered_share"), "value": answered_txt},
    ])
    st.caption(t("retention_note") + " " + t("answered_note"))

st.markdown("<div style='margin:1.2rem 0 0.25rem'></div>", unsafe_allow_html=True)


# ── Activity heatmap (full width) ────────────────────────────────────────────
card_header(
    title=t("activity_heatmap"),
    subtitle=t("activity_heatmap_sub"),
    icon_svg=KPI_ICONS["activity"],
)

if df_heat.empty:
    st.info(t("no_data"))
else:
    # Build 7×24 matrix
    matrix = np.zeros((7, 24), dtype=int)
    for _, row in df_heat.iterrows():
        matrix[int(row["dow"]), int(row["hour"])] += int(row["messages"])

    # Reorder rows so Monday appears on top (more conventional)
    order = [1, 2, 3, 4, 5, 6, 0]
    matrix = matrix[order]
    ordered_labels = [day_labels[i] for i in order]

    fig_h = go.Figure(go.Heatmap(
        z=matrix,
        x=[f"{h:02d}" for h in range(24)],
        y=ordered_labels,
        xgap=3,
        ygap=3,
        colorscale=[
            [0.0,  "#F3F4F6"],
            [0.15, "#DBEAFE"],
            [0.4,  "#93C5FD"],
            [0.7,  "#3B82F6"],
            [1.0,  COLORS["accent"]],
        ],
        showscale=False,
        hovertemplate="<b>%{y}</b> · %{x}h<br>%{z} " + t("hover_messages") + "<extra></extra>",
    ))
    fig_h.update_layout(
        paper_bgcolor=COLORS["bg_card"],
        plot_bgcolor=COLORS["bg_card"],
        font=dict(family="Open Sans, sans-serif", size=10),
        margin=dict(l=8, r=8, t=14, b=8),
        height=240,
        xaxis=dict(
            side="bottom",
            showgrid=False, zeroline=False,
            linecolor=COLORS["bg_card"],
            tickfont=dict(size=9, color=COLORS["text_muted"]),
            fixedrange=True,
            ticks="",
        ),
        yaxis=dict(
            showgrid=False, zeroline=False,
            linecolor=COLORS["bg_card"],
            tickfont=dict(size=11, color=COLORS["text_secondary"]),
            fixedrange=True,
            ticks="",
            autorange="reversed",  # Monday on top
        ),
    )
    st.plotly_chart(fig_h, use_container_width=True)

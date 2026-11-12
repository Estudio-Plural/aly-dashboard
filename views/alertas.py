"""Página Alertas — flags detectados en conversations_data."""

import datetime
import io

import pandas as pd
import streamlit as st

from components.filters import get_filters
from components.kpi_row import render as kpi_row, ICONS as KPI_ICONS
from utils.i18n import t
from utils import db
from utils.styles import COLORS, page_header, card, note, _MONTHS_ES, _MONTHS_EN

filters   = get_filters()
date_from = filters["date_from"]
date_to   = filters["date_to"]
bot_id    = filters["bot_id"]

page_header(t("alerts_page_title"), t("alerts_page_sub"))

# ── Helpers ───────────────────────────────────────────────────────────────────
def _mask(number: str) -> str:
    """Mask phone number: first 4 digits + **** + last 2."""
    s = str(number) if number else ""
    if len(s) >= 6:
        return f"{s[:4]}****{s[-2:]}"
    return s[:2] + "****" if len(s) >= 2 else "****"


def _classify_flag(val: str) -> str:
    """Classify flag as red / orange / other based on HIGH-/MEDIUM-/LOW- prefixes."""
    if not val or not isinstance(val, str):
        return "other"
    v = val.lower()
    # Primary: bot-emitted severity prefixes
    if "high" in v:
        return "red"
    if "medium" in v:
        return "orange"
    # Fallback: legacy keyword detection
    if "red" in v or "rojo" in v or "critico" in v or "crítico" in v:
        return "red"
    if "orange" in v or "naranja" in v or "warning" in v or "advertencia" in v:
        return "orange"
    return "other"


def _flag_emoji(severity: str) -> str:
    return {"red": "🔴", "orange": "🟠"}.get(severity, "⚪")


# ── Load flags ────────────────────────────────────────────────────────────────
try:
    df_flags = db.get_flags_data(date_from, date_to, bot_id=bot_id)
except Exception as e:
    st.error(f"Error de base de datos: {e}")
    df_flags = pd.DataFrame()

lang   = st.session_state.get("lang", "es")
months = _MONTHS_EN if lang == "en" else _MONTHS_ES


def _fmt_day(ts) -> str:
    ts = pd.Timestamp(ts)
    return f"{ts.day} {months[ts.month - 1].lower()} {ts.year}"


def _local(series: pd.Series) -> pd.Series:
    """conversation_date se guarda en UTC sin zona: pasarla a GMT-5 para mostrarla."""
    return (pd.to_datetime(series, errors="coerce")
            .dt.tz_localize("UTC").dt.tz_convert("America/Bogota").dt.tz_localize(None))


# ── Classify & enrich ─────────────────────────────────────────────────────────
if not df_flags.empty:
    df_flags["_tipo"] = df_flags["flags"].apply(_classify_flag)
    # Only keep actionable flags (red and orange)
    df_flags = df_flags[df_flags["_tipo"].isin(["red", "orange"])].copy()
    # reviewed_at viene de Supabase. Es NaT cuando aún no se ha revisado.
    df_flags["reviewed_at"] = pd.to_datetime(df_flags.get("reviewed_at"), errors="coerce")
    df_flags["_fecha"] = _local(df_flags["conversation_date"])

if df_flags.empty:
    n_total = n_red_pending = n_orange_pending = n_reviewed = 0
else:
    pending = df_flags["reviewed_at"].isna()
    n_total          = len(df_flags)
    n_red_pending    = int((pending & (df_flags["_tipo"] == "red")).sum())
    n_orange_pending = int((pending & (df_flags["_tipo"] == "orange")).sum())
    n_reviewed       = int((~pending).sum())

# ── KPI row ───────────────────────────────────────────────────────────────────
# Lo que falta por hacer, no el total: antes «Sin resolver» sumaba también las
# ya revisadas, y marcar una no cambiaba ningún número. En cero no se muestra:
# tres tarjetas en 0 no dicen más que la frase de abajo.
if n_total:
    kpi_row([
        {"label": t("red_pending"),        "value": n_red_pending,
         "accent": "red",      "icon": "alert-triangle"},
        {"label": t("orange_pending"),     "value": n_orange_pending,
         "accent": "yellow",   "icon": "alert-circle"},
        {"label": t("reviewed_in_period"), "value": n_reviewed,
         "accent": "positive", "icon": "flag",
         "caption": t("reviewed_cap").format(n=n_total)},
    ])
    st.markdown("<div style='margin:0.9rem 0 0'></div>", unsafe_allow_html=True)

# ── Sin alertas: decir hasta cuándo y cuál fue la última ─────────────────────
if df_flags.empty:
    d1 = datetime.date.fromisoformat(date_from)
    d2 = datetime.date.fromisoformat(date_to) - datetime.timedelta(days=1)
    with card("sin-alertas", t("alerts_list_title"), icon_svg=KPI_ICONS["flag"]):
        st.markdown(
            f'<p style="font-family:\'Open Sans\',sans-serif;font-size:1rem;font-weight:600;'
            f'color:{COLORS["text"]};margin:0.25rem 0 0.35rem">'
            f'{t("no_alerts_range").format(d1=_fmt_day(d1), d2=_fmt_day(d2))}</p>',
            unsafe_allow_html=True,
        )
        try:
            last = db.get_last_flag(bot_id=bot_id)
        except Exception:
            last = {}
        if last:
            sev = (str(last.get("flag_severity") or "").upper()
                   or ("HIGH" if "high" in str(last.get("flags", "")).lower() else "MEDIUM"))
            note(t("last_alert").format(
                d=_fmt_day(last["conversation_date"]),
                sev=t("sev_red") if sev == "HIGH" else t("sev_orange"),
                state=t("state_reviewed") if pd.notna(last.get("reviewed_at")) else t("state_pending"),
            ))
        else:
            note(t("last_alert_none"))
    st.stop()


# ── Exportación (para el equipo de respuesta) ────────────────────────────────
def _alerts_excel(rows: pd.DataFrame) -> io.BytesIO:
    """Excel con transcripción. Lleva el teléfono completo A PROPÓSITO: es para
    el equipo que contacta a la persona (ver CLAUDE.md, «Números de teléfono»)."""
    conv_ids = rows["conversation_id"].dropna().astype(str).tolist()
    df_msgs  = db.get_messages_by_conversation_ids(conv_ids)

    def _transcript(conv_id):
        if df_msgs.empty:
            return ""
        msgs = df_msgs[df_msgs["conversation_id"].astype(str) == str(conv_id)]
        return "\n".join(f"[{r['role'].upper()}] {r['message']}" for _, r in msgs.iterrows())

    def _reasoning(flag_text):
        """Extract reason after HIGH-/MEDIUM-/LOW- prefix."""
        if not flag_text:
            return ""
        for prefix in ("HIGH-", "MEDIUM-", "LOW-", "high-", "medium-", "low-"):
            if flag_text.startswith(prefix):
                return flag_text[len(prefix):]
        return flag_text

    export_df = rows[["_fecha", "conversation_id", "user_number", "flags", "_tipo", "summary"]].copy()
    export_df["reasoning"]     = export_df["flags"].apply(_reasoning)
    export_df["transcripcion"] = export_df["conversation_id"].apply(_transcript)
    export_df = export_df.rename(columns={
        "_fecha":          "Fecha (GMT-5)",
        "conversation_id": "Conversación",
        "user_number":     "Teléfono",
        "flags":           "Flag completo",
        "_tipo":           "Severidad",
        "summary":         "Resumen",
        "reasoning":       "Razón del flag",
        "transcripcion":   "Transcripción",
    })
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Alertas")
    buf.seek(0)
    return buf


# ── Lista: cada alerta es un desplegable ─────────────────────────────────────
# Antes había una tabla y debajo los mismos registros como desplegables: cada
# alerta aparecía dos veces. La tabla mostraba además el conversation_id, que
# empieza con el teléfono (lo que la columna «Usuario» enmascaraba).
with card("lista", t("alerts_list_title"),
          subtitle=t("alerts_list_sub").format(n=n_total), icon_svg=KPI_ICONS["flag"]):
    col_toggle, col_export = st.columns([3, 1])
    with col_toggle:
        hide_reviewed = st.toggle(t("hide_reviewed"), value=False)
    working = df_flags[df_flags["reviewed_at"].isna()] if hide_reviewed else df_flags
    with col_export:
        st.download_button(
            label=t("export_alerts"),
            data=_alerts_excel(working),
            file_name=f"alertas_{date_from}_{date_to}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help=t("export_alerts_hint"),
            icon=":material/download:",
            use_container_width=True,
        )

    if working.empty:
        note(t("status_all_reviewed"))

    for _, row in working.iterrows():
        # `id` es la PK de conversations_data. `conversation_id` NO es único
        # (el bot lo reusa entre conversaciones distintas del mismo usuario),
        # así que nunca sirve como identidad de fila.
        row_id      = row.get("id")
        fecha       = pd.Timestamp(row["_fecha"])
        flag        = str(row.get("flags", ""))
        summary     = str(row.get("summary", "")) if row.get("summary") else ""
        severity    = row.get("_tipo", "other")
        reviewed_at = row.get("reviewed_at")
        is_reviewed = pd.notna(reviewed_at)
        state = (f"✅ {t('reviewed_on').format(d=_fmt_day(reviewed_at))}" if is_reviewed
                 else t("state_pending"))
        label = (f"{_flag_emoji(severity)}  {_fmt_day(fecha)}, {fecha:%H:%M}  ·  "
                 f"{_mask(row.get('user_number'))}  ·  {state}")

        with st.expander(label):
            color = COLORS["red"] if severity == "red" else COLORS["text"]
            st.markdown(
                f'<p style="font-family:\'Open Sans\',sans-serif;font-size:0.72rem;'
                f'font-weight:700;text-transform:uppercase;letter-spacing:0.06em;'
                f'color:{COLORS["text_muted"]};margin:0 0 0.25rem">{t("flag_label")}</p>'
                f'<p style="font-family:\'Open Sans\',sans-serif;font-size:0.9rem;'
                f'color:{color};margin:0 0 0.75rem">{flag}</p>',
                unsafe_allow_html=True,
            )
            if summary:
                st.markdown(
                    f'<p style="font-family:\'Open Sans\',sans-serif;font-size:0.72rem;'
                    f'font-weight:700;text-transform:uppercase;letter-spacing:0.06em;'
                    f'color:{COLORS["text_muted"]};margin:0 0 0.25rem">{t("summary_label")}</p>'
                    f'<p style="font-family:\'Open Sans\',sans-serif;font-size:0.9rem;'
                    f'color:{COLORS["text"]};line-height:1.6;margin:0 0 0.5rem">{summary}</p>',
                    unsafe_allow_html=True,
                )

            # Key por PK, no por conversation_id: dos filas con el mismo
            # conversation_id generaban keys duplicadas y Streamlit tumbaba la
            # página entera con StreamlitDuplicateElementKey.
            checkbox_key = f"rev_{row_id}"
            st.session_state.setdefault(checkbox_key, is_reviewed)
            checked = st.checkbox(t("mark_reviewed"), key=checkbox_key)
            # Persistimos a Supabase solo cuando hay cambio real respecto al
            # estado en DB. El rerun trae la fila actualizada (con reviewed_at).
            if checked != is_reviewed:
                if checked:
                    db.mark_flag_reviewed(row_id)
                else:
                    db.unmark_flag_reviewed(row_id)
                st.rerun()

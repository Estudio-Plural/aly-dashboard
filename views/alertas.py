"""Página Alertas — flags detectados en conversations_data."""

import io

import pandas as pd
import streamlit as st

from components.filters import get_filters
from components.kpi_row import render as kpi_row, ICONS as KPI_ICONS
from utils.i18n import t
from utils import db
from utils.styles import COLORS, page_header, card_header

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

# ── Classify & enrich ─────────────────────────────────────────────────────────
if not df_flags.empty:
    df_flags["_tipo"] = df_flags["flags"].apply(_classify_flag)
    # Only keep actionable flags (red and orange)
    df_flags = df_flags[df_flags["_tipo"].isin(["red", "orange"])].copy()
    n_red    = int((df_flags["_tipo"] == "red").sum())
    n_orange = int((df_flags["_tipo"] == "orange").sum())
    n_total  = n_red + n_orange
else:
    n_red = n_orange = n_total = 0

# ── KPI row ───────────────────────────────────────────────────────────────────
kpi_row([
    {"label": t("red_flags"),    "value": n_red,    "delta": None,
     "accent": "red",    "icon": "alert-triangle"},
    {"label": t("orange_flags"), "value": n_orange, "delta": None,
     "accent": "yellow", "icon": "alert-circle"},
    {"label": t("open_flags"),   "value": n_total,  "delta": None,
     "accent": "navy",   "icon": "flag"},
])
st.markdown("<div style='margin:1rem 0 0.5rem'></div>", unsafe_allow_html=True)

# ── Flags table ───────────────────────────────────────────────────────────────
card_header(
    title=t("flags_title"),
    subtitle=f"{n_total} {t('open_flags').lower()}" if n_total else "",
    icon_svg=KPI_ICONS["flag"],
)

if df_flags.empty:
    st.markdown(
        f"""
        <div style="background:{COLORS['bg_card']};border:1px solid {COLORS['border']};
             border-radius:10px;padding:2.5rem 1.5rem;text-align:center;margin-top:0.5rem">
            <div style="font-size:2.5rem;margin-bottom:0.75rem">🚩</div>
            <p style="font-family:'Open Sans',sans-serif;font-size:1rem;
               color:{COLORS['text']};font-weight:600;margin:0 0 0.35rem">
                {t('no_flags')}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # ── "Hide reviewed" toggle ────────────────────────────────────────────────
    hide_reviewed = st.toggle(t("hide_reviewed"), value=False)

    # reviewed_at viene de Supabase. Es NaT cuando aún no se ha revisado.
    df_flags["reviewed_at"] = pd.to_datetime(df_flags.get("reviewed_at"), errors="coerce")

    working = df_flags.copy()
    if hide_reviewed:
        working = working[working["reviewed_at"].isna()]

    # Build display dataframe
    display = working[["conversation_date", "conversation_id", "user_number", "flags", "_tipo"]].copy()
    display["user_number"] = display["user_number"].apply(_mask)
    display["flags"] = display.apply(
        lambda r: f"{_flag_emoji(r['_tipo'])} {r['flags']}", axis=1
    )
    display["conversation_date"] = pd.to_datetime(display["conversation_date"]).dt.strftime("%Y-%m-%d %H:%M")
    display = display.drop(columns=["_tipo"])

    display = display.rename(columns={
        "conversation_date": t("date_col"),
        "conversation_id":   "Conversación",
        "user_number":       "Usuario",
        "flags":             t("type_col"),
    })

    st.dataframe(display, use_container_width=True, hide_index=True)

    # ── Flags Excel export ────────────────────────────────────────────────────
    # Fetch transcripts for all flagged conversations
    conv_ids = working["conversation_id"].dropna().astype(str).tolist()
    df_msgs  = db.get_messages_by_conversation_ids(conv_ids)

    def _transcript(conv_id):
        if df_msgs.empty:
            return ""
        rows = df_msgs[df_msgs["conversation_id"].astype(str) == str(conv_id)]
        lines = [f"[{r['role'].upper()}] {r['message']}" for _, r in rows.iterrows()]
        return "\n".join(lines)

    def _reasoning(flag_text):
        """Extract reason after HIGH-/MEDIUM-/LOW- prefix."""
        if not flag_text:
            return ""
        for prefix in ("HIGH-", "MEDIUM-", "LOW-", "high-", "medium-", "low-"):
            if flag_text.startswith(prefix):
                return flag_text[len(prefix):]
        return flag_text

    export_df = working[["conversation_date", "conversation_id", "user_number", "flags", "_tipo", "summary"]].copy()
    export_df["reasoning"]   = export_df["flags"].apply(_reasoning)
    export_df["transcripcion"] = export_df["conversation_id"].apply(_transcript)
    export_df = export_df.rename(columns={
        "conversation_date": "Fecha",
        "conversation_id":   "Conversación",
        "user_number":       "Teléfono",
        "flags":             "Flag completo",
        "_tipo":             "Severidad",
        "summary":           "Resumen",
        "reasoning":         "Razón del flag",
        "transcripcion":     "Transcripción",
    })

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Alertas")
    buf.seek(0)

    st.download_button(
        label=t("export_alerts"),
        data=buf,
        file_name=f"alertas_{date_from}_{date_to}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help=t("export_alerts_hint"),
    )

    # ── Per-flag detail expanders ─────────────────────────────────────────────
    st.markdown("<div style='margin:1.2rem 0 0.25rem'></div>", unsafe_allow_html=True)
    card_header(
        title="Detalle de conversaciones",
        subtitle=f"{len(working)} registros",
        icon_svg=KPI_ICONS["message"],
    )

    for _, row in working.iterrows():
        # `id` es la PK de conversations_data. `conversation_id` NO es único
        # (el bot lo reusa entre conversaciones distintas del mismo usuario),
        # así que sirve para mostrar pero nunca como identidad de fila.
        row_id       = row.get("id")
        conv_id      = str(row.get("conversation_id", "—"))
        fecha        = str(row.get("conversation_date", ""))[:16]
        flag         = str(row.get("flags", ""))
        summary      = str(row.get("summary", "")) if row.get("summary") else ""
        severity     = row.get("_tipo", "other")
        emoji        = _flag_emoji(severity)
        reviewed_at  = row.get("reviewed_at")
        is_reviewed  = pd.notna(reviewed_at)
        reviewed_tag = f"  ✅ {pd.Timestamp(reviewed_at).strftime('%Y-%m-%d %H:%M')}" if is_reviewed else ""

        with st.expander(f"{emoji}  {fecha}  ·  `{conv_id}`{reviewed_tag}"):
            st.markdown(
                f'<p style="font-family:\'Open Sans\',sans-serif;font-size:0.78rem;'
                f'font-weight:700;text-transform:uppercase;color:{COLORS["text_muted"]};margin:0 0 0.25rem">'
                f'Flag</p>'
                f'<p style="font-family:\'Open Sans\',sans-serif;font-size:0.875rem;'
                f'color:{COLORS["red"]};margin:0 0 0.75rem">{flag}</p>',
                unsafe_allow_html=True,
            )
            if summary:
                st.markdown(
                    f'<p style="font-family:\'Open Sans\',sans-serif;font-size:0.78rem;'
                    f'font-weight:700;text-transform:uppercase;color:{COLORS["text_muted"]};margin:0 0 0.25rem">'
                    f'Resumen</p>'
                    f'<p style="font-family:\'Open Sans\',sans-serif;font-size:0.875rem;'
                    f'color:{COLORS["text"]};line-height:1.6;margin:0">{summary}</p>',
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

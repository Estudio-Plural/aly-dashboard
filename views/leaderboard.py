"""Página Conversaciones (antes Leaderboard): las personas del período y, al
elegir una, sus resúmenes, transcripciones y palabras clave."""

import io
import json
import re
from collections import Counter

import pandas as pd
import streamlit as st

from utils.i18n import t
from utils import db
from utils.styles import COLORS, page_header, card, note
from components.filters import get_filters
from components.kpi_row import ICONS as KPI_ICONS

filters   = get_filters()
date_from = filters["date_from"]
date_to   = filters["date_to"]
bot_id    = filters["bot_id"]
lang      = st.session_state.get("lang", "es")

page_header(t("lb_page_title"), t("lb_page_sub"))

df = db.get_leaderboard(date_from, date_to, limit=200, bot_id=bot_id)

if df.empty:
    st.info(t("lb_no_data"))
    st.stop()

# Count red+orange flags per user in Python (avoids phone number format mismatches)
def _is_actionable_flag(val):
    if not val or not isinstance(val, str):
        return False
    v = val.lower()
    return any(kw in v for kw in ("high", "medium", "red", "rojo", "critico", "orange", "naranja", "warning", "advertencia"))

df_flags_raw = db.get_flags_data(date_from, date_to, bot_id=bot_id)
if not df_flags_raw.empty:
    df_flags_raw = df_flags_raw[df_flags_raw["flags"].apply(_is_actionable_flag)]
    flag_counts = df_flags_raw.groupby("user_number").size().reset_index(name="n_flags")
    # Normalize: strip leading zeros / whitespace for robust matching
    flag_counts["user_number"] = flag_counts["user_number"].astype(str).str.strip()
    df["_client_norm"] = df["client_number"].astype(str).str.strip()
    df = df.merge(flag_counts.rename(columns={"user_number": "_client_norm"}), on="_client_norm", how="left")
    df["n_flags"] = df["n_flags"].fillna(0).astype(int)
    df = df.drop(columns=["_client_norm"])
else:
    df["n_flags"] = 0

# ── Prepare data ──────────────────────────────────────────────────────────────
df = df.reset_index(drop=True)
df.index = df.index + 1  # 1-based rank


def _mask(number):
    s = str(number)
    return s[:4] + "****" + s[-2:] if len(s) >= 8 else s[:3] + "****"


def _mask_name(name):
    """El nombre del perfil de WhatsApp, enmascarado: "María López" → "M**** L****"."""
    return " ".join(w[0] + "****" for w in str(name).split())


df["display_name"] = df.apply(
    lambda r: _mask_name(r["name"]) if pd.notna(r.get("name")) and str(r.get("name", "")).strip() else _mask(r["client_number"]),
    axis=1,
)


# ── Tabla: todas las personas del período ────────────────────────────────────
# Antes había un podio y un top 10 en barras encima de la tabla: tres vistas de
# los mismos números, y el detalle (lo valioso) quedaba al final. Ahora la
# tabla va primero y el detalle se abre con el selector o con la casilla.
cols_to_show = ["display_name", "country", "total_messages", "total_conversations",
                "days_active", "last_seen", "n_flags"]
display_df = df[cols_to_show].copy()
display_df["last_seen"] = pd.to_datetime(display_df["last_seen"]).dt.strftime("%d/%m/%Y")
display_df.columns = [
    t("lb_user"), t("lb_country"), t("lb_messages"), t("lb_conversations"),
    t("lb_days_active"), t("lb_last_seen"), t("lb_flags"),
]
col_config = {
    t("lb_messages"):      st.column_config.NumberColumn(format="%d", help=t("lb_messages_help")),
    t("lb_conversations"): st.column_config.NumberColumn(format="%d"),
    t("lb_days_active"):   st.column_config.NumberColumn(format="%d"),
    t("lb_flags"):         st.column_config.NumberColumn(format="%d"),
}

# La elección se guarda por número y no por posición: al cambiar de fechas la
# tabla se reordena y una posición apuntaría a otra persona. El número no se
# muestra (el selector enseña el nombre enmascarado).
numbers = df["client_number"].astype(str).tolist()


def _pick_label(number):
    r = df.iloc[numbers.index(number)]
    return f"{r['display_name']} · {int(r['total_messages']):,} {t('hover_messages')}"


def _on_table_select():
    rows = st.session_state["conv_table"].selection.rows
    st.session_state["conv_pick"] = numbers[rows[0]] if rows else None


if st.session_state.get("conv_pick") not in numbers:
    st.session_state["conv_pick"] = None

with card("personas", t("lb_engagement"), subtitle=t("lb_click_hint"),
          icon_svg=KPI_ICONS["users"]):
    st.selectbox(t("lb_pick"), options=numbers, format_func=_pick_label,
                 key="conv_pick", placeholder=t("lb_pick_none"))
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select=_on_table_select,
        selection_mode="single-row",
        column_config=col_config,
        key="conv_table",
    )


# ── User detail panel ─────────────────────────────────────────────────────────

def _parse_keywords(text: str) -> list:
    """Parse a keywords text field — handles JSON arrays and CSV strings."""
    if not text or not isinstance(text, str):
        return []
    text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(k).strip().lower() for k in parsed if k]
    except (json.JSONDecodeError, ValueError):
        pass
    parts = re.split(r"[,;|\n]+", text)
    return [p.strip().lower() for p in parts if p.strip()]


def _render_wordcloud(df_convs):
    try:
        from wordcloud import WordCloud
    except ImportError:
        st.warning("wordcloud package not installed. Run: pip install wordcloud")
        return

    if df_convs.empty:
        st.info(t("no_keywords_yet"))
        return

    all_kws = []
    for raw in df_convs["keywords"].dropna():
        all_kws.extend(_parse_keywords(raw))

    if not all_kws:
        st.info(t("no_keywords_yet"))
        return

    # Los keywords ya vienen en el idioma activo desde la DB (summary_i18n /
    # keywords_i18n los escribe el bot). No se traduce en la UI.
    freq = Counter(all_kws)

    accent = COLORS["accent"]

    def _color_func(*args, **kwargs):
        return accent

    wc = WordCloud(
        width=800,
        height=260,
        background_color=COLORS["bg_card"],
        color_func=_color_func,
        max_words=40,
        prefer_horizontal=0.85,
    ).generate_from_frequencies(freq)

    buf = io.BytesIO()
    wc.to_image().save(buf, format="PNG")
    buf.seek(0)
    st.image(buf, use_container_width=True)

    # Keyword frequency table
    rows = [(w, c) for w, c in sorted(freq.items(), key=lambda x: -x[1])][:30]
    df_kw = pd.DataFrame(rows, columns=[t("keyword"), t("frequency")])
    st.dataframe(df_kw, use_container_width=True, hide_index=True, height=280)


def _render_summaries(df_convs):
    has_any = False
    for _, row in df_convs.iterrows():
        summary = str(row.get("summary", "")).strip()
        if not summary or summary == "None":
            continue
        has_any = True
        # Sin el conversation_id: empieza con el teléfono de la persona.
        fecha   = str(row.get("conversation_date", ""))[:16]
        label   = f"🗨️  {fecha}"
        with st.expander(label):
            st.html(
                f'<p style="font-family:\'Figtree\',sans-serif;font-size:0.875rem;'
                f'color:{COLORS["text"]};line-height:1.7;margin:0">{summary}</p>'
            )
    if not has_any:
        st.info(t("lb_no_summaries"))


def _render_chat_bubble(role, text, ts):
    is_user    = str(role).lower() == "user"
    align      = "flex-end"         if is_user else "flex-start"
    bg         = COLORS["accent"]   if is_user else COLORS["border"]
    txt_color  = "#FFFFFF"           if is_user else COLORS["text"]
    role_label = t("lb_role_user")  if is_user else t("lb_role_assistant")
    meta_color = "rgba(255,255,255,0.65)" if is_user else COLORS["text_muted"]
    st.html(f"""
    <div style="display:flex;justify-content:{align};margin-bottom:0.5rem">
      <div style="max-width:75%;background:{bg};border-radius:12px;
           padding:0.6rem 0.85rem;box-shadow:0 1px 2px rgba(0,0,0,0.06)">
        <div style="font-family:'Figtree',sans-serif;font-size:0.72rem;
             font-weight:700;color:{meta_color};margin-bottom:0.2rem">{role_label}</div>
        <div style="font-family:'Figtree',sans-serif;font-size:0.875rem;
             color:{txt_color};line-height:1.6">{text}</div>
        <div style="font-family:'Figtree',sans-serif;font-size:0.68rem;
             color:{meta_color};margin-top:0.3rem;text-align:right">{ts}</div>
      </div>
    </div>
    """)


def _render_transcripts_from_msgs(df_msgs):
    """Render transcripts grouped by conversation_id directly from users_interactions."""
    if df_msgs.empty:
        st.info(t("lb_no_transcripts"))
        return

    rendered_any = False
    for conv_id, group in df_msgs.groupby("conversation_id", sort=False):
        group = group.sort_values("timestamp").reset_index(drop=True)
        first_ts = str(group["timestamp"].iloc[0])[:16]
        n_msgs   = len(group)
        label    = f"💬  {first_ts}  ·  {n_msgs} {t('lb_messages_short')}"
        rendered_any = True
        with st.expander(label):
            for _, msg in group.iterrows():
                _render_chat_bubble(
                    msg.get("role", ""),
                    str(msg.get("message", "")),
                    str(msg.get("timestamp", ""))[:16],
                )


# ── Detalle de la persona elegida ────────────────────────────────────────────
pick = st.session_state.get("conv_pick")
if pick is not None:
    user_row     = df.iloc[numbers.index(pick)]
    user_number  = user_row["client_number"]
    display_name = user_row["display_name"]

    st.markdown("<div style='margin:0.9rem 0 0'></div>", unsafe_allow_html=True)
    # El teléfono completo se muestra a propósito en el detalle (ver CLAUDE.md):
    # es lo que el equipo necesita para contactar a la persona.
    with card("detalle", f"{t('lb_detail_for')} {display_name}",
              subtitle=f"📱 {user_number} · " + t("lb_conv_days").format(
                  c=int(user_row["total_conversations"]), d=int(user_row["days_active"])),
              icon_svg=KPI_ICONS["users"]):
        df_convs = db.get_user_conversations(user_number, date_from, date_to, bot_id=bot_id, lang=lang)
        df_msgs  = db.get_user_messages(user_number, date_from, date_to, bot_id=bot_id)

        if df_msgs.empty and df_convs.empty:
            st.info(t("lb_no_conv_data"))
        else:
            # Resúmenes y transcripciones primero (lo más útil); la nube al final.
            tab_sum, tab_trans, tab_wc = st.tabs([
                t("lb_tab_summaries"),
                t("lb_tab_transcripts"),
                t("lb_tab_wordcloud"),
            ])
            with tab_sum:
                _render_summaries(df_convs)
            with tab_trans:
                _render_transcripts_from_msgs(df_msgs)
            with tab_wc:
                _render_wordcloud(df_convs)

"""Sidebar — logo, nav, filters. Writes to st.session_state for all pages."""

import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from utils.i18n import t

# UI opera en GMT-5 (Colombia/México). "Hoy" debe leerse en esa zona, no en
# la del servidor (el contenedor de producción corre en UTC).
TZ = ZoneInfo("America/Bogota")


def _today() -> datetime.date:
    return datetime.datetime.now(TZ).date()


# Material Symbols icons (rendered natively by Streamlit — consistent mono line style)
NAV_ITEMS = [
    ("analysis", [
        ("pages/overview.py",    "nav_home",        ":material/dashboard:"),
        ("pages/usuarios.py",    "nav_users",       ":material/group:"),
    ]),
    ("operation", [
        ("pages/alertas.py",     "nav_alerts",      ":material/warning:"),
        ("pages/leaderboard.py", "nav_leaderboard", ":material/emoji_events:"),
    ]),
]


def _render_logo():
    st.markdown(
        """
        <div style="padding:0.5rem 0 1.25rem;display:flex;align-items:center;gap:0.65rem">
            <div style="
                width:34px;height:34px;border-radius:9px;
                background:linear-gradient(135deg,#0273e5 0%,#110079 100%);
                display:flex;align-items:center;justify-content:center;
                box-shadow:0 2px 6px rgba(2,115,229,0.25)">
                <span style="font-family:'Oswald',sans-serif;font-size:1.1rem;
                    font-weight:700;color:#FFFFFF;letter-spacing:0.02em">A</span>
            </div>
            <div style="display:flex;flex-direction:column;line-height:1.1">
                <span style="font-family:'Oswald',sans-serif;font-size:1.35rem;
                    font-weight:600;color:#0C1214;letter-spacing:0.02em">Aly</span>
                <span style="font-family:'Open Sans',sans-serif;font-size:0.66rem;
                    color:#9CA3AF;text-transform:uppercase;letter-spacing:0.09em;
                    margin-top:0.1rem">Dashboard</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_nav():
    """Custom grouped navigation using st.page_link with Material icons."""
    section_labels = {
        "analysis":  {"es": "Análisis",  "en": "Analysis"},
        "operation": {"es": "Operación", "en": "Operations"},
    }
    lang = st.session_state.get("lang", "es")

    for section_id, items in NAV_ITEMS:
        label = section_labels[section_id][lang]
        st.markdown(
            f'<div class="nav-section">{label}</div>',
            unsafe_allow_html=True,
        )
        for page_path, label_key, icon in items:
            st.page_link(page_path, label=t(label_key), icon=icon)

    st.markdown(
        '<hr style="margin:1rem 0 0.75rem">',
        unsafe_allow_html=True,
    )


def render_sidebar():
    """Render the global sidebar. Pages read filters from st.session_state."""
    with st.sidebar:
        _render_logo()
        _render_nav()

        # ── Bot selector (role-aware) ─────────────────────────────────────────
        # El rol del usuario logueado (auth.require_login) limita qué bots ve:
        #   auth_allowed_bots == None  → todos (admin)
        #   auth_allowed_bots == [...]  → solo esos bot_ids
        from utils.bots import bot_label
        from utils.db import get_available_bot_ids

        available_bots = get_available_bot_ids()
        allowed = st.session_state.get("auth_allowed_bots")  # None = sin restricción

        if allowed is None:
            bot_options = available_bots
        else:
            # Intersecta con lo que hay en la DB; si la discovery no trae el bot
            # del usuario (p. ej. aún sin datos), lo dejamos igual para no dejarlo
            # sin opción.
            bot_options = [b for b in available_bots if b in allowed] or list(allowed)

        # Asegura que la selección actual sea válida para este rol (cubre cambio
        # de usuario en el mismo navegador tras logout/login).
        if st.session_state.get("selected_bot") not in bot_options:
            st.session_state["selected_bot"] = bot_options[0] if bot_options else "apapachar"

        if len(bot_options) > 1:
            st.selectbox(
                "Bot",
                options=bot_options,
                key="selected_bot",
                format_func=bot_label,
                help="Selecciona qué programa ver en el dashboard",
            )
        else:
            # Un solo bot permitido → sin selector, queda fijado y se muestra como chip.
            st.session_state["selected_bot"] = bot_options[0] if bot_options else "apapachar"
            st.markdown(
                '<div class="bot-locked">Bot<br>'
                f'<b>{bot_label(st.session_state["selected_bot"])}</b></div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<hr style="margin:0.75rem 0">',
            unsafe_allow_html=True,
        )

        # ── Date filters ──────────────────────────────────────────────────────
        st.markdown(
            '<p style="font-family:\'Open Sans\',sans-serif;font-size:0.66rem;'
            'font-weight:700;text-transform:uppercase;letter-spacing:0.1em;'
            'color:#9CA3AF;margin-bottom:0.5rem">' + t("filters") + '</p>',
            unsafe_allow_html=True,
        )

        today = _today()

        if "filter_from" not in st.session_state:
            st.session_state["filter_from"] = today - datetime.timedelta(days=30)
        if "filter_to" not in st.session_state:
            st.session_state["filter_to"] = today

        # Los presets escriben en session_state ANTES de que se rendericen los
        # date_input en el siguiente run (los callbacks on_click corren entre
        # runs). Asignar después de instanciar el widget no actualiza la UI.
        def _set_range(days: int):
            t_today = _today()
            st.session_state["filter_from"] = t_today - datetime.timedelta(days=days)
            st.session_state["filter_to"]   = t_today

        st.date_input(t("date_from"), key="filter_from")
        st.date_input(t("date_to"),   key="filter_to")

        col_a, col_b = st.columns(2)
        with col_a:
            st.button("7d",  use_container_width=True, on_click=_set_range, args=(7,))
        with col_b:
            st.button("30d", use_container_width=True, on_click=_set_range, args=(30,))

        # ── Cuenta: conectado como + logout ───────────────────────────────────
        auth_name = st.session_state.get("auth_name")
        auth_role = st.session_state.get("auth_role")
        if auth_name:
            role_label = t(f"role_{auth_role}") if auth_role else ""
            st.markdown(
                f'<div style="margin-top:1.25rem;padding-top:0.75rem;'
                f'border-top:1px solid #E5E7EB;font-family:\'Open Sans\',sans-serif">'
                f'<div style="font-size:0.62rem;text-transform:uppercase;'
                f'letter-spacing:0.08em;color:#9CA3AF">{t("logged_in_as")}</div>'
                f'<div style="font-size:0.85rem;font-weight:600;color:#0C1214">{auth_name}</div>'
                f'<div style="font-size:0.7rem;color:#6B7280">{role_label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        authenticator = st.session_state.get("_authenticator")
        if authenticator is not None:
            authenticator.logout(t("logout"), location="sidebar")

        # ── Footer ────────────────────────────────────────────────────────────
        st.markdown(
            f'<div style="margin-top:0.75rem;padding:0.5rem 0;'
            f'font-family:\'Open Sans\',sans-serif;font-size:0.68rem;'
            f'color:#9CA3AF;border-top:1px solid #E5E7EB">'
            f'{t("last_updated")}<br>'
            f'<span style="color:#6B7280;font-weight:500;font-variant-numeric:tabular-nums">'
            f'{datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M")} GMT-5</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_topbar():
    """Render the global top bar — language selector pinned to the top-right.

    Rendered in app.py above the page content, so it shows on every page.
    """
    lang = st.session_state.get("lang", "es")
    if "lang_seg" not in st.session_state:
        st.session_state["lang_seg"] = "EN" if lang == "en" else "ES"

    def _on_lang_change():
        st.session_state.lang = "en" if st.session_state.get("lang_seg") == "EN" else "es"

    # Push the control to the right; wrap it so CSS can target the topbar only.
    _, col_lang = st.columns([6, 1])
    with col_lang:
        st.markdown('<div class="topbar-lang">', unsafe_allow_html=True)
        st.segmented_control(
            "language",
            options=["ES", "EN"],
            key="lang_seg",
            on_change=_on_lang_change,
            label_visibility="collapsed",
        )
        st.markdown('</div>', unsafe_allow_html=True)


def get_filters() -> dict:
    """Return the current filter values from session_state (for use in pages)."""
    today = _today()
    date_from = st.session_state.get("filter_from", today - datetime.timedelta(days=30))
    date_to   = st.session_state.get("filter_to",   today)
    date_to_excl = date_to + datetime.timedelta(days=1)
    bot_id = st.session_state.get("selected_bot", "apapachar")
    return {
        "date_from": str(date_from),
        "date_to":   str(date_to_excl),
        "bot_id":    bot_id,
    }

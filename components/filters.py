"""Sidebar — logo, nav, filters. Writes to st.session_state for all pages."""

import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from utils.i18n import t
from utils.styles import COLORS

# UI opera en GMT-5 (Colombia/México). "Hoy" debe leerse en esa zona, no en
# la del servidor (el contenedor de producción corre en UTC).
TZ = ZoneInfo("America/Bogota")


def _today() -> datetime.date:
    return datetime.datetime.now(TZ).date()


# Material Symbols icons (rendered natively by Streamlit — consistent mono line style)
# «Conversaciones» vive en views/leaderboard.py (antes se llamaba así); el
# archivo conserva el nombre para no romper los enlaces guardados (/leaderboard).
NAV_ITEMS = [
    ("analysis", [
        ("views/overview.py",    "nav_home",        ":material/dashboard:"),
        ("views/usuarios.py",    "nav_users",       ":material/group:"),
        ("views/leaderboard.py", "nav_leaderboard", ":material/forum:"),
    ]),
    ("operation", [
        ("views/alertas.py",     "nav_alerts",      ":material/warning:"),
    ]),
]


def _render_logo(bot_id=None):
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
                    color:#4B5563;text-transform:uppercase;letter-spacing:0.09em;
                    margin-top:0.1rem">Dashboard</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_program_logo(bot_id)


def _render_program_logo(bot_id):
    """Logo del programa del bot seleccionado (hoy solo Apapáchar), bajo la marca."""
    from utils.bots import bot_logo
    from utils.branding import logo_data_uri

    logo = bot_logo(bot_id) if bot_id else None
    uri = logo_data_uri(logo[0]) if logo else None
    if not uri:
        return
    st.markdown(
        f'<div style="margin:-0.35rem 0 1.15rem;display:flex;justify-content:center">'
        f'<img src="{uri}" alt="{logo[1]}" '
        f'style="width:128px;max-width:100%;height:auto;display:block"></div>',
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


def _resolve_bot_options() -> list:
    """Bots que puede ver el usuario logueado, y deja ``selected_bot`` válido.

    El rol (auth.require_login) limita qué bots ve:
      auth_allowed_bots == None  → todos (admin)
      auth_allowed_bots == [...]  → solo esos bot_ids
    Va antes de dibujar la marca, que necesita saber qué bot está elegido para
    mostrar el logo del programa.
    """
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
    return bot_options


def render_sidebar():
    """Render the global sidebar. Pages read filters from st.session_state."""
    with st.sidebar:
        bot_options = _resolve_bot_options()
        _render_logo(st.session_state.get("selected_bot"))
        _render_nav()

        # ── Bot selector (role-aware) ─────────────────────────────────────────
        from utils.bots import bot_label

        if len(bot_options) > 1:
            st.selectbox(
                t("bot_label"),
                options=bot_options,
                key="selected_bot",
                format_func=bot_label,
                help=t("bot_help"),
            )
        else:
            # Un solo bot permitido → sin selector, queda fijado y se muestra como chip.
            st.session_state["selected_bot"] = bot_options[0] if bot_options else "apapachar"
            st.markdown(
                f'<div class="bot-locked">{t("bot_label")}<br>'
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
            f'color:{COLORS["text_muted"]};margin-bottom:0.5rem">' + t("filters") + '</p>',
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

        # 90d: con pocas personas, 30 días suele mostrar «solo 7 días con
        # actividad»; un trimestre deja ver la tendencia.
        for col, days in zip(st.columns(3), (7, 30, 90)):
            with col:
                st.button(f"{days}d", use_container_width=True, on_click=_set_range, args=(days,))

        # ── Cuenta: conectado como + idioma + logout ─────────────────────────
        auth_name = st.session_state.get("auth_name")
        auth_role = st.session_state.get("auth_role")
        if auth_name:
            role_label = t(f"role_{auth_role}") if auth_role else ""
            st.markdown(
                f'<div style="margin-top:1.25rem;padding-top:0.75rem;'
                f'border-top:1px solid {COLORS["border"]};font-family:\'Open Sans\',sans-serif">'
                f'<div style="font-size:0.62rem;text-transform:uppercase;'
                f'letter-spacing:0.08em;color:{COLORS["text_muted"]}">{t("logged_in_as")}</div>'
                f'<div style="font-size:0.85rem;font-weight:600;color:{COLORS["text"]}">{auth_name}</div>'
                f'<div style="font-size:0.72rem;color:{COLORS["text_secondary"]}">{role_label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        _render_language()
        authenticator = st.session_state.get("_authenticator")
        if authenticator is not None:
            authenticator.logout(t("logout"), location="sidebar")


def _render_language():
    """ES / EN en la barra lateral. Antes ocupaba una franja propia arriba de
    cada página, que empujaba todo el contenido hacia abajo."""
    lang = st.session_state.get("lang", "es")
    if "lang_seg" not in st.session_state:
        st.session_state["lang_seg"] = "EN" if lang == "en" else "ES"

    def _on_lang_change():
        # segmented_control deja None si se vuelve a tocar la opción elegida.
        if st.session_state.get("lang_seg") is None:
            st.session_state["lang_seg"] = "EN" if st.session_state.get("lang") == "en" else "ES"
        st.session_state.lang = "en" if st.session_state.get("lang_seg") == "EN" else "es"

    st.segmented_control(
        t("language"),
        options=["ES", "EN"],
        key="lang_seg",
        on_change=_on_lang_change,
    )


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

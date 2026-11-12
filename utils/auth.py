"""Autenticación + autorización por roles.

Login usuario/contraseña vía ``streamlit-authenticator`` (0.4.x). Credenciales,
cookie y mapeo rol→bots viven en ``st.secrets`` (``.streamlit/secrets.toml`` en
local; en producción, el mismo archivo en /opt/aly-dashboard). Las contraseñas se guardan como hash
bcrypt — nunca en texto plano.

Roles:
  - ``admin``     → ve todos los bots (selector completo).
  - ``apapachar`` → bloqueado al bot ``apapachar`` (datos de Colombia).

El mapeo rol→bots se define en la sección ``[roles]`` del secrets. ``"*"`` = todos
los bots disponibles en la DB. Resuelto a ``None`` (sentinel "sin restricción")
por ``_allowed_bots``; ``components/filters.py`` aplica el filtro al selector.
"""

# El dashboard corre sobre Python 3.9 del sistema; la sintaxis `X | None` en
# anotaciones (PEP 604) recién existe en 3.10. Diferir las anotaciones a strings
# evita evaluarlas en runtime y mantiene compatibilidad con 3.9.
from __future__ import annotations

import copy
from collections.abc import Mapping

import streamlit as st
import streamlit_authenticator as stauth

from utils.i18n import t


def _to_plain(obj):
    """Convierte recursivamente los AttrDict de st.secrets a dict/list mutables.

    ``streamlit-authenticator`` MUTA el dict de credenciales (escribe
    ``logged_in``, ``failed_login_attempts``); st.secrets es read-only, así que
    hay que copiarlo a estructuras nativas antes de pasárselo.
    """
    if isinstance(obj, Mapping):
        return {k: _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_plain(v) for v in obj]
    return obj


def _load_config() -> dict:
    """Lee credenciales + cookie + mapeo de roles desde st.secrets."""
    credentials = copy.deepcopy(_to_plain(st.secrets["credentials"]))
    cookie = st.secrets["cookie"]
    roles = {k: list(v) for k, v in _to_plain(st.secrets["roles"]).items()}
    return {
        "credentials": credentials,
        "cookie_name": cookie["name"],
        "cookie_key": cookie["key"],
        "cookie_expiry_days": float(cookie.get("expiry_days", 30)),
        "roles": roles,
    }


def _allowed_bots(role: str | None, role_map: dict) -> list[str] | None:
    """Resuelve los bot_ids permitidos para un rol.

    Devuelve ``None`` cuando el rol puede ver todo (``"*"`` en su lista), o la
    lista explícita de bot_ids en caso contrario.
    """
    allowed = role_map.get(role, [])
    if "*" in allowed:
        return None  # sin restricción → todos los bots
    return list(allowed)


def _render_login_header():
    """Bloque de marca centrado sobre el formulario de login: el logo de
    Equimundo (dueño del programa Aly) y el nombre del dashboard. Si falta el
    archivo del logo, queda la marca «A» de antes."""
    from utils.branding import logo_data_uri

    uri = logo_data_uri("equimundo.png")
    if uri:
        mark = (
            f'<img src="{uri}" alt="Equimundo" style="width:104px;height:104px;'
            'border-radius:16px;box-shadow:0 4px 14px rgba(17,0,121,0.12);display:block">'
        )
    else:
        mark = (
            '<div style="width:56px;height:56px;border-radius:14px;'
            'background:linear-gradient(135deg,#0273e5 0%,#110079 100%);'
            'display:flex;align-items:center;justify-content:center;'
            'box-shadow:0 4px 14px rgba(2,115,229,0.3)">'
            "<span style=\"font-family:'Oswald',sans-serif;font-size:1.9rem;"
            'font-weight:700;color:#FFFFFF;letter-spacing:0.02em">A</span></div>'
        )
    # Sin sesión no hay nada que navegar: el sidebar vacío ocupaba un cuarto de
    # la pantalla. Este CSS solo se inyecta en la pantalla de login.
    st.html(
        "<style>"
        '[data-testid="stSidebar"], [data-testid="stExpandSidebarButton"],'
        '[data-testid="stSidebarCollapseButton"] { display: none !important; }'
        '[data-testid="stForm"] h1, [data-testid="stForm"] h2, [data-testid="stForm"] h3'
        " { color: var(--text) !important; font-size: 1.15rem !important; }"
        "</style>"
    )
    st.markdown(
        '<div style="display:flex;flex-direction:column;align-items:center;'
        'gap:0.7rem;margin:3rem 0 1.25rem">'
        f"{mark}"
        "<span style=\"font-family:'Oswald',sans-serif;font-size:1.6rem;"
        'font-weight:600;color:#0C1214;letter-spacing:0.02em">Aly Dashboard</span>'
        "<span style=\"font-family:'Open Sans',sans-serif;font-size:0.88rem;"
        'color:#374151">Seguimiento del asistente de WhatsApp</span>'
        "</div>",
        unsafe_allow_html=True,
    )


def require_login() -> dict:
    """Puerta de autenticación. Renderiza el login y detiene la app si no hay
    sesión válida. Llamar en ``app.py`` antes de la nav y las páginas.

    Cuando hay sesión, deja en ``st.session_state`` las claves ``auth_role``,
    ``auth_allowed_bots`` (None=todos), ``auth_name``, ``auth_username`` y
    ``_authenticator`` (para el botón de logout del sidebar), y devuelve un dict
    con esos valores.
    """
    try:
        config = _load_config()
    except (KeyError, FileNotFoundError):
        st.error(
            "Falta la configuración de autenticación. Crea "
            "`.streamlit/secrets.toml` (ver `.streamlit/secrets.toml.example`) "
            "o, en producción, `/opt/aly-dashboard/.streamlit/secrets.toml`."
        )
        st.stop()

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie_name"],
        config["cookie_key"],
        config["cookie_expiry_days"],
        auto_hash=False,  # las contraseñas ya vienen hasheadas (bcrypt) en secrets
    )

    # Hidrata la sesión desde la cookie sin renderizar el formulario.
    authenticator.login(location="unrendered")

    if st.session_state.get("authentication_status") is not True:
        # Aún no autenticado → mostrar pantalla de login y detener todo lo demás.
        # Columna central angosta: el formulario a todo el ancho se veía como
        # un campo de búsqueda. En móvil las columnas se apilan solas.
        _, mid, _ = st.columns([1, 1.25, 1])
        with mid:
            _render_login_header()
            authenticator.login(
                location="main",
                fields={
                    "Form name": t("login_title"),
                    "Username": t("login_username"),
                    "Password": t("login_password"),
                    "Login": t("login_button"),
                },
            )
            if st.session_state.get("authentication_status") is False:
                st.error(t("login_error"))
        st.stop()

    # Autenticado ────────────────────────────────────────────────────────────
    username = st.session_state.get("username")
    name = st.session_state.get("name")
    roles = st.session_state.get("roles") or []
    role = roles[0] if roles else None
    allowed = _allowed_bots(role, config["roles"])

    st.session_state["auth_role"] = role
    st.session_state["auth_allowed_bots"] = allowed
    st.session_state["auth_name"] = name
    st.session_state["auth_username"] = username
    st.session_state["_authenticator"] = authenticator

    return {
        "username": username,
        "name": name,
        "role": role,
        "allowed_bots": allowed,
    }

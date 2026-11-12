"""Dashboard AlyBot — entry point with multi-page navigation."""

import streamlit as st
from dotenv import load_dotenv

from utils.styles import inject as inject_styles
from utils.i18n import t
from utils.auth import require_login
from utils.branding import brand_path
from components.filters import render_sidebar

load_dotenv()

st.set_page_config(
    page_title="Aly · Panel de seguimiento",
    page_icon=brand_path("aly-favicon-64.png"),
    layout="wide",
    # "auto": abierta en escritorio y cerrada en el celular, donde tapaba todo.
    initial_sidebar_state="auto",
)

inject_styles()

# Session state defaults
if "lang" not in st.session_state:
    st.session_state.lang = "es"

# Auth gate — renders the login screen and st.stop()s if not authenticated.
# Past this line the user is logged in; their role + allowed bots live in
# st.session_state (auth_role / auth_allowed_bots), read by the bot selector.
require_login()

# Filter state is initialized in components/filters.py when the sidebar renders

# Define pages
pages = [
    st.Page("views/overview.py",        title="Inicio",          icon="📊"),
    st.Page("views/usuarios.py",         title="Usuarios",        icon="👥"),
    st.Page("views/alertas.py",          title="Alertas",         icon="🚨"),
    st.Page("views/leaderboard.py",      title="Conversaciones",  icon="💬"),
]

pg = st.navigation(pages, position="hidden")

# Sidebar — logo + filters (rendered on every page)
render_sidebar()

pg.run()

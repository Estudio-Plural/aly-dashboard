"""Dashboard AlyBot — entry point with multi-page navigation."""

import streamlit as st
from dotenv import load_dotenv

from utils.styles import inject as inject_styles
from utils.i18n import t
from utils.auth import require_login
from components.filters import render_sidebar, render_topbar

load_dotenv()

st.set_page_config(
    page_title="Dashboard Aly",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
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
    st.Page("views/leaderboard.py",      title="Leaderboard",     icon="🏆"),
]

pg = st.navigation(pages, position="hidden")

# Sidebar — logo + filters (rendered on every page)
render_sidebar()

# Top bar — language selector pinned top-right (rendered on every page)
render_topbar()

pg.run()

"""Bilingual (ES / EN) string lookup."""

import streamlit as st

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ---- Auth ----
    "login_title": {"es": "Iniciar sesión", "en": "Login"},
    "login_username": {"es": "Usuario", "en": "Username"},
    "login_password": {"es": "Contraseña", "en": "Password"},
    "login_button": {"es": "Entrar", "en": "Sign in"},
    "login_error": {"es": "Usuario o contraseña incorrectos.", "en": "Invalid username or password."},
    "logout": {"es": "Cerrar sesión", "en": "Logout"},
    "logged_in_as": {"es": "Conectado como", "en": "Logged in as"},
    "role_admin": {"es": "Administrador", "en": "Administrator"},
    "role_apapachar": {"es": "Apapachar · Colombia", "en": "Apapachar · Colombia"},
    "role_mexico": {"es": "Semillas · México", "en": "Semillas · Mexico"},

    # ---- Sidebar nav ----
    "nav_home":        {"es": "Inicio",      "en": "Home"},
    "nav_users":       {"es": "Usuarios",    "en": "Users"},
    "nav_alerts":      {"es": "Alertas",     "en": "Alerts"},
    "nav_leaderboard": {"es": "Leaderboard", "en": "Leaderboard"},

    # ---- Sidebar / Filters ----
    "filters": {"es": "Filtros", "en": "Filters"},
    "date_range": {"es": "Rango de fechas", "en": "Date range"},
    "date_from": {"es": "Desde", "en": "From"},
    "date_to": {"es": "Hasta", "en": "To"},
    "program": {"es": "Programa", "en": "Program"},
    "all": {"es": "Todos", "en": "All"},
    "language": {"es": "Idioma", "en": "Language"},
    "export_excel": {"es": "Exportar Excel", "en": "Export Excel"},
    "export_hint": {"es": "Descarga los datos filtrados.", "en": "Download filtered data."},

    # ---- Section headers ----
    "users_title": {"es": "USUARIOS", "en": "USERS"},
    "flags_title": {"es": "ALERTAS", "en": "FLAGS"},
    "bugs_title": {"es": "ERRORES", "en": "BUGS"},
    "insights_title": {"es": "INSIGHTS", "en": "INSIGHTS"},
    "reporting_title": {"es": "REPORTES", "en": "REPORTING"},

    # ---- KPIs ----
    "n_users": {"es": "Total usuarios", "en": "Total users"},
    "n_sessions": {"es": "Sesiones", "en": "Sessions"},
    "n_messages": {"es": "Mensajes", "en": "Messages"},

    # ---- Charts ----
    "time_of_day": {"es": "Mensajes por hora del día", "en": "Messages by time of day"},
    "hour_axis": {"es": "Hora", "en": "Hour"},
    "messages_axis": {"es": "Mensajes", "en": "Messages"},
    "hover_messages": {"es": "mensajes", "en": "messages"},
    "hover_users": {"es": "usuarios", "en": "users"},
    "by_country": {"es": "Usuarios por país", "en": "Users by country"},
    "by_gender": {"es": "Usuarios por género", "en": "Users by gender"},
    "by_region": {"es": "Usuarios por región", "en": "Users by region"},
    "region_map": {"es": "Distribución geográfica", "en": "Geographic distribution"},
    "who_is_using": {"es": "¿Quién lo usa?", "en": "Who is using it?"},
    "specifics": {"es": "Detalles de uso", "en": "Usage specifics"},
    "no_data": {"es": "Sin datos disponibles aún.", "en": "No data available yet."},

    # ---- Placeholders ----
    "coming_soon": {"es": "Próximamente", "en": "Coming soon"},
    "flags_desc": {
        "es": "Monitoreo de alertas rojas/naranjas generadas por el agente.",
        "en": "Monitoring of red/orange flags raised by the agent.",
    },
    "bugs_desc": {
        "es": "Registro de errores detectados durante las conversaciones.",
        "en": "Log of errors detected during conversations.",
    },
    "insights_desc": {
        "es": "Tres insights accionables generados automáticamente con IA a partir de las conversaciones recientes.",
        "en": "Three actionable insights automatically generated with AI from recent conversations.",
    },
    "reporting_desc": {
        "es": "Temas frecuentes y preguntas principales detectadas con NLP.",
        "en": "Frequent topics and top questions detected with NLP.",
    },
    "flags_requires": {
        "es": "Requiere columna `flag_type` en `users_interactions`.",
        "en": "Requires `flag_type` column in `users_interactions`.",
    },
    "insights_requires": {
        "es": "Requiere integración con Claude API.",
        "en": "Requires Claude API integration.",
    },
    "reporting_requires": {
        "es": "Requiere extracción de temas con NLP/LLM.",
        "en": "Requires NLP/LLM topic extraction.",
    },

    # ---- Overview page ----
    "ov_page_title":       {"es": "Dashboard Aly", "en": "Aly Dashboard"},
    "ov_page_sub":         {"es": "Resumen operacional del bot de WhatsApp",
                            "en": "Operational summary of the WhatsApp bot"},
    "activity_over_time":  {"es": "Actividad diaria", "en": "Daily activity"},
    "activity_heatmap":    {"es": "Mapa de actividad", "en": "Activity heatmap"},
    "activity_heatmap_sub":{"es": "Hora × día de la semana", "en": "Hour × day of the week"},
    "avg_msg_per_conv":    {"es": "Mensajes / conversación", "en": "Messages / conversation"},
    "vs_prev_period":      {"es": "vs período anterior", "en": "vs previous period"},
    "sparse_data_note":    {"es": "Solo {n} día(s) con actividad en el rango seleccionado.",
                            "en": "Only {n} day(s) with activity in the selected range."},
    # KPI captions (one-line explanation under each metric)
    "kpi_users_cap":       {"es": "Personas que interactuaron con Aly",
                            "en": "People who interacted with Aly"},
    "kpi_sessions_cap":    {"es": "Conversaciones iniciadas con Aly",
                            "en": "Conversations started with Aly"},
    "kpi_messages_cap":    {"es": "Total de mensajes intercambiados",
                            "en": "Total messages exchanged"},
    "kpi_avg_cap":         {"es": "Promedio de mensajes por conversación",
                            "en": "Average messages per conversation"},
    "peak_hour":           {"es": "Hora pico", "en": "Peak hour"},
    "peak_day":            {"es": "Día más activo", "en": "Most active day"},
    "total_convs":         {"es": "Conversaciones", "en": "Conversations"},
    # Registro y retorno (seguimiento M&E)
    "weekly_active_title": {"es": "Usuarios activos por semana", "en": "Weekly active users"},
    "weekly_active_sub":   {"es": "Personas que escribieron al menos una vez en la semana (lunes a domingo)",
                            "en": "People who sent at least one message that week (Monday to Sunday)"},
    "hover_week":          {"es": "Semana del", "en": "Week of"},
    "weekly_partial_note": {"es": "La primera y la última semana pueden estar incompletas según el rango elegido.",
                            "en": "The first and last weeks may be partial, depending on the selected range."},
    "retention_title":     {"es": "Indicadores de seguimiento", "en": "Follow-up indicators"},
    "answered_share":      {"es": "Respondidas con el material", "en": "Answered from the material"},
    "answered_note":       {"es": "Respondidas: preguntas cuya respuesta no fue «No tengo esa información». No cuentan saludos, agradecimientos ni despedidas.",
                            "en": "Answered: questions whose reply was not \"I don't have that information\". Greetings, thanks and goodbyes don't count."},
    "registered_total":    {"es": "Registrados (acumulado)", "en": "Registered (to date)"},
    "registered_new":      {"es": "Nuevos registros en el período", "en": "New registrations in the period"},
    "returning_users":     {"es": "Volvieron en 2+ semanas", "en": "Returned in 2+ weeks"},
    "of":                  {"es": "de", "en": "of"},
    "retention_note":      {"es": "Registrados: quienes completaron el registro inicial (en México, aceptar el aviso de privacidad). Volvieron: usuarios activos del período que escribieron en dos o más semanas distintas.",
                            "en": "Registered: people who completed the initial sign-up (in Mexico, accepting the privacy notice). Returned: active users in the period who wrote in two or more different weeks."},

    # ---- Hero banner ----
    "hero_status_ok":       {"es": "Sistema saludable",          "en": "System healthy"},
    "hero_status_warn":     {"es": "{n} alertas en seguimiento", "en": "{n} flags under review"},
    "hero_status_crit":     {"es": "{n} alertas críticas",       "en": "{n} critical flags"},
    "hero_headline_days":   {"es": "En los últimos <b>{days}</b> días, AlyBot atendió <b>{users}</b> usuarios en <b>{sessions}</b> conversaciones, con <b>{msg}</b> mensajes intercambiados.",
                             "en": "Over the past <b>{days}</b> days, AlyBot served <b>{users}</b> users across <b>{sessions}</b> conversations, exchanging <b>{msg}</b> messages."},
    "hero_meta_label":      {"es": "ALERTAS ABIERTAS",           "en": "OPEN FLAGS"},

    # ---- Card header subtitles ----
    "card_last_n_days":     {"es": "Últimos {n} días", "en": "Last {n} days"},

    # ---- Usuarios page ----
    "users_page_title":    {"es": "Usuarios", "en": "Users"},
    "users_page_sub":      {"es": "Demografía y distribución geográfica", "en": "Demographics & geographic distribution"},
    "demographics":        {"es": "Demografía", "en": "Demographics"},
    "hourly_dist":         {"es": "Distribución horaria", "en": "Hourly distribution"},
    "country_map":         {"es": "Distribución por país", "en": "Country distribution"},
    "region_heatmap":      {"es": "Distribución por departamento (Colombia)",
                            "en": "Distribution by department (Colombia)"},
    "coverage":            {"es": "Cobertura geográfica", "en": "Geographic coverage"},
    "coverage_depts":      {"es": "Departamentos",        "en": "Departments"},
    "coverage_pct":        {"es": "% del país",           "en": "% of country"},
    "region_ranking":      {"es": "Top regiones",         "en": "Top regions"},
    "region_distribution": {"es": "Distribución por región",
                            "en": "Distribution by region"},
    "no_geo_map":          {"es": "Este programa aún no tiene mapa geográfico: su onboarding no define una lista de regiones.",
                            "en": "This program has no geographic map yet: its onboarding does not define a region list."},
    "kpi_countries":       {"es": "Países",            "en": "Countries"},
    "kpi_regions":         {"es": "Regiones",          "en": "Regions"},
    "kpi_top_country":     {"es": "País principal",    "en": "Top country"},
    "kpi_top_region":      {"es": "Región principal",  "en": "Top region"},
    "users_card_sub":      {"es": "{users} usuarios · {regions} regiones",
                            "en": "{users} users · {regions} regions"},
    "unmapped_regions":    {"es": "⚠️ Regiones sin mapear: {regions}",
                            "en": "⚠️ Unmapped regions: {regions}"},

    # ---- Conversaciones page ----
    "convs_page_title":    {"es": "Conversaciones", "en": "Conversations"},
    "convs_page_sub":      {"es": "Temas, keywords y resúmenes", "en": "Topics, keywords & summaries"},
    "top_keywords":        {"es": "Keywords más frecuentes", "en": "Top keywords"},
    "top_topics":          {"es": "Temas principales", "en": "Top topics"},
    "recent_summaries":    {"es": "Resúmenes recientes", "en": "Recent summaries"},
    "keyword":             {"es": "Keyword", "en": "Keyword"},
    "frequency":           {"es": "Frecuencia", "en": "Frequency"},
    "no_keywords_yet":     {
        "es": "Las keywords se poblarán cuando el agente procese conversaciones.",
        "en": "Keywords will populate once the agent processes conversations.",
    },

    # ---- Alertas page ----
    "alerts_page_title":   {"es": "Alertas", "en": "Alerts"},
    "alerts_page_sub":     {"es": "Flags y errores detectados por el bot", "en": "Bot-detected flags and errors"},
    "red_flags":           {"es": "Alertas rojas", "en": "Red flags"},
    "orange_flags":        {"es": "Alertas naranja", "en": "Orange flags"},
    "open_flags":          {"es": "Sin resolver", "en": "Unresolved"},
    "no_flags":            {
        "es": "No hay alertas registradas para este período.",
        "en": "No flags recorded for this period.",
    },
    "flags_setup":         {
        "es": "Para activar las alertas, agrega la columna `flag_type` (red | orange) en `users_interactions`.",
        "en": "To enable flags, add a `flag_type` column (red | orange) to `users_interactions`.",
    },
    "date_col":            {"es": "Fecha", "en": "Date"},
    "type_col":            {"es": "Tipo", "en": "Type"},
    "status_col":          {"es": "Estado", "en": "Status"},
    "description_col":     {"es": "Descripción", "en": "Description"},
    "export_alerts":       {"es": "Exportar Alertas", "en": "Export Flags"},
    "deid_export_title":   {"es": "Exportación sin identificar", "en": "De-identified export"},
    "deid_export_sub":     {"es": "ID seudónimo, fecha y hora, y alerta de riesgo. Sin teléfono ni nombre.",
                            "en": "Pseudonymous ID, date and time, and risk flag. No phone number or name."},
    "deid_export_button":  {"es": "Descargar Excel", "en": "Download Excel"},
    "deid_export_note":    {"es": "Usa el período del filtro. Cada persona tiene el mismo ID en todas las exportaciones y en el Excel de los lunes. La hoja «Cómo leer» explica cada columna.",
                            "en": "Uses the filter period. Each person keeps the same ID across exports and in the Monday Excel. The «How to read» sheet explains each column."},
    "deid_export_note_plain": {"es": "Usa el período del filtro. Cada persona tiene el mismo ID en todas las exportaciones. La hoja «Cómo leer» explica cada columna.",
                               "en": "Uses the filter period. Each person keeps the same ID across exports. The «How to read» sheet explains each column."},
    "deid_export_unavailable": {"es": "La exportación todavía no está disponible.", "en": "The export isn't available yet."},
    "deid_export_missing_key": {"es": "Falta PSEUDONYM_KEY en los secrets (clave de primer nivel, arriba de cualquier [sección]). Tiene que ser la misma llave del reporte semanal.",
                                "en": "PSEUDONYM_KEY is missing from secrets (top-level key, above any [section]). It must be the same key as the weekly report."},
    "deid_export_error":   {"es": "No se pudo generar la exportación: {e}", "en": "Could not build the export: {e}"},
    "export_alerts_hint":  {"es": "Descarga las alertas del período filtrado.", "en": "Download flags for the filtered period."},
    "mark_reviewed":       {"es": "Marcar como revisado", "en": "Mark as reviewed"},
    "hide_reviewed":       {"es": "Ocultar revisados", "en": "Hide reviewed"},
    "reviewed_badge":      {"es": "✅ Revisado", "en": "✅ Reviewed"},

    # ---- Leaderboard page ----
    "lb_page_title":       {"es": "Leaderboard", "en": "Leaderboard"},
    "lb_page_sub":         {"es": "Usuarios más activos en el período seleccionado", "en": "Most active users in the selected period"},
    "lb_rank":             {"es": "Pos.", "en": "Rank"},
    "lb_user":             {"es": "Usuario", "en": "User"},
    "lb_messages":         {"es": "Mensajes", "en": "Messages"},
    "lb_conversations":    {"es": "Conversaciones", "en": "Conversations"},
    "lb_days_active":      {"es": "Días activo", "en": "Days active"},
    "lb_avg_msg":          {"es": "Msg/conv", "en": "Msg/conv"},
    "lb_last_seen":        {"es": "Última vez", "en": "Last seen"},
    "lb_country":          {"es": "País", "en": "Country"},
    "lb_top_stats":        {"es": "Podio", "en": "Podium"},
    "lb_engagement":       {"es": "Tabla completa", "en": "Full table"},
    "lb_no_data":          {"es": "Sin datos para el período seleccionado.", "en": "No data for the selected period."},
    "lb_detail_for":       {"es": "Detalle de", "en": "Detail for"},
    "lb_no_conv_data":     {"es": "Sin conversaciones en este período.", "en": "No conversations in this period."},
    "lb_tab_wordcloud":    {"es": "Nube de palabras", "en": "Word cloud"},
    "lb_tab_summaries":    {"es": "Resúmenes", "en": "Summaries"},
    "lb_tab_transcripts":  {"es": "Transcripciones", "en": "Transcripts"},
    "lb_no_summaries":     {"es": "Sin resúmenes disponibles.", "en": "No summaries available."},
    "lb_no_transcripts":   {"es": "Sin mensajes disponibles.", "en": "No messages available."},
    "lb_messages_short":   {"es": "msgs", "en": "msgs"},
    "lb_role_user":        {"es": "Usuario", "en": "User"},
    "lb_role_assistant":   {"es": "Asistente", "en": "Assistant"},
    "lb_click_hint":       {"es": "Haz clic en la casilla a la izquierda de un usuario para ver su detalle.", "en": "Click the checkbox to the left of a user to see their details."},
    "lb_flags":            {"es": "Flags 🚩", "en": "Flags 🚩"},

    # ---- Misc ----
    "dashboard_title": {"es": "Dashboard AlyBot", "en": "AlyBot Dashboard"},
    "last_updated": {"es": "Última actualización", "en": "Last updated"},
}


def t(key: str) -> str:
    """Return translated string for the current language."""
    lang = st.session_state.get("lang", "es")
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    return entry.get(lang, entry.get("es", key))

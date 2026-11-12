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
    "nav_leaderboard": {"es": "Conversaciones", "en": "Conversations"},

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
    "ov_page_sub":         {"es": "Resumen del período: quién usó a Aly, si volvió y si encontró respuesta",
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
    "alerts_page_sub":     {"es": "Alertas de riesgo detectadas en las conversaciones", "en": "Risk alerts detected in conversations"},
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
    "lb_page_title":       {"es": "Conversaciones", "en": "Conversations"},
    "lb_page_sub":         {"es": "Quién escribió en el período. Elige a una persona para leer sus resúmenes y mensajes.", "en": "Who wrote in the period. Pick someone to read their summaries and messages."},
    "lb_rank":             {"es": "#", "en": "#"},
    "lb_user":             {"es": "Persona", "en": "Person"},
    "lb_messages":         {"es": "Mensajes", "en": "Messages"},
    "lb_conversations":    {"es": "Conversaciones", "en": "Conversations"},
    "lb_days_active":      {"es": "Días activo", "en": "Days active"},
    "lb_avg_msg":          {"es": "Msg/conv", "en": "Msg/conv"},
    "lb_last_seen":        {"es": "Última vez", "en": "Last seen"},
    "lb_country":          {"es": "País", "en": "Country"},
    "lb_top_stats":        {"es": "Podio", "en": "Podium"},
    "lb_engagement":       {"es": "Personas del período", "en": "People in the period"},
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
    "lb_click_hint":       {"es": "Ordenadas por mensajes. También puedes marcar la casilla de una fila.", "en": "Sorted by messages. You can also tick a row's checkbox."},
    "lb_flags":            {"es": "Alertas", "en": "Alerts"},


    # ---- UX 2026-11-12 (revisión con Fable) ----
    # Inicio
    "status_no_alerts":    {"es": "Sin alertas en el período", "en": "No alerts in the period"},
    "status_all_reviewed": {"es": "Alertas revisadas", "en": "Alerts reviewed"},
    "status_pending":      {"es": "{n} alerta(s) sin revisar", "en": "{n} alert(s) not reviewed"},
    "last_message":        {"es": "Último mensaje recibido", "en": "Last message received"},
    "last_message_none":   {"es": "sin mensajes todavía", "en": "no messages yet"},
    "ago_today":           {"es": "hoy", "en": "today"},
    "ago_yesterday":       {"es": "ayer", "en": "yesterday"},
    "ago_days":            {"es": "hace {n} días", "en": "{n} days ago"},
    "data_delay":          {"es": "Los datos se refrescan cada 2 minutos", "en": "Data refreshes every 2 minutes"},
    "kpi_active":          {"es": "Personas activas", "en": "Active people"},
    "kpi_active_cap":      {"es": "Escribieron al menos una vez en el período", "en": "Wrote at least once in the period"},
    "kpi_returning_cap":   {"es": "Escribieron en dos o más semanas distintas", "en": "Wrote in two or more different weeks"},
    "kpi_answered_cap":    {"es": "{a} de {q} preguntas", "en": "{a} of {q} questions"},
    "kpi_pending":         {"es": "Alertas sin revisar", "en": "Alerts not reviewed"},
    "kpi_pending_cap":     {"es": "Rojas y naranjas del período: {n} en total", "en": "Red and orange in the period: {n} total"},
    "vs_prev_abs":         {"es": "vs. {prev} en el período anterior", "en": "vs. {prev} in the previous period"},
    "daily_sub":           {"es": "Mensajes por día (de las personas y de Aly)", "en": "Messages per day (people and Aly)"},
    "volume_title":        {"es": "Volumen del período", "en": "Volume in the period"},
    "vol_conversations":   {"es": "Conversaciones", "en": "Conversations"},
    "vol_messages":        {"es": "Mensajes (personas + Aly)", "en": "Messages (people + Aly)"},
    "vol_msg_per_conv":    {"es": "Mensajes por conversación", "en": "Messages per conversation"},
    "registration_title":  {"es": "Registro", "en": "Registration"},
    "registration_note":   {"es": "Registrados: quienes completaron el registro inicial (en México, aceptar el aviso de privacidad).",
                            "en": "Registered: people who completed the initial sign-up (in Mexico, accepting the privacy notice)."},
    "kpi_notes":           {"es": "<b>Volvieron:</b> personas activas del período que escribieron en dos o más semanas distintas. <b>Respondidas:</b> preguntas cuya respuesta no fue «No tengo esa información»; no cuentan saludos, agradecimientos ni despedidas.",
                            "en": "<b>Returned:</b> active people who wrote in two or more different weeks. <b>Answered:</b> questions whose answer was not “I don't have that information”; greetings, thanks and goodbyes don't count."},
    "usage_hours":         {"es": "Horario de uso", "en": "When people write"},
    "usage_hours_note":    {"es": "Hora pico: <b>{h}</b> · Día más activo: <b>{d}</b>", "en": "Peak hour: <b>{h}</b> · Busiest day: <b>{d}</b>"},
    "week_label":          {"es": "Sem. {d}", "en": "Wk {d}"},
    # Usuarios
    "kpi_depts":           {"es": "Departamentos con usuarios", "en": "Departments with users"},
    "kpi_depts_cap":       {"es": "De los 33 de Colombia", "en": "Out of Colombia's 33"},
    "kpi_regions_cap":     {"es": "Regiones distintas en el período", "en": "Distinct regions in the period"},
    "kpi_new_reg":         {"es": "Nuevos registros", "en": "New sign-ups"},
    "kpi_new_reg_cap":     {"es": "{total} registrados en total", "en": "{total} registered to date"},
    "hover_users_one":     {"es": "usuario(s)", "en": "user(s)"},
    # Alertas
    "red_pending":         {"es": "Rojas sin revisar", "en": "Red, not reviewed"},
    "orange_pending":      {"es": "Naranjas sin revisar", "en": "Orange, not reviewed"},
    "reviewed_in_period":  {"es": "Revisadas", "en": "Reviewed"},
    "reviewed_cap":        {"es": "De {n} alertas en el período", "en": "Of {n} alerts in the period"},
    "alerts_list_title":   {"es": "Alertas del período", "en": "Alerts in the period"},
    "alerts_list_sub":     {"es": "{n} conversación(es). Abre una para leer el resumen y marcarla como revisada.",
                            "en": "{n} conversation(s). Open one to read the summary and mark it as reviewed."},
    "no_alerts_range":     {"es": "Sin alertas rojas ni naranjas entre el {d1} y el {d2}.",
                            "en": "No red or orange alerts between {d1} and {d2}."},
    "last_alert":          {"es": "La última fue el {d} ({sev}, {state}).", "en": "The last one was on {d} ({sev}, {state})."},
    "last_alert_none":     {"es": "Este programa no ha tenido alertas rojas ni naranjas.", "en": "This program hasn't had red or orange alerts."},
    "sev_red":             {"es": "roja", "en": "red"},
    "sev_orange":          {"es": "naranja", "en": "orange"},
    "state_reviewed":      {"es": "revisada", "en": "reviewed"},
    "state_pending":       {"es": "sin revisar", "en": "not reviewed"},
    "reviewed_on":         {"es": "revisada el {d}", "en": "reviewed on {d}"},
    "flag_label":          {"es": "Alerta", "en": "Alert"},
    "summary_label":       {"es": "Resumen", "en": "Summary"},
    # Conversaciones (antes Leaderboard)
    "lb_pick":             {"es": "Ver las conversaciones de", "en": "See the conversations of"},
    "lb_pick_none":        {"es": "Elige a una persona…", "en": "Choose someone…"},
    "lb_messages_help":    {"es": "Mensajes de la persona y de Aly en el período", "en": "Messages from the person and from Aly in the period"},
    "lb_conv_days":        {"es": "{c} conversación(es) · {d} día(s) activo(s)", "en": "{c} conversation(s) · {d} active day(s)"},
    # Marca
    "brand_tagline":       {"es": "Panel de seguimiento", "en": "Monitoring panel"},
    "brand_tagline_long":  {"es": "Panel de seguimiento del asistente de WhatsApp", "en": "WhatsApp assistant monitoring panel"},
    # Sidebar
    "bot_label":           {"es": "Programa", "en": "Program"},
    "bot_help":            {"es": "Qué programa ver en el dashboard", "en": "Which program to show"},

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

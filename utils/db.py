import os
import psycopg2
import psycopg2.extras
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Todos los timestamps almacenados son timestamptz en UTC. La UI opera en GMT-5
# (Colombia/México), así que convertimos en cada query antes de extraer hora,
# día o filtrar por rango.
TZ = "America/Bogota"

# Cuentas de testing/eval que escriben a las mismas tablas que el bot real
# (vienen del repo hermano aly-evals: benchmarks, smoke tests, verify, debug).
# Se filtran SIEMPRE en queries del dashboard para no contaminar KPIs.
_TEST_CLIENT_NUMBERS = (
    "eval", "verify", "smoke", "smoke-test", "smoke-factual",
    "debug-rank", "debug-ingest", "debug-format", "debug-format-fix",
    "debug-fmt", "debug-disclaimer-v2",
    "normal-clean", "clean-only", "cleanmanual-test",
    "+5215512345678",
)
_TEST_CLIENT_LIKE = ("debug-%", "test-%", "smoke%")
_TEST_CONV_LIKE = (
    "eval-%", "verify-%", "trace-%", "debug-%",
    "ingest-%", "rank-%", "smoke-%", "fmt-fix-%",
    "discl-v2-%", "normal-clean-%", "clean-only-%",
    "dump16-%", "cleanmanual-%", "%-test-%",
)


def get_connection():
    return psycopg2.connect(DATABASE_URL)


# Caché de lecturas. Sin esto, cada clic (cambiar de página, de bot o de
# fecha) repetía ~15 queries contra Supabase y la página tardaba en aparecer.
# Dos minutos alcanzan: el bot escribe cada pocos minutos y nadie mira el panel
# en tiempo real. La clave es (query, params), así que el filtro de bot y de
# fechas va dentro y un rol nunca ve datos cacheados de otro. Cada escritura
# (execute) vacía la caché, para que marcar una alerta como revisada se vea
# en el rerun siguiente.
_CACHE_TTL_S = 120


@st.cache_data(ttl=_CACHE_TTL_S, show_spinner=False)
def _fetch_cached(query: str, params: tuple) -> pd.DataFrame:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, list(params))
            rows = cur.fetchall()
            return pd.DataFrame(rows)


def fetch_df(query: str, params=None) -> pd.DataFrame:
    return _fetch_cached(query, tuple(params or ()))


def execute(query: str, params=None) -> int:
    """Run a write query (INSERT/UPDATE/DELETE) and return affected rowcount."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or [])
            n = cur.rowcount
    _fetch_cached.clear()
    return n


# ---------------------------------------------------------------------------
# Bot ID discovery
# ---------------------------------------------------------------------------

def get_available_bot_ids() -> list[str]:
    """Return list of distinct bot_id values present in users_interactions, excluding test accounts."""
    # Build exclusion clauses for test accounts
    placeholders = ",".join(["%s"] * len(_TEST_CLIENT_NUMBERS))
    not_in_clause = f"client_number NOT IN ({placeholders})"
    not_like_clauses = " AND ".join([f"client_number NOT LIKE %s" for _ in _TEST_CLIENT_LIKE])
    conv_not_like_clauses = " AND ".join([f"conversation_id NOT LIKE %s" for _ in _TEST_CONV_LIKE])

    params = list(_TEST_CLIENT_NUMBERS) + list(_TEST_CLIENT_LIKE) + list(_TEST_CONV_LIKE)

    query = f"""
        SELECT DISTINCT bot_id
        FROM public.users_interactions
        WHERE bot_id IS NOT NULL
          AND bot_id != ''
          AND {not_in_clause}
          AND {not_like_clauses}
          AND {conv_not_like_clauses}
        ORDER BY bot_id
    """
    try:
        df = fetch_df(query, params)
        return df["bot_id"].tolist() if not df.empty else ["apapachar"]
    except Exception:
        return ["apapachar"]  # fallback


# ---------------------------------------------------------------------------
# KPI queries
# ---------------------------------------------------------------------------

def get_user_kpis(date_from=None, date_to=None, bot_id=None) -> dict:
    """Return unique users and sessions within optional date range."""
    where, params = _date_filter("created_at", date_from, date_to, bot_id=bot_id)
    query = f"""
        SELECT
            COUNT(DISTINCT client_number) AS n_users,
            COUNT(DISTINCT conversation_id) AS n_sessions
        FROM public.users_interactions
        {where}
    """
    df = fetch_df(query, params)
    row = df.iloc[0]
    return {"n_users": int(row["n_users"]), "n_sessions": int(row["n_sessions"])}


def get_registered_users(date_from=None, date_to=None, bot_id=None) -> dict:
    """Personas registradas en `users_data`: acumulado al cierre del rango y nuevas dentro de él.

    El bot solo inserta la fila cuando la persona termina el registro inicial; en
    México eso es aceptar el aviso de privacidad (Aly, `registrarUsuario`). Se
    cuenta por número y con su primera fila, porque `users_data` no tiene UNIQUE
    y ya tiene duplicados.
    """
    where, params = _date_filter(
        "created_at", None, date_to,
        client_col="number", conv_col=None, bot_id=bot_id,
    )
    nuevos_expr = "COUNT(*)"
    if date_from:
        nuevos_expr = f"COUNT(*) FILTER (WHERE (first_at AT TIME ZONE '{TZ}')::date >= %s)"
        params = [str(date_from)] + params
    query = f"""
        SELECT COUNT(*) AS total, {nuevos_expr} AS nuevos
        FROM (
            SELECT number, MIN(created_at) AS first_at
            FROM public.users_data
            {where}
            GROUP BY number
        ) reg
    """
    row = fetch_df(query, params).iloc[0]
    return {"total": int(row["total"]), "nuevos": int(row["nuevos"])}


def get_returning_users(date_from=None, date_to=None, bot_id=None) -> dict:
    """Usuarios activos en el rango y cuántos escribieron en dos o más semanas distintas.

    Activo = mandó al menos un mensaje (`role = 'user'`). Las semanas van de lunes
    a domingo en hora local.
    """
    where, params = _date_filter(
        "created_at", date_from, date_to, extra="role = 'user'", bot_id=bot_id,
    )
    query = f"""
        SELECT COUNT(*) AS activos,
               COUNT(*) FILTER (WHERE semanas >= 2) AS vuelven
        FROM (
            SELECT client_number,
                   COUNT(DISTINCT date_trunc('week', created_at AT TIME ZONE '{TZ}')) AS semanas
            FROM public.users_interactions
            {where}
            GROUP BY client_number
        ) por_usuario
    """
    row = fetch_df(query, params).iloc[0]
    return {"activos": int(row["activos"]), "vuelven": int(row["vuelven"])}


# Mensajes sociales que no cuentan como pregunta: saludos, agradecimientos,
# despedidas y la respuesta al aviso de privacidad. Se comparan en minúsculas,
# sin tildes ni signos de puntuación, y pueden venir combinados ("hola gracias").
_SOCIAL_MSG_RE = (
    r"^((hola|hi|hello|oi|ola|buen[oa]s?( (dias?|tardes|noches))?|gracias|muchas gracias"
    r"|mil gracias|thanks|thank you|ok|okay|vale|listo|perfecto|super|genial|excelente"
    r"|chao|adios|hasta luego|bye|aly|acepto|no acepto|[12])\s*)+$"
)
# Respuesta de Aly cuando el material no cubre la pregunta. Los tres bots abren
# con la misma frase (FACTUAL en src/Constants/*AgentPrompts.ts del repo Aly);
# también cubre las dos variantes viejas de apapachar ("No tengo información
# sobre eso", "No tengo esa información en el contexto...").
_NO_INFO_RE = r"^\s*(no tengo (esa )?informaci[oó]n|i don['’]t have that)"


# Cada mensaje con el que le sigue en su conversación (`next_role`, `next_message`)
# y si es puramente social. La ventana corre sobre toda la tabla antes de que se
# aplique el WHERE de fechas, para no perder la respuesta de una pregunta que cae
# en el borde del rango. Lleva un parámetro: `_SOCIAL_MSG_RE`.
_MSGS_WITH_REPLY_CTE = """
    WITH msgs AS (
        SELECT conversation_id, client_number, role, message, created_at, bot_id,
               LEAD(role)    OVER w AS next_role,
               LEAD(message) OVER w AS next_message,
               lower(translate(regexp_replace(trim(message), '[¡!¿?.,;:]+', '', 'g'),
                               'áéíóúÁÉÍÓÚ', 'aeiouaeiou')) ~ %s AS social
        FROM public.users_interactions
        WINDOW w AS (PARTITION BY bot_id, client_number, conversation_id
                     ORDER BY created_at, CASE role WHEN 'user' THEN 0 ELSE 1 END)
    )
"""


def get_answer_coverage(date_from=None, date_to=None, bot_id=None) -> dict:
    """Preguntas del período y cuántas recibieron "No tengo esa información".

    Pregunta = mensaje de la usuaria (`role='user'`) que no es puramente social
    (ver `_SOCIAL_MSG_RE`). Cada pregunta se empareja con el mensaje siguiente
    de la misma conversación; la ventana corre sobre toda la tabla antes de
    filtrar, para no perder la respuesta de una pregunta en el borde del rango.
    """
    where, params = _date_filter(
        "created_at", date_from, date_to, extra="role = 'user' AND NOT social", bot_id=bot_id,
    )
    query = f"""
        {_MSGS_WITH_REPLY_CTE}
        SELECT COUNT(*) AS preguntas,
               COUNT(*) FILTER (WHERE next_role = 'ia' AND next_message ~* %s) AS sin_info
        FROM msgs
        {where}
    """
    row = fetch_df(query, [_SOCIAL_MSG_RE, _NO_INFO_RE] + params).iloc[0]
    return {"preguntas": int(row["preguntas"]), "sin_info": int(row["sin_info"])}


def get_weekly_active_users(date_from=None, date_to=None, bot_id=None) -> pd.DataFrame:
    """Usuarios distintos que mandaron al menos un mensaje cada semana (lunes a domingo, hora local)."""
    where, params = _date_filter(
        "created_at", date_from, date_to, extra="role = 'user'", bot_id=bot_id,
    )
    query = f"""
        SELECT date_trunc('week', created_at AT TIME ZONE '{TZ}')::date AS week,
               COUNT(DISTINCT client_number) AS users
        FROM public.users_interactions
        {where}
        GROUP BY 1
        ORDER BY 1
    """
    return fetch_df(query, params)


def get_messages_count(date_from=None, date_to=None, bot_id=None) -> int:
    where, params = _date_filter("created_at", date_from, date_to, bot_id=bot_id)
    query = f"""
        SELECT COUNT(*) AS n FROM public.users_interactions {where}
    """
    df = fetch_df(query, params)
    return int(df.iloc[0]["n"])


# ---------------------------------------------------------------------------
# Time-of-day histogram
# ---------------------------------------------------------------------------

def get_hourly_distribution(date_from=None, date_to=None, bot_id=None) -> pd.DataFrame:
    """Return message count per hour of day (0-23)."""
    where, params = _date_filter("created_at", date_from, date_to, bot_id=bot_id)
    query = f"""
        SELECT
            EXTRACT(HOUR FROM created_at AT TIME ZONE '{TZ}') AS hour,
            COUNT(*) AS messages
        FROM public.users_interactions
        {where}
        GROUP BY 1
        ORDER BY 1
    """
    return fetch_df(query, params)


# ---------------------------------------------------------------------------
# User demographics (from users_data)
# ---------------------------------------------------------------------------

def get_users_by_country(date_from=None, date_to=None, bot_id=None) -> pd.DataFrame:
    where_i, params_i = _date_filter(
        "ui.created_at", date_from, date_to,
        extra="ud.country IS NOT NULL",
        client_col="ui.client_number", conv_col="ui.conversation_id", bot_col="ui.bot_id", bot_id=bot_id,
    )
    query = f"""
        SELECT ud.country, COUNT(DISTINCT ud.number) AS n_users
        FROM public.users_data ud
        JOIN public.users_interactions ui
            ON ui.client_number = ud.number
            AND ui.bot_id = ud.bot_id
        {where_i}
        GROUP BY 1
        ORDER BY 2 DESC
    """
    try:
        return fetch_df(query, params_i)
    except Exception:
        return pd.DataFrame(columns=["country", "n_users"])


def get_users_by_gender(date_from=None, date_to=None, bot_id=None) -> pd.DataFrame:
    """Return user counts grouped by gender.

    Caveat (apapachar, fixed 2026-07-29): a bug in the bot's onboarding meant
    anyone who answered "Otro" was saved with an empty/corrupt `gender`
    instead. Rows from before that date undercount "Otro" — an empty/odd
    value there is likely this bug, not a refusal to answer, and can't be
    recovered retroactively. Not currently wired into any page; surface this
    caveat if a gender breakdown chart gets built on top of this query.
    """
    where_i, params_i = _date_filter(
        "ui.created_at", date_from, date_to,
        extra="ud.gender IS NOT NULL",
        client_col="ui.client_number", conv_col="ui.conversation_id", bot_col="ui.bot_id", bot_id=bot_id,
    )
    query = f"""
        SELECT ud.gender, COUNT(DISTINCT ud.number) AS n_users
        FROM public.users_data ud
        JOIN public.users_interactions ui
            ON ui.client_number = ud.number
            AND ui.bot_id = ud.bot_id
        {where_i}
        GROUP BY 1
        ORDER BY 2 DESC
    """
    try:
        return fetch_df(query, params_i)
    except Exception:
        return pd.DataFrame(columns=["gender", "n_users"])


def get_users_by_region(date_from=None, date_to=None, bot_id=None) -> pd.DataFrame:
    where_i, params_i = _date_filter(
        "ui.created_at", date_from, date_to,
        extra="ud.region IS NOT NULL",
        client_col="ui.client_number", conv_col="ui.conversation_id", bot_col="ui.bot_id", bot_id=bot_id,
    )
    query = f"""
        SELECT ud.region, COUNT(DISTINCT ud.number) AS n_users
        FROM public.users_data ud
        JOIN public.users_interactions ui
            ON ui.client_number = ud.number
            AND ui.bot_id = ud.bot_id
        {where_i}
        GROUP BY 1
        ORDER BY 2 DESC
    """
    try:
        return fetch_df(query, params_i)
    except Exception:
        return pd.DataFrame(columns=["region", "n_users"])


# ---------------------------------------------------------------------------
# Export — full filtered dataset
# ---------------------------------------------------------------------------

def get_pseudonymous_export_data(date_from=None, date_to=None, bot_id=None) -> dict:
    """Datos crudos para la exportación sin identificar (``utils/export.py``).

    Devuelve tres DataFrames que TODAVÍA traen número y ``conversation_id``:
    el seudónimo se pone en ``utils/export.py``, que es lo único que debe
    llamar esta función. Sin texto de mensajes, nombres ni resúmenes.

    - ``messages``: un mensaje de la usuaria (``role='user'``) por fila, con si
      es social y cómo respondió Aly (mismas reglas que ``get_answer_coverage``).
    - ``conversations``: una fila por conversación cerrada (``id`` único), con
      ``flag_severity`` (el enum limpio que también usan los correos de alertas)
      y las etiquetas de riesgo de ``flags``. ``conversation_date`` es naive en
      UTC: se ancla a UTC antes de pasarla a hora local.
    - ``registrations``: primera fila de ``users_data`` por número hasta el
      cierre del rango (acumulado, como ``get_registered_users``).
    """
    where_m, params_m = _date_filter(
        "created_at", date_from, date_to, extra="role = 'user'", bot_id=bot_id,
    )
    messages = fetch_df(f"""
        {_MSGS_WITH_REPLY_CTE}
        SELECT client_number, conversation_id,
               (created_at AT TIME ZONE '{TZ}') AS local_ts,
               social,
               (next_role = 'ia') AS has_reply,
               (next_role = 'ia' AND next_message ~* %s) AS no_info
        FROM msgs
        {where_m}
        ORDER BY created_at
    """, [_SOCIAL_MSG_RE, _NO_INFO_RE] + params_m)

    conv_utc = "(conversation_date AT TIME ZONE 'UTC')"
    where_c, params_c = _date_filter(
        conv_utc, date_from, date_to, client_col="user_number", bot_id=bot_id,
    )
    conversations = fetch_df(f"""
        SELECT user_number AS client_number, conversation_id,
               ({conv_utc} AT TIME ZONE '{TZ}') AS local_ts,
               messages_count, flag_severity, flags
        FROM public.conversations_data
        {where_c}
        ORDER BY conversation_date, id
    """, params_c)

    where_r, params_r = _date_filter(
        "created_at", None, date_to, client_col="number", conv_col=None, bot_id=bot_id,
    )
    registrations = fetch_df(f"""
        SELECT number AS client_number, (MIN(created_at) AT TIME ZONE '{TZ}') AS local_ts
        FROM public.users_data
        {where_r}
        GROUP BY number
        ORDER BY 2
    """, params_r)

    return {"messages": messages, "conversations": conversations, "registrations": registrations}


def get_interactions_export(date_from=None, date_to=None, bot_id=None) -> pd.DataFrame:
    where, params = _date_filter("created_at", date_from, date_to, bot_id=bot_id)
    query = f"""
        SELECT
            conversation_id, client_number, role, message,
            timestamp, status, created_at
        FROM public.users_interactions
        {where}
        ORDER BY created_at
    """
    return fetch_df(query, params)


# ---------------------------------------------------------------------------
# Analytics — new queries for redesigned dashboard
# ---------------------------------------------------------------------------

def get_daily_activity(date_from=None, date_to=None, bot_id=None) -> pd.DataFrame:
    """Return message, unique-user and session counts per calendar day."""
    where, params = _date_filter("created_at", date_from, date_to, bot_id=bot_id)
    query = f"""
        SELECT
            (created_at AT TIME ZONE '{TZ}')::date AS day,
            COUNT(*) AS messages,
            COUNT(DISTINCT client_number) AS users,
            COUNT(DISTINCT conversation_id) AS sessions
        FROM public.users_interactions
        {where}
        GROUP BY 1
        ORDER BY 1
    """
    return fetch_df(query, params)


def get_activity_heatmap(date_from=None, date_to=None, bot_id=None) -> pd.DataFrame:
    """Return message counts indexed by day-of-week (0=Sun) and hour (0-23)."""
    where, params = _date_filter("created_at", date_from, date_to, bot_id=bot_id)
    query = f"""
        SELECT
            EXTRACT(DOW  FROM created_at AT TIME ZONE '{TZ}')::int AS dow,
            EXTRACT(HOUR FROM created_at AT TIME ZONE '{TZ}')::int AS hour,
            COUNT(*) AS messages
        FROM public.users_interactions
        {where}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """
    return fetch_df(query, params)


def get_conversation_metrics(date_from=None, date_to=None, bot_id=None) -> dict:
    """Return average messages per conversation and per-user averages."""
    where, params = _date_filter("created_at", date_from, date_to, bot_id=bot_id)
    query = f"""
        SELECT
            COUNT(*)                                    AS total_messages,
            COUNT(DISTINCT conversation_id)             AS total_conversations,
            COUNT(DISTINCT client_number)               AS total_users,
            ROUND(
                COUNT(*)::numeric /
                NULLIF(COUNT(DISTINCT conversation_id), 0), 1
            )                                           AS avg_msg_per_conv,
            ROUND(
                COUNT(*)::numeric /
                NULLIF(COUNT(DISTINCT client_number), 0), 1
            )                                           AS avg_msg_per_user
        FROM public.users_interactions
        {where}
    """
    df = fetch_df(query, params)
    row = df.iloc[0]
    return {
        "total_messages":      int(row["total_messages"] or 0),
        "total_conversations": int(row["total_conversations"] or 0),
        "total_users":         int(row["total_users"] or 0),
        "avg_msg_per_conv":    float(row["avg_msg_per_conv"] or 0),
        "avg_msg_per_user":    float(row["avg_msg_per_user"] or 0),
    }


def get_kpi_deltas(date_from: str, date_to: str, bot_id=None) -> dict:
    """Compare current period KPIs against the equivalent previous period.

    Returns a dict with keys: users_delta, sessions_delta, messages_delta
    where each value is a float fraction (e.g. 0.12 = +12%).
    """
    import datetime

    try:
        d_from = datetime.date.fromisoformat(date_from)
        d_to   = datetime.date.fromisoformat(date_to)
        span   = d_to - d_from
        prev_from = str(d_from - span)
        prev_to   = str(d_from)
    except Exception:
        return {"users_delta": None, "sessions_delta": None, "messages_delta": None}

    current = get_user_kpis(date_from, date_to, bot_id=bot_id)
    prev    = get_user_kpis(prev_from, prev_to, bot_id=bot_id)
    curr_msg = get_messages_count(date_from, date_to, bot_id=bot_id)
    prev_msg = get_messages_count(prev_from, prev_to, bot_id=bot_id)

    def _delta(curr, prev):
        if prev == 0:
            return None
        return round((curr - prev) / prev, 4)

    return {
        "users_delta":    _delta(current["n_users"],    prev["n_users"]),
        "sessions_delta": _delta(current["n_sessions"], prev["n_sessions"]),
        "messages_delta": _delta(curr_msg,              prev_msg),
        # Los valores del período anterior, para mostrar la diferencia en
        # absoluto («−7 · antes 13»): con pocas personas un % asusta de más.
        "users_prev":     prev["n_users"],
        "sessions_prev":  prev["n_sessions"],
        "messages_prev":  prev_msg,
    }


def get_last_activity(bot_id=None):
    """Fecha y hora (GMT-5) del último mensaje del bot, sin importar el filtro.

    Responde «¿el bot está vivo?» sin abrir nada: si el último mensaje es de
    hace una semana, algo pasa (o nadie está escribiendo). Respeta el filtro de
    cuentas de prueba. Devuelve un ``pd.Timestamp`` o None.
    """
    where, params = _date_filter("created_at", None, None, bot_id=bot_id)
    df = fetch_df(
        f"SELECT MAX(created_at AT TIME ZONE '{TZ}') AS last FROM public.users_interactions {where}",
        params,
    )
    if df.empty or pd.isna(df.iloc[0]["last"]):
        return None
    return pd.Timestamp(df.iloc[0]["last"])


def get_last_flag(bot_id=None) -> dict:
    """La última conversación con alerta roja o naranja, sin importar el filtro.

    Para que Alertas en cero diga algo útil («la última fue el 3 de octubre y
    ya está revisada») en vez de solo «0». Clasifica con ``flag_severity`` y,
    si viene vacío, con el prefijo de ``flags`` (mismo criterio que la página).
    """
    where, params = _date_filter(
        "conversation_date", None, None,
        extra=("(flag_severity IN ('HIGH', 'MEDIUM') "
               "OR flags ILIKE 'HIGH-%%' OR flags ILIKE 'MEDIUM-%%')"),
        client_col="user_number", bot_col="bot_id", bot_id=bot_id,
    )
    df = fetch_df(
        f"""
        SELECT (conversation_date AT TIME ZONE 'UTC') AT TIME ZONE '{TZ}' AS conversation_date,
               flag_severity, flags,
               reviewed_at AT TIME ZONE '{TZ}' AS reviewed_at
        FROM public.conversations_data
        {where}
        ORDER BY conversation_date DESC
        LIMIT 1
        """,
        params,
    )
    if df.empty:
        return {}
    return df.iloc[0].to_dict()


# ---------------------------------------------------------------------------
# Schema introspection (run once to discover available tables)
# ---------------------------------------------------------------------------

def get_schema_info() -> pd.DataFrame:
    """Return all columns across all non-system schemas in Supabase."""
    query = """
        SELECT
            table_schema,
            table_name,
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name, ordinal_position
    """
    try:
        return fetch_df(query)
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})


# ---------------------------------------------------------------------------
# conversations_data — summaries, keywords, flags
# ---------------------------------------------------------------------------

# Contenido bilingüe (ES/EN). El bot (repo Aly_Apapachar) escribe
# summary_i18n / keywords_i18n (jsonb {"es": ..., "en": ...}) además del
# summary/keywords original. El dashboard lee la versión del idioma activo con
# fallback al original. Mientras la migración del bot no haya corrido, las
# columnas no existen y se cae automáticamente al texto original.
_HAS_I18N = None  # cache por proceso: None=sin chequear, True/False una vez resuelto


def _conversations_has_i18n() -> bool:
    """True si conversations_data tiene las columnas bilingües (migración aplicada).

    Se resuelve una sola vez por proceso. Si el bot corre la migración con la app
    ya levantada, hace falta un Reboot de la app para re-detectar (ver CLAUDE.md,
    gotcha de Deployment).
    """
    global _HAS_I18N
    if _HAS_I18N is None:
        try:
            df = fetch_df(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'conversations_data'
                  AND column_name = 'summary_i18n'
                LIMIT 1
                """
            )
            _HAS_I18N = not df.empty
        except Exception:
            _HAS_I18N = False
    return _HAS_I18N


def _i18n_expr(column: str, lang: str, prefix: str = "") -> str:
    """Expresión SQL para leer `column` en `lang` con fallback al original.

    `lang` se restringe a 'es'/'en' (whitelist) — seguro para interpolar.
    `prefix` es el alias de tabla calificado cuando aplica, p. ej. 'cd.'.
    """
    lang = "en" if str(lang).lower() == "en" else "es"
    col = f"{prefix}{column}"
    if _conversations_has_i18n():
        return f"COALESCE(NULLIF({prefix}{column}_i18n->>'{lang}', ''), {col})"
    return col


def get_conversations_data(date_from=None, date_to=None, bot_id=None, lang="es") -> pd.DataFrame:
    """Return all processed conversations with summary, keywords, flags.

    `lang` ('es'/'en') selecciona la versión bilingüe del summary/keywords si
    existe (fallback al original).
    """
    where, params = _date_filter(
        "conversation_date", date_from, date_to,
        client_col="user_number", bot_col="bot_id", bot_id=bot_id,
    )
    query = f"""
        SELECT
            conversation_id,
            user_number,
            conversation_date,
            {_i18n_expr("summary", lang)}  AS summary,
            {_i18n_expr("keywords", lang)} AS keywords,
            flags,
            session
        FROM public.conversations_data
        {where}
        ORDER BY conversation_date DESC
    """
    try:
        return fetch_df(query, params)
    except Exception:
        return pd.DataFrame()


def get_summaries(date_from=None, date_to=None, limit: int = 20, bot_id=None, lang="es") -> pd.DataFrame:
    """Return recent conversation summaries (en `lang` si hay versión bilingüe)."""
    where, params = _date_filter(
        "conversation_date", date_from, date_to,
        extra="summary IS NOT NULL AND summary != ''",
        client_col="user_number", bot_col="bot_id", bot_id=bot_id,
    )
    query = f"""
        SELECT conversation_id, user_number, conversation_date,
               {_i18n_expr("summary", lang)} AS summary
        FROM public.conversations_data
        {where}
        ORDER BY conversation_date DESC
        LIMIT {limit}
    """
    try:
        return fetch_df(query, params)
    except Exception:
        return pd.DataFrame()


def get_flags_data(date_from=None, date_to=None, bot_id=None) -> pd.DataFrame:
    """Return conversations that have a flag value.

    Incluye ``id`` (PK real de la tabla) porque **``conversation_id`` NO es
    único**: el bot reusa el mismo id para conversaciones distintas del mismo
    usuario en días distintos (visto en apapachar y demo). Usar ``id`` — no
    ``conversation_id`` — como identidad de fila en la UI y en los updates de
    ``reviewed_at``.
    """
    where, params = _date_filter(
        "conversation_date", date_from, date_to,
        extra="flags IS NOT NULL AND flags != ''",
        client_col="user_number", bot_col="bot_id", bot_id=bot_id,
    )
    query = f"""
        SELECT id, conversation_id, user_number, conversation_date, flags, summary,
               reviewed_at AT TIME ZONE '{TZ}' AS reviewed_at
        FROM public.conversations_data
        {where}
        ORDER BY conversation_date DESC
    """
    try:
        return fetch_df(query, params)
    except Exception:
        return pd.DataFrame()


def mark_flag_reviewed(row_id) -> int:
    """Stamp reviewed_at = NOW() on ONE conversation row (by PK ``id``).

    Va por ``id`` y no por ``conversation_id`` a propósito: ese campo se repite
    entre conversaciones distintas, y un UPDATE por ``conversation_id`` marcaba
    como revisadas todas las filas que lo compartían — incluida una alerta real
    que nadie había mirado. Devuelve el rowcount (debe ser 1).
    """
    return execute(
        "UPDATE public.conversations_data "
        "SET reviewed_at = NOW() "
        "WHERE id = %s",
        [int(row_id)],
    )


def unmark_flag_reviewed(row_id) -> int:
    """Clear reviewed_at on ONE conversation row (by PK ``id``).

    Mismo motivo que ``mark_flag_reviewed``: la identidad de fila es ``id``.
    """
    return execute(
        "UPDATE public.conversations_data "
        "SET reviewed_at = NULL "
        "WHERE id = %s",
        [int(row_id)],
    )


# ---------------------------------------------------------------------------
# Leaderboard — top users by engagement
# ---------------------------------------------------------------------------

def get_leaderboard(date_from=None, date_to=None, limit: int = 20, bot_id=None) -> pd.DataFrame:
    """Return top users ranked by total messages sent, with engagement metrics.

    Joins users_data by BOTH number AND bot_id so each user's profile is
    specific to the bot they're interacting with.
    """
    where, params = _date_filter(
        "ui.created_at", date_from, date_to,
        client_col="ui.client_number", conv_col="ui.conversation_id", bot_col="ui.bot_id", bot_id=bot_id,
    )
    query = f"""
        SELECT
            ui.client_number,
            ud.name,
            ud.country,
            COUNT(*)                                        AS total_messages,
            COUNT(DISTINCT ui.conversation_id)              AS total_conversations,
            COUNT(DISTINCT (ui.created_at AT TIME ZONE '{TZ}')::date) AS days_active,
            ROUND(
                COUNT(*)::numeric /
                NULLIF(COUNT(DISTINCT ui.conversation_id), 0), 1
            )                                               AS avg_msg_per_conv,
            MAX(ui.created_at AT TIME ZONE '{TZ}')          AS last_seen
        FROM public.users_interactions ui
        LEFT JOIN public.users_data ud
            ON ud.number = ui.client_number
            AND ud.bot_id = ui.bot_id
        {where}
        GROUP BY ui.client_number, ud.name, ud.country
        ORDER BY total_messages DESC
        LIMIT {limit}
    """
    try:
        return fetch_df(query, params)
    except Exception:
        return pd.DataFrame()


def get_flag_counts_by_user(date_from=None, date_to=None, bot_id=None) -> pd.DataFrame:
    """Return count of red+orange flags per user for the given period."""
    where, params = _date_filter(
        "conversation_date", date_from, date_to,
        extra="flags IS NOT NULL AND flags != ''",
        client_col="user_number", bot_col="bot_id", bot_id=bot_id,
    )
    query = f"""
        SELECT user_number,
               COUNT(*) FILTER (
                   WHERE LOWER(flags) LIKE '%high%'
                      OR LOWER(flags) LIKE '%medium%'
                      OR LOWER(flags) LIKE '%red%'
                      OR LOWER(flags) LIKE '%rojo%'
                      OR LOWER(flags) LIKE '%critico%'
                      OR LOWER(flags) LIKE '%orange%'
                      OR LOWER(flags) LIKE '%naranja%'
                      OR LOWER(flags) LIKE '%warning%'
                      OR LOWER(flags) LIKE '%advertencia%'
               ) AS n_flags
        FROM public.conversations_data
        {where}
        GROUP BY user_number
    """
    try:
        return fetch_df(query, params)
    except Exception:
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# RAG knowledge base info
# ---------------------------------------------------------------------------

def get_rag_summary() -> pd.DataFrame:
    query = """
        SELECT project, document_name, COUNT(*) AS chunks
        FROM vector_aly.rag_embeddings
        GROUP BY 1, 2
        ORDER BY 3 DESC
    """
    try:
        return fetch_df(query)
    except Exception:
        return pd.DataFrame(columns=["project", "document_name", "chunks"])


# ---------------------------------------------------------------------------
# Per-user drill-down queries
# ---------------------------------------------------------------------------

def get_user_conversations(user_number, date_from=None, date_to=None, bot_id=None, lang="es") -> pd.DataFrame:
    """Return all conversations_data rows for a specific user.

    Joins through conversation_id from users_interactions to avoid any
    format mismatch between client_number and conversations_data.user_number.
    `lang` ('es'/'en') selecciona la versión bilingüe del summary/keywords.
    """
    date_where, date_params = _date_filter(
        "ui.created_at", date_from, date_to,
        client_col=None, conv_col=None, bot_col="ui.bot_id", bot_id=bot_id,
    )
    if date_where:
        full_where = "WHERE ui.client_number = %s AND " + date_where[len("WHERE "):]
    else:
        full_where = "WHERE ui.client_number = %s"
    params = [str(user_number)] + date_params
    query = f"""
        SELECT DISTINCT ON (cd.conversation_id)
               cd.conversation_id, cd.user_number, cd.conversation_date,
               {_i18n_expr("summary", lang, prefix="cd.")} AS summary,
               {_i18n_expr("keywords", lang, prefix="cd.")} AS keywords,
               cd.flags, cd.session
        FROM public.conversations_data cd
        JOIN public.users_interactions ui USING (conversation_id)
        {full_where}
        ORDER BY cd.conversation_id, cd.conversation_date DESC
    """
    try:
        df = fetch_df(query, params)
        if not df.empty:
            df = df.sort_values("conversation_date", ascending=False).reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame()


def get_user_messages(user_number, date_from=None, date_to=None, bot_id=None) -> pd.DataFrame:
    """Return all interaction messages for a specific user, ordered chronologically."""
    date_where, date_params = _date_filter(
        "created_at", date_from, date_to,
        client_col=None, conv_col=None, bot_col="bot_id", bot_id=bot_id,
    )
    if date_where:
        full_where = "WHERE client_number = %s AND " + date_where[len("WHERE "):]
    else:
        full_where = "WHERE client_number = %s"
    params = [str(user_number)] + date_params
    query = f"""
        SELECT conversation_id, client_number, role, message, timestamp, created_at
        FROM public.users_interactions
        {full_where}
        ORDER BY timestamp ASC
    """
    try:
        return fetch_df(query, params)
    except Exception:
        return pd.DataFrame()


def get_messages_by_conversation_ids(conv_ids: list) -> pd.DataFrame:
    """Return all messages for a list of conversation_ids, ordered chronologically."""
    if not conv_ids:
        return pd.DataFrame()
    query = """
        SELECT conversation_id, client_number, role, message, timestamp
        FROM public.users_interactions
        WHERE conversation_id = ANY(%s)
        ORDER BY conversation_id, timestamp ASC
    """
    try:
        return fetch_df(query, [list(conv_ids)])
    except Exception:
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _date_filter(
    col: str,
    date_from,
    date_to,
    extra: str = "",
    client_col="client_number",
    conv_col="conversation_id",
    bot_col="bot_id",
    bot_id=None,
):
    """Build a WHERE clause for date range + test exclusion + bot_id filter + optional extra.

    El rango de fechas se interpreta en la zona local (America/Bogota / GMT-5),
    para que un filtro "del 1 al 7 de mayo" incluya todos los mensajes vistos
    como ese rango por el equipo en Colombia/México, no en UTC.

    El filtro de tests/eval se aplica SIEMPRE por defecto (ver
    _TEST_CLIENT_NUMBERS / _TEST_CLIENT_LIKE / _TEST_CONV_LIKE arriba). Pasar
    `client_col=None` y/o `conv_col=None` para tablas donde esa columna no
    existe o se quiere apagar el filtro (drill-downs por usuario explícito).

    El filtro bot_id se aplica por defecto usando el valor pasado en `bot_id`
    (si no se pasa, se omite el filtro). Pasar `bot_col=None` para desactivarlo.
    """
    clauses = []
    params: list = []
    if extra:
        clauses.append(extra)
    if date_from:
        clauses.append(f"({col} AT TIME ZONE '{TZ}')::date >= %s")
        params.append(str(date_from))
    if date_to:
        clauses.append(f"({col} AT TIME ZONE '{TZ}')::date < %s")
        params.append(str(date_to))
    if client_col:
        placeholders = ",".join(["%s"] * len(_TEST_CLIENT_NUMBERS))
        clauses.append(f"{client_col} NOT IN ({placeholders})")
        params.extend(_TEST_CLIENT_NUMBERS)
        for pat in _TEST_CLIENT_LIKE:
            clauses.append(f"{client_col} NOT LIKE %s")
            params.append(pat)
    if conv_col:
        for pat in _TEST_CONV_LIKE:
            clauses.append(f"{conv_col} NOT LIKE %s")
            params.append(pat)
    if bot_col and bot_id is not None:
        clauses.append(f"{bot_col} = %s")
        params.append(bot_id)
    if clauses:
        return "WHERE " + " AND ".join(clauses), params
    return "", params

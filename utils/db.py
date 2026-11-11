import os
import psycopg2
import psycopg2.extras
import pandas as pd
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


def fetch_df(query: str, params=None) -> pd.DataFrame:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params or [])
            rows = cur.fetchall()
            return pd.DataFrame(rows)


def execute(query: str, params=None) -> int:
    """Run a write query (INSERT/UPDATE/DELETE) and return affected rowcount."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or [])
            return cur.rowcount


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
    }


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

# CLAUDE.md — Dashboard Aly

## Documentación (Obsidian)
Notas en: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Documentición codigo/Aly Bot (Equimundo)/`
Actualizar cuando cambien: arquitectura, stack, esquema Supabase, páginas/componentes, flujo de datos bot→dashboard.
No actualizar por: bugfixes menores, ajustes de UI, cambios de copy.

## Correr en local
```bash
python3 -m streamlit run app.py
```
`streamlit` no está en el PATH — siempre usar `python3 -m streamlit`. Corre sobre el **Python 3.9 del sistema** (streamlit/psycopg2 instalados globales, sin venv). El login requiere `.streamlit/secrets.toml` (gitignored — copiar de `.streamlit/secrets.toml.example`); sin él, la app muestra "Falta la configuración de autenticación".

---

## Proyecto
Dashboard operativo privado para **Apapáchar** (chatbot WhatsApp RAG, crianza 0-5 años, Fundación Apapacho). Marca visible: **Aly**.

**Multi-bot — alcance del dashboard:** la DB de Supabase es compartida. Las 3 tablas (`users_interactions`, `users_data`, `conversations_data`) tienen columna `bot_id` (type `text`, `NOT NULL`, default `''`). El bot escribe `'apapachar'`, `'demo'` o `'mexico'` (nuevo desde 2026-07-29) según `BOT_ID` env var.

El dashboard **detecta automáticamente** los `bot_id` disponibles en la DB (`utils/db.py:get_available_bot_ids()`) y muestra un **selector en el sidebar** (arriba de los filtros de fecha). El usuario elige qué bot ver; todas las queries filtran por el `bot_id` seleccionado. El valor seleccionado vive en `st.session_state["selected_bot"]` y se pasa via `get_filters()["bot_id"]`.

**Estado actual (2026-08-20)**: hay **autenticación con roles** (ver sección *Autenticación y roles*). El selector de bot se filtra por el rol del usuario logueado: `admin` ve todos los bots; `apapachar` y `mexico` quedan bloqueados a su propio bot (sin selector, chip fijo). El selector muestra **etiquetas legibles** (`utils/bots.py:bot_label`), no el `bot_id` crudo.

---

## Autenticación y roles
Login usuario/contraseña con **`streamlit-authenticator` (0.4.x)**. La puerta vive en `utils/auth.py:require_login()`, llamada en `app.py` **antes** de la nav y las páginas: si no hay sesión válida renderiza la pantalla de login (logo Aly + form) y hace `st.stop()`. La sesión persiste vía cookie firmada (no re-login en cada rerun).

**Credenciales y roles viven en `st.secrets`** (`.streamlit/secrets.toml` en local — **gitignored**; en producción, `/opt/aly-dashboard/.streamlit/secrets.toml` en plural-aly). Plantilla commiteada: `.streamlit/secrets.toml.example`. Estructura: `[cookie]`, `[credentials.usernames.<user>]` (con `password` = **hash bcrypt**, `roles = ["..."]`) y `[roles]` que mapea rol → lista de `bot_id` permitidos (`"*"` = todos).

**Generar un hash bcrypt** para una contraseña nueva:
```bash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'PASSWORD', bcrypt.gensalt()).decode())"
```

**Flujo rol → bots**: `require_login()` deja en session_state `auth_role`, `auth_allowed_bots` (None = todos, o lista de bot_ids), `auth_name`, `_authenticator`. `components/filters.py` lee `auth_allowed_bots` y: si es None muestra el selector con todos los bots; si es lista de 1 oculta el selector y fija el bot (chip `.bot-locked`); si la selección actual no es válida para el rol, la resetea. El logout (`authenticator.logout`) y el "Conectado como" se renderizan en el footer del sidebar.

**Roles actuales**: `admin` → `["*"]` (todos los bots); `apapachar` → `["apapachar"]` (solo Colombia); `mexico` → `["mexico"]` (solo Semillas de Igualdad, México — creado 2026-08-20).

**Agregar un usuario/rol nuevo**: añadir `[credentials.usernames.<user>]` (hash + `roles`) y, si es un rol nuevo, una entrada en `[roles]`. Si es un rol nuevo, agregar también la clave i18n `role_<rol>` en `utils/i18n.py`. Sin migración de DB.

**Ojo — el username no es el rol.** Son cosas separadas: el username es lo que se teclea en el login, el rol sale de la lista `roles` de esa cuenta y es el que decide qué bots ve. En producción los usernames siguen la convención `<programa>_user` (`apapachar_user`, `mexico_user`), con `superadmin` como excepción histórica del admin — no coinciden con el nombre del rol (`apapachar`, `mexico`, `admin`). La plantilla `.streamlit/secrets.toml.example` refleja los nombres reales.

---

## Onboarding por bot — shape de datos y caveats (bot_id)

El onboarding de Typebot es distinto por bot y determina qué llega a `users_data`. No asumir
que todos los bots piden los mismos campos ni usan la misma lista de regiones — es config
implícita por `bot_id`, no un esquema único. Estado al **2026-08-20** (las notas que dicen
"hoy" en `apapachar`/`demo` son del corte del 2026-07-29):

- **`apapachar`** (Colombia): el onboarding se rediseñó hoy para ser más corto y privacy-first.
  Ya no pregunta nombre ni correo — solo género y región. **Toda fila nueva desde hoy tiene
  `name: ""` y `email: ""`** (string vacío, no NULL); filas de antes sí tienen esos datos reales.
  Es un corte en el tiempo, no una migración retroactiva. `leaderboard.py` ya cae correctamente
  al número enmascarado cuando `name` es vacío (`display_name`), no requirió cambios.
- **`mexico`** — programa **"Semillas de Igualdad"** (Equimundo + GENDES, implementado por el
  Tec de Monterrey en el marco de la Nueva Escuela Mexicana). Usuaria: **docente de preescolar
  en servicio en el Estado de México**, no madre/padre — comparte pipeline con Apapáchar pero
  NADA de su contenido (ver `src/Constants/MexicoAgentPrompts.ts` en el repo del bot).
  Número `+1 262-405-0527`.
  **Al 2026-08-20 sigue sin tráfico real** (ver *Estado de los datos de `mexico`* abajo) y su
  onboarding sigue clonado del `demo`: no pide género ni región. El selector de bot
  (`get_available_bot_ids()`) ya lo detecta automáticamente — no requiere cambio de código.
- **`demo`**: sin onboarding de género/región (heredado, sin cambios hoy).

**Lista de regiones de `apapachar`** pasó de 10 (sin prefijo, ej. `"Tolima"`) a **17, todas con
el prefijo literal `"Regional "`** (ej. `"Regional Tolima"`), agregando Arauca, Atlántico,
Bolívar, Caldas, Nariño, Quindío y Risaralda. `components/charts.py:_normalize_region()` quita
ese prefijo (además de tildes/mayúsculas) antes de matchear contra el GeoJSON, así que filas
viejas (`"Tolima"`) y nuevas (`"Regional Tolima"`) agrupan igual en el mapa/ranking de
`usuarios.py` — no hace falta migrar datos históricos. Los 33 departamentos del GeoJSON ya
cubren las regiones nuevas, no hay que tocar `data/colombia_departments.geojson`.

**Caveat de género histórico (`apapachar`)**: había un bug donde responder "Otro" guardaba
`gender` vacío/corrupto en vez de "Otro" — se arregló hoy. Filas de antes de 2026-07-29 con
`gender` vacío/raro probablemente son este bug, no gente que se negó a responder; no es
recuperable retroactivamente. Documentado en el docstring de `db.get_users_by_gender()` — esa
query no está conectada a ninguna página todavía, así que si se construye un breakdown de
género hay que arrastrar este caveat a la UI.

**Mapa geográfico = config por bot (resuelto 2026-08-20)**: el pendiente de "el mapa de Colombia
se renderiza para cualquier bot" se cerró con **`utils/bots.py`**, un registro `bot_id → {label, geo}`.
`pages/usuarios.py` consulta `bot_geo(bot_id)`: si es `"colombia"` renderiza el choropleth de
departamentos + el panel de cobertura territorial (layout 2:1 de siempre); si es `None`
(hoy `mexico` y `demo`) muestra **solo el ranking de regiones a ancho completo**, sin mapa mal
etiquetado y sin "% del país" (una métrica que no significa nada sin GeoJSON), más el caption
`no_geo_map`. Un `bot_id` que aparezca en la DB y no esté en el registro cae a
`DEFAULT_BOT_META` (label = el propio id, sin mapa) — nunca hereda geografía por accidente.
**Cuando Semillas defina su lista de regiones**, agregar el GeoJSON, un `choropleth_mexico()` en
`components/charts.py` y cambiar `BOTS["mexico"]["geo"]` a `"mexico"`; no hay que tocar la página.

### Estado de los datos de `mexico` (verificado 2026-08-20)
La tabla cruda tiene 128 interacciones / 64 conversaciones bajo `bot_id='mexico'`, pero
**~98% es ruido de `aly-evals`**: 126 de esas interacciones vienen de `client_number='eval'` y
las 64 conversaciones son todas `eval-mexico-v*-...`. `_date_filter()` ya las excluye, así que
**lo que el dashboard muestra hoy para México es 1 usuario / 2 mensajes / 1 conversación** — y
esa única fila también es de prueba: `Lorena Nova`, `country='DEMO'`, `region='PRUEBAS'`,
del 2026-07-30. No hay tráfico real de docentes todavía; el dashboard está listo y esperando.

**Bug del onboarding de México — `users_data.gender` guarda el script, no el resultado.** La
única fila de `mexico` tiene en `gender` el **código JavaScript literal** del bloque de Typebot
(`let genderInput = 1\ngenderInput = genderInput.toLowerCase()...`) en vez de `"Hombre"`/
`"Mujer"`/`"Otro"`. El bloque no se está evaluando: se guarda como texto. Hay que arreglarlo en
Typebot **antes** de que entre tráfico real, o toda la demografía de género de Semillas nace
corrupta. Es distinto del caveat de género de `apapachar` (ese guardaba vacío, no el script).

---

## Stack
- **Streamlit ≥ 1.50** — UI con `st.navigation(position="hidden")` + nav custom en sidebar
- **Supabase** (PostgreSQL) — conexión via `psycopg2` con `RealDictCursor`
- **Plotly** — gráficas via fábrica centralizada en `components/charts.py`
- **streamlit-authenticator ≥ 0.4** + **bcrypt** — login usuario/contraseña con roles (ver *Autenticación y roles*)
- **python-dotenv** — `.env` cargado en `app.py`

---

## Estructura de archivos
```
Aly_dashboard/
├── .env                        # DATABASE_URL, PSEUDONYM_KEY (GITIGNORED)
├── Dockerfile                  # Imagen de producción (Python 3.14, instala con constraints.txt)
├── .dockerignore               # Deja .env y secrets.toml fuera de la imagen
├── docker-compose.yml          # Producción en plural-aly: dashboard + Caddy propio en el 443
├── constraints.txt             # Versiones exactas probadas; las usa solo el Dockerfile
├── caddy/Caddyfile             # aly-panel.estudio-plural.co → dashboard:8501 (certificado por TLS-ALPN, sin el 80)
├── .github/workflows/deploy.yml # Despliegue en cada push a main, con el runner propio del servidor
├── .streamlit/
│   ├── config.toml             # Tema Streamlit
│   ├── secrets.toml            # Auth: credenciales + roles (GITIGNORED — no commitear)
│   └── secrets.toml.example    # Plantilla commiteada del secrets.toml
├── app.py                      # Entry point — auth gate (require_login), st.navigation (position="hidden"), CSS, render_sidebar() + render_topbar()
├── pages/
│   ├── overview.py             # Inicio: hero banner, 4 KPIs con sparkline + caption explicativo, growth chart + stat_list (peak hour/day, grid 2:1), usuarios activos por semana + «Indicadores de seguimiento» (registrados acumulados, nuevos en el período, volvieron en 2+ semanas, % respondidas con el material; grid 2:1, desde 2026-11-11 para el M&E de México), heatmap bloques. La gráfica de actividad rellena días sin datos con 0, fija el eje X al rango y desactiva el zoom de Plotly (ver Convenciones)
│   ├── usuarios.py             # Demografía: 3 KPIs (users, regiones, msg/usuario). Layout **según `bot_geo()`**: bots con mapa (apapachar) → 2:1 choropleth Colombia + cobertura + ranking top 10; bots sin mapa (mexico, demo) → ranking top 15 a ancho completo. Al final, **Exportación sin identificar** (botón de Excel, ver sección propia)
│   ├── conversaciones.py       # Keywords + resúmenes (no está en nav, en standby)
│   ├── alertas.py              # Flags 🔴/🟠 (HIGH-/MEDIUM-), export Excel con transcripción, "marcar revisado" persistido en Supabase (reviewed_at)
│   └── leaderboard.py          # Top usuarios: podio, bar top 10, tabla top 20 con Flags 🚩, drill-down con tabs (header muestra teléfono completo del usuario)
├── components/
│   ├── filters.py              # render_sidebar() (logo Aly, nav custom Material icons, bot selector role-aware, date pickers + presets 7d/30d con on_click callbacks, "conectado como" + logout) + render_topbar() (selector de idioma ES/EN arriba a la derecha). get_filters() lee session_state. Sin export — descarga vive en Alertas
│   ├── kpi_row.py              # KPI cards HTML custom: accent bar + icon + sparkline SVG + delta pill. ICONS dict reutilizable
│   └── charts.py               # Fábrica Plotly: bar_h, donut, bar_v, choropleth (silueta flat + dots), choropleth_colombia (departamentos con aliases)
├── data/
│   └── colombia_departments.geojson  # GeoJSON bundled (33 deptos, featureidkey="properties.NOMBRE_DPT")
├── utils/
│   ├── auth.py                 # require_login(): login streamlit-authenticator + resolución rol→bots + logout
│   ├── bots.py                 # Registro bot_id → {label, geo, weekly_deidentified}: nombre legible, qué mapa aplica y si su Excel de los lunes va sin identificar
│   ├── export.py               # Excel de la exportación sin identificar (hojas Cómo leer / Mensajes / Conversaciones / Registros) + chequeo de que no quede ningún identificador crudo
│   ├── pseudonym.py            # IDs seudónimos D-…/C-… con HMAC y PSEUDONYM_KEY — mismo algoritmo que aly-weekly-report
│   ├── db.py                   # Todas las queries SQL
│   ├── i18n.py                 # Traducciones ES/EN via t("key")
│   ├── styles.py               # CSS global + COLORS dict + helpers: page_header, hero_banner, card_header, stat_list, arc_row, section_label
│   └── translate.py            # Traducción de keywords (usada en leaderboard)
└── requirements.txt
```

---

## Navegación
`st.navigation(pages, position="hidden")` oculta la nav nativa; la real se renderiza en `_render_nav()` (components/filters.py) con `st.page_link` + Material Symbols (`:material/dashboard:`, `:material/group:`, `:material/warning:`, `:material/emoji_events:`) agrupados en secciones **ANÁLISIS** (Inicio, Usuarios) y **OPERACIÓN** (Alertas, Leaderboard). La página `conversaciones.py` existe pero no está en `NAV_ITEMS` ni en `app.py:pages`.

**Selector de idioma**: vive en `render_topbar()` (no en el sidebar) — un `st.segmented_control(["ES","EN"], key="lang_seg")` alineado a la derecha del área principal, renderizado en `app.py` antes de `pg.run()` para que aparezca en todas las páginas. Su `on_change` escribe `st.session_state.lang`. CSS: `.topbar-lang` + override compacto de `[data-testid="stSegmentedControl"]` en `utils/styles.py`.

---

## Tablas Supabase
| Tabla | Columnas clave |
|---|---|
| `public.users_interactions` | `conversation_id`, `client_number`, `role`, `message`, `timestamp`, `status`, `created_at` |
| `public.users_data` | `number`, `name`, `country`, `gender`, `region`, `email`, `created_at` |
| `public.conversations_data` | `id` (PK), `conversation_id`, `user_number`, `conversation_date` (**timestamp SIN zona, guardado en UTC**), `summary`, `keywords`, `flags`, `flag_severity` (enum limpio: HIGH / MEDIUM / LOW / Operacional), `flag_reasoning` (texto libre), `messages_count`, `session`, `reviewed_at` (TIMESTAMPTZ — null si pendiente) |
| `vector_aly.rag_embeddings` | `project`, `document_name`, `topics`, `entities`, `key_phrases`, `chunk_index` |

---

## Queries en db.py
Todas las queries de tiempo convierten a **GMT-5 (`America/Bogota`)** vía `AT TIME ZONE` antes de filtrar/extraer hora. Constante `TZ` arriba del módulo.

`_date_filter()` además excluye **siempre** cuentas de testing/eval que vienen del repo hermano `aly-evals` (benchmarks, smoke tests, verify, debug). Las listas viven al inicio de `utils/db.py`: `_TEST_CLIENT_NUMBERS`, `_TEST_CLIENT_LIKE`, `_TEST_CONV_LIKE`. Si aly-evals agrega un nuevo prefijo sentinel, sumarlo a la tupla correspondiente. Queries sobre `conversations_data` pasan `client_col="user_number"`; queries con alias pasan nombres calificados (`client_col="ui.client_number"`). Los drill-downs por usuario explícito apagan el filtro con `client_col=None, conv_col=None`.

- `fetch_df(query, params)` → DataFrame (lecturas)
- `execute(query, params)` → rowcount (escrituras INSERT/UPDATE/DELETE)
- `get_user_kpis(from, to)` → dict n_users, n_sessions
- `get_messages_count(from, to)` → int
- `get_registered_users(from, to)` → dict total (acumulado al cierre del rango) / nuevos (primera fila dentro del rango). Cuenta por `number` y su primera fila: `users_data` no tiene UNIQUE y tiene duplicados. En México la fila nace al aceptar el aviso de privacidad
- `get_returning_users(from, to)` → dict activos / vuelven (escribieron, `role='user'`, en 2+ semanas distintas de lunes a domingo, hora local)
- `get_answer_coverage(from, to)` → dict preguntas / sin_info. Pregunta = mensaje `role='user'` que no es puramente social (`_SOCIAL_MSG_RE`: saludos, gracias, despedidas, respuesta al aviso). Cada una se empareja con el mensaje siguiente de su conversación (LEAD sobre toda la tabla, antes de filtrar el rango); `sin_info` = la respuesta abre con «No tengo esa información» / «I don't have that» (`_NO_INFO_RE`, la frase FACTUAL de los tres bots en el repo Aly). **Si el bot cambia esa frase, actualizar `_NO_INFO_RE`** o el % sube en falso
- `get_weekly_active_users(from, to)` → df week/users (`role='user'`, semana lunes a domingo en GMT-5). La página rellena semanas vacías con 0
- `get_hourly_distribution(from, to)` → df hour/messages (hora en GMT-5; no se usa actualmente en UI — disponible)
- `get_users_by_country/gender/region(from, to)` → df
- `get_daily_activity(from, to)` → df day/messages/users/**sessions** (day en GMT-5; sessions se usa para sparklines de Inicio)
- `get_activity_heatmap(from, to)` → df dow/hour/messages (en GMT-5)
- `get_conversation_metrics(from, to)` → dict métricas agregadas (incluye `avg_msg_per_user`)
- `get_kpi_deltas(from, to)` → dict deltas fraccionales vs período anterior
- `get_conversations_data(from, to, lang="es")` → df completo de conversations_data
- `get_summaries(from, to, limit, lang="es")` → df resúmenes recientes
- `get_flags_data(from, to)` → df conversaciones con flags + `id` (PK) + `reviewed_at` (en GMT-5)
- `mark_flag_reviewed(row_id)` → UPDATE … SET reviewed_at = NOW() **WHERE id** (ver *Identidad de fila*)
- `unmark_flag_reviewed(row_id)` → UPDATE … SET reviewed_at = NULL **WHERE id**
- `get_flag_counts_by_user(from, to)` → df user_number/n_flags (solo HIGH-/MEDIUM-)
- `get_leaderboard(from, to, limit)` → df top usuarios (last_seen / days_active en GMT-5)
- `get_pseudonymous_export_data(from, to)` → dict de 3 df **con número y conversation_id crudos** (messages / conversations / registrations) para `utils/export.py`, que es lo único que debe llamarla. `messages` reusa `_MSGS_WITH_REPLY_CTE` (la misma CTE de `get_answer_coverage`, así que el % sale igual); `conversations` lee `flag_severity` y ancla `conversation_date` a UTC antes de pasarla a GMT-5
- `get_interactions_export(from, to)` → df para Excel export de interacciones (queda disponible aunque ya no se exponga en sidebar)
- `get_messages_by_conversation_ids(conv_ids)` → df mensajes para lista de conversation_ids
- `get_user_conversations(user_number, from, to, lang="es")` → df conversaciones de un usuario (drill-down)
- `get_user_messages(user_number, from, to)` → df mensajes de un usuario (drill-down)

### Contenido bilingüe (ES/EN) de summary/keywords
El bot (`Aly_Apapachar`) escribe en `conversations_data` dos columnas JSONB extra — `summary_i18n` y `keywords_i18n` (`{"es": ..., "en": ...}`, keywords como CSV por idioma) — además del `summary`/`keywords` original. Las queries que devuelven esos campos (`get_conversations_data`, `get_summaries`, `get_user_conversations`) aceptan `lang` ('es'/'en', default 'es') y leen la versión del idioma con **fallback al original** vía el helper `_i18n_expr()`. El `lang` viene de `st.session_state.get("lang", "es")` y lo pasan `conversaciones.py` y `leaderboard.py`.

**Robustez:** `_conversations_has_i18n()` detecta (una vez por proceso, cacheado) si las columnas existen vía `information_schema`. Si la migración del bot **aún no corrió**, `_i18n_expr()` devuelve la columna original y nada se rompe; cuando la migración llegue con la app levantada, hace falta **Reboot app** para re-detectar. La traducción vive **del lado del bot**, no del dashboard — `utils/translate.py` (OpenRouter) quedó **sin uso** (el wordcloud de Leaderboard ahora toma los keywords ya traducidos de la DB).

---

## Componentes reutilizables (utils/styles.py)
- `page_header(title, subtitle="", show_period=True)` — H1 + subtítulo + chip de período (auto desde session_state).
- `hero_banner(headline_html, status_text, status_kind, meta_label, meta_value)` — banner gradient con status pill (`ok`/`warn`/`crit`) y número destacado a la derecha. Usa `<b>` dentro del headline para números grandes.
- `card_header(title, subtitle="", icon_svg="", right_text="")` — header estándar sobre charts/tablas. Reemplaza al viejo `section_label` (que existe pero está legacy).
- `stat_list(items=[{label, value}])` — card vertical compacto tipo sidebar stats.
- `arc_row(items=[{label, pct, value?, accent?}])` — fila de gauges SVG 3/4 (0-100%), label arriba, value dentro del arco.
- `section_label(text)` — legacy, evitar en páginas nuevas.

## KPI cards (components/kpi_row.py)
`render(metrics: list[dict])`. Cada dict:
- `label`, `value`, `delta` (fracción o None), `delta_label`, `prefix`, `suffix`
- `accent`: color key de COLORS (`accent` | `navy` | `positive` | `yellow` | `red`) — pinta la barra izquierda y los dots del sparkline
- `icon`: key de `kpi_row.ICONS` (`users`, `message`, `send`, `chart`, `alert-triangle`, `alert-circle`, `flag`, `activity`)
- `spark`: lista de valores para sparkline SVG inline (opcional)
- `caption`: oración corta explicativa bajo el valor (opcional) — clase `.kpi-card__caption`. En Inicio cada KPI la usa para autoexplicarse (ej. "Personas que interactuaron con Aly").

---

## Convenciones obligatorias
- **SQL**: siempre parametrizado con `%s`. Nunca f-strings con datos externos. `_date_filter()` construye el WHERE.
- **Zona horaria**: la DB guarda timestamptz en UTC, pero la UI opera en **GMT-5 (`America/Bogota`)**. Toda query nueva que extraiga hora/día o filtre por fecha debe convertir con `AT TIME ZONE '{TZ}'` (constante en `utils/db.py`). El "today" del sidebar también se calcula con `ZoneInfo("America/Bogota")`.
- **Filtros globales**: en `st.session_state` (`filter_from`, `filter_to`). Inicializados en `components/filters.py`. Páginas los leen con `get_filters()` (que devuelve `date_to` **exclusivo** = fecha elegida + 1 día).
- **Gráficas de series temporales**: las queries (`get_daily_activity`, etc.) solo devuelven días **con** datos. Para que el filtro de fechas se vea respetado, rellenar los días faltantes con 0 (reindex sobre `pd.date_range(date_from, date_to)`), fijar el eje X con `fig.update_xaxes(range=[...], fixedrange=True)` y desactivar el modebar (`config={"displayModeBar": False}`). Si hay menos días con datos que el span, mostrar `t("sparse_data_note")`. Patrón vivo en `overview.py` (actividad diaria). Evita que un rango con datos escasos parezca un filtro roto.
- **Widgets Streamlit**: si un widget usa `key=`, NO pasar también `value=` — Streamlit lanza warning. Usar session_state para valor inicial. Para presets que mutan widget keys (ej. `7d`/`30d`), usar `on_click` callbacks — asignar a `st.session_state[key]` después de renderizar el widget se ignora silenciosamente.
- **Texto**: todo via `t("key")` de `utils/i18n.py`. Agregar claves nuevas en ambos idiomas.
- **CSS**: inyectado con `st.html(css)` en `utils/styles.inject()`. HTML de componentes sí usa `st.markdown(unsafe_allow_html=True)` (ver `hero_banner`, `card_header`, `arc_row`, `kpi_row`).
- **Colores**: siempre desde el dict `COLORS` de `utils/styles.py`. No hardcodear hex.
- **Números de teléfono**: enmascarar en la UI (primeros 4 dígitos + `****` + últimos 2). El Excel de alertas exporta el número sin mask intencionalmente para el equipo de respuesta.
- **Íconos del sidebar**: override CSS para que las ligatures de Material Symbols no hereden `Open Sans` del selector global `*` del sidebar (ver `utils/styles.py`).
- **Estado compartido entre usuarios**: persistir en Supabase, no en `st.session_state` (que es por sesión de browser). Ej.: `reviewed_at` de las flags vive en `conversations_data`, no en memoria.
- **Filtrado de cuentas test**: toda query nueva sobre `users_interactions/conversations_data` debe pasar por `_date_filter()` para heredar el filtro de aly-evals automáticamente. No bypassear con `fetch_df` directo sin pensar en qué datos estás trayendo.
- **Python 3.9 en local, 3.14 en producción**: en el Mac la app corre sobre el Python 3.9 del sistema; en plural-aly, sobre 3.14 (Docker). El código tiene que andar en los dos. **No usar la sintaxis `X | None`** (PEP 604) en anotaciones de módulos compartidos — falla al importar con `TypeError: unsupported operand type(s) for |`. Usar `Optional[X]` de `typing`, defaults sin tipo, o `from __future__ import annotations` al inicio del módulo (como `utils/auth.py`). Ojo: `py_compile` NO atrapa esto (es eval en runtime al definir) y un HTTP 200 de Streamlit es solo el shell estático; verificar con `python3 -c "import módulo"` o `streamlit.testing.v1.AppTest`.

---

## Identidad de fila en `conversations_data`: usar `id`, NO `conversation_id`

**`conversation_id` no es único.** El bot reusa el mismo id para conversaciones distintas del
mismo usuario en días distintos: al 2026-08-20 hay 2 colisiones en `apapachar` (ej. `3132312`,
del 2 y del 11 de junio, resúmenes distintos) y 20 en `demo`. La PK real de la tabla es la
columna **`id` (bigint)**.

Esto causaba dos bugs en `pages/alertas.py`, arreglados el 2026-08-20:
1. **Crash**: el checkbox "marcar revisado" usaba `key=f"rev_{conv_id}"`; dos filas con el mismo
   `conversation_id` producían keys duplicadas y Streamlit tumbaba la página entera con
   `StreamlitDuplicateElementKey`. Reventaba con `demo` seleccionado; `apapachar` se salvaba
   solo porque sus 2 colisiones no traían flag HIGH/MEDIUM (la página filtra a rojo/naranja).
2. **Corrupción silenciosa, peor que el crash**: `mark_flag_reviewed` hacía
   `UPDATE … WHERE conversation_id = %s`, así que marcar una conversación marcaba **todas** las
   que compartían el id — incluida una alerta real que nadie había revisado, que desaparecía del
   toggle "ocultar revisadas" sin que nadie la mirara. Verificado: el UPDATE viejo tocaba 2 filas,
   el nuevo toca 1.

**Regla**: cualquier query o widget nuevo sobre `conversations_data` que necesite identificar
una fila debe traer y usar `id`. `conversation_id` sirve para mostrar y para cruzar con
`users_interactions` (que no tiene forma de distinguir las colisiones), nunca como clave.

---

## Exportación sin identificar (desde 2026-11-11)
Pedido de Rachel para el M&E de Semillas: ID seudónimo, fecha/hora y alerta de riesgo, sin teléfono ni nombre, para que calculen sus propias cifras. Vive al final de **Usuarios** (`st.download_button`, cacheado 10 min por bot + rango + idioma) y sirve a todos los bots.

- **Hojas**: «Cómo leer» (definiciones; la versión de México aclara que la hora del centro de México es GMT-6), «Mensajes» (un mensaje `role='user'` por fila: ID, ID conversación, fecha y hora, semana, Pregunta / Saludo o cierre, cómo respondió Aly), «Conversaciones» (una por fila: alerta Alta/Media/Baja/Ninguna desde `flag_severity` + las etiquetas `HIGH-/MEDIUM-/LOW-` sin prefijo), «Registros» (primera fila de `users_data` por número, acumulado hasta el cierre del rango).
- **No lleva** teléfono, nombre, texto de mensajes, `summary` ni `flag_reasoning`. `build_excel()` revisa antes de devolver que ninguna celda sea un número o `conversation_id` crudo (y que ningún identificador de 10+ caracteres aparezca adentro de una celda); si pasa, falla en vez de entregar el archivo.
- **IDs**: `D-` + 8 hex de HMAC-SHA256(`PSEUDONYM_KEY`, número). **Tiene que coincidir con `src/pseudonym.py` de aly-weekly-report**, que pone el mismo ID en el Excel de los lunes de México. Las conversaciones llevan `C-` + HMAC de `conv:<número>:<conversation_id>`, porque el `conversation_id` empieza con el teléfono.
- **Llave**: `PSEUDONYM_KEY` en el `.env` (en producción, `/opt/aly-dashboard/.env` en plural-aly; en local, el `.env` del repo). `get_key()` también la busca como clave de primer nivel de `st.secrets`, arriba de `[cookie]`. Es la misma del secret del reporte semanal; copia en `~/Dev/_backups_aly/aly-weekly-report.env`. Si se pierde, los IDs cambian. Sin llave la sección no ofrece el botón (al admin le dice qué falta).
- **Verificado el 2026-11-11** contra las queries del dashboard en los tres bots: activos, los que vuelven, activos por semana, preguntas, «sin información», registrados y alertas Alta/Media recalculados desde el Excel coinciden; los IDs coinciden con los del reporte semanal; cero celdas con teléfono, nombre o `conversation_id`.

---

## Clasificación de flags
El campo `flags` en `conversations_data` es un string CSV con múltiples flags por conversación, cada una con prefijo de severidad:
- `HIGH-<razón>` → 🔴 rojo (crítico)
- `MEDIUM-<razón>` → 🟠 naranja (advertencia)
- `LOW-<razón>` → ignorado en UI (no se muestra)

La lógica de clasificación vive en `_classify_flag()` en `pages/alertas.py`. También se replica en `pages/overview.py` (para el status del hero banner) y `pages/leaderboard.py` (para contar flags por usuario).

**Si el bot cambia el formato de estos campos, actualizar `_classify_flag()` en los 3 archivos.**

---

## Estilo visual
- **Fuentes**: Oswald (títulos, valores KPI, hero number) · Open Sans (body, labels, captions) · Material Symbols Rounded (íconos de nav) — Google Fonts
- **Sidebar**: claro `#FFFFFF` con borde gris, logo con cuadrado gradient (azul→navy) + wordmark "Aly"
- **Cards / fondo contenedores**: blanco `#FFFFFF`
- **Fondo app**: `#F7F8FA` (cool gray, más premium que el antiguo `#F0F2F5`)
- **Accent principal**: `#0273e5` · **Navy**: `#110079` · **Amarillo**: `#FFCF24` · **Naranja**: `#F15B22`
- **Positivo/negativo**: `#22C55E` / `#F15B22`
- **Heatmap**: `go.Heatmap` con `xgap=3, ygap=3` para bloques discretos tipo GitHub contributions; paleta gray→blue→accent.
- **Mapa de países**: `choropleth()` en charts.py renderiza **scattergeo silueta plana** — land `#D1D5DB`, sin bordes de países/costas, dots accent blue con halo soft bajo cada dot. **No se usa en Usuarios actualmente** (se reemplazó por el mapa de Colombia) pero la función queda disponible.
- **Mapa de Colombia**: `choropleth_colombia()` en charts.py — `go.Choropleth` con GeoJSON local (`data/colombia_departments.geojson`). Siempre renderiza los 33 departamentos (deptos sin datos en gris `#E5E7EB`); rampa `#DBEAFE→#3B82F6→accent` para deptos con usuarios. `showscale=False` (la cobertura ya está en el panel lateral). Aliases para normalizar variantes de input: `bogota`→`SANTAFE DE BOGOTA D.C`, `san andres`→`ARCHIPIELAGO ...`, `guajira`→`LA GUAJIRA`, `valle`→`VALLE DEL CAUCA`. Las regiones que no matchean ningún departamento se listan como caption bajo el mapa.

---

## Proyecto Complementario: Aly_Apapachar

**Ubicación**: `/Users/daniel/Dev/Aly_Apapachar/`

Aly_Apapachar es el bot WhatsApp (LangGraph + MongoDB + Twilio) que **genera los datos** que este dashboard visualiza.

### Flujo de datos
```
Aly_Apapachar (bot) → Conversation Closer → Supabase → este dashboard
```

### Contrato de datos
- `keywords`: string CSV — se parsea con `split(",")` en `conversaciones.py`
- `flags`: string CSV con prefijos `HIGH-` / `MEDIUM-` / `LOW-` por flag, múltiples flags por conversación
- `summary`: texto libre en el idioma del facilitador

### Quién escribe cada tabla
| Tabla | Escrita por |
|---|---|
| `public.users_interactions` | `bot.py` (cada mensaje) |
| `public.users_data` | `onboarding_agent.py` (registro nuevo usuario) |
| `public.conversations_data` | Conversation Closer escribe la fila inicial. El **dashboard** escribe `reviewed_at` cuando el equipo marca la flag como revisada |
| `vector_aly.rag_embeddings` | scripts de ingest |

### Otros escritores (ruido conocido)
`aly-evals` (repo hermano en `~/Dev/aly-evals/`) corre benchmarks contra el bot y termina escribiendo cientos de filas sentinel (`client_number IN ('eval','verify','smoke',…)`, `conversation_id LIKE 'eval-%' / 'verify-%' / 'debug-%' / …`). El filtro en `_date_filter()` las excluye automáticamente del dashboard. Antes del filtro (commit `d981c15`, 2026-05-27), `eval` solo aportaba 458 conversaciones / 918 mensajes.

---

## Despliegue

**Producción: https://aly-panel.estudio-plural.co** — Docker en **plural-aly** (el servidor del bot Aly, Hostinger, 187.124.150.145), en `/opt/aly-dashboard`, como proyecto de compose propio (`-p aly-dashboard`): no comparte red ni archivos con el bot. Antes estaba en Streamlit Cloud (`aly-dashboard-pejmrmpdvh8wqefx2ibnzj.streamlit.app`); se mudó en nov-2026.

- **Cómo se despliega**: cada push a `main` corre `.github/workflows/deploy.yml` en un **runner propio instalado en el servidor** (label `aly-dashboard`, usuario `aly-deploy`, del grupo docker y dueño de `/opt/aly-dashboard`). Copia el código con rsync, hace `docker compose up -d --build`, recarga Caddy y verifica `/_stcore/health` por HTTPS. También se puede correr a mano desde Actions (`workflow_dispatch`). Merge = despliegue, igual que antes con Streamlit Cloud. **El repo tiene que ser privado**: con un runner propio, un repo público deja que un PR desde un fork corra código en el servidor del bot.
- **Secretos** (fuera de git y de la imagen, `chmod 600`, en `/opt/aly-dashboard`): `.env` con `DATABASE_URL` y `PSEUDONYM_KEY`, y `.streamlit/secrets.toml` con `[cookie]`, `[credentials]` y `[roles]`. El rsync del workflow los excluye, así que sobreviven a cada despliegue. Para cambiar una contraseña o la llave: editar el archivo en el servidor y `docker compose -p aly-dashboard restart dashboard` desde `/opt/aly-dashboard`. **`PSEUDONYM_KEY` es la misma del reporte semanal** (ver *Exportación sin identificar*).
- **HTTPS**: Caddy propio del panel, que publica **solo el 443**. El 80 del servidor es de Traefik (el proxy del bot) y no se toca: Caddy saca el certificado de Let's Encrypt por el 443 (desafío TLS-ALPN-01, `disable_http_challenge`). Por eso el link siempre va con `https://`; un `http://` lo contesta Traefik. DNS: registro A `aly-panel` → 187.124.150.145 en **Wix** (los nameservers de estudio-plural.co son de Wix).
- **Montajes de carpeta, no de archivo**: `./.streamlit` y `./caddy` se montan como carpetas. Un montaje de un archivo suelto queda pegado al archivo viejo cuando rsync o un editor lo reemplazan, y el contenedor seguiría leyendo la versión anterior.
- **Versiones**: el Dockerfile instala `requirements.txt` **con `constraints.txt`** (las versiones exactas con las que se probó; Streamlit 1.67, pandas 3.1). Así cada despliegue arma la misma imagen. Para subir una versión: cambiarla en `constraints.txt` a propósito, probar con AppTest en un venv de Homebrew 3.14 y verificar que haya ruedas para Linux con `pip download --only-binary=:all: --platform manylinux_2_28_x86_64 --python-version 3.14 -r requirements.txt -c constraints.txt`. Streamlit 1.67 avisa que `use_container_width` se va a quitar: antes de subir Streamlit, pasarlo a `width="stretch"`.
- **Límites**: el contenedor del panel tiene `mem_limit: 1g` y `cpus: 1.0` para no quitarle recursos al bot, y los logs de Docker rotan (10 MB × 3).
- **Acceso al servidor**: el clasificador de Claude bloquea hasta las lecturas por SSH a producción, así que lo del servidor lo corre Daniel con `!` (los comandos, al portapapeles).
- **Local**: `python3 -m streamlit run app.py` (Python 3.9 del sistema, sin Docker).

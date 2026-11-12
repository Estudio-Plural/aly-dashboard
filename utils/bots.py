"""Config por bot (``bot_id``).

Cada bot que escribe a la DB compartida es un programa distinto, con su propia
población, su propio onboarding y su propia geografía. Este módulo centraliza
lo que el dashboard necesita saber de cada uno para no hardcodear supuestos de
Apapáchar (Colombia) en páginas que también sirven a México.

``geo`` indica qué mapa aplica a los valores de ``users_data.region``:
  - ``"colombia"`` → choropleth de los 33 departamentos (``choropleth_colombia``)
  - ``None``       → el bot no tiene mapa; la página muestra solo el ranking de
                     regiones, sin cobertura territorial ni copy de país.

Un ``bot_id`` que aparezca en la DB y no esté acá cae a ``DEFAULT_BOT_META``
(etiqueta = el propio id, sin mapa) — el dashboard no se rompe, simplemente no
asume geografía que no conoce.
"""

# ``logo``: (archivo en assets/logos, texto alternativo) que se muestra en la
# barra lateral cuando ese bot está seleccionado. None = sin logo de programa.
DEFAULT_BOT_META = {"label": None, "geo": None, "weekly_deidentified": False, "logo": None}

BOTS = {
    "apapachar": {
        # Apapáchar (Fundación Apapacho) — crianza 0-5 años, Colombia.
        "label": "Apapáchar · Colombia",
        "geo": "colombia",
        "logo": ("apapachar.png", "Programa Apapáchar"),
    },
    "mexico": {
        # "Semillas de Igualdad" (Equimundo + GENDES / Tec de Monterrey) —
        # docentes de preescolar en el Estado de México. Su onboarding aún no
        # define lista de regiones, así que no tiene mapa todavía.
        "label": "Semillas · México",
        "geo": None,
        # Su Excel de los lunes va sin identificar, con el mismo ID seudónimo que
        # la exportación (``Audience.deidentify`` en aly-weekly-report). Si se
        # prende allá para otro bot, prenderlo acá también.
        "weekly_deidentified": True,
    },
    "demo": {
        "label": "Demo · Equimundo",
        "geo": None,
    },
}


def bot_meta(bot_id: str) -> dict:
    """Metadata del bot, con fallback seguro para ids desconocidos."""
    return BOTS.get(bot_id, DEFAULT_BOT_META)


def bot_label(bot_id: str) -> str:
    """Nombre legible para la UI. Cae al propio ``bot_id`` si no está mapeado."""
    return bot_meta(bot_id).get("label") or bot_id


def bot_geo(bot_id: str):
    """Mapa geográfico aplicable ('colombia' | None)."""
    return bot_meta(bot_id).get("geo")


def bot_weekly_deidentified(bot_id: str) -> bool:
    """Si el Excel de los lunes de este bot lleva el mismo ID seudónimo que la exportación."""
    return bool(bot_meta(bot_id).get("weekly_deidentified"))


def bot_logo(bot_id: str):
    """(archivo, alt) del logo del programa, o None si el bot no tiene."""
    return bot_meta(bot_id).get("logo")

"""Clasificación de alertas: roja (HIGH), naranja (MEDIUM) u otra.

Una sola regla para Alertas, Inicio y Conversaciones. Se lee ``flag_severity``,
el enum limpio que escribe el bot al cerrar la conversación (HIGH / MEDIUM /
LOW / Operacional), igual que los correos de alertas de aly-weekly-report y la
exportación sin identificar (``utils/export.py``).

Antes cada página buscaba subcadenas en todo el texto de ``flags`` (``"red" in
valor``) y «LOW-shared-personal-info» salía como alerta roja porque «shared»
contiene «red».

Si ``flag_severity`` viene vacío (conversaciones cerradas antes del 2026-04-07,
cuando el bot todavía no la escribía), se usa la misma regla con la que el bot
la calcula (``ConversationCloserService._getSeverity``): el prefijo ``HIGH-`` /
``MEDIUM-`` / ``LOW-`` de alguna etiqueta de ``flags``, etiqueta por etiqueta y
nunca como subcadena. Las etiquetas viejas no tienen prefijo, así que esas
conversaciones no cuentan como alerta, como tampoco cuentan en los correos.
"""

import re
from typing import Optional

import pandas as pd

RED = "red"
ORANGE = "orange"
OTHER = "other"

_LEVEL = {"HIGH": RED, "MEDIUM": ORANGE}
_PREFIX_RE = re.compile(r"^(HIGH|MEDIUM|LOW)-", re.IGNORECASE)
_ORDER = ("HIGH", "MEDIUM", "LOW")


def _text(value) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def severity_from_flags(flags) -> Optional[str]:
    """HIGH / MEDIUM / LOW según el prefijo de las etiquetas de ``flags``; None si ninguna lo lleva."""
    found = set()
    for tag in _text(flags).split(","):
        m = _PREFIX_RE.match(tag.strip())
        if m:
            found.add(m.group(1).upper())
    for sev in _ORDER:
        if sev in found:
            return sev
    return None


def alert_level(severity, flags=None) -> str:
    """``"red"`` si es HIGH, ``"orange"`` si es MEDIUM, ``"other"`` en cualquier otro caso."""
    sev = _text(severity).upper()
    if not sev:
        sev = severity_from_flags(flags) or ""
    return _LEVEL.get(sev, OTHER)


def alert_levels(df: pd.DataFrame) -> pd.Series:
    """``alert_level`` fila por fila, con las columnas ``flag_severity`` y ``flags``."""
    if df.empty:
        return pd.Series([], index=df.index, dtype=object)
    sev = df["flag_severity"] if "flag_severity" in df else pd.Series(None, index=df.index)
    flags = df["flags"] if "flags" in df else pd.Series(None, index=df.index)
    return pd.Series([alert_level(s, f) for s, f in zip(sev, flags)], index=df.index, dtype=object)

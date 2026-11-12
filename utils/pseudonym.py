"""IDs seudónimos para la exportación sin identificar.

El ID es un HMAC-SHA256 del número con una llave secreta (``PSEUDONYM_KEY``).
Un hash sin llave no alcanza: los teléfonos son pocos y se pueden probar todos
hasta dar con el que produce cada ID. Sin la llave eso no se puede.

**Tiene que dar el mismo ID que el reporte semanal** (``src/pseudonym.py`` en
Estudio-Plural/aly-weekly-report): misma llave, mismo algoritmo, mismo formato
``D-`` + 8 hex. Así una docente es la misma en el Excel del lunes y en esta
exportación. Si se cambia algo acá, se cambia allá.

La llave vive en el ``.env`` (en producción, ``/opt/aly-dashboard/.env`` en
plural-aly). También se acepta como clave de primer nivel de ``st.secrets``
(arriba de cualquier ``[sección]``). Sin llave la exportación no se ofrece: la
promesa es que el ID no cambie de una exportación a otra.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Optional

ENV_KEY = "PSEUDONYM_KEY"


def get_key() -> Optional[bytes]:
    key = os.getenv(ENV_KEY, "").strip()
    if not key:
        try:
            import streamlit as st
            key = str(st.secrets.get(ENV_KEY, "")).strip()
        except Exception:
            key = ""
    return key.encode() if key else None


def _digest(key: bytes, value: str) -> str:
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()


def user_id(key: bytes, number) -> str:
    """Número → ``D-xxxxxxxx``. Idéntico a ``make_pseudonymizer()`` del reporte semanal."""
    return f"D-{_digest(key, str(number))[:8]}"


def conversation_id(key: bytes, number, conv_id) -> str:
    """Conversación → ``C-xxxxxxxx``.

    El ``conversation_id`` del bot empieza con el teléfono, así que tampoco se
    puede mostrar. Se combina con el número y un prefijo propio para que no
    coincida nunca con un ID de persona.
    """
    return f"C-{_digest(key, f'conv:{number}:{conv_id}')[:8]}"

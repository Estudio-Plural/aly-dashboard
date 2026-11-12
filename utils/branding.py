"""Logos de las organizaciones, embebidos como data URI.

Viven en ``assets/logos/`` (PNG chicos, ~15 KB). Van embebidos en el HTML y no
con ``st.image`` para poder ubicarlos dentro de los bloques de marca (login y
barra lateral) sin depender del static serving de Streamlit.

- ``equimundo.png``: el cuadrado de 640×640 que Laura Phillips-Alvarez
  (Equimundo) mandó el 2026-07-29 para el perfil de WhatsApp del demo; va en
  el login.
- ``apapachar.png``: el «Programa apapáchar» que Milena Yazo (Fundación
  Apapacho) mandó el 2026-08-03; va en la barra lateral cuando el bot es
  Apapáchar.

Para cambiar uno, reemplazar el archivo (mismo nombre). Ver ``bot_logo()`` en
``utils/bots.py`` para asignarle logo a otro bot.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path
from typing import Optional

_DIR = Path(__file__).resolve().parent.parent / "assets" / "logos"


@lru_cache(maxsize=None)
def logo_data_uri(filename: str) -> Optional[str]:
    """``data:image/png;base64,…`` del logo, o None si el archivo no está."""
    path = _DIR / filename
    if not path.is_file():
        return None
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()

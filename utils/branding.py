"""Marca Aly y logos de las organizaciones, embebidos como data URI.

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

_ASSETS = Path(__file__).resolve().parent.parent / "assets"
_DIR = _ASSETS / "logos"
_BRAND = _ASSETS / "brand"
_MIME = {".png": "image/png", ".svg": "image/svg+xml"}


def _data_uri(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    mime = _MIME.get(path.suffix.lower(), "application/octet-stream")
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


@lru_cache(maxsize=None)
def logo_data_uri(filename: str) -> Optional[str]:
    """Logo de una organización aliada (``assets/logos/``), o None si no está."""
    return _data_uri(_DIR / filename)


@lru_cache(maxsize=None)
def brand_data_uri(filename: str) -> Optional[str]:
    """Una pieza de la marca Aly (``assets/brand/``: logotipo, isotipo…).

    Los SVG van como <img> con data URI y no inline: así el sanitizador de
    st.markdown no los toca y el dibujo queda idéntico al archivo."""
    return _data_uri(_BRAND / filename)


def brand_path(filename: str) -> str:
    """Ruta absoluta a una pieza de la marca (para st.set_page_config, etc.)."""
    return str(_BRAND / filename)

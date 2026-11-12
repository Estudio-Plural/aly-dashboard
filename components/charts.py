"""Centralized Plotly chart factory — consistent styling across all pages."""

import json
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.styles import COLORS

_BASE = dict(
    paper_bgcolor=COLORS["bg_card"],
    plot_bgcolor=COLORS["bg_card"],
    font=dict(family="Figtree, sans-serif", size=11, color=COLORS["text"]),
    margin=dict(l=8, r=8, t=14, b=8),
    hoverlabel=dict(
        bgcolor=COLORS["bg_card"],
        bordercolor=COLORS["border"],
        font=dict(family="Figtree, sans-serif", size=11),
    ),
)

_AXIS = dict(
    gridcolor=COLORS["ramp"][0],
    linecolor=COLORS["border"],
    tickfont=dict(size=10, color=COLORS["text_secondary"]),
    title=None,  # hidden by default — card_header shows the label
)


def _layout(title: str = "", **kw):
    base = {**_BASE, "xaxis": _AXIS.copy(), "yaxis": _AXIS.copy()}
    if title:
        base["title"] = dict(
            text=title, x=0.01, xanchor="left",
            font=dict(family="Figtree, sans-serif", size=12,
                      color=COLORS["text_secondary"]),
        )
        base["margin"] = dict(l=8, r=8, t=40, b=8)
    base.update(kw)
    return base


# ── Bar (horizontal) ─────────────────────────────────────────────────────────

def bar_h(df: pd.DataFrame, x: str, y: str, title: str = "",
          color: str = None, height: int = 280) -> go.Figure:
    color = color or COLORS["accent"]
    fig = px.bar(
        df, x=x, y=y, orientation="h",
        color_discrete_sequence=[color],
    )
    fig.update_layout(**_layout(title=title, height=height,
                                yaxis_categoryorder="total ascending"))
    fig.update_yaxes(title_text="")
    # Conteos: enteros y con la cifra al final de la barra. Con valores chicos
    # Plotly ponía el eje en 0 / 0,5 / 1, que no existe para personas.
    x_max = int(df[x].max()) if len(df) else 0
    fig.update_xaxes(title_text="", tickformat=",d", rangemode="tozero",
                     dtick=1 if x_max <= 8 else None, fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_traces(
        marker_line_width=0,
        text=df[x], textposition="outside", cliponaxis=False,
        textfont=dict(size=11, color=COLORS["text"]),
        hovertemplate="<b>%{y}</b><br>%{x} usuarios<extra></extra>",
    )
    return fig


# ── Donut chart ───────────────────────────────────────────────────────────────

def donut(df: pd.DataFrame, names: str, values: str, title: str = "",
          height: int = 280) -> go.Figure:
    palette = [COLORS["accent"], COLORS["yellow"], COLORS["red"], COLORS["green"], COLORS["navy"]]
    fig = px.pie(
        df, names=names, values=values,
        color_discrete_sequence=palette,
        hole=0.55,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        textfont=dict(family="Figtree, sans-serif", size=12, color="#FFFFFF"),
        marker=dict(line=dict(color=COLORS["bg_card"], width=2)),
        hovertemplate="<b>%{label}</b><br>%{value} usuarios (%{percent})<extra></extra>",
    )
    layout = {**_BASE, "height": height, "showlegend": True,
              "legend": dict(orientation="h", yanchor="bottom", y=-0.1,
                             xanchor="center", x=0.5, font=dict(size=11))}
    if title:
        layout["title"] = dict(
            text=title, x=0.01, xanchor="left",
            font=dict(family="Figtree, sans-serif", size=12,
                      color=COLORS["text_secondary"]),
        )
        layout["margin"] = dict(l=8, r=8, t=40, b=8)
    fig.update_layout(**layout)
    return fig


# ── Bar (vertical) ────────────────────────────────────────────────────────────

def bar_v(df: pd.DataFrame, x: str, y: str, title: str = "",
          color: str = None, height: int = 240) -> go.Figure:
    color = color or COLORS["accent"]
    fig = px.bar(df, x=x, y=y, color_discrete_sequence=[color])
    fig.update_layout(**_layout(title=title, height=height, bargap=0.25))
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="")
    fig.update_traces(marker_line_width=0)
    return fig


# ── Silhouette world map (flat land + accent dots at locations) ──────────────

def choropleth(df: pd.DataFrame, locations: str, color: str, title: str = "",
               height: int = 260) -> go.Figure:
    """Flat silhouette map: land mass in a single muted gray (no borders, no
    coastlines), with accent dots at each country with users. Kept under the
    original name for backwards compatibility with callers.
    """
    if df.empty:
        return go.Figure()

    max_n = max(int(df[color].max()), 1)
    df = df.copy()
    df["_size"] = (df[color] / max_n * 14) + 10

    fig = go.Figure()

    # Soft halo under each dot (same location, bigger + transparent)
    fig.add_trace(go.Scattergeo(
        locations=df[locations],
        locationmode="country names",
        marker=dict(
            size=df["_size"] * 2.2,
            color=COLORS["accent"],
            opacity=0.18,
            line=dict(width=0),
        ),
        showlegend=False, hoverinfo="skip",
    ))

    # Main accent dot per country
    fig.add_trace(go.Scattergeo(
        locations=df[locations],
        locationmode="country names",
        text=df[locations],
        customdata=df[color],
        marker=dict(
            size=df["_size"],
            color=COLORS["accent"],
            opacity=1.0,
            line=dict(color="#FFFFFF", width=1.5),
        ),
        hovertemplate="<b>%{text}</b><br>%{customdata} usuarios<extra></extra>",
        showlegend=False,
    ))

    layout = {
        **_BASE, "height": height,
        "geo": dict(
            showframe=False,
            showcoastlines=False,
            showcountries=False,
            showland=True,     landcolor=COLORS["border_strong"],
            showocean=False,
            showlakes=False,
            projection_type="natural earth",
            resolution=110,
            bgcolor=COLORS["bg_card"],
            lonaxis_showgrid=False, lataxis_showgrid=False,
        ),
    }
    if title:
        layout["title"] = dict(
            text=title, x=0.01, xanchor="left",
            font=dict(family="Figtree, sans-serif", size=12,
                      color=COLORS["text_secondary"]),
        )
        layout["margin"] = dict(l=0, r=0, t=40, b=0)
    else:
        layout["margin"] = dict(l=0, r=0, t=8, b=8)

    fig.update_layout(**layout)
    return fig


# ── Colombia department choropleth ───────────────────────────────────────────

_COLOMBIA_GEOJSON_PATH = (
    Path(__file__).parent.parent / "data" / "colombia_departments.geojson"
)
_COLOMBIA_FEATURE_KEY = "properties.NOMBRE_DPT"


@lru_cache(maxsize=1)
def _load_colombia_geojson() -> dict:
    with open(_COLOMBIA_GEOJSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_region(s) -> str:
    """Normalize a raw `users_data.region` value for department matching.

    Strips accents/case and the literal "Regional " prefix the Apapáchar
    onboarding started writing on 2026-07-29 (e.g. "Regional Tolima"), so
    pre- and post-cutover rows for the same department group together
    instead of appearing as two separate regions on the map/ranking.
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.strip().lower()
    if s.startswith("regional "):
        s = s[len("regional "):]
    return s.strip()


def display_region(s) -> str:
    """Nombre de región para mostrar: sin el prefijo «Regional » que el
    onboarding de Apapáchar agrega desde el 2026-07-29 (con tildes y
    mayúsculas, a diferencia de _normalize_region, que es para comparar)."""
    s = str(s or "").strip()
    return s[len("regional "):].strip() if s.lower().startswith("regional ") else s


_COLOMBIA_ALIASES = {
    # User-input form (normalized) → GeoJSON canonical (NOMBRE_DPT)
    "bogota":               "SANTAFE DE BOGOTA D.C",
    "bogota dc":            "SANTAFE DE BOGOTA D.C",
    "bogota d.c":           "SANTAFE DE BOGOTA D.C",
    "bogota d.c.":          "SANTAFE DE BOGOTA D.C",
    "bogota distrito capital": "SANTAFE DE BOGOTA D.C",
    "distrito capital":     "SANTAFE DE BOGOTA D.C",
    "san andres":           "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA",
    "san andres y providencia": "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA",
    "san andres providencia y santa catalina": "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA",
    "guajira":              "LA GUAJIRA",
    "valle":                "VALLE DEL CAUCA",
}


@lru_cache(maxsize=1)
def colombia_region_lookup() -> dict[str, str]:
    """Map normalized department name → canonical GeoJSON name."""
    geojson = _load_colombia_geojson()
    lookup = {
        _normalize_region(f["properties"]["NOMBRE_DPT"]): f["properties"]["NOMBRE_DPT"]
        for f in geojson["features"]
    }
    lookup.update(_COLOMBIA_ALIASES)
    return lookup


def choropleth_colombia(df: pd.DataFrame, region_col: str, value_col: str,
                        height: int = 380) -> go.Figure:
    """Choropleth of Colombian departments shaded by value_col.

    All 33 departments are always rendered; ones without data fall back to a
    light gray base so the full silhouette of Colombia stays visible.
    """
    geojson = _load_colombia_geojson()
    lookup  = colombia_region_lookup()

    # Aggregate user counts per canonical department name
    df = df.copy()
    df["_dept"] = df[region_col].apply(lambda r: lookup.get(_normalize_region(r)))
    agg = (
        df.dropna(subset=["_dept"])
          .groupby("_dept")[value_col].sum()
          .to_dict()
    )

    # Build a row per geojson feature so every department renders
    all_depts = [f["properties"]["NOMBRE_DPT"] for f in geojson["features"]]
    full = pd.DataFrame({
        "_dept": all_depts,
        value_col: [int(agg.get(d, 0)) for d in all_depts],
    })

    max_v = max(int(full[value_col].max()), 1)

    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=full["_dept"],
        z=full[value_col],
        zmin=0,
        zmax=max_v,
        featureidkey=_COLOMBIA_FEATURE_KEY,
        colorscale=[
            [0.0,  COLORS["no_data"]],   # depts with 0 users
            [0.01, COLORS["ramp"][1]],
            [0.25, COLORS["ramp"][2]],
            [0.6,  COLORS["ramp"][3]],
            [1.0,  COLORS["accent"]],
        ],
        marker_line_color="#FFFFFF",
        marker_line_width=0.6,
        showscale=False,
        hovertemplate="<b>%{location}</b><br>%{z} usuarios<extra></extra>",
    ))
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor=COLORS["bg_card"],
    )
    fig.update_layout(
        paper_bgcolor=COLORS["bg_card"],
        plot_bgcolor=COLORS["bg_card"],
        font=dict(family="Figtree, sans-serif", size=11, color=COLORS["text"]),
        hoverlabel=dict(
            bgcolor=COLORS["bg_card"],
            bordercolor=COLORS["border"],
            font=dict(family="Figtree, sans-serif", size=11),
        ),
        height=height,
        margin=dict(l=0, r=0, t=8, b=8),
    )
    return fig

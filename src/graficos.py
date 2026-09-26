"""Estilo visual del equipo y ayudas para construir gráficos Plotly consistentes.

Principios (los mismos del notebook):
- Gris neutro para "el resto" y un color de acento solo en la categoría que importa.
- Nunca doble eje Y: dos medidas de distinta escala van en paneles alineados.
- Barras ordenadas por valor (o por su orden natural: plan, tramo etario, calidad).
- Etiquetas directas en la punta de la barra y tabla "Ver datos" bajo cada gráfico.
"""
from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.kpis import fmt_num

# Paleta del equipo, validada con el validador de accesibilidad (contraste +
# daltonismo, protan/deutan/tritan) del skill de dataviz: pasa las seis
# verificaciones tanto en el par que se usa junto (acento vs. acento_pos) como
# en el trío completo con neutro.
COLOR_NEUTRO = "#B0B7C3"      # el resto de las categorías
COLOR_ACENTO = "#EB6834"      # alerta: peor desempeño
COLOR_ACENTO_POS = "#2A78D6"  # destacar en positivo / serie única
COLOR_LINEA = "#264653"       # líneas de tendencia y referencias
ESCALA_DIVERGENTE = "RdBu_r"  # correlaciones: azul negativo, blanco 0, rojo positivo

_CONFIG_PLOTLY = {
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "scale": 2},  # botón de cámara → PNG para el informe
}


def estilo(fig: go.Figure, titulo: str | None = None, alto: int = 360) -> go.Figure:
    """Aplica el estilo común: título a la izquierda, separadores chilenos, barras delgadas.

    El fondo del gráfico queda fijo en blanco para que se vea como una "tarjeta"
    propia sobre el fondo con tinte de la app (ver .streamlit/config.toml) en vez
    de fundirse con la página.
    """
    fig.update_layout(
        height=alto,
        margin=dict(l=8, r=32, t=64 if titulo else 16, b=8),
        separators=",.",
        bargap=0.45,
        barcornerradius=4,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, title=None),
        hoverlabel=dict(font_size=13),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
    )
    # números en los ejes con separador de miles: 150.000 en vez de 150k
    fig.update_xaxes(tickformat=",~r")
    fig.update_yaxes(tickformat=",~r")
    if titulo:
        fig.update_layout(title=dict(text=titulo, x=0, xanchor="left", font=dict(size=16)))
    return fig


def mostrar(fig: go.Figure) -> None:
    """Dibuja la figura en la página con la configuración común."""
    st.plotly_chart(fig, config=_CONFIG_PLOTLY)


def colores(categorias: Sequence, destacar=None, color_destacado: str = COLOR_ACENTO) -> list[str]:
    """Color de acento para `destacar` (una categoría o lista) y gris neutro para el resto."""
    elegidas = destacar if isinstance(destacar, (list, tuple, set)) else [destacar]
    return [color_destacado if c in elegidas else COLOR_NEUTRO for c in categorias]


def barras(df: pd.DataFrame, categoria: str, valor: str, *, titulo: str, eje_valor: str,
           horizontal: bool = True, destacar=None, color_destacado: str = COLOR_ACENTO,
           decimales: int = 1, sufijo: str = "", hover: dict[str, str] | None = None,
           orden: Sequence | None = None, alto: int | None = None,
           textos: Sequence[str] | None = None) -> go.Figure:
    """Barras de una sola medida con etiqueta en la punta.

    - Sin `destacar`: todas las barras en COLOR_ACENTO_POS (una sola serie).
    - Con `destacar`: esa categoría en `color_destacado` y el resto en gris.
    - `orden`: orden natural de las categorías (si no, se respeta el orden del DataFrame;
      en barras horizontales la primera fila queda abajo, así que ordena ascendente).
    - `hover`: {etiqueta: columna} con texto extra para el tooltip.
    - `textos`: etiquetas propias para la punta de cada barra (por ejemplo, valor y n).
    """
    datos = df.reset_index(drop=True)
    cats = datos[categoria].astype(str)
    if destacar is None:
        color = COLOR_ACENTO_POS
    else:
        color = colores(cats, destacar, color_destacado)
    valores_txt = [f"{fmt_num(v, decimales)}{sufijo}" for v in datos[valor]]
    texto = list(textos) if textos is not None else valores_txt

    extra = ""
    custom = None
    if hover:
        custom = datos[list(hover.values())].astype(str).to_numpy()
        extra = "".join(f"<br>{et}: %{{customdata[{i}]}}" for i, et in enumerate(hover))

    eje_cat, eje_val = ("y", "x") if horizontal else ("x", "y")
    fig = go.Figure(go.Bar(
        **{eje_cat: cats, eje_val: datos[valor]},
        orientation="h" if horizontal else "v",
        marker_color=color,
        text=texto, textposition="outside", cliponaxis=False,
        customdata=custom,
        hovertext=valores_txt,
        hovertemplate=f"<b>%{{{eje_cat}}}</b><br>{eje_valor}: %{{hovertext}}{extra}<extra></extra>",
    ))
    tope = datos[valor].max() if len(datos) else 1
    eje_valor_cfg = dict(title_text=eje_valor, range=[0, tope * 1.18], showgrid=True, zeroline=False)
    eje_cat_cfg = dict(title_text=None, showgrid=False, type="category")
    if orden is not None:
        eje_cat_cfg.update(categoryorder="array", categoryarray=[str(o) for o in orden])
        if horizontal:
            eje_cat_cfg.update(autorange="reversed")
    if horizontal:
        fig.update_xaxes(**eje_valor_cfg)
        fig.update_yaxes(**eje_cat_cfg)
    else:
        fig.update_yaxes(**eje_valor_cfg)
        fig.update_xaxes(**eje_cat_cfg)
    n = len(datos)
    return estilo(fig, titulo, alto or (max(260, 70 + 44 * n) if horizontal else 360))


def paneles_mensuales(serie: pd.DataFrame, paneles: list[dict], titulo: str,
                      alto_panel: int = 190) -> go.Figure:
    """Paneles apilados con el mismo eje X de meses (en vez de un doble eje Y).

    Cada panel: {"columna", "nombre", "tipo": "linea"|"barra", "color", "decimales"}.
    """
    fig = make_subplots(rows=len(paneles), cols=1, shared_xaxes=True, vertical_spacing=0.12,
                        subplot_titles=[p["nombre"] for p in paneles])
    x = serie["mes_nombre"]
    for i, p in enumerate(paneles, start=1):
        dec = p.get("decimales", 0)
        texto = [fmt_num(v, dec) for v in serie[p["columna"]]]
        plantilla = f"<b>%{{x}}</b><br>{p['nombre']}: %{{text}}<extra></extra>"
        if p.get("tipo", "linea") == "barra":
            traza = go.Bar(x=x, y=serie[p["columna"]], marker_color=p["color"], text=texto,
                           textposition="none", hovertemplate=plantilla, name=p["nombre"])
        else:
            traza = go.Scatter(x=x, y=serie[p["columna"]], mode="lines+markers",
                               line=dict(color=p["color"], width=2), marker=dict(size=8),
                               text=texto, hovertemplate=plantilla, name=p["nombre"])
        fig.add_trace(traza, row=i, col=1)
        fig.update_yaxes(rangemode="tozero", showgrid=True, zeroline=False, row=i, col=1)
    fig.update_xaxes(showgrid=False)
    fig.update_layout(showlegend=False)
    fig.update_annotations(x=0, xanchor="left", font_size=13)
    return estilo(fig, titulo, alto=90 + alto_panel * len(paneles))


def ver_tabla(df: pd.DataFrame, etiqueta: str = "Ver datos") -> None:
    """Tabla desplegable bajo el gráfico: el mismo dato, accesible sin el tooltip."""
    numericas = df.select_dtypes("number").columns
    config = {c: st.column_config.NumberColumn(format="localized") for c in numericas}
    with st.expander(etiqueta):
        st.dataframe(df, hide_index=True, column_config=config)


def hallazgo(texto: str) -> None:
    """Hallazgo redactado en el notebook (calculado con todos los datos de 2025)."""
    st.caption(f"**Hallazgo (año completo, sin filtros):** {texto}")

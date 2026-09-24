"""Página 3 · Consumo: reproducciones, minutos, % completado y abandono — Responsable: Hernán.

Sección del notebook: "Reproducciones, minutos vistos, % completado y abandono".
Tablas: reproducciones + contenidos.
"""
import plotly.graph_objects as go
import streamlit as st

from src.datos import sin_datos
from src.graficos import (COLOR_ACENTO, COLOR_ACENTO_POS, COLOR_LINEA, barras, estilo,
                          hallazgo, mostrar, paneles_mensuales, ver_tabla)
from src.kpis import fmt_num, serie_mensual

d = st.session_state["datos"]
rep = d["reproducciones"]

st.title("Consumo")
st.caption("¿Cuánto se ve, qué tan completo y dónde se abandona?")

if sin_datos(rep):
    st.stop()

# ---------------------------------------------------------------- evolución mensual
serie = serie_mensual(d)
mostrar(paneles_mensuales(
    serie,
    paneles=[
        {"columna": "reproducciones", "nombre": "Reproducciones", "color": COLOR_LINEA},
        {"columna": "minutos", "nombre": "Minutos vistos", "color": COLOR_ACENTO_POS},
    ],
    titulo="Reproducciones y minutos vistos por mes",
))
hallazgo("Tras una baja entre febrero y abril, reproducciones y minutos crecen desde mayo y se "
         "aceleran desde septiembre; diciembre es el mes de mayor consumo. Ambas series se "
         "mueven en paralelo.")

# ---------------------------------------------------------------- distribución % completado
st.divider()
media, mediana = rep["porcentaje_completado"].mean(), rep["porcentaje_completado"].median()
fig = go.Figure(go.Histogram(
    x=rep["porcentaje_completado"], nbinsx=30, marker_color=COLOR_ACENTO_POS,
    marker_line=dict(color="white", width=2),
    hovertemplate="%{x}% completado<br>%{y} reproducciones<extra></extra>",
))
# promedio y mediana quedan muy cerca: una etiqueta a cada lado, a distinta altura
for x, color, texto, lado, y in [(media, COLOR_ACENTO, f"Promedio {fmt_num(media, 1)}%", "right", 1.0),
                                 (mediana, COLOR_LINEA, f"Mediana {fmt_num(mediana, 1)}%", "left", 0.9)]:
    fig.add_vline(x=x, line=dict(color=color, width=2))
    fig.add_annotation(x=x, y=y, yref="paper", text=texto, showarrow=False, xanchor=lado,
                       xshift=-6 if lado == "right" else 6, bgcolor="rgba(255,255,255,0.85)")
fig.update_xaxes(title_text="% completado", showgrid=False)
fig.update_yaxes(title_text="N° de reproducciones")
fig.update_layout(bargap=0)
mostrar(estilo(fig, "Distribución del % completado por reproducción"))
aband = rep["abandono_temprano"].eq("Sí")
st.caption(f"Abandono temprano (menos de 20% de avance): {fmt_num(aband.sum())} de "
           f"{fmt_num(len(rep))} reproducciones ({fmt_num(aband.mean() * 100, 2)}%).")
hallazgo("El % completado se concentra entre 55% y 90%. La cola bajo 20% es pequeña (0,4%): "
         "el abandono no es masivo, se concentra en condiciones específicas de dispositivo y "
         "calidad (ver Experiencia técnica).")

# ---------------------------------------------------------------- por tipo de contenido
st.divider()
col_a, col_b = st.columns(2)
with col_a:
    por_tipo = (rep.groupby("tipo_contenido")
                   .agg(pct=("porcentaje_completado", "mean"),
                        minutos=("minutos_reproducidos", "mean"),
                        reproducciones=("reproduccion_id", "count"))
                   .reset_index().sort_values("pct"))
    por_tipo["min_txt"] = por_tipo["minutos"].map(lambda v: fmt_num(v, 1))
    mejor = por_tipo.iloc[-1]["tipo_contenido"]
    mostrar(barras(por_tipo, "tipo_contenido", "pct", horizontal=False,
                   titulo="% completado promedio por tipo de contenido",
                   eje_valor="% completado promedio", sufijo="%", destacar=mejor,
                   color_destacado=COLOR_ACENTO_POS,
                   hover={"Minutos promedio por sesión": "min_txt"}))
    hallazgo("Documentales y series se completan más que las películas; las películas tienen "
             "sesiones más largas pero quedan más veces a medio ver.")
    ver_tabla(por_tipo.rename(columns={"tipo_contenido": "Tipo", "pct": "% completado prom.",
                                       "minutos": "Minutos prom. por sesión",
                                       "reproducciones": "Reproducciones"})
                      [["Tipo", "Reproducciones", "% completado prom.",
                        "Minutos prom. por sesión"]].round(1))

# ---------------------------------------------------------------- top 10
with col_b:
    top = (rep.groupby("titulo")
              .agg(reproducciones=("reproduccion_id", "count"),
                   pct=("porcentaje_completado", "mean"))
              .sort_values("reproducciones", ascending=False).head(10)
              .reset_index().sort_values("reproducciones"))
    top["pct_txt"] = top["pct"].map(lambda v: f"{fmt_num(v, 1)}%")
    mostrar(barras(top, "titulo", "reproducciones", titulo="Top 10 contenidos más reproducidos",
                   eje_valor="Reproducciones", decimales=0,
                   hover={"% completado prom.": "pct_txt"}, alto=420))
    hallazgo("La popularidad no siempre acompaña al % completado: hay títulos muy vistos que "
             "se terminan menos que el promedio. Reportar siempre reproducciones y % completado "
             "juntos.")
    ver_tabla(top.sort_values("reproducciones", ascending=False)
                 .rename(columns={"titulo": "Título", "reproducciones": "Reproducciones",
                                  "pct": "% completado prom."})
                 [["Título", "Reproducciones", "% completado prom."]].round(1))

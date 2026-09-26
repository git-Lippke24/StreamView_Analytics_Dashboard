"""Página 5 · Preferencias de contenido — Responsable: Michelangelo Bandelli.

Sección del notebook: 4.3 "Preferencias de contenido".
Tablas: reproducciones (ya trae género, tipo, idioma, país y segmento de edad),
contenidos (tamaño del catálogo por género) y calificaciones.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.datos import ORDEN_SEGMENTO, sin_datos
from src.graficos import (COLOR_ACENTO_POS, COLOR_CATEGORICO, barras, estilo, hallazgo, mostrar,
                          recomendaciones, ver_tabla)
from src.hallazgos import desviacion_maxima, puntuacion_por_genero
from src.kpis import fmt_num

d = st.session_state["datos"]
rep, cont, cal = d["reproducciones"], d["contenidos"], d["calificaciones"]

st.title("Preferencias de contenido")
st.caption("¿Qué géneros y formatos se consumen, cambian según la edad o el país, y lo más visto es "
           "lo mejor evaluado? · Notebook, sección 4.3.")

if sin_datos(rep):
    st.stop()

# ---------------------------------------------------------------- géneros
st.subheader("Géneros: el consumo sigue al tamaño del catálogo")
generos = (rep.groupby("genero_principal")
              .agg(minutos=("minutos_reproducidos", "sum"), reproducciones=("reproduccion_id", "count"))
              .join(cont.groupby("genero_principal").size().rename("titulos"))
              .reset_index())
generos["min_por_titulo"] = generos["minutos"] / generos["titulos"]
generos["genero"] = generos["genero_principal"] + " (" + generos["titulos"].astype(str) + " títulos)"

medida = st.segmented_control("Medir por", ["Minutos totales", "Minutos por título"],
                              default="Minutos totales") or "Minutos totales"
columna = "minutos" if medida == "Minutos totales" else "min_por_titulo"
generos = generos.sort_values(columna)
generos["min_txt"] = generos["minutos"].map(fmt_num)
generos["mpt_txt"] = generos["min_por_titulo"].map(fmt_num)
mostrar(barras(generos, "genero", columna, titulo=f"{medida} por género",
               eje_valor=medida, decimales=0, destacar=generos.iloc[-1]["genero"],
               color_destacado=COLOR_ACENTO_POS,
               hover={"Minutos totales": "min_txt", "Minutos por título": "mpt_txt"}))
st.caption("Entre paréntesis, los títulos de cada género en el catálogo: más títulos suman más minutos. "
           "Cambia a \"Minutos por título\" para comparar el rendimiento de cada título.")
hallazgo("Drama lidera en minutos (18,3% del total, 26% más que Comedia), pero también es el género con "
         "más títulos (70 de 420): los minutos de cada género siguen casi exactamente al tamaño de su "
         "catálogo (r = 0,98). Por título, los cinco primeros están entre 3.609 y 3.858 minutos, y "
         "Animación (2.736) y Documental (2.238) quedan al final. Drama lidera porque hay más Drama, "
         "no porque cada título rinda más.")
ver_tabla(generos.sort_values("minutos", ascending=False)
                 .rename(columns={"genero_principal": "Género", "titulos": "Títulos",
                                  "reproducciones": "Reproducciones", "minutos": "Minutos totales",
                                  "min_por_titulo": "Minutos por título"})
                 [["Género", "Títulos", "Reproducciones", "Minutos totales", "Minutos por título"]]
                 .round(0))

# ---------------------------------------------------------------- formato por edad o país
st.divider()
st.subheader("Formato por segmento: las preferencias son parejas")
GRUPOS = {"Segmento de edad": "segmento_edad", "País": "pais"}
grupo_nombre = st.segmented_control("Comparar por", list(GRUPOS), default="Segmento de edad") \
    or "Segmento de edad"
grupo = GRUPOS[grupo_nombre]

mezcla = pd.crosstab(rep[grupo], rep["tipo_contenido"], normalize="index") * 100
tipos = [t for t in ["Película", "Serie", "Documental"] if t in mezcla.columns]
orden_grupos = ([s for s in ORDEN_SEGMENTO if s in mezcla.index] if grupo == "segmento_edad"
                else sorted(mezcla.index))
mezcla = mezcla.reindex(orden_grupos)[tipos]
n_grupo = rep[grupo].value_counts()
etiquetas = [f"{g} (n={fmt_num(n_grupo[g])})" for g in mezcla.index]

fig = go.Figure()
for tipo, color in zip(tipos, COLOR_CATEGORICO):
    fig.add_trace(go.Bar(
        y=etiquetas, x=mezcla[tipo], name=tipo, orientation="h", marker_color=color,
        marker_line=dict(color="white", width=1.5),
        text=[f"{fmt_num(v)}%" for v in mezcla[tipo]], textposition="inside", insidetextanchor="middle",
        hovertemplate=f"<b>%{{y}}</b><br>{tipo}: %{{x:.1f}}%<extra></extra>",
    ))
fig.update_layout(barmode="stack", bargap=0.3)
fig.update_xaxes(range=[0, 100], ticksuffix="%", title_text="% de las reproducciones del grupo",
                 showgrid=False)
fig.update_yaxes(autorange="reversed", type="category")
mostrar(estilo(fig, f"Mezcla de formatos por {grupo_nombre.lower()}", alto=max(280, 90 + 44 * len(mezcla))))

chequeo = pd.DataFrame([
    {"Grupo": g_nombre, "Variable": v_nombre,
     "Máxima diferencia con el total (puntos)": desviacion_maxima(rep, g_col, v_col)}
    for g_nombre, g_col in GRUPOS.items()
    for v_nombre, v_col in [("Tipo de contenido", "tipo_contenido"), ("Género", "genero_principal"),
                            ("Idioma original", "idioma_original")]
])
st.caption(f"Con los filtros actuales, ninguna proporción de formato, género o idioma se aleja más de "
           f"{fmt_num(chequeo.iloc[:, 2].max(), 1)} puntos del total, ni por edad ni por país.")
hallazgo("La mezcla de formatos es prácticamente la misma en todos los segmentos: Película 45–47%, "
         "Serie 39–42% y Documental 13–14%; ninguna proporción se aleja más de 1,3 puntos del total. "
         "Lo mismo pasa con el género y el idioma, y también por país (máximo 2,1 puntos). Personalizar "
         "la portada por edad o por país no está respaldado por los datos.")
ver_tabla(chequeo.round(1), etiqueta="Ver la diferencia máxima por grupo y variable")
ver_tabla(mezcla.round(1).reset_index(names=grupo_nombre))

# ---------------------------------------------------------------- calificación por género
st.divider()
st.subheader("Calificación por género: lo mejor evaluado es lo menos visto")
if not sin_datos(cal):
    por_genero = puntuacion_por_genero(rep, cal)
    mejores = por_genero.nlargest(2, "puntuacion")["genero_principal"].tolist()
    por_genero["n_txt"] = por_genero["calificaciones"].map(fmt_num)
    fig = barras(por_genero, "genero_principal", "puntuacion", titulo="Puntuación promedio por género",
                 eje_valor="Puntuación promedio (1 a 5)", decimales=2, destacar=mejores,
                 color_destacado=COLOR_ACENTO_POS, hover={"Calificaciones": "n_txt"},
                 textos=[f"{fmt_num(p, 2)} · {fmt_num(r)} reproducciones"
                         for p, r in zip(por_genero["puntuacion"], por_genero["reproducciones"])])
    fig.update_xaxes(range=[0, 6.3], tickvals=[0, 1, 2, 3, 4, 5])
    mostrar(fig)
    hallazgo("Documental (4,27) y Animación (4,14) son los géneros mejor calificados, pero también los "
             "dos con menos reproducciones. Comedia es el 2.º género más visto y el peor calificado "
             "(3,80); Drama combina ambas cosas: 1.º en reproducciones y 3.º en puntuación (4,11). Las "
             "diferencias son moderadas (de 3,80 a 4,27). Aquí \"Documental\" es el género, distinto "
             "del tipo de contenido Documental del gráfico anterior.")
    ver_tabla(por_genero.sort_values("puntuacion", ascending=False)
                        .rename(columns={"genero_principal": "Género", "puntuacion": "Puntuación prom.",
                                         "calificaciones": "Calificaciones",
                                         "reproducciones": "Reproducciones"})
                        [["Género", "Puntuación prom.", "Calificaciones", "Reproducciones"]].round(2))

recomendaciones([
    "Evaluar géneros y compras de catálogo por **rendimiento por título** (minutos y % completado "
    "por título), no por el total del género.",
    "Dar más exposición en portada a **Documental y Animación** y medir si suben sus reproducciones "
    "sin que baje la puntuación.",
    "No segmentar la portada por edad ni por país: **personalizar según el historial** de cada usuario.",
])

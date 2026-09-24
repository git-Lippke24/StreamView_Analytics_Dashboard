"""Página 5 · Preferencias de contenido — Responsable: por asignar.

Sección del notebook: "Preferencias de contenido" (pendiente).
Pregunta del README: preferencias por género, tipo, idioma, país y segmento.
Tablas: reproducciones (ya trae genero_principal, tipo_contenido, idioma_original,
exclusivo, pais y segmento_edad) + contenidos.
"""
import streamlit as st

from src.datos import sin_datos
from src.graficos import barras, mostrar, ver_tabla
from src.kpis import fmt_num

d = st.session_state["datos"]
rep = d["reproducciones"]

st.title("Preferencias de contenido")
st.caption("¿Qué géneros, formatos e idiomas prefiere cada país y segmento?")

st.info(
    "**Pendiente: esta página se completa con la sección \"Preferencias de contenido\" del "
    "notebook.** El gráfico de abajo es solo un ejemplo para partir: reemplázalo por los "
    "hallazgos del análisis (por ejemplo, género más visto por país o por segmento de edad, "
    "contenido exclusivo vs. no exclusivo, idioma original).",
    icon=":material/construction:",
)

if sin_datos(rep):
    st.stop()

# ---------------------------------------------------------------- ejemplo inicial
por_genero = (rep.groupby("genero_principal")
                 .agg(reproducciones=("reproduccion_id", "count"),
                      pct=("porcentaje_completado", "mean"))
                 .reset_index().sort_values("reproducciones"))
por_genero["pct_txt"] = por_genero["pct"].map(lambda v: f"{fmt_num(v, 1)}%")
mostrar(barras(por_genero, "genero_principal", "reproducciones",
               titulo="Ejemplo: reproducciones por género principal", eje_valor="Reproducciones",
               decimales=0, hover={"% completado prom.": "pct_txt"}))
ver_tabla(por_genero.sort_values("reproducciones", ascending=False)
                    .rename(columns={"genero_principal": "Género", "reproducciones": "Reproducciones",
                                     "pct": "% completado prom."})
                    [["Género", "Reproducciones", "% completado prom."]].round(1))

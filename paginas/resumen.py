"""Página 1 · Resumen ejecutivo — Responsable: grupal.

KPIs de cabecera y evolución mensual de consumo y cancelaciones.
"""
import streamlit as st

from src.datos import sin_datos
from src.graficos import COLOR_ACENTO, COLOR_LINEA, mostrar, paneles_mensuales, ver_tabla
from src.kpis import fmt_num, fmt_pct, kpis_generales, serie_mensual

d = st.session_state["datos"]

st.title("StreamView Analytics · Resumen 2025")
st.caption("¿Qué combinación de contenido, dispositivo y experiencia de uso mantiene a un "
           "usuario reproduciendo, interactuando y suscrito?")

if sin_datos(d["reproducciones"]):
    st.stop()

k = kpis_generales(d)

st.subheader("Suscripciones")
c1, c2, c3 = st.columns(3)
c1.metric("Suscripciones activas", fmt_num(k["activas"]),
          help=f"De {fmt_num(k['usuarios'])} usuarios en el filtro. Estado al 31-12-2025.")
c2.metric("Tasa de cancelación", fmt_pct(k["tasa_cancelacion"]),
          help="Suscripciones canceladas / total de suscripciones (estado al 31-12-2025).")
c3.metric("Ingreso mensual de referencia", f"USD {fmt_num(k['ingreso_mensual'])}",
          help="Suma de precio_mensual_usd de las suscripciones activas.")

st.subheader("Consumo y satisfacción")
c4, c5, c6, c7 = st.columns(4)
c4.metric("Minutos vistos", fmt_num(k["minutos"]),
          help=f"{fmt_num(k['reproducciones'])} reproducciones en el período.")
c5.metric("% completado promedio", fmt_pct(k["pct_completado"] / 100))
c6.metric("Abandono temprano", fmt_pct(k["tasa_abandono"], 2),
          help="Reproducciones con menos de 20% de avance / total de reproducciones.")
c7.metric("Puntuación promedio", f"{fmt_num(k['puntuacion'], 2)} / 5",
          help=f"Recomendaría: {fmt_pct(k['tasa_recomienda'])} de las calificaciones.")

serie = serie_mensual(d)
fig = paneles_mensuales(
    serie,
    paneles=[
        {"columna": "minutos", "nombre": "Minutos vistos", "tipo": "linea", "color": COLOR_LINEA},
        {"columna": "cancelaciones", "nombre": "Suscripciones canceladas",
         "tipo": "barra", "color": COLOR_ACENTO},
    ],
    titulo="Consumo y cancelaciones por mes",
)
mostrar(fig)
st.caption("Dos paneles con el mismo eje de meses en lugar de un doble eje Y: "
           "cada medida conserva su propia escala sin inventar una correlación visual.")
ver_tabla(serie.rename(columns={
    "mes_nombre": "Mes", "reproducciones": "Reproducciones", "minutos": "Minutos vistos",
    "usuarios_activos": "Usuarios que reprodujeron", "cancelaciones": "Cancelaciones",
})[["Mes", "Reproducciones", "Minutos vistos", "Usuarios que reprodujeron", "Cancelaciones"]])

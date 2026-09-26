"""Página 1 · Resumen ejecutivo — Responsable: grupal.

KPIs de cabecera (responden a los filtros), evolución mensual de consumo y
cancelaciones, y un hallazgo clave por línea de análisis del notebook (año completo).
"""
import streamlit as st

from src.datos import sin_datos
from src.graficos import COLOR_ACENTO, COLOR_LINEA, mostrar, paneles_mensuales, ver_tabla
from src.hallazgos import hallazgos_clave
from src.kpis import UMBRAL_BUFFERING, fmt_num, fmt_pct, kpis_generales, serie_mensual

d = st.session_state["datos"]

st.title("Más minutos que nunca, pero más cancelaciones")
st.caption("Resumen 2025 · ¿Qué combinación de contenido, dispositivo y experiencia de uso mantiene "
           "a un usuario reproduciendo, interactuando y suscrito?")

if sin_datos(d["reproducciones"]):
    st.stop()

k = kpis_generales(d)

# ---------------------------------------------------------------- KPIs (con filtros)
st.subheader("Negocio")
c1, c2, c3, c4 = st.columns(4)
with c1.container(border=True):
    st.metric("Suscripciones activas", fmt_num(k["activas"]),
              help=f"De {fmt_num(k['usuarios'])} usuarios en el filtro. Estado al 31-12-2025.")
with c2.container(border=True):
    st.metric("Tasa de cancelación", fmt_pct(k["tasa_cancelacion"]),
              help="Suscripciones canceladas / total de suscripciones (estado al 31-12-2025).")
with c3.container(border=True):
    st.metric("Ingreso mensual de referencia", f"USD {fmt_num(k['ingreso_mensual'])}",
              help="Suma de precio_mensual_usd de las suscripciones activas.")
with c4.container(border=True):
    pct_perdido = k["ingreso_perdido"] / k["ingreso_potencial"] if k["ingreso_potencial"] else 0
    st.metric("Ingreso mensual perdido", f"USD {fmt_num(k['ingreso_perdido'])}",
              help=f"Precio mensual de las suscripciones canceladas: {fmt_pct(pct_perdido)} del "
                   f"ingreso potencial (activas + canceladas).")

st.subheader("Uso, experiencia y satisfacción")
c5, c6, c7, c8 = st.columns(4)
with c5.container(border=True):
    st.metric("Minutos vistos", fmt_num(k["minutos"]),
              help=f"{fmt_num(k['reproducciones'])} reproducciones en el período.")
with c6.container(border=True):
    st.metric("% completado promedio", fmt_pct(k["pct_completado"] / 100),
              help=f"Abandono temprano (menos de 20% de avance): {fmt_pct(k['tasa_abandono'], 2)} "
                   f"de las reproducciones.")
with c7.container(border=True):
    st.metric(f"Sesiones con buffering alto (>{UMBRAL_BUFFERING} s)", fmt_pct(k["pct_buffering_alto"]),
              help=f"Reproducciones con más de {UMBRAL_BUFFERING} s de buffering: sobre ese umbral "
                   "el abandono temprano se multiplica (ver Experiencia técnica).")
with c8.container(border=True):
    st.metric("Puntuación promedio", f"{fmt_num(k['puntuacion'], 2)} / 5",
              help=f"Recomendaría: {fmt_pct(k['tasa_recomienda'])} de las calificaciones.")

# ---------------------------------------------------------------- evolución mensual
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

# ---------------------------------------------------------------- hallazgos clave (año completo)
st.divider()
st.subheader("Hallazgos clave del año")
st.caption("Un hallazgo por línea de análisis, con todos los datos de 2025 (no cambian con los "
           "filtros). El detalle está en cada página y en el notebook, sección 4.")

h = hallazgos_clave()
g1, g2 = h["mejor_calificados"]
TARJETAS = [
    ("4.1 Retención", fmt_pct(h["tasa_basico"] / 100),
     f"**El plan Básico concentra la fuga:** casi 1 de cada 2 suscriptores Básico cancela, y el "
     f"plan aporta el {fmt_num(h['basico_pct_cancelaciones'])}% de todas las cancelaciones "
     f"(Premium cancela {fmt_num(h['tasa_premium'], 1)}%).",
     "paginas/retencion.py", "Retención"),
    ("4.2 Consumo", f"{fmt_num(h['movil_pct_abandonos'])}%",
     f"**El abandono se concentra en móvil:** con el {fmt_num(h['movil_pct_reproducciones'])}% de "
     f"las reproducciones, acumula el {fmt_num(h['movil_pct_abandonos'])}% de los abandonos "
     f"tempranos y tiene el menor % completado ({fmt_num(h['movil_pct_completado'], 1)}%).",
     "paginas/consumo.py", "Consumo"),
    ("4.3 Preferencias", f"≤ {fmt_num(h['pref_desviacion_max'], 1)} pts",
     f"**Los gustos son parejos por edad y país:** la mezcla de géneros, formatos e idiomas no se "
     f"aleja más de {fmt_num(h['pref_desviacion_max'], 1)} puntos del total. "
     f"{g1['genero_principal']} ({fmt_num(g1['puntuacion'], 2)}) y {g2['genero_principal']} "
     f"({fmt_num(g2['puntuacion'], 2)}) son los géneros mejor calificados, pero están en los puestos "
     f"{g1['puesto_reproducciones']} y {g2['puesto_reproducciones']} de {h['n_generos']} en "
     f"reproducciones.",
     "paginas/preferencias.py", "Preferencias"),
    ("4.4 Experiencia técnica", f"{fmt_num(h['android_pct_abandonos'])}%",
     f"**Android con app 6.8–6.9:** con solo el {fmt_num(h['android_pct_reproducciones'], 1)}% de "
     f"las reproducciones ({fmt_num(h['android_dispositivos'])} dispositivos) genera el "
     f"{fmt_num(h['android_pct_abandonos'])}% de los abandonos tempranos. La versión 7.0 ya "
     f"corrige el problema: falta que esos usuarios actualicen.",
     "paginas/experiencia.py", "Experiencia técnica"),
    ("4.5 Satisfacción", f"+{fmt_num(h['completado_nota5'] - h['completado_nota3'], 1)} pts",
     f"**Quien termina un contenido lo califica mejor:** el % completado sube de "
     f"{fmt_num(h['completado_nota3'], 1)}% con nota 3 a {fmt_num(h['completado_nota5'], 1)}% con "
     f"nota 5. Es un termómetro de satisfacción disponible en cada reproducción.",
     "paginas/satisfaccion.py", "Satisfacción"),
]
for linea, valor, texto, pagina, nombre in TARJETAS:
    with st.container(border=True):
        c_valor, c_texto, c_link = st.columns([1.3, 5, 1.3], vertical_alignment="center")
        c_valor.metric(linea, valor)
        c_texto.markdown(texto)
        c_link.page_link(pagina, label=f"Ver {nombre}", icon=":material/arrow_forward:")

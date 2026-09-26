"""StreamView Analytics · Dashboard EP1 (ADY1104 Visualización de Datos).

Punto de entrada: carga los datos, dibuja los filtros globales en la barra lateral
y define la navegación. Este archivo corre en cada página, por eso los filtros
se comparten entre todas.

Ejecutar:  streamlit run app.py
"""
import streamlit as st

from src.datos import MESES, ORDEN_PLAN, ORDEN_SEGMENTO, cargar_datos, filtrar

st.set_page_config(page_title="StreamView Analytics 2025", page_icon=":material/live_tv:",
                   layout="wide")

datos = cargar_datos()
usuarios = datos["usuarios"]

# ---------------------------------------------------------------- filtros globales
with st.sidebar:
    st.header("Filtros")
    mes_desde, mes_hasta = st.select_slider("Meses de 2025", options=MESES,
                                            value=(MESES[0], MESES[-1]))
    paises_todos = sorted(usuarios["pais"].unique())
    paises = st.multiselect("País", paises_todos, default=paises_todos)
    planes = st.multiselect("Plan", ORDEN_PLAN, default=ORDEN_PLAN)
    segmentos = st.multiselect("Segmento de edad", ORDEN_SEGMENTO, default=ORDEN_SEGMENTO)
    st.caption("El estado de las suscripciones es al 31-12-2025: el filtro de meses "
               "no cambia la tasa de cancelación. La página Historia usa siempre el año completo.")

# ---------------------------------------------------------------- navegación
# Para agregar una página: crea el archivo en paginas/ y súmalo a esta lista.
paginas = {
    "Dashboard": [
        st.Page("paginas/resumen.py", title="Resumen ejecutivo", icon=":material/dashboard:",
                default=True),
        st.Page("paginas/retencion.py", title="Retención", icon=":material/group_remove:"),
        st.Page("paginas/consumo.py", title="Consumo", icon=":material/play_circle:"),
        st.Page("paginas/preferencias.py", title="Preferencias", icon=":material/movie:"),
        st.Page("paginas/experiencia.py", title="Experiencia técnica", icon=":material/devices:"),
        st.Page("paginas/satisfaccion.py", title="Satisfacción", icon=":material/star:"),
    ],
    "Storytelling": [
        st.Page("paginas/historia.py", title="Historia y recomendaciones",
                icon=":material/auto_stories:"),
    ],
}
pagina = st.navigation(paginas)

# ---------------------------------------------------------------- datos filtrados
if paises and planes and segmentos:
    st.session_state["datos"] = filtrar(
        datos,
        meses=(MESES.index(mes_desde) + 1, MESES.index(mes_hasta) + 1),
        paises=paises, planes=planes, segmentos=segmentos,
    )
elif pagina.url_path != "historia":  # Historia usa siempre el año completo
    st.warning("Selecciona al menos un país, un plan y un segmento de edad en la barra lateral.")
    st.stop()

pagina.run()

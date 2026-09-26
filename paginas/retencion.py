"""Página 2 · Retención y cancelación — Responsable: Sebastián.

Sección del notebook: 4.1 "Retención y cancelación de clientes".
Tablas: usuarios + suscripciones (una suscripción por usuario).
"""
import plotly.graph_objects as go
import streamlit as st

from src.datos import ORDEN_PLAN, ORDEN_SEGMENTO, sin_datos
from src.graficos import (COLOR_ACENTO, COLOR_NEUTRO, barras, estilo, hallazgo, mostrar,
                          recomendaciones, ver_tabla)
from src.kpis import fmt_num, fmt_pct, kpis_generales, serie_mensual, tasa_cancelacion_por

d = st.session_state["datos"]
usuarios = d["usuarios"]

st.title("Retención y cancelación")
st.caption("¿Quién cancela su suscripción y por qué? Estado de las suscripciones al 31-12-2025. "
           "· Notebook, sección 4.1.")

if sin_datos(usuarios):
    st.stop()

k = kpis_generales(d)
c1, c2, c3, c4 = st.columns(4)
with c1.container(border=True):
    st.metric("Usuarios", fmt_num(k["usuarios"]))
with c2.container(border=True):
    st.metric("Activas", fmt_num(k["activas"]))
with c3.container(border=True):
    st.metric("Canceladas", fmt_num(k["canceladas"]))
with c4.container(border=True):
    st.metric("Tasa de cancelación", fmt_pct(k["tasa_cancelacion"]))

# ---------------------------------------------------------------- tasa por dimensión
DIMENSIONES = {
    "Plan": ("plan", ORDEN_PLAN),
    "País": ("pais", None),
    "Segmento de edad": ("segmento_edad", ORDEN_SEGMENTO),
    "Canal de adquisición": ("canal_adquisicion", None),
}
HALLAZGOS = {  # redactados en el notebook con todos los datos (notebook, sección 4.1.1)
    "Plan": "Básico concentra la fuga: 44,1% cancela, casi 1 de cada 2. Estándar cancela 20,7% y "
            "Premium solo 12,0% (88% retiene).",
    "País": "Tasas de cancelación entre 24,5% (Chile) y 35,8% (Ecuador, muestra chica, n=67). "
            "Argentina y Chile retienen mejor (~75% activa).",
    "Segmento de edad": "45-54 cancela menos (21,2%, 79% activa). Los extremos cancelan más: "
                        "18-24 (33,4%, 67% activa) y 55+ (32,3%, 68% activa, muestra chica, n=65).",
    "Canal de adquisición": "Referido cancela menos (22,0%): llegan precalificados. Publicidad "
                            "digital cancela más (30,8%).",
}

dimension = st.segmented_control("Ver la tasa de cancelación por", list(DIMENSIONES),
                                 default="Plan") or "Plan"
columna, orden = DIMENSIONES[dimension]
tabla = tasa_cancelacion_por(usuarios, columna)
if orden is None:
    tabla = tabla.sort_values("tasa")  # horizontal: la mayor queda arriba
# Con filtros extremos todas las tasas pueden ser 0: en ese caso no se destaca ninguna
peor = tabla.loc[tabla["tasa"].idxmax(), columna] if tabla["tasa"].max() > 0 else None
tabla["n_txt"] = tabla["usuarios"].map(fmt_num)
tabla["c_txt"] = tabla["canceladas"].map(fmt_num)

fig = barras(tabla, columna, "tasa", titulo=f"Tasa de cancelación por {dimension.lower()}",
             eje_valor="% de suscripciones canceladas", sufijo="%", destacar=peor,
             orden=[o for o in (orden or []) if o in set(tabla[columna])] or None,
             hover={"Usuarios": "n_txt", "Canceladas": "c_txt"})
mostrar(fig)
hallazgo(HALLAZGOS[dimension])
ver_tabla(tabla.rename(columns={columna: dimension, "usuarios": "Usuarios",
                                "canceladas": "Canceladas", "tasa": "Tasa de cancelación (%)"})
               [[dimension, "Usuarios", "Canceladas", "Tasa de cancelación (%)"]].round(1))

# ---------------------------------------------------------------- motivos
st.divider()
canceladas = usuarios[usuarios["estado"] == "Cancelada"]
if not sin_datos(canceladas):
    motivos = (canceladas["motivo_cancelacion"].value_counts().rename_axis("motivo")
               .reset_index(name="cancelaciones").sort_values("cancelaciones"))
    motivos["pct"] = motivos["cancelaciones"] / motivos["cancelaciones"].sum() * 100
    motivos["pct_txt"] = motivos["pct"].map(lambda v: f"{fmt_num(v, 1)}%")
    principal = motivos.iloc[-1]
    fig = barras(motivos, "motivo", "cancelaciones", titulo="Motivos de cancelación",
                 eje_valor="Cancelaciones", decimales=0, destacar=principal["motivo"],
                 hover={"% de las cancelaciones": "pct_txt"})
    mostrar(fig)
    st.caption(f"\"{principal['motivo']}\" explica el {fmt_num(principal['pct'], 0)}% de las "
               f"cancelaciones del filtro actual. Para ver los motivos de un plan, fíltralo en la "
               f"barra lateral.")
    hallazgo("\"Poco uso\" es el motivo más declarado (32,3% de las cancelaciones), seguido de "
             "\"Precio\" (21,9%) y \"Cambio a otra plataforma\" (16,6%). \"Poco uso\" encabeza en los "
             "tres planes; lo que cambia es el segundo motivo: \"Precio\" en Básico (20,0%) y Estándar "
             "(25,2%), y en Premium empatan \"Precio\" y \"Contenido insuficiente\" (22,9% cada uno, "
             "con solo 35 cancelaciones). El motivo declarado no prueba la causa: quienes cancelan "
             "estuvieron activos 5,8 meses en promedio en 2025, contra 10,2 de quienes siguen.")
    ver_tabla(motivos.rename(columns={"motivo": "Motivo", "cancelaciones": "Cancelaciones",
                                      "pct": "% del total"})
                     [["Motivo", "Cancelaciones", "% del total"]].round(1))

# ---------------------------------------------------------------- cancelaciones por mes
st.divider()
serie = serie_mensual(d)
fig = go.Figure(go.Bar(
    x=serie["mes_nombre"], y=serie["cancelaciones"],
    marker_color=[COLOR_NEUTRO if m <= 6 else COLOR_ACENTO for m in serie["mes"]],
    text=serie["cancelaciones"].map(fmt_num), textposition="outside", cliponaxis=False,
    hovertemplate="<b>%{x}</b><br>Cancelaciones: %{text}<extra></extra>",
))
fig.update_yaxes(title_text="Suscripciones canceladas",
                 range=[0, max(serie["cancelaciones"].max(), 1) * 1.2])
fig.update_xaxes(showgrid=False)
mostrar(estilo(fig, "Suscripciones canceladas por mes (2° semestre destacado)"))
hallazgo("Las cancelaciones crecen fuerte durante el año: de 15 en enero a 68 en diciembre, y el "
         "67,2% ocurre en el segundo semestre, justo cuando más crece el consumo: más actividad no se "
         "tradujo en más retención.")

recomendaciones([
    "Priorizar **campañas de reactivación y beneficios de upgrade para el plan Básico**, antes del "
    "2.º semestre (cuando se acelera la fuga), midiendo su efecto en la tasa de cancelación mensual "
    "como KPI de seguimiento.",
])

"""Página 2 · Retención y cancelación — Responsable: Sebastián.

Sección del notebook: "Retención y cancelación de clientes".
Tablas: usuarios + suscripciones (una suscripción por usuario).
"""
import streamlit as st

from src.datos import ORDEN_PLAN, ORDEN_SEGMENTO, sin_datos
from src.graficos import barras, hallazgo, mostrar, ver_tabla
from src.kpis import fmt_num, fmt_pct, kpis_generales, tasa_cancelacion_por

d = st.session_state["datos"]
usuarios = d["usuarios"]

st.title("Retención y cancelación")
st.caption("¿Quién cancela su suscripción y por qué? Estado de las suscripciones al 31-12-2025.")

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
HALLAZGOS = {  # redactados en el notebook con todos los datos (ver notebook, sección Retención)
    "Plan": "Básico concentra la fuga: 44% cancela, casi 1 de cada 2. Estándar cancela 21% y "
            "Premium solo 12% (88% retiene).",
    "País": "Tasas de cancelación entre 24% (Chile) y 36% (Ecuador, muestra chica, n=67). "
            "Argentina y Chile retienen mejor (~75% activa).",
    "Segmento de edad": "45-54 cancela menos (21%, 79% activa). Los extremos cancelan más: "
                        "18-24 (33%, 67% activa) y 55+ (32%, 68% activa, muestra chica, n=65).",
    "Canal de adquisición": "Referido cancela menos (22%): llegan precalificados. Publicidad "
                            "digital cancela más (31%).",
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
               f"cancelaciones del filtro actual.")
    ver_tabla(motivos.rename(columns={"motivo": "Motivo", "cancelaciones": "Cancelaciones",
                                      "pct": "% del total"})
                     [["Motivo", "Cancelaciones", "% del total"]].round(1))

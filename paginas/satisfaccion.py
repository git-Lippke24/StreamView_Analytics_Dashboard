"""Página 6 · Consumo, interacciones y calificaciones — Responsable: Hernán.

Sección del notebook: 4.5 "Relación entre consumo, interacciones y calificaciones".
Tablas: reproducciones, interacciones, calificaciones.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.datos import sin_datos
from src.graficos import (COLOR_ACENTO_POS, COLOR_LINEA, COLOR_NEUTRO, ESCALA_DIVERGENTE,
                          barras, estilo, hallazgo, mostrar, recomendaciones, ver_tabla)
from src.kpis import fmt_num

d = st.session_state["datos"]
rep, inter, cal = d["reproducciones"], d["interacciones"], d["calificaciones"]

st.title("Satisfacción")
st.caption("¿Ver más significa estar más satisfecho? Consumo, interacciones y calificaciones. "
           "· Notebook, sección 4.5.")

if sin_datos(rep) or sin_datos(cal):
    st.stop()

# Cada calificación cruzada con el % completado que ese usuario tuvo en ese contenido
rep_par = (rep.groupby(["usuario_id", "contenido_id"])["porcentaje_completado"].mean()
              .reset_index())
cal_par = cal.merge(rep_par, on=["usuario_id", "contenido_id"], how="inner")

# ---------------------------------------------------------------- completado vs puntuación
if not sin_datos(cal_par):
    por_punt = (cal_par.groupby("puntuacion_1_5")
                       .agg(pct=("porcentaje_completado", "mean"),
                            calificaciones=("calificacion_id", "count"))
                       .reset_index())
    por_punt["puntuacion"] = por_punt["puntuacion_1_5"].astype(str)
    por_punt["n_txt"] = por_punt["calificaciones"].map(fmt_num)
    corr_par = cal_par["puntuacion_1_5"].corr(cal_par["porcentaje_completado"])
    # El n va visible en cada barra: la nota 2 tiene muy pocos casos
    etiquetas = [f"{fmt_num(p, 1)}% · n={n}" for p, n in zip(por_punt["pct"], por_punt["n_txt"])]
    mostrar(barras(por_punt, "puntuacion", "pct", horizontal=False,
                   titulo="% completado del mismo contenido según la puntuación otorgada",
                   eje_valor="% completado promedio", sufijo="%",
                   destacar=por_punt["puntuacion"].iloc[-1], color_destacado=COLOR_ACENTO_POS,
                   hover={"Calificaciones": "n_txt"}, textos=etiquetas))
    st.caption(f"{fmt_num(len(cal_par))} calificaciones cruzadas con su reproducción · "
               f"correlación puntuación–% completado: {fmt_num(corr_par, 2)}.")
    hallazgo("La relación más clara de la sección: el % completado sube con la puntuación, de "
             "64,7% con nota 3 (504 calificaciones) a 78,8% con nota 5 (396). La nota 2 tiene "
             "solo 3 casos y no se usa para concluir. La correlación es débil (0,20), pero el "
             "patrón es monotónico: terminar un contenido es un buen termómetro de satisfacción.")

# ---------------------------------------------------------------- correlaciones
st.divider()
ETIQUETAS = {
    "n_reproducciones": "N° reproducciones", "minutos_totales": "Minutos totales",
    "pct_completado_prom": "% completado prom.", "n_interacciones": "N° interacciones",
    "n_me_gusta": "N° \"me gusta\"", "n_calificaciones": "N° calificaciones",
    "puntuacion_prom": "Puntuación prom.", "tasa_recomendaria": "Tasa \"recomendaría\"",
}
nivel = st.segmented_control("Nivel de agregación", ["Usuario", "Contenido"],
                             default="Usuario") or "Usuario"
clave = "usuario_id" if nivel == "Usuario" else "contenido_id"

base = rep.groupby(clave).agg(n_reproducciones=("reproduccion_id", "count"),
                              minutos_totales=("minutos_reproducidos", "sum"),
                              pct_completado_prom=("porcentaje_completado", "mean"))
base = base.join(inter.groupby(clave).size().rename("n_interacciones"))
base = base.join(cal.groupby(clave).agg(n_calificaciones=("calificacion_id", "count"),
                                        puntuacion_prom=("puntuacion_1_5", "mean")))
if nivel == "Usuario":
    base = base.join(inter[inter["tipo_interaccion"] == "Me gusta"].groupby(clave).size()
                     .rename("n_me_gusta"))
    base = base.join(cal.groupby(clave)["recomendaria"].apply(lambda s: s.eq("Sí").mean())
                     .rename("tasa_recomendaria"))
# Conteos sin registros = 0. Los PROMEDIOS de quien nunca calificó quedan vacíos: rellenarlos
# con 0 inventa una correlación falsa entre "N° calificaciones" y "Puntuación prom.".
conteos = [c for c in base.columns if c.startswith("n_")]
base[conteos] = base[conteos].fillna(0)

corr = base.corr().rename(index=ETIQUETAS, columns=ETIQUETAS)
fig = go.Figure(go.Heatmap(
    z=corr.values, x=corr.columns, y=corr.index, colorscale=ESCALA_DIVERGENTE,
    zmin=-1, zmax=1, zmid=0, texttemplate="%{z:.2f}", xgap=2, ygap=2,
    hovertemplate="%{y} vs. %{x}<br>Correlación: %{z:.2f}<extra></extra>",
    colorbar=dict(title="r", thickness=12),
))
fig.update_yaxes(autorange="reversed")
fig.update_xaxes(tickangle=-40)
mostrar(estilo(fig, f"Correlaciones a nivel {nivel.lower()}", alto=560))
if nivel == "Usuario":
    hallazgo("Cuánto ve un usuario casi no se relaciona con cuánto interactúa (≈0,00) ni con "
             "cómo califica (≈0,06): ver mucho no implica estar más satisfecho. Tampoco "
             "califican más alto quienes califican más seguido (≈−0,02).")
else:
    hallazgo("Más reproducciones traen más interacciones (0,77), pero la relación con la "
             "puntuación es débil y negativa (−0,18): los contenidos más vistos no son "
             "necesariamente los mejor evaluados.")
st.caption("Usuarios o contenidos sin calificaciones no entran en las correlaciones de "
           "puntuación y recomendación (no se rellenan con 0).")
ver_tabla(corr.round(2).reset_index(names="Variable"))

# ---------------------------------------------------------------- interacciones de un clic
st.divider()
col_a, col_b = st.columns(2)
with col_a:
    def pares(tipo: str):
        return set(map(tuple, inter.loc[inter["tipo_interaccion"] == tipo,
                                        ["usuario_id", "contenido_id"]].to_numpy()))

    if not sin_datos(cal_par):
        claves = list(zip(cal_par["usuario_id"], cal_par["contenido_id"]))
        filas = []
        for tipo, etiqueta in [("Me gusta", "Dejó \"Me gusta\""),
                               ("Agregar a mi lista", "Agregó a su lista")]:
            con_interaccion = pares(tipo)
            marcado = [k in con_interaccion for k in claves]
            promedio = cal_par.groupby(marcado)["puntuacion_1_5"].mean()
            filas.append({"Interacción": etiqueta, "No": promedio.get(False),
                          "Sí": promedio.get(True)})
        tabla = pd.DataFrame(filas)

        fig = go.Figure()
        for serie, color in [("No", COLOR_NEUTRO), ("Sí", COLOR_ACENTO_POS)]:
            fig.add_trace(go.Bar(
                x=tabla["Interacción"], y=tabla[serie], name=serie, marker_color=color,
                text=[fmt_num(v, 2) if pd.notna(v) else "" for v in tabla[serie]],
                textposition="outside", cliponaxis=False,
                hovertemplate="%{x}: " + serie + "<br>Puntuación prom.: %{text}<extra></extra>",
            ))
        fig.update_yaxes(title_text="Puntuación promedio (1 a 5)", range=[0, 5.5])
        fig.update_xaxes(showgrid=False)
        fig.update_layout(barmode="group", bargap=0.35, bargroupgap=0.1)
        mostrar(estilo(fig, "Puntuación según si hubo interacción previa", alto=380))
        hallazgo("La puntuación casi no cambia si el usuario dejó \"Me gusta\" (3,97 vs. 3,96) "
                 "o agregó el título a su lista (3,94 vs. 3,97): las interacciones de un clic "
                 "son señales débiles de satisfacción.")
        ver_tabla(tabla.round(2))

# ---------------------------------------------------------------- popularidad vs puntuación
with col_b:
    por_cont = (rep.groupby("contenido_id").agg(n_reproducciones=("reproduccion_id", "count"),
                                                titulo=("titulo", "first"))
                   .join(cal.groupby("contenido_id").agg(n_calificaciones=("calificacion_id", "count"),
                                                        puntuacion=("puntuacion_1_5", "mean")),
                         how="inner"))
    por_cont = por_cont[por_cont["n_calificaciones"] >= 3].reset_index()
    if not sin_datos(por_cont):
        promedio = por_cont["puntuacion"].mean()
        fig = go.Figure(go.Scatter(
            x=por_cont["n_reproducciones"], y=por_cont["puntuacion"], mode="markers",
            marker=dict(size=por_cont["n_calificaciones"], sizemode="area",
                        sizeref=2 * por_cont["n_calificaciones"].max() / 28 ** 2, sizemin=4,
                        color=COLOR_ACENTO_POS, opacity=0.55, line=dict(color="white", width=1)),
            customdata=por_cont[["titulo", "n_calificaciones"]].to_numpy(),
            hovertemplate=("<b>%{customdata[0]}</b><br>Reproducciones: %{x}<br>"
                           "Puntuación prom.: %{y:.2f}<br>Calificaciones: %{customdata[1]}"
                           "<extra></extra>"),
        ))
        fig.add_hline(y=promedio, line=dict(color=COLOR_LINEA, width=1.5),
                      annotation_text=f"Promedio {fmt_num(promedio, 2)}",
                      annotation_position="top right",
                      annotation_bgcolor="rgba(255,255,255,0.85)")
        fig.update_xaxes(title_text="N° de reproducciones del contenido", showgrid=False)
        fig.update_yaxes(title_text="Puntuación promedio")
        mostrar(estilo(fig, "Popularidad vs. puntuación por contenido", alto=380))
        st.caption("Tamaño del punto = N° de calificaciones. Solo contenidos con 3 o más "
                   "calificaciones.")
        hallazgo("Hay títulos muy vistos bajo el promedio y títulos poco vistos muy bien "
                 "evaluados (posibles joyas ocultas del catálogo).")

recomendaciones([
    "Usar el **% completado como señal de satisfacción en tiempo real:** sube con la puntuación "
    "(r = 0,20), mientras que un \"Me gusta\" casi no la cambia (3,97 vs. 3,96), y está disponible en "
    "cada reproducción, cuando solo el 12,7% de las reproducciones tiene una calificación.",
    "Para portada, recomendaciones y renovación de licencias, **cruzar siempre reproducciones con % "
    "completado y puntuación**, no solo el volumen.",
])

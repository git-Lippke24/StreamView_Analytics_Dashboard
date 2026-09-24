"""Página 4 · Experiencia técnica — Responsables: Hernán (dispositivo, buffering, calidad)
y pendiente de asignar (sistema operativo y versión de app).

Secciones del notebook: "Reproducciones…" (gráficos de dispositivo y buffering) y
"Experiencia técnica por dispositivo" (pendiente).
Tablas: reproducciones + dispositivos.
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.datos import ORDEN_CALIDAD, sin_datos
from src.graficos import (COLOR_ACENTO, COLOR_NEUTRO, barras, estilo, hallazgo, mostrar,
                          ver_tabla)
from src.kpis import fmt_num

d = st.session_state["datos"]
rep = d["reproducciones"]

st.title("Experiencia técnica")
st.caption("¿En qué dispositivo y con qué calidad falla la reproducción?")

if sin_datos(rep):
    st.stop()

# ---------------------------------------------------------------- por dispositivo
por_disp = (rep.groupby("tipo_dispositivo")
               .agg(pct=("porcentaje_completado", "mean"),
                    abandono=("abandono_temprano", lambda s: s.eq("Sí").mean() * 100),
                    buffering=("buffering_segundos", "mean"),
                    reproducciones=("reproduccion_id", "count"))
               .reset_index().sort_values("pct"))
por_disp["buf_txt"] = por_disp["buffering"].map(lambda v: f"{fmt_num(v, 1)} s")
por_disp["n_txt"] = por_disp["reproducciones"].map(fmt_num)
orden = por_disp["tipo_dispositivo"].tolist()[::-1]  # mismo orden en ambos paneles

col_a, col_b = st.columns(2)
with col_a:
    peor_pct = por_disp.iloc[0]["tipo_dispositivo"]
    mostrar(barras(por_disp, "tipo_dispositivo", "pct", titulo="% completado promedio",
                   eje_valor="% completado promedio", sufijo="%", destacar=peor_pct,
                   orden=orden, hover={"Buffering prom.": "buf_txt", "Reproducciones": "n_txt"}))
with col_b:
    peor_ab = por_disp.loc[por_disp["abandono"].idxmax(), "tipo_dispositivo"]
    mostrar(barras(por_disp, "tipo_dispositivo", "abandono",
                   titulo="Tasa de abandono temprano (<20% visto)",
                   eje_valor="% de reproducciones abandonadas", sufijo="%", decimales=2,
                   destacar=peor_ab, orden=orden,
                   hover={"Buffering prom.": "buf_txt", "Reproducciones": "n_txt"}))
hallazgo("Móvil, el dispositivo con más reproducciones, tiene el menor % completado (63,2% vs. "
         "79,8% en Smart TV) y la mayor tasa de abandono (0,98%). Móvil y Tablet duplican el "
         "buffering promedio del resto (~11 s vs. ~6 s).")
ver_tabla(por_disp.rename(columns={"tipo_dispositivo": "Dispositivo",
                                   "reproducciones": "Reproducciones",
                                   "pct": "% completado prom.", "abandono": "% abandono",
                                   "buffering": "Buffering prom. (s)"})
                  [["Dispositivo", "Reproducciones", "% completado prom.", "% abandono",
                    "Buffering prom. (s)"]].round(2))

# ---------------------------------------------------------------- buffering vs completado
st.divider()
muestra = rep.sample(min(2000, len(rep)), random_state=42)
pendiente, intercepto = np.polyfit(rep["buffering_segundos"], rep["porcentaje_completado"], 1)
x_linea = np.array([rep["buffering_segundos"].min(), rep["buffering_segundos"].max()])
corr = rep["buffering_segundos"].corr(rep["porcentaje_completado"])

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=muestra["buffering_segundos"], y=muestra["porcentaje_completado"], mode="markers",
    marker=dict(color=COLOR_NEUTRO, size=6, opacity=0.35), name="Reproducción (muestra)",
    hovertemplate="Buffering: %{x:.1f} s<br>Completado: %{y:.1f}%<extra></extra>",
))
fig.add_trace(go.Scatter(
    x=x_linea, y=intercepto + pendiente * x_linea, mode="lines",
    line=dict(color=COLOR_ACENTO, width=2), name="Tendencia lineal",
    hovertemplate="Tendencia: %{y:.1f}%<extra></extra>",
))
fig.update_xaxes(title_text="Buffering (segundos)", showgrid=False)
fig.update_yaxes(title_text="% completado")
mostrar(estilo(fig, "Buffering vs. % completado", alto=420))
st.caption(f"Correlación con los filtros actuales: {fmt_num(corr, 2)}. Se grafica una muestra "
           f"de {fmt_num(len(muestra))} reproducciones; la tendencia usa todas.")
hallazgo("Correlación negativa moderada (≈ −0,31): a más segundos de buffering, menor avance "
         "en el contenido. El buffering es una palanca de retención, no solo una métrica "
         "técnica.")

# ---------------------------------------------------------------- calidad de video
st.divider()
st.subheader("Calidad de video")
por_calidad = (rep.groupby("calidad_video")
                  .agg(reproducciones=("reproduccion_id", "count"),
                       pct=("porcentaje_completado", "mean"),
                       buffering=("buffering_segundos", "mean"),
                       abandono=("abandono_temprano", lambda s: s.eq("Sí").mean() * 100))
                  .reindex([c for c in ORDEN_CALIDAD if c in set(rep["calidad_video"])])
                  .round({"pct": 1, "buffering": 1, "abandono": 2})
                  .reset_index())
st.dataframe(
    por_calidad, hide_index=True,
    column_config={
        "calidad_video": "Calidad",
        "reproducciones": st.column_config.NumberColumn("Reproducciones", format="localized"),
        "pct": st.column_config.NumberColumn("% completado prom.", format="localized"),
        "buffering": st.column_config.NumberColumn("Buffering prom. (s)", format="localized"),
        "abandono": st.column_config.NumberColumn("% abandono", format="localized"),
    },
)
hallazgo("El abandono es mayor en SD (0,51%) y menor en 4K (0,32%), aunque no baja de forma pareja: Full HD (0,42%) supera a HD (0,37%).")

# ---------------------------------------------------------------- pendiente
st.divider()
st.subheader("Sistema operativo y versión de app")
st.info(
    "**Pendiente: responsable por asignar (sección \"Experiencia técnica por dispositivo\" "
    "del notebook).** `reproducciones` ya trae las columnas `sistema_operativo` y "
    "`version_app` unidas desde `dispositivos`. Sugerencia: % completado, abandono y buffering "
    "por sistema operativo y por versión de app, con el mismo helper `barras()` de arriba.",
    icon=":material/construction:",
)

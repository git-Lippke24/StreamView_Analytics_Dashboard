"""Página 4 · Experiencia técnica — Responsables: Hernán (dispositivo, buffering, calidad)
y Matias (sistema operativo, versión de app, foco geográfico y relación con cancelaciones).

Secciones del notebook: "Reproducciones…" (gráficos de dispositivo y buffering) y
"Experiencia técnica por dispositivo" (sistema operativo/versión, países y cancelaciones).
Tablas: reproducciones + dispositivos + usuarios.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.datos import ORDEN_CALIDAD, sin_datos
from src.graficos import (COLOR_ACENTO, COLOR_LINEA, COLOR_NEUTRO, barras, estilo, hallazgo,
                          mostrar, ver_tabla)
from src.kpis import fmt_num

d = st.session_state["datos"]
rep = d["reproducciones"]
usu = d["usuarios"]

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
hallazgo("Móvil, el dispositivo más usado (30,6% de las reproducciones), tiene el menor % "
         "completado (63,2% vs. 79,8% en Smart TV) y la mayor tasa de abandono (0,98%): concentra "
         "75 de los 99 abandonos del año (76%). Móvil y Tablet duplican el buffering promedio del "
         "resto (≈11,5 s vs. ≈5,8 s).")
ver_tabla(por_disp.rename(columns={"tipo_dispositivo": "Dispositivo",
                                   "reproducciones": "Reproducciones",
                                   "pct": "% completado prom.", "abandono": "% abandono",
                                   "buffering": "Buffering prom. (s)"})
                  [["Dispositivo", "Reproducciones", "% completado prom.", "% abandono",
                    "Buffering prom. (s)"]].round(2))

# ---------------------------------------------------------------- buffering vs completado
st.divider()
muestra = rep.sample(min(2000, len(rep)), random_state=42)
# La tendencia y la correlación solo tienen sentido con varios puntos y buffering que varíe
hay_tendencia = len(rep) >= 3 and rep["buffering_segundos"].nunique() > 1
if hay_tendencia:
    pendiente, intercepto = np.polyfit(rep["buffering_segundos"], rep["porcentaje_completado"], 1)
    x_linea = np.array([rep["buffering_segundos"].min(), rep["buffering_segundos"].max()])
    corr = rep["buffering_segundos"].corr(rep["porcentaje_completado"])

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=muestra["buffering_segundos"], y=muestra["porcentaje_completado"], mode="markers",
    marker=dict(color=COLOR_NEUTRO, size=6, opacity=0.35), name="Reproducción (muestra)",
    hovertemplate="Buffering: %{x:.1f} s<br>Completado: %{y:.1f}%<extra></extra>",
))
if hay_tendencia:
    fig.add_trace(go.Scatter(
        x=x_linea, y=intercepto + pendiente * x_linea, mode="lines",
        line=dict(color=COLOR_ACENTO, width=2), name="Tendencia lineal",
        hovertemplate="Tendencia: %{y:.1f}%<extra></extra>",
    ))
fig.update_xaxes(title_text="Buffering (segundos)", showgrid=False)
fig.update_yaxes(title_text="% completado")
mostrar(estilo(fig, "Buffering vs. % completado", alto=420))
if hay_tendencia:
    st.caption(f"Correlación con los filtros actuales: {fmt_num(corr, 2)}. Se grafica una muestra "
               f"de {fmt_num(len(muestra))} reproducciones; la tendencia usa todas.")
else:
    st.caption("Con los filtros actuales hay muy pocas reproducciones para calcular una tendencia.")
hallazgo("Correlación negativa moderada (≈ −0,31): a más segundos de buffering, menor avance "
         "en el contenido. El buffering es una palanca de consumo efectivo; su efecto sobre la "
         "retención es una hipótesis a validar (el buffering promedio de un usuario no se asocia "
         "con haber cancelado).")

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
hallazgo("La calidad de video casi no cambia el % completado (71,2% a 72,4%). El abandono es "
         "mayor en SD (0,51%) y menor en 4K (0,32%), pero no baja de forma pareja: Full HD "
         "(0,42%) supera a HD (0,37%). Son diferencias de décimas con pocos casos, así que la "
         "calidad no aparece como un factor fuerte; el buffering sí.")

# ---------------------------------------------------------------- sistema operativo y version app
st.divider()
st.subheader("Sistema operativo y versión de app")

DISPOSITIVOS_FIJOS = {"Smart TV", "Computador", "Consola"}
ANDROID, APPLE, FIJO = "Android", "Apple (iOS/iPadOS)", "Fijo (TV/PC/consola)"
ORDEN_VERSION = ["6.8", "6.9", "7.0", "7.1", "7.2"]

rep_os = rep.dropna(subset=["sistema_operativo", "version_app"]).copy()
rep_os["familia_app"] = np.select(
    [rep_os["sistema_operativo"].eq("Android"),
     rep_os["sistema_operativo"].isin(["iOS", "iPadOS"]),
     rep_os["tipo_dispositivo"].isin(DISPOSITIVOS_FIJOS)],
    [ANDROID, APPLE, FIJO], default=None,
)
rep_os = rep_os.dropna(subset=["familia_app"])

if not sin_datos(rep_os, minimo=10):
    buf_version = (rep_os.groupby(["familia_app", "version_app"])["buffering_segundos"]
                         .mean().unstack("familia_app").reindex(ORDEN_VERSION))
    fig = go.Figure()
    for serie, color, grosor in [(FIJO, COLOR_NEUTRO, 2), (APPLE, COLOR_LINEA, 2),
                                 (ANDROID, COLOR_ACENTO, 3)]:
        if serie not in buf_version.columns:
            continue
        fig.add_trace(go.Scatter(
            x=ORDEN_VERSION, y=buf_version[serie], mode="lines+markers", name=serie,
            line=dict(color=color, width=grosor), marker=dict(size=8),
            hovertemplate=f"{serie}<br>Versión %{{x}}: %{{y:.1f}} s<extra></extra>",
        ))
    fig.update_xaxes(title_text="Versión de la app", showgrid=False)
    fig.update_yaxes(title_text="Buffering promedio (s)", rangemode="tozero")
    mostrar(estilo(fig, "El buffering de Android cae a la mitad desde la versión 7.0", alto=380))
    ver_tabla(buf_version.round(1).reset_index().rename(columns={"version_app": "Versión de app"}))
hallazgo("En Android, las versiones 6.8 y 6.9 tienen ≈22 s de buffering; desde la 7.0 bajan a "
         "≈10 s, igual que en Apple y en los dispositivos fijos (que no cambian con la versión). "
         "Es un problema acotado (1.050 reproducciones, 103 dispositivos) y específico del "
         "reproductor de Android anterior a la 7.0: la versión que lo corrige ya existe, solo "
         "falta que esos usuarios actualicen.")

# ---------------------------------------------------------------- foco geografico
st.divider()
st.subheader("Buffering por país")

FOCOS_PAIS = ["Perú", "Ecuador"]
rep_geo = rep.assign(familia=np.where(rep["tipo_dispositivo"].isin(DISPOSITIVOS_FIJOS),
                                      "Fijo", "Portátil"))
buf_pais = rep_geo.groupby(["familia", "pais"])["buffering_segundos"].mean().reset_index()

col_fijo, col_portatil = st.columns(2)
for col, familia in [(col_fijo, "Fijo"), (col_portatil, "Portátil")]:
    with col:
        datos_familia = (buf_pais[buf_pais["familia"] == familia]
                                  .sort_values("buffering_segundos"))
        if not sin_datos(datos_familia, minimo=2):
            mostrar(barras(datos_familia, "pais", "buffering_segundos",
                           titulo=f"Buffering promedio — {familia}",
                           eje_valor="Buffering promedio (s)", sufijo=" s",
                           destacar=FOCOS_PAIS, orden=datos_familia["pais"].tolist()))
hallazgo("Perú y Ecuador tienen ≈3,5 s más de buffering que el resto en ambas familias de "
         "dispositivo (fijos: 8,6–8,8 s vs. ≈5,2 s; portátiles: 14,5–14,7 s vs. ≈10,9 s), y juntos "
         "suman el 17% de las reproducciones. Como el aumento aparece en todo tipo de dispositivo "
         "y no solo en la app móvil, apunta a un problema de red o de distribución de contenido "
         "(CDN) en esos países, más que a la app.")
ver_tabla(buf_pais.pivot(index="pais", columns="familia", values="buffering_segundos")
                  .round(1).reset_index().rename(columns={"pais": "País"}))

# ---------------------------------------------------------------- relacion con cancelaciones
st.divider()
st.subheader("¿La experiencia técnica explica las cancelaciones?")

usuario_tec = (rep.groupby("usuario_id")["buffering_segundos"].mean()
                  .rename("buffering_prom").reset_index()
                  .merge(usu[["usuario_id", "estado"]], on="usuario_id", how="left"))

CUARTILES = ["Q1\nmenos buffering", "Q2", "Q3", "Q4\nmás buffering"]
cuartil_ok = False
if len(usuario_tec) >= 20 and usuario_tec["buffering_prom"].nunique() >= 4:
    try:
        usuario_tec["cuartil"] = pd.qcut(usuario_tec["buffering_prom"], 4, labels=CUARTILES)
        cuartil_ok = True
    except ValueError:
        pass  # muy pocos valores distintos de buffering con los filtros actuales

if cuartil_ok:
    churn_cuartil = (usuario_tec.groupby("cuartil", observed=True)["estado"]
                                .apply(lambda s: s.eq("Cancelada").mean() * 100)
                                .reset_index(name="tasa"))
    mostrar(barras(churn_cuartil, "cuartil", "tasa", horizontal=False,
                   titulo="Cancelación según el buffering promedio del usuario",
                   eje_valor="% de usuarios cancelados", sufijo="%", orden=CUARTILES))
    st.caption(f"Con los filtros actuales: {fmt_num(len(usuario_tec))} usuarios agrupados en "
               f"cuartiles de buffering promedio.")
else:
    st.info("Con los filtros actuales no hay suficiente variación de buffering para formar "
            "cuartiles.")

cancelados = usu[usu["estado"] == "Cancelada"]
if not sin_datos(cancelados, minimo=5):
    pct_tecnico = cancelados["motivo_cancelacion"].eq("Problemas técnicos").mean() * 100
    st.caption(f"\"Problemas técnicos\" explica el {fmt_num(pct_tecnico, 1)}% de las "
               f"cancelaciones del filtro actual (ver el detalle de motivos en Retención).")

hallazgo("La tasa de cancelación es prácticamente la misma entre cuartiles de buffering (entre "
         "24,5% y 29,9%, promedio 27,7% con todos los datos de 2025): el buffering promedio de un "
         "usuario no predice si cancela. \"Problemas técnicos\" es además un motivo declarado "
         "minoritario (36 de 415 cancelaciones, 8,7%), muy por debajo de \"Poco uso\" y "
         "\"Precio\". La experiencia técnica reduce el consumo efectivo (ver más arriba), pero no "
         "aparece como la causa principal de las cancelaciones: son fenómenos relacionados pero "
         "distintos.")

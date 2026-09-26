"""Página 4 · Experiencia técnica — Responsables: Hernán (dispositivo, buffering, calidad)
y Matias (tramos de buffering, sistema operativo, versión de app, foco geográfico, 4K y
relación con cancelaciones).

Secciones del notebook: 4.2.4 y 4.2.5 (dispositivo, buffering y calidad) y 4.4
"Experiencia técnica por dispositivo, sistema operativo, versión de app y calidad".
Tablas: reproducciones + dispositivos + usuarios.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.datos import ORDEN_CALIDAD, ORDEN_PLAN, sin_datos
from src.graficos import (COLOR_ACENTO, COLOR_LINEA, COLOR_NEUTRO, barras, estilo, hallazgo,
                          mostrar, recomendaciones, ver_tabla)
from src.hallazgos import SEGMENTOS_TECNICOS, fig_segmentos_tecnicos, segmento_tecnico
from src.kpis import UMBRAL_BUFFERING, fmt_num

d = st.session_state["datos"]
rep = d["reproducciones"]
usu = d["usuarios"]

st.title("Experiencia técnica")
st.caption("¿Dónde falla la reproducción (dispositivo, versión de app, país, calidad) y cuánto consumo "
           "cuesta? · Notebook, secciones 4.2.4, 4.2.5 y 4.4.")

if sin_datos(rep):
    st.stop()

# ---------------------------------------------------------------- por dispositivo
st.subheader("Completado y abandono por dispositivo")
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
st.subheader("Buffering vs. % completado")
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

# ---------------------------------------------------------------- tramos de buffering
st.divider()
st.subheader("¿Cuánto consumo cuesta el buffering?")
TRAMOS = ["0", "0–5", "5–10", "10–15", "15–20", "20–30", ">30"]
TRAMOS_ALTOS = ["15–20", "20–30", ">30"]  # sobre UMBRAL_BUFFERING
por_tramo = (rep.assign(tramo=pd.cut(rep["buffering_segundos"], [-0.1, 0, 5, 10, 15, 20, 30, np.inf],
                                     labels=TRAMOS))
                .groupby("tramo", observed=True)
                .agg(reproducciones=("reproduccion_id", "count"),
                     pct=("porcentaje_completado", "mean"),
                     abandono=("abandono_temprano", lambda s: s.eq("Sí").mean() * 100))
                .reset_index())
por_tramo["tramo"] = por_tramo["tramo"].astype(str)
por_tramo["n_txt"] = por_tramo["reproducciones"].map(fmt_num)
orden_tramos = [t for t in TRAMOS if t in set(por_tramo["tramo"])]
col_a, col_b = st.columns(2)
with col_a:
    mostrar(barras(por_tramo, "tramo", "pct", horizontal=False, titulo="% completado promedio",
                   eje_valor="% completado promedio", sufijo="%", destacar=TRAMOS_ALTOS,
                   orden=orden_tramos, hover={"Reproducciones": "n_txt"}))
with col_b:
    mostrar(barras(por_tramo, "tramo", "abandono", horizontal=False,
                   titulo="Tasa de abandono temprano (<20% visto)",
                   eje_valor="% de reproducciones abandonadas", sufijo="%", decimales=1,
                   destacar=TRAMOS_ALTOS, orden=orden_tramos, hover={"Reproducciones": "n_txt"}))
st.caption(f"Eje horizontal: segundos de buffering en la sesión. En rojo, los tramos sobre "
           f"{UMBRAL_BUFFERING} s (buffering alto).")
hallazgo("El % completado cae de forma sostenida con el buffering: de 79,5% en sesiones sin buffering "
         "a 51,2% sobre los 30 s (≈ −1 punto por cada segundo extra). El abandono temprano se mantiene "
         "en 0,2% o menos bajo los 10 s y se dispara sobre los 15 s: 0,8% (15–20 s), 2,3% (20–30 s) y "
         "5,3% (>30 s). Por eso 15 s es el umbral de buffering alto que usamos como KPI en el Resumen.")
ver_tabla(por_tramo.rename(columns={"tramo": "Buffering (s)", "reproducciones": "Reproducciones",
                                    "pct": "% completado prom.", "abandono": "% abandono"})
                   [["Buffering (s)", "Reproducciones", "% completado prom.", "% abandono"]].round(2))

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
         "≈10 s, igual que en Apple. En Apple y en los dispositivos fijos la versión no cambia nada. "
         "Es un problema acotado (1.050 reproducciones, 103 dispositivos) y específico del "
         "reproductor de Android anterior a la 7.0: la versión que lo corrige ya existe, solo "
         "falta que esos usuarios actualicen.")

# Un grupo pequeño, un daño desproporcionado (notebook 4.4.5)
seg = segmento_tecnico(rep)
metricas_seg = (rep.assign(segmento=seg, abandono=rep["abandono_temprano"].eq("Sí"))
                   .groupby("segmento")
                   .agg(reproducciones=("reproduccion_id", "count"),
                        buffering=("buffering_segundos", "mean"),
                        pct=("porcentaje_completado", "mean"),
                        abandonos=("abandono", "sum"),
                        tasa_abandono=("abandono", lambda s: s.mean() * 100))
                   .reindex([s for s in SEGMENTOS_TECNICOS if s in set(seg)])
                   .reset_index())
mostrar(fig_segmentos_tecnicos(
    rep, titulo="Participación de cada segmento en las reproducciones y en los abandonos tempranos"))
st.caption("Si un segmento se comportara como el promedio, su trozo mediría lo mismo en ambas barras.")
hallazgo("Android con app 6.8–6.9 es solo el 4,2% de las reproducciones, pero genera el 25% de los "
         "abandonos tempranos (25 de 99). Frente a otros móviles y tablets tiene 2,2 veces el "
         "buffering (22,3 s vs. 10,3 s), ve 8 puntos menos de cada contenido (57,3% vs. 65,4% "
         "completado) y abandona 4 veces más (2,4% vs. 0,6%). Si se comportara como el resto de los "
         "portátiles, se evitarían ~19 de los 99 abandonos tempranos del año.")
ver_tabla(metricas_seg.rename(columns={"segmento": "Segmento", "reproducciones": "Reproducciones",
                                       "buffering": "Buffering prom. (s)", "pct": "% completado prom.",
                                       "abandonos": "Abandonos", "tasa_abandono": "% abandono"})
                      .round(2))

# ---------------------------------------------------------------- foco geografico
st.divider()
st.subheader("Buffering por país")

FOCOS_PAIS = ["Perú", "Ecuador"]
rep_geo = rep.assign(familia=np.where(rep["tipo_dispositivo"].isin(DISPOSITIVOS_FIJOS),
                                      "Fijo", "Portátil"))
buf_pais = rep_geo.groupby(["familia", "pais"])["buffering_segundos"].mean().reset_index()
buf_pais_ancho = buf_pais.pivot(index="pais", columns="familia", values="buffering_segundos")

# Gráfico de pesas (dumbbell): un punto por familia y país, conectados por una línea.
# Con dos paneles separados el orden de países no coincide entre uno y otro (cada uno
# ordena por su propio valor); el dumbbell fija un único orden y muestra el nivel de
# cada familia y la brecha entre ambas en la misma fila.
if {"Fijo", "Portátil"}.issubset(buf_pais_ancho.columns):
    buf_pais_ancho = buf_pais_ancho.dropna(subset=["Fijo", "Portátil"])
if not sin_datos(buf_pais_ancho, minimo=2):
    orden_pais = buf_pais_ancho.sort_values("Portátil").index.tolist()
    y_pos = list(range(len(orden_pais)))
    colores_pais = [COLOR_ACENTO if p in FOCOS_PAIS else COLOR_NEUTRO for p in orden_pais]

    fig = go.Figure()
    for i, (pais, color) in enumerate(zip(orden_pais, colores_pais)):
        fig.add_trace(go.Scatter(
            x=[buf_pais_ancho.loc[pais, "Fijo"], buf_pais_ancho.loc[pais, "Portátil"]],
            y=[i, i], mode="lines", line=dict(color=color, width=2),
            showlegend=False, hoverinfo="skip",
        ))
    fig.add_trace(go.Scatter(
        x=buf_pais_ancho.loc[orden_pais, "Fijo"], y=y_pos, mode="markers",
        name="Fijo (TV/PC/consola)", customdata=orden_pais,
        marker=dict(size=11, color="white", line=dict(width=2, color=colores_pais)),
        hovertemplate="<b>%{customdata}</b><br>Fijo: %{x:.1f} s<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=buf_pais_ancho.loc[orden_pais, "Portátil"], y=y_pos, mode="markers",
        name="Portátil (Móvil/Tablet)", customdata=orden_pais,
        marker=dict(size=11, color=colores_pais),
        hovertemplate="<b>%{customdata}</b><br>Portátil: %{x:.1f} s<extra></extra>",
    ))
    for pais in FOCOS_PAIS:  # etiqueta directa solo en los países foco, para no saturar
        if pais not in orden_pais:
            continue
        i = orden_pais.index(pais)
        for familia in ("Fijo", "Portátil"):
            fig.add_annotation(x=buf_pais_ancho.loc[pais, familia], y=i,
                               text=f"{fmt_num(buf_pais_ancho.loc[pais, familia], 1)} s",
                               showarrow=False, yshift=13, font=dict(size=10, color=COLOR_LINEA))
    fig.update_yaxes(tickmode="array", tickvals=y_pos, ticktext=orden_pais, showgrid=False)
    fig.update_xaxes(title_text="Buffering promedio (s)", rangemode="tozero", showgrid=True,
                     zeroline=False)
    mostrar(estilo(fig, "Buffering promedio por país: fijos vs. portátiles",
                  alto=max(280, 60 + 34 * len(orden_pais))))
hallazgo("Perú y Ecuador tienen ≈3,5 s más de buffering que el resto en ambas familias de "
         "dispositivo (fijos: 8,6–8,8 s vs. ≈5,2 s; portátiles: 14,5–14,7 s vs. ≈10,9 s), y juntos "
         "suman el 17% de las reproducciones. Como el aumento aparece en todo tipo de dispositivo "
         "y no solo en la app móvil, apunta a un problema de red o de distribución de contenido "
         "(CDN) en esos países, más que a la app.")
ver_tabla(buf_pais.pivot(index="pais", columns="familia", values="buffering_segundos")
                  .round(1).reset_index().rename(columns={"pais": "País"}))

# ---------------------------------------------------------------- calidad de video y 4K
st.divider()
st.subheader("Calidad de video")
calidades = [c for c in ORDEN_CALIDAD if c in set(rep["calidad_video"])]
por_calidad = (rep.groupby("calidad_video")
                  .agg(reproducciones=("reproduccion_id", "count"),
                       pct=("porcentaje_completado", "mean"),
                       buffering=("buffering_segundos", "mean"),
                       abandono=("abandono_temprano", lambda s: s.eq("Sí").mean() * 100))
                  .reindex(calidades)
                  .round({"pct": 1, "buffering": 1, "abandono": 2})
                  .reset_index())
buf_calidad = (rep_geo.groupby(["calidad_video", "familia"])["buffering_segundos"].mean()
                      .unstack("familia").reindex(calidades).round(1).reset_index())
pct_4k_plan = (rep.groupby("plan")["calidad_video"].apply(lambda s: s.eq("4K").mean() * 100)
                  .reindex([p for p in ORDEN_PLAN if p in set(rep["plan"])]).round(1)
                  .reset_index(name="% de reproducciones en 4K"))
col_a, col_b, col_c = st.columns([3, 2, 1.6])
with col_a:
    st.caption("Resultados por calidad")
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
with col_b:
    st.caption("Buffering promedio (s) por calidad y familia")
    st.dataframe(buf_calidad, hide_index=True,
                 column_config={"calidad_video": "Calidad"} | {
                     c: st.column_config.NumberColumn(c, format="localized")
                     for c in buf_calidad.columns if c != "calidad_video"})
with col_c:
    st.caption("Uso de 4K por plan")
    st.dataframe(pct_4k_plan, hide_index=True,
                 column_config={"plan": "Plan", "% de reproducciones en 4K":
                                st.column_config.NumberColumn("% en 4K", format="localized")})
hallazgo("La calidad de video casi no cambia el % completado (71,2% a 72,4%). El abandono es "
         "mayor en SD (0,51%) y menor en 4K (0,32%), pero no baja de forma pareja: Full HD "
         "(0,42%) supera a HD (0,37%). Son diferencias de décimas con pocos casos, así que la "
         "calidad no aparece como un factor fuerte; el buffering sí.")
hallazgo("SD, HD y Full HD tienen el mismo buffering; el 4K suma ~2 s en ambas familias y en "
         "portátiles llega a 13,4 s. El plan Premium reproduce el 34% de su contenido en 4K (Básico: "
         "4%): el 4K en una pantalla de celular aporta poco valor visual, agrega buffering y lo sufren "
         "sobre todo los clientes que más pagan.")

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
    promedio_churn = usuario_tec["estado"].eq("Cancelada").mean() * 100
    fig = barras(churn_cuartil, "cuartil", "tasa", horizontal=False,
                titulo="Cancelación según el buffering promedio del usuario",
                eje_valor="% de usuarios cancelados", sufijo="%", orden=CUARTILES)
    # Línea de referencia en el promedio general: si las barras la siguen de cerca,
    # es la prueba visual de que el cuartil de buffering no cambia la cancelación.
    fig.add_hline(y=promedio_churn, line=dict(color=COLOR_LINEA, dash="dash", width=1.5),
                 annotation_text=f"Promedio: {fmt_num(promedio_churn, 1)}%",
                 annotation_position="top left", annotation_font_size=11)
    mostrar(fig)
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

hallazgo("La tasa de cancelación no sube con el buffering: entre cuartiles va de 24,5% a 29,9% "
         "(promedio 27,7% con todos los datos de 2025), y el cuartil con menos buffering (Q1) es el "
         "que más cancela. \"Problemas técnicos\" es además un motivo declarado minoritario (36 de 415 "
         "cancelaciones, 8,7%), muy por debajo de \"Poco uso\" y \"Precio\". La experiencia técnica "
         "reduce el consumo (ver más arriba), pero no explica las cancelaciones: para la retención, el "
         "foco está en el plan Básico (ver Retención).")

recomendaciones([
    "**Forzar o incentivar la actualización a la versión 7.0** en los 103 dispositivos Android con "
    "app 6.8–6.9: son el 4,2% de las reproducciones y el 25% de los abandonos tempranos, y la versión "
    "que corrige el problema ya existe.",
    "**Revisar la red de distribución de contenido (CDN) en Perú y Ecuador:** suman el 17% de las "
    "reproducciones y tienen ~3,5 s más de buffering en todo tipo de dispositivo.",
    "**En móviles y tablets, no partir en 4K por defecto:** suma ~2 s de buffering y afecta sobre todo "
    "a Premium (34% de sus reproducciones en 4K).",
    f"**Seguir el % de sesiones con buffering sobre {UMBRAL_BUFFERING} s** como KPI técnico "
    f"(está en el Resumen).",
])

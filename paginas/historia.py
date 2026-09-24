"""Página 7 · Historia y recomendaciones (data storytelling) — Responsable: grupal.

Narrativa guiada en 4 pasos: contexto → tensión → hallazgos → acción.
Usa SIEMPRE el año completo (no aplica los filtros) para que el relato sea estable
durante la presentación. Las cifras se calculan en vivo desde los datos.
"""
import plotly.graph_objects as go
import streamlit as st

from src.datos import ORDEN_PLAN, ORDEN_SEGMENTO, cargar_datos, filtrar
from src.graficos import (COLOR_ACENTO, COLOR_ACENTO_POS, COLOR_LINEA, COLOR_NEUTRO, barras,
                          estilo, mostrar)
from src.kpis import fmt_num, kpis_generales, serie_mensual, tasa_cancelacion_por

datos = cargar_datos()
d = filtrar(datos, meses=(1, 12), paises=sorted(datos["usuarios"]["pais"].unique()),
            planes=ORDEN_PLAN, segmentos=ORDEN_SEGMENTO)
k = kpis_generales(d)
serie = serie_mensual(d)
rep, usuarios = d["reproducciones"], d["usuarios"]

st.title("Más minutos que nunca, pero más cancelaciones")
st.caption("Audiencia: comité de Producto y Retención · Propósito: informar y persuadir · "
           "Datos: año completo 2025 (esta página no usa los filtros).")

# ================================================================ 1. Contexto
st.header("1. Contexto: el consumo creció durante 2025")
minutos = serie.set_index("mes")["minutos"]
var_abr_dic = (minutos[12] / minutos[4] - 1) * 100
c1, c2 = st.columns([1, 3])
c1.metric("Minutos vistos en 2025", fmt_num(k["minutos"]))
c1.metric("Diciembre vs. abril", f"+{fmt_num(var_abr_dic, 0)}%")
with c2:
    fig = go.Figure(go.Scatter(
        x=serie["mes_nombre"], y=serie["minutos"], mode="lines+markers",
        line=dict(color=COLOR_LINEA, width=2), marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>Minutos: %{y:,.0f}<extra></extra>",
    ))
    fig.add_annotation(x=serie["mes_nombre"].iloc[-1], y=serie["minutos"].iloc[-1],
                       text=f"{fmt_num(serie['minutos'].iloc[-1])} min", showarrow=False,
                       xanchor="right", yanchor="bottom", yshift=10)
    fig.update_yaxes(rangemode="tozero", title_text="Minutos vistos")
    fig.update_xaxes(showgrid=False)
    mostrar(estilo(fig, "Minutos vistos por mes", alto=320))

# ================================================================ 2. Tensión
st.header("2. Tensión: las cancelaciones crecieron más rápido")
cancel = serie.set_index("mes")["cancelaciones"]
pct_h2 = cancel.loc[7:12].sum() / cancel.sum() * 100
c1, c2 = st.columns([1, 3])
c1.metric("Cancelaciones en enero", fmt_num(cancel[1]))
c1.metric("Cancelaciones en diciembre", fmt_num(cancel[12]))
c1.metric("Ocurridas en el 2° semestre", f"{fmt_num(pct_h2, 0)}%")
with c2:
    fig = go.Figure(go.Bar(
        x=serie["mes_nombre"], y=serie["cancelaciones"],
        marker_color=[COLOR_NEUTRO if m <= 6 else COLOR_ACENTO for m in serie["mes"]],
        text=serie["cancelaciones"].map(fmt_num), textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Cancelaciones: %{text}<extra></extra>",
    ))
    fig.update_yaxes(title_text="Suscripciones canceladas", range=[0, cancel.max() * 1.2])
    fig.update_xaxes(showgrid=False)
    mostrar(estilo(fig, "Suscripciones canceladas por mes (2° semestre destacado)", alto=320))

# ================================================================ 3. Hallazgos
st.header("3. Hallazgos: quién se va y dónde falla la experiencia")

st.subheader("Se va el plan Básico, y se va por poco uso")
col_a, col_b = st.columns(2)
with col_a:
    por_plan = tasa_cancelacion_por(usuarios, "plan")
    mostrar(barras(por_plan, "plan", "tasa", titulo="Tasa de cancelación por plan",
                   eje_valor="% canceladas", sufijo="%", destacar="Básico", orden=ORDEN_PLAN))
with col_b:
    motivos = (usuarios.loc[usuarios["estado"] == "Cancelada", "motivo_cancelacion"]
               .value_counts(normalize=True).mul(100).rename_axis("motivo")
               .reset_index(name="pct").sort_values("pct"))
    mostrar(barras(motivos, "motivo", "pct", titulo="Motivos de cancelación",
                   eje_valor="% de las cancelaciones", sufijo="%", decimales=0,
                   destacar=motivos.iloc[-1]["motivo"]))

st.subheader("El móvil concentra la peor experiencia")
por_disp = (rep.groupby("tipo_dispositivo")
               .agg(pct=("porcentaje_completado", "mean"), buffering=("buffering_segundos", "mean"))
               .reset_index().sort_values("pct"))
movil = por_disp.set_index("tipo_dispositivo").loc["Móvil"]
col_a, col_b = st.columns([3, 1])
with col_a:
    mostrar(barras(por_disp, "tipo_dispositivo", "pct",
                   titulo="% completado promedio por dispositivo", eje_valor="% completado",
                   sufijo="%", destacar="Móvil"))
col_b.metric("Buffering promedio en móvil", f"{fmt_num(movil['buffering'], 1)} s")
col_b.metric("Buffering promedio en Smart TV",
             f"{fmt_num(por_disp.set_index('tipo_dispositivo').loc['Smart TV', 'buffering'], 1)} s")

st.subheader("Terminar un contenido anticipa una buena nota")
rep_par = rep.groupby(["usuario_id", "contenido_id"])["porcentaje_completado"].mean().reset_index()
cal_par = d["calificaciones"].merge(rep_par, on=["usuario_id", "contenido_id"])
por_punt = (cal_par.groupby("puntuacion_1_5")["porcentaje_completado"].mean()
                   .reset_index(name="pct"))
por_punt["puntuacion"] = por_punt["puntuacion_1_5"].astype(str)
mostrar(barras(por_punt, "puntuacion", "pct", horizontal=False,
               titulo="% completado según la puntuación otorgada al mismo contenido",
               eje_valor="% completado promedio", sufijo="%",
               destacar=por_punt["puntuacion"].iloc[-1], color_destacado=COLOR_ACENTO_POS))

# ================================================================ 4. Acción
st.header("4. Acción: recomendaciones")
st.markdown(
    """
1. **Retener al plan Básico antes de que deje de usar la plataforma.** Casi la mitad cancela y
   "Poco uso" es el motivo principal: detectar a quienes bajan su consumo y reactivarlos
   (recomendaciones personalizadas, recordatorios, beneficios de upgrade).
2. **Priorizar la experiencia en móvil:** precarga, calidad adaptativa y recuperación ante cortes,
   porque ahí se concentran el menor % completado y el mayor buffering.
3. **Tratar el buffering como KPI de calidad de servicio,** no solo como métrica de
   infraestructura: se asocia a menor consumo efectivo.
4. **Usar el % completado como señal de satisfacción en tiempo real:** anticipa la calificación
   y cubre a todos los usuarios, no solo a los que califican.
5. **Decidir portada y licencias cruzando reproducciones con % completado y puntuación,**
   no solo por volumen.
"""
)
st.info("Pendiente: sumar las recomendaciones de Preferencias de contenido y de Experiencia "
        "técnica (sistema operativo y versión de app) cuando esas secciones estén listas.",
        icon=":material/construction:")

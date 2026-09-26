"""Página 7 · Historia y recomendaciones (data storytelling) — Responsable: grupal.

Narrativa guiada en 4 pasos: contexto → tensión → hallazgos → acción.
Usa SIEMPRE el año completo (no aplica los filtros) para que el relato sea estable
durante la presentación. Las cifras se calculan en vivo desde los datos, con las mismas
funciones que el Resumen (src/hallazgos.py), y las recomendaciones son las del notebook.
"""
import plotly.graph_objects as go
import streamlit as st

from src.datos import ORDEN_PLAN
from src.graficos import (COLOR_ACENTO, COLOR_ACENTO_POS, COLOR_LINEA, COLOR_NEUTRO, barras,
                          estilo, mostrar)
from src.hallazgos import anio_completo, fig_segmentos_tecnicos, hallazgos_clave, puntuacion_por_genero
from src.kpis import fmt_num, fmt_pct, kpis_generales, serie_mensual, tasa_cancelacion_por

d = anio_completo()
h = hallazgos_clave()
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
with c1.container(border=True):
    st.metric("Minutos vistos en 2025", fmt_num(k["minutos"]))
    st.metric("Diciembre vs. abril", f"+{fmt_num(var_abr_dic, 0)}%")
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
with c1.container(border=True):
    st.metric("Cancelaciones en enero", fmt_num(cancel[1]))
    st.metric("Cancelaciones en diciembre", fmt_num(cancel[12]))
    st.metric("Ocurridas en el 2° semestre", f"{fmt_num(pct_h2, 0)}%")
    st.metric("Ingreso mensual perdido", f"USD {fmt_num(k['ingreso_perdido'])}",
              help=f"{fmt_pct(k['ingreso_perdido'] / k['ingreso_potencial'])} del ingreso mensual "
                   "potencial: el precio de las suscripciones canceladas.")
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
st.header("3. Hallazgos: quién se va, dónde falla la experiencia y qué contenido funciona")

st.subheader("La fuga se concentra en el plan Básico, y el motivo más declarado es el poco uso")
col_a, col_b = st.columns(2)
with col_a:
    por_plan = tasa_cancelacion_por(usuarios, "plan")
    mostrar(barras(por_plan, "plan", "tasa", titulo="Tasa de cancelación por plan",
                   eje_valor="% canceladas", sufijo="%", destacar="Básico", orden=ORDEN_PLAN))
with col_b:
    cancel_basico = usuarios.loc[(usuarios["estado"] == "Cancelada") & (usuarios["plan"] == "Básico")]
    motivos = (cancel_basico["motivo_cancelacion"]
               .value_counts(normalize=True).mul(100).rename_axis("motivo")
               .reset_index(name="pct").sort_values("pct"))
    mostrar(barras(motivos, "motivo", "pct", titulo="Motivos declarados de cancelación (plan Básico)",
                   eje_valor="% de las cancelaciones", sufijo="%", decimales=0,
                   destacar=motivos.iloc[-1]["motivo"]))
st.caption(f"El plan Básico aporta el {fmt_num(h['basico_pct_cancelaciones'])}% de las cancelaciones. "
           "\"Poco uso\" es el motivo declarado, no una causa probada: quienes cancelan estuvieron "
           "activos 5,8 meses en promedio en 2025, contra 10,2 de quienes siguen activos.")

st.subheader("La experiencia falla en móviles, y sobre todo en Android con la app antigua")
col_a, col_b = st.columns([3, 1])
with col_a:
    mostrar(fig_segmentos_tecnicos(
        rep, titulo=f"El {fmt_num(h['android_pct_reproducciones'], 0)}% de las reproducciones concentra "
                    f"el {fmt_num(h['android_pct_abandonos'], 0)}% de los abandonos tempranos"))
with col_b.container(border=True):
    st.metric("Buffering en Android con app 6.8–6.9", f"{fmt_num(h['android_buffering'], 1)} s")
    st.metric("Buffering en otros móviles y tablets", f"{fmt_num(h['portatil_buffering'], 1)} s")
st.caption(f"El móvil tiene el {fmt_num(h['movil_pct_reproducciones'])}% de las reproducciones y el "
           f"{fmt_num(h['movil_pct_abandonos'])}% de los abandonos; dentro de él, el problema se concentra "
           f"en {fmt_num(h['android_dispositivos'])} dispositivos Android con app anterior a la 7.0, "
           "y la versión que lo corrige ya existe. Ojo: la mala experiencia técnica reduce el consumo, "
           f"pero no explica las cancelaciones (entre cuartiles de buffering la cancelación solo va de "
           f"{fmt_num(h['churn_cuartil_min'], 1)}% a {fmt_num(h['churn_cuartil_max'], 1)}%, sin tendencia, "
           f"y \"Problemas técnicos\" es el {fmt_num(h['pct_problemas_tecnicos'], 1)}% de los motivos).")

st.subheader("El contenido mejor calificado es el menos visto")
generos = puntuacion_por_genero(rep, d["calificaciones"])
mejores = [g["genero_principal"] for g in h["mejor_calificados"]]
fig = barras(generos, "genero_principal", "puntuacion", titulo="Puntuación promedio por género",
             eje_valor="Puntuación promedio (1 a 5)", decimales=2, destacar=mejores,
             color_destacado=COLOR_ACENTO_POS,
             textos=[f"{fmt_num(p, 2)} · {fmt_num(r)} reproducciones"
                     for p, r in zip(generos["puntuacion"], generos["reproducciones"])])
fig.update_xaxes(range=[0, 6.3], tickvals=[0, 1, 2, 3, 4, 5])
mostrar(fig)
st.caption(f"Los gustos son parejos por edad y país (la mezcla de géneros, formatos e idiomas no se aleja "
           f"más de {fmt_num(h['pref_desviacion_max'], 1)} puntos del total): no hace falta segmentar el "
           "catálogo, sino dar más visibilidad a lo que ya se valora bien.")

st.subheader("Quien termina un contenido lo califica mejor")
rep_par = rep.groupby(["usuario_id", "contenido_id"])["porcentaje_completado"].mean().reset_index()
cal_par = d["calificaciones"].merge(rep_par, on=["usuario_id", "contenido_id"])
por_punt = (cal_par.groupby("puntuacion_1_5")
                   .agg(pct=("porcentaje_completado", "mean"), n=("calificacion_id", "count"))
                   .reset_index())
por_punt["puntuacion"] = por_punt["puntuacion_1_5"].astype(str)
mostrar(barras(por_punt, "puntuacion", "pct", horizontal=False,
               titulo="% completado según la puntuación otorgada al mismo contenido",
               eje_valor="% completado promedio", sufijo="%",
               destacar=por_punt["puntuacion"].iloc[-1], color_destacado=COLOR_ACENTO_POS,
               textos=[f"{fmt_num(p, 1)}% · n={fmt_num(n)}"
                       for p, n in zip(por_punt["pct"], por_punt["n"])]))
st.caption("La nota 2 tiene muy pocos casos; la lectura se apoya en las notas 3 a 5. Un \"Me gusta\" "
           "casi no cambia la nota (3,97 vs. 3,96): el % completado es mejor señal de satisfacción.")

# ================================================================ 4. Acción
st.header("4. Acción: recomendaciones")
st.markdown(f"""
| # | Recomendación | Hallazgo que la respalda | KPI de seguimiento | Área |
| --- | --- | --- | --- | --- |
| 1 | **Retener al plan Básico** con campañas de reactivación y beneficios de upgrade, antes del 2.º semestre | Básico cancela {fmt_num(h['tasa_basico'], 1)}% y aporta el {fmt_num(h['basico_pct_cancelaciones'])}% de las cancelaciones; la fuga se acelera en el 2.º semestre | Tasa de cancelación mensual del plan Básico | Retención y Marketing |
| 2 | **Forzar la actualización a la versión 7.0** en Android con app 6.8–6.9 | {fmt_num(h['android_pct_reproducciones'], 1)}% de las reproducciones y {fmt_num(h['android_pct_abandonos'])}% de los abandonos; la 7.0 baja el buffering de ~22 s a ~10 s | % de reproducciones en versiones anteriores a la 7.0 y abandono temprano en móvil | Producto y Tecnología |
| 3 | **Revisar la red de distribución (CDN) en Perú y Ecuador** | {fmt_num(h['buffering_alto_foco'])}% de sus sesiones supera los 15 s de buffering, contra {fmt_num(h['buffering_alto_resto'])}% en el resto, en todo tipo de dispositivo | % de sesiones con buffering >15 s por país | Tecnología |
| 4 | **Dar más visibilidad a Documental y Animación** y evaluar el catálogo por rendimiento por título | Son los géneros mejor calificados ({fmt_num(h['mejor_calificados'][0]['puntuacion'], 2)} y {fmt_num(h['mejor_calificados'][1]['puntuacion'], 2)}) y los menos vistos | Reproducciones por título y puntuación | Contenido |
| 5 | **Usar el % completado como señal de satisfacción** y cruzarlo con reproducciones y puntuación para portada y licencias | Sube de {fmt_num(h['completado_nota3'], 1)}% (nota 3) a {fmt_num(h['completado_nota5'], 1)}% (nota 5); solo el {fmt_num(h['pct_reproducciones_calificadas'], 1)}% de las reproducciones tiene una calificación | % completado por título | Producto y Contenido |
""")
st.caption("Correlación no es causalidad: las recomendaciones 1 y 2 deberían probarse primero con un grupo "
           "piloto y medirse con su KPI antes de extenderlas. Datos ficticios con fines pedagógicos.")

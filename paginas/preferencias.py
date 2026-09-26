"""Página 5 · Preferencias de contenido — Responsable: [Tu Nombre].

Secciones del notebook: "Preferencias de contenido".
Tablas: reproducciones, contenidos, usuarios, calificaciones.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.datos import ORDEN_SEGMENTO, sin_datos
from src.graficos import (COLOR_ACENTO_POS, COLOR_CATEGORICO, barras, estilo, hallazgo,
                          mostrar, ver_tabla)
from src.kpis import fmt_num

d = st.session_state["datos"]
rep = d["reproducciones"]
cont = d["contenidos"]
usu = d["usuarios"]
cal = d["calificaciones"]

st.title("Preferencias de contenido")
st.caption("¿Qué géneros y formatos capturan la mayor atención según el segmento?")

if sin_datos(rep) or sin_datos(cont):
    st.stop()

# ---------------------------------------------------------------- géneros más consumidos
st.header("1. Géneros más consumidos según tiempo invertido")

# SOLUCIÓN AL ERROR: Solo traemos las columnas de 'cont' que no existan ya en 'rep' para evitar los sufijos _x e _y
cols_cont_necesarias = [c for c in cont.columns if c not in rep.columns or c == "contenido_id"]
rep_cont = rep.merge(cont[cols_cont_necesarias], on="contenido_id", how="left")

top_generos = (rep_cont.groupby("genero_principal")
               .agg(minutos=("minutos_reproducidos", "sum"))
               .reset_index()
               .sort_values("minutos", ascending=False).head(5)
               .sort_values("minutos"))  # Orden ascendente para el gráfico horizontal
top_generos["min_txt"] = top_generos["minutos"].map(lambda v: fmt_num(v, 0))

mejor_genero = top_generos.iloc[-1]["genero_principal"]

mostrar(barras(top_generos, "genero_principal", "minutos", 
               titulo="Top 5 géneros más consumidos (Total minutos vistos)",
               eje_valor="Minutos reproducidos", destacar=mejor_genero,
               color_destacado=COLOR_ACENTO_POS,
               hover={"Minutos vistos": "min_txt"}))

hallazgo("Se observa un género que lidera ampliamente en retención de atención, mientras que "
         "los demás mantienen niveles más uniformes. Este género es el pilar principal del "
         "engagement en la plataforma, justificando priorizar la inversión del presupuesto de "
         "adquisición y producción en él.")

ver_tabla(top_generos.sort_values("minutos", ascending=False)
          .rename(columns={"genero_principal": "Género Principal", "minutos": "Minutos totales"})
          [["Género Principal", "Minutos totales"]])

# ---------------------------------------------------------------- preferencia de formato
st.divider()
st.header("2. Preferencia de formato por segmento de edad")

if not sin_datos(usu):
    # SOLUCIÓN: Solo cruzamos segmento_edad si no venía ya pre-cargado
    cols_usu_necesarias = ["usuario_id"]
    if "segmento_edad" not in rep_cont.columns:
        cols_usu_necesarias.append("segmento_edad")
        
    rep_cont_usu = rep_cont.merge(usu[cols_usu_necesarias], on="usuario_id", how="left")
    
    pref_edad = (rep_cont_usu.groupby(["segmento_edad", "tipo_contenido"])
                 .size().reset_index(name="reproducciones"))

    fig = go.Figure()
    tipos = sorted(pref_edad["tipo_contenido"].unique())
    # Identidad, no bueno/malo: cada tipo de contenido lleva su propio color fijo
    # del trío categórico (validado para distinguirse entre sí, no solo del vecino).

    # Iterar sobre cada tipo de contenido para crear las barras agrupadas
    for i, tipo in enumerate(tipos):
        df_tipo = pref_edad[pref_edad["tipo_contenido"] == tipo].set_index("segmento_edad")
        y_vals = [df_tipo.loc[seg, "reproducciones"] if seg in df_tipo.index else 0 for seg in ORDEN_SEGMENTO]

        fig.add_trace(go.Bar(
            x=ORDEN_SEGMENTO, y=y_vals, name=tipo,
            marker_color=COLOR_CATEGORICO[i % len(COLOR_CATEGORICO)],
            hovertemplate="%{x}: " + tipo + "<br>Reproducciones: %{y}<extra></extra>"
        ))

    fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.1)
    fig.update_yaxes(title_text="Cantidad de reproducciones")
    fig.update_xaxes(title_text="Segmento de Edad", showgrid=False)
    mostrar(estilo(fig, "Consumo de formato por cohorte demográfica"))

    hallazgo("Existe una clara segmentación en la forma de consumir contenido; los distintos "
             "grupos de edad tienen proporciones diferentes en la elección de Series frente a "
             "Películas. El catálogo no es 'talla única', y sugerimos personalizar el Home "
             "durante el onboarding destacando el formato preferido de cada segmento.")

    tabla_edad = (pref_edad.pivot(index="segmento_edad", columns="tipo_contenido", values="reproducciones")
                  .fillna(0).reindex(ORDEN_SEGMENTO).reset_index()
                  .rename(columns={"segmento_edad": "Segmento de edad"}))
    ver_tabla(tabla_edad)
else:
    st.info("Datos de usuarios no disponibles para cruzar edad.")

# ---------------------------------------------------------------- satisfacción y valoración
st.divider()
st.header("3. Satisfacción del usuario: Géneros mejor calificados")

if not sin_datos(cal):
    # SOLUCIÓN: Evitar duplicados también con las calificaciones
    cols_cont_cal = [c for c in cont.columns if c not in cal.columns or c == "contenido_id"]
    calif_cont = cal.merge(cont[cols_cont_cal], on="contenido_id", how="left")
    
    calif_gen = (calif_cont.groupby("genero_principal")
                 .agg(promedio_calificacion=("puntuacion_1_5", "mean"),
                      volumen_calificaciones=("puntuacion_1_5", "count"))
                 .reset_index())
    
    # Filtrar muestras pequeñas
    calif_gen_robusto = calif_gen[calif_gen["volumen_calificaciones"] > 30]
    top_calificados = (calif_gen_robusto.sort_values("promedio_calificacion", ascending=False).head(5)
                       .sort_values("promedio_calificacion"))

    if not top_calificados.empty:
        mejor_calificado = top_calificados.iloc[-1]["genero_principal"]
        top_calificados["prom_txt"] = top_calificados["promedio_calificacion"].map(lambda v: fmt_num(v, 2))
        top_calificados["vol_txt"] = top_calificados["volumen_calificaciones"].map(lambda v: fmt_num(v, 0))

        fig_calif = barras(top_calificados, "genero_principal", "promedio_calificacion",
                           titulo="Top 5 géneros con mayor calificación promedio",
                           eje_valor="Calificación promedio", destacar=mejor_calificado,
                           color_destacado=COLOR_ACENTO_POS,
                           hover={"Calificación": "prom_txt", "N° Evaluaciones": "vol_txt"})
        
        # Fijar límite del eje X de 0 a 5
        fig_calif.update_xaxes(range=[0, 5])
        mostrar(fig_calif)

        hallazgo("Los géneros con mejor puntuación no siempre coinciden con los géneros más "
                 "reproducidos masivamente. Hay nichos de contenido de alta calidad que fidelizan "
                 "enormemente a quienes los consumen. Ideal usar estos contenidos en campañas de "
                 "retención de usuarios en riesgo de churn.")

        ver_tabla(top_calificados.sort_values("promedio_calificacion", ascending=False)
                  .rename(columns={"genero_principal": "Género Principal", 
                                   "promedio_calificacion": "Calificación prom.",
                                   "volumen_calificaciones": "N° Evaluaciones"})
                  [["Género Principal", "Calificación prom.", "N° Evaluaciones"]].round(2))
    else:
        st.info("No hay suficientes géneros con más de 30 calificaciones para mostrar un top sólido.")
else:
    st.info("No hay datos de calificaciones disponibles.")
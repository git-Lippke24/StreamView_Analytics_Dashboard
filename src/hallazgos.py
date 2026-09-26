"""Hallazgos clave del año completo y cálculos compartidos entre páginas.

Resumen, Historia y las páginas de análisis usan estas funciones para que una
misma cifra se calcule de una sola forma, con las definiciones del notebook.
Los hallazgos clave usan siempre el año completo (sin los filtros de la barra
lateral) para que el relato de la presentación sea estable.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.datos import ORDEN_PLAN, ORDEN_SEGMENTO, cargar_datos, filtrar
from src.graficos import COLOR_ACENTO, COLOR_NEUTRO, COLOR_NEUTRO_OSCURO, estilo
from src.kpis import UMBRAL_BUFFERING, fmt_num, tasa_cancelacion_por

# Segmentos técnicos del notebook (4.4.1): Android con app anterior a la 7.0 es el foco
SEG_FIJO = "Dispositivos fijos"
SEG_PORTATIL = "Otros portátiles"
SEG_ANDROID = "Android con app 6.8–6.9"
SEGMENTOS_TECNICOS = [SEG_FIJO, SEG_PORTATIL, SEG_ANDROID]
PAISES_FOCO = ["Perú", "Ecuador"]


def anio_completo() -> dict[str, pd.DataFrame]:
    """Todas las tablas de 2025, sin los filtros de la barra lateral."""
    datos = cargar_datos()
    return filtrar(datos, meses=(1, 12), paises=sorted(datos["usuarios"]["pais"].unique()),
                   planes=ORDEN_PLAN, segmentos=ORDEN_SEGMENTO)


def segmento_tecnico(rep: pd.DataFrame) -> pd.Series:
    """Segmento técnico de cada reproducción: fijos, otros portátiles o Android 6.8–6.9."""
    portatil = rep["tipo_dispositivo"].isin(["Móvil", "Tablet"])
    android_antigua = rep["sistema_operativo"].eq("Android") & rep["version_app"].isin(["6.8", "6.9"])
    return pd.Series(np.select([android_antigua, portatil], [SEG_ANDROID, SEG_PORTATIL],
                               default=SEG_FIJO), index=rep.index)


def participacion_segmentos(rep: pd.DataFrame) -> pd.DataFrame:
    """% de las reproducciones y de los abandonos tempranos que aporta cada segmento técnico."""
    seg = segmento_tecnico(rep)
    abandono = rep["abandono_temprano"].eq("Sí")
    return (pd.DataFrame({
        "Reproducciones": seg.value_counts(normalize=True),
        "Abandonos tempranos": seg[abandono].value_counts(normalize=True),
    }).reindex(SEGMENTOS_TECNICOS).fillna(0) * 100)


def fig_segmentos_tecnicos(rep: pd.DataFrame, titulo: str) -> go.Figure:
    """Dos barras 100% apiladas: si un segmento fuera "normal", su trozo mediría lo mismo en ambas."""
    part = participacion_segmentos(rep)
    colores = {SEG_FIJO: COLOR_NEUTRO, SEG_PORTATIL: COLOR_NEUTRO_OSCURO, SEG_ANDROID: COLOR_ACENTO}
    fig = go.Figure()
    for seg in SEGMENTOS_TECNICOS:
        valores = part.loc[seg]
        fig.add_trace(go.Bar(
            y=part.columns, x=valores, name=seg, orientation="h", marker_color=colores[seg],
            marker_line=dict(color="white", width=2),
            text=[f"{fmt_num(v, 1 if v < 10 else 0)}%" for v in valores], textposition="auto",
            cliponaxis=False,
            hovertemplate=f"<b>{seg}</b><br>%{{y}}: %{{x:.1f}}%<extra></extra>",
        ))
    fig.update_layout(barmode="stack", bargap=0.35)
    fig.update_xaxes(range=[0, 108], tickvals=[0, 25, 50, 75, 100], ticksuffix="%", showgrid=False)
    fig.update_yaxes(autorange="reversed", type="category")
    return estilo(fig, titulo, alto=260)


def desviacion_maxima(rep: pd.DataFrame, grupo: str, variable: str) -> float:
    """Máxima distancia (en puntos %) entre la mezcla de `variable` de un grupo y la del total."""
    mezcla = pd.crosstab(rep[grupo], rep[variable], normalize="index")
    total = rep[variable].value_counts(normalize=True)
    return float((mezcla - total).abs().max().max() * 100)


def puntuacion_por_genero(rep: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame:
    """Puntuación promedio, N° de calificaciones y reproducciones por género (orden ascendente)."""
    return (cal.groupby("genero_principal")
               .agg(puntuacion=("puntuacion_1_5", "mean"), calificaciones=("calificacion_id", "count"))
               .join(rep.groupby("genero_principal").size().rename("reproducciones"))
               .fillna({"reproducciones": 0})
               .reset_index()
               .sort_values("puntuacion"))


@st.cache_data(show_spinner=False)
def hallazgos_clave() -> dict:
    """Las cifras de un hallazgo por línea de análisis, con todo 2025 (notebook, sección 4)."""
    d = anio_completo()
    usu, rep, cal = d["usuarios"], d["reproducciones"], d["calificaciones"]
    abandono = rep["abandono_temprano"].eq("Sí")
    h = {}

    # 4.1 Retención
    por_plan = tasa_cancelacion_por(usu, "plan").set_index("plan")
    h["tasa_basico"] = por_plan.loc["Básico", "tasa"]
    h["tasa_premium"] = por_plan.loc["Premium", "tasa"]
    h["basico_pct_cancelaciones"] = por_plan.loc["Básico", "canceladas"] / por_plan["canceladas"].sum() * 100
    canceladas = usu[usu["estado"] == "Cancelada"]
    h["pct_problemas_tecnicos"] = canceladas["motivo_cancelacion"].eq("Problemas técnicos").mean() * 100

    # 4.2 Consumo por dispositivo
    movil = rep["tipo_dispositivo"].eq("Móvil")
    h["movil_pct_reproducciones"] = movil.mean() * 100
    h["movil_pct_abandonos"] = movil[abandono].mean() * 100
    h["movil_pct_completado"] = rep.loc[movil, "porcentaje_completado"].mean()

    # 4.3 Preferencias
    h["pref_desviacion_max"] = max(desviacion_maxima(rep, grupo, var)
                                   for grupo in ["segmento_edad", "pais"]
                                   for var in ["genero_principal", "tipo_contenido", "idioma_original"])
    generos = puntuacion_por_genero(rep, cal)
    generos["puesto_reproducciones"] = generos["reproducciones"].rank(ascending=False, method="min").astype(int)
    h["n_generos"] = len(generos)
    h["mejor_calificados"] = generos.nlargest(2, "puntuacion")[
        ["genero_principal", "puntuacion", "reproducciones", "puesto_reproducciones"]].to_dict("records")

    # 4.4 Experiencia técnica
    seg = segmento_tecnico(rep)
    android = seg.eq(SEG_ANDROID)
    h["android_pct_reproducciones"] = android.mean() * 100
    h["android_pct_abandonos"] = android[abandono].mean() * 100
    h["android_dispositivos"] = rep.loc[android, "dispositivo_id"].nunique()
    h["android_buffering"] = rep.loc[android, "buffering_segundos"].mean()
    h["portatil_buffering"] = rep.loc[seg.eq(SEG_PORTATIL), "buffering_segundos"].mean()
    alto = rep["buffering_segundos"].gt(UMBRAL_BUFFERING)
    foco = rep["pais"].isin(PAISES_FOCO)
    h["buffering_alto_foco"] = alto[foco].mean() * 100
    h["buffering_alto_resto"] = alto[~foco].mean() * 100
    por_usuario = (rep.groupby("usuario_id")["buffering_segundos"].mean().rename("buffering").reset_index()
                      .merge(usu[["usuario_id", "estado"]], on="usuario_id"))
    cuartil = pd.qcut(por_usuario["buffering"], 4, labels=False)
    churn = por_usuario["estado"].eq("Cancelada").groupby(cuartil).mean() * 100
    h["churn_cuartil_min"], h["churn_cuartil_max"] = churn.min(), churn.max()

    # 4.5 Satisfacción: cada calificación con el % completado del mismo usuario en el mismo contenido
    rep_par = rep.groupby(["usuario_id", "contenido_id"])["porcentaje_completado"].mean().reset_index()
    cal_par = cal.merge(rep_par, on=["usuario_id", "contenido_id"])
    por_nota = cal_par.groupby("puntuacion_1_5")["porcentaje_completado"].mean()
    h["completado_nota3"], h["completado_nota5"] = por_nota[3], por_nota[5]
    pares_calificados = cal[["usuario_id", "contenido_id"]].drop_duplicates().assign(calificado=True)
    h["pct_reproducciones_calificadas"] = (rep[["usuario_id", "contenido_id"]]
                                           .merge(pares_calificados, how="left")["calificado"]
                                           .notna().mean() * 100)
    return h

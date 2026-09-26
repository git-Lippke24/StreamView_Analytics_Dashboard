"""KPIs y agregados compartidos entre páginas.

Las definiciones son las mismas del notebook, para que las cifras coincidan.
"""
from __future__ import annotations

import pandas as pd

from src.datos import MESES

# Segundos de buffering sobre los que el abandono temprano se dispara (notebook 4.4.2)
UMBRAL_BUFFERING = 15


def kpis_generales(d: dict) -> dict[str, float]:
    """KPIs de cabecera sobre las tablas ya filtradas."""
    usu, rep, cal = d["usuarios"], d["reproducciones"], d["calificaciones"]
    activas = usu["estado"].eq("Activa")
    return {
        "usuarios": len(usu),
        "activas": int(activas.sum()),
        "canceladas": int((~activas).sum()),
        "tasa_cancelacion": usu["estado"].eq("Cancelada").mean(),
        "ingreso_mensual": usu.loc[activas, "precio_mensual_usd"].sum(),
        "ingreso_perdido": usu.loc[~activas, "precio_mensual_usd"].sum(),
        "ingreso_potencial": usu["precio_mensual_usd"].sum(),
        "reproducciones": len(rep),
        "minutos": rep["minutos_reproducidos"].sum(),
        "pct_completado": rep["porcentaje_completado"].mean(),
        "tasa_abandono": rep["abandono_temprano"].eq("Sí").mean(),
        "buffering": rep["buffering_segundos"].mean(),
        "pct_buffering_alto": rep["buffering_segundos"].gt(UMBRAL_BUFFERING).mean(),
        "puntuacion": cal["puntuacion_1_5"].mean(),
        "tasa_recomienda": cal["recomendaria"].eq("Sí").mean(),
    }


def serie_mensual(d: dict) -> pd.DataFrame:
    """Reproducciones, minutos, usuarios activos y cancelaciones por mes del rango."""
    desde, hasta = d["meses"]
    meses = pd.Index(range(desde, hasta + 1), name="mes")
    rep = d["reproducciones"]
    consumo = rep.groupby("mes").agg(
        reproducciones=("reproduccion_id", "count"),
        minutos=("minutos_reproducidos", "sum"),
        usuarios_activos=("usuario_id", "nunique"),
    )
    cancel = d["usuarios"].groupby("mes_cancelacion").size().rename("cancelaciones")
    cancel.index = cancel.index.astype(int)
    serie = consumo.join(cancel, how="outer").reindex(meses).fillna(0).reset_index()
    serie["mes_nombre"] = serie["mes"].map(lambda m: MESES[m - 1])
    return serie


def tasa_cancelacion_por(usuarios: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Usuarios, canceladas y tasa de cancelación por categoría de `columna`."""
    return (usuarios.groupby(columna)
                    .agg(usuarios=("usuario_id", "count"),
                         canceladas=("estado", lambda s: s.eq("Cancelada").sum()))
                    .assign(tasa=lambda t: t["canceladas"] / t["usuarios"] * 100)
                    .reset_index())


def fmt_num(valor: float, decimales: int = 0) -> str:
    """Número con formato chileno: 1.423.491 · 3,96."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_pct(proporcion: float, decimales: int = 1) -> str:
    """Proporción (0-1) como porcentaje con coma decimal: 0.277 -> '27,7%'."""
    return f"{fmt_num(proporcion * 100, decimales)}%"

"""Carga, uniones y filtros del dataset StreamView Analytics.

Toda la preparación de datos vive aquí para que las páginas del dashboard
(y el notebook, si se quiere) usen exactamente las mismas tablas.

Uso en una página:
    d = st.session_state["datos"]          # tablas ya filtradas por la barra lateral
    rep = d["reproducciones"]
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
ORDEN_PLAN = ["Básico", "Estándar", "Premium"]
ORDEN_SEGMENTO = ["18-24", "25-34", "35-44", "45-54", "55+"]
ORDEN_CALIDAD = ["SD", "HD", "Full HD", "4K"]

# Columnas del usuario (incluye su suscripción) que se copian a las tablas de hechos
# para poder filtrar por país, plan y segmento en cualquier página.
_ATRIBUTOS_USUARIO = ["usuario_id", "pais", "segmento_edad", "canal_adquisicion", "plan", "estado"]
_ATRIBUTOS_CONTENIDO = ["contenido_id", "titulo", "tipo_contenido", "genero_principal",
                        "idioma_original", "exclusivo"]


def _leer(nombre: str, fechas: list[str] | None = None) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / f"{nombre}.csv", parse_dates=fechas)


@st.cache_data(show_spinner="Cargando datos…")
def cargar_datos() -> dict[str, pd.DataFrame]:
    """Lee los 7 CSV y devuelve las tablas enriquecidas (sin filtrar).

    - usuarios: cada usuario con su suscripción (hay exactamente una por usuario).
    - reproducciones, calificaciones, interacciones: con atributos del usuario,
      del contenido y la columna `mes` (1 a 12) para filtrar por período.
    """
    usuarios = _leer("usuarios", ["fecha_registro"])
    suscripciones = _leer("suscripciones", ["fecha_inicio", "fecha_fin"])
    contenidos = _leer("contenidos", ["fecha_alta_catalogo"])
    dispositivos = _leer("dispositivos", ["fecha_registro_dispositivo"])
    reproducciones = _leer("reproducciones", ["fecha_hora_inicio"])
    calificaciones = _leer("calificaciones", ["fecha_calificacion"])
    interacciones = _leer("interacciones", ["fecha_hora"])

    # versión de app como texto ("7.2"), no como número decimal
    dispositivos["version_app"] = dispositivos["version_app"].map(lambda v: f"{v:.1f}")

    usuarios = usuarios.merge(suscripciones, on="usuario_id", how="left")
    usuarios["mes_cancelacion"] = usuarios["fecha_fin"].dt.month  # vacío si sigue activa

    atrib_usr = usuarios[_ATRIBUTOS_USUARIO]
    atrib_cont = contenidos[_ATRIBUTOS_CONTENIDO]

    reproducciones = (
        reproducciones
        .merge(atrib_usr, on="usuario_id", how="left")
        .merge(atrib_cont, on="contenido_id", how="left")
        .merge(dispositivos[["dispositivo_id", "sistema_operativo", "version_app"]],
               on="dispositivo_id", how="left")
    )
    reproducciones["mes"] = reproducciones["fecha_hora_inicio"].dt.month

    calificaciones = (calificaciones.merge(atrib_usr, on="usuario_id", how="left")
                                    .merge(atrib_cont, on="contenido_id", how="left"))
    calificaciones["mes"] = calificaciones["fecha_calificacion"].dt.month

    interacciones = (interacciones.merge(atrib_usr, on="usuario_id", how="left")
                                  .merge(atrib_cont, on="contenido_id", how="left"))
    interacciones["mes"] = interacciones["fecha_hora"].dt.month

    return {
        "usuarios": usuarios,
        "contenidos": contenidos,
        "dispositivos": dispositivos,
        "reproducciones": reproducciones,
        "calificaciones": calificaciones,
        "interacciones": interacciones,
    }


def filtrar(datos: dict[str, pd.DataFrame], meses: tuple[int, int], paises: list[str],
            planes: list[str], segmentos: list[str]) -> dict[str, pd.DataFrame]:
    """Aplica los filtros globales de la barra lateral.

    - País, plan y segmento filtran todas las tablas.
    - El rango de meses filtra reproducciones, calificaciones e interacciones.
      `usuarios` no se filtra por mes: su estado es el del cierre (31-12-2025).
    """
    def del_usuario(df: pd.DataFrame) -> pd.Series:
        return (df["pais"].isin(paises) & df["plan"].isin(planes)
                & df["segmento_edad"].isin(segmentos))

    desde, hasta = meses
    salida = {
        "usuarios": datos["usuarios"][del_usuario(datos["usuarios"])],
        "contenidos": datos["contenidos"],
        "dispositivos": datos["dispositivos"],
        "meses": (desde, hasta),
    }
    for tabla in ("reproducciones", "calificaciones", "interacciones"):
        df = datos[tabla]
        salida[tabla] = df[del_usuario(df) & df["mes"].between(desde, hasta)]
    return salida


def sin_datos(df: pd.DataFrame, minimo: int = 1) -> bool:
    """Muestra un aviso y devuelve True si el filtro dejó la tabla vacía."""
    if len(df) < minimo:
        st.info("No hay datos suficientes para esta vista con los filtros seleccionados.")
        return True
    return False

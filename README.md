# StreamView Analytics Dashboard

Dashboard interactivo en Streamlit sobre **StreamView Analytics**, una plataforma de streaming ficticia (datos 2025): retención, consumo, experiencia técnica, preferencias y satisfacción. Trabajo colaborativo de **ADY1104 Visualización de Datos (Duoc UC)**, Evaluación Parcial 1: narrativa visual y storytelling para comunicar hallazgos a un público objetivo.

**App en línea:** _pendiente de despliegue_ (agregar aquí el enlace `https://….streamlit.app`)

---

## Contexto académico

| Sigla | Asignatura | Créditos SCT | Créditos Duoc | Formato | Línea formativa |
|---|---|---|---|---|---|
| ADY1104 | Visualización de Datos | 4 | 10 | Presencial | Análisis de Datos |

**Resultado de aprendizaje (RA1).** Desarrolla narrativas creativas para explicar casos de ciencia de datos a un público objetivo, utilizando técnicas de comunicación oral, escrita y visual.

| Indicador de logro | Descripción | Dónde se trabaja en este proyecto |
|---|---|---|
| IL1.1 | Identifica audiencias y objetivos de comunicación para adaptar narrativas visuales según el contexto de análisis y el público objetivo. | Audiencia definida (comité de Producto y Retención) y propósito informativo y persuasivo: notebook y página **Historia y recomendaciones**. |
| IL1.2 | Aplica principios de percepción visual y cognición para favorecer la interpretación y comprensión de información cuantitativa. | Color de acento solo en la categoría relevante sobre gris neutro, barras ordenadas, sin doble eje Y y etiquetas directas (`src/graficos.py`). |
| IL1.3 | Selecciona tipologías de gráficos, atributos visuales y formas de representación considerando el tipo de dato y el propósito comunicacional. | Líneas para tiempo, barras para comparar, histograma para distribuciones, dispersión para relaciones, mapa de calor para correlaciones y tarjetas para KPIs. |
| IL1.4 | Construye narrativas visuales integrando técnicas de storytelling y recursos de comunicación oral, escrita y visual para comunicar hallazgos analíticos. | Página **Historia y recomendaciones**: contexto → tensión → hallazgos → acción, más la presentación oral del equipo. |

---

## El caso

StreamView Analytics es una plataforma ficticia de streaming digital. El dataset permite analizar retención de clientes, engagement, preferencias de consumo, uso de dispositivos, calidad de experiencia y valoración de contenidos.

- **Período principal de análisis:** 01-01-2025 al 31-12-2025.
- **Pregunta de negocio:** ¿qué combinación de contenido, dispositivo y experiencia de uso mantiene a un usuario reproduciendo, interactuando y suscrito?

### Dataset

| Tabla | Registros | Contenido |
|---|---|---|
| `usuarios.csv` | 1.500 | País, ciudad, edad, segmento, género y canal de adquisición |
| `contenidos.csv` | 420 | Tipo, género, idioma, duración, exclusividad |
| `suscripciones.csv` | 1.500 | Plan, fechas, estado, precio y motivo de cancelación |
| `dispositivos.csv` | 2.492 | Tipo, sistema operativo y versión de app |
| `reproducciones.csv` | 25.000 | Minutos, % completado, abandono temprano, calidad y buffering |
| `calificaciones.csv` | 3.119 | Puntuación 1 a 5, recomendaría y categoría del comentario |
| `interacciones.csv` | 7.438 | Me gusta, listas, compartir, descargas, clics en recomendaciones |
| `diccionario_datos.csv` | — | Descripción de cada campo |

**Relaciones**

- `usuarios.usuario_id` → `suscripciones`, `dispositivos`, `reproducciones`, `calificaciones`, `interacciones`
- `contenidos.contenido_id` → `reproducciones`, `calificaciones`, `interacciones`
- `dispositivos.dispositivo_id` → `reproducciones.dispositivo_id`

**Importante**

- Todos los datos son ficticios y de uso pedagógico.
- El dataset contiene patrones realistas para descubrir tendencias y hallazgos; no se entregan respuestas esperadas.
- `fecha_fin` y `motivo_cancelacion` quedan vacíos cuando la suscripción sigue activa.
- En series, `duracion_min` representa la duración aproximada de un episodio.

El enunciado original del dataset está en [`data/README_dataset.txt`](data/README_dataset.txt).

---

## Líneas de análisis y páginas del dashboard

| Línea de análisis | Página | Responsable | Estado |
|---|---|---|---|
| KPIs y dashboard ejecutivo | Resumen ejecutivo | Grupal | Lista |
| Retención y cancelación por plan, país, segmento y canal | Retención | Sebastian Gonzalez Pino | Lista |
| Reproducciones, minutos vistos, % completado y abandono | Consumo | Hernan Lippke | Lista |
| Experiencia técnica por dispositivo, sistema operativo, app y calidad | Experiencia técnica | Hernan Lippke + por asignar | En progreso |
| Preferencias por género, tipo, idioma, país y segmento | Preferencias | Por asignar | Pendiente |
| Relación entre consumo, interacciones y calificaciones | Satisfacción | Hernan Lippke | Lista |
| Data storytelling y recomendaciones | Historia y recomendaciones | Grupal | En progreso |

---

## Estructura del repositorio

```
StreamView_Analytics_Dashboard/
├── app.py                  # entrada: filtros globales y navegación
├── paginas/                # una página del dashboard por archivo
│   ├── resumen.py
│   ├── retencion.py
│   ├── consumo.py
│   ├── experiencia.py
│   ├── preferencias.py
│   ├── satisfaccion.py
│   └── historia.py
├── src/
│   ├── datos.py            # carga de CSV, uniones y filtros
│   ├── kpis.py             # KPIs y formato de números (1.423.491 · 71,5%)
│   └── graficos.py         # paleta del equipo y ayudas para Plotly
├── data/                   # los 7 CSV + diccionario + enunciado del dataset
├── notebooks/
│   └── EV1_Visualizacion_de_Datos.ipynb
├── docs/capturas/          # capturas del dashboard para el informe
├── scripts/
│   ├── setup.ps1           # crea .venv en Windows
│   └── setup.sh            # crea .venv en Mac / Linux
├── .streamlit/config.toml  # tema y opciones de Streamlit
├── requirements.txt        # dependencias de la app (las usa Streamlit Cloud)
└── requirements-dev.txt    # app + notebook (ipykernel, matplotlib, seaborn)
```

---

## Levantar el entorno de desarrollo

Requisitos: **Python 3.10 o superior (recomendado 3.12)**, Git y VS Code con las extensiones Python y Jupyter. Todo corre dentro de un entorno virtual `.venv` propio de cada integrante, que no se sube al repositorio.

### Windows (PowerShell)

```powershell
git clone https://github.com/git-Lippke24/StreamView_Analytics_Dashboard.git
cd StreamView_Analytics_Dashboard
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

- Si PowerShell bloquea `Activate.ps1`, ejecuta una sola vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- Para usar una versión específica de Python: `powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -Version 3.12`.

### Mac / Linux

```bash
git clone https://github.com/git-Lippke24/StreamView_Analytics_Dashboard.git
cd StreamView_Analytics_Dashboard
bash scripts/setup.sh
source .venv/bin/activate
streamlit run app.py
```

La app se abre en `http://localhost:8501` y se recarga sola al guardar un archivo.

### Notebook

Abre `notebooks/EV1_Visualizacion_de_Datos.ipynb` en VS Code y elige el kernel **Python (StreamView .venv)**. El notebook lee los CSV desde `../data`; en Google Colab usa la carpeta actual.

---

## Agregar o completar una página

1. Crea o edita el archivo en `paginas/`. Una página nueva se registra en la lista `paginas` de `app.py`.
2. Lee los datos ya filtrados: `d = st.session_state["datos"]` (tablas `usuarios`, `reproducciones`, `calificaciones`, `interacciones`, `contenidos`, `dispositivos`).
3. Usa las ayudas de `src/graficos.py` para mantener el estilo: `barras()`, `paneles_mensuales()`, `mostrar()`, `ver_tabla()` y `hallazgo()`.

Convenciones del equipo:

- Título del gráfico descriptivo y el hallazgo debajo, con `hallazgo()`.
- Gris neutro (`COLOR_NEUTRO`) para el resto y un solo color de acento para lo que importa: `COLOR_ACENTO` para alertas y `COLOR_ACENTO_POS` para lo positivo.
- Nunca doble eje Y: dos medidas de distinta escala van en paneles separados.
- Cada gráfico lleva su tabla `ver_tabla()` para leer los valores sin depender del tooltip.

---

## Flujo de trabajo con Git

```bash
git pull                                  # traer lo último antes de empezar
# ... editar tu página ...
git add paginas/retencion.py
git commit -m "Retención: tasa de cancelación por canal"
git push
```

Coordinen antes de editar el mismo archivo al mismo tiempo, en especial el notebook: Git no fusiona bien cambios simultáneos en un `.ipynb`.

---

## Despliegue en Streamlit Community Cloud

1. Entrar a [share.streamlit.io](https://share.streamlit.io) con la cuenta de GitHub.
2. **Create app** → repositorio `git-Lippke24/StreamView_Analytics_Dashboard`, rama `main`, archivo `app.py`.
3. En **Advanced settings** elegir Python 3.12 y desplegar.
4. Pegar la URL resultante al inicio de este README.

Cada `git push` a `main` actualiza la app. Si pasa 12 horas sin visitas se suspende; se reactiva con un clic, así que conviene abrirla unos minutos antes de presentar.

---

## Integrantes

- Matias Arauz
- Michelangelo Bandelli
- Sebastian Gonzalez Pino
- Hernan Lippke

Duoc UC · Ingeniería en Informática · 2026

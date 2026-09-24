STREAMVIEW ANALYTICS — DATASET SINTÉTICO PARA EP1
Asignatura: ADY1104 Visualización de Datos
Período principal de análisis: 01-01-2025 al 31-12-2025

CONTEXTO
StreamView Analytics es una plataforma ficticia de streaming digital. El dataset permite analizar
retención de clientes, engagement, preferencias de consumo, uso de dispositivos, calidad de
experiencia y valoración de contenidos.

TABLAS
usuarios.csv          1,500 registros
contenidos.csv        420 registros
suscripciones.csv     1,500 registros
dispositivos.csv      2,492 registros
reproducciones.csv    25,000 registros
calificaciones.csv    3,119 registros
interacciones.csv     7,438 registros
diccionario_datos.csv descripción de campos

RELACIONES
usuarios.usuario_id -> suscripciones, dispositivos, reproducciones, calificaciones, interacciones
contenidos.contenido_id -> reproducciones, calificaciones, interacciones
dispositivos.dispositivo_id -> reproducciones.dispositivo_id

IMPORTANTE
- Todos los datos son ficticios y de uso pedagógico.
- El dataset contiene patrones realistas para descubrir tendencias y hallazgos.
- No se entregan respuestas ni hallazgos esperados.
- fecha_fin y motivo_cancelacion quedan vacíos cuando la suscripción sigue activa.
- En series, duracion_min representa la duración aproximada de un episodio.

IDEAS DE ANÁLISIS
- Retención/cancelación por plan, país, segmento y canal.
- Reproducciones, minutos vistos, porcentaje completado y abandono.
- Preferencias por género, tipo, idioma, país y segmento.
- Experiencia técnica por dispositivo, sistema operativo, app y calidad.
- Relación entre consumo, interacciones y calificaciones.
- KPIs y dashboard ejecutivo.

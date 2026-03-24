# Registro de Desarrollo y Traspaso (Handoff)

Este documento sirve para mantener un registro continuo de nuestro trabajo, objetivos, decisiones clave y próximos pasos en el proyecto. Se actualizará periódicamente de acuerdo a tus peticiones.

---

## Resumen del Proyecto y Arquitectura

**Datalogger Resultados** es una aplicación de escritorio desarrollada en Python, diseñada para analizar datos de telemetría (datalogger) de motocicletas en diferentes pruebas de rendimiento (Frenado, Aceleración, Ascenso, Recuperación). 

El flujo principal consiste en que el usuario carga archivos CSV generados por el datalogger, selecciona la motocicleta y el piloto, e inicia el análisis. El programa procesa matemáticamente las señales (usando un flanco en la señal `Pulsador == 100` para detectar eventos), calcula métricas (distancia, tiempos, aceleración) e imprime reportes en PDF con tablas y gráficas.

### Estructura de Módulos Principales
* **`main.py`**: Punto de entrada de la aplicación. Gestiona la interfaz gráfica principal usando `customtkinter`. Sirve como contenedor que carga las distintas vistas de pruebas desde la carpeta `modules/`, y administra el registro de pilotos y motos.
* **`data_manager.py`**: Se encarga de la persistencia de datos (motos, pilotos y ranking) guardando y leyendo archivos JSON (`motos.json`, `pilotos.json`, `ranking.json`).
* **`analysis_controller.py`**: El "cerebro" orquestador. Recibe los datos validados desde la UI, llama a `analyzer.py` para hacer los cálculos numéricos, a `plotter.py` para generar las vistas gráficas, y finalmente junta todo para crear el PDF usando `reporter.py`.
* **`analyzer.py`**: El motor matemático basado en `pandas` y `numpy`. Limpia y analiza los CSVs brutos, detectando el inicio exacto de los eventos y calculando integrales (aceleración -> velocidad -> posición).
* **`plotter.py`**: Construye las gráficas (Velocidad vs Tiempo, Aceleración, RPMs, etc.) empleando la librería `matplotlib`.
* **`reporter.py`**: Se encarga de la maquetación y exportación de resultados a formato PDF usando `reportlab`.
* **Carpeta `modules/`**: Contiene las interfaces de usuario (formularios y tablas) separadas para cada tipo de prueba, por ejemplo `braking_test.py`, `acceleration_0_80.py`, etc. 

---

## Sesión: 02 de Marzo de 2026

### 🎯 Objetivo Principal
- Crear y establecer una plantilla base para llevar el registro del proyecto en `docs/HANDOFF.md`.
- Mantener un control claro sobre qué se ha hecho y qué falta por hacer.

### 👤 Peticiones del Usuario (Daniel)
- Crear el documento `docs/HANDOFF.md`.
- Incluir secciones para peticiones, objetivos, decisiones, archivos tocados, comandos ejecutados, pendientes y próximos pasos.
- Incluir un espacio para fragmentos de código (snippets) importantes.

### 🧠 Decisiones Tomadas
- Se ha establecido la estructura base del archivo `HANDOFF.md`. Al inicio de cada sesión de trabajo, crearemos una nueva entrada o actualizaremos la existente manteniendo esta estructura.
- El archivo se alojará en la carpeta `docs` dentro del directorio `Programa Resultados`.

### 📁 Archivos Modificados / Creados
- `[NUEVO]` `docs/HANDOFF.md`

### 💻 Comandos Ejecutados
*(No se han ejecutado comandos de consola en esta sesión inicial)*

### 📝 Snippets Importantes
*(Ningún snippet por el momento, aquí se guardarán configuraciones o bloques clave de código que vayamos desarrollando)*

### ⏳ Pendientes
- Integrar la documentación del estado actual de `main.py` y demás componentes si es necesario.

### 🚀 Próximos Pasos
- Esperar las próximas instrucciones de Daniel sobre qué funcionalidad de `main.py` (o del proyecto en general) vamos a empezar a programar o revisar.

---

## Sesión: 04 de Marzo de 2026

### 🎯 Objetivo Principal
- Implementar la función de **"Previsualizar"** reportes antes de generar el PDF final.

### 👤 Peticiones del Usuario (Daniel)
- Agregar un botón o flujo para poder ver las gráficas y la tabla resumen antes de confirmar la generación del PDF.

### 🧠 Decisiones Tomadas
- Se introdujo `preview_window.py` que contiene `PreviewWindow`, un `CTkToplevel` con scroll para ver imágenes y tablas.
- Se refactorizó `analysis_controller.py`:
  - Los métodos antiguos (`process_data`, `process_acceleration_0_80`, etc.) se dividieron. Ahora hay métodos `evaluate_*` que retornan un diccionario con la información y las gráficas en memoria (`io.BytesIO`).
  - Se unificó la generación de reporte PDF a través del método `generate_pdf(preview_data)`.
- Se actualizaron los módulos de la interfaz (`braking_test.py`, `acceleration_0_80.py`, `climbing_test.py`, `recovery_test.py`) para consumir la nueva lógica de evaluación e invocar `PreviewWindow`.

### 📁 Archivos Modificados / Creados
- `[NUEVO]` `preview_window.py`
- `[NUEVO]` `docs/UI_PREVIEW_DESIGN.md`
- `[NUEVO]` `version.py`
- `[MODIFICADO]` `analysis_controller.py`
- `[MODIFICADO]` `analyzer.py`
- `[MODIFICADO]` `main.py`
- `[MODIFICADO]` `reporter.py`
- `[MODIFICADO]` `plotter.py`
- `[MODIFICADO]` `modules/braking_test.py`
- `[MODIFICADO]` `modules/acceleration_0_80.py`
- `[MODIFICADO]` `modules/climbing_test.py`
- `[MODIFICADO]` `modules/recovery_test.py`

### ✨ Nuevas Correcciones y Modificaciones (Misma Sesión)
- Se eliminó la Velocidad y Dirección del Viento de la interfaz principal (`main.py`) y de los reportes PDF (`reporter.py`).
- Se mejoró el contraste de las tablas en `PreviewWindow` (encabezado azul, fondo blanco).
- Se corrigieron errores como `SettingWithCopyWarning` en `analyzer.py` y `table_segments is not defined` en `analysis_controller.py`.
- Se estableció un estándar fijo para la exportación de archivos (tanto CSV como PDF): `(Prueba)_(Motocicleta)_(Codigo Modelo)_(Piloto)_(Fecha)`.
- Se implementó un control de versiones a través de `version.py` (actualmente en **v1.1.0**). El título de la aplicación principal ahora muestra la versión actual, y los reportes PDF tienen la versión estampada en la esquina inferior derecha.

### 📍 Nueva Función: Control de Lugares de Prueba (v1.1.0)
- Se añadió un sistema de gestión de lugares en `data_manager.py` (guardado en `lugares.json`).
- Nueva interfaz en `main.py` para seleccionar un lugar de prueba de una lista desplegable, junto con un botón para agregar nuevos lugares (Nombre, Altitud, Coordenadas).
- Se implementó la validación estricta: es obligatorio seleccionar un lugar para poder generar reportes o visualizarlos.
- Se actualizó la tabla de "Condiciones Ambientales" en `reporter.py` para incluir también los datos del lugar seleccionado.

### 🚀 Nueva Prueba: Velocidad Máxima (v1.3.0)
- **Extracción (`analyzer.py`)**: Se añadió `extract_top_speed_events` (buscando de 0 a 200m tras activarse el Pulsador=100) y `calculate_top_speed_metrics` orientada a la `V. Máxima`.
- **Análisis (`analysis_controller.py`)**: Se introdujo `evaluate_top_speed()`, organizando las tablas a los estándares globales y generando reportes gráficos similares a los de Recuperación, agregando una tabla especial sólo con el pico de velocidad.
- **Interfaz y Módulo (`main.py` & `top_speed_test.py`)**: Se insertó en la cuadrícula inicial de selección el botón "Velocidad Máxima", vinculado a un nuevo módulo que permite cargar el CSV, asignar peso y solicitar la generación del reporte.

### 📝 Correcciones Recientes de Exportación e Interfaz (v1.1.1 - v1.3.3)
- Se estandarizaron todas las tablas resumen en la primera vista bajo el formato: `V. Inicial (km/h)`, `V. Final (km/h)`, `Tiempo (s)`, `Distancia (m)`, `Acel Prom (m/s²)`, `Top RPM` para todas las pruebas integradas en esta iteración.
- Se actualizó la nomenclatura de archivos exportados (PDF y CSV) para incluir el `Lugar` en lugar del `Piloto`, además de añadir la hora exacta de la generación. Formato final: `(Prueba)_(Motocicleta)_(Codigo Modelo)_(Lugar)_(Fecha_Hora)`.
- Se solucionó un error en `evaluate_recovery` donde no se generaban archivos CSV independientes para la prueba de Recuperación. Ahora exportará por cada grupo de velocidad (Ej: `Recuperacion_30kmh_...`).
- Se corrigió un bloque de código duplicado accidentalmente introducido en `analysis_controller.py` para la generación de nombres de PDF.
- Se corrigió un crash de herencia de clases de interfaz y un parámetro de Callback en el `PreviewWindow` para la prueba de "Velocidad Máxima" (v1.3.1 - v1.3.3).

### 💻 Comandos Ejecutados
*(Refactorización de código sin instalación de nuevas dependencias)*

### ⏳ Pendientes
- Ejecutar pruebas manuales y visuales para confirmar que el diseño del PreviewWindow soporta correctamente el flujo de trabajo del usuario.

### 🚀 Próximos Pasos
- Completar las pruebas con datos reales para dar por finalizada la integración de la previsualización.

---

## Sesión: 05 de Marzo de 2026

### 🎯 Objetivo Principal
- Optimizar el espacio vertical de la interfaz principal (`main.py`) para monitores o resoluciones limitadas (altura libre de 900px máximo).
- Reestructurar el encabezado de información técnica de los reportes PDF.

### 👤 Peticiones del Usuario (Daniel)
- Reorganizar la parte de selección de prueba y recortar espacio en lo alto en `main.py` ajustando la geometría a 900 de altura máxima.
- Modificar la tabla de datos técnicos de la moto al inicio del reporte PDF (`reporter.py`), ordenando los campos en una estructura de 4 filas y dos columnas principales.
- Actualizar el control de versiones.

### 🧠 Decisiones Tomadas
- Se sustituyeron los grandes botones en cuadrícula por un componente horizontal avanzado llamado `CTkSegmentedButton` en `main.py`, que encapsula todas las opciones de pruebas en una sola línea.
- Se agruparon lógicamente los combos de `Motocicleta` y `Lugar de Prueba` en una cabecera más compacta, y de igual forma las `Condiciones Ambientales` en un pie de página junto al bloque de `Comentarios` y el botón de generar.
- La geometría de ventana se estableció en `1100x850` para un margen de seguridad razonable debajo de 900px.
- La versión fue subida a **v1.4.0** tras la reestructuración completa de la ventana principal y la modificación del PDF.

### 📁 Archivos Modificados / Creados
- `[MODIFICADO]` `version.py`
- `[MODIFICADO]` `main.py`
- `[MODIFICADO]` `reporter.py`
- `[MODIFICADO]` `docs/HANDOFF.md`

### � Cambio Mayor de Interfaz y Flujo (v2.0.0)
- **Reestructuración de inicio**. A petición del usuario, se modificó drásticamente el flujo de inicio de la aplicación para hacerla escalable a nuevos modos de operación.
- **Menú Principal (`main.py`)**: Se extrajo la interfaz de pruebas individual a una sub-vista, y ahora la aplicación arranca con una pantalla de bienvenida que ofrece 3 opciones de trabajo:
  1. `Comparativo` (En desarrollo)
  2. `Todas las pruebas` (En desarrollo)
  3. `Individual` (Interfaz funcional actual)
- **Navegación**: Se implementó un sistema de limpieza de pantalla (`clear_window`) para cambiar entre las distintas vistas sin abrir ventanas múltiples.
- **Retorno al menú principal**: A cada módulo se le agregó un botón en la esquina inferior izquierda (`⬅ Regresar`) para volver instantáneamente a la selección principal.
- **Control de Versiones (`version.py`)**: Debido al cambio sustancial en el "core" de la navegación e interfaz, se ha incrementado el sistema directo a su **Versión 2.0.0**.

### 📄 Estandarización de PDF y Pruebas (v2.1.0)
- **Corrección de Proporciones Gráficas**: Se modificó el `reporter.py` para usar `ImageReader`, calculando dinámicamente el `aspect_ratio` real de las gráficas entregadas por `matplotlib` para prevenir estiramientos en el PDF.
- **Redimensionamiento de Gráficas**: Se modificó `plotter.py` estableciendo un alto de figura menor (`figsize=(15, 3)`) para RPM y Aceleración, garantizando que ambas encajen perfectamente en una misma hoja junto a la gráfica principal de Velocidad.
- **Titulación Dinámica (PDF)**: Se parametrizó `reporter.add_header` para que el título siga estrictamente la convención solicitada: `- Prueba de "[tipo]" del modelo "[Moto]" ("[Codigo]") -`.
- **Refactorización de Prueba de Frenado**: 
  - Se modificó `analyzer.py` para leer y asignar el grupo al que pertenece la prueba de frenado (40 km/h o 60 km/h ±5 km/h).
  - Se reescribió la lógica interna en `analysis_controller.py` > `evaluate_braking` para descartar pruebas fuera de los rangos.
  - El PDF de frenado ahora genera estrictamente una "Hoja 1" con el resumen comparativo de los mejores 3 eventos de 40 km/h y 60 km/h combinados.
  - La "Hoja 2" contiene el análisis detallado (Velocidad, RPM y Aceleración) del mejor evento de 40 km/h.
  - La "Hoja 3" contiene el análisis detallado del mejor evento de 60 km/h.
- **Simplificación de Aceleración**: Se eliminaron las gráficas segmentadas de la prueba de aceleración para concentrar el análisis en una sola página de detalle general por requerimiento del usuario.
- **Control de Versiones**: Se actualizó a **v2.1.0** para reflejar estas integraciones estructurales en los reportes finales.

### 💻 Comandos Ejecutados
*(Sin comandos ejecutados, solo refactorizaciones algorítmicas y gráficas)*

### ⏳ Pendientes
- Desarrollar la lógica y diseño de las ventanas vacías `Comparativo` y `Todas las pruebas` a futuro.

### 🚀 Próximos Pasos
- Esperar confirmación de Daniel para avanzar en las nuevas rutas de "Comparativo" o "Todas las pruebas".

---

## Sesión: 10 de Marzo de 2026

### 🎯 Objetivo Principal
- Eliminar los guiones (`-`) del título principal en los reportes PDF.

### 👤 Peticiones del Usuario (Daniel)
- Quitar los guiones "-" que envuelven el título de cada informe.

### 🧠 Decisiones Tomadas
- Se modificó el formato de string predeterminado en `reporter.py` (`PDFReporter.add_header`) quitando los guiones al inicio y al final.
- El formato final pasa de ser `- Prueba de [tipo] del modelo "[Moto]" ("[Codigo]") -` a ser: `Prueba de [tipo] del modelo "[Moto]" ("[Codigo]")`.
- Se actualizó la versión de la aplicación a **v2.1.1**.

### 📁 Archivos Modificados / Creados
- `[MODIFICADO]` `reporter.py`
- `[MODIFICADO]` `version.py`
- `[MODIFICADO]` `docs/HANDOFF.md`

### 💻 Comandos Ejecutados
*(Sin comandos ejecutados, solo edición de texto en Python)*

### ⏳ Pendientes
- Desarrollar la lógica y diseño de las ventanas vacías `Comparativo` y `Todas las pruebas` a futuro.

### 🚀 Próximos Pasos
- Esperar confirmación de Daniel para avanzar en las nuevas rutas de "Comparativo" o "Todas las pruebas", o cualquier otro ajuste menor.

---

## Sesión: 10 de Marzo de 2026 (Refactorización Gestor de Datos)

### 🎯 Objetivo Principal
- Mover la gestión de datos (Pilotos, Motocicletas, Lugares) al menú principal para un acceso más limpio y centralizado.
- Almacenar permanentemente el peso asociado a cada piloto.

### 👤 Peticiones del Usuario (Daniel)
- Agregar peso `0` por defecto a los pilotos antiguos insertados previamente como cadenas de texto para evitar perder su registro.
- Eliminar el campo de entrada manual de "peso" de cada módulo de prueba individual, consolidando la información de peso directamente según el perfil del piloto.

### 🧠 Decisiones Tomadas
- Se ha creado una estructura de botones en la parte baja del menú principal en `main.py` ("Gestión de Motos", "Gestión de Lugares", "Gestión de Pilotos").
- Los módulos de pruebas ahora extraen automáticamente el peso desde el `DataManager` en base al nombre del piloto.
- Se ha implementado un sistema de migración automática en `data_manager.py` para leer `pilotos.json` al arranque y convertir cualquier nombre antiguo en un diccionario de datos estructurado.

### 📁 Archivos Modificados / Creados
- `[MODIFICADO]` `data_manager.py`
- `[MODIFICADO]` `main.py`
- `[MODIFICADO]` `modules/braking_test.py`
- `[MODIFICADO]` `modules/climbing_test.py`
- `[MODIFICADO]` `modules/acceleration_0_80.py`
- `[MODIFICADO]` `modules/recovery_test.py`
- `[MODIFICADO]` `modules/top_speed_test.py`
- `[MODIFICADO]` `version.py`

### 🚀 Control de Versiones (v2.2.0)
### 📁 Archivos Modificados / Creados
- `[NUEVO]` `docs/HANDOFF.md`

### 💻 Comandos Ejecutados
*(No se han ejecutado comandos de consola en esta sesión inicial)*

### 📝 Snippets Importantes
*(Ningún snippet por el momento, aquí se guardarán configuraciones o bloques clave de código que vayamos desarrollando)*

### ⏳ Pendientes
- Integrar la documentación del estado actual de `main.py` y demás componentes si es necesario.

### 🚀 Próximos Pasos
- Esperar las próximas instrucciones de Daniel sobre qué funcionalidad de `main.py` (o del proyecto en general) vamos a empezar a programar o revisar.

---

## Sesión: 04 de Marzo de 2026

### 🎯 Objetivo Principal
- Implementar la función de **"Previsualizar"** reportes antes de generar el PDF final.

### 👤 Peticiones del Usuario (Daniel)
- Agregar un botón o flujo para poder ver las gráficas y la tabla resumen antes de confirmar la generación del PDF.

### 🧠 Decisiones Tomadas
- Se introdujo `preview_window.py` que contiene `PreviewWindow`, un `CTkToplevel` con scroll para ver imágenes y tablas.
- Se refactorizó `analysis_controller.py`:
  - Los métodos antiguos (`process_data`, `process_acceleration_0_80`, etc.) se dividieron. Ahora hay métodos `evaluate_*` que retornan un diccionario con la información y las gráficas en memoria (`io.BytesIO`).
  - Se unificó la generación de reporte PDF a través del método `generate_pdf(preview_data)`.
- Se actualizaron los módulos de la interfaz (`braking_test.py`, `acceleration_0_80.py`, `climbing_test.py`, `recovery_test.py`) para consumir la nueva lógica de evaluación e invocar `PreviewWindow`.

### 📁 Archivos Modificados / Creados
- `[NUEVO]` `preview_window.py`
- `[NUEVO]` `docs/UI_PREVIEW_DESIGN.md`
- `[NUEVO]` `version.py`
- `[MODIFICADO]` `analysis_controller.py`
- `[MODIFICADO]` `analyzer.py`
- `[MODIFICADO]` `main.py`
- `[MODIFICADO]` `reporter.py`
- `[MODIFICADO]` `plotter.py`
- `[MODIFICADO]` `modules/braking_test.py`
- `[MODIFICADO]` `modules/acceleration_0_80.py`
- `[MODIFICADO]` `modules/climbing_test.py`
- `[MODIFICADO]` `modules/recovery_test.py`

### ✨ Nuevas Correcciones y Modificaciones (Misma Sesión)
- Se eliminó la Velocidad y Dirección del Viento de la interfaz principal (`main.py`) y de los reportes PDF (`reporter.py`).
- Se mejoró el contraste de las tablas en `PreviewWindow` (encabezado azul, fondo blanco).
- Se corrigieron errores como `SettingWithCopyWarning` en `analyzer.py` y `table_segments is not defined` en `analysis_controller.py`.
- Se estableció un estándar fijo para la exportación de archivos (tanto CSV como PDF): `(Prueba)_(Motocicleta)_(Codigo Modelo)_(Piloto)_(Fecha)`.
- Se implementó un control de versiones a través de `version.py` (actualmente en **v1.1.0**). El título de la aplicación principal ahora muestra la versión actual, y los reportes PDF tienen la versión estampada en la esquina inferior derecha.

### 📍 Nueva Función: Control de Lugares de Prueba (v1.1.0)
- Se añadió un sistema de gestión de lugares en `data_manager.py` (guardado en `lugares.json`).
- Nueva interfaz en `main.py` para seleccionar un lugar de prueba de una lista desplegable, junto con un botón para agregar nuevos lugares (Nombre, Altitud, Coordenadas).
- Se implementó la validación estricta: es obligatorio seleccionar un lugar para poder generar reportes o visualizarlos.
- Se actualizó la tabla de "Condiciones Ambientales" en `reporter.py` para incluir también los datos del lugar seleccionado.

### 🚀 Nueva Prueba: Velocidad Máxima (v1.3.0)
- **Extracción (`analyzer.py`)**: Se añadió `extract_top_speed_events` (buscando de 0 a 200m tras activarse el Pulsador=100) y `calculate_top_speed_metrics` orientada a la `V. Máxima`.
- **Análisis (`analysis_controller.py`)**: Se introdujo `evaluate_top_speed()`, organizando las tablas a los estándares globales y generando reportes gráficos similares a los de Recuperación, agregando una tabla especial sólo con el pico de velocidad.
- **Interfaz y Módulo (`main.py` & `top_speed_test.py`)**: Se insertó en la cuadrícula inicial de selección el botón "Velocidad Máxima", vinculado a un nuevo módulo que permite cargar el CSV, asignar peso y solicitar la generación del reporte.

### 📝 Correcciones Recientes de Exportación e Interfaz (v1.1.1 - v1.3.3)
- Se estandarizaron todas las tablas resumen en la primera vista bajo el formato: `V. Inicial (km/h)`, `V. Final (km/h)`, `Tiempo (s)`, `Distancia (m)`, `Acel Prom (m/s²)`, `Top RPM` para todas las pruebas integradas en esta iteración.
- Se actualizó la nomenclatura de archivos exportados (PDF y CSV) para incluir el `Lugar` en lugar del `Piloto`, además de añadir la hora exacta de la generación. Formato final: `(Prueba)_(Motocicleta)_(Codigo Modelo)_(Lugar)_(Fecha_Hora)`.
- Se solucionó un error en `evaluate_recovery` donde no se generaban archivos CSV independientes para la prueba de Recuperación. Ahora exportará por cada grupo de velocidad (Ej: `Recuperacion_30kmh_...`).
- Se corrigió un bloque de código duplicado accidentalmente introducido en `analysis_controller.py` para la generación de nombres de PDF.
- Se corrigió un crash de herencia de clases de interfaz y un parámetro de Callback en el `PreviewWindow` para la prueba de "Velocidad Máxima" (v1.3.1 - v1.3.3).

### 💻 Comandos Ejecutados
*(Refactorización de código sin instalación de nuevas dependencias)*

### ⏳ Pendientes
- Ejecutar pruebas manuales y visuales para confirmar que el diseño del PreviewWindow soporta correctamente el flujo de trabajo del usuario.

### 🚀 Próximos Pasos
- Completar las pruebas con datos reales para dar por finalizada la integración de la previsualización.

---

## Sesión: 05 de Marzo de 2026

### 🎯 Objetivo Principal
- Optimizar el espacio vertical de la interfaz principal (`main.py`) para monitores o resoluciones limitadas (altura libre de 900px máximo).
- Reestructurar el encabezado de información técnica de los reportes PDF.

### 👤 Peticiones del Usuario (Daniel)
- Reorganizar la parte de selección de prueba y recortar espacio en lo alto en `main.py` ajustando la geometría a 900 de altura máxima.
- Modificar la tabla de datos técnicos de la moto al inicio del reporte PDF (`reporter.py`), ordenando los campos en una estructura de 4 filas y dos columnas principales.
- Actualizar el control de versiones.

### 🧠 Decisiones Tomadas
- Se sustituyeron los grandes botones en cuadrícula por un componente horizontal avanzado llamado `CTkSegmentedButton` en `main.py`, que encapsula todas las opciones de pruebas en una sola línea.
- Se agruparon lógicamente los combos de `Motocicleta` y `Lugar de Prueba` en una cabecera más compacta, y de igual forma las `Condiciones Ambientales` en un pie de página junto al bloque de `Comentarios` y el botón de generar.
- La geometría de ventana se estableció en `1100x850` para un margen de seguridad razonable debajo de 900px.
- La versión fue subida a **v1.4.0** tras la reestructuración completa de la ventana principal y la modificación del PDF.

### 📁 Archivos Modificados / Creados
- `[MODIFICADO]` `version.py`
- `[MODIFICADO]` `main.py`
- `[MODIFICADO]` `reporter.py`
- `[MODIFICADO]` `docs/HANDOFF.md`

###  Cambio Mayor de Interfaz y Flujo (v2.0.0)
- **Reestructuración de inicio**. A petición del usuario, se modificó drásticamente el flujo de inicio de la aplicación para hacerla escalable a nuevos modos de operación.
- **Menú Principal (`main.py`)**: Se extrajo la interfaz de pruebas individual a una sub-vista, y ahora la aplicación arranca con una pantalla de bienvenida que ofrece 3 opciones de trabajo:
  1. `Comparativo` (En desarrollo)
  2. `Todas las pruebas` (En desarrollo)
  3. `Individual` (Interfaz funcional actual)
- **Navegación**: Se implementó un sistema de limpieza de pantalla (`clear_window`) para cambiar entre las distintas vistas sin abrir ventanas múltiples.
- **Retorno al menú principal**: A cada módulo se le agregó un botón en la esquina inferior izquierda (`⬅ Regresar`) para volver instantáneamente a la selección principal.
- **Control de Versiones (`version.py`)**: Debido al cambio sustancial en el "core" de la navegación e interfaz, se ha incrementado el sistema directo a su **Versión 2.0.0**.

### 📄 Estandarización de PDF y Pruebas (v2.1.0)
- **Corrección de Proporciones Gráficas**: Se modificó el `reporter.py` para usar `ImageReader`, calculando dinámicamente el `aspect_ratio` real de las gráficas entregadas por `matplotlib` para prevenir estiramientos en el PDF.
- **Redimensionamiento de Gráficas**: Se modificó `plotter.py` estableciendo un alto de figura menor (`figsize=(15, 3)`) para RPM y Aceleración, garantizando que ambas encajen perfectamente en una misma hoja junto a la gráfica principal de Velocidad.
- **Titulación Dinámica (PDF)**: Se parametrizó `reporter.add_header` para que el título siga estrictamente la convención solicitada: `- Prueba de "[tipo]" del modelo "[Moto]" ("[Codigo]") -`.
- **Refactorización de Prueba de Frenado**: 
  - Se modificó `analyzer.py` para leer y asignar el grupo al que pertenece la prueba de frenado (40 km/h o 60 km/h ±5 km/h).
  - Se reescribió la lógica interna en `analysis_controller.py` > `evaluate_braking` para descartar pruebas fuera de los rangos.
  - El PDF de frenado ahora genera estrictamente una "Hoja 1" con el resumen comparativo de los mejores 3 eventos de 40 km/h y 60 km/h combinados.
  - La "Hoja 2" contiene el análisis detallado (Velocidad, RPM y Aceleración) del mejor evento de 40 km/h.
  - La "Hoja 3" contiene el análisis detallado del mejor evento de 60 km/h.
- **Simplificación de Aceleración**: Se eliminaron las gráficas segmentadas de la prueba de aceleración para concentrar el análisis en una sola página de detalle general por requerimiento del usuario.
- **Control de Versiones**: Se actualizó a **v2.1.0** para reflejar estas integraciones estructurales en los reportes finales.

### 💻 Comandos Ejecutados
*(Sin comandos ejecutados, solo refactorizaciones algorítmicas y gráficas)*

### ⏳ Pendientes
- Desarrollar la lógica y diseño de las ventanas vacías `Comparativo` y `Todas las pruebas` a futuro.

### 🚀 Próximos Pasos
- Esperar confirmación de Daniel para avanzar en las nuevas rutas de "Comparativo" o "Todas las pruebas".

---

## Sesión: 10 de Marzo de 2026

### 🎯 Objetivo Principal
- Eliminar los guiones (`-`) del título principal en los reportes PDF.

### 👤 Peticiones del Usuario (Daniel)
- Quitar los guiones "-" que envuelven el título de cada informe.

### 🧠 Decisiones Tomadas
- Se modificó el formato de string predeterminado en `reporter.py` (`PDFReporter.add_header`) quitando los guiones al inicio y al final.
- El formato final pasa de ser `- Prueba de [tipo] del modelo "[Moto]" ("[Codigo]") -` a ser: `Prueba de [tipo] del modelo "[Moto]" ("[Codigo]")`.
- Se actualizó la versión de la aplicación a **v2.1.1**.

### 📁 Archivos Modificados / Creados
- `[MODIFICADO]` `reporter.py`
- `[MODIFICADO]` `version.py`
- `[MODIFICADO]` `docs/HANDOFF.md`

### 💻 Comandos Ejecutados
*(Sin comandos ejecutados, solo edición de texto en Python)*

### ⏳ Pendientes
- Desarrollar la lógica y diseño de las ventanas vacías `Comparativo` y `Todas las pruebas` a futuro.

### 🚀 Próximos Pasos
- Esperar confirmación de Daniel para avanzar en las nuevas rutas de "Comparativo" o "Todas las pruebas", o cualquier otro ajuste menor.

---

## Sesión: 10 de Marzo de 2026 (Refactorización Gestor de Datos)

### 🎯 Objetivo Principal
- Mover la gestión de datos (Pilotos, Motocicletas, Lugares) al menú principal para un acceso más limpio y centralizado.
- Almacenar permanentemente el peso asociado a cada piloto.

### 👤 Peticiones del Usuario (Daniel)
- Agregar peso `0` por defecto a los pilotos antiguos insertados previamente como cadenas de texto para evitar perder su registro.
- Eliminar el campo de entrada manual de "peso" de cada módulo de prueba individual, consolidando la información de peso directamente según el perfil del piloto.

### 🧠 Decisiones Tomadas
- Se ha creado una estructura de botones en la parte baja del menú principal en `main.py` ("Gestión de Motos", "Gestión de Lugares", "Gestión de Pilotos").
- Los módulos de pruebas ahora extraen automáticamente el peso desde el `DataManager` en base al nombre del piloto.
- Se ha implementado un sistema de migración automática en `data_manager.py` para leer `pilotos.json` al arranque y convertir cualquier nombre antiguo en un diccionario de datos estructurado.

### 📁 Archivos Modificados / Creados
- `[MODIFICADO]` `data_manager.py`
- `[MODIFICADO]` `main.py`
- `[MODIFICADO]` `modules/braking_test.py`
- `[MODIFICADO]` `modules/climbing_test.py`
- `[MODIFICADO]` `modules/acceleration_0_80.py`
- `[MODIFICADO]` `modules/recovery_test.py`
- `[MODIFICADO]` `modules/top_speed_test.py`
- `[MODIFICADO]` `version.py`

### 🚀 Control de Versiones (v2.2.0)
- Incremento de versión (minor) por la introducción de los paneles de administración y cambio estructural en los archivos JSON de guardado local.

### 💻 Comandos Ejecutados
*(Refactorización interna en Python)*

### ⏳ Pendientes
- Desarrollar la lógica y diseño de las ventanas vacías `Comparativo` y `Todas las pruebas`.

---

## Sesión: 11 de Marzo de 2026 (Integración de Mapa GPS Automático)

### 🎯 Objetivo Principal
- Implementar una previsualización cartográfica satelital (Mapa de Calor GPS) que dibuje la ruta de las pruebas en base a las coordenadas de longitud, latitud y velocidad.

### 👤 Peticiones del Usuario (Daniel)
- Agregar un condicional de internet para que si la laptop está offline no falle al crear pdfs.
- Insertar la gráfica satelital al inicio (primer lugar) de las páginas de Resumen en los reportes de previsualización y PDF generados.
- Añadir un "auto-zoom" dinámico y utilizar la vista híbrida (satélite con trazado de calles).

### 🧠 Decisiones Tomadas
- Se ha instalado la tubería `staticmap` via pip, la cual descarga los tiles en memoria sin requerir navegadores web instalados.
- En `plotter.py` se construyó el método `plot_gps_heatmap`. Este método:
  1. Ejecuta un ping silencioso de 1s a los DNS de Cloudflare (1.1.1.1) para comprobar disponibilidad de red.
  2. Obtiene de Google Maps el formato Híbrido (`lyrs=y`).
  3. Ejecuta un "monkey-patch" sobre la librería permitiendo un zoom súper detallado hasta el nivel 20 para visualizaciones perfectas en pistas muy cortas.
  4. Calcula un `bounding box` de expansión ajustando dinámicamente un 5% de zoom adicional en los bordes para encuadrar la ruta sin cortar las esquinas.
  5. Colorea la línea de trayecto trazando segmentos que se tiñen de "frío a caliente" (Colormap de matplotlib "jet") según la métrica intersectorial `Velocidad_GPS`.
- En `analysis_controller.py`, para todos y cada uno de los métodos (`evaluate_braking`, `evaluate_recovery`, `evaluate_climbing`, etc), se captura el *Mejor Desempeño General*, se genera su imagen GPS, y se inyecta de #1 en la lista `images_hoja1` y en las hojas de detalles.

### 📁 Archivos Modificados / Creados
- `[MODIFICADO]` `plotter.py`
- `[MODIFICADO]` `analysis_controller.py`
- `[MODIFICADO]` `version.py`

### 🚀 Control de Versiones (v2.3.0)
- Incremento de versión oficial debido a la introducción estructural y visual del ploteo avanzado de lat/lon satelitales vía web.

### 💻 Comandos Ejecutados
- `pip install staticmap`

### ⏳ Pendientes
- Iniciar el diseño y desarrollo del modo "Todas las pruebas".

---

## Sesión: 12 de Marzo de 2026

### 🎯 Objetivo Principal
- Sincronizar las dependencias del proyecto y actualizar el archivo `requirements.txt`.

### 👤 Peticiones del Usuario (Daniel)
- Revisar qué librerías son necesarias para correr todo el proyecto y cuáles están instaladas.
- Actualizar el archivo `requirements.txt` si falta alguna.

### 🧠 Decisiones Tomadas
- Se identificó que `staticmap` (necesaria para la v2.3.0) no estaba en los requisitos originales ni instalada en el entorno.
- Se instaló `staticmap` y `pillow` manualmente.
- Se actualizó `requirements.txt` para incluir la lista completa de librerías mandatorias.

### 📁 Archivos Modificados / Creados
- `[MODIFICADO]` `requirements.txt`
- `[MODIFICADO]` `docs/HANDOFF.md`

### 💻 Comandos Ejecutados
- `pip install staticmap pillow`

### 🚀 Control de Versiones (v2.3.1)
- Versión de parche para asegurar la integridad de la instalación.

### ⏳ Pendientes
- Retomar la planificación arquitectónica e inicializar el desarrollo del módulo "Todas las pruebas".

### 🚀 Próximos Pasos
- Iniciar el diseño y desarrollo del modo "Todas las pruebas".

---

## Sesión: 13 de Marzo de 2026 (Reestructuración de Reportes y Contexto GPS)

### 🎯 Objetivo Principal
- Implementar una descripción geográfica detallada (Contexto) de cada prueba (distancia, altitud, coordenadas, link original de Google Maps).
- Reestructurar de cero los reportes PDF para estandarizarlos a: 
  - Hoja 1 (Contexto Geográfico). 
  - Hoja 2 (Resumen numérico).
  - Hoja 3 (Mapa del Mejor Evento 1). 
  - Hoja 4 (Gráficas del Mejor Evento 1), etc.
- Agregar Barra de Colores (Colorbar) explicativa al trazado de la ruta.

### 👤 Peticiones del Usuario (Daniel)
- Agregar texto con "largo de la pista, altitud, latitud y longitud, y link directo a google maps" deduciéndolo de las columnas CSV.
- A los mapas de línea de calor ponerles una leyenda descriptiva de color-velocidad.
- Obligar un orden "Hoja 1", "Hoja 2", "Hoja N" muy estricto excluyendo o juntando gráficas y resúmenes.

### 🧠 Decisiones Tomadas
- Se introdujo `analyzer.get_gps_context(df)` para iterar todo un trazado global y devolver un diccionario rico en los datos del entorno.
- En `plotter.plot_gps_heatmap` se renderizó de forma manual usando Matplotlib una leyenda y barra lateral ligada al Colormap (`jet`) basándose en los extremos de velocidad para ayudar al lector a entender la escala métrica de velocidad en pista.
- En `analysis_controller.py`, se partió la lógica de inyección combinada antigua de Previsualización (`preview_data['sections']`). Se aisló `contexto_gps` y `context_map`. A continuación, se separaron con recuadros exactos precalculables cada sección como una nueva hoja.
- El PDFReporter fue adaptado en su cabecera para pintar la "Tabla de Referencias Satelitales" e imagen SVG. Cada paso final del bucle `sections` ejecuta ahora implícitamente `reporter.add_page_break()`, asegurando total pureza de una hoja, un contenido.
- Todas y cada una de las sub-clases (`modules/braking_test.py`, `acceleration_0_80.py`, etc) fueron actualizadas para entregar los dicts del render geográfico nativamente al UI.

### 📁 Archivos Modificados / Creados
- `[MODIFICADO]` `analyzer.py`
- `[MODIFICADO]` `plotter.py`
- `[MODIFICADO]` `analysis_controller.py`
- `[MODIFICADO]` `reporter.py`
- `[MODIFICADO]` `preview_window.py`
- `[MODIFICADO]` `modules/*.py` (x5)
- `[MODIFICADO]` `version.py`

### 🚀 Control de Versiones (v2.4.0)
- Salto en subversión confirmando la total reescritura arquitectónica del controlador de PDFs, Mapas Geotags y Contexto inteligente.

### ⏳ Pendientes
- Revisar requerimientos de la prueba de frenado planteados en "nuevas funciones".

### 🚀 Próximos Pasos
- Estudiar y estructurar el abordaje del archivo "Nuevas funciones" (referentes a Frenado de 163 a 168).

---

## Sesión: 13 de Marzo de 2026 (Hotfix: Ajustes visuales de PDF y Mapas Gráficos)

### 🎯 Objetivo Principal
- Limpiar el exceso de textos generados en los PDFs paginados, erradicar hojas en blanco y modificar el enfoque visual de la primera página hacia una vista "geográfica plana", conservando los mapas de calor para los eventos específicos.

### 👤 Peticiones del Usuario (Daniel)
- Quitar "Mapa de Contexto Global" del inicio.
- Reubicar el link directo a Google Maps bajo el título "Ubicación de la prueba".
- Reemplazar el mapa de calor inicial por un trazado simple, grueso, de color azul, que indique estáticamente la distancia de la prueba en metros.
- Solucionar un bug donde el `reporter.py` eyectaba una Hoja 2 vacía por desbordamiento del mapa y tabla inicial unidos.
- Agrandar sustancialmente el `figsize` de las gráficas resumen para aprovechar más hoja.
- Limpiar todos los títulos residuales como "Hoja 3: mapa de calor - mejor evento".

### 🧠 Decisiones Tomadas
- Se limpiaron los "Paragraph" residuales en `reporter.py` inyectados en la Hoja 1, consolidando "Ubicación de la prueba" con su respectivo vínculo HTML anclado semánticamente bajo la tabla de contexto.
- En `plotter.py` se construyó `plot_gps_route_simple(df)`, una reutilización minimalista de staticmap que en lugar de iterar promedios de calor, traza una ruta fija `#1f538d` a 5px, añadiendo desde Matplotlib el overlay de texto dinámico de `distance_m`.
- En `plotter.py` se refactorizaron los métodos paramétricos (e.j., `plot_speed_vs_time`, `plot_accel_vs_time`) para soportar sobreescritura del `figsize` (default a 15x6). `analysis_controller` ahora los invoca con `figsize=(15,8)` para gráficos de resumen expandidos.
- Se reparó la lógica de paginación en `analysis_controller.py / generate_pdf`, forzando condicional e incondicionalmente un `reporter.add_page_break()` antes de imprimir los resúmenes tabulares, asegurando que la data (como "Top 3 de Frenado") respire siempre desde la Hoja 2.
- Se iteraron manualmente todos los Evaluadores (`evaluate_braking`, `evaluate_acceleration_0_80`, `evaluate_climbing`, etc) para sustituir "Mapa de Calor Global" por la nueva "Línea Azul Simple" e inyectando las depuraciones fonéticas solicitadas sobre los diccionarios `sections`.
- **Bugfixes menores resueltos sobre la marcha:**
  - `analyzer.py`: Estandarización de llaves de contexto (`'distancia_m'`, `'altitud_promedio_msnm'`) a *snake_case* en lugar de capitalizadas, homologando el formato que consumían el preview UI y el PDFReporter.
  - `plotter.py`: Implementación de una vista horizontal estática o banner en el renderizado `StaticMap(800, 400)` y `figsize=(10, 5)`. Se evitó escalar las imágenes por `inch` en ReporterLab para impedir la pérdida de nitidez y ratio, resolviendo desbordamientos por adición de textos largos (comentarios).
  - Reintegrada dependencia local ausente (`import numpy`, `from reportlab.lib.units import inch`).

### 📁 Archivos Modificados / Creados
- `[MODIFICADO]` `reporter.py`
- `[MODIFICADO]` `plotter.py`
- `[MODIFICADO]` `analysis_controller.py`
- `[MODIFICADO]` `analyzer.py`
- `[MODIFICADO]` `preview_window.py`

### 🚀 Control de Versiones (v2.4.1)
- Bugfixing resolutivo e iteración en diseño UX/UI en exportación estática de ReportLab PDFs y UI Preview.

---

## Sesión: 13 de Marzo de 2026 (Fixes: Aceleración y Leyenda de Calor)

### 🎯 Objetivo Principal
- Corregir el error de tipado al previsualizar la prueba de Aceleración 0-80 km/h que causaba el quiebre de la aplicación.
- Mejorar el aspecto visual en la leyenda gráfica del mapa de calor satelital, reduciendo su escala y centrándola correctamente en pantalla para evitar traslapes.
- Identificar y engrosar la línea azul representativa del trayecto global de la prueba en los mapas satelitales fijos. 

### 👤 Peticiones del Usuario (Daniel)
- Solicitar la solución del error en Aceleración (`TypeError: Plotter.plot_acceleration_comparison() got an unexpected keyword argument 'figsize'`).
- Señalar que los números de la "barra de colores" o leyenda en el mapa de calor se montaban y cortaban sobre la propia imagen. Se requirió bajar el tamaño al 50% y centrar verticalmente, conservando la ubicación horizontal.
- Cambiar el grosor de la línea azul gruesa que indica el trazado en la vista global.

### 🧠 Decisiones Tomadas
- En `plotter.py` > `plot_acceleration_comparison`, se introdujo formalmente el parámetro por defecto `figsize=(15, 6)` que fue omitido durante la actualización v2.4.1 de expansión cartográfica, subsanando el crash inmediato de compatibilidad con `analysis_controller.py`.
- En `plotter.py` > `plot_gps_heatmap`, se manipuló el objeto Matplotlib ajustando el marco del lienzo principal con `plt.subplots_adjust(right=0.85)` para darle aire al mapa, e inyectando un nuevo `fig.add_axes([0.88, 0.325, 0.03, 0.35])` al `Colorbar` (reduciéndolo de `0.7` de altura a `0.35`, y subiendo el eje inferior `y` desde `0.15` a `0.325` para un anclaje centrado y elegante).
- En `plotter.py` > `plot_gps_route_simple`, el trazo (`Line`) sobre las coordenadas fue actualizado incrementando el grosor azul de `5` a `10` puntos de peso, haciendo la ruta de la Hoja 1 mucho más evidente en impresiones con resolución elevada.
- Incremento a **v2.4.3** reflejando estas correcciones rápidas.

### 📁 Archivos Modificados / Creados
- `[MODIFICADO]` `plotter.py`
- `[MODIFICADO]` `version.py`
- `[MODIFICADO]` `docs/HANDOFF.md`

### 🚀 Control de Versiones (v2.4.3)
- Hotfixes (Solución rápida de crash estético y de ejecución de UI).

### ⏳ Pendientes
- Estructuración e inicialización del modo "Todas las pruebas".

### 🚀 Próximos Pasos
- Construir la maqueta visual e integración inicial en `main.py` de la interfaz Combinada (Selección masiva de pilotos y archivos de cada etapa).

---

## Sesión: 13 de Marzo de 2026 (Refinamiento Estético de Reportes)

### 🎯 Objetivo Principal
- Corregir el truncamiento de etiquetas de ejes en las gráficas exportadas.
- Ajustar el espaciado vertical entre elementos en las hojas de detalle del PDF.

### 👤 Peticiones del Usuario (Daniel)
- Notificar que la palabra "Tiempo (s)" se estaba cortando en el borde inferior de las gráficas.
- Solicitar más aire/espacio entre las gráficas de RPM, Aceleración y la tabla resumen final.

### 🧠 Decisiones Tomadas
- En `plotter.py`, se implementó el uso sistemático de `bbox_inches='tight'` en todos los métodos de guardado de imágenes (`plt.savefig`). Esto garantiza que Matplotlib calcule el área de guardado incluyendo dinámicamente todos los elementos externos como títulos y etiquetas de ejes, evitando recortes.
- En `reporter.py`, se parametrizó el método `add_image` y `add_table` con un argumento `space_after=12` por defecto, permitiendo flexibilidad en el diseño del layout.
- En `analysis_controller.py`, se ajustaron los flujos de creación de PDF para inyectar espacios personalizados (`25pt` tras RPM y `30pt` tras Aceleración), logrando una distribución visual más equilibrada y profesional en las hojas de resultados.
- Incremento a **v2.4.4** para marcar este hito de pulido visual.

### �� Archivos Modificados / Creados
- `[MODIFICADO]` `plotter.py`
- `[MODIFICADO]` `reporter.py`
- `[MODIFICADO]` `analysis_controller.py`
- `[MODIFICADO]` `version.py`
- `[MODIFICADO]` `docs/HANDOFF.md`

### 🚀 Control de Versiones (v2.4.4)
- Mejoras de renderizado y maquetación PDF.

---

## Sesión: 23 de Marzo de 2026 (Nuevas Variables de Moto)

### 🎯 Objetivo Principal
- Añadir las variables "Chasis" y "Motor" al registro y gestión de las motocicletas, y a la generación de reportes PDF.

### 👤 Peticiones del Usuario (Daniel)
- Modificar el módulo donde se guardan las motos para incluir los datos de chasis y motor.

### 🧠 Decisiones Tomadas
- Se actualizó la interfaz de la tabla en `main.py` (`show_gestion_motos_view`) para mostrar las nuevas columnas "Chasis" y "Motor".
- Se ajustó el formulario de agregar motocicleta (`start_add_moto`) en `main.py` para incluir los nuevos campos de entrada y actualizar el tamaño de la ventana.
- Se modificó `reporter.py` (`add_header`) para renderizar "Chasis" y "Motor" en la cabecera técnica de la hoja de detalles por cada generación de PDF.
- Los nuevos datos se agregan orgánicamente en `motos.json` a través de los diccionarios, manteniendo la total retrocompatibilidad paramétrica para las motocicletas previamente registradas al invocar un `dict.get()`.

### 📁 Archivos Modificados / Creados
- `[MODIFICADO]` `main.py`
- `[MODIFICADO]` `reporter.py`
- `[MODIFICADO]` `version.py`
- `[MODIFICADO]` `docs/HANDOFF.md`

### 🚀 Control de Versiones (v2.5.0)
- Actualización de versión (minor) por la adición de parámetros nativos en la ficha de registros de Motocicleta.

### 💻 Comandos Ejecutados
*(Edición de interfaces y PDFs. Validación exitosa)*

### ⏳ Pendientes
- Estructuración e inicialización del modo "Todas las pruebas".

---

## Sesión: 23 de Marzo de 2026 (Altura de Pilotos)

### 🎯 Objetivo Principal
- Añadir la variable "Altura" escalarmente al módulo central de Pilotos y reflejarlo en todos los análisis y PDFs.

### 👤 Peticiones del Usuario (Daniel)
- Agregar al módulo de pilotos la altura. Por defecto establecer en todos 0.
- Variar la versión del programa.
- Registrar estos cambios en el HANDOFF.

### 🧠 Decisiones Tomadas
- Se introdujo la variable "Altura (cm)" en los flujos principales de `data_manager.py`. Automáticamente se actualizarán (`peso: 0, altura: 0`) los pilotos antiguos sin necesidad de intervención manual durante el `load_pilotos`.
- Se incorporó la entrada de UI para la Altura en la vista interactiva de agregar/modificar pilotos en `main.py`.
- Se mapeó exhaustivamente el paso del dato de `altura` de los pilotos a través de todos los reportes de módulos (`braking_test`, `acceleration_0_80`, `climbing_test`, `recovery_test`, `top_speed_test`).
- Se reescribió `reporter.py` para imprimir el texto como `Nombre (Peso Kg, Altura cm)` en la cabecera del PDF final.

---

## [2026-03-24] - Módulo de Reportes Excel y Ajuste de Títulos de Mapas

### 🚀 Novedades y Cambios Implementados

1. **Limpieza de Títulos en Mapas (PDF)**
   - Se iteraron todos los bloques generadores de PDF en `analysis_controller.py` para remover referencias residuales ("Hoja 3: Mapa de Calor", o el nombre de los pilotos en paréntesis).
   - Ahora, absolutamente todos los bloques de mapas GPS llevan como único título estricto: `"Ubicación de la prueba"`.

2. **Nuevo Sistema de Reportes en Excel (`openpyxl`)**
   - Instalación e inclusión de `openpyxl` en `requirements.txt`.
   - Creación de `excel_reporter.py` con la clase `ExcelReporter` configurada para buscar las plantillas en `.../Formatos` y guardar en `.../Resultados`.
   - Se implementó la lógica de escritura (mapeo de datos y pegado de imágenes) para la plantilla `ft-nm-000-008.xlsx` del test de **Aceleración**.

3. **Interfaz Gráfica (Previsualización)**
   - Se actualizó `preview_window.py` para inyectar un botón extra: **"Generar Reporte Excel"** (verde oscuro estilo Excel).
   - Se modificó `analysis_controller.py` para incrustar datos crudos (top 3 eventos, segmentos del mejor evento, e imágenes compiladas) en el `preview_data` exportado hacia la interfaz.
   - En `modules/acceleration_0_80.py`, se conectó el nuevo callback para accionar generar el Excel y lanzar cuadros de diálogo de éxito o error con la ruta del archivo generado.

### 📁 Archivos Modificados / Creados
- `[CREADO]` `excel_reporter.py`
- `[MODIFICADO]` `analysis_controller.py`
- `[MODIFICADO]` `preview_window.py`
- `[MODIFICADO]` `modules/acceleration_0_80.py`
- `[MODIFICADO]` `requirements.txt`
- `[MODIFICADO]` `version.py`
- `[MODIFICADO]` `docs/HANDOFF.md`

### 🚀 Control de Versiones (v2.7.0)
- Salto de versión menor debido a la integración completa del sistema estructural de reportes en Excel (`openpyxl`) y la refactorización estética de los títulos PDF de los mapas.

### 💻 Comandos Ejecutados
- `pip install openpyxl`
- `echo "openpyxl" >> requirements.txt`

### ⏳ Pendientes
- Esperar directivas y confirmación sobre "Todas las pruebas".
- Añadir paulatinamente funciones en `excel_reporter.py` para los otros archivos `ft-nm-000-XX.xlsx` (Frenado, Recuperación, Velocidad Máxima, Ascenso) a medida que el usuario lo indique.

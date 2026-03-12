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
- Retomar la planificación arquitectónica e inicializar el desarrollo del módulo "Todas las pruebas".

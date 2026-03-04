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

### 💻 Comandos Ejecutados
*(Refactorización de código sin instalación de nuevas dependencias)*

### ⏳ Pendientes
- Ejecutar pruebas manuales y visuales para confirmar que el diseño del PreviewWindow soporta correctamente el flujo de trabajo del usuario.

### 🚀 Próximos Pasos
- Completar las pruebas con datos reales para dar por finalizada la integración de la previsualización.

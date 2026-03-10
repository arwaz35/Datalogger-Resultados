# Diseño de la Interfaz de Previsualización

## Objetivo
Implementar una función de "Previsualización" (Preview) en las distintas interfaces de prueba (Frenado, Aceleración, Ascenso, Recuperación) que permita al usuario ver las gráficas y la tabla resumen **antes** de generar definitivamente el archivo PDF.

## 1. Cambios en la Interfaz de Usuario (UI)

### 1.1 El Botón "Previsualizar"
Actualmente, el flujo general cuenta con botones como "Buscar" (para archivos CSV) dentro de cada fila del módulo y un botón principal "Generar" o "Procesar" en la ventana principal (`main.py`) que lanza el análisis completo hasta el PDF.

Para lograr esto de forma ordenada, la propuesta es:
- Agregar un botón **"Previsualizar"** en la vista principal o en cada pestaña de las pruebas, justo a un lado del botón encargado de ejecutar la acción (dependiendo exactamente de dónde esté el botón de Generar Reporte).
- Al hacer clic en este botón, el programa Validará las entradas, ejecutará el análisis matemático y cargará una **Ventana Emergente (`CTkToplevel`)**.

### 1.2 La Ventana de Previsualización (Pop-up)
La nueva ventana será un visor organizado:
- **Estructura tipo Scroll:** Puesto que las pruebas pueden tener múltiples gráficas (especialmente la prueba de Recuperación que se agrupa por 40km/h, 50km/h, etc.), la ventana emergente debe tener un `CTkScrollableFrame`.
- **Organización Visual (Ejemplo de Recuperación):**
  1. **Título:** "Resultados Preliminares - Recuperación"
  2. **Sección 30 km/h:**
     - Gráfica de Velocidad vs Tiempo.
     - Gráfica de Aceleración vs Tiempo.
     - Pequeña celda o tabla resumen con los resultados calculados.
     - *Separador Visual*
  3. **Sección 40 km/h:**
     - ... (mismo formato)
- **Controles de la Ventana:**
  - Botón: "Cerrar" (Cancela y vuelve al menú anterior).
  - Botón: "Generar Reporte PDF" (Aprueba los datos expuestos y prosigue a la generación del documento final).

## 2. Flujo de Datos y Arquitectura

Para que la previsualización no obligue a recalcular todo cuando el usuario confirme el PDF, tenemos que ajustar el **`analysis_controller.py`** y el **`plotter.py`**.

### 2.1 Refactorización de `analysis_controller.py`
Actualmente, métodos como `process_recovery` realizan tres tareas en un solo bloque:
1. Extraer y calcular métricas (`analyzer.py`).
2. Generar imágenes (`plotter.py`).
3. Armar el PDF (`reporter.py`).

**Propuesta:** Dividir la lógica de orquestación.
- `controller.evaluate_data(...)`: Retorna diccionarios de resultados crudos y las imágenes renderizadas (en memoria `BytesIO`), o figuras de matplotlib (para mostrarlas en la UI de CustomTkinter usando `FigureCanvasTkAgg`).
- `controller.generate_pdf(resultados, imagenes)`: Toma los bloques que ya fueron calculados y los plasma en el PDF.

### 2.2 Integración de Gráficos en CustomTkinter (CTK)
Podemos exportamos las gráficas usando:
- **Opción A (Recomendada):** Guardar cada gráfica generada por `plotter.py` en un objeto de imagen de CTk (`CTkImage`) usando Pillow (`PIL.Image`). Esto es muy ligero y fácil de inyectar en la interfaz tipo grilla que ya usamos.
- **Opción B:** Usar `FigureCanvasTkAgg` nativo de Matplotlib para incrustarlo en Tkinter, dando posibilidad de zoom y paneo (quizás excesivo para una simple vista previa).

## 3. Próximos Pasos (Plan de Ejecución)
1. **Paso 1:** Crear un componente universal de UI (`PreviewWindow`) en `main.py` o módulo dedicado, el cual pueda renderizar títulos, imágenes y tablas básicas.
2. **Paso 2:** Modificar `analysis_controller.py` en una de las pruebas (por ejemplo, Frenado) para que devuelva los datos procesados en lugar de mandar a generar el PDF directamente.
3. **Paso 3:** Conectar el botón de la interfaz de la prueba a la ventana de visualización, pasándole los datos extraídos en el Paso 2.
4. **Paso 4:** Probar el flujo completo (Carga -> Análisis -> Preview -> PDF).
5. **Paso 5:** Replicar la arquitectura en las demás pruebas (Aceleración, Ascenso, Recuperación).

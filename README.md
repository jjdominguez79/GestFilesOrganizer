# GestFiles Organizer

Aplicación de escritorio para organizar documentación de clientes por año y mes, con interfaz operativa de despacho, trazabilidad de fecha documental y reporte Excel por ejecución.

## Qué se ha cambiado

- Se ha rehecho la pantalla inicial en `PySide6` con una home más corporativa y orientada a trabajo administrativo: cabecera de producto, panel de operaciones, módulo de clientes, estados visuales, progreso y log.
- La detección de fecha ya no usa una selección simple por regex. Ahora trabaja por candidatos, zonas del documento, etiquetas positivas/negativas, puntuación y decisión trazable.
- El Excel de detalle incorpora columnas de auditoría para la fecha elegida: confianza, etiqueta asociada, contexto, zona, página, revisión manual y motivo resumido.
- Se han añadido pruebas representativas para facturas con fecha de emisión, periodos, cargos y detalles de consumo.

## Cómo funciona la nueva detección de fechas

Pipeline actual:

1. Extracción de texto por páginas.
2. Recogida de todas las fechas candidatas de las primeras páginas.
3. Clasificación por zona del documento:
   - `header`
   - `top`
   - `party_block`
   - `body`
   - `table`
   - `footer`
4. Scoring con configuración centralizada en [`app_settings.py`](/c:/Users/GestinemFiscal/GestFilesOrganizer/app/config/app_settings.py):
   - etiquetas positivas fuertes: `fecha factura`, `fecha de emisión`, `invoice date`, etc.
   - etiquetas negativas fuertes: `vencimiento`, `fecha de cargo`, `periodo facturado`, `histórico`, etc.
   - pesos por zona, contexto, tablas, rangos de fechas y pistas de factura.
5. Selección de la mejor candidata solo si supera el umbral mínimo.
6. Si la confianza es baja o no supera el umbral, la fecha queda marcada para revisión manual o se usa el fallback de fecha de modificación si está activado.

La lógica está separada en:

- [`date_detection_engine.py`](/c:/Users/GestinemFiscal/GestFilesOrganizer/app/services/date_detection_engine.py): candidatos, scoring y selección.
- [`date_extractor.py`](/c:/Users/GestinemFiscal/GestFilesOrganizer/app/services/date_extractor.py): integración con extracción de texto, OCR opcional y fallback.
- [`document_processor.py`](/c:/Users/GestinemFiscal/GestFilesOrganizer/app/services/document_processor.py): uso del resultado estructurado y trazabilidad en logs.

## UI y framework

- La UI sigue en `PySide6`.
- No ha sido necesario cambiar de framework porque ya permitía un rediseño completo con mejor jerarquía visual y estados más claros.
- La paleta, tamaños y estilos globales están centralizados en [`theme.py`](/c:/Users/GestinemFiscal/GestFilesOrganizer/app/config/theme.py).

## Ejecución

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.venv\Scripts\python.exe organizador_clientes_gui.py
```

También puede ejecutarse con:

```powershell
.venv\Scripts\python.exe -m app.main
```

## Pruebas

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

# GestFiles Organizer

Aplicación de escritorio para organizar documentación de clientes por año y mes, con detección de fecha documental, resumen Excel por ejecución y gestión visual orientada a despacho profesional.

## Estructura del proyecto

```text
app/
  config/
  models/
  services/
  ui/
  utils/
  main.py
organizador_clientes_gui.py
requirements.txt
```

## Decisiones de implementación

- La base funcional de organización existente se ha mantenido y repartido en servicios especializados.
- La interfaz se ha migrado de Tkinter a `PySide6` para conseguir una experiencia más profesional, mejor separación entre UI y lógica, y un camino más limpio para empaquetado futuro en Windows.
- El Excel se genera por cliente y por ejecución actual, no sobre histórico, para evitar mezclar lotes y facilitar auditoría.
- El renombrado de carpeta elimina `_` al final del proceso solo si no hubo errores críticos de procesamiento o de generación de Excel. Si falla el renombrado, los documentos ya movidos o copiados no se revierten.

## Funcionalidad actual

- Selección de carpeta raíz y escaneo de subcarpetas de clientes.
- Marcado manual, marcado global y marcado solo de carpetas con `_`.
- Filtro visual para mostrar solo carpetas con `_`.
- Estados visuales por cliente: pendiente, en proceso, procesado y error.
- Organización de PDFs e imágenes por `AAAA/AAAA-MM`.
- Detección de fecha por texto PDF, OCR PDF, OCR imagen, fecha de modificación o sin fecha.
- Opción mover o copiar.
- Detección de archivos ya organizados para no reprocesarlos.
- Renombrado automático de carpetas para quitar `_` al finalizar.
- Generación de Excel con hojas `Resumen` y `Detalle`.
- Parsing heurístico de campos de factura con tolerancia a documentos sin datos extraíbles.
- Log visual exportable.
- Procesamiento en hilo para no bloquear la UI.

## Requisitos

- Python 3.11 o superior recomendado.
- Windows 10/11 recomendado para el flujo de escritorio y empaquetado.
- `Tesseract OCR` y `Poppler` solo si más adelante se activa OCR real de imágenes/PDF escaneados.

## Instalación

1. Crear y activar entorno virtual:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

## Ejecución

```powershell
.venv\Scripts\python.exe organizador_clientes_gui.py
```

También puede ejecutarse con:

```powershell
.venv\Scripts\python.exe -m app.main
```

## Dependencias principales

- `PySide6`: interfaz gráfica profesional.
- `PyPDF2`: extracción de texto PDF.
- `openpyxl`: generación del Excel.
- `Pillow`, `pytesseract`, `pdf2image`: soporte OCR opcional.

## Personalización visual y de empresa

- Los textos de producto, propietario, teléfono, portal y web se configuran en [`app_settings.py`](/c:/Users/GestinemFiscal/GestFilesOrganizer/app/config/app_settings.py).
- La paleta y estilos globales se controlan desde [`theme.py`](/c:/Users/GestinemFiscal/GestFilesOrganizer/app/config/theme.py).

## OCR opcional

La configuración actual deja OCR desactivado por defecto en [`app_settings.py`](/c:/Users/GestinemFiscal/GestFilesOrganizer/app/config/app_settings.py).  
Si se quiere activar:

1. Instalar Tesseract OCR.
2. Instalar Poppler si se desea OCR sobre PDFs escaneados.
3. Ajustar `enabled=True` y la ruta `tesseract_cmd`.

## Empaquetado básico con PyInstaller

Instalar PyInstaller:

```powershell
pip install pyinstaller
```

Generar ejecutable:

```powershell
pyinstaller --noconfirm --windowed --name GestFilesOrganizer organizador_clientes_gui.py
```

Si se añaden logos o recursos en `app/assets/`, habrá que incluirlos con `--add-data`.

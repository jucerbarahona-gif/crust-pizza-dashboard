# San Francisco Crust Pizza — Aplicación y entrega académica

## Qué contiene este proyecto

- `app.py`: aplicación web para indicadores, gráficos, filtros, calidad de datos, subida de Ventas, Clientes y Productos y asistente de IA.
- `analytics.py`: validaciones, cálculos y agregaciones reproducibles.
- `datos/ventas.csv`, `datos/clientes.csv`, `datos/productos.csv`: datos para abrir el dashboard, extraídos de los Excel originales sin recalcular sus importes. El CSV de clientes incluye únicamente los campos analíticos necesarios (no los nombres).
- `datos/*xlsx`: bases académicas originales (referencia y comprobación).
- `Informe_Ejecutivo_Crust_Pizza.docx`: informe listo para revisar y personalizar (4 páginas).
- `Presentacion_Crust_Pizza_7_diapositivas.pptx`: siete diapositivas con análisis real.
- `Guion_Video_Crust_Pizza.docx`: guion de grabación de pantalla con partes asignadas.
- `Hoja_Control_Equipo.docx`: hoja de control **propuesta**; si la universidad proporcionó una plantilla oficial, úsala en su lugar.
- `tests_preparar.py`: pruebas de cálculo, carga de los tres Excel/CSV y actualización de datos.

## 1. Probar la aplicación en una computadora

Instala Python 3.11 o 3.12. Descomprime el ZIP conservando las carpetas. Abre una terminal en la carpeta que tiene `app.py`.

```bash
python -m venv .venv
```

Activa el entorno:

- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

Instala dependencias y arranca:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abre el enlace local que muestra Streamlit (normalmente `http://localhost:8501`).

## 2. Publicar la aplicación para el profesor

La universidad pide un enlace **público y operativo**. Esta es una ruta de publicación, sujeta a la plataforma y permisos de quien administre la cuenta:

1. Entra a GitHub, crea preferentemente un repositorio privado para el proyecto y sube solamente los archivos necesarios para la aplicación: `app.py`, `analytics.py`, `requirements.txt`, `.streamlit/config.toml` y `datos/*.csv`. No subas los Excel originales a un repositorio público, porque incluyen nombres de clientes; los CSV proporcionados son suficientes para ejecutar la app.
2. Abre [Streamlit Community Cloud](https://share.streamlit.io/) y accede con GitHub.
3. Selecciona **Create app**, indica el repositorio, la rama (p. ej., `main`) y el archivo principal **`app.py`**.
4. Pulsa **Deploy**. Streamlit proporcionará un enlace del tipo `https://<nombre>.streamlit.app`.
5. Copia el enlace y ábrelo desde una ventana privada o dispositivo diferente para comprobar que carga sin pedir permiso.
6. Comprueba los seis KPI, las pestañas, los cinco filtros, la actualización de ventas y el asistente.
7. Inserta la URL real en el informe o en la hoja de control y en la presentación, y entrégala con el resto de archivos.

Documentación oficial: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

**Importante:** el archivo `.streamlit/secrets.toml` o una credencial privada no se debe subir a un repositorio público.

## 3. Activar la inteligencia artificial generativa

La aplicación incluye la integración preparada, pero **sin clave API no se han probado ni generado recomendaciones de IA externa**. Los hechos que aparecen automáticamente son cálculos internos y están etiquetados como tales.

- Si tienen permiso y una clave válida de API compatible, entra a la configuración de tu aplicación en Streamlit Community Cloud, sección **Secrets**.
- Agrega una línea de esta forma (con tu clave real en la plataforma, no en código fuente):

```toml
OPENAI_API_KEY = "TU_CLAVE_PRIVADA_AQUI"
```

- Guarda, reinicia la aplicación si es necesario y abre **Asistente IA**.
- Realiza una consulta. Comprueba que el asistente devuelve recomendaciones ancladas en los indicadores; contrástalas con la pestaña de datos.
- Si recibes un error, revisa el acceso, los permisos y el modelo que tu servicio tenga habilitado. Esta función puede tener costos de API.

Documentación oficial sobre secretos: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management

**No compartas la clave por WhatsApp, capturas, archivos de proyecto ni un repositorio.**

## 4. Cargar los tres archivos originales y actualizar las ventas

1. Abre la app y expande **Cargar o actualizar bases de datos** en la barra izquierda.
2. Verás tres botones independientes: **1. Ventas**, **2. Clientes** y **3. Productos**. Aceptan los Excel `.xlsx` originales de la universidad y también `.csv` con las mismas columnas.
3. La aplicación ya muestra un análisis de los CSV de ejemplo del ZIP. Para comprobar la carga inicial, selecciona los tres Excel incluidos en `datos/`. La aplicación validará las relaciones y debe mostrar los mismos resultados.
4. Para mostrar la **actualización automática** que exige la actividad, prepara un archivo nuevo de Ventas que conserve las columnas originales y selecciona únicamente **1. Ventas**. Los indicadores y todas las gráficas se recalculan al subirlo, sin editar el código. **Clientes** y **Productos** pueden permanecer como están.
5. Prueba los cinco filtros. Si subes un archivo con columnas incompletas, fechas inválidas o códigos desconocidos, la aplicación muestra un mensaje en lugar de utilizar datos incorrectos.
6. Para restablecer la base de ejemplo, pulsa la cruz de cada archivo seleccionado dentro de su cargador (o actualiza la sesión si es necesario).

**Limitación técnica:** los archivos cargados son temporales por sesión; no sobrescriben el repositorio ni los archivos originales. **Privacidad:** el Excel de Clientes contiene nombres personales; evita compartirlo o publicarlo en repositorios abiertos. El código usa los campos analíticos mínimos y no envía nombres al asistente de IA.

## 5. Qué se comprobó en los datos originales

- 45.900 filas de Ventas, 1.000 Clientes y 44 Productos.
- Periodo de Ventas: 2024-01-01 a 2025-12-28.
- Ventas netas: US$1.357.881,66.
- Utilidad bruta: US$813.713,76.
- Margen bruto: 59,93 %.
- Ticket promedio: US$29,58 por VentaID.
- No existen errores mayores a US$0,03 al recomputar costo, venta neta y utilidad.
- Los precios y costos históricos no coinciden con el catálogo por referencia. Por ello el cálculo financiero usa las columnas de Ventas.
- Los contadores acumulados de 986 clientes no coinciden con el número de transacciones de Ventas; el estado de actividad se debe validar.

## 6. Cronograma sugerido para entregar el 29/11/2026

| Fecha | Responsable | Acción |
|---|---|---|
| Vie. 27 | Integrantes 1 y 2 | Revisar datos, indicadores, filtros y gráficas. Corregir problemas de interfaz. |
| Vie. 27 | Integrante 3 | Crear repositorio, desplegar la aplicación, activar IA con credencial si está disponible. |
| Sáb. 28 | Integrantes 1 y 4 | Revisar análisis y completar nombres, número de equipo y enlace público en archivos. |
| Sáb. 28 | Los cuatro | Grabar y montar video, enviar entrega completa. |
| Dom. 29 | Respaldo | Resolver únicamente contratiempos, no comenzar desarrollo. |

## 7. Requisitos y límites que conviene conocer

- El enunciado menciona 6 páginas en una sección y 5 páginas para el informe en otra. El informe proporcionado tiene 4 páginas, para respetar ambos límites.
- El informe y las diapositivas contienen resultados calculados; el equipo debe revisar y aprobar las decisiones, no solo copiar recomendaciones.
- No existe todavía un enlace público real ni un video grabado; esos pasos requieren una cuenta de despliegue y grabación del funcionamiento real.
- La hoja de control adjunta es una plantilla orientativa, no se ha verificado que coincida con el formato oficial de la universidad.

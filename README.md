# Laboratorio 4 — Datos geoespaciales (versión notebook)

**Curso:** CC3084 · Data Science · Semestre 02, 2026

Esta es una versión independiente del laboratorio, organizada según la convención del repositorio de referencia del curso. Todo el desarrollo, las explicaciones y las salidas de los ejercicios 1 al 8 están en un único cuaderno:

```text
notebooks/laboratorio-4-datos-geoespaciales.ipynb
```

El notebook contiene la conexión con openEO, la definición de la descarga, el cálculo de índices, el análisis temporal y espacial, las correlaciones, la comparación entre lagos y los análisis adicionales. Las salidas quedan incrustadas para que el entregable pueda leerse sin volver a descargar los rasters.

## Integrantes y distribución

| Integrante | Ejercicios | Trabajo |
|---|---:|---|
| Daniel Chet | 1–4 | Conexión openEO, descarga, índices y análisis temporal; corresponde al avance ya realizado |
| Javier Linares | 5–6 | Mapas y análisis espacial; correlaciones temporales y a nivel de píxel |
| Dulce Ambrosio | 7–8 | Comparación formal entre lagos; extensión, distribuciones, persistencia y estacionalidad |

El detalle de tareas y productos se encuentra en `DISTRIBUCION_TRABAJO.md`.

## Estructura

```text
version_notebook/
├── notebooks/          # notebook principal, ejecutado y con salidas
├── data/raw/           # GeoTIFF de Sentinel-2 descargados; no se versionan
├── data/processed/     # índices raster derivados; no se versionan
├── results/            # tablas y figuras generadas por el notebook
├── build_nb.py         # generador reproducible del notebook
├── codebook.md         # descripción de variables, bandas y umbrales
├── requirements.txt
└── README.md
```

Para no duplicar aproximadamente 315 MB, esta copia local reutiliza automáticamente los rasters ya descargados en `../datos/raster/` y `../resultados/indices/`. Si esas carpetas no existen, el notebook usa `data/raw/` y `data/processed/` dentro de esta versión.

## Cómo ejecutarlo

Desde esta carpeta:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 notebooks\laboratorio-4-datos-geoespaciales.ipynb
```

También puede abrirse en JupyterLab o VS Code y ejecutarse de arriba hacia abajo.

## Regenerar el notebook

```powershell
..\.venv\Scripts\python.exe build_nb.py
```

La autenticación de descarga usa OIDC en el navegador. El notebook no guarda usuario, contraseña ni tokens dentro del proyecto.

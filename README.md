# Laboratorio 4 — Datos geoespaciales (versión notebook)

**Curso:** CC3084 · Data Science · Semestre 02, 2026

Esta es una versión independiente del laboratorio, organizada según la convención del repositorio de referencia del curso. Todo el desarrollo, las explicaciones y las salidas están en un único cuaderno:

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

## Estructura

```text
Lab4-Analisis-Geoespacial/
├── notebooks/          # notebook principal, ejecutado y con salidas
├── data/raw/           # GeoTIFF de Sentinel-2 descargados; no se versionan
├── data/processed/     # índices raster derivados; no se versionan
├── results/            # tablas y figuras generadas por el notebook
├── codebook.md         # descripción de variables, bandas y umbrales
├── requirements.txt
└── README.md
```

Para no duplicar aproximadamente 315 MB, el notebook usa `data/raw/` y `data/processed/` para almacenar los datos descargados localmente, sin embargo se adjuntara un link con un zip con los datos crudos para una replicacion mas sencilla. [Raster.rar](https://drive.google.com/file/d/1KXpNmaA0zDZxkLs7ox1u0fcUC86VvBuv/view?usp=sharing)

## Dónde colocar los datos

El notebook supone que `Lab4-Analisis-Geoespacial/` es la raíz del proyecto. Los GeoTIFF originales de Sentinel-2 deben colocarse dentro de `data/raw/`, separados por lago:

```text
Lab4-Analisis-Geoespacial/
└── data/
    └── raw/
        ├── amatitlan/
        │   ├── 2025-01-28.tif
        │   ├── 2025-04-15.tif
        │   ├── 2025-04-28.tif
        │   ├── 2025-11-24.tif
        │   ├── 2026-01-08.tif
        │   ├── 2026-02-02.tif
        │   ├── 2026-02-07.tif
        │   ├── 2026-03-29.tif
        │   ├── 2026-04-13.tif
        │   ├── 2026-04-28.tif
        │   └── 2026-06-19.tif
        └── atitlan/
            ├── 2025-01-18.tif
            ├── 2025-04-13.tif
            ├── 2025-05-13.tif
            ├── 2025-07-17.tif
            ├── 2025-11-21.tif
            ├── 2025-12-29.tif
            ├── 2026-02-12.tif
            ├── 2026-03-24.tif
            ├── 2026-04-13.tif
            ├── 2026-04-28.tif
            └── 2026-07-22.tif
```

En total deben existir **22 GeoTIFF originales: 11 de Amatitlán y 11 de Atitlán**. Los nombres deben conservar exactamente el formato `AAAA-MM-DD.tif` porque el notebook busca las fechas oficiales con esos nombres.


### Índices procesados

No es obligatorio copiar previamente los índices. Si únicamente están disponibles los 22 archivos originales, el notebook calcula los productos derivados y los guarda automáticamente en:

```text
data/processed/indices/amatitlan/AAAA-MM-DD_indices.tif
data/processed/indices/atitlan/AAAA-MM-DD_indices.tif
```

Si los índices ya fueron calculados, pueden colocarse directamente con esta estructura para evitar reprocesarlos:

```text
Lab4-Analisis-Geoespacial/
└── data/
    └── processed/
        └── indices/
            ├── amatitlan/
            │   └── 11 archivos con el sufijo `_indices.tif`
            └── atitlan/
                └── 11 archivos con el sufijo `_indices.tif`
```

Aunque existan los índices procesados, la versión actual del notebook valida el inciso de descarga comprobando los 22 archivos de `data/raw/`. Por eso, para ejecutar todas las celdas de principio a fin, los rasters originales siempre deben estar presentes.

Las tablas y figuras creadas durante la ejecución se guardan en `results/`. No se deben colocar manualmente rasters dentro de esa carpeta.


## Cómo ejecutarlo

Desde esta carpeta:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 notebooks\laboratorio-4-datos-geoespaciales.ipynb
```

También puede abrirse en JupyterLab o VS Code y ejecutarse de arriba hacia abajo.


La autenticación de descarga usa OIDC en el navegador. El notebook no guarda usuario, contraseña ni tokens dentro del proyecto.


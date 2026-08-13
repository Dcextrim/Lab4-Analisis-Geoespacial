# Laboratorio 4 

**Curso:** CC3084 · Data Science · Semestre 02, 2026

Esta carpeta contiene el entregable principal

```text
notebooks/laboratorio-4.ipynb
```

El cuaderno incluye:

1. conexión y evidencia de la API openEO;
2. áreas, fechas oficiales, bandas mínimas y función de descarga;
3. cálculo de NDVI, NDWI, NDCI, FAI, máscara de agua y estimador de cianobacterias;
4. análisis temporal de las 11 fechas de cada lago.

## Estructura

```text
Lab4-Analisis-Geoespacial/
├── notebooks/          # notebook ejecutado, con tablas y gráfico incrustados
├── data/raw/           # rasters descargados; no se versionan
├── data/processed/     # índices raster; no se versionan
├── results/            # evidencia, resumen y gráfico temporal
├── codebook.md
├── requirements.txt
└── README.md
```

Para evitar datos pesados, no se adjuntan la data utilizada sin embargo hay codigo para descargarlo y manejar la data localmente donde se utilizan las carpetas `data/`.

## Ejecutar

Desde esta carpeta:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 notebooks\laboratorio-4.ipynb
```

La autenticación de descarga usa OIDC en el navegador. No se guardan credenciales en el notebook.

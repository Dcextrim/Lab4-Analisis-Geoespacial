# Laboratorio 4, Parte 2 - Modelos con datos geoespaciales

**Curso:** CC3084 Ciencia de Datos, Universidad del Valle de Guatemala  
**Avance:** Ejercicios 1, 2 y 3  
**Área de estudio:** lagos de Atitlán y Amatitlán, Guatemala

Este repositorio implementa el Patrón A exigido en CC3084: un pipeline de scripts secuenciales con responsabilidades únicas y un notebook separado para EDA y mapas. La unidad de análisis es un píxel Sentinel-2 de 20 m para un lago y una fecha. Los 22 GeoTIFF crudos se consideran inmutables; todas las tablas derivadas se regeneran ejecutando el pipeline de principio a fin.

## Estructura

```text
Lab4.2/
├── data/
│   ├── raw/                         # 22 GeoTIFF originales; inmutables
│   └── processed/                   # salidas 01, 02 y 03; regenerables
├── informe/
│   └── informe_avance.md            # redacción académica y referencias
├── notebooks/
│   └── 01_analisis_exploratorio.ipynb
├── output/pdf/
│   └── informe_avance_ejercicios_1_2_3.pdf
├── results/                         # figuras generadas por el notebook
├── src/
│   ├── 01_preparacion_datos.py
│   ├── 02_construccion_respuesta.py
│   └── 03_variables_predictoras.py
├── codebook.md
├── README.md
└── requirements.txt
```

`data/raw/` y `data/processed/` no se versionan en Git por su tamaño. No se debe editar ni reemplazar manualmente ningún valor en `data/raw/`. La reproducibilidad se conserva porque las salidas procesadas se producen únicamente con los scripts versionados.

## Pipeline secuencial

| Script | Archivo generado | Responsabilidad única | Entrada | Salida |
|---|---|---|---|---|
| `src/01_preparacion_datos.py` | `data/processed/01_datos_limpios.csv` | Validar los 22 GeoTIFF; escalar reflectancia; remover NoData, valores inválidos, nubes brillantes y píxeles que no pertenecen al agua de los lagos; calcular índices auditables | `data/raw/{lago}/AAAA-MM-DD.tif` | Una fila por píxel válido, con bandas, coordenadas, NDVI, NDWI, NDCI e índice cuantitativo |
| `src/01_preparacion_datos.py` | `data/processed/01_reporte_limpieza.csv` | Registrar la trazabilidad de exclusiones | Conteos internos del paso 01 | Conteos por lago y fecha |
| `src/02_construccion_respuesta.py` | `data/processed/02_datos_con_respuesta.csv` | Crear `presencia_alta_cianobacterias` con umbral inclusivo de 20 mg/m³ | `01_datos_limpios.csv` | Datos limpios con respuesta binaria |
| `src/02_construccion_respuesta.py` | `02_configuracion_respuesta.json`, `02_distribucion_clases.csv` | Documentar umbral, fuga y balance de clases | Salida del paso 02 | Manifiesto y conteos auditables |
| `src/03_variables_predictoras.py` | `data/processed/03_datos_listos_modelado.csv` | Construir variables adicionales y eliminar físicamente predictores con fuga | `02_datos_con_respuesta.csv` | Matriz final sin `B04`, `B05`, `NDCI`, índice objetivo ni `NDVI` |
| `src/03_variables_predictoras.py` | `03_variables_modelado.json` | Declarar roles de columnas y partición recomendada | Esquema final | Manifiesto de predictores |

## Decisión crítica sobre fuga de datos

El índice cuantitativo es una función determinista de `NDCI=(B05-B04)/(B05+B04)`. Por tanto, `indice_cianobacterias_mg_m3`, `ndci`, `b04` y `b05` no pueden formar parte de `X`. `NDVI` también se excluye del modelado porque reutiliza `B04`. Estas variables permanecen en el archivo 02 exclusivamente para trazabilidad y para las gráficas solicitadas; el script 03 las elimina del archivo final. Incluirlas produciría una validación circular, no capacidad predictiva.

## Cómo correrlo

Los comandos siguientes se ejecutan desde `Lab4.2/` en PowerShell. Se recomienda Python 3.11 o 3.12.

```powershell
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Ejecutar el pipeline en orden estricto:

```powershell
& .\.venv\Scripts\python.exe .\src\01_preparacion_datos.py
& .\.venv\Scripts\python.exe .\src\02_construccion_respuesta.py
& .\.venv\Scripts\python.exe .\src\03_variables_predictoras.py
```

Ejecutar y guardar el notebook con todas sus salidas:

```powershell
& .\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1800 .\notebooks\01_analisis_exploratorio.ipynb
```

Las cinco figuras quedan en `results/`. Para una verificación mínima del pipeline:

```powershell
Get-Item .\data\processed\01_datos_limpios.csv
Get-Item .\data\processed\02_datos_con_respuesta.csv
Get-Item .\data\processed\03_datos_listos_modelado.csv
Get-Content .\data\processed\03_variables_modelado.json
```

## Consideraciones de modelado

- No dividir píxeles aleatoriamente: la autocorrelación espacial haría que píxeles vecinos aparezcan en entrenamiento y prueba. La partición debe hacerse por fecha o por bloques espaciales.
- Priorizar PR-AUC, recall, precision y F1 de la clase 1, además de la matriz de confusión. Accuracy se reporta únicamente junto a un baseline de clase mayoritaria.
- Cualquier ponderación o remuestreo debe ajustarse dentro de cada pliegue de entrenamiento, nunca antes de separar los datos.
- El umbral de 20 mg/m³ es un criterio operativo de detección remota, no una declaración de aptitud recreacional ni un diagnóstico toxicológico.

La explicación científica, las limitaciones y las referencias completas están en [informe/informe_avance.md](informe/informe_avance.md). El diccionario de datos y todas las reglas de transformación están en [codebook.md](codebook.md).

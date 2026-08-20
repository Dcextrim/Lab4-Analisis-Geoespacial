# Codebook - Laboratorio 4, Parte 2

## Unidad de análisis

Cada fila de `03_datos_listos_modelado.csv` representa el centro de un píxel Sentinel-2 de 20 m que fue clasificado como agua válida dentro del rectángulo de estudio de Atitlán o Amatitlán en una fecha. Todos los ráster están en un CRS proyectado y las coordenadas se expresan en metros. El conjunto final no contiene valores faltantes.

## Diccionario del dataset final

| Nombre | Tipo pandas | Descripción | Valores válidos / unidad | Rol |
|---|---|---|---|---|
| `lago` | `string` | Nombre legible del lago | `Amatitlan`, `Atitlan` | Identificador; no predictor |
| `lago_id` | `string` | Identificador normalizado | `amatitlan`, `atitlan` | Identificador; no predictor |
| `fecha` | `string` convertible a `datetime64[ns]` | Fecha de adquisición | `AAAA-MM-DD` | Grupo temporal; no predictor |
| `satelite` | `string` | Plataforma de Sentinel-2 | `Sentinel-2A`, `Sentinel-2B`, `Sentinel-2C` | Metadato; no predictor |
| `nubosidad_escena_pct` | `float64` | Nubosidad reportada para la escena | 0 a 100 % | Metadato; no predictor |
| `crs` | `string` | Sistema de referencia del GeoTIFF | CRS proyectado, actualmente `EPSG:32615` | Metadato |
| `fila` | `int64` | Índice de fila en el ráster fuente | Entero no negativo | Identificador espacial |
| `columna` | `int64` | Índice de columna en el ráster fuente | Entero no negativo | Identificador espacial |
| `coordenada_x` | `float64` | Este del centro del píxel | Metros en `crs` | Identificador espacial |
| `coordenada_y` | `float64` | Norte del centro del píxel | Metros en `crs` | Identificador espacial |
| `b02` | `float64` | Reflectancia TOA azul, ~490 nm | -0.05 a 1.50, adimensional | Predictor |
| `b03` | `float64` | Reflectancia TOA verde, ~560 nm | -0.05 a 1.50, adimensional | Predictor |
| `b07` | `float64` | Reflectancia de borde rojo 3, ~783 nm | -0.05 a 1.50, adimensional | Predictor |
| `b08` | `float64` | Reflectancia NIR ancha, ~842 nm | -0.05 a 1.50, adimensional | Predictor |
| `b8a` | `float64` | Reflectancia NIR estrecha, ~865 nm | -0.05 a 1.50, adimensional | Predictor |
| `b11` | `float64` | Reflectancia SWIR 1, ~1610 nm | -0.05 a 1.50, adimensional | Predictor |
| `b12` | `float64` | Reflectancia SWIR 2, ~2190 nm | -0.05 a 1.50, adimensional | Predictor |
| `ndwi` | `float64` | Índice de agua `(B03-B08)/(B03+B08)` | -1 a 1 | Predictor |
| `indice_turbidez_azul_verde` | `float64` | Contraste normalizado `(B03-B02)/(B03+B02)` | -1 a 1 | Predictor experimental |
| `razon_borde_rojo_verde` | `float64` | Razón `B07/B03`; proxy experimental de pendiente espectral asociada con biomasa/pigmentos | No negativo en observaciones válidas | Predictor experimental |
| `presencia_alta_cianobacterias` | `int64` | Respuesta binaria construida con el índice cuantitativo | `0` si índice < 20 mg/m³; `1` si índice ≥ 20 mg/m³ | Respuesta |

Aunque al leer el CSV pandas puede inferir `float64` e `int64`, los arreglos ráster se procesan originalmente como `float32` y la respuesta se construye como `int8`. Esta diferencia de almacenamiento no cambia el significado de las variables.

## Variables auditables del archivo 02 que no llegan al conjunto final

| Variable | Fórmula / origen | Motivo de exclusión de predictores |
|---|---|---|
| `indice_cianobacterias_mg_m3` | `clip(826.57*NDCI³ - 176.43*NDCI² + 19*NDCI + 4.071, 0, 500)` | Es la variable continua umbralizada para obtener la respuesta |
| `ndci` | `(B05-B04)/(B05+B04)` | La respuesta es una función determinista de esta variable |
| `b04` | Reflectancia roja | Entrada directa de NDCI |
| `b05` | Reflectancia de borde rojo 1 | Entrada directa de NDCI |
| `ndvi` | `(B08-B04)/(B08+B04)` | Comparte B04 con la construcción de la respuesta; se retiene solo para EDA |

## Reglas de limpieza y transformación

Las reglas se aplican en el orden indicado, de modo que los conteos de exclusión no duplican píxeles.

1. Exigir exactamente 22 GeoTIFF con las combinaciones oficiales de lago y fecha.
2. Exigir nueve bandas numéricas y ordenadas: `B02`, `B03`, `B04`, `B05`, `B07`, `B08`, `B8A`, `B11`, `B12`.
3. Exigir CRS proyectado, dimensiones positivas y resolución espacial entre 19.5 m y 20.5 m.
4. Detectar la escala de reflectancia: multiplicar por `0.0001` cuando el percentil 99 de una muestra es mayor que 2; de lo contrario conservar la escala 0-1.
5. Remover máscaras internas, NoData, infinitos, NaN y píxeles con las nueve bandas iguales a cero.
6. Remover reflectancias fuera de `[-0.05, 1.50]`.
7. Remover nubes brillantes mediante una heurística L1C que combina brillo visible, blancura y SWIR. Los insumos no incluyen SCL ni QA60; por ello esta máscara no se considera equivalente a Sen2Cor.
8. Remover tierra y píxeles fuera del lago con una máscara multiespectral de agua basada en NDWI, MNDWI, AWEI, NDVI y DBSI dentro del rectángulo geográfico de cada lago.
9. Calcular NDVI, NDWI, NDCI e índice cuantitativo; remover cualquier resultado no finito.
10. Crear `presencia_alta_cianobacterias` con comparación inclusiva `>= 20 mg/m³`.
11. Calcular las dos variables adicionales usando únicamente bandas no involucradas en la etiqueta.
12. Eliminar físicamente del archivo final las cinco variables con fuga indicadas arriba.

## Reglas de uso

- `lago`, `fecha`, coordenadas, fila y columna son variables de agrupación, no predictores por defecto.
- La partición debe hacerse por fecha o bloques espaciales para evitar transferencia de píxeles vecinos entre entrenamiento y prueba.
- Los dos índices adicionales son hipótesis espectrales. Deben validarse con mediciones in situ antes de interpretarlos como concentración física.
- La clase 1 significa alta presencia **operativa** para este análisis; no equivale a una alerta sanitaria de la OMS.

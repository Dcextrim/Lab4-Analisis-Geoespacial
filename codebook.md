# Codebook — Laboratorio 4

## Observaciones

Se utilizan 22 observaciones oficiales: 11 del lago Amatitlán y 11 del lago Atitlán. Cada producto se trabaja a 20 m en EPSG:32615.

## Bandas

| Banda | Uso principal |
|---|---|
| B02, B11, B12 | Máscara de agua |
| B03, B08 | NDWI |
| B04, B08 | NDVI |
| B04, B05 | NDCI y estimador de clorofila-a |
| B04, B07, B8A | Floating Algal Index |

## Variables del resumen temporal

| Variable | Descripción |
|---|---|
| `cyano_promedio_mg_m3` | Promedio del estimador sobre agua válida |
| `cyano_mediana_mg_m3` | Mediana espacial por fecha |
| `cyano_p95_mg_m3` | Percentil 95 espacial por fecha |
| `ndvi_promedio_agua` | NDVI promedio sobre la máscara de agua |
| `ndwi_promedio_agua` | NDWI promedio sobre la máscara de agua |
| `area_agua_valida_km2` | Área válida utilizada en el resumen |

El Q75 marca fechas relativamente altas dentro de cada lago. No es un límite sanitario.


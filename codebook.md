# Codebook — Laboratorio 4

## Unidad de análisis

Cada observación representa un lago y una fecha oficial del laboratorio. Se analizaron 11 fechas del lago Amatitlán y 11 del lago Atitlán. Los rasters se trabajan a 20 m en EPSG:32615.

## Bandas Sentinel-2 L1C

| Banda | Uso |
|---|---|
| B02 | Azul; máscara de agua |
| B03 | Verde; NDWI y máscara |
| B04 | Rojo; NDVI, NDCI y FAI |
| B05 | Borde rojo; NDCI |
| B07 | Borde rojo 3; FAI |
| B08 | Infrarrojo cercano; NDVI y NDWI |
| B8A | Infrarrojo cercano estrecho; FAI |
| B11 | SWIR 1; máscara de agua |
| B12 | SWIR 2; máscara de agua |

## Productos derivados

| Variable | Descripción |
|---|---|
| `NDVI` | `(B08-B04)/(B08+B04)` calculado únicamente sobre agua válida |
| `NDWI` | `(B03-B08)/(B03+B08)` calculado únicamente sobre agua válida |
| `NDCI` | `(B05-B04)/(B05+B04)` |
| `CYANO_CHLA` | Clorofila-a estimada con el polinomio del evalscript de Sentinel Hub, en mg/m³ |
| `FAI` | Floating Algal Index |
| `WATER_MASK` | Máscara binaria de agua del mismo evalscript |

## Definiciones exploratorias

- Concentración alta principal: `CYANO_CHLA ≥ 20 mg/m³`.
- Sensibilidad: umbrales alternativos de 10 y 30 mg/m³.
- Fecha extensa: al menos 5% del agua válida alcanza 20 mg/m³.
- Zona persistente: alcanza 20 mg/m³ en al menos 50% de sus fechas válidas, con un mínimo de seis observaciones.
- Época seca: noviembre–abril; época lluviosa: mayo–octubre.

Estas definiciones permiten comparar fechas y lagos. No constituyen límites sanitarios.


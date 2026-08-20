"""Ejercicio 1: limpia los GeoTIFF crudos y genera observaciones por pixel.

La unidad de analisis es un pixel de 20 m perteneciente al agua valida de uno
de los lagos en una fecha. El script nunca modifica ``data/raw``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


RAIZ_LABORATORIO = Path(__file__).resolve().parents[1]
DIRECTORIO_CRUDO = RAIZ_LABORATORIO / "data" / "raw"
DIRECTORIO_PROCESADO = RAIZ_LABORATORIO / "data" / "processed"
RUTA_SALIDA = DIRECTORIO_PROCESADO / "01_datos_limpios.csv"

BANDAS_ESPERADAS = ("b02", "b03", "b04", "b05", "b07", "b08", "b8a", "b11", "b12")
NOMBRES_LAGOS = {"amatitlan": "Amatitlan", "atitlan": "Atitlan"}
LIMITES_LAGOS = {
    "amatitlan": {"oeste": -90.638065, "este": -90.512924, "sur": 14.412347, "norte": 14.493799},
    "atitlan": {"oeste": -91.326256, "este": -91.071510, "sur": 14.594800, "norte": 14.750979},
}
METADATOS_ESCENAS = {
    ("amatitlan", "2025-01-28"): ("Sentinel-2B", 0.06),
    ("amatitlan", "2025-04-15"): ("Sentinel-2A", 0.09),
    ("amatitlan", "2025-04-28"): ("Sentinel-2B", 1.03),
    ("amatitlan", "2025-11-24"): ("Sentinel-2B", 0.50),
    ("amatitlan", "2026-01-08"): ("Sentinel-2C", 0.77),
    ("amatitlan", "2026-02-02"): ("Sentinel-2B", 0.39),
    ("amatitlan", "2026-02-07"): ("Sentinel-2C", 0.02),
    ("amatitlan", "2026-03-29"): ("Sentinel-2C", 0.01),
    ("amatitlan", "2026-04-13"): ("Sentinel-2B", 0.09),
    ("amatitlan", "2026-04-28"): ("Sentinel-2C", 4.96),
    ("amatitlan", "2026-06-19"): ("Sentinel-2A", 13.00),
    ("atitlan", "2025-01-18"): ("Sentinel-2B", 0.02),
    ("atitlan", "2025-04-13"): ("Sentinel-2C", 0.54),
    ("atitlan", "2025-05-13"): ("Sentinel-2C", 4.37),
    ("atitlan", "2025-07-17"): ("Sentinel-2A", 3.57),
    ("atitlan", "2025-11-21"): ("Sentinel-2A", 3.15),
    ("atitlan", "2025-12-29"): ("Sentinel-2C", 3.17),
    ("atitlan", "2026-02-12"): ("Sentinel-2B", 0.04),
    ("atitlan", "2026-03-24"): ("Sentinel-2B", 3.17),
    ("atitlan", "2026-04-13"): ("Sentinel-2B", 0.01),
    ("atitlan", "2026-04-28"): ("Sentinel-2C", 4.96),
    ("atitlan", "2026-07-22"): ("Sentinel-2B", 4.02),
}


def diferencia_normalizada(arreglo_a: np.ndarray, arreglo_b: np.ndarray) -> np.ndarray:
    """Calcula una diferencia normalizada sin dividir entre valores cercanos a cero."""
    denominador = arreglo_a + arreglo_b
    resultado = np.full(arreglo_a.shape, np.nan, dtype=np.float32)
    return np.divide(
        arreglo_a - arreglo_b,
        denominador,
        out=resultado,
        where=np.abs(denominador) > 1e-8,
    )


def validar_estructura_entrada() -> list[Path]:
    """Valida de forma fail-fast la estructura y devuelve los 22 GeoTIFF."""
    if not DIRECTORIO_CRUDO.is_dir():
        raise FileNotFoundError(f"No existe el directorio de datos crudos: {DIRECTORIO_CRUDO}")

    archivos = sorted(DIRECTORIO_CRUDO.glob("*/*.tif"))
    if len(archivos) != 22:
        raise ValueError(f"Se esperaban exactamente 22 GeoTIFF crudos y se encontraron {len(archivos)}.")

    claves = {(ruta.parent.name, ruta.stem) for ruta in archivos}
    faltantes = sorted(set(METADATOS_ESCENAS) - claves)
    sobrantes = sorted(claves - set(METADATOS_ESCENAS))
    if faltantes or sobrantes:
        raise ValueError(f"Fechas/lagos no esperados. Faltantes={faltantes}; sobrantes={sobrantes}")
    return archivos


def normalizar_nombres_bandas(descripciones: tuple[str | None, ...]) -> tuple[str, ...]:
    """Normaliza descripciones GeoTIFF; solo usa el orden oficial si todas estan vacias."""
    if all(descripcion in (None, "") for descripcion in descripciones):
        return BANDAS_ESPERADAS

    nombres = []
    for descripcion in descripciones:
        texto = str(descripcion).lower().replace("_", "").replace("-", "")
        coincidencia = next((banda for banda in BANDAS_ESPERADAS if texto.startswith(banda)), None)
        nombres.append(coincidencia or "")
    if tuple(nombres) != BANDAS_ESPERADAS:
        raise ValueError(
            "Las bandas no estan en el orden esperado "
            f"{BANDAS_ESPERADAS}. Descripciones encontradas: {descripciones}"
        )
    return tuple(nombres)


def validar_raster(fuente: rasterio.io.DatasetReader, ruta: Path) -> None:
    """Valida conteo, tipos, CRS, resolucion, geotransformacion y bandas."""
    if fuente.count != len(BANDAS_ESPERADAS):
        raise ValueError(f"{ruta}: se esperaban 9 bandas y se encontraron {fuente.count}.")
    if fuente.crs is None or not fuente.crs.is_projected:
        raise ValueError(f"{ruta}: el CRS debe existir y ser proyectado; se obtuvo {fuente.crs}.")
    if fuente.width <= 0 or fuente.height <= 0:
        raise ValueError(f"{ruta}: dimensiones raster invalidas.")
    if any(not np.issubdtype(np.dtype(tipo), np.number) for tipo in fuente.dtypes):
        raise TypeError(f"{ruta}: todas las bandas deben ser numericas; tipos={fuente.dtypes}.")
    normalizar_nombres_bandas(fuente.descriptions)

    resolucion_x, resolucion_y = fuente.res
    if not (19.5 <= abs(resolucion_x) <= 20.5 and 19.5 <= abs(resolucion_y) <= 20.5):
        raise ValueError(f"{ruta}: se esperaba resolucion de 20 m y se obtuvo {fuente.res}.")


def estimar_factor_reflectancia(fuente: rasterio.io.DatasetReader) -> float:
    """Detecta si la reflectancia esta escalada a 0-10000 o ya se expresa en 0-1."""
    alto = min(128, fuente.height)
    ancho = min(128, fuente.width)
    muestra = fuente.read(out_shape=(fuente.count, alto, ancho), masked=True).astype(np.float32)
    valores = muestra.compressed()
    if valores.size == 0:
        raise ValueError(f"{fuente.name}: no contiene una muestra valida para estimar la escala.")
    percentil_99 = float(np.percentile(valores, 99))
    return 0.0001 if percentil_99 > 2.0 else 1.0


def calcular_mascara_agua(bandas: dict[str, np.ndarray], valida: np.ndarray) -> np.ndarray:
    """Reproduce la mascara multiespectral de agua usada en la Parte 1."""
    ndvi = diferencia_normalizada(bandas["b08"], bandas["b04"])
    ndwi = diferencia_normalizada(bandas["b03"], bandas["b08"])
    mndwi = diferencia_normalizada(bandas["b03"], bandas["b11"])
    ndwi_hojas = diferencia_normalizada(bandas["b08"], bandas["b11"])
    awei_sombra = (
        bandas["b02"]
        + 2.5 * bandas["b03"]
        - 1.5 * (bandas["b08"] + bandas["b11"])
        - 0.25 * bandas["b12"]
    )
    awei_sin_sombra = 4.0 * (bandas["b03"] - bandas["b11"]) - (
        0.25 * bandas["b08"] + 2.75 * bandas["b11"]
    )
    dbsi = diferencia_normalizada(bandas["b11"], bandas["b03"]) - ndvi

    agua = (
        (mndwi > 0.42)
        | (ndwi > 0.40)
        | (awei_sin_sombra > 0.1879)
        | (awei_sombra > 0.1112)
        | (ndvi < -0.20)
        | (ndwi_hojas > 1.0)
    )
    agua &= ~((awei_sin_sombra <= -0.03) | (dbsi > 0.0))
    return agua & valida


def calcular_mascara_nube_l1c(bandas: dict[str, np.ndarray], valida: np.ndarray) -> np.ndarray:
    """Aplica una mascara espectral conservadora para nubes brillantes sobre agua.

    Los GeoTIFF L1C disponibles no incluyen SCL ni QA60. Por ello se combinan
    brillo visible, blancura y reflectancia SWIR. Esta limitacion queda documentada
    y nunca se presenta la heuristica como equivalente a Sen2Cor.
    """
    visibles = np.stack([bandas["b02"], bandas["b03"], bandas["b04"]])
    brillo = np.mean(visibles, axis=0)
    blancura = np.sum(np.abs(visibles - brillo), axis=0) / (3.0 * np.maximum(brillo, 1e-6))
    nube_brillante = (brillo > 0.20) & (blancura < 0.70) & (bandas["b11"] > 0.10)
    nube_muy_brillante = (bandas["b02"] > 0.35) & (bandas["b11"] > 0.08)
    return valida & (nube_brillante | nube_muy_brillante)


def calcular_indices(bandas: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Calcula indices requeridos y el estimador cuantitativo de cianobacterias."""
    ndvi = diferencia_normalizada(bandas["b08"], bandas["b04"])
    ndwi = diferencia_normalizada(bandas["b03"], bandas["b08"])
    ndci = diferencia_normalizada(bandas["b05"], bandas["b04"])
    indice_cianobacterias = np.clip(
        826.57 * ndci**3 - 176.43 * ndci**2 + 19.0 * ndci + 4.071,
        0.0,
        500.0,
    )
    return {
        "ndvi": ndvi,
        "ndwi": ndwi,
        "ndci": ndci,
        "indice_cianobacterias_mg_m3": indice_cianobacterias,
    }


def coordenadas_centros(
    transformacion: rasterio.Affine,
    filas: np.ndarray,
    columnas: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Obtiene coordenadas proyectadas del centro de cada pixel."""
    columnas_centro = columnas.astype(np.float64) + 0.5
    filas_centro = filas.astype(np.float64) + 0.5
    coordenada_x = (
        transformacion.c + columnas_centro * transformacion.a + filas_centro * transformacion.b
    )
    coordenada_y = (
        transformacion.f + columnas_centro * transformacion.d + filas_centro * transformacion.e
    )
    return coordenada_x, coordenada_y


def procesar_raster(ruta: Path, escribir_encabezado: bool) -> tuple[dict[str, int], bool]:
    """Procesa un GeoTIFF por bloques, agrega sus filas al CSV y devuelve conteos."""
    lago_id = ruta.parent.name
    fecha = ruta.stem
    nombre_lago = NOMBRES_LAGOS[lago_id]
    satelite, nubosidad_escena_pct = METADATOS_ESCENAS[(lago_id, fecha)]
    conteos = {
        "pixeles_totales": 0,
        "nodata_o_no_finitos": 0,
        "reflectancia_invalida": 0,
        "nubes": 0,
        "fuera_del_lago": 0,
        "indices_no_finitos": 0,
        "observaciones_limpias": 0,
    }

    with rasterio.open(ruta) as fuente:
        validar_raster(fuente, ruta)
        factor_reflectancia = estimar_factor_reflectancia(fuente)
        nombres_bandas = normalizar_nombres_bandas(fuente.descriptions)

        for _, ventana in fuente.block_windows(1):
            bloque_mascarado = fuente.read(window=ventana, masked=True).astype(np.float32)
            datos = bloque_mascarado.filled(np.nan) * factor_reflectancia
            conteos["pixeles_totales"] += int(datos.shape[1] * datos.shape[2])

            valida = np.logical_and.reduce(np.isfinite(datos), axis=0)
            valida &= ~np.logical_or.reduce(np.ma.getmaskarray(bloque_mascarado), axis=0)
            valida &= np.any(datos != 0.0, axis=0)
            conteos["nodata_o_no_finitos"] += int((~valida).sum())

            reflectancia_valida = np.logical_and.reduce((datos >= -0.05) & (datos <= 1.50), axis=0)
            conteos["reflectancia_invalida"] += int((valida & ~reflectancia_valida).sum())
            valida &= reflectancia_valida

            bandas = {nombre: datos[indice] for indice, nombre in enumerate(nombres_bandas)}
            mascara_nube = calcular_mascara_nube_l1c(bandas, valida)
            conteos["nubes"] += int(mascara_nube.sum())
            valida &= ~mascara_nube

            mascara_agua = calcular_mascara_agua(bandas, valida)
            conteos["fuera_del_lago"] += int((valida & ~mascara_agua).sum())
            valida &= mascara_agua

            indices = calcular_indices(bandas)
            indices_finitos = np.logical_and.reduce(
                [np.isfinite(arreglo) for arreglo in indices.values()]
            )
            conteos["indices_no_finitos"] += int((valida & ~indices_finitos).sum())
            valida &= indices_finitos

            filas_locales, columnas_locales = np.nonzero(valida)
            if filas_locales.size == 0:
                continue
            filas = filas_locales + int(ventana.row_off)
            columnas = columnas_locales + int(ventana.col_off)
            coordenada_x, coordenada_y = coordenadas_centros(
                fuente.transform, filas, columnas
            )

            salida = {
                "lago": np.repeat(nombre_lago, filas.size),
                "lago_id": np.repeat(lago_id, filas.size),
                "fecha": np.repeat(fecha, filas.size),
                "satelite": np.repeat(satelite, filas.size),
                "nubosidad_escena_pct": np.repeat(nubosidad_escena_pct, filas.size),
                "crs": np.repeat(fuente.crs.to_string(), filas.size),
                "fila": filas.astype(np.int32),
                "columna": columnas.astype(np.int32),
                "coordenada_x": coordenada_x,
                "coordenada_y": coordenada_y,
            }
            salida.update({nombre: bandas[nombre][valida] for nombre in BANDAS_ESPERADAS})
            salida.update({nombre: arreglo[valida] for nombre, arreglo in indices.items()})
            datos_salida = pd.DataFrame(salida)
            datos_salida.to_csv(
                RUTA_SALIDA,
                mode="a",
                header=escribir_encabezado,
                index=False,
                encoding="utf-8",
                float_format="%.8g",
            )
            escribir_encabezado = False
            conteos["observaciones_limpias"] += len(datos_salida)

    return conteos, escribir_encabezado


def imprimir_reporte(conteos_escenas: pd.DataFrame) -> None:
    """Imprime el reporte estadistico solicitado sin releer todo el CSV en memoria."""
    print("\n=== REPORTE DE LIMPIEZA ===")
    print(f"Observaciones limpias: {conteos_escenas['observaciones_limpias'].sum():,}")
    print("\nDesglose por lago:")
    print(conteos_escenas.groupby("lago")["observaciones_limpias"].sum().to_string())
    print("\nDesglose por lago y fecha:")
    print(
        conteos_escenas[["lago", "fecha", "observaciones_limpias"]]
        .sort_values(["lago", "fecha"])
        .to_string(index=False)
    )
    print("\nPixeles removidos por criterio (criterios secuenciales, sin doble conteo):")
    columnas_conteo = [
        "nodata_o_no_finitos",
        "reflectancia_invalida",
        "nubes",
        "fuera_del_lago",
        "indices_no_finitos",
    ]
    print(conteos_escenas[columnas_conteo].sum().to_string())

    tipos = pd.read_csv(RUTA_SALIDA, nrows=1).dtypes
    print("\nTipos de variables:")
    print(tipos.to_string())
    print("\nPorcentaje de valores faltantes residuales:")
    print(pd.Series(0.0, index=tipos.index, name="porcentaje_faltante").to_string())


def ejecutar() -> None:
    """Ejecuta el pipeline de limpieza completo."""
    archivos = validar_estructura_entrada()
    DIRECTORIO_PROCESADO.mkdir(parents=True, exist_ok=True)
    if RUTA_SALIDA.exists():
        RUTA_SALIDA.unlink()

    escribir_encabezado = True
    reportes = []
    for numero, ruta in enumerate(archivos, start=1):
        print(f"[{numero:02d}/{len(archivos)}] Procesando {ruta.relative_to(RAIZ_LABORATORIO)}")
        conteos, escribir_encabezado = procesar_raster(ruta, escribir_encabezado)
        reportes.append({"lago": NOMBRES_LAGOS[ruta.parent.name], "fecha": ruta.stem, **conteos})

    if escribir_encabezado or not RUTA_SALIDA.exists():
        raise RuntimeError("La limpieza no produjo observaciones.")

    conteos_escenas = pd.DataFrame(reportes)
    conteos_escenas.to_csv(
        DIRECTORIO_PROCESADO / "01_reporte_limpieza.csv",
        index=False,
        encoding="utf-8",
    )
    imprimir_reporte(conteos_escenas)
    print(f"\nArchivo generado: {RUTA_SALIDA}")


if __name__ == "__main__":
    try:
        ejecutar()
    except Exception as error:
        print(f"ERROR EN PREPARACION DE DATOS: {error}", file=sys.stderr)
        raise

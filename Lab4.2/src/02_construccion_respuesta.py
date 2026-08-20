"""Ejercicio 2: construye la respuesta binaria y documenta la fuga de datos."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


RAIZ_LABORATORIO = Path(__file__).resolve().parents[1]
DIRECTORIO_PROCESADO = RAIZ_LABORATORIO / "data" / "processed"
RUTA_ENTRADA = DIRECTORIO_PROCESADO / "01_datos_limpios.csv"
RUTA_SALIDA = DIRECTORIO_PROCESADO / "02_datos_con_respuesta.csv"
RUTA_CONFIGURACION = DIRECTORIO_PROCESADO / "02_configuracion_respuesta.json"

UMBRAL_ALTA_PRESENCIA_MG_M3 = 20.0
TAMANO_BLOQUE = 200_000
COLUMNAS_REQUERIDAS = {
    "lago",
    "lago_id",
    "fecha",
    "b02",
    "b03",
    "b04",
    "b05",
    "b07",
    "b08",
    "b8a",
    "b11",
    "b12",
    "ndvi",
    "ndwi",
    "ndci",
    "indice_cianobacterias_mg_m3",
}

# Estas columnas se conservan en 02 para trazabilidad y EDA, pero quedan
# explicitamente prohibidas en X. El archivo 03 las elimina fisicamente.
COLUMNAS_EXCLUIDAS_POR_FUGA = {
    "indice_cianobacterias_mg_m3": "Es la magnitud continua umbralizada para crear y.",
    "ndci": "La respuesta es una funcion polinomica determinista de NDCI.",
    "b04": "Interviene directamente en NDCI=(B05-B04)/(B05+B04).",
    "b05": "Interviene directamente en NDCI=(B05-B04)/(B05+B04).",
    "ndvi": "Reutiliza B04; por ello incorpora indirectamente una entrada de la etiqueta.",
}


def validar_entrada() -> list[str]:
    """Valida existencia, esquema y tipos antes de escribir cualquier salida."""
    if not RUTA_ENTRADA.is_file():
        raise FileNotFoundError(
            f"No existe {RUTA_ENTRADA}. Ejecute primero src/01_preparacion_datos.py."
        )
    encabezado = pd.read_csv(RUTA_ENTRADA, nrows=10)
    faltantes = sorted(COLUMNAS_REQUERIDAS - set(encabezado.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en 01_datos_limpios.csv: {faltantes}")

    columnas_numericas = COLUMNAS_REQUERIDAS - {"lago", "lago_id", "fecha"}
    no_numericas = [
        columna
        for columna in columnas_numericas
        if not pd.api.types.is_numeric_dtype(encabezado[columna])
    ]
    if no_numericas:
        raise TypeError(f"Las siguientes columnas deben ser numericas: {no_numericas}")
    return encabezado.columns.tolist()


def validar_bloque(datos: pd.DataFrame, numero_bloque: int) -> None:
    """Aplica invariantes de dominio a cada bloque de entrada."""
    if datos.empty:
        raise ValueError(f"El bloque {numero_bloque} esta vacio.")
    if datos[list(COLUMNAS_REQUERIDAS)].isna().any().any():
        columnas = datos.columns[datos.isna().any()].tolist()
        raise ValueError(f"Bloque {numero_bloque}: valores faltantes en {columnas}.")
    if not datos["lago_id"].isin(["amatitlan", "atitlan"]).all():
        raise ValueError(f"Bloque {numero_bloque}: lago_id fuera del dominio permitido.")
    if not datos["indice_cianobacterias_mg_m3"].between(0.0, 500.0).all():
        raise ValueError(f"Bloque {numero_bloque}: indice de cianobacterias fuera de [0, 500].")
    fechas = pd.to_datetime(datos["fecha"], format="%Y-%m-%d", errors="coerce")
    if fechas.isna().any():
        raise ValueError(f"Bloque {numero_bloque}: existen fechas invalidas.")


def ejecutar() -> None:
    """Crea la etiqueta binaria por bloques y reporta su distribucion."""
    columnas_entrada = validar_entrada()
    if RUTA_SALIDA.exists():
        RUTA_SALIDA.unlink()

    conteos_globales = {0: 0, 1: 0}
    conteos_agrupados: list[pd.DataFrame] = []
    escribir_encabezado = True

    lector = pd.read_csv(RUTA_ENTRADA, chunksize=TAMANO_BLOQUE)
    for numero_bloque, datos in enumerate(lector, start=1):
        if datos.columns.tolist() != columnas_entrada:
            raise ValueError(f"Bloque {numero_bloque}: el esquema cambio durante la lectura.")
        validar_bloque(datos, numero_bloque)

        datos["presencia_alta_cianobacterias"] = (
            datos["indice_cianobacterias_mg_m3"] >= UMBRAL_ALTA_PRESENCIA_MG_M3
        ).astype(np.int8)
        datos.to_csv(
            RUTA_SALIDA,
            mode="a",
            header=escribir_encabezado,
            index=False,
            encoding="utf-8",
            float_format="%.8g",
        )
        escribir_encabezado = False

        conteo_bloque = datos["presencia_alta_cianobacterias"].value_counts()
        for clase in (0, 1):
            conteos_globales[clase] += int(conteo_bloque.get(clase, 0))
        conteos_agrupados.append(
            datos.groupby(["lago", "fecha", "presencia_alta_cianobacterias"], observed=True)
            .size()
            .rename("observaciones")
            .reset_index()
        )
        print(f"Bloque {numero_bloque}: {len(datos):,} observaciones procesadas.")

    if escribir_encabezado:
        raise RuntimeError("El archivo de entrada no contiene observaciones.")

    distribucion = (
        pd.concat(conteos_agrupados, ignore_index=True)
        .groupby(["lago", "fecha", "presencia_alta_cianobacterias"], as_index=False)[
            "observaciones"
        ]
        .sum()
    )
    distribucion.to_csv(
        DIRECTORIO_PROCESADO / "02_distribucion_clases.csv",
        index=False,
        encoding="utf-8",
    )

    total = sum(conteos_globales.values())
    if total == 0:
        raise RuntimeError("No fue posible construir la variable respuesta.")
    configuracion = {
        "variable_respuesta": "presencia_alta_cianobacterias",
        "definicion": {
            "0": "ausencia o baja presencia",
            "1": "alta presencia operativa",
        },
        "umbral_inclusivo_mg_m3": UMBRAL_ALTA_PRESENCIA_MG_M3,
        "columnas_excluidas_del_conjunto_predictor_por_fuga": COLUMNAS_EXCLUIDAS_POR_FUGA,
        "nota": (
            "Las columnas excluidas se retienen en el archivo 02 solo para auditoria y EDA; "
            "el script 03 las remueve del archivo final de modelado."
        ),
    }
    RUTA_CONFIGURACION.write_text(
        json.dumps(configuracion, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n=== DISTRIBUCION GLOBAL DE LA RESPUESTA ===")
    for clase in (0, 1):
        porcentaje = 100.0 * conteos_globales[clase] / total
        print(f"Clase {clase}: {conteos_globales[clase]:,} ({porcentaje:.4f}%)")
    print("\nVariables excluidas del conjunto predictor por fuga:")
    for variable, razon in COLUMNAS_EXCLUIDAS_POR_FUGA.items():
        print(f"- {variable}: {razon}")
    print(f"\nArchivo generado: {RUTA_SALIDA}")


if __name__ == "__main__":
    try:
        ejecutar()
    except Exception as error:
        print(f"ERROR EN CONSTRUCCION DE LA RESPUESTA: {error}", file=sys.stderr)
        raise

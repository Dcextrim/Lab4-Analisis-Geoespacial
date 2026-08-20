"""Ejercicio 3: construye el conjunto final de modelado sin fuga de datos."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


RAIZ_LABORATORIO = Path(__file__).resolve().parents[1]
DIRECTORIO_PROCESADO = RAIZ_LABORATORIO / "data" / "processed"
RUTA_ENTRADA = DIRECTORIO_PROCESADO / "02_datos_con_respuesta.csv"
RUTA_SALIDA = DIRECTORIO_PROCESADO / "03_datos_listos_modelado.csv"
RUTA_CONFIGURACION = DIRECTORIO_PROCESADO / "03_variables_modelado.json"
TAMANO_BLOQUE = 200_000

COLUMNAS_IDENTIFICADORAS = [
    "lago",
    "lago_id",
    "fecha",
    "satelite",
    "nubosidad_escena_pct",
    "crs",
    "fila",
    "columna",
    "coordenada_x",
    "coordenada_y",
]
PREDICTORAS_BASE_SIN_FUGA = ["b02", "b03", "b07", "b08", "b8a", "b11", "b12", "ndwi"]
PREDICTORAS_ADICIONALES = ["indice_turbidez_azul_verde", "razon_borde_rojo_verde"]
VARIABLE_RESPUESTA = "presencia_alta_cianobacterias"
COLUMNAS_PROHIBIDAS_POR_FUGA = ["indice_cianobacterias_mg_m3", "ndci", "b04", "b05", "ndvi"]


def diferencia_normalizada(arreglo_a: pd.Series, arreglo_b: pd.Series) -> np.ndarray:
    """Calcula una diferencia normalizada con resultado NaN si el denominador es cero."""
    denominador = arreglo_a.to_numpy(np.float64) + arreglo_b.to_numpy(np.float64)
    numerador = arreglo_a.to_numpy(np.float64) - arreglo_b.to_numpy(np.float64)
    resultado = np.full(len(arreglo_a), np.nan, dtype=np.float32)
    return np.divide(numerador, denominador, out=resultado, where=np.abs(denominador) > 1e-8)


def validar_entrada() -> list[str]:
    """Valida de forma fail-fast el esquema producido por el Ejercicio 2."""
    if not RUTA_ENTRADA.is_file():
        raise FileNotFoundError(
            f"No existe {RUTA_ENTRADA}. Ejecute primero src/02_construccion_respuesta.py."
        )
    encabezado = pd.read_csv(RUTA_ENTRADA, nrows=10)
    requeridas = set(COLUMNAS_IDENTIFICADORAS + PREDICTORAS_BASE_SIN_FUGA)
    requeridas.update(COLUMNAS_PROHIBIDAS_POR_FUGA)
    requeridas.add(VARIABLE_RESPUESTA)
    faltantes = sorted(requeridas - set(encabezado.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en la entrada: {faltantes}")
    return encabezado.columns.tolist()


def crear_variables_adicionales(datos: pd.DataFrame) -> pd.DataFrame:
    """Agrega dos proxies espectrales que no reutilizan B04 ni B05.

    - indice_turbidez_azul_verde: contraste normalizado B03-B02. Cambios en
      dispersion por particulas alteran la pendiente visible azul-verde.
    - razon_borde_rojo_verde: B07/B03. Resume el realce del borde rojo respecto
      al verde y es sensible a biomasa/pigmentos, pero requiere calibracion local.
    """
    datos = datos.copy()
    datos["indice_turbidez_azul_verde"] = diferencia_normalizada(datos["b03"], datos["b02"])
    datos["razon_borde_rojo_verde"] = np.divide(
        datos["b07"].to_numpy(np.float64),
        datos["b03"].to_numpy(np.float64),
        out=np.full(len(datos), np.nan, dtype=np.float64),
        where=np.abs(datos["b03"].to_numpy(np.float64)) > 1e-8,
    ).astype(np.float32)
    return datos


def validar_bloque_final(datos: pd.DataFrame, numero_bloque: int) -> None:
    """Comprueba dominios y ausencia de columnas/valores peligrosos."""
    columnas_modelado = PREDICTORAS_BASE_SIN_FUGA + PREDICTORAS_ADICIONALES
    if datos[columnas_modelado + [VARIABLE_RESPUESTA]].isna().any().any():
        columnas = datos.columns[datos.isna().any()].tolist()
        raise ValueError(f"Bloque {numero_bloque}: valores faltantes en {columnas}.")
    if not datos[VARIABLE_RESPUESTA].isin([0, 1]).all():
        raise ValueError(f"Bloque {numero_bloque}: respuesta fuera del dominio binario.")
    if not datos["ndwi"].between(-1.0, 1.0).all():
        raise ValueError(f"Bloque {numero_bloque}: NDWI fuera de [-1, 1].")
    if set(COLUMNAS_PROHIBIDAS_POR_FUGA) & set(datos.columns):
        raise AssertionError("El conjunto final todavia contiene variables con fuga.")


def ejecutar() -> None:
    """Genera el CSV final por bloques y un manifiesto de variables."""
    columnas_entrada = validar_entrada()
    if RUTA_SALIDA.exists():
        RUTA_SALIDA.unlink()

    columnas_salida = (
        COLUMNAS_IDENTIFICADORAS
        + PREDICTORAS_BASE_SIN_FUGA
        + PREDICTORAS_ADICIONALES
        + [VARIABLE_RESPUESTA]
    )
    escribir_encabezado = True
    total_observaciones = 0

    for numero_bloque, datos in enumerate(
        pd.read_csv(RUTA_ENTRADA, chunksize=TAMANO_BLOQUE), start=1
    ):
        if datos.columns.tolist() != columnas_entrada:
            raise ValueError(f"Bloque {numero_bloque}: el esquema cambio durante la lectura.")
        datos = crear_variables_adicionales(datos)
        datos_finales = datos[columnas_salida].copy()
        validar_bloque_final(datos_finales, numero_bloque)
        datos_finales.to_csv(
            RUTA_SALIDA,
            mode="a",
            header=escribir_encabezado,
            index=False,
            encoding="utf-8",
            float_format="%.8g",
        )
        escribir_encabezado = False
        total_observaciones += len(datos_finales)
        print(f"Bloque {numero_bloque}: {len(datos_finales):,} observaciones listas.")

    if escribir_encabezado or total_observaciones == 0:
        raise RuntimeError("No se generaron observaciones de modelado.")

    configuracion = {
        "unidad_analisis": "pixel de 20 m por lago y fecha",
        "columnas_identificadoras_no_predictoras": COLUMNAS_IDENTIFICADORAS,
        "variables_predictoras": PREDICTORAS_BASE_SIN_FUGA + PREDICTORAS_ADICIONALES,
        "variable_respuesta": VARIABLE_RESPUESTA,
        "variables_removidas_por_fuga": COLUMNAS_PROHIBIDAS_POR_FUGA,
        "nota_ndvi": (
            "NDVI se conserva en 02 para el EDA solicitado, pero no es predictor final porque "
            "reutiliza B04, banda que participa en la etiqueta determinista."
        ),
        "particion_recomendada": (
            "Separar por fecha o por bloques espaciales; nunca dividir pixeles vecinos al azar."
        ),
    }
    RUTA_CONFIGURACION.write_text(
        json.dumps(configuracion, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\n=== VARIABLES PREDICTORAS FINALES SIN FUGA ===")
    for variable in PREDICTORAS_BASE_SIN_FUGA + PREDICTORAS_ADICIONALES:
        print(f"- {variable}")
    print(f"Observaciones finales: {total_observaciones:,}")
    print(f"Archivo generado: {RUTA_SALIDA}")


if __name__ == "__main__":
    try:
        ejecutar()
    except Exception as error:
        print(f"ERROR EN VARIABLES PREDICTORAS: {error}", file=sys.stderr)
        raise

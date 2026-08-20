# Informe de avance - Laboratorio 4, Parte 2

**Curso:** CC3084 Ciencia de Datos, Universidad del Valle de Guatemala  

## 1. Justificación técnica de la limpieza

La observación elemental del análisis es un píxel multiespectral de Sentinel-2 de 20 m. Antes de convertir el ráster a una tabla de modelado se descartaron los píxeles NoData, no finitos, saturados o fuera del rango operativo de reflectancia. Los valores NoData no representan una medición de radiancia o reflectancia; tratarlos como ceros introduciría una concentración artificial en el origen de la distribución, alteraría los cocientes espectrales y permitiría que un algoritmo aprendiera la geometría del mosaico en lugar del fenómeno ambiental. Los infinitos y los denominadores cercanos a cero son igualmente incompatibles con los supuestos numéricos de la mayoría de estimadores y pueden desestabilizar la optimización.

Las nubes modifican la señal recibida por el sensor por dispersión y absorción atmosférica. Una nube brillante incrementa simultáneamente la reflectancia visible y SWIR y oculta la columna de agua; su espectro corresponde a la atmósfera/nube, no al fitoplancton. Si esos píxeles permanecieran, podrían desplazar las distribuciones, generar valores extremos en índices y originar asociaciones espurias con la fecha o el lago. Los GeoTIFF L1C disponibles no contienen una banda SCL ni QA60. Por eso se aplicó y documentó una máscara conservadora de brillo visible, blancura y SWIR. Esta heurística reduce contaminación evidente, pero no sustituye la clasificación Sen2Cor y puede dejar nubes delgadas o sombra residual; dicha incertidumbre debe considerarse al interpretar el modelo.

También se eliminaron píxeles terrestres y de orilla mediante una máscara multiespectral de agua. Un píxel mixto puede combinar agua, suelo, infraestructura y vegetación ribereña. La respuesta espectral de vegetación terrestre -absorción en rojo y alta reflectancia NIR- es mucho más intensa que la señal acuática y podría dominar NDVI, NDWI y los bordes rojos. Dejar observaciones fuera de los lagos permitiría que el clasificador distinguiera tierra de agua, una tarea trivial pero distinta a identificar cianobacterias. La limpieza, por tanto, reduce sesgo de selección, varianza espuria y errores de dominio; a la vez mejora la validez de las métricas de generalización.

Las exclusiones se aplicaron de manera secuencial y se registraron por lago y fecha en `01_reporte_limpieza.csv`. Esta trazabilidad permite detectar escenas con cobertura anormal sin editar `data/raw/` y garantiza que el resultado pueda regenerarse desde los 22 GeoTIFF originales.

## 2. Construcción y justificación científica de la variable respuesta

El índice cuantitativo utilizado en la Parte 1 estima clorofila-a asociada con cianobacterias a partir de `NDCI=(B05-B04)/(B05+B04)` y del polinomio `826.57*NDCI³ - 176.43*NDCI² + 19*NDCI + 4.071`, truncado a 0-500 mg/m³. La implementación corresponde al algoritmo para Sentinel-2 L1C publicado por Sentinel Hub. NDCI fue propuesto para estimar clorofila-a en aguas productivas y ópticamente complejas porque contrasta la absorción alrededor del rojo con el incremento de reflectancia en el borde rojo (Mishra y Mishra, 2012).

Se definió `presencia_alta_cianobacterias = 1` cuando el estimador es mayor o igual que **20 mg/m³**, y 0 en caso contrario. Para agua, `1 mg/m³ = 1 µg/L`, por lo que el umbral equivale numéricamente a 20 µg/L de clorofila-a estimada. La elección conserva el criterio principal establecido en la Parte 1 y se ubica entre dos referencias históricas de la OMS para aguas recreacionales con predominio de cianobacterias: 10 µg/L se asoció con una probabilidad relativamente baja de efectos adversos y 50 µg/L con una probabilidad moderada. Así, 20 µg/L funciona como un nivel conservador de **tamizaje operativo** por encima de la señal de vigilancia inferior, sin esperar hasta el nivel de 50 µg/L.

La guía vigente de la OMS (2021), que sustituyó la edición de 2003, enfatiza el biovolumen y recomienda adaptar los niveles de actuación a las condiciones locales. También acepta indicadores como fluorescencia, turbidez o datos satelitales cuando se calibran localmente y señala que clorofila-a debe acompañarse de verificación de dominancia de cianobacterias. En consecuencia, la clase 1 no se interpreta como diagnóstico toxicológico, concentración de microcistina ni prohibición de uso recreacional. Es una etiqueta de teledetección para priorizar áreas y fechas que requieren muestreo in situ. Antes de una decisión de salud pública se necesitarían conteo/biovolumen, composición taxonómica, clorofila-a de laboratorio y cianotoxinas.

El umbral inclusivo evita ambigüedad en el punto de corte y su valor está centralizado como constante en el script 02. Como análisis de sensibilidad posterior se recomienda repetir el modelado con 10 y 50 mg/m³. El primer valor aproxima la vigilancia histórica de la OMS; el segundo aproxima su referencia histórica de probabilidad moderada. La estabilidad de las conclusiones frente a esos cortes sería evidencia más sólida que el desempeño con un solo umbral.

## 3. Análisis del desbalance de clases

El notebook calcula la distribución global, por lago y por fecha usando todas las observaciones. Esta desagregación es indispensable: un balance global aparente puede ocultar fechas sin positivos o un lago que concentre casi toda la clase 1. Además, los píxeles no son muestras independientes; la autocorrelación espacial reduce el tamaño efectivo de muestra y hace que millones de filas no equivalgan a millones de réplicas ambientales.

Con una clase 1 minoritaria, un clasificador que siempre prediga 0 puede alcanzar un Accuracy elevado sin detectar un solo episodio de interés. Accuracy tampoco diferencia el costo ambiental de un falso negativo del de un falso positivo. Por ello, la evaluación debe incluir matriz de confusión, **recall o sensibilidad** de la clase 1, **precision**, **F1-score** y **área bajo la curva Precision-Recall (PR-AUC)**. PR-AUC es especialmente informativa cuando la prevalencia positiva es baja, porque su línea base depende de dicha prevalencia. ROC-AUC puede reportarse como complemento, pero puede parecer optimista ante una gran cantidad de negativos.

Se debe comparar contra un baseline de clase mayoritaria y reportar intervalos de variación entre particiones temporales o espaciales. Si se emplean `class_weight`, sobremuestreo o submuestreo, el ajuste se realiza exclusivamente dentro del conjunto de entrenamiento de cada pliegue. Balancear antes de separar datos filtraría información de prueba. La partición recomendada es por fecha completa o por bloques espaciales; una división aleatoria de píxeles colocaría vecinos altamente correlacionados en entrenamiento y prueba y sobrestimaría la generalización.

## 4. Identificación exacta de fuga de datos

La variable respuesta no proviene de una medición de campo independiente. Es una transformación determinista de las mismas bandas espectrales. Esta circunstancia exige una política de exclusión más estricta que la de un problema supervisado convencional:

| Variable excluida | Relación con la etiqueta | Consecuencia de incluirla |
|---|---|---|
| `indice_cianobacterias_mg_m3` | Es la variable continua a la que se aplica el umbral de 20 mg/m³ | El modelo recibiría directamente la respuesta antes de binarizarla |
| `ndci` | El índice cuantitativo es un polinomio determinista de NDCI | Bastaría aprender un umbral monótono o casi monótono |
| `b04` | Participa en el numerador y denominador de NDCI | El modelo reconstruiría parcialmente la fórmula objetivo |
| `b05` | Participa en el numerador y denominador de NDCI | El modelo reconstruiría parcialmente la fórmula objetivo |
| `ndvi` | Utiliza `B04` en `(B08-B04)/(B08+B04)` | Introduce indirectamente una entrada de la etiqueta |

Estas columnas se conservan en `02_datos_con_respuesta.csv` para auditar la construcción y satisfacer el EDA solicitado, pero no forman parte de `X`. El script 03 las elimina físicamente de `03_datos_listos_modelado.csv`. Esta decisión explica una aparente desviación del listado inicial del ejercicio: NDVI sí se calcula, describe y visualiza, pero no puede considerarse predictor válido de una etiqueta que comparte B04. Presentar métricas con esas variables mediría la capacidad de reconstruir una ecuación conocida, no de generalizar a una observación ambiental independiente.

También se excluyen como predictores por defecto el lago, la fecha, el satélite, la nubosidad de escena, las coordenadas, la fila y la columna. Se conservan para agrupar y diseñar validación. Incluirlos sin un objetivo explícito puede hacer que el modelo memorice campañas, geometrías o diferencias sistemáticas entre lagos.

## 5. Justificación física de las variables espectrales

El MSI de Sentinel-2 observa 13 bandas entre el visible, NIR y SWIR. Los productos utilizados fueron remuestreados a una grilla común de 20 m. La interpretación de agua es más delicada que la terrestre: la reflectancia acuática es baja, la atmósfera contribuye una fracción grande de la señal y sedimentos, materia orgánica disuelta, profundidad y brillo solar pueden confundirse con pigmentos.

### Bandas conservadas como predictores

- **B02, azul (~490 nm).** La luz azul penetra agua relativamente clara, pero es sensible a dispersión atmosférica, materia orgánica disuelta coloreada y partículas finas. En combinación con verde aporta información sobre color y pendiente visible; por sí sola no identifica cianobacterias.
- **B03, verde (~560 nm).** Coincide con una región de reflectancia relativamente alta para muchos tipos de agua con fitoplancton y contrasta con la absorción en rojo. Puede responder a pigmentos y partículas suspendidas, por lo que es útil para color, turbidez y NDWI.
- **B07, borde rojo 3 (~783 nm).** En aguas con biomasa superficial elevada puede aumentar la retrodispersión cerca del borde rojo/NIR. Ayuda a detectar cambios de pendiente relacionados con floraciones, aunque también responde a vegetación flotante y píxeles mixtos.
- **B08, NIR ancho (~842 nm).** El agua pura absorbe fuertemente en NIR, de modo que su reflectancia suele ser baja. Una señal elevada puede indicar partículas, espuma, biomasa superficial, vegetación flotante o contaminación de orilla. Es fundamental para separar agua mediante NDWI.
- **B8A, NIR estrecho (~865 nm).** Proporciona una medida NIR menos ancha y a 20 m, útil para caracterizar la forma de la respuesta cerca del borde rojo y controlar anomalías superficiales.
- **B11 y B12, SWIR (~1610 y ~2190 nm).** El agua absorbe intensamente en SWIR. Por ello son eficaces para distinguir agua de tierra, nubes, suelo y vegetación, y para detectar píxeles mixtos. Su utilidad principal en este problema es controlar el dominio y la turbidez/superficie, no medir clorofila directamente.
- **NDWI.** Se calcula como `(B03-B08)/(B03+B08)`. Valores altos son consistentes con agua abierta porque el agua refleja más en verde que en NIR; valores menores pueden señalar turbidez intensa, biomasa superficial o mezcla con tierra. Aunque la muestra ya está enmascarada como agua, NDWI preserva variación óptica interna útil.
- **Índice de turbidez azul-verde.** El contraste `(B03-B02)/(B03+B02)` resume la pendiente visible sin usar B04 o B05. Partículas y pigmentos alteran de forma distinta las bandas azul y verde. Se considera una característica experimental, no una concentración calibrada.
- **Razón borde rojo-verde.** `B07/B03` compara el realce cercano al borde rojo con el verde. Puede responder a biomasa y pigmentos en floraciones densas, pero también a partículas y efectos atmosféricos; necesita validación in situ.

### Variables calculadas solo para EDA

**B04** (~665 nm) coincide con una región de absorción fuerte de clorofila-a; **B05** (~705 nm) captura el incremento de reflectancia del borde rojo que se intensifica en aguas productivas. Su contraste forma NDCI, razón por la cual son físicamente informativas pero estadísticamente inadmisibles como predictores de esta etiqueta. **NDVI**, `(B08-B04)/(B08+B04)`, fue diseñado para vegetación verde: la clorofila absorbe rojo y la estructura foliar refleja NIR. Sobre agua, valores elevados pueden indicar vegetación flotante, biomasa superficial o mezcla costera. Se visualiza como control de calidad, pero se excluye por compartir B04 con la etiqueta.

## 6. Limitaciones

El conjunto usa reflectancia de nivel L1C y una máscara de nubes heurística. La corrección atmosférica específica para aguas interiores, la detección de brillo solar y una máscara de litoral vectorial mejorarían la calidad. Además, el índice de clorofila proviene de datos simulados y no fue calibrado con muestras simultáneas de Atitlán y Amatitlán.

## Referencias

- European Space Agency / Copernicus. (2026). *Sentinel-2 MSI Processor: Context and Terminology*. https://s2.pages.eopf.copernicus.eu/msi/s2msi/main/context.html
- McFeeters, S. K. (1996). The use of the Normalized Difference Water Index (NDWI) in the delineation of open water features. *International Journal of Remote Sensing, 17*(7), 1425-1432. https://doi.org/10.1080/01431169608948714
- Mishra, S., & Mishra, D. R. (2012). Normalized difference chlorophyll index: A novel model for remote estimation of chlorophyll-a concentration in turbid productive waters. *Remote Sensing of Environment, 117*, 394-406. https://doi.org/10.1016/j.rse.2011.10.016
- Sentinel Hub. (s. f.). *Cyanobacteria Chlorophyll-a NDCI L1C*. https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/cyanobacteria_chla_ndci_l1c/
- World Health Organization. (2003). *Guidelines for safe recreational water environments. Volume 1: Coastal and fresh waters*. https://iris.who.int/bitstream/handle/10665/42591/9241545801.pdf
- World Health Organization. (2021). *Guidelines on recreational water quality. Volume 1: Coastal and fresh waters*. https://www.who.int/publications/i/item/9789240031302

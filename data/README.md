# Datos

## Datos de entrada, en `raw/`

| Archivo | Contenido | Frecuencia | Fuente |
|---|---|---|---|
| `bccr_tasa_medi_diaria.xlsx` | Tasa de interés promedio del Mercado Integrado de Liquidez (MEDI) | Diaria | Banco Central de Costa Rica |
| `bccr_tipo_cambio_diario.xlsx` | Tipo de cambio de referencia de compra y de venta, colones por dólar | Diaria | Banco Central de Costa Rica |
| `bccr_balanza_pagos_trimestral.xlsx` | Inversión directa, de cartera y otra inversión, activos y pasivos (MBP6), en millones de dólares | Trimestral | Banco Central de Costa Rica |
| `bccr_pib_dolares_trimestral.xlsx` | Producto interno bruto nominal, en millones de dólares | Trimestral | Banco Central de Costa Rica |
| `fred_treasury_bills_3m_semanal.csv` | Rendimiento de las Treasury Bills a 3 meses (serie `WTB3MS`) | Semanal | [FRED](https://fred.stlouisfed.org/series/WTB3MS) |
| `variables_macro_trimestrales.csv` | Variables macroeconómicas de control y reservas internacionales, ya llevadas a frecuencia trimestral | Trimestral | Banco Central de Costa Rica, FRED y FMI |
| `banco_mundial_reservas_pib_anual.csv` | Reservas totales menos oro (`FI.RES.XGLD.CD`) y PIB (`NY.GDP.MKTP.CD`), en dólares corrientes, 1960-2024 | Anual | [Banco Mundial](https://datos.bancomundial.org/pais/costa-rica) |

Los archivos del Banco Central y de FRED son las descargas originales. Con ellos el código calcula los índices de independencia monetaria, estabilidad cambiaria y apertura financiera.

`variables_macro_trimestrales.csv` reúne las series que el artículo usa como controles y las reservas, ya agregadas a trimestres. Cada columna es una variable.

| Variable | Descripción | Unidad |
|---|---|---|
| `trimestre` | Trimestre, de 1999Q1 a 2025Q4 | |
| `inflacion` | Inflación interanual, promedio del trimestre | % |
| `crecimiento_pib` | Crecimiento del PIB | % |
| `apertura_comercial` | Apertura comercial | Razón respecto al PIB |
| `terminos_intercambio` | Términos de intercambio | Índice |
| `vix` | Índice de volatilidad VIX | Puntos |
| `tasa_efr` | Tasa efectiva de los fondos federales de EE. UU. | % |
| `ri_pib` | Reservas internacionales netas | Razón respecto al PIB trimestral |

## Base construida, en `processed/`

`base_trimestral.csv` se genera con `python -m trilema` y tiene 108 trimestres, de 1999Q1 a 2025Q4. Contiene los tres índices, las variables de `variables_macro_trimestrales.csv` y `ri_pib_norm`, que es `ri_pib` normalizada entre 0 y 1 en la muestra para la restricción del cuadrilema.

| Variable | Descripción | Unidad |
|---|---|---|
| `IM` | Independencia monetaria | Índice de 0 a 1 |
| `EC` | Estabilidad cambiaria | Índice de 0 a 1 |
| `AF` | Apertura financiera de facto | Índice de 0 a 1 |
| `ri_pib_norm` | Reservas sobre el PIB, normalizadas | De 0 a 1 |

Los regímenes cambiarios son las minidevaluaciones (1999Q1 a 2006Q3), las bandas cambiarias (2006Q4 a 2014Q4) y la flotación administrada (2015Q1 a 2025Q4).

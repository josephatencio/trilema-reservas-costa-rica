"""Une los índices con las variables macroeconómicas en una base trimestral."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .indices import apertura_financiera, estabilidad_cambiaria, independencia_monetaria

RAIZ = Path(__file__).resolve().parents[2]
CRUDOS = RAIZ / "data" / "raw"
PROCESADOS = RAIZ / "data" / "processed"


def construir_base(crudos: Path = CRUDOS) -> pd.DataFrame:
    """Devuelve la base de 108 trimestres (1999Q1 a 2025Q4), indexada por trimestre."""
    indices = pd.concat([independencia_monetaria(crudos), estabilidad_cambiaria(crudos),
                         apertura_financiera(crudos)], axis=1)
    macro = pd.read_csv(crudos / "variables_macro_trimestrales.csv", index_col="trimestre")
    macro.index = pd.PeriodIndex(macro.index, freq="Q")
    base = indices.join(macro, how="inner").sort_index().astype(float)
    base.index.name = "trimestre"
    # Reservas normalizadas entre 0 y 1 en la muestra, para la restricción del cuadrilema
    ri = base["ri_pib"]
    base["ri_pib_norm"] = (ri - ri.min()) / (ri.max() - ri.min())
    return base


def reservas_largo_plazo(crudos: Path = CRUDOS) -> pd.DataFrame:
    """Reservas internacionales sin oro y PIB en dólares corrientes del Banco Mundial, 1960-2024,
    y la razón entre ambos en porcentaje."""
    tabla = pd.read_csv(crudos / "banco_mundial_reservas_pib_anual.csv", index_col="anio")
    tabla["ri_pib"] = 100 * tabla["reservas_sin_oro_usd"] / tabla["pib_usd"]
    return tabla


def regimen(q: pd.Period) -> str:
    if q <= pd.Period("2006Q3", "Q"):
        return "Minidevaluaciones"
    if q <= pd.Period("2014Q4", "Q"):
        return "Bandas"
    return "Flotación administrada"

"""Construcción de los índices trimestrales del trilema a partir de los datos crudos.

* IM: independencia monetaria, falta de comovilidad entre la tasa MEDI y la de los Treasury Bills.
* EC: estabilidad cambiaria, inversa de la volatilidad del tipo de cambio CRC/USD.
* AF: apertura financiera de facto, flujos de la balanza de pagos sobre el PIB, normalizados.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

INICIO = pd.Period("1999Q1", "Q")
FIN = pd.Period("2025Q4", "Q")
MIN_SEMANAS_IM = 8  # observaciones semanales mínimas por trimestre para la correlación
MIN_SEMANAS_EC = 5


def _ventana(serie: pd.Series) -> pd.Series:
    return serie[(serie.index >= INICIO) & (serie.index <= FIN)]


def independencia_monetaria(raw: Path) -> pd.Series:
    """IM_t = (1 - corr(i_CR, i_US)_t) / 2, con datos semanales dentro de cada trimestre."""
    usa = pd.read_csv(raw / "fred_treasury_bills_3m_semanal.csv")
    usa = usa.rename(columns={"observation_date": "fecha", "WTB3MS": "i_us"})
    usa["fecha"] = pd.to_datetime(usa["fecha"])
    usa = usa.set_index("fecha")[["i_us"]].resample("W-FRI").mean()

    cri = pd.read_excel(raw / "bccr_tasa_medi_diaria.xlsx", sheet_name="Series", skiprows=4)
    cri = cri.rename(columns={cri.columns[1]: "i_cr", "Fecha": "fecha"})
    cri["fecha"] = pd.to_datetime(cri["fecha"])
    cri = cri.set_index("fecha")[["i_cr"]].resample("W-FRI").mean()

    semanal = cri.join(usa, how="inner")
    trimestre = semanal.index.to_period("Q")

    def _im(g: pd.DataFrame) -> float:
        d = g.dropna()
        if len(d) < MIN_SEMANAS_IM:
            return np.nan
        return (1 - float(np.clip(d["i_cr"].corr(d["i_us"]), -1, 1))) / 2

    im = pd.Series({q: _im(g) for q, g in semanal.groupby(trimestre)}, name="IM")
    return _ventana(im)


def estabilidad_cambiaria(raw: Path) -> pd.Series:
    """EC_t = 0.01 / (0.01 + sd_t(variación logarítmica semanal del tipo de cambio promedio))."""
    tc = pd.read_excel(raw / "bccr_tipo_cambio_diario.xlsx", sheet_name="Series", skiprows=4)
    tc["Fecha"] = pd.to_datetime(tc["Fecha"])
    tc = tc.set_index("Fecha")
    promedio = ((tc["Tipo cambio compra"] + tc["Tipo cambio venta"]) / 2).resample("W-FRI").mean()
    dlog = np.log(promedio).diff()

    def _ec(g: pd.Series) -> float:
        d = g.dropna()
        return 0.01 / (0.01 + d.std()) if len(d) >= MIN_SEMANAS_EC else np.nan

    ec = pd.Series({q: _ec(g) for q, g in dlog.groupby(dlog.index.to_period("Q"))}, name="EC")
    return _ventana(ec)


def apertura_financiera(raw: Path) -> pd.Series:
    """AF_t: suma de flujos absolutos de la balanza de pagos sobre el PIB, normalizada min-max."""
    bop = pd.read_excel(raw / "bccr_balanza_pagos_trimestral.xlsx", sheet_name="Series",
                        skiprows=4)
    bop = bop.rename(columns={bop.columns[0]: "fecha"})
    bop["fecha"] = pd.to_datetime(bop["fecha"])
    bop = bop.set_index("fecha")
    flujos = bop.iloc[:, :6].abs().sum(axis=1)
    flujos_q = flujos.groupby(flujos.index.to_period("Q")).sum()

    pib = pd.read_excel(raw / "bccr_pib_dolares_trimestral.xlsx", sheet_name="Series", skiprows=4)
    pib = pib.rename(columns={pib.columns[0]: "fecha", pib.columns[1]: "pib"})
    pib["fecha"] = pd.to_datetime(pib["fecha"])
    pib = pib.set_index("fecha")["pib"]
    pib_q = pib.groupby(pib.index.to_period("Q")).last()

    razon = (flujos_q / pib_q).dropna()
    af = (razon - razon.min()) / (razon.max() - razon.min())
    af.name = "AF"
    return _ventana(af)

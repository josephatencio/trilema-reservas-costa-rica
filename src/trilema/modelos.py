"""Restricción del trilema y del cuadrilema y regresiones sobre la inflación."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import statsmodels.api as sm
from linearmodels.iv import IV2SLS

MUESTRAS = {
    "Minidevaluaciones": ("1999Q1", "2006Q3"),
    "Bandas": ("2006Q4", "2014Q4"),
    "Flotación administrada": ("2015Q1", "2025Q4"),
    "Robusta": ("2006Q4", "2025Q4"),
    "Completa": ("1999Q1", "2025Q4"),
}
TRILEMA = ["IM", "EC", "AF"]
CUADRILEMA = ["IM", "EC", "AF", "ri_pib_norm"]
CONTROLES = ["crecimiento_pib", "apertura_comercial", "terminos_intercambio", "vix", "tasa_efr"]
PARES = {"A: EC + IM": ["EC", "IM"], "B: EC + AF": ["EC", "AF"], "C: IM + AF": ["IM", "AF"]}


def rezagos_hac(n: int) -> int:
    """Selector de Newey y West (1994)."""
    return max(1, math.floor(4 * (n / 100) ** (2 / 9)))


def mco_hac(y, X, rezagos: int | None = None):
    """Mínimos cuadrados con errores HAC; por defecto, rezagos de Newey y West según len(y)."""
    rezagos = rezagos_hac(len(y)) if rezagos is None else rezagos
    return sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": rezagos})


def submuestra(df: pd.DataFrame, nombre: str) -> pd.DataFrame:
    ini, fin = MUESTRAS[nombre]
    return df[(df.index >= pd.Period(ini, "Q")) & (df.index <= pd.Period(fin, "Q"))]


def restriccion(df: pd.DataFrame, variables: list[str]) -> dict:
    """2 = suma de beta_k x_k + e, sin intercepto y con errores HAC, para cada muestra."""
    salida = {}
    for nombre in MUESTRAS:
        d = submuestra(df, nombre).dropna(subset=variables)
        salida[nombre] = mco_hac(pd.Series(2.0, index=d.index), d[variables])
    return salida


def participaciones(modelos: dict, df: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    """Peso relativo de cada vértice, |beta_k x la media de x_k|, como porcentaje de la suma."""
    filas = {}
    for nombre, m in modelos.items():
        medias = submuestra(df, nombre)[variables].mean()
        contribucion = (m.params[variables] * medias).abs()
        filas[nombre] = 100 * contribucion / contribucion.sum()
    return pd.DataFrame(filas).T


def en_diferencias(df: pd.DataFrame) -> pd.DataFrame:
    return df.diff().add_prefix("d_").dropna()


def macro_diferencias(df: pd.DataFrame, vertices: list[str]):
    """Inflación en primeras diferencias sobre los vértices, las reservas y los controles."""
    d = en_diferencias(df)
    columnas = [f"d_{v}" for v in vertices] + ["d_ri_pib"] + [f"d_{c}" for c in CONTROLES]
    return mco_hac(d["d_inflacion"], sm.add_constant(d[columnas]))


def pares_de_vertices(df: pd.DataFrame) -> dict:
    return {n: macro_diferencias(df, v) for n, v in PARES.items()}


def interacciones(df: pd.DataFrame) -> dict:
    """Cada vértice con su interacción centrada con las reservas, en primeras diferencias."""
    d = en_diferencias(df)
    salida = {}
    for v in TRILEMA:
        x = d[f"d_{v}"] - d[f"d_{v}"].mean()
        r = d["d_ri_pib"] - d["d_ri_pib"].mean()
        tb = pd.DataFrame({f"d_{v}": x, "d_ri_pib": r, f"{v}_x_RI": x * r})
        tb = tb.join(d[[f"d_{c}" for c in CONTROLES]])
        salida[v] = mco_hac(d["d_inflacion"], sm.add_constant(tb))
    return salida


def interacciones_por_par(df: pd.DataFrame) -> dict:
    """Cada par de vértices con la interacción centrada de ambos con las reservas, en primeras
    diferencias."""
    d = en_diferencias(df)
    r = d["d_ri_pib"] - d["d_ri_pib"].mean()
    salida = {}
    for nombre, vertices in PARES.items():
        tb = pd.DataFrame({"d_ri_pib": r})
        for v in vertices:
            x = d[f"d_{v}"] - d[f"d_{v}"].mean()
            tb[f"d_{v}"] = x
            tb[f"{v}_x_RI"] = x * r
        tb = tb.join(d[[f"d_{c}" for c in CONTROLES]])
        salida[nombre] = mco_hac(d["d_inflacion"], sm.add_constant(tb))
    return salida


def variables_instrumentales(df: pd.DataFrame) -> dict:
    """Efecto de las reservas con rezagos como instrumentos, primera etapa y test de Hausman.

    Sirve como análisis de sensibilidad. Los rezagos de una serie persistente son instrumentos
    discutibles, de modo que no se interpreta como identificación causal.
    """
    d = df.copy()
    d["ri_l1"] = d["ri_pib"].shift(1)
    d["ri_l2"] = d["ri_pib"].shift(2)
    d["inflacion_l1"] = d["inflacion"].shift(1)
    exogenas = TRILEMA + CONTROLES + ["inflacion_l1"]
    d = d.dropna(subset=["inflacion", "ri_pib", "ri_l1", "ri_l2", *exogenas])
    lags = rezagos_hac(len(d))
    modelo_iv = IV2SLS(d["inflacion"], sm.add_constant(d[exogenas]), d[["ri_pib"]],
                       d[["ri_l1", "ri_l2"]])
    iv = modelo_iv.fit(cov_type="kernel", bandwidth=lags)
    primera = mco_hac(d["ri_pib"], sm.add_constant(d[exogenas + ["ri_l1", "ri_l2"]]), lags)
    prueba_f = primera.wald_test("ri_l1=0, ri_l2=0", use_f=True, scalar=True)
    f_primera = float(np.squeeze(prueba_f.statistic))
    d["residuo"] = primera.resid
    hausman = mco_hac(d["inflacion"], sm.add_constant(d[exogenas + ["ri_pib", "residuo"]]), lags)
    return {
        "coef_iv": float(iv.params["ri_pib"]),
        "se_iv": float(iv.std_errors["ri_pib"]),
        "p_iv": float(iv.pvalues["ri_pib"]),
        "n": int(iv.nobs),
        "f_primera_etapa": f_primera,
        "p_hausman": float(hausman.pvalues["residuo"]),
        "p_sargan": float(iv.sargan.pval),
    }


def estrellas(p: float) -> str:
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


def tabla_restriccion(modelos: dict, variables: list[str]) -> pd.DataFrame:
    """Coeficientes, errores, valores p, N y R2 por muestra, en formato largo."""
    filas = []
    for muestra, m in modelos.items():
        for v in variables:
            filas.append({"muestra": muestra, "variable": v, "coef": m.params[v], "se": m.bse[v],
                          "p": m.pvalues[v], "n": int(m.nobs), "r2": m.rsquared,
                          "rezagos_hac": rezagos_hac(int(m.nobs))})
    return pd.DataFrame(filas)


def tabla_modelos(modelos: dict) -> pd.DataFrame:
    filas = []
    for nombre, m in modelos.items():
        for v in m.params.index:
            filas.append({"modelo": nombre, "variable": v, "coef": m.params[v], "se": m.bse[v],
                          "p": m.pvalues[v], "n": int(m.nobs), "r2": m.rsquared})
    return pd.DataFrame(filas)

"""Pruebas previas: raíz unitaria, cointegración, causalidad de Granger y quiebres estructurales."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.tsa.stattools import adfuller, coint, grangercausalitytests, kpss
from statsmodels.tsa.vector_ar.vecm import coint_johansen

from .modelos import mco_hac, rezagos_hac


def _phillips_perron(y: pd.Series) -> tuple[float, float]:
    """Regresión de Dickey-Fuller con errores HAC y valor p normal, solo como desempate."""
    v = y.dropna().to_numpy()
    res = mco_hac(np.diff(v), sm.add_constant(v[:-1]), rezagos_hac(len(v)))
    z = res.tvalues[1]
    return z, 2 * stats.norm.sf(abs(z))


def raiz_unitaria(df: pd.DataFrame, variables: dict[str, str]) -> pd.DataFrame:
    """ADF y KPSS. I(0) si ADF rechaza y KPSS no, I(1) si ADF no rechaza y KPSS sí, y ambiguo en
    otro caso."""
    filas = []
    for nombre, col in variables.items():
        s = df[col].dropna()
        adf = adfuller(s, autolag="AIC")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            kp = kpss(s, regression="c", nlags="auto")
        pp = _phillips_perron(s)
        p_a, p_k = adf[1], kp[1]
        if p_a < 0.05 and p_k > 0.05:
            orden = "I(0)"
        elif p_a > 0.05 and p_k < 0.05:
            orden = "I(1)"
        else:
            orden = "Ambiguo"
        p_diferencia = adfuller(s.diff().dropna(), autolag="AIC")[1]
        filas.append({"variable": nombre, "adf": adf[0], "p_adf": p_a, "kpss": kp[0], "p_kpss": p_k,
                      "pp": pp[0], "p_pp": pp[1], "p_adf_primera_dif": p_diferencia,
                      "orden": orden})
    return pd.DataFrame(filas)


def engle_granger(df: pd.DataFrame, variables: dict[str, str]) -> pd.DataFrame:
    filas = []
    for nombre, col in variables.items():
        d = df[["inflacion", col]].dropna()
        tau, p, _ = coint(d["inflacion"], d[col])
        filas.append({"par": f"Inflación ~ {nombre}", "tau": tau, "p": p})
    return pd.DataFrame(filas)


def johansen(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """Pruebas de la traza y del máximo valor propio, con intercepto y un rezago en diferencias."""
    j = coint_johansen(df[columnas].dropna().to_numpy(), det_order=0, k_ar_diff=1)
    return pd.DataFrame(
        {
            "h0_rango": [f"r <= {i}" for i in range(len(columnas))],
            "traza": j.lr1,
            "critico_traza_5": j.cvt[:, 1],
            "rechaza_traza": j.lr1 > j.cvt[:, 1],
            "max_valor_propio": j.lr2,
            "critico_max_5": j.cvm[:, 1],
            "rechaza_max": j.lr2 > j.cvm[:, 1],
        }
    )


def granger(df: pd.DataFrame, variables: dict[str, str], rezagos=(1, 2, 4)) -> pd.DataFrame:
    """Prueba de Granger, con hipótesis nula de que la variable no antecede a la inflación."""
    filas = []
    for nombre, col in variables.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = grangercausalitytests(df[["inflacion", col]].dropna(), maxlag=max(rezagos))
        for lag in rezagos:
            f, p = r[lag][0]["ssr_ftest"][:2]
            filas.append({"variable": nombre, "rezagos": lag, "f": f, "p": p})
    return pd.DataFrame(filas)


def quiebres(serie: pd.Series, min_segmento: int = 10, max_quiebres: int = 3) -> list[str]:
    """Búsqueda secuencial de quiebres en la media que minimiza la suma de residuos al cuadrado,
    al estilo de Bai y Perron."""
    s = serie.dropna()
    y = s.to_numpy()
    n = len(y)

    def ssr(segmento: np.ndarray) -> float:
        return float(np.sum((segmento - segmento.mean()) ** 2))

    def mejor(seg: np.ndarray, base: int) -> int | None:
        mejor_ssr, k_mejor = np.inf, None
        for k in range(min_segmento, len(seg) - min_segmento):
            total = ssr(seg[:k]) + ssr(seg[k:])
            if total < mejor_ssr:
                mejor_ssr, k_mejor = total, k
        return None if k_mejor is None else k_mejor + base

    encontrados: list[int] = []
    for _ in range(max_quiebres):
        cortes = [0, *sorted(encontrados), n]
        candidato, valor = None, np.inf
        for a, b in zip(cortes[:-1], cortes[1:]):
            if b - a < 2 * min_segmento:
                continue
            k = mejor(y[a:b], a)
            if k is not None:
                total = ssr(y[:k]) + ssr(y[k:])
                if total < valor:
                    candidato, valor = k, total
        if candidato is not None:
            encontrados.append(candidato)
    return [str(s.index[k]) for k in sorted(encontrados)]

"""Corre el análisis completo y guarda la base, las tablas y las figuras."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import articulo_ingles as ingles
from . import diagnosticos as dg
from . import figuras as fg
from . import modelos as md
from .base import PROCESADOS, RAIZ, construir_base, reservas_largo_plazo

SALIDAS = RAIZ / "outputs"
FIGURAS_ARTICULO = RAIZ / "report" / "latex" / "figures"
# Versión en inglés del artículo, con sus figuras, cuadros y cifras
FIGURAS_ARTICULO_EN = RAIZ / "report" / "latex" / "en" / "figures"
CUADROS_ARTICULO_EN = RAIZ / "report" / "latex" / "en" / "tables"
VARIABLES_PRUEBAS = {
    "Inflación": "inflacion",
    "IM": "IM",
    "EC": "EC",
    "AF": "AF",
    "RI/PIB": "ri_pib",
    "Crecimiento del PIB": "crecimiento_pib",
    "Términos de intercambio": "terminos_intercambio",
    "Apertura comercial": "apertura_comercial",
}
SERIES_QUIEBRES = {"IM": "IM", "EC": "EC", "AF": "AF", "RI/PIB": "ri_pib", "Inflación": "inflacion"}


@dataclass
class Resultados:
    base: pd.DataFrame
    reservas_anuales: pd.DataFrame
    trilema: dict
    cuadrilema: dict
    part_trilema: pd.DataFrame
    part_cuadrilema: pd.DataFrame
    pares: dict
    completo_dif: object
    interacciones: dict
    interacciones_pares: dict
    iv: dict
    raiz_unitaria: pd.DataFrame
    engle_granger: pd.DataFrame
    johansen: pd.DataFrame
    granger: pd.DataFrame
    quiebres: pd.DataFrame


def ejecutar() -> Resultados:
    base = construir_base()
    tri = md.restriccion(base, md.TRILEMA)
    cua = md.restriccion(base, md.CUADRILEMA)
    i1 = ["inflacion", "ri_pib", "EC", "AF"]
    quiebres = pd.DataFrame({n: pd.Series(dg.quiebres(base[c]))
                             for n, c in SERIES_QUIEBRES.items()})
    quiebres.index = [f"Quiebre {i + 1}" for i in quiebres.index]
    otros = {k: v for k, v in VARIABLES_PRUEBAS.items() if k != "Inflación"}
    return Resultados(
        base=base,
        reservas_anuales=reservas_largo_plazo(),
        trilema=tri,
        cuadrilema=cua,
        part_trilema=md.participaciones(tri, base, md.TRILEMA),
        part_cuadrilema=md.participaciones(cua, base, md.CUADRILEMA),
        pares=md.pares_de_vertices(base),
        completo_dif=md.macro_diferencias(base, md.TRILEMA),
        interacciones=md.interacciones(base),
        interacciones_pares=md.interacciones_por_par(base),
        iv=md.variables_instrumentales(base),
        raiz_unitaria=dg.raiz_unitaria(base, VARIABLES_PRUEBAS),
        engle_granger=dg.engle_granger(base, otros),
        johansen=dg.johansen(base, i1),
        granger=dg.granger(base, otros),
        quiebres=quiebres,
    )


def guardar(res: Resultados, carpeta: Path = SALIDAS) -> None:
    tablas = carpeta / "tables"
    figs = carpeta / "figures"
    tablas.mkdir(parents=True, exist_ok=True)
    PROCESADOS.mkdir(parents=True, exist_ok=True)
    res.base.to_csv(PROCESADOS / "base_trimestral.csv", encoding="utf-8-sig")
    sin_indice = {
        "cuadro1_trilema": md.tabla_restriccion(res.trilema, md.TRILEMA),
        "cuadro2_cuadrilema": md.tabla_restriccion(res.cuadrilema, md.CUADRILEMA),
        "cuadro3_inflacion_diferencias": md.tabla_modelos(res.pares),
        "inflacion_diferencias_tres_vertices": md.tabla_modelos({"Completo": res.completo_dif}),
        "interacciones_vertice_reservas": md.tabla_modelos(res.interacciones),
        "interacciones_pares_reservas": md.tabla_modelos(res.interacciones_pares),
        "diagnostico_raiz_unitaria": res.raiz_unitaria,
        "diagnostico_engle_granger": res.engle_granger,
        "diagnostico_johansen": res.johansen,
        "diagnostico_granger": res.granger,
    }
    con_indice = {
        "participacion_trilema": res.part_trilema,
        "participacion_cuadrilema": res.part_cuadrilema,
        "reservas_pib_1960_2024": res.reservas_anuales,
        "diagnostico_quiebres": res.quiebres,
        "sensibilidad_variables_instrumentales": pd.Series(res.iv).to_frame("valor"),
    }
    for nombre, tabla in sin_indice.items():
        tabla.to_csv(tablas / f"{nombre}.csv", index=False, encoding="utf-8-sig")
    for nombre, tabla in con_indice.items():
        tabla.to_csv(tablas / f"{nombre}.csv", encoding="utf-8-sig")

    fg.panel_indices(res.base, figs / "indices_trilema.png",
                     FIGURAS_ARTICULO / "indices_trilema.pdf")
    fg.participacion(res.part_trilema, res.part_cuadrilema,
                     figs / "participacion_trilema_cuadrilema.png",
                     FIGURAS_ARTICULO / "participacion_trilema_cuadrilema.pdf")
    fg.reservas_largo_plazo(res.reservas_anuales, figs / "reservas_pib_1960_2024.png",
                            FIGURAS_ARTICULO / "reservas_pib_1960_2024.pdf")
    fg.inflacion_y_reservas(res.base, figs / "inflacion_y_reservas.png")

    # Las mismas figuras con los textos en inglés, y los cuadros y las cifras de esa versión
    en = figs / "en"
    fg.panel_indices(res.base, en / "indices_trilema.png",
                     FIGURAS_ARTICULO_EN / "indices_trilema.pdf", idioma="en")
    fg.participacion(res.part_trilema, res.part_cuadrilema,
                     en / "participacion_trilema_cuadrilema.png",
                     FIGURAS_ARTICULO_EN / "participacion_trilema_cuadrilema.pdf", idioma="en")
    fg.reservas_largo_plazo(res.reservas_anuales, en / "reservas_pib_1960_2024.png",
                            FIGURAS_ARTICULO_EN / "reservas_pib_1960_2024.pdf", idioma="en")
    fg.inflacion_y_reservas(res.base, en / "inflacion_y_reservas.png", idioma="en")
    ingles.escribir_cuadros(res, CUADROS_ARTICULO_EN)

"""Cuadros y cifras de la versión en inglés del artículo."""
from __future__ import annotations

from pathlib import Path

from . import modelos as md

SIGLAS = {"IM": "MI", "EC": "ERS", "AF": "FO", "ri_pib_norm": "IR/GDP"}
REGIMENES = {"Minidevaluaciones": "Crawling peg", "Bandas": "Bands",
             "Flotación administrada": "Managed float", "Robusta": "Robust"}
FILAS_INFLACION = {"d_IM": r"$\Delta$MI", "d_EC": r"$\Delta$ERS", "d_AF": r"$\Delta$FO",
                   "d_ri_pib": r"$\Delta$IR/GDP", "d_apertura_comercial": r"$\Delta$Trade openness",
                   "d_vix": r"$\Delta$VIX"}
MODELOS = {"A: EC + IM": ("Model A", "ERS + MI"), "B: EC + AF": ("Model B", "ERS + FO"),
           "C: IM + AF": ("Model C", "MI + FO")}


def _con_estrellas(m, v: str, decimales: int) -> str:
    estrellas = md.estrellas(m.pvalues[v])
    return f"{m.params[v]:.{decimales}f}" + (f"$^{{{estrellas}}}$" if estrellas else "")


def _error(m, v: str, decimales: int) -> str:
    return rf"{{\scriptsize ({m.bse[v]:.{decimales}f})}}"


def cuadro_restriccion(modelos: dict, variables: list[str]) -> str:
    """Cuadros 1 y 2. Coeficiente con estrellas y error estándar HAC debajo, por régimen."""
    muestras = list(REGIMENES)
    lineas = [r"\begin{tabular}{lcccc}", r"\toprule",
              " & " + " & ".join(rf"\textbf{{{REGIMENES[m]}}}" for m in muestras) + r" \\",
              r"\cmidrule(lr){2-2} \cmidrule(lr){3-3} \cmidrule(lr){4-4} \cmidrule(lr){5-5}",
              " & " + " & ".join(f"{md.MUESTRAS[m][0]}--{md.MUESTRAS[m][1]}" for m in muestras)
              + r" \\", r"\midrule"]
    for i, v in enumerate(variables):
        if i:
            lineas.append(r"\addlinespace")
        lineas.append(SIGLAS[v] + " & " + " & ".join(_con_estrellas(modelos[m], v, 4)
                                                     for m in muestras) + r" \\")
        lineas.append(" & " + " & ".join(_error(modelos[m], v, 4) for m in muestras) + r" \\")
    lineas += [r"\midrule",
               "$N$ & " + " & ".join(str(int(modelos[m].nobs)) for m in muestras) + r" \\",
               "$R^2$ & " + " & ".join(f"{modelos[m].rsquared:.4f}" for m in muestras) + r" \\",
               r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lineas) + "\n"


def cuadro_inflacion(pares: dict) -> str:
    """Cuadro 3. Inflación en primeras diferencias con cada par de vértices."""
    nombres = list(MODELOS)
    lineas = [r"\begin{tabular*}{\textwidth}{l @{\extracolsep{\fill}} ccc}", r"\toprule",
              " & " + " & ".join(rf"\textbf{{{MODELOS[n][0]}}}" for n in nombres) + r" \\",
              " & " + " & ".join(MODELOS[n][1] for n in nombres) + r" \\", r"\midrule"]
    for v, etiqueta in FILAS_INFLACION.items():
        if v == "d_ri_pib":
            lineas.append(r"\addlinespace")
        coeficientes = [_con_estrellas(pares[n], v, 3) if v in pares[n].params else "--"
                        for n in nombres]
        errores = [_error(pares[n], v, 3) if v in pares[n].params else "" for n in nombres]
        lineas.append(etiqueta + " & " + " & ".join(coeficientes) + r" \\")
        lineas.append(" & " + " & ".join(errores) + r" \\")
    lineas += [r"\midrule", r"Other controls & Yes & Yes & Yes \\",
               "$N$ & " + " & ".join(str(int(pares[n].nobs)) for n in nombres) + r" \\",
               "$R^2$ & " + " & ".join(f"{pares[n].rsquared:.3f}" for n in nombres) + r" \\",
               r"\bottomrule", r"\end{tabular*}"]
    return "\n".join(lineas) + "\n"


def cifras(res) -> dict[str, str]:
    """Cada cifra calculada que cita el texto, con el nombre de su macro."""
    t, c = res.part_trilema, res.part_cuadrilema
    valores_p = sorted(m.pvalues["IM_x_RI"] for m in (res.interacciones["IM"],
                                                       res.interacciones_pares["A: EC + IM"],
                                                       res.interacciones_pares["C: IM + AF"]))
    coef_reservas = abs(res.pares["A: EC + IM"].params["d_ri_pib"])
    n = {m: int(res.trilema[m].nobs) for m in md.MUESTRAS}
    return {
        "Trimestres": str(len(res.base)),
        "NMini": str(n["Minidevaluaciones"]), "NBandas": str(n["Bandas"]),
        "NFlotacion": str(n["Flotación administrada"]), "NRobusta": str(n["Robusta"]),
        "RdosTrilema": f"{res.trilema['Robusta'].rsquared:.4f}",
        "RdosCuadrilema": f"{res.cuadrilema['Robusta'].rsquared:.4f}",
        "PesoEcRobusta": f"{t.loc['Robusta', 'EC']:.2f}",
        "PesoImRobusta": f"{t.loc['Robusta', 'IM']:.2f}",
        "PesoAfRobusta": f"{t.loc['Robusta', 'AF']:.2f}",
        "PesoImBandas": f"{t.loc['Bandas', 'IM']:.2f}",
        "PesoAfBandas": f"{t.loc['Bandas', 'AF']:.2f}",
        "PesoEcFlotacion": f"{t.loc['Flotación administrada', 'EC']:.2f}",
        "PesoRiRobusta": f"{c.loc['Robusta', 'ri_pib_norm']:.2f}",
        "PesoRiBandas": f"{c.loc['Bandas', 'ri_pib_norm']:.2f}",
        "PesoRiFlotacion": f"{c.loc['Flotación administrada', 'ri_pib_norm']:.2f}",
        "PInteraccionMin": f"{valores_p[0]:.3f}", "PInteraccionMax": f"{valores_p[-1]:.3f}",
        "CoefReservas": f"{coef_reservas:.1f}", "CoefReservasPuntos": f"{coef_reservas / 100:.3f}",
    }


def escribir_cuadros(res, carpeta: Path) -> None:
    """Escribe los tres cuadros y las cifras del texto de la versión en inglés."""
    carpeta.mkdir(parents=True, exist_ok=True)
    archivos = {
        "cuadro1_trilema": cuadro_restriccion(res.trilema, md.TRILEMA),
        "cuadro2_cuadrilema": cuadro_restriccion(res.cuadrilema, md.CUADRILEMA),
        "cuadro3_inflacion": cuadro_inflacion(res.pares),
        "cifras": "\n".join(["% Generado por python -m trilema. No editar a mano."]
                            + [rf"\newcommand{{\cifra{k}}}{{{v}}}" for k, v in cifras(res).items()])
                  + "\n",
    }
    for nombre, texto in archivos.items():
        (carpeta / f"{nombre}.tex").write_text(texto, encoding="utf-8")

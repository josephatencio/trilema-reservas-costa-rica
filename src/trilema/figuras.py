"""Figuras del artículo, calculadas desde los resultados.

Cada figura se guarda dos veces, como PNG en outputs/figures, para verla sin compilar nada, y
como PDF vectorial en report/latex/figures, que es la que usa el artículo. Se dibujan al tamaño en
que se imprimen y sin título, porque el artículo lo pone en el pie de cada figura. Con
idioma="en" se dibuja la misma figura con los textos de la versión en inglés del artículo.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

AZUL, CELESTE, CLARO, NARANJA, GRIS = "#153A63", "#4F8FC0", "#A9C8E4", "#D1602F", "#7A8490"
COLORES = {"EC": AZUL, "IM": CELESTE, "AF": CLARO, "ri_pib_norm": NARANJA}
# Textos de cada figura en español y en inglés. En inglés las siglas son MI, ERS, FO e IR.
TEXTOS = {
    "es": {
        "nombres": {
            "IM": "Independencia monetaria (IM)",
            "EC": "Estabilidad cambiaria (EC)",
            "AF": "Apertura financiera (AF)",
            "ri_pib_norm": "Reservas internacionales (RI)",
        },
        # Los mismos nombres en dos líneas, para escribirlos al lado de cada panel
        "al_lado": {
            "IM": "Independencia\nmonetaria (IM)",
            "EC": "Estabilidad\ncambiaria (EC)",
            "AF": "Apertura\nfinanciera (AF)",
            "ri_pib_norm": "Reservas\ninternacionales (RI)",
        },
        "regimenes": ("Minidevaluaciones", "Bandas", "Flotación administrada"),
        "regimenes_cortos": ("Minidevaluaciones", "Bandas", "Flotación"),
        "serie": "Serie trimestral",
        "promedio": "Promedio móvil de 8 trimestres",
        "muestras": ("Muestra robusta\n2006-2025", "Bandas\n2006-2014", "Flotación\n2015-2025"),
        "trilema": "Trilema",
        "cuadrilema": "Cuadrilema (trilema con reservas)",
        "inflacion": "Inflación interanual, promedio del trimestre",
        "reservas_trimestre": "Reservas internacionales netas sobre el PIB del trimestre",
        "tendencia": "Tendencia lineal",
        "reservas_pib": "Reservas sobre el PIB",
        "por_ciento": " %",
    },
    "en": {
        "nombres": {
            "IM": "Monetary independence (MI)",
            "EC": "Exchange rate stability (ERS)",
            "AF": "Financial openness (FO)",
            "ri_pib_norm": "International reserves (IR)",
        },
        "al_lado": {
            "IM": "Monetary\nindependence (MI)",
            "EC": "Exchange rate\nstability (ERS)",
            "AF": "Financial\nopenness (FO)",
            "ri_pib_norm": "International\nreserves (IR)",
        },
        "regimenes": ("Crawling peg", "Bands", "Managed float"),
        "regimenes_cortos": ("Crawling peg", "Bands", "Float"),
        "serie": "Quarterly series",
        "promedio": "8-quarter moving average",
        "muestras": ("Robust sample\n2006-2025", "Bands\n2006-2014", "Managed float\n2015-2025"),
        "trilema": "Trilemma",
        "cuadrilema": "Quadrilemma (trilemma with reserves)",
        "inflacion": "Year-on-year inflation, quarterly average",
        "reservas_trimestre": "Net international reserves to quarterly GDP",
        "tendencia": "Linear trend",
        "reservas_pib": "Reserves to GDP",
        "por_ciento": "%",
    },
}
ANCHO = 6.3  # ancho del texto del artículo, en pulgadas
ESTILO = {
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9.5, "axes.titlesize": 9.5, "axes.titleweight": "bold", "axes.labelsize": 9.5,
    "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9, "legend.frameon": False,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
    "axes.edgecolor": "#444444", "axes.grid": True, "grid.color": "#DADDE1", "grid.linewidth": 0.5,
    "axes.axisbelow": True, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 3, "ytick.major.size": 0, "lines.linewidth": 1.6, "savefig.dpi": 300,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "figure.constrained_layout.use": True,
    "pdf.fonttype": 42,
}
CAMBIOS_DE_REGIMEN = (("2006Q4", "Bandas"), ("2015Q1", "Flotación administrada"))


def _guardar(fig, png: Path, pdf: Path | None) -> None:
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, facecolor="white")
    if pdf is not None:
        pdf.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(pdf, facecolor="white")
    plt.close(fig)


def _regimenes(ax, rotular: bool = False, idioma: str = "es") -> None:
    """Líneas en los cambios de régimen cambiario y, si se pide, el nombre de cada régimen arriba
    del panel."""
    for trimestre, _ in CAMBIOS_DE_REGIMEN:
        ax.axvline(pd.Period(trimestre, "Q").to_timestamp(), color="#444444", lw=0.8, ls="--")
    if rotular:
        inicios = ("1999Q1", *(trimestre for trimestre, _ in CAMBIOS_DE_REGIMEN))
        rotulos = zip(inicios, TEXTOS[idioma]["regimenes"])
        for trimestre, nombre in rotulos:
            ax.annotate(nombre, (pd.Period(trimestre, "Q").to_timestamp(), 1),
                        xycoords=("data", "axes fraction"), xytext=(4, 3),
                        textcoords="offset points", va="bottom", fontsize=8.5, color="#444444")


def panel_indices(base: pd.DataFrame, png: Path, pdf: Path | None = None,
                  idioma: str = "es") -> None:
    """Serie trimestral y promedio móvil de 8 trimestres de cada índice, con los tres regímenes
    cambiarios."""
    t = TEXTOS[idioma]
    x = base.index.to_timestamp()
    with plt.rc_context(ESTILO):
        fig, ejes = plt.subplots(4, 1, figsize=(ANCHO, 5.0), sharex=True)
        for i, (ax, v) in enumerate(zip(ejes, ["IM", "EC", "AF", "ri_pib_norm"])):
            color = NARANJA if v == "ri_pib_norm" else AZUL
            ax.plot(x, base[v], color=color, lw=0.8, alpha=0.35)
            ax.plot(x, base[v].rolling(8, min_periods=8).mean(), color=color, lw=1.9)
            ax.set_ylim(0, 1.05)
            ax.set_yticks([0, 0.5, 1])
            ax.set_ylabel(t["al_lado"][v], rotation=0, ha="right", va="center", color=color,
                          fontweight="bold", fontsize=9, labelpad=10, linespacing=1.25)
            ax.grid(axis="x", visible=False)
            _regimenes(ax, rotular=i == 0, idioma=idioma)
        ejes[-1].set_xlim(x[0], x[-1])
        ejes[-1].xaxis.set_major_locator(mdates.YearLocator(4, month=1, day=1))
        ejes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        leyenda = [Line2D([], [], color=GRIS, lw=0.8, alpha=0.6, label=t["serie"]),
                   Line2D([], [], color=GRIS, lw=1.9, label=t["promedio"])]
        fig.legend(handles=leyenda, loc="outside lower center", ncol=2)
        _guardar(fig, png, pdf)


def participacion(tri: pd.DataFrame, cuad: pd.DataFrame, png: Path,
                  pdf: Path | None = None, idioma: str = "es") -> None:
    """Peso relativo de cada componente en la muestra robusta, en bandas y en flotación
    administrada."""
    t = TEXTOS[idioma]
    muestras = dict(zip(["Robusta", "Bandas", "Flotación administrada"], t["muestras"]))
    with plt.rc_context(ESTILO):
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(ANCHO, 4.0))

        def panel(ax, tb, componentes, titulo):
            for i, m in enumerate(muestras):
                izquierda = 0.0
                for c in componentes:
                    v = tb.loc[m, c]
                    ax.barh(i, v, left=izquierda, height=0.62, color=COLORES[c], edgecolor="white",
                            linewidth=0.8)
                    if v >= 6:
                        claro = c in ("AF", "IM")
                        ax.text(izquierda + v / 2, i, f"{v:.1f}{t['por_ciento']}", ha="center",
                                va="center",
                                fontsize=8.5, fontweight="bold",
                                color="#1A1A1A" if claro else "white")
                    else:  # en un segmento angosto la cifra va encima de la barra
                        ax.annotate(f"{v:.1f}{t['por_ciento']}", (izquierda + v / 2, i - 0.31),
                                    xytext=(0, 2),
                                    textcoords="offset points", ha="center", va="bottom",
                                    fontsize=8, color="#333333")
                    izquierda += v
            ax.set_xlim(0, 100)
            ax.set_ylim(len(muestras) - 0.45, -0.75)
            ax.set_yticks(range(len(muestras)), list(muestras.values()))
            ax.set_xticks([])
            ax.grid(False)
            ax.spines[:].set_visible(False)
            ax.tick_params(length=0)
            ax.set_title(titulo, loc="left")

        panel(a1, tri, ["EC", "IM", "AF"], t["trilema"])
        panel(a2, cuad, ["ri_pib_norm", "EC", "IM", "AF"], t["cuadrilema"])
        orden = ["EC", "IM", "AF", "ri_pib_norm"]
        fig.legend(handles=[Patch(color=COLORES[c], label=t["nombres"][c]) for c in orden],
                   loc="outside lower center", ncol=2)
        _guardar(fig, png, pdf)


def inflacion_y_reservas(base: pd.DataFrame, png: Path, pdf: Path | None = None,
                         idioma: str = "es") -> None:
    """Inflación interanual y reservas sobre el PIB trimestral, en dos paneles con el mismo eje de
    tiempo."""
    t = TEXTOS[idioma]
    x = base.index.to_timestamp()
    with plt.rc_context(ESTILO):
        fig, (a, b) = plt.subplots(2, 1, figsize=(ANCHO, 3.8), sharex=True)
        a.plot(x, base["inflacion"], color=AZUL)
        a.axhline(0, color="#444444", lw=0.6)
        a.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:.0f}{t['por_ciento']}"))
        a.set_title(t["inflacion"], loc="left", pad=14)
        b.plot(x, 100 * base["ri_pib"], color=NARANJA)
        b.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:.0f}{t['por_ciento']}"))
        b.set_title(t["reservas_trimestre"], loc="left")
        for i, ax in enumerate((a, b)):
            ax.grid(axis="x", visible=False)
            _regimenes(ax, rotular=i == 0, idioma=idioma)
        b.set_xlim(x[0], x[-1])
        b.xaxis.set_major_locator(mdates.YearLocator(4, month=1, day=1))
        b.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        _guardar(fig, png, pdf)


def reservas_largo_plazo(anual: pd.DataFrame, png: Path, pdf: Path | None = None,
                         idioma: str = "es") -> None:
    """Reservas sobre el PIB de 1960 a 2024, con su tendencia lineal y los regímenes cambiarios
    desde 1984."""
    t = TEXTOS[idioma]
    anios = anual.index.to_numpy()
    valores = anual["ri_pib"].to_numpy()
    pendiente, intercepto = np.polyfit(anios, valores, 1)
    with plt.rc_context(ESTILO):
        fig, ax = plt.subplots(figsize=(ANCHO, 2.9))
        regimenes = [(inicio, fin, nombre) for (inicio, fin), nombre
                     in zip(((1984, 2006), (2006, 2015), (2015, 2024.5)), t["regimenes_cortos"])]
        for (inicio, fin, nombre), tono in zip(regimenes, ("#EEF1F5", "#E2E7EE", "#EEF1F5")):
            ax.axvspan(inicio, fin, color=tono, lw=0)
            ax.text((inicio + fin) / 2, 1.0, nombre, transform=ax.get_xaxis_transform(),
                    ha="center", va="bottom", fontsize=8.5, color="#444444")
        ax.plot(anios, valores, color=AZUL, lw=1.8)
        ax.plot(anios, intercepto + pendiente * anios, color=NARANJA, lw=1.1, ls="--")
        ax.annotate(t["tendencia"], (1991, intercepto + pendiente * 1991), xytext=(1986.5, 4.2),
                    textcoords="data", ha="center", color=NARANJA, fontsize=8.5, fontweight="bold",
                    arrowprops={"arrowstyle": "-", "color": NARANJA, "lw": 0.8, "shrinkA": 2,
                                "shrinkB": 2})
        ax.set_xlim(anios[0] - 0.5, anios[-1] + 0.5)
        ax.set_ylim(0, None)
        ax.set_xticks(range(1960, 2025, 8))
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:.0f}{t['por_ciento']}"))
        ax.set_ylabel(t["reservas_pib"])
        ax.grid(axis="x", visible=False)
        _guardar(fig, png, pdf)

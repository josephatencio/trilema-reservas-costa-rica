"""Corre el análisis completo con python -m trilema."""
from __future__ import annotations

import sys
import warnings

from .flujo import SALIDAS, ejecutar, guardar


def main() -> None:
    warnings.filterwarnings("ignore", category=FutureWarning)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    res = ejecutar()
    guardar(res)
    tri, cua = res.part_trilema, res.part_cuadrilema
    print(f"Base: {len(res.base)} trimestres, de {res.base.index[0]} a {res.base.index[-1]}")
    print(f"Muestra robusta. R2 trilema: {res.trilema['Robusta'].rsquared:.4f}; R2 cuadrilema: "
          f"{res.cuadrilema['Robusta'].rsquared:.4f}")
    print(f"Peso de la estabilidad cambiaria (trilema, robusta): {tri.loc['Robusta', 'EC']:.2f}%")
    print(f"Peso de las reservas (cuadrilema, robusta): {cua.loc['Robusta', 'ri_pib_norm']:.2f}%")
    print(f"Tablas y figuras en {SALIDAS}")


if __name__ == "__main__":
    main()

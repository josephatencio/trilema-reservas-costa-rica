"""Las cifras publicadas en el artículo deben salir de los datos crudos con este código."""
import numpy as np
import pytest

from trilema import modelos as md
from trilema.flujo import ejecutar

# Cuadro 1 del artículo, con el coeficiente y el error estándar
CUADRO_1 = {
    "Minidevaluaciones": {"IM": (-0.0155, 0.0075), "EC": (2.0431, 0.0043), "AF": (0.0028, 0.0074),
                          "n": 31, "r2": 1.0000},
    "Bandas": {"IM": (1.3918, 0.1599), "EC": (1.3652, 0.2099), "AF": (0.7426, 0.3369), "n": 33,
               "r2": 0.9724},
    "Flotación administrada": {"IM": (0.2968, 0.1483), "EC": (2.2204, 0.0910),
                               "AF": (0.8222, 0.1453), "n": 44, "r2": 0.9801},
    "Robusta": {"IM": (0.8043, 0.1670), "EC": (1.9063, 0.1507), "AF": (0.6530, 0.2026), "n": 77,
                "r2": 0.9710},
}
# Cuadro 2 del artículo
CUADRO_2 = {
    "Minidevaluaciones": {"IM": (-0.0159, 0.0086), "EC": (2.0436, 0.0081), "AF": (0.0033, 0.0075),
                          "ri_pib_norm": (-0.0020, 0.0188), "n": 31, "r2": 1.0000},
    "Bandas": {"IM": (1.2615, 0.1492), "EC": (0.9096, 0.3287), "AF": (0.5958, 0.2095),
               "ri_pib_norm": (0.7012, 0.2989), "n": 33, "r2": 0.9760},
    "Flotación administrada": {"IM": (0.2207, 0.1630), "EC": (2.0083, 0.1464),
                               "AF": (0.7888, 0.1837), "ri_pib_norm": (0.3072, 0.2206), "n": 44,
                               "r2": 0.9808},
    "Robusta": {"IM": (0.7071, 0.1578), "EC": (1.5968, 0.2015), "AF": (0.5860, 0.2089),
                "ri_pib_norm": (0.4541, 0.1736), "n": 77, "r2": 0.9726},
}
# Cuadro 3 del artículo, con el coeficiente y el error estándar de cada modelo
CUADRO_3 = {
    "A: EC + IM": {"d_IM": (-0.227, 0.517), "d_EC": (-0.210, 0.821), "d_ri_pib": (-6.405, 2.639),
                   "d_apertura_comercial": (8.588, 2.885), "d_vix": (0.048, 0.024), "r2": 0.148},
    "B: EC + AF": {"d_EC": (-0.121, 0.833), "d_AF": (-0.130, 0.398), "d_ri_pib": (-6.216, 2.703),
                   "d_apertura_comercial": (8.784, 2.928), "d_vix": (0.049, 0.024), "r2": 0.147},
    "C: IM + AF": {"d_IM": (-0.218, 0.504), "d_AF": (-0.137, 0.400), "d_ri_pib": (-6.462, 2.764),
                   "d_apertura_comercial": (8.763, 2.845), "d_vix": (0.048, 0.024), "r2": 0.149},
}


@pytest.fixture(scope="module")
def res():
    return ejecutar()


def test_base_tiene_108_trimestres_completos(res):
    assert len(res.base) == 108
    assert res.base[["IM", "EC", "AF", "ri_pib_norm", "inflacion"]].notna().all().all()
    assert str(res.base.index[0]) == "1999Q1" and str(res.base.index[-1]) == "2025Q4"


def test_indices_entre_cero_y_uno(res):
    for v in ("IM", "EC", "AF", "ri_pib_norm"):
        assert res.base[v].between(0, 1).all(), v


@pytest.mark.parametrize("cuadro,atributo", [(CUADRO_1, "trilema"), (CUADRO_2, "cuadrilema")])
def test_restricciones_iguales_al_articulo(res, cuadro, atributo):
    modelos = getattr(res, atributo)
    for muestra, esperado in cuadro.items():
        m = modelos[muestra]
        assert int(m.nobs) == esperado["n"]
        assert round(m.rsquared, 4) == pytest.approx(esperado["r2"], abs=1e-4)
        for v, valores in esperado.items():
            if v in ("n", "r2"):
                continue
            coef, se = valores
            assert m.params[v] == pytest.approx(coef, abs=6e-5), (muestra, v)
            assert m.bse[v] == pytest.approx(se, abs=6e-5), (muestra, v)


def test_inflacion_en_diferencias_igual_al_articulo(res):
    for modelo, esperado in CUADRO_3.items():
        m = res.pares[modelo]
        assert int(m.nobs) == 107
        assert round(m.rsquared, 3) == pytest.approx(esperado["r2"], abs=1e-3)
        for v, valores in esperado.items():
            if v == "r2":
                continue
            assert m.params[v] == pytest.approx(valores[0], abs=6e-4), (modelo, v)
            assert m.bse[v] == pytest.approx(valores[1], abs=6e-4), (modelo, v)


def test_interacciones_del_articulo(res):
    # Solo la interacción de IM con las reservas es significativa. Es negativa en las tres
    # especificaciones que la incluyen (IM sola, par A y par C), con valores p de 0.014 a 0.032
    im = [res.interacciones["IM"], res.interacciones_pares["A: EC + IM"],
          res.interacciones_pares["C: IM + AF"]]
    valores_p = sorted(round(m.pvalues["IM_x_RI"], 3) for m in im)
    assert valores_p == [0.014, 0.031, 0.032]
    assert all(m.params["IM_x_RI"] < 0 for m in im)
    otras = [res.interacciones["EC"].pvalues["EC_x_RI"], res.interacciones["AF"].pvalues["AF_x_RI"]]
    for m in res.interacciones_pares.values():
        otras += [m.pvalues[v] for v in m.params.index if v.endswith("_x_RI")
                  and not v.startswith("IM")]
    assert all(p > 0.10 for p in otras)


def test_reservas_largo_plazo_del_articulo(res):
    # Según el anexo, menos de 4 % del PIB en casi todo 1960-1979 y cerca de 15 % en 2023-2024
    ri = res.reservas_anuales["ri_pib"]
    assert (ri.loc[1960:1979] < 4).mean() >= 0.9
    assert all(14 < ri.loc[a] < 16 for a in (2023, 2024))


def test_participaciones_iguales_al_articulo(res):
    t, c = res.part_trilema, res.part_cuadrilema
    assert t.loc["Robusta", "EC"] == pytest.approx(67.88, abs=0.01)
    assert t.loc["Robusta", "IM"] == pytest.approx(18.74, abs=0.01)
    assert t.loc["Robusta", "AF"] == pytest.approx(13.39, abs=0.01)
    assert t.loc["Bandas", "IM"] == pytest.approx(34.49, abs=0.01)
    assert t.loc["Bandas", "AF"] == pytest.approx(16.76, abs=0.01)
    assert t.loc["Flotación administrada", "EC"] == pytest.approx(78.08, abs=0.01)
    # Participaciones de las reservas que reporta el artículo, en el texto y en la figura
    assert c.loc["Robusta", "ri_pib_norm"] == pytest.approx(14.80, abs=0.005)
    assert c.loc["Bandas", "ri_pib_norm"] == pytest.approx(23.09, abs=0.005)
    assert c.loc["Flotación administrada", "ri_pib_norm"] == pytest.approx(9.82, abs=0.005)


def test_participaciones_suman_cien(res):
    assert np.allclose(res.part_trilema.sum(axis=1), 100)
    assert np.allclose(res.part_cuadrilema.sum(axis=1), 100)


def test_orden_de_integracion_del_articulo(res):
    orden = res.raiz_unitaria.set_index("variable")["orden"]
    assert orden["Inflación"] == "I(1)"
    assert orden["IM"] == "I(0)"
    assert orden["Crecimiento del PIB"] == "I(0)"
    for v in ("EC", "Apertura comercial", "Términos de intercambio"):
        assert orden[v] == "I(1)"


def test_granger_del_articulo(res):
    g = res.granger.set_index(["variable", "rezagos"])["p"]
    assert g[("Apertura comercial", 1)] < 0.05
    assert g[("EC", 4)] < 0.05
    assert all(g[("RI/PIB", k)] > 0.05 for k in (1, 2, 4))


def test_johansen_un_vector(res):
    j = res.johansen
    assert bool(j.loc[0, "rechaza_traza"]) and not bool(j.loc[1, "rechaza_traza"])


def test_rezagos_hac():
    assert md.rezagos_hac(108) == 4
    assert md.rezagos_hac(77) == 3
    assert md.rezagos_hac(31) == 3

# -*- coding: utf-8 -*-
"""
Experimento de calibracion: que hace cada defecto de diseno con la inferencia.

Sobre cada paisaje sintetico se colocan los sitios de dos maneras cuya verdad
se conoce por construccion —sin efecto (S0, intercambiable con el nulo) y con
efecto (S1, la mejor de K colocaciones)— y se ejecuta el contraste tres veces:
con el procedimiento correcto y con cada uno de los dos defectos de diseno.

El diseno es apareado: los tres procedimientos comparten paisaje, configuracion
y colocacion observada, de modo que toda diferencia entre ellos es atribuible
al defecto y a nada mas.

Lo que se mide:

  calibracion   en S0 el p del procedimiento correcto es uniforme por simetria;
                el desvio de la uniformidad en los defectuosos es la medida
                exacta de cuanto rompen la inferencia
  potencia      en S1 la potencia del correcto tiene un valor teorico conocido
                (el maximo de K sorteos frente a N sorteos frescos); la perdida
                de los defectuosos se mide contra ese techo
  mecanismo     el sesgo del recorte se registra junto al angulo entre la nube
                y el grano del terreno, para mostrar de que depende su signo
  diagnosticos  fraccion de nulos que pisan agua y cobertura de orientaciones,
                que delatan ambos defectos sin conocer la verdad

Salida: results/calibracion.json
"""
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from terrain_lab import (N_SITIOS, PASOS_ORIENTACION, cobertura_orientaciones,
                         colocacion_S0, colocacion_S1, contraste, densidad,
                         desalineacion, forma_alargada, nulo_rigido, paisaje,
                         region_ajustada)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")

R_SEMILLAS = 60      # replicas de paisaje
N_NULL = 199         # colocaciones nulas por contraste
K_MEJOR = 40         # candidatas entre las que S1 elige la mejor
MARGEN_AJUSTADO = 25 # celdas del defecto de recorte (750 m a 30 m/celda)
ALFA = 0.05
SEMILLA_BASE = 20260830


def una_replica(semilla):
    dem, agua, theta = paisaje(semilla=semilla)
    rng = np.random.default_rng(SEMILLA_BASE + semilla)
    dc, dr = forma_alargada(rng)

    # colocaciones observadas de los dos escenarios
    cc0, fr0, ang0 = colocacion_S0(dem, agua, dc, dr, rng)
    d0 = densidad(dem, cc0, fr0)
    (cc1, fr1, ang1), d1 = colocacion_S1(dem, agua, dc, dr, rng, k=K_MEJOR)

    rep = {"semilla": semilla, "theta_grados": math.degrees(theta),
           "S0": {"densidad": d0, "desalineacion_grados": math.degrees(desalineacion(ang0, theta))},
           "S1": {"densidad": d1, "desalineacion_grados": math.degrees(desalineacion(ang1, theta))}}

    # nulo correcto y nulo con agua: la region es el mapa entero, de modo que la
    # misma distribucion nula sirve a los dos escenarios (el p es el rango del
    # observado dentro de ella, y compartirla no rompe nada)
    dens_ok, _, _, _, _ = nulo_rigido(dem, agua, dc, dr, N_NULL, rng)
    dens_ag, _, _, en_agua, frac_celdas = nulo_rigido(dem, agua, dc, dr, N_NULL, rng,
                                                      permitir_agua=True)

    # nulo con recorte: la region depende de la colocacion observada, asi que
    # hay una distribucion por escenario
    reg0 = region_ajustada(cc0, fr0, dem, MARGEN_AJUSTADO)
    reg1 = region_ajustada(cc1, fr1, dem, MARGEN_AJUSTADO)
    dens_m0, _, _, _, _ = nulo_rigido(dem, agua, dc, dr, N_NULL, rng, region=reg0)
    dens_m1, _, _, _, _ = nulo_rigido(dem, agua, dc, dr, N_NULL, rng, region=reg1)

    for esc, d_obs, dens_m, reg in (("S0", d0, dens_m0, reg0), ("S1", d1, dens_m1, reg1)):
        z, p = contraste(d_obs, dens_ok)
        rep[esc]["correcto"] = {"z": z, "p": p}
        z, p = contraste(d_obs, dens_ag)
        rep[esc]["agua"] = {"z": z, "p": p}
        z, p = contraste(d_obs, dens_m)
        rep[esc]["recorte"] = {"z": z, "p": p,
                               "cobertura": cobertura_orientaciones(dem, dc, dr, reg)}

    rep["diagnosticos"] = {
        "agua_nulos_que_pisan": en_agua / N_NULL,
        "agua_fraccion_celdas": frac_celdas,
        "cobertura_region_completa": cobertura_orientaciones(dem, dc, dr),
    }
    return rep


# ------------------------------------------------------------------ estadisticas
def wilson(k, n, zc=1.96):
    """Intervalo de Wilson para una proporcion."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1 + zc * zc / n
    cen = (p + zc * zc / (2 * n)) / den
    rad = zc * math.sqrt(p * (1 - p) / n + zc * zc / (4 * n * n)) / den
    return (max(0.0, cen - rad), min(1.0, cen + rad))


def ks_uniforme(ps):
    """Estadistico KS contra la uniforme y su p asintotico."""
    x = np.sort(np.asarray(ps))
    n = len(x)
    d = float(np.max(np.maximum(np.arange(1, n + 1) / n - x, x - np.arange(0, n) / n)))
    lam = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * d
    p = 2 * sum((-1) ** (j - 1) * math.exp(-2 * (j * lam) ** 2) for j in range(1, 101))
    return d, float(min(max(p, 0.0), 1.0))


def potencia_teorica(k, n_null, alfa, n_mc=200000, semilla=7):
    """Potencia esperada del contraste correcto en S1, por simetria de rangos.

    El observado es el maximo de k sorteos intercambiables con los n_null del
    nulo: la distribucion del rango es conocida y se evalua por Monte Carlo.
    """
    rng = np.random.default_rng(semilla)
    u = rng.random((n_mc, k + n_null))
    obs = u[:, :k].max(axis=1)
    p = (np.sum(u[:, k:] >= obs[:, None], axis=1) + 1) / (n_null + 1)
    return float(np.mean(p <= alfa))


def spearman(a, b):
    """Correlacion de Spearman con p por permutacion (numpy puro)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    rho = float(np.corrcoef(ra, rb)[0, 1])
    rng = np.random.default_rng(11)
    hits = sum(abs(np.corrcoef(rng.permutation(ra), rb)[0, 1]) >= abs(rho)
               for _ in range(10000))
    return rho, (hits + 1) / 10001


def resumen(reps):
    out = {}
    for esc in ("S0", "S1"):
        out[esc] = {}
        for proc in ("correcto", "agua", "recorte"):
            zs = [r[esc][proc]["z"] for r in reps]
            ps = [r[esc][proc]["p"] for r in reps]
            k = sum(1 for p in ps if p <= ALFA)
            lo, hi = wilson(k, len(ps))
            d, pks = ks_uniforme(ps)
            out[esc][proc] = {
                "z_media": float(np.mean(zs)), "z_sd": float(np.std(zs)),
                "rechazo": k / len(ps), "rechazo_ic95": [lo, hi],
                "ks_D": d, "ks_p_uniforme": pks, "n": len(ps),
            }
    # mecanismo del recorte: sesgo apareado frente a desalineacion con el grano
    dz = [r["S0"]["recorte"]["z"] - r["S0"]["correcto"]["z"] for r in reps]
    des = [r["S0"]["desalineacion_grados"] for r in reps]
    rho, p_rho = spearman(des, dz)
    out["mecanismo_recorte"] = {
        "dz_medio": float(np.mean(dz)), "dz_sd": float(np.std(dz)),
        "dz_abs_medio": float(np.mean(np.abs(dz))),
        "spearman_desalineacion": rho, "p_spearman": p_rho,
    }
    out["diagnosticos"] = {
        "agua_nulos_que_pisan_media": float(np.mean(
            [r["diagnosticos"]["agua_nulos_que_pisan"] for r in reps])),
        "agua_fraccion_celdas_media": float(np.mean(
            [r["diagnosticos"]["agua_fraccion_celdas"] for r in reps])),
        "cobertura_completa_media": float(np.mean(
            [r["diagnosticos"]["cobertura_region_completa"] for r in reps])),
        "cobertura_recorte_S0_media": float(np.mean(
            [r["S0"]["recorte"]["cobertura"] for r in reps])),
    }
    out["potencia_teorica_S1_correcto"] = potencia_teorica(K_MEJOR, N_NULL, ALFA)
    return out


def main():
    os.makedirs(RES, exist_ok=True)
    reps = []
    t0 = time.time()
    print("CALIBRACION: %d replicas x 2 escenarios x 3 procedimientos (nulo de %d)"
          % (R_SEMILLAS, N_NULL), flush=True)
    for s in range(R_SEMILLAS):
        reps.append(una_replica(s))
        if (s + 1) % 5 == 0:
            print("  %2d/%d  (%.0f s)" % (s + 1, R_SEMILLAS, time.time() - t0), flush=True)

    res = resumen(reps)
    print("\n%-10s %-10s %8s %8s %10s %12s" %
          ("escenario", "proced.", "z medio", "z sd", "rechazo", "KS p(unif)"))
    for esc in ("S0", "S1"):
        for proc in ("correcto", "agua", "recorte"):
            c = res[esc][proc]
            print("%-10s %-10s %+8.2f %8.2f %9.0f%% %12.4f"
                  % (esc, proc, c["z_media"], c["z_sd"], 100 * c["rechazo"],
                     c["ks_p_uniforme"]))
    print("\npotencia teorica S1 correcto: %.2f" % res["potencia_teorica_S1_correcto"])
    m = res["mecanismo_recorte"]
    print("mecanismo del recorte: dz medio %+.2f (sd %.2f) | rho(desalineacion) %+.2f (p=%.4f)"
          % (m["dz_medio"], m["dz_sd"], m["spearman_desalineacion"], m["p_spearman"]))
    d = res["diagnosticos"]
    print("diagnosticos: nulos que pisan agua %.0f %% | cobertura recorte %.0f %% (completa %.0f %%)"
          % (100 * d["agua_nulos_que_pisan_media"], 100 * d["cobertura_recorte_S0_media"],
             100 * d["cobertura_completa_media"]))

    json.dump({"config": {"replicas": R_SEMILLAS, "n_null": N_NULL, "k_mejor": K_MEJOR,
                          "margen_ajustado_celdas": MARGEN_AJUSTADO, "alfa": ALFA,
                          "semilla_base": SEMILLA_BASE,
                          "n_sitios": N_SITIOS, "pasos_orientacion": PASOS_ORIENTACION},
               "replicas": reps, "resumen": res},
              open(os.path.join(RES, "calibracion.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("\n  -> %s  (%.0f s en total)" % (os.path.join(RES, "calibracion.json"),
                                            time.time() - t0))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Motor de linea de vision con defectos conmutables.

Este modulo cumple dos funciones a la vez, y esa es toda su gracia. Calcula la
linea de vision entre dos celdas de un modelo de elevacion, correctamente. Y
puede calcularla mal, de las maneras concretas en que se calcula mal en la
practica, activando un defecto por su nombre.

Los defectos no son inventados. Los tres primeros aparecieron en un analisis
real de intervisibilidad —doi:10.5281/zenodo.22176260— y ninguno produjo un
fallo visible: los tres devolvian redes de aspecto razonable y estadisticos
interpretables. Se corrigieron por casualidad, no por diseno.

Poder activarlos a voluntad permite lo que de otro modo seria una afirmacion sin
respaldo: medir si un banco de pruebas los detecta. Un banco que no distingue el
motor correcto del averiado no vale nada, por muchos casos que tenga.

DEFECTOS

  curvatura_restada     Resta el termino de curvatura en vez de sumarlo. Vuelve
                        la Tierra concava: a larga distancia ningun relieve
                        bloquea. Es el error de signo mas facil de cometer,
                        porque hablar de «descenso por curvatura» lo sugiere.

  sin_curvatura         Ignora curvatura y refraccion. Defensible por debajo de
                        unos pocos kilometros, desastroso mas alla.

  altura_objetivo_nula  Trata el objetivo como un punto en el suelo. Frecuente
                        cuando la altura se deja al valor por defecto.

  extremos_incluidos    Comprueba el bloqueo tambien en las celdas de los dos
                        extremos, de modo que el propio observador o el propio
                        objetivo se tapan a si mismos. Da falsos negativos en
                        cuanto observador u objetivo estan sobre relieve.

  muestreo_grueso       Muestrea el perfil con pocos puntos fijos en lugar de
                        uno por celda. Se salta barreras estrechas.
"""
import numpy as np

R_EARTH = 6371000.0
K_REFRACTION = 0.13
R_EFF = R_EARTH / (1.0 - K_REFRACTION)

DEFECTOS = (
    "curvatura_restada",
    "sin_curvatura",
    "altura_objetivo_nula",
    "extremos_incluidos",
    "muestreo_grueso",
)


def curvature_rise(d, D, r_eff=R_EFF):
    """Elevacion aparente del terreno intermedio respecto a la cuerda, en metros.

    Trabajando en el plano tangente al observador, el terreno desciende d^2/2R y
    el objetivo D^2/2R. Al reescribir la condicion de bloqueo respecto a la recta
    que une los dos extremos sin corregir, ambos descensos se combinan en
    d(D-d)/2R, que se SUMA al terreno intermedio: visto desde esa cuerda la
    Tierra abulta entre los extremos y el abultamiento se anula en ellos.
    """
    return d * (D - d) / (2.0 * r_eff)


def line_of_sight(dem, res_x, res_y, c0, r0, c1, r1,
                  h_obs=1.7, h_tgt=3.0, defecto=None, return_profile=False):
    """True si hay vision directa entre dos celdas. `defecto` avería el calculo."""
    if defecto is not None and defecto not in DEFECTOS:
        raise ValueError("defecto desconocido: %r" % defecto)

    dx = (c1 - c0) * res_x
    dy = (r1 - r0) * res_y
    D = float(np.hypot(dx, dy))
    if D < 1e-6:
        return (True, None) if return_profile else True

    if defecto == "muestreo_grueso":
        n = 10
    else:
        n = int(max(abs(c1 - c0), abs(r1 - r0))) + 1
    n = max(n, 3)

    t = np.linspace(0.0, 1.0, n)
    cc = np.clip(np.rint(c0 + (c1 - c0) * t).astype(np.int32), 0, dem.shape[1] - 1)
    rr = np.clip(np.rint(r0 + (r1 - r0) * t).astype(np.int32), 0, dem.shape[0] - 1)

    z = dem[rr, cc].astype(np.float64)
    d = t * D

    if defecto == "sin_curvatura":
        z_corr = z.copy()
    elif defecto == "curvatura_restada":
        z_corr = z - curvature_rise(d, D)
    else:
        z_corr = z + curvature_rise(d, D)

    alt_tgt = 0.0 if defecto == "altura_objetivo_nula" else h_tgt
    z_ini = z[0] + h_obs
    z_fin = z[-1] + alt_tgt
    vista = z_ini + (z_fin - z_ini) * t

    if defecto == "extremos_incluidos":
        interior = slice(None)
    else:
        interior = slice(1, -1)

    despejado = bool(np.all(z_corr[interior] <= vista[interior] + 1e-9))
    if return_profile:
        return despejado, {"d": d, "z": z, "z_corr": z_corr, "vista": vista, "D": D}
    return despejado

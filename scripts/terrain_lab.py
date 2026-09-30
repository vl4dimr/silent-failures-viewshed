# -*- coding: utf-8 -*-
"""
Laboratorio de paisajes sinteticos para defectos de diseno del analisis.

El banco de casos y propiedades (suite.py) valida el motor geometrico. Pero dos
de los tres artefactos documentados en el caso real —doi:10.5281/zenodo.22176260—
no estaban en el motor sino en el diseno del contraste: puntos nulos sorteados
sobre el lago, y una region de muestreo recortada que sesgaba las orientaciones
del nulo rigido. Un motor perfecto ejecuta ambos sin protestar.

Para medirlos hace falta otra cosa: un paisaje donde la verdad se conozca por
construccion. Este modulo la fabrica.

LA CONSTRUCCION

El escenario sin efecto (S0) coloca la configuracion de sitios en una posicion
y orientacion sorteadas con las mismas reglas que usa el modelo nulo. Observado
y nulos son entonces intercambiables, y el valor p del contraste es uniforme
POR CONSTRUCCION: no aproximadamente, sino de forma exacta, por simetria. Todo
desvio medido de esa uniformidad es un defecto del procedimiento, no del azar.

El escenario con efecto (S1) coloca la configuracion en la mejor de K
colocaciones sorteadas: literalmente «situada donde ve mas de lo que veria la
misma configuracion en otro punto», que es la hipotesis que el nulo rigido
contrasta. La potencia teorica del contraste tambien se conoce por simetria
(el maximo de K sorteos frente a N sorteos frescos), asi que la potencia
medida puede compararse con la esperada, no solo consigo misma.

Sobre esa base se inyectan los dos defectos de diseno:

  permitir_agua     el nulo sortea tambien sobre el lago, que en un modelo de
                    elevacion es un plano perfecto que no bloquea nada
  region ajustada   la region de muestreo del nulo se recorta al contorno de lo
                    observado mas un margen escaso, y las orientaciones que no
                    caben quedan excluidas

Y se calculan los dos diagnosticos que los delatan sin conocer la verdad:
la fraccion de colocaciones nulas que pisan agua, y la cobertura de
orientaciones de la region de muestreo.

El terreno es anisotropo a proposito —crestas con una direccion dominante—
porque el sesgo de orientacion solo muerde cuando el terreno tiene grano. La
direccion del grano se sortea en cada replica y se registra: permite medir como
el sesgo depende del angulo entre la configuracion y el terreno, que es
justamente lo que un analista no puede conocer a priori.
"""
import math

import numpy as np

from los_engine import line_of_sight

RES = 30.0          # tamano de celda, m
MARGEN_BORDE = 5    # celdas de resguardo en el borde del mapa
N_SITIOS = 32       # sitios de la nube sintetica (forma_alargada)
PASOS_ORIENTACION = 360  # orientaciones que prueba el diagnostico D2, una por grado


# ------------------------------------------------------------------- el paisaje
def _gauss_suave(campo, sigma):
    """Suavizado gaussiano por FFT, sin dependencias fuera de numpy."""
    n0, n1 = campo.shape
    fy = np.fft.fftfreq(n0)[:, None]
    fx = np.fft.fftfreq(n1)[None, :]
    g = np.exp(-2.0 * (math.pi ** 2) * (sigma ** 2) * (fy ** 2 + fx ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(campo) * g))


def paisaje(n=380, semilla=0, cota=3800.0, con_lago=True):
    """Terreno sintetico con grano direccional y, opcionalmente, un lago.

    Devuelve (dem, agua, theta): el modelo de elevacion, la mascara de agua y la
    direccion dominante de las crestas. El lago se construye como lo construye
    un modelo de elevacion real: inundando las cotas bajas de una cuenca y
    asignandoles una cota constante. Un plano perfecto que no proyecta sombra
    ni bloquea vista alguna, igual que el Titicaca en el Copernicus DEM.
    """
    rng = np.random.default_rng(semilla)
    y, x = np.mgrid[0:n, 0:n].astype(np.float64)

    # crestas con direccion dominante theta
    theta = float(rng.uniform(0, math.pi))
    u = x * math.cos(theta) + y * math.sin(theta)
    relieve = 45.0 * np.sin(2 * math.pi * u / rng.uniform(45, 75) + rng.uniform(0, 2 * math.pi))

    # colinas anchas que rompen la periodicidad pura
    for _ in range(5):
        cx, cy = rng.uniform(0, n, 2)
        s = rng.uniform(35, 90)
        relieve += rng.normal(0, 35) * np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (2 * s * s)))

    # rugosidad fina
    relieve += _gauss_suave(rng.normal(0, 1, (n, n)), 2.5) * 18.0

    # cuenca lacustre en un flanco. Debe ser bastante mas honda que la amplitud
    # de las crestas: si no, el 25 % inundado se reparte por todos los valles y
    # el «lago» queda hecho jirones en vez de ser un cuerpo con ribera, que es
    # la geografia del caso real.
    bx, by = ((0.10 * n, 0.85 * n) if rng.uniform() < 0.5 else (0.90 * n, 0.15 * n))
    relieve -= 200.0 * np.exp(-(((x - bx) ** 2 + (y - by) ** 2) / (2 * (0.42 * n) ** 2)))

    dem = (cota + relieve).astype(np.float32)
    agua = np.zeros(dem.shape, dtype=bool)
    if con_lago:
        cota_agua = float(np.percentile(dem, 24))
        agua = dem <= cota_agua
        dem = dem.copy()
        dem[agua] = cota_agua
    return dem, agua, theta


# ------------------------------------------------------- configuracion de sitios
def forma_alargada(rng, n_sitios=N_SITIOS, largo=250.0, ancho=18.0):
    """Nube de sitios alargada, en celdas, centrada en su media.

    La elongacion no es un capricho: los conjuntos reales siguen corredores del
    paisaje —una ribera, un valle— y es exactamente esa forma la que hace que
    una region de muestreo ajustada excluya orientaciones.
    """
    dc = rng.uniform(-largo / 2, largo / 2, n_sitios)
    dr = rng.uniform(-ancho / 2, ancho / 2, n_sitios)
    return dc - dc.mean(), dr - dr.mean()


def _gira(dc, dr, ang):
    c, s = math.cos(ang), math.sin(ang)
    return dc * c - dr * s, dc * s + dr * c


def region_completa(dem):
    h, w = dem.shape
    return (MARGEN_BORDE, h - 1 - MARGEN_BORDE, MARGEN_BORDE, w - 1 - MARGEN_BORDE)


def region_ajustada(cols, fils, dem, margen=25):
    """El defecto de recorte: contorno de lo observado mas un margen escaso."""
    rmin, rmax, cmin, cmax = region_completa(dem)
    return (max(rmin, int(fils.min()) - margen), min(rmax, int(fils.max()) + margen),
            max(cmin, int(cols.min()) - margen), min(cmax, int(cols.max()) + margen))


def intento_colocacion(dem, agua, dc, dr, rng, region=None, permitir_agua=False):
    """Un sorteo de orientacion y traslacion. None si no cabe o pisa agua."""
    rmin, rmax, cmin, cmax = region if region is not None else region_completa(dem)
    ang = float(rng.uniform(0, 2 * math.pi))
    rc, rr = _gira(dc, dr, ang)
    lo_c, hi_c = cmin - rc.min(), cmax - rc.max()
    lo_r, hi_r = rmin - rr.min(), rmax - rr.max()
    if lo_c >= hi_c or lo_r >= hi_r:
        return None
    cc = np.rint(rc + rng.uniform(lo_c, hi_c)).astype(int)
    fr = np.rint(rr + rng.uniform(lo_r, hi_r)).astype(int)
    if not permitir_agua and agua[fr, cc].any():
        return None
    return cc, fr, ang


# ------------------------------------------------------------------ el contraste
def densidad(dem, cols, fils):
    """Densidad de intervisibilidad de la red completa de pares."""
    n = len(cols)
    aristas, pares = 0, 0
    for i in range(n):
        for j in range(i + 1, n):
            pares += 1
            aristas += line_of_sight(dem, RES, RES, int(cols[i]), int(fils[i]),
                                     int(cols[j]), int(fils[j]))
    return aristas / pares


def nulo_rigido(dem, agua, dc, dr, n_null, rng, region=None, permitir_agua=False):
    """Distribucion nula por traslacion y rotacion rigidas.

    Devuelve (densidades, angulos aceptados, intentos, colocaciones que pisan
    agua, fraccion media de celdas sobre agua). Las dos ultimas son el
    diagnostico D1: en un nulo bien disenado valen cero.
    """
    dens, angs = [], []
    en_agua, celdas_agua = 0, 0.0
    intentos = 0
    while len(dens) < n_null and intentos < n_null * 500:
        intentos += 1
        col = intento_colocacion(dem, agua, dc, dr, rng, region, permitir_agua)
        if col is None:
            continue
        cc, fr, ang = col
        pisa = int(agua[fr, cc].sum())
        if pisa:
            en_agua += 1
            celdas_agua += pisa / len(cc)
        dens.append(densidad(dem, cc, fr))
        angs.append(ang)
    n = len(dens)
    return (np.array(dens), np.array(angs), intentos, en_agua,
            (celdas_agua / n if n else 0.0))


def contraste(d_obs, dens_nulas):
    """z y p unilateral contra la distribucion nula, como en el caso real."""
    p = float((np.sum(dens_nulas >= d_obs) + 1) / (len(dens_nulas) + 1))
    sd = float(dens_nulas.std())
    z = float((d_obs - dens_nulas.mean()) / sd) if sd > 0 else float("nan")
    return z, p


# ------------------------------------------------------------------ diagnosticos
def cobertura_orientaciones(dem, dc, dr, region=None, pasos=PASOS_ORIENTACION):
    """Diagnostico D2: fraccion de orientaciones que caben en la region.

    Es geometria pura y cuesta nada. En el caso real habria marcado 244/360
    antes de calcular una sola linea de vision.
    """
    rmin, rmax, cmin, cmax = region if region is not None else region_completa(dem)
    caben = 0
    for k in range(pasos):
        rc, rr = _gira(dc, dr, 2 * math.pi * k / pasos)
        if (cmin - rc.min() < cmax - rc.max()) and (rmin - rr.min() < rmax - rr.max()):
            caben += 1
    return caben / pasos


# ------------------------------------------------------------------- escenarios
def colocacion_S0(dem, agua, dc, dr, rng):
    """Sin efecto: una colocacion sorteada con las reglas del nulo.

    La intercambiabilidad con los sorteos nulos es lo que hace exacto el
    escenario: el p del contraste correcto es uniforme por simetria.
    """
    while True:
        col = intento_colocacion(dem, agua, dc, dr, rng)
        if col is not None:
            return col


def colocacion_S1(dem, agua, dc, dr, rng, k=40):
    """Con efecto: la mejor de k colocaciones sorteadas.

    «Situada donde ve mas de lo que veria la misma configuracion en otro punto
    del territorio», por construccion. La potencia esperada del contraste se
    conoce por simetria de rangos y se calcula en la fase de estadisticas.
    """
    mejor, mejor_d = None, -1.0
    hechos = 0
    while hechos < k:
        col = intento_colocacion(dem, agua, dc, dr, rng)
        if col is None:
            continue
        d = densidad(dem, col[0], col[1])
        hechos += 1
        if d > mejor_d:
            mejor, mejor_d = col, d
    return mejor, mejor_d


def desalineacion(ang, theta):
    """Angulo entre el eje de la nube y el grano del terreno, en [0, pi/2].

    El eje largo de la nube es invariante bajo giros de pi, y el grano tambien:
    lo que importa es cuanto se cruzan.
    """
    d = abs((ang - theta) % math.pi)
    return min(d, math.pi - d)


# ------------------------------------------------------------------- smoke test
if __name__ == "__main__":
    import time

    t0 = time.time()
    dem, agua, theta = paisaje(semilla=1)
    print("paisaje %s | agua %.1f %% | grano %.0f grados | %.2f s"
          % (dem.shape, 100 * agua.mean(), math.degrees(theta), time.time() - t0))

    rng = np.random.default_rng(99)
    dc, dr = forma_alargada(rng)

    t0 = time.time()
    cc, fr, ang = colocacion_S0(dem, agua, dc, dr, rng)
    d0 = densidad(dem, cc, fr)
    print("S0: densidad %.4f | una densidad tarda %.0f ms"
          % (d0, 1000 * (time.time() - t0)))

    t0 = time.time()
    (cc1, fr1, ang1), d1 = colocacion_S1(dem, agua, dc, dr, rng, k=10)
    print("S1 (k=10): mejor densidad %.4f | %.1f s" % (d1, time.time() - t0))

    t0 = time.time()
    dens, angs, intentos, ea, fa = nulo_rigido(dem, agua, dc, dr, 20, rng)
    z, p = contraste(d0, dens)
    print("nulo x20: %.1f s | S0 z=%+.2f p=%.2f | pisan agua %d" % (time.time() - t0, z, p, ea))

    cob_full = cobertura_orientaciones(dem, dc, dr)
    cob_tight = cobertura_orientaciones(dem, dc, dr, region_ajustada(cc, fr, dem))
    print("cobertura de orientaciones: completa %.2f | ajustada %.2f" % (cob_full, cob_tight))

# -*- coding: utf-8 -*-
"""
Banco de pruebas de terrenos sinteticos de respuesta conocida.

Un algoritmo de visibilidad falla en silencio. Sobre terreno real no hay forma
de saber si acierta: devuelve un mapa plausible tanto si el criterio geometrico
es correcto como si no. La unica manera de comprobarlo es preguntarle por
terrenos cuya respuesta se conoce de antemano.

El banco tiene dos partes, y la segunda es la que importa.

CASOS. Terrenos construidos donde la respuesta se deduce a mano: un plano, una
barrera que debe tapar, la misma rebajada que no debe, una depresion que no
puede tapar nada. Son necesarios y son debiles: un motor averiado puede pasarlos
por casualidad si los casos no tocan justo lo que rompio.

PROPIEDADES. Invariantes que la visibilidad cumple sobre cualquier terreno, y
que se comprueban sobre terrenos aleatorios. Que la vision sea reciproca. Que
subir el observador nunca quite vision. Que sobre un plano la vision se pierda
al alejarse y no se recupere. Un motor averiado no las pasa por casualidad,
porque no hay un caso concreto al que ajustarse: hay que estar bien.

Las cotas de curvatura no se escriben a mano, se derivan. Sobre un plano, la
vista se pierde cuando el abultamiento en el punto medio, D^2/(8*R_ef), supera
la altura media de la linea, (h_obs+h_tgt)/2. Eso da una distancia critica
exacta contra la que probar por ambos lados.
"""
import math

import numpy as np

from los_engine import R_EFF, line_of_sight

RES = 30.0  # tamano de celda, m


# --------------------------------------------------------------------- terrenos
def plano(n=1400, cota=3800.0):
    return np.full((3, n), cota, dtype=np.float32)


def con_barrera(n=400, cota=3800.0, altura=50.0, col=None, ancho=1):
    dem = np.full((3, n), cota, dtype=np.float32)
    col = n // 2 if col is None else col
    dem[:, col:col + ancho] = cota + altura
    return dem


def con_depresion(n=400, cota=3800.0, hondura=80.0):
    dem = np.full((3, n), cota, dtype=np.float32)
    dem[:, n // 2 - 5:n // 2 + 5] = cota - hondura
    return dem


def con_cima_en(n, col, cota=3800.0, altura=40.0):
    dem = np.full((3, n), cota, dtype=np.float32)
    dem[:, col] = cota + altura
    return dem


def rugoso(n=300, cota=3800.0, amplitud=60.0, semilla=0):
    rng = np.random.default_rng(semilla)
    perfil = rng.normal(0, amplitud, n).cumsum()
    perfil -= perfil.mean()
    return np.tile((cota + perfil).astype(np.float32), (3, 1))


def distancia_critica(h_obs, h_tgt):
    """Distancia sobre plano a la que la curvatura corta la vista. Exacta."""
    return math.sqrt(8.0 * R_EFF * (h_obs + h_tgt) / 2.0)


# ----------------------------------------------------------------------- casos
def casos():
    """Cada entrada: (nombre, funcion(defecto) -> bool_obtenido, esperado)."""
    C = []

    def add(nombre, fn, esperado):
        C.append((nombre, fn, esperado))

    # -- geometria basica
    add("plano a 3 km: se ve",
        lambda d: line_of_sight(plano(), RES, RES, 0, 1, 100, 1, defecto=d), True)

    add("barrera de 50 m a media distancia: tapa",
        lambda d: line_of_sight(con_barrera(altura=50.0), RES, RES, 0, 1, 399, 1, defecto=d), False)

    # Estos dos deben medirse por debajo de la distancia critica (11.7 km con las
    # alturas por defecto). Mas alla, el plano ya esta tapado por la curvatura y
    # el rasgo que se quiere probar no decide nada: la prueba mediria otra cosa.
    # Se escribieron primero a 12 km y fallaban por eso, no por el motor.
    add("barrera rebajada a 1 m a 3 km: no tapa",
        lambda d: line_of_sight(con_barrera(n=100, altura=1.0), RES, RES, 0, 1, 99, 1,
                                defecto=d), True)

    add("depresion a 3 km: nunca tapa",
        lambda d: line_of_sight(con_depresion(n=100), RES, RES, 0, 1, 99, 1, defecto=d), True)

    # La curvatura y el relieve se suman: la misma barrera decide o no segun la
    # distancia. Es la interaccion que hace facil equivocar una expectativa.
    add("barrera de 2 m: no tapa a 3 km",
        lambda d: line_of_sight(con_barrera(n=100, altura=2.0), RES, RES, 0, 1, 99, 1,
                                defecto=d), True)
    add("la misma barrera de 2 m si tapa a 12 km",
        lambda d: line_of_sight(con_barrera(n=400, altura=2.0), RES, RES, 0, 1, 399, 1,
                                defecto=d), False)

    # Tambien a 3 km, y por el mismo motivo: a 12 km la curvatura tapaba sola y
    # la prueba pasaba sin llegar a mirar la barrera. Un caso puede aprobar por
    # la razon equivocada, y entonces no prueba lo que dice su nombre.
    add("barrera de una sola celda a 3 km: tapa igual",
        lambda d: line_of_sight(con_barrera(n=100, altura=80.0, ancho=1), RES, RES, 0, 1, 99, 1,
                                defecto=d), False)

    # -- alturas
    add("objetivo a ras de suelo tras loma de 12 m: no se ve",
        lambda d: line_of_sight(con_barrera(altura=12.0), RES, RES, 0, 1, 399, 1,
                                h_obs=1.7, h_tgt=0.0, defecto=d), False)

    add("mismo caso con objetivo de 30 m: se ve",
        lambda d: line_of_sight(con_barrera(altura=12.0), RES, RES, 0, 1, 399, 1,
                                h_obs=1.7, h_tgt=30.0, defecto=d), True)

    # -- extremos: el propio relieve del observador no debe taparle
    add("observador sobre una cima: no se tapa a si mismo",
        lambda d: line_of_sight(con_cima_en(400, 0), RES, RES, 0, 1, 399, 1, defecto=d), True)

    add("objetivo sobre una cima: sigue viendose",
        lambda d: line_of_sight(con_cima_en(400, 399), RES, RES, 0, 1, 399, 1, defecto=d), True)

    # -- curvatura, con la cota derivada y no escrita a mano
    dc = distancia_critica(1.7, 3.0)
    n_corto = int(dc * 0.75 / RES)
    n_largo = int(dc * 1.6 / RES)
    add("plano justo por debajo de la distancia critica (%.1f km): se ve" % (dc * 0.75 / 1000),
        lambda d: line_of_sight(plano(n_corto + 2), RES, RES, 0, 1, n_corto, 1, defecto=d), True)
    add("plano bien por encima de la critica (%.1f km): la curvatura tapa" % (dc * 1.6 / 1000),
        lambda d: line_of_sight(plano(n_largo + 2), RES, RES, 0, 1, n_largo, 1, defecto=d), False)

    n_40 = int(40000 / RES)
    add("plano a 40 km: mas alla del horizonte geometrico",
        lambda d: line_of_sight(plano(n_40 + 2), RES, RES, 0, 1, n_40, 1, defecto=d), False)

    add("plano a 1 km: la curvatura no cambia nada",
        lambda d: line_of_sight(plano(40), RES, RES, 0, 1, 33, 1, defecto=d), True)

    return C


# ------------------------------------------------------------------ propiedades
def propiedades():
    """Invariantes comprobados sobre terrenos aleatorios.

    Devuelve (nombre, funcion(defecto) -> (n_violaciones, n_pruebas)).
    """
    P = []

    def reciprocidad(defecto):
        """A ve a B si y solo si B ve a A. La geometria no tiene sentido de marcha."""
        fallos = n = 0
        for s in range(40):
            dem = rugoso(300, semilla=s)
            for c0, c1 in ((0, 299), (10, 250), (40, 180), (5, 120)):
                ida = line_of_sight(dem, RES, RES, c0, 1, c1, 1, h_obs=1.7, h_tgt=1.7, defecto=defecto)
                vta = line_of_sight(dem, RES, RES, c1, 1, c0, 1, h_obs=1.7, h_tgt=1.7, defecto=defecto)
                n += 1
                fallos += int(ida != vta)
        return fallos, n

    def monotonia_altura(defecto):
        """Subir el observador nunca puede quitar vision que ya se tenia."""
        fallos = n = 0
        for s in range(40):
            dem = rugoso(300, semilla=100 + s)
            for h in (0.0, 2.0, 5.0, 10.0):
                bajo = line_of_sight(dem, RES, RES, 0, 1, 299, 1, h_obs=h, h_tgt=3.0, defecto=defecto)
                alto = line_of_sight(dem, RES, RES, 0, 1, 299, 1, h_obs=h + 25.0, h_tgt=3.0,
                                     defecto=defecto)
                n += 1
                fallos += int(bajo and not alto)
        return fallos, n

    def monotonia_distancia(defecto):
        """Sobre un plano, una vez perdida la vista por curvatura no se recupera."""
        fallos = n = 0
        dc = distancia_critica(1.7, 3.0)
        cols = [int(dc * f / RES) for f in (0.5, 0.8, 1.0, 1.3, 1.8, 2.5)]
        dem = plano(max(cols) + 3)
        visto_antes = True
        for c in cols:
            v = line_of_sight(dem, RES, RES, 0, 1, c, 1, defecto=defecto)
            n += 1
            if v and not visto_antes:
                fallos += 1
            visto_antes = v
        return fallos, n

    def barrera_creciente(defecto):
        """Subir una barrera nunca puede destapar lo que ya tapaba."""
        fallos = n = 0
        tapaba = False
        for altura in (0.0, 5.0, 12.0, 25.0, 60.0, 150.0, 400.0):
            v = line_of_sight(con_barrera(altura=altura), RES, RES, 0, 1, 399, 1, defecto=defecto)
            n += 1
            if tapaba and v:
                fallos += 1
            tapaba = not v
        return fallos, n

    P.append(("reciprocidad de la vision", reciprocidad))
    P.append(("monotonia en la altura del observador", monotonia_altura))
    P.append(("monotonia en la distancia sobre plano", monotonia_distancia))
    P.append(("monotonia en la altura de la barrera", barrera_creciente))
    return P

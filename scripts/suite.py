# -*- coding: utf-8 -*-
"""
Banco de pruebas de terrenos sinteticos de respuesta conocida.

Un algoritmo de visibilidad falla en silencio. Sobre terreno real no hay forma
de saber si acierta: devuelve un mapa plausible tanto si el criterio geometrico
es correcto como si no. La unica manera de comprobarlo es preguntarle por
terrenos cuya respuesta se conoce de antemano.

El banco tiene dos partes.

CASOS. Terrenos construidos donde la respuesta se deduce: un plano, una barrera
que debe tapar, la misma rebajada que no debe, una depresion que no puede tapar
nada. Cada caso declara el rasgo que dice probar y de que tipo es:

  rasgo     el rasgo decide el veredicto: si se retira (barrera a 0 m, objetivo
            a 0 m, curvatura apagada) el veredicto tiene que cambiar. Si no
            cambia, el caso aprueba por la razon equivocada —tipicamente porque
            la curvatura tapa sola— y no prueba lo que dice su nombre.
  control   el rasgo esta presente y NO debe decidir: el caso afirma que no
            tapa (una barrera de 1 m, una depresion, el relieve bajo el propio
            observador). Retirarlo no puede cambiar nada.

Esa comprobacion se ejecuta mecanicamente (comprobar_rasgo) y su resultado va
al JSON: es una mutacion de la entrada, y el banco se la aplica a si mismo.
Tres casos de la primera version estaban a 12 km, por encima de la distancia
critica, y pasaban por curvatura; se han bajado a donde el rasgo decide.

PROPIEDADES. Relaciones que la visibilidad cumple sobre cualquier terreno y
que se comprueban sobre terrenos aleatorios de semilla fija. Las cuatro de la
primera version (reciprocidad con alturas iguales y tres monotonias) son
condiciones necesarias que ningun mutante rompe: todo motor simetrico en
d <-> D-d y monotono en las alturas las cumple, averiado o no. Se conservan en
propiedades_v1() para que el hallazgo sea reproducible. Las vigentes se
disenaron para discriminar:

  reciprocidad con alturas intercambiadas   LOS(a->b; ho, ht) == LOS(b->a; ht, ho)
  obstaculo dominante en cualquier celda    subir una celda interior nunca
                                            destapa, y por encima de todo el
                                            terreno siempre tapa
  distancia critica derivada sobre plano    se ve al 90 %, se pierde al 110 %
                                            y no se recupera al 150 %
  alturas: monotonia y existencia           subir observador u objetivo nunca
                                            quita vista, y subiendolos lo
                                            bastante siempre se ve

Las cotas de curvatura no se escriben a mano, se derivan. Sobre un plano la
recta que une los dos extremos es tangente a la parabola d(D-d)/2R cuando
D = sqrt(2R h_obs) + sqrt(2R h_tgt): la suma de las dos distancias al
horizonte. La forma sqrt(8R (h_obs+h_tgt)/2) que uso la primera version solo
coincide con alturas iguales; con 1.7 y 3.0 m sobrestima 115 m, y con el
objetivo a ras de suelo, 2 km. Se conserva como distancia_critica_aprox para
dejar constancia.
"""
import math

import numpy as np

from los_engine import R_EFF, curvature_rise, line_of_sight

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


def terrenos_aleatorios(k, semilla, n=300):
    """k terrenos de semilla fija con amplitud variada: de llanuras onduladas de
    unos metros a sierras de cientos. Las propiedades deben cumplirse en todos,
    y solo en los suaves se ven las alturas de observador y objetivo."""
    rng = np.random.default_rng(semilla)
    out = []
    for _ in range(k):
        amplitud = float(10.0 ** rng.uniform(-0.5, 1.8))      # 0.3 .. 60 m por celda
        out.append(rugoso(n, amplitud=amplitud, semilla=int(rng.integers(1 << 30))))
    return out


def distancia_critica(h_obs, h_tgt, r_eff=R_EFF):
    """Distancia sobre plano a la que la curvatura corta la vista. Exacta.

    Es la suma de las dos distancias al horizonte: la recta entre los extremos
    es tangente al abultamiento d(D-d)/2R justo en D = sqrt(2R ho) + sqrt(2R ht).
    """
    return math.sqrt(2.0 * r_eff * h_obs) + math.sqrt(2.0 * r_eff * h_tgt)


def distancia_critica_aprox(h_obs, h_tgt, r_eff=R_EFF):
    """La formula de la primera version: abultamiento en el punto medio igual a
    la altura media de la linea. Solo es exacta con h_obs == h_tgt; en el resto
    sobrestima (por concavidad de la raiz). Se conserva como registro."""
    return math.sqrt(8.0 * r_eff * (h_obs + h_tgt) / 2.0)


# ----------------------------------------------------------------------- casos
def _caso(nombre, esperado, tipo, rasgo, sin_rasgo, terreno, n, c1,
          h_obs=1.7, h_tgt=3.0, **geom):
    """Un caso: observador en la columna 0, objetivo en c1, fila central.

    sin_rasgo dice como retirar el rasgo: 'altura' u 'hondura' lo ponen a cero,
    'h_tgt' baja el objetivo al suelo, 'curvatura' apaga el termino de curvatura
    en el motor correcto.
    """
    assert tipo in ("rasgo", "control")
    assert sin_rasgo in ("altura", "hondura", "h_tgt", "curvatura")
    return dict(nombre=nombre, esperado=esperado, tipo=tipo, rasgo=rasgo,
                sin_rasgo=sin_rasgo, terreno=terreno, n=n, c0=0, c1=c1,
                h_obs=h_obs, h_tgt=h_tgt, geom=geom)


def dem_del_caso(c, sin_rasgo=False):
    g = dict(c["geom"])
    if sin_rasgo and c["sin_rasgo"] in ("altura", "hondura"):
        g[c["sin_rasgo"]] = 0.0
    t = c["terreno"]
    if t == "plano":
        return plano(c["n"])
    if t == "barrera":
        return con_barrera(c["n"], altura=g["altura"], col=g.get("col"),
                           ancho=g.get("ancho", 1))
    if t == "depresion":
        return con_depresion(c["n"], hondura=g["hondura"])
    if t == "cima":
        return con_cima_en(c["n"], g["col"], altura=g["altura"])
    raise ValueError(t)


def geometria(c):
    """(dem, res, c0, r0, c1, r1, h_obs, h_tgt): lo que un motor externo necesita."""
    return dem_del_caso(c), RES, c["c0"], 1, c["c1"], 1, c["h_obs"], c["h_tgt"]


def evaluar_caso(c, defecto=None, sin_rasgo=False):
    dem = dem_del_caso(c, sin_rasgo)
    h_tgt = 0.0 if (sin_rasgo and c["sin_rasgo"] == "h_tgt") else c["h_tgt"]
    if sin_rasgo and c["sin_rasgo"] == "curvatura":
        assert defecto is None
        defecto = "sin_curvatura"       # el motor correcto sin el termino
    return line_of_sight(dem, RES, RES, c["c0"], 1, c["c1"], 1,
                         h_obs=c["h_obs"], h_tgt=h_tgt, defecto=defecto)


def comprobar_rasgo(c):
    """¿Decide el rasgo? Se ejecuta el caso con el rasgo retirado.

    En un caso de tipo 'rasgo' el veredicto tiene que cambiar; en un 'control'
    no puede cambiar. Cualquier otra cosa es un caso que prueba lo que no dice.
    """
    con = bool(evaluar_caso(c))
    sin = bool(evaluar_caso(c, sin_rasgo=True))
    decide = con != sin
    if c["tipo"] == "rasgo":
        ok = decide and con == c["esperado"]
    else:
        ok = (not decide) and con == c["esperado"]
    return dict(veredicto_con_rasgo=con, veredicto_sin_rasgo=sin,
                rasgo_decide=decide, comprobacion_rasgo_ok=ok)


def descripcion_geometrica(c):
    """La geometria del caso en numeros, para tabularla sin teclear."""
    D = (c["c1"] - c["c0"]) * RES
    g = c["geom"]
    if c["terreno"] == "plano":
        altura, ancho, pos = 0.0, 0, None
    elif c["terreno"] == "depresion":
        altura, ancho, pos = -g["hondura"], 10, (c["n"] // 2 - 5) * RES
    else:
        altura, ancho = g["altura"], g.get("ancho", 1)
        pos = (c["n"] // 2 if g.get("col") is None else g["col"]) * RES
    return dict(tipo=c["tipo"], rasgo=c["rasgo"], terreno=c["terreno"],
                distancia_km=D / 1000.0, celdas=c["c1"] - c["c0"],
                h_obs=c["h_obs"], h_tgt=c["h_tgt"],
                altura_rasgo_m=altura, ancho_rasgo_celdas=ancho,
                posicion_rasgo_km=(None if pos is None else pos / 1000.0),
                abultamiento_medio_m=curvature_rise(D / 2.0, D),
                altura_linea_medio_m=(c["h_obs"] + c["h_tgt"]) / 2.0,
                distancia_critica_km=distancia_critica(c["h_obs"], c["h_tgt"]) / 1000.0)


def casos_detallados():
    """Los 15 casos con su geometria y su rasgo declarado."""
    C = []
    dc = distancia_critica(1.7, 3.0)

    # -- geometria basica. La barrera de 50 m estaba a 12 km, donde la curvatura
    #    tapa sola con estas alturas; a 6 km el abultamiento es de 0.6 m y decide
    #    la barrera.
    C.append(_caso("plano a 3 km: se ve", True, "control", "curvatura a 3 km",
                   "curvatura", "plano", 102, 100))
    C.append(_caso("barrera de 50 m a 6 km: tapa", False, "rasgo", "barrera de 50 m",
                   "altura", "barrera", 200, 199, altura=50.0, col=100, ancho=1))
    C.append(_caso("barrera rebajada a 1 m a 3 km: no tapa", True, "control",
                   "barrera de 1 m", "altura", "barrera", 100, 99, altura=1.0, col=50, ancho=1))
    C.append(_caso("depresion a 3 km: nunca tapa", True, "control", "depresion de 80 m",
                   "hondura", "depresion", 100, 99, hondura=80.0))

    # -- curvatura y relieve se suman: la misma barrera decide o no segun la
    #    distancia. A 12 km la curvatura tapaba sola (la prueba no miraba la
    #    barrera); a 9 km el abultamiento es de 1.4 m y los 2 m de barrera
    #    encima de el son lo que corta la linea, que va a 2.35 m.
    C.append(_caso("barrera de 2 m: no tapa a 3 km", True, "control", "barrera de 2 m",
                   "altura", "barrera", 100, 99, altura=2.0, col=50, ancho=1))
    C.append(_caso("la misma barrera de 2 m si tapa a 9 km", False, "rasgo", "barrera de 2 m",
                   "altura", "barrera", 300, 299, altura=2.0, col=150, ancho=1))
    C.append(_caso("barrera de una sola celda a 3 km: tapa igual", False, "rasgo",
                   "barrera de 80 m y una celda", "altura", "barrera", 100, 99,
                   altura=80.0, col=50, ancho=1))

    # -- alturas. Con el objetivo a ras de suelo la distancia critica es de
    #    5.0 km (el horizonte del observador); a 12 km la loma no decidia nada.
    C.append(_caso("objetivo a ras de suelo tras loma de 12 m a 4 km: no se ve", False,
                   "rasgo", "loma de 12 m", "altura", "barrera", 134, 133,
                   h_obs=1.7, h_tgt=0.0, altura=12.0, col=67, ancho=1))
    C.append(_caso("mismo caso con objetivo de 30 m: se ve", True, "rasgo",
                   "objetivo de 30 m", "h_tgt", "barrera", 134, 133,
                   h_obs=1.7, h_tgt=30.0, altura=12.0, col=67, ancho=1))

    # -- extremos: el relieve bajo el propio observador u objetivo no tapa. Son
    #    controles: a 6 km el plano se ve, y la cima no puede cambiarlo.
    C.append(_caso("observador sobre una cima: no se tapa a si mismo", True, "control",
                   "cima de 40 m bajo el observador", "altura", "cima", 200, 199,
                   col=0, altura=40.0))
    C.append(_caso("objetivo sobre una cima: sigue viendose", True, "control",
                   "cima de 40 m bajo el objetivo", "altura", "cima", 200, 199,
                   col=199, altura=40.0))

    # -- curvatura, con la cota derivada y no escrita a mano
    n_corto = int(dc * 0.75 / RES)
    n_largo = int(dc * 1.6 / RES)
    C.append(_caso("plano justo por debajo de la distancia critica (%.1f km): se ve"
                   % (n_corto * RES / 1000), True, "control",
                   "curvatura por debajo de la distancia critica", "curvatura",
                   "plano", n_corto + 2, n_corto))
    C.append(_caso("plano bien por encima de la critica (%.1f km): la curvatura tapa"
                   % (n_largo * RES / 1000), False, "rasgo",
                   "curvatura por encima de la distancia critica", "curvatura",
                   "plano", n_largo + 2, n_largo))
    n_40 = int(40000 / RES)
    C.append(_caso("plano a 40 km: mas alla del horizonte geometrico", False, "rasgo",
                   "curvatura a 40 km", "curvatura", "plano", n_40 + 2, n_40))
    C.append(_caso("plano a 1 km: la curvatura no cambia nada", True, "control",
                   "curvatura a 1 km", "curvatura", "plano", 40, 33))
    return C


def casos():
    """Cada entrada: (nombre, funcion(defecto) -> bool_obtenido, esperado)."""
    return [(c["nombre"], (lambda d, c=c: evaluar_caso(c, d)), c["esperado"])
            for c in casos_detallados()]


# ------------------------------------------------------------------ propiedades
def propiedades():
    """Invariantes comprobados sobre terrenos aleatorios de semilla fija.

    Devuelve (nombre, funcion(defecto) -> (n_violaciones, n_pruebas)).
    """
    P = []

    def reciprocidad_alturas(defecto):
        """A con ho ve a B con ht si y solo si B con ho' = ht ve a A con ht' = ho.

        La geometria no tiene sentido de marcha, pero la linea si depende de que
        altura va en cada extremo: intercambiarlas junto con el sentido deja la
        misma recta. Un motor que ignore una de las dos alturas rompe esto.
        """
        fallos = n = 0
        for dem in terrenos_aleatorios(40, 11):
            for c0, c1 in ((0, 299), (10, 250), (40, 180), (5, 120)):
                for ho, ht in ((1.7, 3.0), (0.0, 10.0), (2.0, 40.0)):
                    ida = line_of_sight(dem, RES, RES, c0, 1, c1, 1, h_obs=ho, h_tgt=ht,
                                        defecto=defecto)
                    vta = line_of_sight(dem, RES, RES, c1, 1, c0, 1, h_obs=ht, h_tgt=ho,
                                        defecto=defecto)
                    n += 1
                    fallos += int(ida != vta)
        return fallos, n

    def obstaculo_dominante(defecto):
        """Subir una celda interior nunca destapa; y una celda que sobresale
        1000 m por encima de todo el terreno tapa, este donde este.

        La segunda mitad es la que discrimina: un motor que muestrea el perfil
        con pocos puntos fijos no ve el obstaculo si cae entre dos muestras.
        """
        fallos = n = 0
        rng = np.random.default_rng(23)
        for dem in terrenos_aleatorios(40, 12):
            for _ in range(3):
                while True:
                    c0, c1 = sorted(int(x) for x in rng.integers(0, 300, 2))
                    if c1 - c0 >= 20:
                        break
                m = int(rng.integers(c0 + 1, c1))
                cotas = [dem[1, m] + h for h in (0.0, 5.0, 20.0, 100.0)]
                cotas.append(float(dem.max()) + 1000.0)
                tapaba, ok = False, True
                for cota in cotas:
                    d2 = dem.copy()
                    d2[:, m] = cota
                    v = line_of_sight(d2, RES, RES, c0, 1, c1, 1, defecto=defecto)
                    if tapaba and v:
                        ok = False          # subir la celda destapo
                    tapaba = not v
                if not tapaba:
                    ok = False              # el obstaculo dominante no tapa
                n += 1
                fallos += int(not ok)
        return fallos, n

    def distancia_critica_derivada(defecto):
        """Sobre un plano, con alturas sorteadas: se ve al 90 % de la distancia
        critica derivada, se pierde al 110 % y sigue perdida al 150 %.

        Discrimina el signo y la presencia del termino de curvatura, y tambien
        la altura del objetivo, porque la distancia critica depende de ella.
        """
        fallos = n = 0
        rng = np.random.default_rng(31)
        for _ in range(40):
            ho, ht = (float(x) for x in rng.uniform(0.5, 30.0, 2))
            dc = distancia_critica(ho, ht)
            c_bajo = int(0.9 * dc / RES)
            c_alto = int(1.1 * dc / RES) + 1
            c_lejos = int(1.5 * dc / RES) + 1
            dem = plano(c_lejos + 2)
            for c, esperado in ((c_bajo, True), (c_alto, False), (c_lejos, False)):
                v = line_of_sight(dem, RES, RES, 0, 1, c, 1, h_obs=ho, h_tgt=ht,
                                  defecto=defecto)
                n += 1
                fallos += int(bool(v) != esperado)
        return fallos, n

    def alturas_monotonas_y_suficientes(defecto):
        """Subir el observador o el objetivo nunca quita vista, y doblando la
        altura desde 1 m se acaba viendo siempre (antes de 2^20 m).

        La existencia es lo que discrimina: un motor que deje el objetivo en el
        suelo no lo vera nunca por mucho que se le suba.
        """
        fallos = n = 0
        for dem in terrenos_aleatorios(40, 13):
            for c0, c1 in ((0, 299), (40, 180)):
                for lado in ("observador", "objetivo"):
                    veia, ok = False, True
                    for k in range(21):
                        h = float(2 ** k)
                        ho, ht = (h, 1.7) if lado == "observador" else (1.7, h)
                        v = line_of_sight(dem, RES, RES, c0, 1, c1, 1, h_obs=ho, h_tgt=ht,
                                          defecto=defecto)
                        if veia and not v:
                            ok = False          # subir quito vista
                        veia = v
                    if not veia:
                        ok = False              # nunca llego a verse
                    n += 1
                    fallos += int(not ok)
        return fallos, n

    P.append(("reciprocidad con alturas intercambiadas", reciprocidad_alturas))
    P.append(("obstaculo dominante en cualquier celda interior", obstaculo_dominante))
    P.append(("distancia critica derivada sobre plano", distancia_critica_derivada))
    P.append(("alturas: subir nunca quita vista y basta para ver", alturas_monotonas_y_suficientes))
    return P


def propiedades_v1():
    """Las cuatro propiedades de la primera version, tal como estaban.

    Se conservan porque el analisis de mutantes mostro que ninguna detecta
    ningun defecto: son condiciones necesarias que todos los mutantes cumplen.
    Ese resultado se registra en benchmark.json como hallazgo.
    """
    P = []

    def reciprocidad(defecto):
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
        fallos = n = 0
        dc = distancia_critica_aprox(1.7, 3.0)
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
